################################################################################
## Project: Fanclub Mark IV "Master"  ## File: interface.py                   ##
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
 + FC GUI Master object (instance of FCProcess).
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import time as tm
import threading as mt
import multiprocessing as mp
import tkinter as tk

import fc.process as pr
import fc.utils as us

from fc.gui import splash as spl, base as bas, profile as pro, network as ntw, \
    control as ctr

## CONSTANTS ###################################################################
SID = 2
SIGNATURE = "[GU]"
TITLE = "FC MkIV"

SPLASH_SECONDS = 3

################################################################################
class GUI(pr.FCProcess):
    sid = SID

    @staticmethod
    def routine(data):
        """
        To be executed by the child process. Runs GUI main loop. See FCProcess
        for more on DATA argument.
        """
        # Setup ................................................................
        profile, pipes, sid, pqueue = data['profile'], data['pipes'], \
            data['sid'], data['pqueue']

        P = us.printers(pqueue, SIGNATURE)
        printr, printe, printw, printd, prints, printx = \
            P[us.R], P[us.E], P[us.W], P[us.D], P[us.S], P[us.X]

        # Build GUI ............................................................
        # Splash:
        splash = spl.SplashHandler(version = "0", timeout = SPLASH_SECONDS,
            width = 750, height = 500, useFactor = False)
        st = tm.time()
        splash.start()

        # GUI:
        root = tk.Tk()
        base = bas.Base(root, title = TITLE + " " + version, version = version)

        # FIXME ----------------------------------------------------------------
        # TODO: Fix API
        mcp = tk.Button(base.getTopBar(), text = "Motion Capture")
        ter = tk.Button(base.getTopBar(), text = "Console")
        hlp = tk.Button(base.getTopBar(), text = "Help")
        base.addToTop(hlp)
        base.addToTop(ter)
        base.addToTop(mcp)

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
        # (end) FIXME ----------------------------------------------------------
        # Set up watchdog ......................................................
        lock = mt.Lock()
        def wroutine(P, L):
            """
            Watch the message pipe P for STOP signal. Terminate if L is acquired
            by the thread.
            """
            while not L.acquire(False):
                if P.poll(0):
                    message = P.recv()
                    if message is pr.STOP:
                        base.quit()
            L.release()

        watchdog = mt.Thread(name = "FCMkIV GUI watchdog", target = wroutine,
            args = (pipes[pr.MESSAGE], lock))

        # Launch ...............................................................
        # End splash screen:
        splash.join(SPLASH_SECONDS)
        # Start main loop:
        lock.acquire()
        watchdog.start()
        root.mainloop()

        # End ..................................................................
        if not lock.acquire(False):
            lock.release()

    def __init__(self, pqueue, version = ""):
        pr.FCProcess.__init__(self, pqueue, self.routine, name = "FC GUI",
            symbol = SIGNATURE, args = {'version' : version})

    def isRunnable(self):
        return True

    def usesMatrix(self):
        return True

    def usesNetwork(self):
        return True

    def usesSlaveList(self):
        return True
