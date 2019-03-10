################################################################################
## Project: Fanclub Mark IV "Master"  ## File: tkgui.py                       ##
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
 + Tkinter-based Fan Club GUI.
 +
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import multiprocessing as mp
import tkinter as tk

import fc.utils as us
import fc.interface as it
from fc.tkwidgets import splash as spl, base as bas, network as ntw, \
    control as ctr, profile as pro
from fc.tkwidgets.embedded import icon as icn

## GLOBALS #####################################################################
TITLE = "FC MkIV"
SPLASH_SECONDS = 5

SENTINEL_PERIOD = .01

################################################################################
class FCGUI(it.FCInterface):
    symbol = "[GI]"

    def __init__(self, pqueue, archive, communicator, period = SENTINEL_PERIOD):
        """
        Build a new FCGUI using PQUEUE for printing, ARCHIVE (FCArchive) and
        COMMUNNICATOR (FCCommunicator). NOTE: The Tkinter root will be
        created here, and hence visible without assembly.

        Optional argument PERIOD sets the seconds between sentinel cycles (i.e
        periodic checks to distribute inter-process data and print messages.)
        defaults to fc.interface.SENTINEL_PERIOD.
        """
        it.FCInterface.__init__(self, pqueue, archive, communicator, period)

    def _mainloop(self):
        """
        Overriden. Build GUI and run main loop. See fc.interface.FCInterface.
        """

        # FIXME: add missing behavior from Interface base class (?)

        # Fix Windows DPI ......................................................
        if self.platform is us.WINDOWS:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)


        # Build GUI ............................................................
        # Splash:
        splash = spl.SerialSplash(version = "0", width = 750, height = 500,
            useFactor = False)
        splash.run(SPLASH_SECONDS)

        # GUI:
        self.root = tk.Tk()

        base = bas.Base(self.root, title = TITLE + " " +
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

        # Start sentinels:
        self._start()

        # Main loop ------------------------------------------------------------
        self.root.mainloop()

    def process(self, code, text):
        """
        Overriden. See fc.utils.PrintServer.
        """
        # FIXME need actual implementation.
        print(us.CODE_TO_STR[code] + text)

    # Overriding sentinel thread implementation --------------------------------
    def start(self):
        """
        Overriden. Modified to do nothing so that sentinel threads can be
        started after Tkinter root has been initialized.
        """
        return

    def _start(self):
        """
        Overriden. Starts sentinel threads.
        """
        self._checkStarted()
        self.root.after(self.period_ms, self._cycle)
        self._setStarted()

    def _cycle(self):
        """
        Overriden. Executes single cycle of both print and inter-process
        sentinels.
        """

        it.FCInterface._cycle(self)
        if not self.done.is_set():
            self.root.after(self.period_ms, self._cycle)
        else:
            print(self.symbol, "Sentinels terminated")
