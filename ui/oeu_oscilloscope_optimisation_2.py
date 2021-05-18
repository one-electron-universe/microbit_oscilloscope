import sys
import threading
import serial
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Slider, Button, RadioButtons
import time
import pickle
import argparse

data_store = 4000000
data = [0 for _ in range(data_store)]
dataptr = 1
displayptr = 0
sfreq = 0
wfreq = 1000000
display_size = 1200
new_display_size = display_size

def dump_data(event):
    global data, dataptr
    filename = time.strftime("%Y%m%d%H%M%S") + ".oeu"
    with open(filename, "wb") as f:
        pickle.dump((dataptr, data),f)
        f.close()

def zoom_out(event):
    global ax, display_size, new_display_size
    new_display_size = display_size * 2

def get_stored_data(filename):
    global data, dataptr
    with open(filename, "rb") as f:
        dataptr, data = pickle.load(f)
        f.close()

def zoom_in(event):
    global ax, display_size, new_display_size
    new_display_size = int(display_size / 2)

def get_data(usbpath):
    global data, dataptr, sfreq, wfreq, ax
    time_count = time.perf_counter()
    last_dataptr = 0
    with serial.Serial(usbpath, 115200, timeout=0.01) as ser:
        f = None
        while True:
            r = ser.read()
            for b in r:
                #print(b,r)
                if dataptr >= len(data):
                     print("ran out of space")
                     dataptr = 1
                data[dataptr] = b
                #print(data[dataptr])
                if data[dataptr-1] <= 100 and data[dataptr] > 100:
                    wfreq = (dataptr - last_dataptr)
                    last_dataptr = dataptr
                dataptr += 1
                if dataptr % 1000 == 0:
                    now = time.perf_counter()
                    sfreq = 1000.0 / (now - time_count)
                    time_count = now
                    if f is None:
                        f = ax.text(0.9, 1.0, "SF =  " + str(int(sfreq)), transform=ax.transAxes,
                            ha="center", va="center", color="g", family="sans-serif",
                            fontweight="bold", fontsize=10)
                    else:
                        f.set_text("WF = " + "{:.4F}".format(sfreq/wfreq) 
                                + " SF = " + str(int(sfreq)) 
                                + " WS = " + "{:.4f}".format(display_size/sfreq))
                    #print(sfreq)

def update_skip(val):
    global skip
    skip = sspeed.val

def update_display_count(val):
    global dataptr, displayptr
    if scount.val > dataptr:
        scount.set_val(dataptr)
    displayptr = scount.val

def update(*args):
    #print(args)

    global skip, display_size, new_display_size, dataptr, displayptr, line, display_data, scount

    if dataptr < display_size:
        return line

    skip_data = min(skip, max(dataptr - displayptr, 0))

    displayptr += skip_data
    if displayptr+display_size > dataptr:
        displayptr = dataptr - display_size
    display_data[:] = np.array(data[displayptr:displayptr+display_size])

    #will this work?
    scount.set_val(displayptr)

    line.set_ydata(display_data)
    return line

if __name__ == "__main__" :
    parser = argparse.ArgumentParser(description="OEU Oscilloscope (3KHz)")
    parser.add_argument("-f", action="store_true",help="read data from file")
    parser.add_argument("path", help="usb or file path")
    parser.add_argument("wsize", type=int, help="size of window")

    args = parser.parse_args()

    read_from_file=args.f
    usbpath = args.path
    display_size = args.wsize

    print(read_from_file, usbpath, display_size)

    skip = int(display_size/10)

    if read_from_file:
        skip = 0
        get_stored_data(usbpath)
    else:
        # START COLLECTING DATA if not loading from file
        collector = threading.Thread(target=get_data, args=(usbpath,), daemon=True)
        collector.start()

    # Create new Figure with black background
    fig = plt.figure(figsize=(16, 8), facecolor='black')

    # Add a subplot with no frame
    ax = plt.subplot(frameon=False)

    plt.axline((0,0),(1,0),lw=1)
    plt.axline((0,85),(1,85),lw=0.2)
    plt.axline((0,170),(1,170),lw=0.2)
    plt.axline((0,255),(1,255),lw=0.2)
    axcolor = 'lightblue'
    #attempting slider
    axspeed = plt.axes([0.18, 0.05, 0.65, 0.03], facecolor=axcolor)
    axcount = plt.axes([0.18, 0.0, 0.65, 0.03], facecolor=axcolor)

    sspeed = Slider(axspeed, 'Speed', 0, display_size, valinit=skip, color='g', valstep=1)
    scount = Slider(axcount, 'Data', 1, data_store, valinit=display_size, color='g', valstep=1)

    sspeed.on_changed(update_skip)
    scount.on_changed(update_display_count)

    #rax = plt.axes([0.1, 0.9, 0.1, 0.1], facecolor=axcolor)
    #radio = RadioButtons(rax, ('Real Time', 'Stored'))

    axsave = plt.axes([0.1, 0.9, 0.05,0.05], facecolor=axcolor)
    bsave = Button(axsave, "Save")
    bsave.on_clicked(dump_data)

    #axzoomin = plt.axes([0.16, 0.9, 0.05,0.05], facecolor=axcolor)
    #bzoomin = Button(axzoomin, "Zoom In")
    #bzoomin.on_clicked(zoom_in)

    #axzoomout = plt.axes([0.22, 0.9, 0.05,0.05], facecolor=axcolor)
    #bzoomout = Button(axzoomout, "Zoom Out")
    #bzoomout.on_clicked(zoom_out)

    display_data = np.zeros(display_size,dtype=int)

    # Generate line plots
    xscale = np.linspace(0,display_data.shape[-1]-1,display_data.shape[-1])
    lw = 1
    line, = ax.plot(xscale, display_data, color="g", lw=lw)

    ax.set_ylim(0, 300)

    #ax.set_xticks(np.array([x/1000. for x in range(1000)]))
    #ax.set_yticks(np.array([y for y in range(-1,1000)]))

    #ax.set_xticks([])
    #ax.set_yticks([])

    ax.text(0.5, 1.0, "One Electron Universe ", transform=ax.transAxes,
        ha="center", va="center", color="g", family="sans-serif", fontweight="bold", fontsize=16)

    anim = animation.FuncAnimation(fig, update, interval=1)
    plt.show()
