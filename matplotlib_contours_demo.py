import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl

x_data = np.arange(0, 10, 0.01)
y_data = np.array([np.sin(i/10 + x_data) for i in range(1, 11)])

fig, axs = plt.subplots(2, 1, figsize=(5, 4))

axs[0].plot(x_data, y_data[0], label='sin(x)')
axs[0].set_title('Line Plot')

gradient = np.vstack((x_data, y_data))

# y_data = np.array([y_data])
print(y_data.shape)
axs[1].pcolormesh(y_data, cmap='gist_ncar')
axs[1].set_title('Line Plot with Viridis Colormap')

plt.figure(figsize=(5, 4))

theta_vec = np.linspace(0, np.pi, 50)
# Radius goes from 0 to 10
r_vec = np.linspace(0, 10, 50)

# Create the 2D grid
theta, r = np.meshgrid(theta_vec, r_vec)

y_data = np.sin(r + theta)
print(y_data.shape)

ax_polar = plt.subplot(projection='polar')
ax_polar.pcolormesh(theta, r, y_data, cmap='gist_ncar')
ax_polar.set_title('Line Plot with Viridis Colormap')

plt.tight_layout()
plt.show()