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

theta = 0

center_x, center_y = 0, 0
max_radius = 10
step = 1

for r in range(step, max_radius + 1, step):
    circle = QtWidgets.QGraphicsEllipseItem(
        center_x - r, center_y - r,
        2 * r, 2 * r
    )
    circle.setPen(pg.mkPen((150, 150, 150, 120)))  # light gray
    plt.addItem(circle)

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
    global steps, theta
    steps += 1
    theta += 0.01
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