import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
import numpy as np
import cv2

# --- Configuration ---
NUM_RANGE_BINS = 500
NUM_ANGLES = 360
CARTESIAN_SIZE = 1000

# 1. Initialize the Polar Matrix
polar_data = np.zeros((NUM_ANGLES, NUM_RANGE_BINS), dtype=np.float32)

# --- PyQtGraph Setup ---
app = pg.mkQApp()
plt = pg.plot()
plt.setAspectLocked(True)
plt.setXRange(-NUM_RANGE_BINS, NUM_RANGE_BINS)
plt.setYRange(-NUM_RANGE_BINS, NUM_RANGE_BINS)

# Create a blank image to initialize dimensions, then set Rect
blank_image = np.zeros((CARTESIAN_SIZE, CARTESIAN_SIZE))
imageItem = pg.ImageItem(blank_image)
imageItem.setRect(QtCore.QRectF(-NUM_RANGE_BINS, -NUM_RANGE_BINS, CARTESIAN_SIZE, CARTESIAN_SIZE))
plt.addItem(imageItem)

# Using your requested 'viridis' colormap
plt.addColorBar(imageItem, colorMap='viridis', values=(0, 255))

# Draw physical range rings (light gray)
for r in range(100, NUM_RANGE_BINS + 1, 100):
    circle = QtWidgets.QGraphicsEllipseItem(-r, -r, 2 * r, 2 * r)
    circle.setPen(pg.mkPen((150, 150, 150, 100)))
    plt.addItem(circle)

beam_line = plt.plot(pen=pg.mkPen('r', width=2))


# --- Your Custom Sweep Function ---
def make_random_sine_sum(n_waves=5, freq_range=(0.01, 0.05), amp_range=(10, 50)):
    params = []
    for _ in range(n_waves):
        amp = np.random.uniform(*amp_range)
        freq = np.random.uniform(*freq_range)
        phase = np.random.uniform(0, 2 * np.pi)
        params.append((amp, freq, phase))

    def f(x_array):
        # We process the entire array of 500 range bins at once
        y = np.zeros_like(x_array, dtype=float)
        for amp, freq, phase in params:
            y += amp * np.sin(2 * np.pi * freq * x_array + phase)

        # Shift the wave up so it's strictly positive, and scale to 255 for the colormap
        return np.clip(y + 128, 0, 255)

    return f


# Create the function and an array representing the range (0 to 499)
sweepFunc = make_random_sine_sum()
range_indices = np.arange(NUM_RANGE_BINS)

# --- Simulation Logic ---
current_angle_deg = 0


def update():
    global current_angle_deg, polar_data

    # 1. Phosphor Decay (Fading) - comment this out if you don't want the tail to fade!
    polar_data *= 0.98

    # 2. Ingest New Data
    # We pass the range indices + the angle so the wave visually shifts as it spins
    new_ping = sweepFunc(range_indices + current_angle_deg)
    polar_data[current_angle_deg, :] = new_ping

    # 3. Transform Polar to Cartesian
    cartesian_image = cv2.warpPolar(
        polar_data,
        dsize=(CARTESIAN_SIZE, CARTESIAN_SIZE),
        center=(NUM_RANGE_BINS, NUM_RANGE_BINS),
        maxRadius=NUM_RANGE_BINS,
        flags=cv2.WARP_INVERSE_MAP | cv2.INTER_LINEAR
    )

    # Flip the image over the Y-axis to make it sweep Clockwise
    cartesian_image = cv2.flip(cartesian_image, 1)

    # 4. Update the GUI
    imageItem.setImage(cartesian_image, autoLevels=False)

    # 5. Update the red sweep line visual
    rad = np.radians(current_angle_deg + 180)
    x = NUM_RANGE_BINS * -np.sin(rad)
    y = NUM_RANGE_BINS * np.cos(rad)
    beam_line.setData([0, x], [0, y])

    # Move to the next angle
    current_angle_deg = (current_angle_deg + 1) % NUM_ANGLES


timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(16)  # ~60 FPS

pg.exec()