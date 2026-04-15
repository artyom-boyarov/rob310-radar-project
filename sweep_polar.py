import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
import numpy as np
import cv2

# --- Configuration ---
NUM_RANGE_BINS = 500
NUM_ANGLES = 360
CARTESIAN_SIZE = 1000

# Define your Radar's Physical Sweep Constraints
MIN_ANGLE = -45
MAX_ANGLE = 45

# 1. Initialize the Polar Matrix
polar_data = np.zeros((NUM_ANGLES, NUM_RANGE_BINS), dtype=np.float32)

# --- PyQtGraph Setup ---
app = pg.mkQApp()
plt = pg.plot(title="Phased Array FMCW Radar (-45° to +45°)")
plt.setAspectLocked(True)
plt.setXRange(-NUM_RANGE_BINS, NUM_RANGE_BINS)
plt.setYRange(-NUM_RANGE_BINS, NUM_RANGE_BINS)

# Create a blank image to initialize dimensions, using row-major to sync with OpenCV
blank_image = np.zeros((CARTESIAN_SIZE, CARTESIAN_SIZE))
imageItem = pg.ImageItem(blank_image, axisOrder='row-major')
imageItem.setRect(QtCore.QRectF(-NUM_RANGE_BINS, -NUM_RANGE_BINS, CARTESIAN_SIZE, CARTESIAN_SIZE))
plt.addItem(imageItem)
plt.addColorBar(imageItem, colorMap='viridis', values=(0, 255))

# Draw physical range rings (light gray)
for r in range(100, NUM_RANGE_BINS + 1, 100):
    circle = QtWidgets.QGraphicsEllipseItem(-r, -r, 2 * r, 2 * r)
    circle.setPen(pg.mkPen((150, 150, 150, 100)))
    plt.addItem(circle)

# Draw dashed boundary lines for the -45 and +45 degree limits
bound_pen = pg.mkPen((150, 150, 150, 150), style=QtCore.Qt.DashLine)
for angle in [MIN_ANGLE, MAX_ANGLE]:
    rad = np.radians(angle)
    # Using the "Top = 0" convention (sin for x, cos for y)
    x = NUM_RANGE_BINS * np.sin(rad)
    y = NUM_RANGE_BINS * np.cos(rad)
    plt.plot([0, x], [0, y], pen=bound_pen)

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
        y = np.zeros_like(x_array, dtype=float)
        for amp, freq, phase in params:
            y += amp * np.sin(2 * np.pi * freq * x_array + phase)
        return np.clip(y + 128, 0, 255)

    return f


sweepFunc = make_random_sine_sum()
range_indices = np.arange(NUM_RANGE_BINS)

# --- Simulation Logic ---
current_angle_deg = MIN_ANGLE
sweep_direction = 1  # 1 for sweeping right, -1 for sweeping left


def update():
    global current_angle_deg, polar_data, sweep_direction

    # 1. Phosphor Decay (Fading)
    polar_data *= 0.98

    # 2. Ingest New Data
    new_ping = sweepFunc(range_indices + current_angle_deg)

    # SHIFT THE ANGLE BY 270 DEGREES.
    # OpenCV natively places 0 degrees at the Right (East).
    # By adding 270, we force OpenCV to map our 0 degrees to the Top (North).
    matrix_row = int(90 - current_angle_deg) % 360
    polar_data[matrix_row, :] = new_ping

    # 3. Transform Polar to Cartesian
    cartesian_image = cv2.warpPolar(
        polar_data,
        dsize=(CARTESIAN_SIZE, CARTESIAN_SIZE),
        center=(NUM_RANGE_BINS, NUM_RANGE_BINS),
        maxRadius=NUM_RANGE_BINS,
        flags=cv2.WARP_INVERSE_MAP | cv2.INTER_LINEAR
    )


    # 4. Update the GUI
    imageItem.setImage(cartesian_image, autoLevels=False)

    # 5. Update the red sweep line visual
    rad = np.radians(current_angle_deg)
    x = NUM_RANGE_BINS * np.sin(rad)
    y = NUM_RANGE_BINS * np.cos(rad)
    beam_line.setData([0, x], [0, y])

    # 6. Ping-Pong Sweep Logic
    current_angle_deg += sweep_direction

    # If we hit a boundary, reverse the sweep direction
    if current_angle_deg >= MAX_ANGLE:
        sweep_direction = -1
    elif current_angle_deg <= MIN_ANGLE:
        sweep_direction = 1


timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(16)  # ~60 FPS

pg.exec()