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

from fc import printer as pt, utils as us
from fc.frontend import frontend as fe
from fc.frontend.gui.widgets import splash as spl, base as bas
import fc.frontend.gui.embedded.icon as icn

## GLOBALS #####################################################################
TITLE = "FC MkIV"
SPLASH_SECONDS = 4

################################################################################
class FCGUI(fe.FCFrontend):
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
        fe.FCFrontend.__init__(self, archive, pqueue)
        self.base = None

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
        base = bas.Base(self.root, self.network, self.external, self.mapper,
            self.archive, title, self.version, self.addFeedbackClient,
            self.addNetworkClient, self.addSlaveClient, self._onProfileChange,
            setLive = self.setLive, setF = self.altFeedbackIn,
            pqueue = self.pqueue)
        base.pack(fill = tk.BOTH, expand = True)
        self._setPrintMethods(base)
        self.archiveClient(base)
        self.network.connect()
        base.focusControl()

    def _mainloop(self):
        """
        Overriden. Build GUI and run main loop. See base class.
        """
        self.root.mainloop()

    def print(self, code, text):
        """
        Overriden. See fc.utils.PrintServer.
        """
        self.outputs[code](text)

    # Overriding sentinel thread implementation --------------------------------
    def _setPrintMethods(self, base):
        """
        Get the print methods from the base widgets. Placed here to keep build
        code clean.
        """
        self.outputs = {}
        self.outputs[pt.R], self.outputs[pt.W], self.outputs[pt.E], \
            self.outputs[pt.S], self.outputs[pt.D], self.outputs[pt.X] = \
            base.getConsoleMethods()
