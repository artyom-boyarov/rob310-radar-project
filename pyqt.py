import pyqtgraph as pg
import numpy as np

app = pg.mkQApp()
plt = pg.plot()
plt.setAspectLocked(True)
plt.setXRange(-10, 10)
plt.setYRange(-10, 10)

data = np.fromfunction(lambda i, j: (1+0.3*np.sin(i)) * (i)**2 + (j)**2, (100, 100))
print(data)
noisy_data = data * (1 + 0.2 * np.random.random(data.shape) )
imageItem = pg.ImageItem(noisy_data)
imageItem.setPos(-50, -50)
plt.addItem(imageItem)
plt.addColorBar(imageItem, colorMap='viridis', values=(0, 20_000) ) 

beam_line = plt.plot()

theta = 0

def update():
    global theta
    theta += 0.05
    imageItem.setImage(data * (1 + 0.2 * np.random.random(data.shape) ))
    
    # r = np.linspace(0, 10, 100)
    # x = r * np.cos(theta)
    # y = r * np.sin(theta)

    # beam_line.setData(x, y)

timer = pg.QtCore.QTimer()
timer.timeout.connect(update)
timer.start(16)  # ~60 FPS

pg.exec()