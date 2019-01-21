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

## AUXILIARY GLOBALS ###########################################################

## MAIN ########################################################################
class SplashFrame(tk.Frame):
    """
    Borderless container for arbitrary widgets to be displayed in the FC splash
    screen.
    """

    def __init__(self, widget, master=None, width=0.3, height=0.3,
        useFactor=True):

        tk.Frame.__init__(self, master)
        self.pack(side = tk.TOP, fill = tk.BOTH, expand = tk.YES)

        # Screen size
        ws = self.master.winfo_screenwidth()
        hs = self.master.winfo_screenheight()
        w = (useFactor and ws*width) or width
        h = (useFactor and ws*height) or height

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
        self.config(bg = 'red')
        self.label = tk.Label(self, text = 'TEST')
        self.label.pack(fill = tk.BOTH, expand = True)

class SplashHandler:

    @staticmethod
    def _routine(lock, widget, timeout, kwargs = {}):
        """
        To be executed by the separate process that displays the splash screen.
        """
        root = tk.Tk()
        splash = SplashFrame(master = root, widget = widget, **kwargs)
        start = tm.time()

        def r():
            while not \
                (lock.acquire(block = False) and \
                (tm.time() - start < timeout if timeout is not None else True)):
                tm.sleep(.01)
            lock.release()
            root.quit()

        thread = mt.Thread(name = "FC Splash Screen Watchdog", target = r,
            daemon = True)

        thread.start()
        root.mainloop()

    def __init__(self, widget, version, timeout = None, **kwargs):
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

## DEMO ########################################################################
if __name__ == '__main__':
    print("FC Splash Screen demo started")
    S = SplashHandler(FCSplashWidget, 'Demo', width = 800, height = 500,
        useFactor = False)
    S.start()
    tm.sleep(3)
    S.stop()

    print("FC Splash Screen demo finished")
