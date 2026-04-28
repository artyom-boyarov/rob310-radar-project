import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
import numpy as np
import cv2
import warnings

# Silence PyQtGraph's internal math warnings on empty arrays
warnings.filterwarnings("ignore", category=RuntimeWarning)

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
plt.setBackground((68, 1, 84))  # Match Viridis 0-value (dark purple)
plt.setAspectLocked(True)

# Hide the default Cartesian X and Y axes
plt.hideAxis('left')
plt.hideAxis('bottom')

plt.setXRange(-400, 400, padding=0)
plt.setYRange(0, 550, padding=0)
plt.setLimits(xMin=-400, xMax=400, yMin=0, yMax=550)

# Create a blank image to initialize dimensions, using row-major to sync with OpenCV
blank_image = np.zeros((CARTESIAN_SIZE, CARTESIAN_SIZE))
imageItem = pg.ImageItem(blank_image, axisOrder='row-major', levels=(0, 255))
imageItem.setRect(QtCore.QRectF(-NUM_RANGE_BINS, -NUM_RANGE_BINS, CARTESIAN_SIZE, CARTESIAN_SIZE))
plt.addItem(imageItem)
plt.addColorBar(imageItem, colorMap='viridis', values=(0, 255))

grid_pen = pg.mkPen(color=(255, 255, 255, 255), width=2.5)

arc_angles = np.linspace(np.radians(MIN_ANGLE), np.radians(MAX_ANGLE), 100)
# Draw physical range arcs with higher precision (every 50 units)
for r in range(50, NUM_RANGE_BINS + 1, 50):
    x = r * np.sin(arc_angles)
    y = r * np.cos(arc_angles)
    arc_item = pg.PlotCurveItem(x, y, pen=grid_pen)
    arc_item.setZValue(100)
    plt.addItem(arc_item)

    # Distance labels on the left edge (-45 deg)
    text_left = pg.TextItem(f"{r}", color=(200, 200, 200), anchor=(1.1, 0.5))
    text_left.setPos(r * np.sin(np.radians(MIN_ANGLE)), r * np.cos(np.radians(MIN_ANGLE)))
    text_left.setZValue(100)
    plt.addItem(text_left)

    # Distance labels on the right edge (+45 deg)
    text_right = pg.TextItem(f"{r}", color=(200, 200, 200), anchor=(-0.1, 0.5))
    text_right.setPos(r * np.sin(np.radians(MAX_ANGLE)), r * np.cos(np.radians(MAX_ANGLE)))
    text_right.setZValue(100)
    plt.addItem(text_right)

# Draw dashed boundary lines for the -45 and +45 degree limits
bound_pen = pg.mkPen(color=(255, 255, 255, 255), width=2.5, style=QtCore.Qt.PenStyle.DashLine)
for angle in [MIN_ANGLE, MAX_ANGLE]:
    rad = np.radians(angle)
    # Using the "Top = 0" convention (sin for x, cos for y)
    x = NUM_RANGE_BINS * np.sin(rad)
    y = NUM_RANGE_BINS * np.cos(rad)
    line_item = plt.plot([0, x], [0, y], pen=bound_pen)
    line_item.setZValue(100)

# Draw internal angle marks and text labels every 15 degrees
for angle in range(MIN_ANGLE, MAX_ANGLE + 1, 15):
    rad = np.radians(angle)
    x_outer = NUM_RANGE_BINS * np.sin(rad)
    y_outer = NUM_RANGE_BINS * np.cos(rad)

    # Draw faint radial lines for the intermediate angles
    if angle not in [MIN_ANGLE, MAX_ANGLE]:
        faint_pen = pg.mkPen(color=(255, 255, 255, 100), width=1, style=QtCore.Qt.PenStyle.DotLine)
        line = plt.plot([0, x_outer], [0, y_outer], pen=faint_pen)
        line.setZValue(90)

    # Add angle text label just outside the max radius rim
    text_angle = pg.TextItem(f"{angle}°", color=(255, 255, 255), anchor=(0.5, 0.5))
    text_angle.setPos((NUM_RANGE_BINS + 25) * np.sin(rad), (NUM_RANGE_BINS + 25) * np.cos(rad))
    text_angle.setZValue(100)
    plt.addItem(text_angle)

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
        flags=cv2.WARP_INVERSE_MAP | cv2.INTER_LINEAR | cv2.WARP_FILL_OUTLIERS
    )


    # 4. Update the GUI
    imageItem.setImage(cartesian_image, autoLevels=False, levels=(0, 255))

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
