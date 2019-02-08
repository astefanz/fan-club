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
 + Tkinter-based FC GUI.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import time as tm
import tkinter as tk

import fc.interface as itf
import fc.utils as us
from fc.tkwidgets import splash as spl, base as bas, network as ntw, \
    control as ctr, profile as pro

from fc.tkwidgets.embedded import icon as icn

## CONSTANTS ###################################################################
SID = 2
SIGNATURE = "[GI]"
TITLE = "FC MkIV"

SPLASH_SECONDS = 3

################################################################################
class GUI(itf.FCInterface):
    sid = SID

    @staticmethod
    def sroutine(data):
        """
        Target for the sentinel thread. Monitors pipes to process inter-process
        messages to and from this GUI.
        """
        # Setup ................................................................
        pipes,pqueue = data['pipes'] ,  data['pqueue']

        P = us.printers(pqueue, SIGNATURE)
        printr, printe, printw, printd, prints, printx = \
            P[us.R], P[us.E], P[us.W], P[us.D], P[us.S], P[us.X]

        # FIXME

    def __init__(self, pqueue, version = ""):
        itf.FCInterface.__init__(self, pqueue, self.sroutine, sid = self.sid)
        self.version = version

    def _mainloop(self):
        # Build GUI ............................................................
        # Splash:
        splash = spl.SerialSplash(version = "0", width = 750, height = 500,
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
