import sys
import time

import cv2
import numpy as np
import sounddevice as sd
import soundfile as sf
from stupidArtnet import StupidArtnet

# --- Config -----------------------------------------------------------------
TARGET_IP     = "192.168.1.195"  # Network Address (destination). 127.0.0.1 = loopback
SOURCE_IP     = "192.168.1.20"   # Local Address (NIC to send from); None = auto
MIRROR_IP     = "127.0.0.1"      # also send here for cylinder_sim.py; None to disable
ARTNET_PORT   = 6454             # standard Art-Net port
UNIVERSE_BASE = 0               # change to 1 if controller is 1-indexed
VIDEO_FILE    = "show.mov"
AUDIO_FILE    = "track.wav"
PLAY_AUDIO    = True            # set True to play audio in sync
NUM_STRIPS    = 16
PIXELS        = 150
# ----------------------------------------------------------------------------

PACKET_SIZE = PIXELS * 3        # 450 bytes per universe


def load_video(path):
    """Decode the whole video into (n_frames, NUM_STRIPS, PIXELS, 3) uint8 RGB."""
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        sys.exit(f"ERROR: could not open video '{path}'")
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))  # OpenCV is BGR
    cap.release()
    if not frames:
        sys.exit(f"ERROR: no frames decoded from '{path}'")
    video = np.asarray(frames, dtype=np.uint8)
    # Source is 16 wide x 150 tall (strips run as columns); transpose so each
    # strip becomes a row -> (n_frames, 16, 150, 3).
    if video.shape[1:3] == (PIXELS, NUM_STRIPS):
        video = video.transpose(0, 2, 1, 3)
    return np.ascontiguousarray(video), fps


def main():
    video, fps = load_video(VIDEO_FILE)
    n_frames, h, w, _ = video.shape

    if (h, w) != (NUM_STRIPS, PIXELS):
        sys.exit(f"ERROR: video is {h}x{w}, expected {NUM_STRIPS}x{PIXELS}")
    if not fps or fps <= 0:
        sys.exit("ERROR: could not read a valid fps from the video")

    duration = n_frames / fps
    print(f"fps={fps:.3f}  frames={n_frames}  duration={duration:.2f}s")

    # One Art-Net sender per universe / strip.
    # source_address is a socket bind (ip, port); port 0 = OS picks ephemeral.
    bind = (SOURCE_IP, 0) if SOURCE_IP else None
    senders = [
        StupidArtnet(TARGET_IP, UNIVERSE_BASE + r, PACKET_SIZE,
                     source_address=bind, port=ARTNET_PORT)
        for r in range(NUM_STRIPS)
    ]
    # Optional mirror to the local simulator (no source bind -> reaches loopback).
    mirror = [
        StupidArtnet(MIRROR_IP, UNIVERSE_BASE + r, PACKET_SIZE, port=ARTNET_PORT)
        for r in range(NUM_STRIPS)
    ] if MIRROR_IP else []

    def send_frame(idx):
        frame = video[idx]
        for r in range(NUM_STRIPS):
            packet = frame[r].tobytes()           # row -> 450 bytes RGB
            senders[r].send(packet)
            if mirror:
                mirror[r].send(packet)

    if not PLAY_AUDIO:
        # No audio: pace the video off the wall clock.
        frame_interval = 1.0 / fps
        start = time.perf_counter()
        idx = 0
        while True:
            send_frame(idx)
            idx = (idx + 1) % n_frames
            if idx == 0:
                start = time.perf_counter()
            sleep = (start + idx * frame_interval) - time.perf_counter()
            if sleep > 0:
                time.sleep(sleep)
        return

    # Audio is the master clock: the video frame is chosen from the audio's
    # real playback position, so the two can never drift apart and loop together.
    audio, sr = sf.read(AUDIO_FILE, dtype="float32", always_2d=True)
    n_audio = len(audio)
    print(f"audio: {n_audio / sr:.2f}s @ {sr}Hz  ({audio.shape[1]} ch)")
    if abs(n_audio / sr - duration) > 0.05:
        print(f"WARNING: audio/video lengths differ by "
              f"{abs(n_audio / sr - duration) * 1000:.0f} ms -> they will be "
              f"time-stretched to match. Re-export them to equal length.")

    pos = 0                          # current audio frame (written), wraps on loop
    def callback(outdata, frames, time_info, status):
        nonlocal pos
        i = 0
        while i < frames:            # fill output, looping seamlessly at the end
            n = min(frames - i, n_audio - pos)
            outdata[i:i + n] = audio[pos:pos + n]
            pos = (pos + n) % n_audio
            i += n

    stream = sd.OutputStream(samplerate=sr, channels=audio.shape[1],
                             callback=callback)
    stream.start()
    lat = int(stream.latency * sr)   # frames the buffer runs ahead of the speakers
    last = -1
    while True:
        # Audible position -> matching video frame (audio fraction maps to video).
        audible = (pos - lat) % n_audio
        idx = min(int(audible / n_audio * n_frames), n_frames - 1)
        if idx != last:
            last = idx
            send_frame(idx)
        time.sleep(0.001)            # poll the audio clock ~1 kHz; cheap


if __name__ == "__main__":
    main()
