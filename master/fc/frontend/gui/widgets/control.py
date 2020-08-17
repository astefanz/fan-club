################################################################################
## Project: Fanclub Mark IV "Master" GUI          ## File: control.py         ##
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
 + Graphical interface for the FC array control tools.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

# TODO:
# - Display table? (give to control panel as another display)

# TODO ON REVISED I-P STANDARD:
# - for grid, use MAC addresses to create mapping as indices arrive from
# network. After that, for new boards, only the total number of fans is needed.
# NOTE: or... is it? after all, the DC offset will always be half the array,
# and saved slaves are guaranteed to always keep the lower indices

## IMPORTS #####################################################################
import os
import time as tm
import random as rd
import multiprocessing as mp
import copy as cp

import math
import random
from math import *
from random import *

import tkinter as tk
import tkinter.filedialog as fdg
import tkinter.ttk as ttk
import tkinter.font as fnt

from fc import archive as ac, printer as pt, standards as std, utils as us
from fc.backend import mapper as mr

from fc.frontend.gui import guiutils as gus
from fc.frontend.gui.embedded import colormaps as cms
from fc.frontend.gui.widgets import grid as gd, loader as ldr, timer as tmr, \
    external as ex

## GLOBALS #####################################################################
P_TIME = 't'
P_ROW, P_COLUMN, P_LAYER = 'r', 'c', 'l'
P_DUTY_CYCLE = 'd'
P_RPM = 'p'
P_MAX_RPM = 'P'
P_ROWS, P_COLUMNS, P_LAYERS = 'R', 'C', 'L'
P_INDEX, P_FAN = 's', 'f'
P_INDICES, P_FANS = 'S', 'F'
P_STEP = 'k'

## MAIN WIDGET #################################################################
class ControlWidget(tk.Frame, pt.PrintClient):
    """
    Container for all the FC control GUI front-end widgets.
    """
    SYMBOL = "[CW]"

    def __init__(self, master, network, external, mapper, archive, pqueue,
        setLiveBE, setFBE):
        tk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

        self.archive = archive
        self.network = network
        self.external = external
        self.mapper = mapper
        self.setLiveBE, self.setFBE = setLiveBE, setFBE

        self.S_buffer = None
        self.N_buffer = None

        self.main = ttk.PanedWindow(self, orient = tk.HORIZONTAL)
        self.main.pack(fill = tk.BOTH, expand = True)

        self.displayFrame = tk.Frame(self.main)
        self.displays = []

        self.controlFrame = tk.Frame(self.main)
        self.control = None

        self.isLive = None
        self.maxRPM = None

        self._build()

        self.main.add(self.controlFrame, weight = 2)
        self.main.add(self.displayFrame, weight = 16)

    def redraw(self):
        """
        Rebuild widgets.
        """
        self.display.redraw()

    def feedbackIn(self, F, simulated = False):
        """
        Process a new feedback vector.
            - F := feedback vector to process.
            - simulated := whether this is a fake feedback vector to display
                when in flow builder mode. Defaults to False.
        """
        if self.isLive and not simulated:
            self.display.feedbackIn(F)
            self.control.feedbackIn(F)
        elif not self.isLive and simulated:
            self.display.feedbackIn(F)
            self.control.feedbackIn(F)
            self.setFBE(F)

    def slavesIn(self, S):
        """
        Process a new slaves vector.
        """
        self.S_buffer = S
        if self.isLive:
            self.display.slavesIn(S)
            self.control.slavesIn(S)

    def networkIn(self, N):
        """
        Process a new network vector.
        """
        self.N_buffer = N
        if self.isLive:
            self.display.networkIn(N)

    def blockAdjust(self):
        """
        Deactivate automatic adjustment of widgets upon window resizes.
        """
        self.display.blockAdjust()

    def unblockAdjust(self):
        """
        Activate automatic adjustment of widgets upon window resizes.
        """
        self.display.unblockAdjust()

    def _setLive(self, live, redundance = 0):
        """
        Set feedback display mode.
            - live := whether in live display mode (True) or in flow builder
                mode (False).
        """
        self.isLive = live
        self.setLiveBE(live)
        if self.isLive:
            if self.N_buffer is not None:
                self.display.networkIn(self.N_buffer)
            else:
                self.printw("No network state buffered when switching to Live")
            if self.S_buffer is not None:
                self.display.slavesIn(self.S_buffer)
            else:
                self.printw("No slave state buffered when switching to Live")
        else:
            self.display.activate()
            self.feedbackIn(self._emptyFeedback(), simulated = True)

    def _build(self):
        """
        Build sub-widgets.
        """
        self.maxRPM = self.archive[ac.maxRPM]
        self._buildDisplays()
        self._buildControl()
        self._setLive(True)

    def _buildControl(self):
        """
        Build control pane.
        """
        if self.control is not None:
            self.control.destroy()
            self.control = None
        self.control = ControlPanelWidget(self.controlFrame, self.mapper,
            self.archive, self.network, self.external, self.display,
            self._setLive, self.pqueue)
        self.control.pack(fill = tk.BOTH, expand = True)

    def _buildDisplays(self):
        """
        Build the interactive display widgets.
        """
        if self.displays:
            for display in self.displays:
                display.destroy()
            self.display.destroy()
        self.displays = []

        self.display = DisplayMaster(self.displayFrame, self.pqueue)
        self.display.pack(fill = tk.BOTH, expand = True)

        # Grid:
        self.grid = GridWidget(self.display, self.archive,
            self.mapper, self._send, pqueue = self.pqueue)
        self.display.add(self.grid, text = "Control Grid")
        self.displays.append(self.grid)
        self.external.setController(self.grid)

        # Live table
        self.table = LiveTable(self.display, self.archive, self.mapper,
            self._send, self.network, pqueue = self.pqueue)
        self.display.add(self.table, text = "Live Table")
        self.displays.append(self.table)

    def _send(self, C):
        if self.isLive:
            self.network.controlIn(C)
        else:
            self.feedbackIn(self._buildFlow(C), True)

    def _buildFlow(self, C):
        """
        Build and return a simulated flow to feed back to the display widgets.
            - C := Control vector
        """
        F = [0]*len(C)
        for i, dc in enumerate(C):
            F[i] = int(dc*self.maxRPM)
        return F + C

    def _emptyFeedback(self):
        """
        Build a zeroed-out feedback vector based on the current profile.
        """
        return [0]*self.archive[ac.maxFans]*len(self.archive[ac.savedSlaves])*2

    def profileChange(self):
        """
        Handle a change in the loaded profile.
        """
        self._build()

## WIDGETS #####################################################################
class PythonInputWidget(tk.Frame):
    """
    Base class for a widget for Python code input.
    """
    SYMBOL = "[PI]"

    WARNING = "NOTE: Scripts use zero-indexing"
    HEADER = "def duty_cycle({}):"
    FOOTER = "self.func = duty_cycle"

    IMPORTS = "math", "random"

    PARAMETERS = (P_ROW, P_COLUMN, P_LAYER, P_INDEX, P_FAN, P_DUTY_CYCLE, P_RPM,
        P_ROWS, P_COLUMNS, P_LAYERS, P_INDICES, P_FANS, P_MAX_RPM,P_TIME,P_STEP)


    def __init__(self, master, callback, pqueue):
        """
        Create a Python input widget in which the user may define a function
        to be mappeded throughout the array.

        CALLBACK is a method to which to pass the resulting Python function
        after being parsed and instantiated, as well as the current time step.
        """
        tk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

        self.parameters = self.PARAMETERS
        self._buildSignature()

        self.callback = callback

        self.interactive = []

        self.grid_columnconfigure(1, weight = 1)
        row = 0

        self.noteLabel = tk.Label(self, font = "Courier 7 bold",
            text = self.WARNING, fg = "orange", anchor = tk.W)
        self.noteLabel.grid(row = row, column = 0, columnspan = 2, sticky = "EW")
        row += 1
        self.topLabel = tk.Label(self, font = "Courier 6 bold",
            text = self.signature, anchor = tk.W)
        self.topLabel.grid(row = row, column = 0, columnspan = 2, sticky = "EW")
        row += 1

        self.font = tk.font.Font(font = "Courier 7 bold")
        self.tabstr = "  "
        self.tabsize = self.font.measure(self.tabstr)
        self.realtabs = "    "

        self.indent = tk.Label(self, font = self.font, text = self.tabstr)
        self.indent.grid(row = row, column = 0, sticky = "NS")

        self.text = tk.Text(self, font = self.font,
            width = 30, height = 2, padx = 10, pady = 0, bg = 'white',
            fg = 'black', insertbackground = "#ff6e1f",
            tabs = self.tabsize)
        self.text.grid(row = row, column = 1, rowspan = 2, sticky = "NEWS")
        self.grid_rowconfigure(row, weight = 1)
        self.interactive.append(self.text)

        # For scrollbar, see:
        # https://www.python-course.eu/tkinter_text_widget.php

        self.scrollbar = tk.Scrollbar(self)
        self.scrollbar.grid(row = row, column = 2, rowspan = 1,
            sticky = "NS")
        self.scrollbar.config(command = self.text.yview)
        self.text.config(yscrollcommand = self.scrollbar.set)
        row += 1

        self.buttonFrame = tk.Frame(self)
        self.buttonFrame.grid(row = row, column = 0, columnspan = 2,
            sticky = "WE")

        # TODO
        self.runButton = tk.Button(self.buttonFrame, text = "Apply Statically",
            command = self._run, **gus.padc, **gus.fontc)
        self.runButton.pack(side = tk.LEFT, **gus.padc)
        self.interactive.append(self.runButton)

        self.loader = ldr.LoaderWidget(self.buttonFrame,
            filetypes = (("Fan Club Python Procedures", ".fcpy"),),
            onSave = self._onSave, onLoad = self._onLoad)
        self.loader.pack(side = tk.LEFT)

        # Wrap-up:
        self.func = None

    # API ......................................................................
    def enable(self):
        """
        Enable buttons and fields.
        """
        self.loader.enable()
        for widget in self.interactive:
            widget.config(state = tk.NORMAL)

    def disable(self):
        """
        Block all interactive components
        """
        self.loader.disable()
        for widget in self.interactive:
            widget.config(state = tk.DISABLED)

    def flat(self):
        """
        Get a "flat" (replace newline by semicolon) version of the currently
        written function.
        """
        body = self.text.get("1.0", tk.END)
        while '\n' in body:
            body = body.replace('\n', ";")
        return body

    def get(self, *_):
        """
        Parses and returns current function. Returns None if the input field is
        left blank
        """
        return self._parse()

    # Internal methods .........................................................
    def _parse(self):
        """
        Parse and return the current function.
        """
        raw = self.text.get(1.0, tk.END)
        if len(raw) < len("return"):
            print("Too short") # FIXME DEBUG
            return None
        retabbed = raw.replace('\t', self.realtabs)

        built = self.signature + '\n'
        """
        for imported in self.IMPORTS:
            built += self.realtabs + "import {}\n".format(imported)
        """ # FIXME test
        for line in retabbed.split('\n'):
            built += self.realtabs + line + '\n'
        built += self.FOOTER + '\n'

        exec(built) # TODO: fix security hole in exec
        # Function is stored in self.func
        return self.func

    def _run(self, *_):
        """
        To be called when the Run button is clicked. Parse the function and
        pass it to the given callback.
        """
        try:
            self._parse()
            if self.func is not None:
                self.callback(self.func, 0, 0)

        except Exception as e:
            self.printx(e, "Exception when parsing Python input:")

    def _buildSignature(self):
        """
        Build the function signature to be consistent with the
        current value of the stored parameter list.
        """
        self.signature = self.HEADER.format(
            ("{}, "*len(self.parameters)).format(*self.parameters)[:-2])

    def _onLoad(self, loaded):
        """
        To be executed by the Load routine within a LoaderWidget.
        """
        if loaded is not None:
            body, filename = loaded
            self.printr("Loaded FC Python function \"{}\"".format(filename))
            self.text.delete('1.0', tk.END)
            self.text.insert('1.0', body)
            # See: https://stackoverflow.com/questions/27966626/
            #   how-to-clear-delete-the-contents-of-a-tkinter-text-widget

    def _builtin(self, *E):
        """
        To be executed by the Built-in button.
        """
        print("[WARNING] _builtin not implemented ")

    def _onSave(self, *E):
        """
        To be executed by the Save routine within a LoaderWidget.
        """
        return self.text.get('1.0', tk.END)

    def _help(self, *E):
        """
        To be executed by Help button.
        """
        print("[WARNING] _help not implemented ")

class MainControlWidget(tk.Frame, pt.PrintClient):
    """
    Container for the steady flow control tools.
    """
    SYMBOL = "[SC]"
    SLIDER_MIN = 0
    SLIDER_MAX = 100

    FT_ROW, FT_COL, FT_TV, FT_GNLOG, FT_GDLOG = 0, 1 ,2 ,3, 5
    FT_LIST =4 # FIXME temp
    FILETYPES = (
        ("Row (,)", FT_ROW),
        ("Column (\\n)", FT_COL),
        ("t, val", FT_TV),
        ("Log (gen)", FT_GNLOG),
        ("Log (grid)", FT_GDLOG),
    )


    def __init__(self, master, network, display, logstart, logstop,  pqueue):
        tk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

        # Setup ................................................................
        self.network = network
        self.display = display

        self.logstart, self.logstop = logstart, logstop

        self.grid_columnconfigure(0, weight = 1)
        row = 0
        self.loadedFlow = None
        self.flowType = None
        self.values = None
        self.n = None
        self.times = None
        self.tmax = 0
        self.activeWidgets = []

        # Callbacks:
        self.selectAll = self._nothing
        self.deselectAll = self._nothing

        self.simpleFrame = tk.Frame(self)
        self.simpleFrame.grid(row = row, sticky = "EW")
        row += 1

        # Direct input .........................................................
        self.directFrame = tk.LabelFrame(self.simpleFrame,
            text = "Direct input", **gus.lfconf)
        self.directFrame.pack(side = tk.LEFT, fill = tk.X, expand = True)

        self.directValueEntry = tk.Entry(self.directFrame, **gus.efont,
            width = 6)
        self.directValueEntry.pack(side = tk.LEFT, **gus.padc)
        # FIXME validate
        self.sendDirectButton = tk.Button(self.directFrame, text = "Apply",
            **gus.padc, **gus.fontc, command = self._onSendDirect)
        self.sendDirectButton.pack(side = tk.LEFT, **gus.padc)
        self.activeWidgets.append(self.directValueEntry)
        self.activeWidgets.append(self.sendDirectButton)

        # FIXME keyboard bindings

        # Random flow ..........................................................
        self.randomFrame = tk.LabelFrame(self.simpleFrame, text = "Random Flow",
            **gus.lfconf)
        self.randomFrame.pack(side = tk.LEFT, fill = tk.X, expand = True)

        self.leftB = tk.Label(self.randomFrame, text = "[", **gus.fontc)
        self.leftB.pack(side = tk.LEFT)

        # FIXME validate
        self.randomLow = tk.Entry(self.randomFrame, **gus.fontc, width = 5)
        self.randomLow.pack(side = tk.LEFT)
        self.randomLow.insert(0, "0")
        self.activeWidgets.append(self.randomLow)

        self.comma = tk.Label(self.randomFrame, text = ", ", **gus.efont)
        self.comma.pack(side = tk.LEFT)

        # FIXME validate
        self.randomHigh = tk.Entry(self.randomFrame, **gus.efont, width = 5)
        self.randomHigh.pack(side = tk.LEFT)
        self.randomHigh.insert(0, "100")
        self.activeWidgets.append(self.randomHigh)

        self.rightB = tk.Label(self.randomFrame, text = "]", **gus.fontc)
        self.rightB.pack(side = tk.LEFT)

        self.sendRandomButton = tk.Button(self.randomFrame, text = "Apply",
            **gus.padc, **gus.fontc, command = self._sendRandom)
        self.sendRandomButton.pack(side = tk.LEFT, **gus.padc)
        self.activeWidgets.append(self.sendRandomButton)

        # Slider ...............................................................
        self.sliderFrame = tk.LabelFrame(self, text = "Slider",
            **gus.lfconf)
        self.sliderFrame.grid(row = row, sticky = "EW")
        row += 1

        # Slider:
        self.slider = tk.Scale(self.sliderFrame, from_ = 0, to = 100,
            command = lambda s: self._sendDirect(float(s)),
            orient = tk.HORIZONTAL)
        self.slider.pack(side = tk.TOP, fill = tk.X, expand = True)
        self.activeWidgets.append(self.slider)

        # Quick duty cycles:
        self.quickDCButtons = []
        self.quickDCFrame = tk.Frame(self.sliderFrame)
        self.quickDCFrame.pack(side = tk.TOP, fill = tk.X, expand = True)
        for dc in [0, 10, 20, 30, 50, 70, 80, 90, 100]:
            button = tk.Button(self.quickDCFrame, text = "{:3d}%".format(dc),
                command = self._quickDCCallback(dc/100),
                padx = 0, font = "TkFixedFont 6" \
                + (" bold" if dc in (0, 50, 100) else ""))
            button.pack(side = tk.LEFT, fill = tk.X, expand = True)
            self.quickDCButtons.append(button)
            self.activeWidgets.append(button)

        # Padding row:
        self.grid_rowconfigure(row, weight = 2)
        row += 1

        # Load Flows ...........................................................
        self.flowFrame = tk.LabelFrame(self, text = "Load Flow",**gus.lfconf)
        self.flowFrame.grid(row = row, sticky = "EW")
        row += 1

        self.flowLoaderFrame = tk.Frame(self.flowFrame)
        self.flowLoaderFrame.pack(side = tk.TOP, fill = tk.X, expand = True)
        self.flowLoader = ldr.FlowLoaderWidget(self.flowLoaderFrame,
            self._onLoad)
        self.flowLoader.pack(side = tk.LEFT)
        self.activeWidgets.append(self.flowLoader)

        self.fileLabel = tk.Label(self.flowLoaderFrame, text = "File: ",
            **gus.fontc, **gus.padc)
        self.fileLabel.pack(side = tk.LEFT)
        self.fileField = tk.Entry(self.flowLoaderFrame, **gus.fontc, width = 20,
            state = tk.DISABLED)
        self.fileField.pack(side = tk.LEFT, fill = tk.X, expand = True)
        self.fileTypeLabel = tk.Label(self.flowLoaderFrame, text = "Type: ",
            **gus.fontc, **gus.padc)
        self.fileTypeLabel.pack(side = tk.LEFT)

        self.fileTypes = {"List": self.FT_LIST, "t vs U" : self.FT_TV,
            #"log-u" : self.FT_LGU, "log-g" : self.FT_LGG FIXME implement
            }
        self.typeMenuVar = tk.StringVar()
        self.typeMenuVar.trace('w', self._onTypeMenuChange)
        self.typeMenuVar.set(tuple(self.fileTypes.keys())[0])
        self.typeMenu = tk.OptionMenu(self.flowLoaderFrame, self.typeMenuVar,
            *list(self.fileTypes.keys()))
        self.typeMenu.config(width = 6, **gus.fontc)
        self.typeMenu.pack(side = tk.LEFT)
        self.activeWidgets.append(self.typeMenu)

        # TODO:
        # - start/stop
        # - display
        # - tstep
        self.timer = tmr.TimerWidget(self.flowFrame,
            startF = self._startFlow,
            stopF = self._stopFlow,
            stepF = self._stepF,
            endDCF = lambda dc:self._sendDirect(dc, False),
            logstartF = self.logstart,
            logstopF = self.logstop)
        self.timer.pack(side = tk.TOP, fill = tk.X, expand = True)
    # API ......................................................................


    # Internal methods .........................................................
    def _onSendDirect(self, *_):
        """
        Callback for direct send button.
        """
        try:
            self._sendDirect(float(self.directValueEntry.get()), True)
        except Exception as e:
            self.printx(e, "Exception when sending direct DC")

    def _sendDirect(self, dc, normalize = True):
        """
        Send a "direct input" command using the given send callback.
            - dc := duty cycle to send as float in [0, 100] if normalize is True
                or in [0, 1] if normalize is False.
            - normalize := bool, whether to divide dc by 100.
        """
        normalized = dc/100 if normalize else dc
        self.display.set(normalized)

    def _sendRandom(self, *_):
        """
        Send a randomly-generated magnitude command using the given send
        callback.
        """
        try:
            minDC, maxDC = \
                float(self.randomLow.get()), float(self.randomHigh.get())
            if maxDC < minDC:
                raise ValueError("Upper bound ({maxDC:d}) cannot be "\
                    " smaller than lower ({minDC:d})")
            def f(*_):
                return ((rd.random()*(maxDC - minDC) + minDC))/100
            self.display.map(f, 0, 0)

        except Exception as e:
            self.printx(e, "Exception while processing random DC")

    def _setSliderMax(self, *_):
        """
        Callback for the slider's "Max" button.
        """
        self._sendDirect(self.SLIDER_MAX)

    def _setSliderMin(self, *_):
        """
        Callback for the slider's "Min" button.
        """
        self._sendDirect(self.SLIDER_MIN)

    def _quickDCCallback(self, dc):
        """
        Build a callback to apply the given duty cycle.
        - dc: float, in [0.0, 1.0] to apply when called.
        """
        def callback(*_):
            self._sendDirect(dc, normalize = False)
        return callback

    def _startFlow(self):
        try:
            if self.loadedFlow is not None and self._parseFlow():
                # TODO prepare (disable widgets, etc)
                self._setActiveWidgets(tk.DISABLED)
                return True
            else:
                return False
        except Exception as e:
            self.printx(e, "Exception while starting loaded flow")
            return False

    def _stepF(self, t, k):
        """
        To be called on each step of the flow loader.
        """
        # Process step:
        if self.flowType == self.FT_LIST:
            self.display.set(self.values[min(k, self.n - 1)])
        elif self.flowType == self.FT_TV:
            dc = self._getInterpolatedDC(t)
            print(t, dc)
            self._sendDirect(dc, False)
        else:
            self.printe("Flow type unavailable")
        # Check for stop or continue condition:

    def _stopFlow(self):
        """
        Callback to stop the loaded flow.
        """
        self.values = None
        self.times = None
        self.tmax = 0
        self._setActiveWidgets(tk.NORMAL)

    def _onTypeMenuChange(self, *_):
        self.flowType = self.fileTypes[self.typeMenuVar.get()]

    def _setActiveWidgets(self, state):
        """
        Set all interactive widgets to the given state (either tk.DISABLED or
        tk.NORMAL)
        """
        for widget in self.activeWidgets:
            widget.config(state = state)

    def _onLoad(self, loaded):
        """
        Load callback for FlowLoader.
        """
        if loaded is not None:
            data, filename = loaded
            self.loadedFlow = data
            self.fileField.config(state = tk.NORMAL)
            self.fileField.delete(0, tk.END)
            self.fileField.insert(0, filename.split("/")[-1].split("\\")[-1])
            self.fileField.config(state = tk.DISABLED)

    def _parseFlow(self):
        """
        Extract data from the loaded flow for execution and return whether such
        extraction was successful or not (as bool).
        """

        try:
            if self.flowType == self.FT_LIST:
                values_raw = eval("[" + self.loadedFlow  +"]")
                self.n = len(values_raw)

            elif self.flowType == self.FT_TV:
                lines = self.loadedFlow.split("\n")
                self.n = len(lines)
                self.times, values_raw = [0]*self.n, [0]*self.n
                for i, line in enumerate(lines):
                    if len(line) > 0:
                        time, value = line.split(",")
                        self.times[i], values_raw[i] = float(time),float(value)
                self.tmax = max(self.times)
            else:
                raise RuntimeError("Loaded flow type not available") # TODO

            # Normalize and store extracted values:
            normalize = False
            for value in values_raw:
                if value > 1.0:
                    normalize = True
                    break
            if normalize:
                values_max = max(values_raw)
                self.values = list(map(lambda v: v/values_max, values_raw))
            else:
                self.values = values_raw

            print(self.times) # FIXME debug
            return True

        except Exception as e:
            self.printx(e, "Exception while parsing flow")
            return False

    def _getInterpolatedDC(self, t):
        """
        Interpolate a duty cycle from the loaded flow's values and times
        list, using the current timestamp.
        """
        # Handle out-of-range cases:
        if t <= self.times[0]:
            return self.values[0]
        elif t >= self.tmax:
            return self.values[-1]

        # Find nearest timestamp:
        # Find nearest time:
        i, ti = 0, self.times[0]
        while t > ti and i < self.n:
            i += 1
            ti = self.times[i]
        t0 = self.times[i - 1]
        v0, vi = self.values[i-1], self.values[i]

        # Interpolate a weighted average of the two values:
        p = (ti - t)/(ti - t0)
        dc =  (v0*p + vi*(1 - p))
        return dc

    @staticmethod
    def _nothing(*_):
        """
        Placeholder function to serve as a default callback.
        """
        pass

class FunctionControlWidget(tk.Frame, pt.PrintClient):
    """
    Container for the dynamic flow control tools.
    """
    SYMBOL = "[DC]"
    DEFAULT_STEP_MS = 1000
    DEFAULT_END = ""

    def __init__(self, master, display, logstart, logstop, pqueue):
        tk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

        self.display = display
        self.logstart, self.logstop = logstart, logstop

        self.grid_columnconfigure(0, weight = 1)
        row = 0

        self.activeWidgets = []

        # Python interpreter ...................................................
        self.grid_rowconfigure(row, weight = 1)
        self.pythonFrame = tk.LabelFrame(self, text = "Python",
            **gus.lfconf)
        self.pythonFrame.grid(row = row, sticky = "NEWS")
        row += 1
        self.python = PythonInputWidget(self.pythonFrame, self._applyFunction,
            pqueue)
        self.flat = self.python.flat
        self.python.pack(fill = tk.BOTH, expand = True)

        # Timing ...............................................................
        self.timeFrame = tk.LabelFrame(self, text = "Time Series",
            **gus.lfconf)
        self.timeFrame.grid(row = row, sticky = "EW")
        row += 1

        self.timer = tmr.TimerWidget(self.timeFrame,
            startF = self._start,
            stopF = self._stop,
            stepF = self._step,
            endDCF = self.display.set,
            logstartF = self.logstart,
            logstopF = self.logstop)
        self.timer.pack(fill = tk.X, expand = True)

        # Wrap-up:
        self.f = None
        self.widget = None

    def _applyFunction(self, f, t, k):
        """
        To be called by the Python input widget to apply its function once.
        """
        self._stop()
        if f is not None:
            self.f = f
            self.display.map(f, t, k)

    def _start(self, *_):
        self.f = self.python.get()
        if self.f is not None:
            self.widget = self.display.currentWidget()
            self.python.disable()
            for widget in self.activeWidgets:
                widget.config(state = tk.DISABLED)
            return True
        else:
            return False

    def _stop(self, *_):
        self.widget = None
        self.python.enable()
        self.f = None
        for widget in self.activeWidgets:
            widget.config(state = tk.NORMAL)


    def _step(self, t, k):
        """
        Complete one timestep
        """
        self.widget.map(self.f, t, k)


class BuiltinFlow:
    """
    Data structure for pre-built flows.
    """

    PTYPE_GRID, PTYPE_TABLE = range(2)
    ATTR_INT, ATTR_INT_NONNEG, ATTR_INT_POS, ATTR_FLOAT_NONNEG, ATTR_FLOAT_POS,\
    ATTR_BOOL = range(6)


    def __init__(self, name, description, source, ptype, attributes):
        """
        Build a new data structure to contain the data for a built-in flow.

        - name: str, name to display to the user to refer to this flow.
        - description: str, description to display to the user about this flow.
        - source: str, python code to be plugged into the FC Python interpreter.
        - ptype: int, predefined constant (as a class attribute) that indicates
            the kind of parameters the flow's function takes (either those in
            the Grid or in the LiveTable).
        - attributes: dict, mapping from attribute names (str) to their format
            as a corresponding constant as defined in this class' attributes.
        """
        self.name, self.description = name, description
        self.source, self.ptype, self.attributes = source, ptype, attributes

class FlowLibraryWidget(tk.Frame, pt.PrintClient):
    """
    Container for built-in flows.
    """

    def __init__(self, master, flows, display, pqueue):
        tk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)
        # Setup:
        self.flows = flows
        self.display = display

        self.interactive = []

        LIST_ROW, LIST_COLUMN = 0, 0
        HSCROLL_ROW, HSCROLL_COLUMN = LIST_ROW + 1, LIST_COLUMN
        VSCROLL_ROW, VSCROLL_COLUMN = LIST_ROW, LIST_COLUMN + 1
        DESC_ROW, DESC_COLUMN = HSCROLL_ROW + 1, LIST_COLUMN
        ATTR_ROW, ATTR_COLUMN = DESC_ROW + 1, DESC_COLUMN
        ASCROLL_ROW, ASCROLL_COLUMN = ATTR_ROW, ATTR_COLUMN + 1
        CTRL_ROW, CTRL_COLUMN = ATTR_ROW + 1, ATTR_COLUMN

        self.grid_columnconfigure(LIST_COLUMN, weight = 1)
        self.grid_rowconfigure(ATTR_ROW, weight = 1)

        # TODO
        # Flow list ............................................................
        self.list = ttk.Treeview(self, height = 5)
        self.list.grid(row = LIST_ROW, column = LIST_COLUMN,
            sticky = "NEW")
        # Add columns:
        self.columns = ("Built-in Flows",)
        self.list['columns'] = self.columns
        self.list.column("#0", width = 20, stretch = False)
        for column in self.columns:
            self.list.column(column, anchor = "center")
            self.list.heading(column, text = column)
        # Build scrollbars:
        # See: https://lucasg.github.io/2015/07/21/
        #    How-to-make-a-proper-double-scrollbar-frame-in-Tkinter/
        self.hscrollbar = ttk.Scrollbar(self, orient = tk.HORIZONTAL)
        self.hscrollbar.config(command = self.list.xview)
        self.hscrollbar.grid(row = HSCROLL_ROW,
            column = HSCROLL_COLUMN, sticky = "EW")
        self.vscrollbar = ttk.Scrollbar(self, orient = tk.VERTICAL)
        self.vscrollbar.config(command = self.list.yview)
        self.vscrollbar.grid(row = VSCROLL_ROW,
            column = VSCROLL_COLUMN, sticky = "NS")

        # Build description display
        self.descriptionFrame = tk.LabelFrame(self, text = "About",
            **gus.fontc)
        self.descriptionFrame.grid(row = DESC_ROW, column = DESC_COLUMN,
            sticky = "NEWS", columnspan = 2)
        self.descriptionFrame.grid_columnconfigure(0, weight = 1)

        self.nameDisplay = tk.Label(self.descriptionFrame, anchor = tk.W,
            relief =tk.SUNKEN, bd = 1)
        self.nameDisplay.grid(row = 0, column = 0, sticky = "EW")

        self.descriptionDisplay = tk.Text(self.descriptionFrame,
            width = 30, height = 2, padx = 10, pady = 0,
            bg = 'darkgray', fg = 'black', insertbackground = "#ff6e1f",
            state = tk.DISABLED)
        self.descriptionDisplay.grid(row = 1, column = 0, sticky = "NEWS")

        self.dscrollbar = ttk.Scrollbar(self.descriptionFrame,
            orient = tk.VERTICAL)
        self.dscrollbar.config(command = self.descriptionDisplay.yview)
        self.dscrollbar.grid(row = 1, column = 1, sticky = "NS")

        # Build attribute menu NOTE: add scrollbar
        self.attributeFrame = tk.LabelFrame(self, text = "Configure Flow",
            **gus.fontc)
        self.attributeFrame.grid(row = ATTR_ROW, column = ATTR_COLUMN,
            sticky = "NEWS")

        self.attributeDisplay = tk.Frame(self.attributeFrame)
        self.attributeDisplay.pack(fill = tk.BOTH, expand = True)

        self.ascrollbar = ttk.Scrollbar(self, orient = tk.VERTICAL)
        #self.ascrollbar.config(command = self.attributeDisplay.yview) FIXME
        self.ascrollbar.grid(row = ASCROLL_ROW, column = ASCROLL_COLUMN,
            sticky = "NS")


        # Build control
        self._apply = lambda: None # FIXME
        self.controlFrame = tk.LabelFrame(self, text = "Control", **gus.fontc)
        self.controlFrame.grid(row = CTRL_ROW, column = CTRL_COLUMN,
            sticky = "NEWS", columnspan = 2)
        self.applyButton = tk.Button(self.controlFrame, text = "Apply",
            command = self._apply, **gus.fontc)
        self.applyButton.pack(side = tk.TOP, fill = tk.X, expand = True)

        # FIXME temp
        self._startFlow = lambda: None
        self._stopFlow = lambda: None
        self._stepF = lambda: None
        self._sendDirect = lambda: None
        self.logstart = lambda: None
        self.logstop = lambda: None

        self.timer = tmr.TimerWidget(self.controlFrame,
            startF = self._startFlow,
            stopF = self._stopFlow,
            stepF = self._stepF,
            endDCF = lambda dc:self._sendDirect(dc, False),
            logstartF = self.logstart,
            logstopF = self.logstop)
        self.timer.pack(side = tk.TOP, fill = tk.X, expand = True)

        # Add flows
        for category, name in flows:
            self.add(flow, category)

    # API ......................................................................
    def add(self, flow: BuiltinFlow, category: str):
        """
        Add a flow to the library.
        """
        # TODO
        pass

    def config(self, state):
        """
        Set the state of all interactive widgets.
        - state := Tkinter constant, one of tk.NORMAL and tk.DISABLED.
        """
        for widget in self.interactive:
            widget.config(state = state)
    # FIXME

class ControlPanelWidget(tk.Frame, pt.PrintClient):
    """
    Container for the control GUI tools and peripherals.
    """
    SYMBOL = "[CP]"

    """ Codes for display modes. """
    DM_LIVE = 690
    DM_BUILDER = 691

    def __init__(self, master, mapper, archive, network, external, display,
        setLive, pqueue):
        tk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

        # Setup ................................................................
        self.mapper = mapper
        self.archive = archive
        self.network = network
        self.externalBackEnd = external
        self.display = display
        self.setLive = setLive
        self.grid_columnconfigure(0, weight = 1)
        row = 0

        self.F = fnt.Font(family = 'TkDefaultFont', size = 7)
        self.S = ttk.Style()
        self.S.configure('.', font = self.F)
        self.activeWidgets = []
        self.filename = None
        self.fullname = None
        self.inWindows = self.archive[ac.platform] == us.WINDOWS

        # TODO: Callbacks and validations

        # Mode and layer .......................................................
        self.topFrame = tk.Frame(self)
        self.topFrame.grid(row = row, sticky = "EW")
        row += 1

        self.viewFrame = tk.LabelFrame(self.topFrame, text = "View",**gus.fontc,
            padx = 10)
        self.viewFrame.pack(side = tk.LEFT, fill = tk.BOTH, expand = True)

        self.viewVar = tk.IntVar()
        self.viewVar.trace('w', self._onModeChange)
        self.liveButton = tk.Radiobutton(self.viewFrame,
            variable = self.viewVar, value = self.DM_LIVE, text = "Live",
            **gus.rbconf)
        self.liveButton.pack(side = tk.TOP, padx = 5, fill = tk.X,
            expand = True)
        self.builderButton = tk.Radiobutton(self.viewFrame,
            variable = self.viewVar, value = self.DM_BUILDER,
            text = "Preview", **gus.rbconf)
        self.builderButton.pack(side = tk.TOP, padx = 5, fill = tk.X,
            expand = True)

        # Selection ............................................................
        self.selectFrame = tk.LabelFrame(self.topFrame, text = "Select",
            **gus.fontc, padx = 10)
        self.selectFrame.pack(side = tk.LEFT, fill = tk.BOTH, expand = True)

        self.selectAllButton = tk.Button(self.selectFrame, text = "Select All",
            command = self.selectAll, **gus.fontc)
        self.selectAllButton.pack(side = tk.TOP, padx = 5, fill = tk.X,
            expand = True)
        self.deselectAllButton = tk.Button(self.selectFrame,
            text = "Deselect All", command = self.deselectAll, **gus.fontc)
        self.deselectAllButton.pack(side = tk.TOP, padx = 5, fill = tk.X,
            expand = True)

        self.bind('<Control-a>', self.selectAll)
        self.bind('<Control-A>', self.selectAll)
        self.bind('<Control-d>', self.deselectAll)
        self.bind('<Control-D>', self.deselectAll)

        # Flow control .........................................................
        self.grid_rowconfigure(row, weight = 1) # FIXME
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row = row, sticky = "NEWS")
        row += 1

        # Basic ................................................................
        self.basic = MainControlWidget(self.notebook, network, display,
            self._onRecordStart, self._onRecordStop, pqueue)
        self.notebook.add(self.basic, text = "Manual")

        # Flow Library .........................................................
        self.library = FlowLibraryWidget(self.notebook, {}, self.display,pqueue)
            # TODO
        self.notebook.add(self.library, text = "Library",state = tk.NORMAL)

        # Functional ...........................................................
        self.functional = FunctionControlWidget(self.notebook, display,
            self._onRecordStart, self._onRecordStop, pqueue)
        self.notebook.add(self.functional, text = "Scripting",
            state = tk.NORMAL)

        # External .............................................................
        self.external = ex.ExternalControlWidget(self.notebook,
            self.archive, self.externalBackEnd, pqueue) # FIXME pass backend
        self.notebook.add(self.external, text = "External",
            state = tk.NORMAL)

        # Record ...............................................................
        # Add spacer:
        self.grid_rowconfigure(row, weight = 0) # FIXME
        row += 1

        self.recordFrame = tk.LabelFrame(self, text = "Record Data", **gus.fontc)
        self.recordFrame.grid(row = row, sticky = "EW")
        row += 1

        self.fileFrame = tk.Frame(self.recordFrame)
        self.fileFrame.pack(side = tk.TOP, fill = tk.X, expand = True)

        self.fileLabel = tk.Label(self.fileFrame, text = "File: ",
            **gus.fontc, **gus.padc)
        self.fileLabel.pack(side = tk.LEFT)
        self.fileField = tk.Entry(self.fileFrame, **gus.fontc, width = 20,
            state = tk.DISABLED)
        self.fileField.pack(side = tk.LEFT, fill = tk.X, expand = True)
        self.fileButton = tk.Button(self.fileFrame, text = "...",
            command = self._onFileButton, **gus.fontc, **gus.padc)
        self.fileButton.pack(side = tk.LEFT, **gus.padc)
        self.activeWidgets.append(self.fileButton)

        self.dataLogger = DataLogger(self.archive, self.pqueue)
        self.logDirectory = os.getcwd() # Get current working directory

        self.recordControlFrame = tk.Frame(self.recordFrame)
        self.recordControlFrame.pack(side = tk.TOP, fill = tk.X, expand = True,
            **gus.padc)
        self.recordStartButton = tk.Button(self.recordControlFrame,
            text = "Start", **gus.fontc, **gus.padc,
            command = self._onRecordStart)
        self.recordStartButton.pack(side = tk.LEFT)
        self.recordPauseButton = tk.Button(self.recordControlFrame,
            text = "Pause", **gus.fontc, **gus.padc, state = tk.DISABLED,
            command = self._onRecordPause)
        self.recordPauseButton.pack(side = tk.LEFT, padx = 10)

        self.recordIndexVar = tk.BooleanVar()
        self.recordIndexVar.set(False)
        self.recordIndexButton = tk.Checkbutton(self.recordControlFrame,
            text = "Auto Index", variable = self.recordIndexVar,
            indicatoron = False, padx = 10, pady = 5, **gus.fontc)
        self.recordIndexButton.pack(side = tk.LEFT, **gus.padc)
        self.activeWidgets.append(self.recordIndexButton)

        self.nextIndexLabel = tk.Label(self.recordControlFrame,
            text = "  Next: ", **gus.fontc, **gus.padc)
        self.nextIndexLabel.pack(side = tk.LEFT)
        validateN = self.register(gus._validateN)
        self.nextIndexEntry = tk.Entry(self.recordControlFrame,
            **gus.efont, width = 6, validate = 'key',
            validatecommand = (validateN, '%S', '%s', '%d'))
        self.nextIndexEntry.pack(side = tk.LEFT, **gus.padc)
        self.nextIndexEntry.insert(0, "1")
        self.activeWidgets.append(self.nextIndexEntry)

        # Wrap-up ..............................................................
        self.viewVar.set(self.DM_LIVE)

    # API ......................................................................
    def feedbackIn(self, F):
        """
        Process a feedback vector F
        """
        self.dataLogger.feedbackIn(F, tm.time())

    def slavesIn(self, S):
        """
        Process a slave vector S.
        """
        self.dataLogger.slavesIn(S)

    def selectAll(self, event = None):
        self.display.selectAll()

    def deselectAll(self, event = None):
        self.display.deselectAll()

    # TODO: Set layers?

    # Internal methods .........................................................
    def _onModeChange(self, *A):
        """
        To be called when the view mode is changed (between live mode and flow
        builder.)
        """
        if self.viewVar.get() == self.DM_LIVE:
            self.setLive(True)
        elif self.viewVar.get() == self.DM_BUILDER:
            self.setLive(False)

    def _getDefaultFile(self):
        """
        Return the (relative) filename to be used by default.
        """
        return "FC_recording_on_{}.csv".format(tm.strftime(
            "%a_%d_%b_%Y_%H:%M:%S", tm.localtime()))

    def _onFileButton(self, *_):
        """
        To be called when the "..." button to set a filename for the data logger
        is pressed. Will request a filename from the user and, if one is given,
        write it in the corresponding input field.
        """
        # Get filename:
        fetched = self._getFile()

        # Check if this is a valid, new filename:
        if fetched is not None and len(fetched) > 0 and \
            fetched != self.fullname:
            self._setFile(filename = fetched, absolute = True)

    def _getFile(self):
        """
        Ask the user to select a filename for the data logger and return the
        result. If the user cancels the operation, None is returned.
        """
        return fdg.asksaveasfilename(initialdir = self.logDirectory,
            title = "Set Log File",
                initialfile = self.filename if self.filename is not None else \
                    self._getDefaultFile(),
                filetypes = (("CSV", ".csv"),("Plain Text", ".txt")))

    def _setFile(self, filename, absolute = False):
        """
        Set the filename to use for data logs.
            - filename := str, name to use
            - absolute := bool, whether to split the given filename (by / or \
                delimiters).
        """
        # Get the working directory of the file and the filename by itself
        if absolute:
            splitted = filename.split('/' if not self.inWindows else '\\')
            self.logDirectory = ("{}/"*(len(splitted)-1)).format(*splitted[:-1])
            self.filename = splitted[-1]
            self.fullname = filename
        else:
            self.logDirectory = "./" if not self.inWindows else ".\\"
            self.filename = filename
            self.fullname = self.logDirectory + self.filename

        # Place filename in text field:
        self.fileField.config(state = tk.NORMAL)
        self.fileField.delete(0, tk.END)
        self.fileField.insert(0, self.filename)
        self.fileField.config(state = tk.DISABLED)

        # Reset index:
        self.nextIndexEntry.delete(0, tk.END)
        self.nextIndexEntry.insert(0, "1")

    def _setLive(self, *_):
        """
        Set the state of this and sub-modules to "live feedback." Does nothing
        when already in said state.
        """
        if self.viewVar.get() != self.DM_LIVE:
            self.viewVar.set(self.DM_BUILDER)

    def _setBuilder(self, *_):
        """
        Set the state of this and sub-modules to "flow builder." Does nothing
        when already in said state.
        """
        if self.viewVar.get() != self.DM_BUILDER:
            self.viewVar.set(self.DM_LIVE)

    def _onRecordStart(self, event = None):
        """
        Callback for data logger start.
        """
        # TODO
        if self.fullname is None:
            self._setFile(self._getDefaultFile())

        self.fileField.config(state = tk.DISABLED)
        self.recordStartButton.config(text = "Stop",
            command = self._onRecordStop) # FIXME temp
        filename = self.fullname

        if self.recordIndexVar.get():
            try:
                index = int(self.nextIndexEntry.get())
            except ValueError:
                pass
            else:
                self.nextIndexEntry.delete(0, tk.END)
                self.nextIndexEntry.insert(0, "{}".format(index + 1))
                name, ext = filename.split(".")[:-1], filename.split(".")[-1]
                filename =  ("{}"*len(name) + "_{}.").format(*name, index) + ext

        self._setActiveWidgets(tk.DISABLED)
        self.dataLogger.start(filename,script = self._getScript(),
            mappings = [str(mapping) for mapping in self.display.getMappings()])

    def _getScript(self):
        """
        Get the "flat" (replace newline by semicolon) Python function
        in the dynamic Python input widget.
        """
        return self.functional.flat()

    def _onRecordStop(self, event = None):
        self.dataLogger.stop()
        self.recordStartButton.config(text = "Start",
            command = self._onRecordStart) # FIXME temp
        self._setActiveWidgets(tk.NORMAL)

    def _onRecordPause(self, event = None):
        """
        Callback for data logger pause.
        """
        # TODO
        pass

    def _setActiveWidgets(self, state):
        """
        Set all widgets that should be active when not recording and inactive
        when recording to the given state (either tk.NORMAL or tk.DISABLED).
        """
        for widget in self.activeWidgets:
            widget.config(state = state)

class DisplayMaster(tk.Frame, pt.PrintClient):
    """
    Wrapper around interactive control widgets such as the grid or the live
    table. Allows the user to switch between them and abstracts their specifics
    away from the rest of the control front-end.
    """
    SYMBOL = "[DM]"
    MENU_ROW, MENU_COLUMN = 0, 0
    CONTENT_ROW, CONTENT_COLUMN = 1, 0
    GRID_KWARGS = {'row':CONTENT_ROW, 'column':CONTENT_COLUMN, 'sticky':"NEWS"}

    def __init__(self, master, pqueue):
        """
        Create a new DisplayMaster.

        - feedbackIn(F) : takes a standard feedback vector
        - networkIn(N) : takes a standard network state vector
        - slavesIn(S) : takes a standard slave state vector

        - activate(A) : 'turn on' display using the optional activation vector A
        - deactivate() : 'turn off' display

        - selectAll()
        - deselectAll()
        - map(f, t) : takes a function that accepts the standardized parameters
                    of the PythonInputWidget and returns a normalized duty cycle
                    (in [0, 1])
        - set(dc) : takes a normalized duty cycle ([0, 1])
        - apply()
        - getC() : return a standard control vector
        - limit(dc) : takes a normalized duty cycle ([0, 1])
        - redraw()

        - blockAdjust()
        - unblockAdjust()

        - getMapping()

        See fc.standards.
        """
        tk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)
        self.displays = {}
        self.selected = tk.IntVar()
        self.selected.trace('w', self._update)
        self.current = None
        self.parameterCallbacks = []

        self.grid_rowconfigure(self.CONTENT_ROW, weight = 1)
        self.grid_columnconfigure(self.CONTENT_COLUMN, weight = 1)

        self.menuFrame = tk.Frame(self)
        self.menuFrame.grid(row = self.MENU_ROW, column = self.MENU_COLUMN,
            sticky = "EW")

        self.digits = 10
        self.counterFormat = "{" + ":0{}d".format(self.digits) + "}"
        self.counterVar = tk.StringVar()
        self.counterVar.set("0"*self.digits)
        self.deltaVar = tk.StringVar()
        self.counterVar.set("00.000")
        self.counterDisplay = tk.Label(self.menuFrame, **gus.fontc,
            textvariable = self.counterVar, width = 10, fg = "darkgray")
        self.counterDisplay.pack(side = tk.LEFT)
        self.deltaDisplay = tk.Label(self.menuFrame, **gus.fontc,
            textvariable = self.deltaVar, width = 5, fg = "darkgray")
        self.deltaDisplay.pack(side = tk.LEFT, padx = 10)
        self.last_time = tm.time()
        self.count = 0

        self.selectorFrame = tk.Frame(self.menuFrame)
        self.selectorFrame.pack(side = tk.RIGHT, fill= tk.Y)

    # API ----------------------------------------------------------------------

    def add(self, display, text, **pack_kwargs):
        """
        Add DISPLAY to this DisplayMaster. Behaves just like ttk.Notebook.add.
        """
        index = len(self.displays)
        self.displays[index] = display

        button = tk.Radiobutton(self.selectorFrame, variable = self.selected,
            value = index, text = text, **gus.rbconf)
        button.pack(side = tk.LEFT, **gus.padc)

        if self.current is None:
            display.grid(**self.GRID_KWARGS)
            self.current = index

    def currentWidget(self):
        """
        Get the currently active display widget.
        """
        return self.displays[self.current]

    # Wrapper methods ----------------------------------------------------------
    def feedbackIn(self, F):
        self.count += 1
        self.counterVar.set(self.counterFormat.format(self.count))
        this_time = tm.time()
        self.deltaVar.set("{:02.3f}s".format(this_time - self.last_time))
        self.last_time = this_time
        self.displays[self.current].feedbackIn(F)

    def networkIn(self, N):
        self.displays[self.current].networkIn(N)

    def slavesIn(self, S):
        self.displays[self.current].slavesIn(S)

    def activate(self, A = None):
        for display in self.displays.values():
            display.activate(A)

    def deactivate(self):
        for display in self.displays.values():
            display.deactivate()

    def selectAll(self):
        self.displays[self.current].selectAll()

    def deselectAll(self):
        self.displays[self.current].deselectAll()

    def map(self, f, t, k):
        self.displays[self.current].map(f, t, k)

    def set(self, dc):
        self.displays[self.current].set(dc)

    def apply(self):
        self.displays[self.current].apply()

    def getC(self):
        return self.displays[self.current].getC()

    def limit(self, dc):
        self.displays[self.current].limit(dc)

    def blockAdjust(self):
        self.displays[self.current].blockAdjust()

    def unblockAdjust(self):
        self.displays[self.current].unblockAdjust()

    def redraw(self):
        self.displays[self.current].redraw()

    def getMappings(self):
        mappings = []
        for display in self.displays.values():
            mapping = display.getMapping()
            if mapping is not None:
                mappings.append(mapping)
        return mappings

    # Internal methods ---------------------------------------------------------
    def _update(self, *event):
        new = self.selected.get()
        if new != self.current:
            self.displays[self.current].grid_forget()
            self.displays[new].grid(**self.GRID_KWARGS)
            self.current = new

class GridWidget(gd.BaseGrid, pt.PrintClient):
    """
    Front end for the 2D interactive Grid.
    """
    # TODO: keep backup for live feedback
    SYMBOL = "[GD]"
    RESIZE_MS = 400

    SM_SELECT = 55
    SM_DRAW = 65

    DEFAULT_COLORS = cms.COLORMAP_GALCIT_REVERSED
    DEFAULT_OFF_COLOR = "#303030"
    DEFAULT_EMPTY_COLOR = 'darkgray'
    DEFAULT_HIGH = 100
    DEFAULT_LOW = 0
    CURSOR = "hand1"

    OUTLINE_NORMAL = "black"
    OUTLINE_SELECTED = "orange"
    WIDTH_NORMAL = 1
    WIDTH_SELECTED = 3

    def __init__(self, master, archive, mapper, send, pqueue,
        colors = DEFAULT_COLORS, off_color = DEFAULT_OFF_COLOR,
        high = DEFAULT_HIGH, empty_color = DEFAULT_EMPTY_COLOR):

        # Setup ................................................................
        self.archive = archive
        self.mapper = mapper
        self.send_method = send

        self.fanArray = self.archive[ac.fanArray]
        self.L = self.fanArray[ac.FA_layers]
        self.R, self.C = self.fanArray[ac.FA_rows], self.fanArray[ac.FA_columns]
        self.RC = self.R*self.C
        self.RCL = self.RC*self.L
        self.size_g = self.RC*self.L
        self.range_g = range(self.size_g)
        self.maxRPM = self.archive[ac.maxRPM]
        self.maxFans = self.archive[ac.maxFans]

        print("**", self.R, self.C, self.L, self.RC, self.RCL)
        self.empty_color = empty_color
        self.off_color = off_color
        gd.BaseGrid.__init__(self, master, self.R, self.C, cursor = self.CURSOR,
            empty = self.empty_color)
        pt.PrintClient.__init__(self, pqueue)

        # Mapping ..............................................................
        self.values_g = [0]*self.size_g
        self.selected_g = [False]*self.size_g

        # FIXME transplant behavior that should be in Mapper
        self.getIndex_g = self.mapper.index_KG
        self.getIndex_k = self.mapper.index_GK
        self.getCoordinates_g = self.mapper.tuple_KG
        self.getCoordinates_k = self.mapper.tuple_GK

        self.nslaves = len(self.archive[ac.savedSlaves])
        self.size_k = self.nslaves*self.maxFans
        self.range_k = range(self.size_k)
        self.F_buffer = [0]*(2*self.size_k)

        self.control_buffer = []
        self._resetControlBuffer()

        # Tools ................................................................
        self.toolBar = tk.Frame(self)
        self.toolBar.grid(row = self.GRID_ROW + 1, sticky = "WE")

        # Data type control (RPM vs DC) ........................................
        self.maxValue = self.maxRPM
        self.maxValues = {"RPM" : self.maxRPM, "DC" : 1}
        self.offsets = {"RPM" : 0, "DC" : 1}
        self.offset = self.offsets["RPM"]
        self.typeFrame = tk.Frame(self.toolBar)
        self.typeFrame.pack(side = tk.LEFT, fill = tk.Y)
        self.typeMenuVar = tk.StringVar()
        self.typeMenuVar.trace('w', self._onTypeMenuChange)
        self.typeMenuVar.set("RPM")
        self.typeMenu = tk.OptionMenu(self.toolBar, self.typeMenuVar,
            *list(self.offsets.keys()))
        self.typeMenu.config(width = 3, **gus.fontc)
        self.typeMenu.pack(side = tk.LEFT)

        # Layer control ........................................................
        self.layer = 0
        self.layerFrame = tk.Frame(self.toolBar)
        self.layerFrame.pack(side = tk.LEFT, fill = tk.Y)
        self.layerVar = tk.StringVar()
        self.layerVar.trace('w', self._onLayerChange)
        self.layerMenu = tk.OptionMenu(self.layerFrame, self.layerVar,
            *["Layer {}".format(l + 1) for l in range(self.L)])
        self.layerMenu.config(**gus.fontc)
        self.layerMenu.pack(side = tk.LEFT, **gus.padc)

        # Layer selection ......................................................
        self.deepVar = tk.BooleanVar()
        self.deepVar.set(True)
        self.deepButton = tk.Checkbutton(self.toolBar,
            text = "Deep Select", variable = self.deepVar,
            indicatoron = False, padx = 10, pady = 5, **gus.fontc)
        self.deepButton.pack(side = tk.LEFT, **gus.padc)

        # Selection mode control ...............................................
        # FIXME
        self.selectMode = tk.IntVar()
        self.selectButton = tk.Radiobutton(self.toolBar,
            variable = self.selectMode, value = self.SM_SELECT,
            text = "Rectangle", **gus.rbconf)
        self.selectButton.pack(side = tk.LEFT)
        self.drawButton = tk.Radiobutton(self.toolBar, text = "Trace",
            variable = self.selectMode, value = self.SM_DRAW, **gus.rbconf)
        self.drawButton.pack(side = tk.LEFT)
        self.selectMode.trace('w', self._onSelectModeChange)

        self.drag_start = None
        self.drag_end = None

        self.selected_count = 0

        # Selection hold .......................................................
        self.holdVar = tk.BooleanVar()
        self.holdVar.set(True)
        self.holdButton = tk.Checkbutton(self.toolBar,
            text = "Hold Selection", variable = self.holdVar,
            indicatoron = False, padx = 10, pady = 5, **gus.fontc)
        self.holdButton.pack(side = tk.RIGHT, **gus.padc)

        # Color Bar ............................................................
        self.colorBar = ColorBarWidget(self, colors = cms.COLORMAP_GALCIT,
            high = self.maxRPM, unit = "RPM", pqueue = pqueue)
        self.colorBar.grid(row = self.GRID_ROW, column = self.GRID_COLUMN + 1,
            sticky = "NS")

        # Setup ................................................................

        # Automatic resizing:
        self.bind("<Configure>", self._scheduleAdjust)

        self.adjusting = False
        self.colors = colors
        self.numColors = len(colors)
        self.maxColor = self.numColors - 1
        self.high = high
        self.low = 0
        self.rows, self.columns = range(self.R), range(self.C)
        self.dc = 0 # Whether to use duty cycles

        self.is_live = True

        # TODO: (redundant "TODO's" indicate priority)
        # - handle resets on profile changing TODO
        # - handle control vector construction TODO
        # - handle multilayer assignment (how to deal with unselected layers?)
        #   (TODO)
        # - drag, drop, etc..
        # - get selections
        # - [...]
        self.layerVar.set("Layer 1")
        self.selectMode.set(self.SM_SELECT)

        # Configure callbacks:
        self.setLeftClick(self._onLeftClick)
        self.setRightClick(self._onRightClick)
        self.setLeftRelease(self._onLeftRelease)
        self.setRightRelease(self._onRightRelease)
        self.setLeftDoubleClick(self._onDoubleLeft)
        self.setRightDoubleClick(self._onDoubleRight)
        self.setLeftDrag(self._onLeftDrag)
        self.setRightDrag(self._onRightDrag)

    # Standard interface .......................................................
    def activate(self, F_0 = None):
        if F_0 is not None:
            self.feedbackIn(F_0)

    def deactivate(self):
        self.feedbackIn([std.RIP]*(self.size_g*2)) # TODO performance
        pass

    def feedbackIn(self, F):
        """
        Process the feedback vector F according to the grid mapping.
        """
        # FIXME performance
        # FIXME nomenclature
        if self.built():
            for k in self.range_k:
                g = self.getIndex_g(k)
                if g >= 0:
                    self.update_g(g, F[k + self.size_g*self.offset])
            self.F_buffer = F
        else:
            self.printw("F received while grid isn't built. Ignoring.")

    def networkIn(self, N):
        if N[std.NS_I_CONN] != std.NS_CONNECTED:
            self.deactivate()

    def slavesIn(self, S):
        pass

    def selectAll(self):
        for g in self.range_g:
            self.select_g(g)

    def deselectAll(self):
        for g in self.range_g:
            self.deselect_g(g)

    def map(self, func, t = 0, t_step = 0):
        """
        Map the given function to the entire array, calling it once for each
        fan with the corresponding argument values.

        Note that values that correspond only to mapped fans (such as row,
        column and layer) will default to zero when unavailable.

        - func := function to map
        - t := timestamp (float)
        - t_step := time step (int)
        """
        """
        IMPLEMENTATION NOTES:
        - func(r, c, l, s, f, d, p, R, C, L, S, F, P, t, k)
        PARAMETERS = (P_ROW, P_COLUMN, P_LAYER, P_INDEX, P_FAN, P_DUTY_CYCLE,
        P_RPM, P_ROWS, P_COLUMNS, P_LAYERS, P_INDICES, P_FANS, P_MAX_RPM,P_TIME,
        P_STEP)
        """
        # FIXME performance
        try:
            for k in self.range_k:
                g = self.getIndex_g(k)
                s, f  = self.slave_k(k), self.fan_k(k)
                if g == std.PAD: # FIXME prev: if g != std.PAD:
                    l, r, c = 0, 0, 0
                else:
                    l, r, c = self.getCoordinates_g(s, f)

                if self.selected_count == 0 or (g >= 0 and self.selected_g[g]):
                    self.control_buffer[k] = func(r, c, l, s, f,
                        self.F_buffer[self.size_k + k], self.F_buffer[k],
                        self.R, self.C, self.L, self.nslaves, self.maxFans,
                        self.maxRPM, t, t_step)
        except Exception as e:
            print(k)
            raise e

        else:
            self.send_method(self.control_buffer)
            if not self.holdVar.get():
                self.deselectAll()

    def set(self, dc):
        """
        Map the given duty cycle.
        """
        self.map(self._const(dc), 0, 0)

    def apply(self):
        # FIXME
        pass

    def getC(self):
        # FIXME
        pass

    def limit(self, dc):
        # FIXME
        pass

    def blockAdjust(self):
        self.unbind("<Configure>")
        pass

    def unblockAdjust(self):
        self.bind("<Configure>", self._scheduleAdjust)
        pass

    def redraw(self, event = None):
        self.draw(margin = 20)
        self.colorBar.redraw()

    # Mapping ..................................................................
    def layer_g(self, g):
        """
        Get the layer that corresponds to the given grid-coordinate index.
        """
        return g // self.RC

    def gridi_g(self, g):
        """
        Get the 2D "within layer" index that corresponds to the given
        grid-coordinate index.

        In a single-layer grid, this function makes no difference.
        """
        return g % self.RC

    def slave_k(self, k):
        """
        Get the slave index corresponding to the network-coordinate index k.
        """
        return k // self.maxFans

    def fan_k(self, k):
        """
        Get the fan index corresponding to the network-coordinate index k.
        """
        return k % self.maxFans

    # Activity .................................................................
    def update_g(self, g, value):
        """
        Set the given grid index to the given value, saturating it at this
        grid's maximum value, and update the corresponding cell's color if
        the value is in the observed layer.

        - g := int, G-coordinate index.
        - value := int or float, value to apply.
        """
        self.values_g[g] = value
        fill = self.empty_color

        if value >= 0:
            fill = self.colors[min(self.maxColor,
                int(((value*self.maxColor)/self.maxValue)))]
        elif value == std.RIP:
            fill = self.off_color

        if self.layer_g(g) == self.layer:
            self.filli(self.gridi_g(g), fill)

    # Selection ................................................................
    # FIXME: performance
    def select_i(self, i):
        if self.deepVar.get():
            l = 0
            while l < self.L:
                self.select_g(i + l*self.RC)
                l += 1
        else:
            self.select_g(i + self.layer*self.RC)

    def deselect_i(self, i):
        if self.deepVar.get():
            l = 0
            while l < self.L:
                self.deselect_g(i + l*self.RC)
                l += 1
        else:
            self.deselect_g(i + self.layer*self.RC)


    def select_g(self, g):
        if not self.selected_g[g]:
            self.selected_count += 1
        self.selected_g[g] = True
        if self.layer_g(g) == self.layer:
            self.outlinei(self.gridi_g(g),
                self.OUTLINE_SELECTED, self.WIDTH_SELECTED)

    def deselect_g(self, g):
        if self.selected_g[g]:
            self.selected_count -= 1
        self.selected_g[g] = False
        if self.layer_g(g) == self.layer:
            self.outlinei(self.gridi_g(g),
                self.OUTLINE_NORMAL, self.WIDTH_NORMAL)

    # Widget ...................................................................
    def blockAdjust(self):
        """
        Deactivate automatic adjustment of widgets upon window resizes.
        """
        self.unbind("<Configure>")

    def unblockAdjust(self):
        """
        Activate automatic adjustment of widgets upon window resizes.
        """
        self.bind("<Configure>", self._scheduleAdjust)

    def getMapping(self):
        """
        Get the mapping data structure of this Grid.
        """
        return [self.getIndex_g(k) for k in self.range_k]

    # Internal methods .........................................................
    def _onLayerChange(self, *A):
        """
        To be called when the view layer is changed.
        """
        self.layer = int(self.layerVar.get().split()[-1]) - 1
        self._updateStyle()

    def _onTypeMenuChange(self, *E):
        """
        TO be called when the data type (RPM or DC) is changed.
        """
        self.offset = self.offsets[self.typeMenuVar.get()]
        self.maxValue = self.maxValues[self.typeMenuVar.get()]

    def _onSelectModeChange(self, *E):
        """
        To be called when the direct input mode is changed.
        """
        pass

    def _scheduleAdjust(self, *E):
        self.after(self.RESIZE_MS, self._adjust)
        self.unbind("<Configure>")

    def _updateStyle(self, event = None):
        """
        Enforce style rules when switching layers.
        """
        l = self.layer
        offset = self.layer*self.RC
        for g in range(offset, offset + self.RC):
            self.update_g(g, self.values_g[g])
            if self.selected_g[g]:
                self.select_g(g)
            else:
                self.deselect_g(g)

    def _resetControlBuffer(self):
        """
        Set the control buffer back to its default value.
        """
        self.control_buffer = [0]*self.size_k

    def _adjust(self, *E):
        self.redraw()
        self.bind("<Configure>", self._scheduleAdjust)

    @staticmethod
    def _onLeftClick(grid, i):
        grid.drag_start = i
        grid.drag_end = i
        if i is not None:
            if grid.selected_g[grid.layer*grid.RC + i]:
                grid.deselect_i(i)
            else:
                grid.select_i(i)

    @staticmethod
    def _onRightClick(grid, i):
        grid.drag_start = i
        grid.drag_end = i
        if i is not None:
            grid.deselect_i(i)

    @staticmethod
    def _generalDrag(grid, i, f_g):
        if i != None:
            if grid.selectMode.get() == grid.SM_SELECT:
                if grid.drag_start == None:
                    grid.drag_start = i
                if i != None:
                    grid.drag_end = i
            else:
                f_g(grid.layer*grid.RC + i)


    @staticmethod
    def _onLeftDrag(grid, i):
        if i != None:
            if grid.selectMode.get() == grid.SM_SELECT:
                if grid.drag_start == None:
                    grid.drag_start = i
                grid.drag_end = i
            else:
                grid.select_i(i)

    @staticmethod
    def _onRightDrag(grid, i):
        if i != None:
            if grid.selectMode.get() == grid.SM_SELECT:
                if grid.drag_start == None:
                    grid.drag_start = i
                grid.drag_end = i
            else:
                grid.deselect_i(i)

    @staticmethod
    def _onLeftRelease(grid, i):
        grid._generalRelease(grid, i, grid.select_i)

    @staticmethod
    def _onRightRelease(grid, i):
        grid._generalRelease(grid, i, grid.deselect_i)

    @staticmethod
    def _generalRelease(grid, i, f_i):
        if grid.drag_start != grid.drag_end and grid.drag_start != None and \
            grid.drag_end != None:

            if grid.selectMode.get() == grid.SM_SELECT:
                row_1, row_2 = grid.drag_start//grid.R, grid.drag_end//grid.R
                row_start = min(row_1, row_2)
                row_end = max(row_1, row_2)

                col_1, col_2 = grid.drag_start%grid.R, grid.drag_end%grid.R
                col_start = min(col_1, col_2)
                col_end = max(col_1, col_2)

                for r in range(row_start, row_end + 1):
                    for c in range(col_start, col_end + 1):
                        f_i(r*grid.C + c)

                grid.drag_start = None
                grid.drag_end = None
            else:
                pass

    @staticmethod
    def _onDoubleLeft(grid, i):
        k_i = grid.getIndex_k(i + grid.layer*grid.RC)
        k_0 = grid.slave_k(k_i)*grid.maxFans

        for k in range(k_0, k_0 + grid.maxFans):
            g = grid.getIndex_g(k)
            if g >= 0:
                grid.select_g(g)

    @staticmethod
    def _onDoubleRight(grid, i):
        k_i = grid.getIndex_k(i + grid.layer*grid.RC)
        k_0 = grid.slave_k(k_i)*grid.maxFans

        for k in range(k_0, k_0 + grid.maxFans):
            g = grid.getIndex_g(k)
            if g >= 0:
                grid.deselect_g(g)

    @staticmethod
    def _const(dc):
        """
        Return a function that ignores all arguments and returns the given
        duty cycle.
        """
        def g(*_):
            return dc
        return g

class ColorBarWidget(tk.Frame):
    """
    Draw a vertical color gradient for color-coding reference.
    """
    SYMBOL = "[CB]"

    def __init__(self, master, colors, pqueue, high = 100, unit = "[?]"):

        tk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

        # Setup ................................................................
        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure(1, weight = 1)
        self.colors = colors
        self.steps = len(colors)
        self.high, self.low = high, 0


        # Widgets ..............................................................
        self.highLabel = tk.Label(self, text = "{} {}".format(high, unit),
            font = "Courier 5", bg = "black", fg = "white")
        self.highLabel.grid(row = 0, sticky = "EW")

        self.canvas = tk.Canvas(self, bg = self.colors[-1],
            width = self.highLabel.winfo_width())
        self.canvas.grid(row = 1, sticky = 'NEWS')

        self.lowLabel = tk.Label(self, text = "{} {}".format(self.low, unit),
            font = "Courier 5", bg = "black", fg = "white")
        self.lowLabel.grid(row = 2, sticky = "EW")

        print("[REM] Pass MAX RPM to color bar") # FIXME

        self._draw()

    # API ......................................................................
    def redraw(self, *E):
        """
        Rebuild the color bar to adjust to a new size.
        """
        self.canvas.delete(tk.ALL)
        self._draw()

    def setHigh(self, new):
        """
        Set a new high value.
        """
        self.high = new

    # Internal methods .........................................................
    def _draw(self, *E):
        """
        Draw the colorbar.
        """
        self.winfo_toplevel().update_idletasks()
        height = max(self.winfo_height(), self.winfo_reqheight())
        width = self.highLabel.winfo_reqwidth()
        step = height/self.steps
        left, right = 0, width
        y = 0
        self.bind("<Button-1>", self.redraw)
        for i in range(self.steps):
            iid = self.canvas.create_rectangle(
                left, y, right, y + step, fill = self.colors[i],
                width = 0)
            self.canvas.tag_bind(iid, "<ButtonPress-1>", self.redraw)
            y += step
        self.canvas.create_line(left, y, right, y, width = 4)
        self.canvas.create_line(left, y, right, y, width = 2, fill = 'white')

class LiveTable(pt.PrintClient, tk.Frame):
    """
    Another interactive control widget. This one displays all slaves and fans
    in a tabular fashion and hence needs no mapping.
    """
    SYMBOL = "[LT]"

    MENU_ROW, MENU_COLUMN = 0, 0
    TABLE_ROW, TABLE_COLUMN = 2, 0
    HSCROLL_ROW, HSCROLL_COLUMN = MENU_ROW + 1, TABLE_COLUMN
    VSCROLL_ROW, VSCROLL_COLUMN = TABLE_ROW, TABLE_COLUMN + 1

    INF = float('inf')
    NINF = -INF


    def __init__(self, master, archive, mapper, send_method, network, pqueue):
        """
        Create a new LiveTable in MASTER.

            master := Tkinter parent widget
            archive := FCArchive instance
            send_method := method to which to pass generated control vectors
            pqueue := Queue instance for I-P printing

        """
        tk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)
        self.archive = archive
        self.mapper = mapper
        self.send_method = send_method

        self.maxFans = self.archive[ac.maxFans]
        self.startDisplacement = 2
        self.endDisplacement = self.startDisplacement + self.maxFans

        self.fanArray = self.archive[ac.fanArray]
        self.L = self.fanArray[ac.FA_layers]
        self.R, self.C = self.fanArray[ac.FA_rows], self.fanArray[ac.FA_columns]
        self.RC = self.R*self.C
        self.RCL = self.RC*self.L
        self.size_g = self.RC*self.L
        self.range_g = range(self.size_g)
        self.maxRPM = self.archive[ac.maxRPM]
        self.maxFans = self.archive[ac.maxFans]

        # Mapping ..............................................................
        self.values_g = [0]*self.size_g
        self.selected_g = [False]*self.size_g


        # FIXME transplant behavior that should be in Mapper
        self.getIndex_g = self.mapper.index_KG
        self.getIndex_k = self.mapper.index_GK
        self.getCoordinates_g = self.mapper.tuple_KG
        self.getCoordinates_k = self.mapper.tuple_GK

        self.nslaves = len(self.archive[ac.savedSlaves])
        self.size_k = self.nslaves*self.maxFans
        self.range_k = range(self.size_k)
        self.F_buffer = [0]*(2*self.size_k)

        self.selected_count = 0
        self.control_buffer = []
        self._resetControlBuffer()

        # Build menu ...........................................................
        self.main = tk.Frame(self)
        self.main.pack(fill = tk.BOTH, expand = True)

        self.main.grid_rowconfigure(self.TABLE_ROW, weight = 1)
        self.main.grid_columnconfigure(self.TABLE_COLUMN, weight = 1)

        # Set background:
        self.bg = "#e2e2e2"
        self.fg = "black"
        self.main.config(bg = self.bg)

        self.topBar = tk.Frame(self.main, bg = self.bg)
        self.topBar.grid(row = self.MENU_ROW, column = self.MENU_COLUMN,
            sticky = "EW")

        self.offset = 0
        self.showMenuVar = tk.StringVar()
        self.showMenuVar.trace('w', self._showMenuCallback)
        self.showMenuVar.set("RPM")
        self.showMenu = tk.OptionMenu(self.topBar, self.showMenuVar,"RPM","DC")
        self.showMenu.config(width = 3, background = self.bg,
            highlightbackground = self.bg, foreground = self.fg, **gus.fontc)
        self.showMenu.pack(side = tk.LEFT)

        self.playPauseFlag = True
        self.playPauseButton = tk.Button(
            self.topBar,
            bg = self.bg,
            highlightbackground = self.bg,
            fg = self.fg,
            text = "Pause",
            command = self._playPause,
            **gus.fontc,
        )
        self.bind("<space>", self._playPause)
        self.master.bind("<space>",self._playPause)

        self.playPauseButton.pack(side = tk.LEFT)

        self.printThread = None
        self.donePrinting = False
        self.printMatrixButton = tk.Button(
            self.topBar,
            bg = self.bg,
            highlightbackground = self.bg,
            fg = self.fg,
            text = "Print",
            command = self._printMatrix,
            **gus.fontc,
        )
        self.master.bind("<Control-P>",self._printMatrix)
        self.master.bind("<Control-p>",self._printMatrix)

        self.wasPaused = False

        # Sentinel .............................................................
        self.sentinelWidgets = []
        self._sentinelCheck = lambda x: False

        self.sentinelFrame = tk.Frame(
            self.topBar,
            bg = self.bg,
        )

        self.sentinelLabel = tk.Label(
            self.sentinelFrame,
            bg = self.bg,
            fg = self.fg,
            text = " Watchdog: ",
            **gus.fontc,
        )
        self.sentinelLabel.pack(side = tk.LEFT)

        self.sentinelSecondaryLabel = tk.Label(
            self.sentinelFrame,
            bg = self.bg,
            fg = self.fg,
            **gus.fontc
        )
        self.sentinelSecondaryLabel.pack(side = tk.LEFT)

        self.sentinelMenuVar = tk.StringVar()
        self.sentinelMenuVar.set("Above")
        self.sentinelMenu = tk.OptionMenu(
            self.sentinelFrame,
            self.sentinelMenuVar,
            "Above",
            "Below",
            "Outside 10% of",
            "Within 10% of",
            "Not"
        )
        self.sentinelMenu.configure(
            highlightbackground = self.bg,
            bg = self.bg,
            **gus.fontc,
        )
        self.sentinelMenu.pack(side = tk.LEFT)
        self.sentinelWidgets.append(self.sentinelMenu)

        validateC = self.register(gus._validateN)
        self.sentinelEntry = tk.Entry(self.sentinelFrame,
            highlightbackground = self.bg,
            bg = 'white', width  = 5,
            fg = self.fg, **gus.fontc,
            validate = 'key', validatecommand = \
                (validateC, '%S', '%s', '%d'))
        self.sentinelEntry.insert(0,'0')
        self.sentinelEntry.pack(side = tk.LEFT)
        self.sentinelWidgets.append(self.sentinelEntry)

        self.sentinelTerciaryLabel = tk.Label(
            self.sentinelFrame,
            bg = self.bg,
            fg = self.fg,
            **gus.fontc,
            text = " RPM   "
        )
        self.sentinelTerciaryLabel.pack(side = tk.LEFT)

        self.sentinelActionMenuVar = tk.StringVar()
        self.sentinelActionMenuVar.set("Highlight")
        self.sentinelActionMenu = tk.OptionMenu(
            self.sentinelFrame,
            self.sentinelActionMenuVar,
            "Warn me",
            "Highlight",
            "Shut down",
        )
        self.sentinelActionMenu.configure(
            highlightbackground = self.bg,
            bg = self.bg,
            **gus.fontc,
        )
        self.sentinelActionMenu.pack(side = tk.LEFT)
        self.sentinelWidgets.append(self.sentinelActionMenu)

        self.sentinelPauseVar = tk.BooleanVar()
        self.sentinelPauseVar.set(True)
        self.sentinelPauseButton = tk.Checkbutton(
            self.sentinelFrame,
            text ="Freeze",
            variable = self.sentinelPauseVar,
            bg = self.bg,
            fg = self.fg,
            **gus.fontc)
        self.sentinelPauseButton.pack(side = tk.LEFT)
        self.sentinelWidgets.append(self.sentinelPauseButton)

        self.sentinelPrintVar = tk.IntVar()
        self.sentinelPrintButton = tk.Checkbutton(
            self.sentinelFrame,
            text ="Print",
            variable = self.sentinelPrintVar,
            bg = self.bg,
            fg = self.fg,
            **gus.fontc)
        self.sentinelPrintButton.pack(side = tk.LEFT)
        self.sentinelWidgets.append(self.sentinelPrintButton)

        self.sentinelApplyButton = tk.Button(
            self.sentinelFrame,
            bg = self.bg,
            highlightbackground = self.bg,
            fg = self.fg,
            text = "Apply",
            command = self._applySentinel,
            state = tk.NORMAL,
            **gus.fontc
        )
        self.sentinelApplyButton.pack(side = tk.LEFT)

        self.sentinelClearButton = tk.Button(
            self.sentinelFrame,
            bg = self.bg,
            highlightbackground = self.bg,
            fg = self.fg,
            text = "Clear",
            command = self._clearSentinel,
            state = tk.DISABLED,
            **gus.fontc,
        )
        self.sentinelClearButton.pack(side = tk.LEFT)

        self.sentinelFrame.pack(side = tk.RIGHT)
        self.sentinelFlag = False

        # Build table ..........................................................
        self.tableFrame = tk.Frame(self.main)
        self.tableFrame.grid(row = self.TABLE_ROW, column = self.TABLE_COLUMN,
            sticky = "NEWS")
        self.table = ttk.Treeview(self.tableFrame,
            height = 32)
        self.table.pack(fill = tk.BOTH, expand = True)
        # Add columns:
        self.columns = ("Index", "Max", "Min")
        self.specialColumns = len(self.columns)

        self.style = ttk.Style(self.table)
        self.style.configure('Treeview.Heading', font = ('TkFixedFont 7'))

        self.zeroes = ()
        for fanNumber in range(self.maxFans):
            self.columns += ("{}".format(fanNumber+1),)
            self.zeroes += (0,)
        self.columns += ("Pad",)

        self.table['columns'] = self.columns

        self.table.column("#0", width = 20, stretch = True)

        self.boldFontSettings = "TkFixedFont 7 bold"
        self.font = tk.font.Font(font = self.boldFontSettings)
        self.rpmwidth = self.font.measure("12345")
        self.specwidth = self.font.measure("  Index  ")
        # Build columns:
        for column in self.columns[:self.specialColumns]:
            self.table.column(column,
                anchor = "center", stretch = False, width = self.specwidth)
            self.table.heading(column, text = column)

        for column in self.columns[self.specialColumns:-1]:
            self.table.column(column, width = self.rpmwidth,
                anchor = "center", stretch = False)
            self.table.heading(column, text = column)

        self.table.column(self.columns[-1], width = self.rpmwidth,
            anchor = "center", stretch = True)
        self.table.heading(self.columns[-1], text = " ")

        # Configure tags:
        self.table.tag_configure(
            "H", # Highlight
            background= '#fffaba',
            foreground ='#44370b',
            font = self.boldFontSettings
        )

        self.table.tag_configure(
            "D", # Disconnected
            background= '#262626',
            foreground ='#808080',
            font = self.boldFontSettings
        )

        self.table.tag_configure(
            "N", # Normal
            background= 'white',
            foreground ='black',
            font = 'TkFixedFont 7'
        )

        # Build scrollbars .....................................................
        # See: https://lucasg.github.io/2015/07/21/
        #    How-to-make-a-proper-double-scrollbar-frame-in-Tkinter/
        self.hscrollbar = ttk.Scrollbar(self.main, orient = tk.HORIZONTAL)
        self.hscrollbar.config(command = self.table.xview)
        self.hscrollbar.grid(row = self.HSCROLL_ROW,
            column = self.HSCROLL_COLUMN, sticky = "EW")

        self.vscrollbar = ttk.Scrollbar(self.main, orient = tk.VERTICAL)
        self.vscrollbar.config(command = self.table.yview)
        self.vscrollbar.grid(row = self.VSCROLL_ROW,
            column = self.VSCROLL_COLUMN, sticky = "NS")


        # FIXME verify consistency with new standard
        # Add rows and build slave list:
        self.slaves = {}
        self.fans = range(self.maxFans)
        self.numSlaves = 0

    def networkIn(self, N):
        if not N[std.NS_I_CONN]:
            self.deactivate()

    def slavesIn(self, S):
        pass

    def selectAll(self):
        for index, iid in self.slaves.items():
            self.table.selection_add(iid)

    def deselectAll(self):
        self.table.selection_set(())

    def map(self, func, t = 0, t_step = 0):
        """
        Map the given function to the entire array, calling it once for each
        fan with the corresponding argument values.

        Note that values that correspond only to mapped fans (such as row,
        column and layer) will default to zero when unavailable.

        - func := function to map
        - t := timestamp (float)
        - t_step := time step (int)
        """
        """
        IMPLEMENTATION NOTES:
        - func(r, c, l, s, f, d, p, R, C, L, S, F, P, t, k)
        PARAMETERS = (P_ROW, P_COLUMN, P_LAYER, P_INDEX, P_FAN, P_DUTY_CYCLE,
        P_RPM, P_ROWS, P_COLUMNS, P_LAYERS, P_INDICES, P_FANS, P_MAX_RPM,P_TIME,
        P_STEP)

        * "g" is still relevant here because FC functions use both Grid and
            LiveTable parameters.
        """
        # FIXME why are there redundant implementations of this? See GridWidget
        # FIXME no Exception handling?
        # FIXME performance
        for k in self.range_k:
            g = self.getIndex_g(k)
            s, f  = self.slave_k(k), self.fan_k(k)
            if g == std.PAD: # FIXME prev: if g != std.PAD:
                l, r, c = 0, 0, 0
            else:
                l, r, c = self.getCoordinates_g(s, f)

            if self.selected_count == 0 or (g >= 0 and self.selected_g[g]):
                self.control_buffer[k] = func(r, c, l, s, f,
                    self.F_buffer[self.size_k + k], self.F_buffer[k],
                    self.R, self.C, self.L, self.nslaves, self.maxFans,
                    self.maxRPM, t, t_step)

        self.send_method(self.control_buffer)


    def set(self, dc):
        self.map(self._const(dc), 0, 0)

    def apply(self):
        # FIXME
        pass

    def getC(self):
        # FIXME
        pass

    def limit(self, dc):
        # FIXME
        pass

    def blockAdjust(self):
        # FIXME
        pass

    def unblockAdjust(self):
        # FIXME
        pass

    def redraw(self):
        # FIXME
        print("redraw")
        pass

    def getMapping(self):
        return None

    # Mapping ..................................................................
    def layer_g(self, g):
        """
        Get the layer that corresponds to the given grid-coordinate index.
        """
        return g // self.RC

    def gridi_g(self, g):
        """
        Get the 2D "within layer" index that corresponds to the given
        grid-coordinate index.

        In a single-layer grid, this function makes no difference.
        """
        return g % self.RC

    def slave_k(self, k):
        """
        Get the slave index corresponding to the network-coordinate index k.
        """
        return k // self.maxFans

    def fan_k(self, k):
        """
        Get the fan index corresponding to the network-coordinate index k.
        """
        return k % self.maxFans

    # Selection ................................................................
    # TODO implement

    # Internal methods .........................................................
    def activate(self, A = None):
        """
        Set the display as "active."
            - A := Optional "activation vector" (a feedback vector with which to
                initialize slave lists and display values).
        """
        if A is None:
            for index in self.slaves:
                self.activatei(index)
        else:
            self.feedbackIn(A)

    def activatei(self, i):
        """
        "Turn on" the row corresponding to the slave in index i.
        """
        self.table.item(self.slaves[i], values = (i + 1), tag = "N")

    def deactivate(self):
        """
        Seemingly "turn off" all rows to indicate inactivity; meant to be used,
        primarily, upon network shutdown.
        """
        for index in self.slaves:
            self.deactivatei(index)
        self._resetControlBuffer()

    def deactivatei(self, i):
        """
        "Turn off" the row corresponding to the slave in index i.
        """
        self.table.item(self.slaves[i],
            values = (i + 1,), tag = "D")

    def _resetControlBuffer(self):
        """
        Set the control buffer back to its default value.
        """
        self.control_buffer = [0]*self.size_k

    def _applySentinel(self, event = False):
        """
        Activate a sentinel according to the user's configuration.
        """
        try:
            if self.sentinelEntry.get() != '':
                self.sentinelFlag = True
                self.sentinelApplyButton.config(state = tk.DISABLED)

                self._sentinelCheck = self._assembleSentinel()

                for widget in self.sentinelWidgets:
                    widget.config(state = tk.DISABLED)
                self.sentinelClearButton.config(state = tk.NORMAL)
        except Exception as e:
            self.printx(e, "Exception in live table:")

    def _executeSentinel(self, targetSlave, targetFan, RPM):
        """
        Trigger the sentinel due to the RPM detected in the target fan of the
        target slave.
        """

        # Action:
        action = self.sentinelActionMenuVar.get()

        if action == "Highlight row(s)":
            pass

        elif action == "Warn me":
            self._printe("WARNING: Module {}, Fan {} at {} RPM".format(
                targetSlave + 1, targetFan, RPM))

        elif action == "Shut down":
            network.shutdown()
            if self.playPauseFlag:
                self._playPause()

            self._printe("WARNING: Shutdown triggered by Module {}, Fan {} "\
                "({} RPM)".format(targetSlave + 1, targetFan, RPM))

        # Print (and avoid printing the same matrix twice):
        if self.sentinelPrintVar.get() and \
            self.lastPrintedMatrix < self.matrixCount:
            self._printMatrix(sentinelValues = (targetFan,targetSlave,RPM))
            self.lastPrintedMatrix = self.matrixCount

        # Pause:
        if self.sentinelPauseVar.get() and self.playPauseFlag:
            self._playPause()

    def _assembleSentinel(self):
        """
        Gather the user's configuration from the relevant input widgets and
        build a new sentinel.
        """
        check = self.sentinelMenuVar.get()
        value = int(self.sentinelEntry.get())

        if check == "Above":
            return lambda rpm : rpm > value

        elif check == "Below":
            return lambda rpm : rpm < value

        elif check == "Outside 10% of":
            return lambda rpm : rpm > value*1.1 or rpm < value*.9

        elif check == "Within 10% of":
            return lambda rpm : rpm < value*1.1 and rpm > value*.9

        elif check == "Not":
            return lambda rpm : rpm != value

    def _clearSentinel(self, event = False):
        """
        Deactivate an active sentinel.
        """
        self.sentinelFlag = False
        self.sentinelClearButton.config(state = tk.DISABLED)
        for widget in self.sentinelWidgets:
            widget.config(state = tk.NORMAL)
        self.sentinelApplyButton.config(state = tk.NORMAL)

    def _printMatrix(self, event = None, sentinelValues = None):
        # FIXME should this be here?

        if self.playPauseFlag:
            self.wasPaused = False
            self._playPause()

        else:
            self.wasPaused = True

        # Lock table ...........................................................
        self.playPauseButton.config(state = tk.DISABLED)
        self.printMatrixButton.config(state = tk.DISABLED)

        if not self.sentinelFlag:
            for widget in self.sentinelWidgets:
                widget.config(state = tk.DISABLED)
            self.sentinelApplyButton.config(state = tk.DISABLED)

        else:
            self.sentinelClearButton.config(state = tk.DISABLED)

        # Print ................................................................
        self.donePrinting = False

        self.printThread = threading.Thread(
            name = "FCMkII_LT_Printer",
            target = self._printRoutine,
            args = (sentinelValues,)
        )
        self.printThread.setDaemon(True)
        self.printThread.start()

        self._printChecker()

    def _printChecker(self):
        """
        Each call checks if printing should be deactivated.
        """
        if not self.donePrinting:
            self.after(100, self._printChecker)

        else:
            # Unlock table:
            self.playPauseButton.config(state = tk.NORMAL)
            self.printMatrixButton.config(state = tk.NORMAL)
            if not self.sentinelFlag:
                for widget in self.sentinelWidgets:
                    widget.config(state = tk.NORMAL)
                self.sentinelApplyButton.config(state = tk.NORMAL)
                if not self.wasPaused:
                    self._playPause()
            else:
                self.sentinelClearButton.config(state = tk.NORMAL)
                if not self.sentinelPauseVar.get():
                    self._playPause()

    def _printRoutine(self, sentinel = None):
        # FIXME incompatible
        try:
            fileName = "FCMkII_table_print_on_{}.csv".format(
                time.strftime("%a_%d_%b_%Y_%H:%M:%S", time.localtime()))

            self._printM("Printing to file")

            with open(fileName, 'w') as f:
                # File setup ...................................................

                f.write("Fan Club MkII data launched on {}  using "\
                    "profile \"{}\" with a maximum of {} fans.\n"\
                    "Matrix number (since live table was launched): {}\n\n".\
                    format(
                        time.strftime(
                            "%a %d %b %Y %H:%M:%S", time.localtime()),
                        self.profile[ac.name],
                        self.profile[ac.maxFans],
                        self.matrixCount
                        )
                    )

                if sentinel is not None:
                    f.write("NOTE: This data log was activated by a watchdog "\
                        "trigger caused by fan {} of module {} being "\
                        "measured at {} RPM "\
                        "(Condition: \"{}\" if \"{}\" {} RPM)\n".\
                        format(
                            sentinel[0]+1,  # Fan
                            sentinel[1]+1,  # Slave
                            sentinel[2],    # RPM value
                            self.sentinelActionMenuVar.get(),
                            self.sentinelMenuVar.get(),
                            self.sentinelEntry.get()
                            )
                    )

                # Headers (fifth line):

                # Write headers:
                f.write("Module,")

                for column in self.columns[self.specialColumns:]:
                    f.write("{} RPM,".format(column))

                # Move to next line:
                f.write('\n')

                # Write matrix:
                for index, row in enumerate(self.latestMatrix):
                    f.write("{},".format(index+1))
                    for value in row[1:]:
                        f.write("{},".format(value))

                    f.write('\n')

            self.donePrinting = True
            self._printM("Done printing",'G')

        except:
            self._printM("ERROR When printing matrix: {}".\
                format(traceback.print_exc()),'E')
            self.donePrinting = True

        # End _printRoutine ====================================================

    def _playPause(self, event = None, force = None):
        """
        Toggle the play and pause statuses.
         """

        if self.playPauseFlag or force is False:
            self.playPauseFlag = False
            self.playPauseButton.config(text = "Play", bg = 'orange',
                fg = 'white')
        elif not self.playPauseFlag or force is True:
            self.playPauseFlag = True
            self.playPauseButton.config(text = "Pause", bg = self.bg,
                fg = self.fg)

    def _showMenuCallback(self, *event):
        if self.showMenuVar.get() == "RPM":
            self.offset = 0
        elif self.showMenuVar.get() == "DC":
            self.offset = 1

    # Standard interface .......................................................
    def feedbackIn(self, F):
        if self.playPauseFlag:
            # FIXME: performance
            L = len(F)//2
            N = L//self.maxFans

            if N > self.numSlaves:
                for index in range(self.numSlaves, N):
                    self.slaves[index] = self.table.insert('', 'end',
                        values = (index + 1,) + self.zeroes, tag = 'N')
                    self.numSlaves += 1

            slave_i, vector_i = 0, L*self.offset
            end_i = L + vector_i
            tag = "N"
            while vector_i < end_i:
                values = tuple(F[vector_i:vector_i + self.maxFans])

                if std.RIP in values:
                    # This slave is disconnected
                    self.table.item(self.slaves[slave_i],
                        values = (slave_i + 1,), tag = "D")
                elif std.PAD not in values:
                    # This slave is active
                    if self.sentinelFlag:
                        for fan, value in enumerate(values):
                            if self._sentinelCheck(values):
                                tag = "H"
                                self._executeSentinel(slave_i, fan, value)
                    self.table.item(self.slaves[slave_i],
                        values = (slave_i + 1, max(values), min(values)) \
                            + values, tag = tag)
                slave_i += 1
                vector_i += self.maxFans

            self.F_buffer = F

        self.built = True

    @staticmethod
    def _const(dc):
        """
        Return a function that ignores any arguments passed and returns the
        given duty cycle.
        - dc: the value to be returned.
        """
        def f(*_):
            return dc
        return f

class DataLogger(pt.PrintClient):
    """
    Print feedback vectors to CSV files.
    """
    SYMBOL = "[DL]"
    STOP = -69
    S_I_NAME, S_I_MAC = 0, 1


    # NOTE:
    # - you cannot add slaves mid-print, as the back-end process takes only F's
    # NOTE: watchdog?

    def __init__(self, archive, pqueue):
        pt.PrintClient.__init__(self, pqueue)

        self.pipeRecv, self.pipeSend = None, None
        self._buildPipes()
        self.archive = archive
        self.process = None

        self.slaves = {}

    # API ----------------------------------------------------------------------

    def start(self, filename, timeout = std.MP_STOP_TIMEOUT_S,
        script = "[NONE]", mappings = ("[NONE]",)):
        """
        Begin data logging.
        """
        try:
            if self.active():
                self.stop(timeout)
            self._buildPipes()
            arr = self.archive[ac.fanArray]
            self.process = mp.Process(
                name = "FC_Log_Backend",
                target = self._routine,
                args = (
                    filename, self.archive[ac.version], self.slaves,
                    self.archive[ac.name], self.archive[ac.maxFans],
                    (arr[ac.FA_rows], arr[ac.FA_columns], arr[ac.FA_layers]),
                    self.pipeRecv, script, mappings, self.pqueue),
                daemon = True,)
            self.process.start()
            self.prints("Data log started")
        except Exception as e:
            self.printx(e, "Exception activating data log:")
            self._sendStop()

    def stop(self, timeout = std.MP_STOP_TIMEOUT_S):
        """
        Stop data logging.
        """
        try:
            if self.active():
                self.printr("Stopping data log")
                self._sendStop()
                self.process.join(timeout)
                if self.process.is_alive():
                    self.process.terminate()
                self.process = None
                self.printr("Data log stopped")
        except Exception as e:
            self.printx(e, "Exception stopping data log:")
            self._sendStop()

    def active(self):
        """
        Return whether the printer back-end is active.
        """
        return self.process is not None and self.process.is_alive()

    def feedbackIn(self, F, t = 0):
        """
        Process the feedback vector F with timestamp t.
        """
        # FIXME: optm. time stamping
        if self.active():
            self.pipeSend.send((F, t))

    def slavesIn(self, S):
        """
        Process a slave data vector.
        """
        length = len(S)
        i = 0
        while i < length:
            index, name, mac = \
                S[i + std.SD_INDEX] + 1, S[i + std.SD_NAME], S[i + std.SD_MAC]
            if index not in self.slaves:
                self.slaves[index] = (name, mac)
            i += std.SD_LEN

    def networkIn(self, N):
        """
        Process a network state vector.
        """
        pass

    # Internal methods ---------------------------------------------------------
    def _sendStop(self):
        """
        Send the stop signal.
        """
        self.pipeSend.send(self.STOP)

    def _buildPipes(self):
        """
        Reset the pipes. Do not use while the back-end is active.
        """
        self.pipeRecv, self.pipeSend = mp.Pipe(False)

    @staticmethod
    def _routine(filename, version, slaves, profileName, maxFans, dimensions,
        pipeRecv, script, mappings, pqueue):
        """
        Routine executed by the back-end process.
        """

        # FIXME exception handling
        # FIXME watch for thread death

        # FIXME performance
        P = pt.PrintClient(pqueue)
        P.symbol = "[DR]"
        P.printr("Setting up data log")
        with open(filename, 'w') as f:
            # (Header) Log basic data:
            f.write("Fan Club MkIV ({}) data log started on {}  using "\
                "profile \"{}\"\n".format(
                    version,tm.strftime("%a %d %b %Y %H:%M:%S", tm.localtime()),
                    profileName))

            # (Header) filename:
            f.write("Filename: \"{}\"\n".format(filename))

            # (Header) Module breakdown:
            f.write("Modules: |")
            rpm_boilerplate = ""
            dc_boilerplate = ""
            for fan in range(maxFans):
                rpm_boilerplate += "s{0}" + "rpm{},".format(fan + 1)
                dc_boilerplate += "s{0}" + "dc{},".format(fan + 1)
            rpm_headers = ""
            dc_headers = ""
            for index, data in slaves.items():
                name, mac = data
                f.write("\"{}\": {} - \"{}\" | ".format(index, name, mac))
                rpm_headers += rpm_boilerplate.format(index)
                dc_headers += dc_boilerplate.format(index)
            f.write("\n")

            # (Header) Dimensions:
            f.write("Dimensions (rows, columns, layers): {}x{}x{}\n".format(
                *dimensions))

            # (Header) Max fans:
            f.write("Max Fans: {}\n".format(maxFans))

            # (Header) Mappings:
            f.write("Fan Array Mapping(s):\n")
            for i, mapping in enumerate(mappings):
                f.write("\tMapping {}: {}\n".format(i + 1, mapping))

            # (Header) Functions in use:
            fn_temp = "Script (Flattened. Replace ; for newline):\n"
            f.write(fn_temp + script + "\n")

            # Header (3/4)
            f.write("Column headers are of the form s[MODULE#][type][FAN#]"\
                "with type being first \"rpm\" and then all \"dc\"\n")

            # Header (4/4):
            f.write("Time (s)," + rpm_headers + dc_headers + "\n")

            P.prints("Data log online")
            t_start = tm.time()
            while True:
                # FIXME performance
                data = pipeRecv.recv()
                if data == DataLogger.STOP:
                    break
                F, t = data
                f.write("{},".format(t - t_start))
                for item in F:
                    f.write("{},".format(item if item != -666 else 'NaN'))
                f.write("\n")
        P.printr("Data logger back-end ending")


## DEMO ########################################################################
if __name__ == "__main__":
    print("FCMkIV Control GUI demo started")
    mw = tk.Tk()
    CW = ControlWidget(mw, print, print)
    CW.pack(fill = tk.BOTH, expand = True)
    mw.mainloop()

    print("FCMkIV Control GUI demo finished")
