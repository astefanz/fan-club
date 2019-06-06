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
import tkinter as tk

import fc.utils as us
import fc.interface as it
import fc.communicator as cm
from fc.tkwidgets import splash as spl, base as bas
from fc.tkwidgets.embedded import icon as icn

## GLOBALS #####################################################################
TITLE = "FC MkIV"
SPLASH_SECONDS = 5

################################################################################
class FCGUI(it.FCInterface):
    SYMBOL = "[GI]"

    def __init__(self, archive, pqueue):
        """
        Build a new FCGUI using PQUEUE for printing and ARCHIVE (FCArchive) to
        manage profile data.
        NOTE: The Tkinter root will be created here, and hence visible without
        assembly.

        Optional argument PERIOD sets the seconds between sentinel cycles (i.e
        periodic checks to distribute inter-process data and print messages.)
        defaults to fc.interface.SENTINEL_PERIOD.
        """
        it.FCInterface.__init__(self, archive, pqueue)
        self.base = None

    def _mainloop(self):
        """
        Overriden. Build GUI and run main loop. See fc.interface.FCInterface.
        """

        # Fix Windows DPI ......................................................
        if self.platform is us.WINDOWS:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)


        # Build GUI ............................................................
        # Splash:
        splash = spl.SerialSplash(version = "0")
        splash.run(SPLASH_SECONDS)

        # GUI:
        self.root = tk.Tk()
        title = TITLE + " " + self.version
        base = bas.Base(self.root, self.network, self.external, self.archive,
            title, self.version, self.feedbackClient, self.networkClient,
            self.slaveClient, self._onProfileChange, self.pqueue)
        base.pack(fill = tk.BOTH, expand = True)
        self._setPrintMethods(base)
        self.archiveClient(base)
        self.network.connect()
        base.focusControl()

        # Main loop ------------------------------------------------------------
        self._start()
        self.root.mainloop()


    def process(self, code, text):
        """
        Overriden. See fc.utils.PrintServer.
        """
        self.outputs[code](text)

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

    def _setPrintMethods(self, base):
        """
        Get the print methods from the base widgets. Placed here to keep build
        code clean.
        """
        self.outputs = {}
        self.outputs[us.R], self.outputs[us.W], self.outputs[us.E], \
            self.outputs[us.S], self.outputs[us.D], self.outputs[us.X] = \
            base.getConsoleMethods()
