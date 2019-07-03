################################################################################
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
 + General time-sequence control GUI widget.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import os
import time as tm

import tkinter as tk
import tkinter.filedialog as fdg
import tkinter.ttk as ttk
import tkinter.font as fnt

from fc.frontend.gui import guiutils as gus
from fc.frontend.gui.widgets import grid as gd
from fc.frontend.gui.embedded import colormaps as cms

## GLOBALS #####################################################################
NOTHING = lambda: None

## CLASS #######################################################################
class TimerWidget(tk.Frame):
    DEFAULT_STEP_MS = 100
    DEFAULT_END = 0

    END_STEP, END_TIME = 0, 1

    def __init__(self, master, startF, stopF, stepF, endDCF,logstartF,logstopF):
        tk.Frame.__init__(self, master)

        # Setup:
        self.startF = startF
        self.stopF = stopF
        self.stepF = stepF
        self.endDCF = endDCF
        self.logstartF = logstartF
        self.logstopF = logstopF

        self.activeWidgets = []
        self.running = False
        self.period = self.DEFAULT_STEP_MS
        self.endType = None
        self.t0 = 0
        self.t = 0
        self.k0 = 0
        self.k = 0
        self.t_in = 0

        validateF = self.register(gus._validateF)
        validateC = self.register(gus._validateN)

        self.timeFrame = tk.Frame(self)
        self.timeFrame.pack(fill = tk.BOTH, expand = True)

        self.timeTopBar = tk.Frame(self.timeFrame)
        self.timeTopBar.pack(side = tk.TOP, fill = tk.X, expand = True)

        # Start/Stop button:
        self.startStopButton = tk.Button(self.timeTopBar, text = "Start",
            state = tk.NORMAL, command = self._start, **gus.fontc)
        self.startStopButton.pack(side = tk.LEFT)

        # Step label:
        self.stepLabel = tk.Label(self.timeTopBar, text = "   Step: ",
            **gus.fontc)
        self.stepLabel.pack(side = tk.LEFT)

        # Step field:
        validateC = self.register(gus._validateN)
        self.stepEntry = tk.Entry(self.timeTopBar, bg = 'white', width  = 6,
            **gus.efont, validate = 'key',
            validatecommand = (validateC, '%S', '%s', '%d'))
        self.stepEntry.insert(0, self.DEFAULT_STEP_MS)
        self.stepEntry.pack(side = tk.LEFT)
        self.activeWidgets.append(self.stepEntry)

        # Unit label:
        self.unitLabel = tk.Label(self.timeTopBar, text = "(ms)",
            **gus.fontc)
        self.unitLabel.pack(side = tk.LEFT)

        # End label:
        self.endLabel = tk.Label(self.timeTopBar, text = "   End: ",
            **gus.fontc)
        self.endLabel.pack(side = tk.LEFT)

        # End field:
        self.endEntry = tk.Entry(self.timeTopBar, bg = 'white', width  = 6,
            **gus.efont, validate = 'key',
            validatecommand = (validateC, '%S', '%s', '%d'))
        self.endEntry.pack(side = tk.LEFT)
        self.end = None
        self.activeWidgets.append(self.endEntry)

        self.ends = {"Step (k)":self.END_STEP, "Time (s)":self.END_TIME}
        self.endMenuVar = tk.StringVar()
        self.endMenuVar.set(tuple(self.ends.keys())[0])
        self.endMenu = tk.OptionMenu(self.timeTopBar, self.endMenuVar,
            *list(self.ends.keys()))
        self.endMenu.config(width = 10, **gus.fontc)
        self.endMenu.pack(side = tk.LEFT)
        self.activeWidgets.append(self.endMenu)

        # Timing display bar:
        self.timeDisplayBar = tk.Frame(self.timeFrame)
        self.timeDisplayBar.pack(side = tk.TOP, fill = tk.X, expand = True,
            pady = 10)

        # Index display:
        self.kLabel = tk.Label(self.timeDisplayBar, text = "  k = ",
            **gus.fontc)
        self.kLabel.pack(side = tk.LEFT)

        self.kVar = tk.IntVar()
        self.indexDisplay = tk.Entry(self.timeDisplayBar, relief = tk.SUNKEN,
            bd = 1, textvariable = self.kVar, **gus.fontc, justify = 'c',
            validate = 'key', validatecommand = (validateC, '%S', '%s', '%d'))
        self.indexDisplay.pack(side = tk.LEFT, fill = tk.X, expand = True)
        self.kVar.set(0)
        self.activeWidgets.append(self.indexDisplay)

        # Time display:
        self.tLabel = tk.Label(self.timeDisplayBar, text = "  t = ",
            **gus.fontc)
        self.tLabel.pack(side = tk.LEFT)

        self.tVar = tk.DoubleVar()
        self.timeDisplay = tk.Entry(self.timeDisplayBar, relief = tk.SUNKEN,
            bd = 1, textvariable = self.tVar, **gus.fontc, justify = 'c',
            validate = 'key', validatecommand = (validateF, '%S', '%s', '%d'))
        self.timeDisplay.pack(side = tk.LEFT, fill = tk.X, expand = True)
        self.tVar.set(0.0)
        self.activeWidgets.append(self.timeDisplay)

        # Timing control bar:
        self.timeControlBar = tk.Frame(self.timeFrame)
        self.timeControlBar.pack(side = tk.TOP, fill = tk.X, expand = True)

        # Control logging:
        self.logVar = tk.BooleanVar()
        self.logVar.set(False)
        self.logButton = tk.Checkbutton(self.timeControlBar,
            text = "Log Data", variable = self.logVar,
            indicatoron = False, padx = 10, pady = 5, **gus.fontc)
        self.logButton.pack(side = tk.LEFT, **gus.padc)
        self.activeWidgets.append(self.logButton)

        # End DC:
        self.endDCVar = tk.BooleanVar()
        self.endDCVar.set(False)
        self.endDCButton = tk.Checkbutton(self.timeControlBar,
            text = "Set DC at end: ", variable = self.endDCVar,
            indicatoron = False, padx = 10, pady = 5, **gus.fontc)
        self.endDCButton.pack(side = tk.LEFT, **gus.padc)
        self.activeWidgets.append(self.endDCButton)

        self.endDCEntry = tk.Entry(self.timeControlBar, **gus.efont, width = 6,
            validate = 'key',validatecommand = (validateF, '%S', '%s', '%d'))
        self.endDCEntry.pack(side = tk.LEFT, **gus.padc)
        self.endDCEntry.insert(0, "0")
        self.activeWidgets.append(self.endDCEntry)

        self.endDCLabel = tk.Label(self.timeControlBar, **gus.fontc,
            fg = "darkgray", text = "[0.0, 100.0]")
        self.endDCLabel.pack(side = tk.LEFT)

    def _start(self, *_):
        if not self.running:
            if self.startF():
                self.startStopButton.config(state = tk.NORMAL, text = "Stop",
                    command = self._stop)

                self.running = True

                period_raw = self.stepEntry.get()
                self.period = int(period_raw if period_raw is not None else \
                    self.DEFAULT_STEP_MS)
                self.stepEntry.delete(0, tk.END)
                self.stepEntry.insert(0, self.period)

                t_raw = self.tVar.get()
                self.t_in = float(t_raw if t_raw is not None else 0.0)
                self.tVar.set(self.t_in)

                self.t0 = tm.time()
                self.t = self.t0 + self.t_in

                k_raw = self.kVar.get()
                self.k0 = int(k_raw if k_raw is not None else 0)
                self.kVar.set(self.k0)

                self.k = self.k0
                end_raw = self.endEntry.get()

                for widget in self.activeWidgets:
                    widget.config(state = tk.DISABLED)

                if end_raw is None or len(end_raw) == 0:
                    self.end = None
                else:
                    self.end = int(end_raw)
                    self.endType = self.ends[self.endMenuVar.get()]

                if self.logVar.get():
                    self.logstartF()

                self._step()

    def _stop(self, *_):
        # FIXME:
        if self.running:
            if self.endDCVar.get():
                endDC_raw = self.endDCEntry.get()
                if endDC_raw is not None and len(endDC_raw) > 0:
                    endDC = float(endDC_raw)/100.0
                    if endDC <= 1.0 and endDC >= 0.0:
                        self.endDCF(endDC)

            if self.logVar.get():
                self.logstopF()

            self.running = False
            self.t = 0
            self.k = 0
            self.tVar.set(self.t_in)
            self.kVar.set(self.k0)
            for widget in self.activeWidgets:
                widget.config(state = tk.NORMAL)
            self.startStopButton.config(state = tk.NORMAL, text = "Start",
                command = self._start)
            self.stopF()

    def _step(self):
        """
        Complete one timestep
        """
        if self.running:
            self.kVar.set(self.k)
            self.stepF(self.t, self.k)
            self.t = self.t_in + tm.time() - self.t0
            self.tVar.set(f"{self.t:.3f}")
            self.k += 1
            if self.end is not None and \
                (self.endType == self.END_TIME and self.t > self.end or\
                self.endType == self.END_STEP and self.k > self.end):
                self._stop()
            else:
                self.after(self.period, self._step)

