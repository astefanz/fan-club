################################################################################
## Project: Fanclub Mark IV "Master" splash screen ## File: splash.py         ##
##----------------------------------------------------------------------------##
## CALIFORNIA INSTITUTE OF TECHNOLOGY ## GRADUATE AEROSPACE LABORATORY ##     ##
## CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES                      ##     ##
##----------------------------------------------------------------------------##
##      ____      __      __  __      _____      __      __    __    ____     ##
##     / __/|   _/ /|    / / / /|  _- __ __\    / /|    / /|  / /|  / _  \    ##
##    / /_ |/  / /  /|  /  // /|/ / /|__| _|   / /|    / /|  / /|/ /   --||   ##
##   / __/|/ _/    /|/ /   / /|/ / /|    __   / /|    / /|  / /|/ / _  \|/    ##
##  / /|_|/ /  /  /|/ / // //|/ / /|__- / /  / /___  / -|_ - /|/ /     /|     ##
## /_/|/   /_/ /_/|/ /_/ /_/|/ |\ ___--|_|  /_____/| |-___-_|/  /____-/|/     ##
## |_|/    |_|/|_|/  |_|/|_|/   \|___|-    |_____|/   |___|     |____|/       ##
##                   _ _    _    ___   _  _      __  __   __                  ##
##                  | | |  | |  | T_| | || |    |  ||_ | | _|                 ##
##                  | _ |  |T|  |  |  |  _|      ||   \\_//                   ##
##                  || || |_ _| |_|_| |_| _|    |__|  |___|                   ##
##                                                                            ##
##----------------------------------------------------------------------------##
## Alejandro A. Stefan Zavala ## <astefanz@berkeley.edu>   ##                 ##
## Chris J. Dougherty         ## <cdougher@caltech.edu>    ##                 ##
## Marcel Veismann            ## <mveisman@caltech.edu>    ##                 ##
################################################################################

""" ABOUT ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 + Show a "splash screen," built in an independent Python process to avoid
 + interfering with the primary FC GUI.
 +
 + Original recipe by Sunjay Varma.
 + See: http://code.activestate.com/recipes/577271-tkinter-splash-screen/
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import tkinter as tk
import tkinter.ttk as ttk

import multiprocessing as mp
import threading as mt
import time as tm

from fc.frontend.gui.embedded import splash3_bg as stp

## AUXILIARY GLOBALS ###########################################################
DEFAULT_TIMEOUT = 3

## MAIN ########################################################################
class SplashFrame(tk.Frame):
    """
    Borderless container for arbitrary widgets to be displayed in the FC splash
    screen.
    """

    def __init__(self, widget, master=None, width=750, height=500, ratio=False):

        tk.Frame.__init__(self, master)
        self.pack(side = tk.TOP, fill = tk.BOTH, expand = tk.YES)

        # Screen size
        ws = self.master.winfo_screenwidth()
        hs = self.master.winfo_screenheight()
        w = (ratio and ws*width) or width
        h = (ratio and ws*height) or height

        # Position
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        self.master.geometry('%dx%d+%d+%d' % (w, h, x, y))

        self.widget = widget(self)
        self.widget.pack(fill = tk.BOTH, expand = True)

        self.master.overrideredirect(True)
        self.lift()

class FCSplashWidget(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)

        self.image = tk.PhotoImage(data = stp.SPLASH)
        self.image = self.image.subsample(2)
        self.label = tk.Label(self, image = self.image, anchor = tk.CENTER,
            bg = '#ff6e1f')
        self.label.pack(side = tk.LEFT, fill = tk.BOTH, expand = True)

class SerialSplash:
    """
    Splash screen that blocks while it is desplayed (better cross-platform
    compatibility).
    """

    def __init__(self, version = "[...]", widget = FCSplashWidget, **kwargs):
        self.version = version
        self.widget = widget
        self.kwargs = kwargs

    def run(self, timeout = DEFAULT_TIMEOUT):
        """
        Display the splash screen for TIMEOUT seconds. If omitted, TIMEOUT
        defaults to DEFAULT_TIMEOUT.
        """
        root = tk.Tk()
        root.bind("<Button-1>", lambda e: root.destroy())
        splash = SplashFrame(master = root, widget = self.widget, **self.kwargs)
        start = tm.time()

        root.after(1000*timeout, root.destroy)
        root.mainloop()

class ParallelSplash:
    """
    Splash window that is built as a separate process, allowing for other tasks
    to be done while it is being displayed.
    """

    @staticmethod
    def _routine(lock, widget, timeout, kwargs = {}):
        """
        To be executed by the separate process that displays the splash screen.
        """
        root = tk.Tk()
        root.bind("<Button-1>", lambda e: root.destroy())
        splash = SplashFrame(master = root, widget = widget, **kwargs)
        start = tm.time()

        def r():
            acquired = False
            while (tm.time()-start < timeout) if timeout is not None else True:
                tm.sleep(.01)
                if lock.acquire(False):
                    acquired = True
                    break
            if acquired:
                lock.release()
            root.destroy()

        thread = mt.Thread(name = "FC Splash Screen Watchdog", target = r,
            daemon = True)

        thread.start()
        root.mainloop()

    def __init__(self, version, timeout = None, widget = FCSplashWidget,
        **kwargs):
        """
        WIDGET is a class that inherits from Tkinter's Frame class, to be
        instantiated with no arguments (other than a parent Frame), and packed
        to fill the entirety of the splash screen.

        VERSION is a String to be represent the FC software version being run.

        TIMEOUT is an integer representing the number of seconds to wait before
        the splash screen deletes itself. Defaults to None to indicate the
        splash screen will wait indefinitely.

        Optionally, keyword arguments that correspond to the FC SplashScreen
        constructor can be forwarded.
        """
        self.widget = widget
        self.version = version
        self.timeout = timeout
        self.kwargs = kwargs
        self._setProcess()

    def start(self):
        """
        Start the splash screen. Does nothing if the splash screen is already
        active.
        """
        if not self.isActive():
            self.lock.acquire()
            self.process.start()

    def stop(self):
        """
        Stop the splash screen. Does nothing if the splash screen is not active.
        """
        if self.isActive():
            self.lock.release()

    def join(self, timeout = None):
        """
        Block until the splash screen process ends on its own. Terminate after
        TIMEOUT seconds (wait forever if no TIMEOUT is given). Returns
        immediately if the process is not active.
        """
        self.process.join(timeout)
        self.stop()
        self.terminate()

    def terminate(self):
        """
        Forcibly terminate the splash screen process. Does nothing if such
        process is already dead.
        """
        if self.process.is_alive():
            self.process.terminate()

    def isActive(self):
        """
        Return whether the splash screen is currently shown.
        """
        return self.process.is_alive()

    def _setProcess(self):
        self.lock = mp.Lock()
        self.process = mp.Process(name = "FC Splash Screen",
            target = self._routine,
            args = (self.lock, self.widget, self.timeout, self.kwargs),
            daemon = True)
