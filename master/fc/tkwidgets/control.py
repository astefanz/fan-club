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

## IMPORTS #####################################################################
import os
import time as tm

import tkinter as tk
import tkinter.filedialog as fdg
import tkinter.ttk as ttk
import tkinter.font as fnt

from . import guiutils as gus, grid as gd, loader as ldr
from .embedded import colormaps as cms

## GLOBALS #####################################################################

## WIDGETS #####################################################################
class PythonInputWidget(tk.Frame):
    """
    Base class for a widget for Python code input.
    """

    HEADER = "def duty_cycle(r, c, l, p, d, t):"
    FOOTER = "self.func = duty_cycle"

    def __init__(self, master, callback, printr, printx): # FIXME params
        """
        Create a Python input widget in which the user may define a function
        of the form
            f(r, c, l, p, d, t)
              |  |  |  |  |  |
              |  |  |  |  |  time
              |  |  |  |  duty cycle
              |  |  |  RPM
              |  |  layer
              |  column
              row

        CALLBACK is a method to which to pass the resulting Python function
        after being parsed and instantiated.
        """
        tk.Frame.__init__(self, master)

        self.callback = callback
        self.printr = printr
        self.printx = printx

        self.grid_rowconfigure(1, weight = 1)
        self.grid_columnconfigure(1, weight = 1)
        row = 0

        self.topLabel = tk.Label(self, font = "Courier 7 bold",
            text = self.HEADER, anchor = tk.W)
        self.topLabel.grid(row = row, column = 0, columnspan = 2, sticky = "EW")
        row += 1

        self.font = tk.font.Font(font = "Courier 7 bold")
        self.tabstr = "  "
        self.tabsize = self.font.measure(self.tabstr)
        self.realtabs = "    "

        self.indent = tk.Label(self, font = self.font, text = self.tabstr)
        self.indent.grid(row = row, column = 0, sticky = "NS")

        self.text = tk.Text(self, font = self.font,
            width = 30, height = 2, padx = 10, pady = 0, bg = 'black',
            fg = 'lightgray', insertbackground = "#ff6e1f",
            tabs = self.tabsize)
        self.text.grid(row = row, column = 1, rowspan = 2, sticky = "NEWS")

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
        self.runButton = tk.Button(self.buttonFrame, text = "Run",
            command = self._run, **gus.padc, **gus.fontc)
        self.runButton.pack(side = tk.LEFT, **gus.padc)

        self.loader = ldr.LoaderWidget(self.buttonFrame,
            filetypes = (("Fan Club Python Procedures", ".fcpy"),),
            onSave = self._onSave, onLoad = self._onLoad)
        self.loader.pack(side = tk.LEFT)

        # TODO
        self.builtinButton = tk.Button(self.buttonFrame, text = "Built-in",
            **gus.padc, **gus.fontc, command = self._builtin)
        self.builtinButton.pack(side = tk.LEFT, **gus.padc)

        # TODO
        self.helpButton = tk.Button(self.buttonFrame, text = "Help",
            **gus.padc, **gus.fontc, command = self._help)
        self.helpButton.pack(side = tk.LEFT, **gus.padc)

    def _run(self, *E):
        """
        To be called when the Run button is clicked. Parse the function and
        pass it to the given callback.
        """
        try:
            raw = self.text.get(1.0, tk.END)
            retabbed = raw.replace('\t', self.realtabs)

            built = self.HEADER + '\n'
            for line in retabbed.split('\n'):
                built += self.realtabs + line + '\n'
            built += self.FOOTER + '\n'

            exec(built) # TODO: fix security hole in exec
            self.callback(self.func)

        except Exception as e:
            self.printx("Exception when parsing Python input:", e)

    def _onLoad(self, contents):
        """
        To be executed by the Load routine within a LoaderWidget.
        """
        print("[WARNING] FCPY not yet implemented")
        print(contents)

    def _builtin(self, *E):
        """
        To be executed by the Built-in button.
        """
        print("[WARNING] _builtin not implemented ")

    def _onSave(self, *E):
        """
        To be executed by the Save routine within a LoaderWidget.
        """
        print("[WARNING] _save not implemented ")

    def _help(self, *E):
        """
        To be executed by Help button.
        """
        print("[WARNING] _help not implemented ")

    # FIXME API

class SteadyControlWidget(tk.Frame):
    """
    Container for the steady flow control tools.
    """

    """ Codes for direct input modes. """
    DI_SELECT = 55
    DI_DRAW = 65

    def __init__(self, master, network,
        printr = lambda s:None, printx = lambda e:None):
        tk.Frame.__init__(self, master)

        # Setup ................................................................
        self.network = network
        self.grid_columnconfigure(0, weight = 1)
        row = 0

        # Callbacks:
        self.selectAll = self._nothing
        self.deselectAll = self._nothing


        # Direct input .........................................................
        self.directFrame = tk.LabelFrame(self, text = "Direct input",
            **gus.lfconf)
        self.directFrame.grid(row = row, sticky = "EW")
        row += 1

        self.directMode = tk.IntVar()
        self.selectButton = tk.Radiobutton(self.directFrame,
            variable = self.directMode, value = self.DI_SELECT, text = "Select",
            **gus.rbconf)
        self.selectButton.pack(side = tk.LEFT, **gus.padc)
        self.drawButton = tk.Radiobutton(self.directFrame, text = "Draw",
            variable = self.directMode, value = self.DI_DRAW, **gus.rbconf)
        self.drawButton.pack(side = tk.LEFT, **gus.padc)
        self.directMode.trace('w', self._onDirectModeChange)

        self.directValueEntry = tk.Entry(self.directFrame, **gus.efont, width = 6)
        self.directValueEntry.pack(side = tk.LEFT, **gus.padc)
        # FIXME validate
        self.sendDirectButton = tk.Button(self.directFrame, text = "Send",
            **gus.padc, **gus.fontc, command = self._sendDirect)
        self.sendDirectButton.pack(side = tk.LEFT, **gus.padc)

        # FIXME keyboard bindings

        # Random flow ..........................................................
        self.randomFrame = tk.LabelFrame(self, text = "Random Flow",
            **gus.lfconf)
        self.randomFrame.grid(row = row, sticky = "EW")
        row += 1

        self.leftB = tk.Label(self.randomFrame, text = "[", **gus.fontc)
        self.leftB.pack(side = tk.LEFT)

        # FIXME validate
        self.randomLow = tk.Entry(self.randomFrame, **gus.fontc, width = 5)
        self.randomLow.pack(side = tk.LEFT)

        self.comma = tk.Label(self.randomFrame, text = ", ", **gus.efont)
        self.comma.pack(side = tk.LEFT)

        # FIXME validate
        self.randomHigh = tk.Entry(self.randomFrame, **gus.efont, width = 5)
        self.randomHigh.pack(side = tk.LEFT)

        self.rightB = tk.Label(self.randomFrame, text = "]", **gus.fontc)
        self.rightB.pack(side = tk.LEFT)

        self.sendRandomButton = tk.Button(self.randomFrame, text = "Send",
            **gus.padc, **gus.fontc, command = self._sendRandom)
        self.sendRandomButton.pack(side = tk.LEFT, **gus.padc)

        # Python interpreter
        self.grid_rowconfigure(row, weight = 1)
        self.pythonFrame = tk.LabelFrame(self, text = "Python",
            **gus.lfconf)
        self.pythonFrame.grid(row = row, sticky = "NEWS")
        row += 1
        self.python = PythonInputWidget(self.pythonFrame, self._sendPython,
            lambda m: print(m), lambda x, m: print(x, m)) # FIXME
        self.python.pack(fill = tk.BOTH, expand = True)
        # FIXME configure python

        # File
        self.fileFrame = tk.LabelFrame(self, text = "Load/Save Flows",
            **gus.lfconf)
        self.fileFrame.grid(row = row, sticky = "EW")
        row += 1

        self.loader = ldr.FlowLoaderWidget(self.fileFrame, self._onSave,
            self._onLoad)
        self.loader.pack(side = tk.LEFT)

        # Wrap-up
        self.directMode.set(self.DI_SELECT)

    # API ......................................................................


    # Internal methods .........................................................
    def _sendDirect(self, *E):
        """
        Send a "direct input" command using the given send callback.
        """
        # FIXME
        pass

    def _sendRandom(self, *E):
        """
        Send a randomly-generated magnitude command using the given send
        callback.
        """
        # FIXME
        pass

    def _sendPython(self, function, *E):
        """
        Send a command generated by the Python input.
        """
        print("[WARNING] Python input not yet available. Received ",
            function)
        # FIXME
        pass

    def _onSave(self):
        """
        Save callback for FlowLoader.
        """
        # FIXME
        print("[WARNING] _onSave not implemented")

    def _onLoad(self, loaded):
        """
        Load callback for FlowLoader.
        """
        # FIXME
        print("[WARNING] _onLoad not implemented")

    def _onDirectModeChange(self, *E):
        """
        To be called when the direct input mode is changed.
        """
        self.deselectAll()

    @staticmethod
    def _nothing(*A):
        """
        Placeholder function to serve as a default callback.
        """
        pass

    # FIXME

class DynamicControlWidget(tk.Frame):
    """
    Container for the steady flow control tools.
    """

    def __init__(self, master, printr = lambda s:None, printx = lambda e:None):
        tk.Frame.__init__(self, master)

        self.grid_columnconfigure(0, weight = 1)
        row = 0

        # Python interpreter
        self.grid_rowconfigure(row, weight = 1)
        self.pythonFrame = tk.LabelFrame(self, text = "Python",
            **gus.lfconf)
        self.pythonFrame.grid(row = row, sticky = "NEWS")
        row += 1
        self.python = PythonInputWidget(self.pythonFrame, self._sendPython,
            lambda m: print(m), lambda x, m: print(x, m)) # FIXME
        self.python.pack(fill = tk.BOTH, expand = True)
        # FIXME configure python

        # File
        self.fileFrame = tk.LabelFrame(self, text = "Load/Save Flows",
            **gus.lfconf)
        self.fileFrame.grid(row = row, sticky = "EW")
        row += 1

        self.loader = ldr.FlowLoaderWidget(self.fileFrame, self._onSave,
            self._onLoad)
        self.loader.pack(side = tk.LEFT)

    def _sendPython(self, function, *E):
        """
        Python input callback.
        """
        # FIXME
        print("[WARNING] _sendPython not implemented")

    def _onSave(self):
        """
        Save callback for FlowLoader.
        """
        # FIXME
        print("[WARNING] _onSave not implemented")

    def _onLoad(self, loaded):
        """
        Load callback for FlowLoader.
        """
        # FIXME
        print("[WARNING] _onLoad not implemented")

class ExternalControlWidget(tk.Frame):
    """
    Container for the "external" control tools.
    """

    def __init__(self, master, printr = lambda s:None, printx = lambda e:None):
        tk.Frame.__init__(self, master)
        l = tk.Label(self, text = "[External control goes here]")
        l.pack(fill = tk.BOTH, expand = True)
        # FIXME
    # FIXME

class ControlPanelWidget(tk.Frame):
    """
    Container for the control GUI tools and peripherals.
    """

    """ Codes for view modes. """
    VM_LIVE = 690
    VM_BUILDER = 691

    def __init__(self, master, network,
        printr = lambda s:None, printx = lambda e:None):
        tk.Frame.__init__(self, master)

        # Setup ................................................................
        self.network = network
        self.grid_columnconfigure(0, weight = 1)
        row = 0

        self.F = fnt.Font(family = 'TkDefaultFont', size = 7)
        self.S = ttk.Style()
        self.S.configure('.', font = self.F)

        # TODO: Callbacks and validations

        # Mode and layer .......................................................
        self.viewFrame = tk.LabelFrame(self, text = "View", **gus.fontc)
        self.viewFrame.grid(row = row, sticky = "EW")
        row += 1

        self.viewVar = tk.IntVar()
        self.viewVar.trace('w', self._onModeChange)
        self.liveButton = tk.Radiobutton(self.viewFrame,
            variable = self.viewVar, value = self.VM_LIVE, text = "Real Time",
            **gus.rbconf)
        self.liveButton.pack(side = tk.LEFT, pady = 5)
        self.builderButton = tk.Radiobutton(self.viewFrame,
            variable = self.viewVar, value = self.VM_BUILDER,
            text = "Flow Builder", **gus.rbconf)
        self.builderButton.pack(side = tk.LEFT, pady = 5)

        self.layerFrame = tk.Frame(self.viewFrame)
        self.layerFrame.pack(side = tk.LEFT, **gus.padc)
        self.layerLabel = tk.Label(self.layerFrame, text = "Layer: ",
            **gus.fontc, **gus.padc)
        self.layerLabel.pack(side = tk.LEFT, **gus.padc)
        self.layerVar = tk.IntVar()
        self.layerVar.trace('w', self._onLayerChange)
        self.layerMenu = tk.OptionMenu(self.layerFrame, self.layerVar, 1)
        self.layerMenu.config(**gus.fontc)
        self.layerMenu.pack(side = tk.LEFT, **gus.padc)

        # Flow control .........................................................
        self.grid_rowconfigure(row, weight = 1) # FIXME
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row = row, sticky = "NEWS")
        row += 1

        # Steady ...............................................................
        self.steady = SteadyControlWidget(self.notebook, printr, printx)
        self.notebook.add(self.steady, text = "Steady Flow")

        # Dynamic ..............................................................
        self.dynamic = DynamicControlWidget(self.notebook, printr, printx)
        self.notebook.add(self.dynamic, text = "Dynamic Flow",
            state = tk.NORMAL)

        # External .............................................................
        self.external = ExternalControlWidget(self.notebook, printr, printx)
        self.notebook.add(self.external, text = "External Control",
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
        self.fileButton = tk.Button(self.fileFrame, text = "...", **gus.fontc,
            **gus.padc)
        self.fileButton.pack(side = tk.LEFT, **gus.padc)

        self.recordControlFrame = tk.Frame(self.recordFrame)
        self.recordControlFrame.pack(side = tk.TOP, fill = tk.X, expand = True,
            **gus.padc)
        self.recordStartButton = tk.Button(self.recordControlFrame,
            text = "Start", **gus.fontc, **gus.padc)
        self.recordStartButton.pack(side = tk.LEFT)
        self.recordPauseButton = tk.Button(self.recordControlFrame,
            text = "Pause", **gus.fontc, **gus.padc, state = tk.DISABLED)
        self.recordPauseButton.pack(side = tk.LEFT, padx = 10)

        # Matrix count .........................................................
        self.matrixCountFrame = tk.LabelFrame(self, **gus.lfconf,
            text = "Diagnostics")
        self.matrixCountFrame.grid(row = row, sticky = "EW")
        row += 1
        self.matrixCountLabel = tk.Label(self.matrixCountFrame,
            text = "Matrix: ", **gus.fontc, **gus.padc)
        self.matrixCountLabel.pack(side = tk.LEFT, **gus.padc)
        self.matrixCountVar = tk.IntVar()
        self.matrixCountVar.set(0)
        self.matrixDisplay = tk.Label(self.matrixCountFrame,
            textvariable = self.matrixCountVar, font = "Courier 7",
            bg = "lightgray", relief = tk.SUNKEN, bd = 1)
        self.matrixDisplay.pack(side = tk.LEFT, fill = tk.X, expand = True)

        # Wrap-up ..............................................................
        self.viewVar.set(self.VM_LIVE)
        self.layerVar.set(1)

    # API ......................................................................
    # FIXME

    # TODO: Set layers?

    # Internal methods .........................................................
    def _onModeChange(self, *A):
        """
        To be called when the view mode is changed (between live mode and flow
        builder.)
        """
        # TODO
        pass

    def _onLayerChange(self, *A):
        """
        To be called when the view layer is changed.
        """
        # TODO
        pass

class GridWidget(gd.BaseGrid):
    """
    Front end for the 2D interactive Grid.
    """

    DEFAULT_COLORS = cms.COLORMAP_GALCIT_REVERSED
    DEFAULT_OFF_COLOR = "#303030"
    DEFAULT_HIGH = 100
    DEFAULT_LOW = 0
    CURSOR = "hand1"

    def __init__(self, master, R, C, colors = DEFAULT_COLORS,
        off_color = DEFAULT_OFF_COLOR, high = DEFAULT_HIGH,
        low = DEFAULT_LOW, printr = lambda s:None, printx = lambda e:None):
        # Setup ................................................................
        gd.BaseGrid.__init__(self, master, R, C, cursor = self.CURSOR,
            empty = off_color)
        self.adjusting = False
        self.last_width, self.last_height = 0, 0
        self.colors = colors
        self.numColors = len(colors)
        self.maxColor = self.numColors - 1
        self.high = high
        self.low = low
        self.off_color = off_color

        # FIXME

    def update(self, values):
        i = 0
        for value in values:
            self.setLinear(i, fill = self.colors[min(self.maxColor,
                (value*self.maxColor//self.numColors))])
            i += 1

    def select(self, r, c):
        # FIXME
        pass

    def deselect(self, r, c):
        # FIXME
        pass

    def selectAll(self, r, c):
        # FIXME
        pass

    def deselectAll(self, r, c):
        # FIXME
        pass

    def redraw(self, *E):
        self.draw(margin = 10)
        self.canvas.bind("<Button-1>", self.__testbind) # FIXME

    def __testbind(self, *E)
        print("[DEV] __testbind")
        self.update([i for i in range(self.R*self.C)])

    # FIXME


class ColorBarWidget(tk.Frame):
    """
    Draw a vertical color gradient for color-coding reference.
    """
    def __init__(self, master, colors, high = 100, low = 0, unit = "[?]",
        printr = lambda s:None, printx = lambda e:None):


        # Setup ................................................................
        tk.Frame.__init__(self, master)
        self.printr, self.printx = printr, printx
        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure(1, weight = 1)
        self.colors = colors
        self.steps = len(colors)

        # Widgets ..............................................................
        self.highLabel = tk.Label(self, text = "{} {}".format(high, unit),
            font = "Courier 5", bg = "black", fg = "white")
        self.highLabel.grid(row = 0, sticky = "EW")

        self.canvas = tk.Canvas(self, bg = self.colors[-1],
            width = self.highLabel.winfo_width())
        self.canvas.grid(row = 1, sticky = 'NEWS')

        self.lowLabel = tk.Label(self, text = "{} {}".format(low, unit),
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

    # Internal methods .........................................................
    def _draw(self, *E):
        """
        Draw the colorbar.
        """
        height = max(self.winfo_height(), self.winfo_reqheight())
        width = self.highLabel.winfo_reqwidth()
        step = max(height/self.steps, 3)
        left, right = 0, width
        y = 0
        for i in range(self.steps):
            iid = self.canvas.create_rectangle(
                left, y, right, y + step, fill = self.colors[i], width = 0)
            self.canvas.tag_bind(iid, "<ButtonPress-1>", self.redraw)
            y += step
        self.canvas.create_line(left, y, right, y, width = 4)
        self.canvas.create_line(left, y, right, y, width = 2, fill = 'white')

## BASE ########################################################################
class ControlWidget(tk.Frame):
    """
    Container for all the FC control GUI front-end widgets.
    """

    RESIZE_MS = 400

    def __init__(self, master, network,
        printr = lambda s:None, printx = lambda e:None):
        tk.Frame.__init__(self, master)

        # Core setup -----------------------------------------------------------
        self.main = ttk.PanedWindow(self, orient = tk.HORIZONTAL)
        self.main.pack(fill = tk.BOTH, expand = True)
        self.bind("<Configure>", self._scheduleAdjust)

        # Control panel --------------------------------------------------------
        # FIXME
        self.control = ControlPanelWidget(self.main, network, printr, printx)
        self.main.add(self.control, weight = 2)
        # Grid -----------------------------------------------------------------
        # FIXME
        self.grid = GridWidget(self.main, 32, 32, printr = printr,
            printx = printx)
        self.main.add(self.grid, weight = 16)

        # Color Bar ------------------------------------------------------------
        # FIXME
        self.bar = ColorBarWidget(self.main,
            colors = cms.COLORMAP_GALCIT, printr = printr, printx = printx,
            unit = "RPM")
        self.main.add(self.bar, weight = 0)
        # Wrap-up --------------------------------------------------------------
        # FIXME

    # FIXME: API
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

    def redrawGrid(self):
        """
        Rebuild the grid widget.
        """
        self.grid.redraw()

    def _scheduleAdjust(self, *E):
        self.after(self.RESIZE_MS, self._adjust)
        self.unbind("<Configure>")

    def _adjust(self, *E):
        self.grid.redraw()
        self.bar.redraw()
        self.bind("<Configure>", self._scheduleAdjust)

## DEMO ########################################################################
if __name__ == "__main__":
    print("FCMkIV Control GUI demo started")
    mw = tk.Tk()
    CW = ControlWidget(mw, print, print)
    CW.pack(fill = tk.BOTH, expand = True)
    mw.mainloop()

    print("FCMkIV Control GUI demo finished")
