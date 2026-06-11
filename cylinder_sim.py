import socket
import threading

import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from pyqtgraph.Qt import QtCore, QtWidgets

# --- Config -----------------------------------------------------------------
BIND_IP       = "0.0.0.0"       # listen on all interfaces (catches loopback too)
PORT          = 6454            # Art-Net port
NUM_STRIPS    = 16
PIXELS        = 150
UNIVERSE_BASE = 0               # must match the player
RADIUS        = 14.0            # cylinder radius (world units)
HEIGHT        = 45.0            # cylinder height (world units)
POINT_SIZE    = 4.0            # LED dot size in pixels
UNLIT_COLOR   = (0.05, 0.05, 0.06)  # faint ambient so strips show when idle
# ----------------------------------------------------------------------------

ARTNET_HEADER = b"Art-Net\x00"

# Shared LED buffer: (strip, pixel, RGB). Written by the receiver thread,
# read by the render timer. uint8 assignment under the GIL is atomic enough here.
pixels = np.zeros((NUM_STRIPS, PIXELS, 3), dtype=np.uint8)


def parse_artdmx(data):
    """Return (strip, rgb_array) for a valid ArtDMX packet, else None."""
    if len(data) < 18 or data[:8] != ARTNET_HEADER:
        return None
    if (data[8] | (data[9] << 8)) != 0x5000:        # OpOutput / ArtDMX
        return None
    universe = data[14] | (data[15] << 8)
    strip = universe - UNIVERSE_BASE
    if not (0 <= strip < NUM_STRIPS):
        return None
    length = (data[16] << 8) | data[17]
    n = min(length // 3, PIXELS)
    if n == 0:
        return None
    rgb = np.frombuffer(data[18:18 + n * 3], dtype=np.uint8).reshape(n, 3)
    return strip, rgb


def receiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((BIND_IP, PORT))
    while True:
        data, _ = sock.recvfrom(2048)
        parsed = parse_artdmx(data)
        if parsed:
            strip, rgb = parsed
            pixels[strip, :len(rgb)] = rgb


def make_positions():
    """3D positions for every LED: 16 vertical strips around a cylinder."""
    pos = np.zeros((NUM_STRIPS * PIXELS, 3), dtype=np.float32)
    i = 0
    for s in range(NUM_STRIPS):
        ang = 2 * np.pi * s / NUM_STRIPS
        x, y = RADIUS * np.cos(ang), RADIUS * np.sin(ang)
        for p in range(PIXELS):
            z = (0.5 - p / (PIXELS - 1)) * HEIGHT  # pixel 0 at top
            pos[i] = (x, y, z)
            i += 1
    return pos


def main():
    app = QtWidgets.QApplication([])
    view = gl.GLViewWidget()
    view.setWindowTitle("Cylinder Art-Net Simulation  (drag=orbit, scroll=zoom)")
    view.setCameraPosition(distance=2.2 * HEIGHT, elevation=12)
    view.resize(900, 900)
    view.show()

    # Grid mesh capping the TOP of the cylinder.
    grid = gl.GLGridItem()
    grid.setSize(RADIUS * 3, RADIUS * 3, 1)
    grid.setSpacing(RADIUS / 4, RADIUS / 4, 1)
    grid.translate(0, 0, HEIGHT / 2)
    view.addItem(grid)

    pos = make_positions()
    colors = np.ones((NUM_STRIPS * PIXELS, 4), dtype=np.float32)  # RGBA, A=1
    colors[:, :3] = UNLIT_COLOR
    scatter = gl.GLScatterPlotItem(pos=pos, color=colors, size=POINT_SIZE,
                                   pxMode=True)
    view.addItem(scatter)

    def update():
        # strip-major flatten matches make_positions() ordering.
        rgb = pixels.reshape(-1, 3).astype(np.float32) / 255.0
        dark = rgb.max(axis=1) < 0.05            # unlit LEDs -> show dim gray
        rgb[dark] = UNLIT_COLOR
        colors[:, :3] = rgb
        scatter.setData(color=colors)

    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(16)  # ~60 fps refresh

    threading.Thread(target=receiver, daemon=True).start()
    pg.exec()


if __name__ == "__main__":
    main()
