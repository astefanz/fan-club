################################################################################
## Project: Fanclub Mark IV "Master"  ## File: gui.py                         ##
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
 + Fan Club GUI.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import time as tm
import tkinter as tk

import fc.utils as us
from fc.tkwidgets import splash as spl, base as bas, network as ntw, \
    control as ctr, profile as pro

from fc.tkwidgets.embedded import icon as icn

## CONSTANTS ###################################################################
TITLE = "FC MkIV"
SPLASH_SECONDS = 5

################################################################################
class GUI:
    symbol = "[GI]"

    @staticmethod
    def sroutine(data):
        """
        Target for the sentinel thread. Monitors pipes to process inter-process
        messages to and from this GUI.
        """
        # Setup ................................................................
        pipes,pqueue = data['pipes'],data['pqueue']

        # FIXME

    def __init__(self, pqueue, version = "", platform = us.UNKNOWN):
        """
        Initialize a new Tkinter-based FC GUI. PQUEUE is a multiprocess.Queue
        instance to be used for printing, VERSION is a string to display as
        the current software version, and PLATFORM is a constant defined in
        fc.utils (see fc.platform).
        """
        # FIXME: itf.FCInterface.__init__(self, pqueue, self.sroutine, sid = self.sid)
        self.version = version
        self.platform = platform

    def mainloop(self):
        """
        Run the main loop of the interface. Expected to block during the entire
        execution of the interface. (Returning means the interface has been
        closed.)
        """
        # FIXME: add missing behavior from Interface base class

        # Sentinel setup .......................................................
        slock = mt.Lock()
        pipes = self._pipes()

        data = {}
        data.update({'pipes': None}) # FIXME
        data.update({'pqueue': self.pqueue})
        data.update({'lock': slock})

        sentinel = mt.Thread(name = "FCI Sentinel", target = self.sroutine,
            args = (data,), daemon = True)
        slock.acquire()

        sentinel.start()

        # Fix Windows DPI ......................................................
        if self.platform is us.WINDOWS:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)


        # Build GUI ............................................................
        # Splash:
        plash = spl.SerialSplash(version = "0", width = 750, height = 500,
            useFactor = False)
        splash.run(SPLASH_SECONDS)

        # GUI:
        root = tk.Tk()

        base = bas.Base(root, title = TITLE + " " +
            self.version, version = self.version)

        # FIXME ----------------------------------------------------------------
        # TODO: Fix API


        ext = tk.Button(base.getTopBar(), text = "External Control")
        ter = tk.Button(base.getTopBar(), text = "Console")
        hlp = tk.Button(base.getTopBar(), text = "Help")
        base.addToTop(hlp)
        base.addToTop(ter)
        base.addToTop(ext)

        profile = pro.ProfileDisplay(base.getProfileTab())
        base.setProfileWidget(profile)

        network = ntw.NetworkWidget(base.getNetworkTab())
        base.setNetworkWidget(network)

        netWidget = network.getNetworkControlWidget()
        netWidget.addTarget("All", 1)
        netWidget.addTarget("Selected", 2)

        for message, code in \
            {"Add":1,"Disconnect":2,"Reboot":3, "Remove": 4}.items():
            netWidget.addMessage(message, code)

        control = ctr.ControlWidget(base.getControlTab())
        base.setControlWidget(control)

        bot = ntw.StatusBarWidget(base.getBottomFrame())
        base.setBottom(bot)

        base.pack(fill = tk.BOTH, expand = True)
        base.focusControl()
        control.grid.d()

        # Start main loop:
        root.mainloop()

        # Cleanup ..............................................................
        if not slock.acquire(False):
            slock.release()
