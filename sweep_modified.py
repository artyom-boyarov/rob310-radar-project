import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import numpy as np

app = pg.mkQApp()
plt = pg.plot()
plt.setAspectLocked(True)
plt.setXRange(-10, 10)
plt.setYRange(-10, 10)

imageData = np.zeros((1000, 1000))
imageItem = pg.ImageItem(imageData)
#imageItem.setPos(-50, -50)
imageItem.setRect(-10, -10, 20, 20)
plt.addItem(imageItem)
plt.addColorBar(imageItem, colorMap='viridis', values=(0, 20_000) ) 

beam_line = plt.plot()

theta = np.pi / 4  # Start at 45 degrees
theta_dir = 1

max_radius = 10
step = 1

# --- Create the 90-degree sector grid ---
start_angle = np.pi / 4   # 45 degrees
end_angle = 3 * np.pi / 4 # 135 degrees
grid_pen = pg.mkPen(color=(255, 255, 255, 255), width=2.5)

# Draw the concentric arcs
arc_angles = np.linspace(start_angle, end_angle, 100)
for r in range(step, max_radius + 1, step):
    x = r * np.cos(arc_angles)
    y = r * np.sin(arc_angles)
    arc_item = pg.PlotCurveItem(x, y, pen=grid_pen)
    arc_item.setZValue(100)
    plt.addItem(arc_item)

# Draw the radial lines
for angle in [start_angle, end_angle]:
    x = [0, max_radius * np.cos(angle)]
    y = [0, max_radius * np.sin(angle)]
    line_item = pg.PlotCurveItem(x, y, pen=grid_pen)
    line_item.setZValue(100)
    plt.addItem(line_item)

def make_random_sine_sum(n_waves=5, freq_range=(0.5, 5.0), amp_range=(0.2, 1.0)):
    params = []
    for _ in range(n_waves):
        amp = np.random.uniform(*amp_range)
        freq = np.random.uniform(*freq_range)
        phase = np.random.uniform(0, 2 * np.pi)
        params.append((amp, freq, phase))

    def f(x):
        x = np.asarray(x)
        y = np.zeros_like(x, dtype=float)

        for amp, freq, phase in params:
            y += amp * np.sin(2 * np.pi * freq * x + phase)

        return y

    return f

sweepFunc = make_random_sine_sum(5, (0, 10), (2000, 2000))
dirStep = 1

stepsPerUpdate = 16
steps = 0

def update():
    global steps, theta, theta_dir
    steps += 1
    theta += 0.01 * theta_dir
    
    # Reverse direction if we hit 45 deg (pi/4) or 135 deg (3*pi/4)
    if theta >= 3 * np.pi / 4:
        theta = 3 * np.pi / 4
        theta_dir = -1
    elif theta <= np.pi / 4:
        theta = np.pi / 4
        theta_dir = 1

    w, h = imageData.shape
    dx, dy = np.cos(theta) * dirStep, np.sin(theta) * dirStep
    x, y = w / 2, h / 2
    while True:
        x, y= x + dx, y + dy
        i, j = int(x), int(y)
        if not (0 <= i < h and 0 <= j < w):
            break
        imageData[i, j] = 10000 + sweepFunc(theta)
    
    if (steps % stepsPerUpdate == 0):
        imageItem.setImage(imageData)
    
    

timer = pg.QtCore.QTimer()
timer.timeout.connect(update)
timer.start(1)  # ~60 FPS

pg.exec()
