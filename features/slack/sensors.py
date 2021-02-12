import numpy as np
import matplotlib.pyplot as plt
import datetime
import sys

# source: https://matplotlib.org/stable/gallery/lines_bars_and_markers/cohere.html#sphx-glr-gallery-lines-bars-and-markers-cohere-py
# (with tweaks)

def get_data(write_file=None):

    # Fixing random state for reproducibility
    np.random.seed(19680801)

    dt = .01
    t = np.arange(0, 30, dt)

    # get important data from sensitive instruments
    nse1 = np.random.randn(len(t))
    nse2 = np.random.randn(len(t))
    s1 = np.sin(2 * np.pi * 10 * t) + nse1
    s2 = np.sin(2 * np.pi * 10 * t) + nse2

    # plot them both
    fig, axs = plt.subplots(2, 1)
    axs[0].plot(t, s1, t, s2)
    axs[0].set_xlim(0, 2)

    now = datetime.datetime.now()
    time = now - datetime.timedelta(seconds=now.second % 2,
                                    microseconds=now.microsecond)


    axs[0].set_xlabel(f"seconds after {time.strftime('%H:%M:%S')}")
    axs[0].set_ylabel('sensor output')
    axs[0].grid(True)


    # look for patterns
    cxy, f = axs[1].cohere(s1, s2, 256, 1. / dt)
    axs[1].set_ylabel('signal strength')

    fig.tight_layout()

    if write_file:
        plt.savefig(write_file)

    return np.max(cxy)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        get_data(sys.argv[1])
    else:
        get_data("plot.png")
