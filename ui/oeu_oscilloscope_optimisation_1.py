import serial
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

def get_data():
    with serial.Serial('path to usb', 115200, timeout=0.01) as ser:
        while True:
            r = ser.read(3)
            if len(r) == 3:
                yield int(r.decode())
            else:
                yield -1

data_size = 500

# Create new Figure with black background
fig = plt.figure(figsize=(16, 8), facecolor='black')

# Add a subplot with no frame
ax = plt.subplot(frameon=False)

r = get_data()
data = np.zeros(data_size,dtype=int)

# Generate line plots
xscale = np.linspace(-1,1,data.shape[-1])
line, = ax.plot(xscale, data, color="g")

ax.set_ylim(-1, 1000)

ax.text(0.5, 1.0, "One Electron Universe ", transform=ax.transAxes,
        ha="center", va="center", color="g",
        family="sans-serif", fontweight="bold", fontsize=16)

def update(*args):

    skip = 400

    next_line = np.zeros(data_size,dtype=int)
    next_line[:data_size-skip] = data[skip:]
    next_line[data_size-skip:] = np.array([next(r) for _ in range(skip)])
    data[:] = next_line

    line.set_ydata(data)
    return line

anim = animation.FuncAnimation(fig, update, interval=1)
plt.show()
