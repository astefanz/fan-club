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

if __name__ == "__main__":
    import embedded.colormaps as cms
    import grid as gd
else:
    from .embedded import colormaps as cms
    from . import grid as gd

## GLOBALS #####################################################################
# Pre-defined configurations:
efont = {"font":"Courier 7"}
fontc = {"font":"TkDefaultFont 7"}
padc = {"padx":5, "pady":5}
lfconf = {**fontc, **padc}
lfpack = {"side":tk.TOP, "anchor":tk.N, "fill":tk.X, "expand":True}
rbconf = {"indicatoron":False, **fontc, **padc}

## WIDGETS #####################################################################
class SteadyControlWidget(tk.Frame):
    """
    Container for the steady flow control tools.
    """

    """ Codes for direct input modes. """
    DI_SELECT = 55
    DI_DRAW = 65

    def __init__(self, master, printr = lambda s:None, printx = lambda e:None):
        # Setup ................................................................
        tk.Frame.__init__(self, master)
        self.grid_columnconfigure(0, weight = 1)
        row = 0

        # Callbacks:
        self._loadCallback = self._nothing
        self.saveCallback = self._nothing
        self.sendCallback = self._nothing
        self.selectAll = self._nothing
        self.deselectAll = self._nothing


        # Direct input .........................................................
        self.directFrame = tk.LabelFrame(self, text = "Direct input", **lfconf)
        self.directFrame.grid(row = row, sticky = "EW")
        row += 1

        self.directMode = tk.IntVar()
        self.selectButton = tk.Radiobutton(self.directFrame,
            variable = self.directMode, value = self.DI_SELECT, text = "Select",
            **rbconf)
        self.selectButton.pack(side = tk.LEFT, **padc)
        self.drawButton = tk.Radiobutton(self.directFrame, text = "Draw",
            variable = self.directMode, value = self.DI_DRAW, **rbconf)
        self.drawButton.pack(side = tk.LEFT, **padc)
        self.directMode.trace('w', self._onDirectModeChange)

        self.directValueEntry = tk.Entry(self.directFrame, **efont, width = 6)
        self.directValueEntry.pack(side = tk.LEFT, **padc)
        # FIXME validate
        self.sendDirectButton = tk.Button(self.directFrame, text = "Send",
            **padc, **fontc, command = self._sendDirect)
        self.sendDirectButton.pack(side = tk.LEFT, **padc)

        # FIXME keyboard bindings

        # Random flow ..........................................................
        self.randomFrame = tk.LabelFrame(self, text = "Random Flow", **lfconf)
        self.randomFrame.grid(row = row, sticky = "EW")
        row += 1

        self.leftB = tk.Label(self.randomFrame, text = "[", **fontc)
        self.leftB.pack(side = tk.LEFT)

        # FIXME validate
        self.randomLow = tk.Entry(self.randomFrame, **fontc, width = 5)
        self.randomLow.pack(side = tk.LEFT)

        self.comma = tk.Label(self.randomFrame, text = ", ", **efont)
        self.comma.pack(side = tk.LEFT)

        # FIXME validate
        self.randomHigh = tk.Entry(self.randomFrame, **efont, width = 5)
        self.randomHigh.pack(side = tk.LEFT)

        self.rightB = tk.Label(self.randomFrame, text = "]", **fontc)
        self.rightB.pack(side = tk.LEFT)

        self.sendRandomButton = tk.Button(self.randomFrame, text = "Send",
            **padc, **fontc, command = self._sendRandom)
        self.sendRandomButton.pack(side = tk.LEFT, **padc)

        # Python interpreter
        self.pythonFrame = tk.LabelFrame(self, text = "Python (Expression)",
            **lfconf)
        self.pythonFrame.grid(row = row, sticky = "NEWS")
        row += 1

        self.pythonFrame.grid_rowconfigure(0, weight = 1)
        self.pythonFrame.grid_columnconfigure(0, weight = 1)

        self.pythonText = tk.Text(self.pythonFrame, font = "Courier 7 bold",
            width = 30, height = 2, padx = 10, pady = 10, bg = 'black',
            fg = 'lightgray', insertbackground = "#ff6e1f")
        self.pythonText.grid(row = 0, column = 0, sticky = "NEWS")

        # For scrollbar, see:
        # https://www.python-course.eu/tkinter_text_widget.php

        self.pythonScrollbar = tk.Scrollbar(self.pythonFrame)
        self.pythonScrollbar.grid(row = 0, column = 1, sticky = "NS")
        self.pythonScrollbar.config(command = self.pythonText.yview)
        self.pythonText.config(yscrollcommand = self.pythonScrollbar.set)

        self.pythonButtonFrame = tk.Frame(self.pythonFrame)
        self.pythonButtonFrame.grid(row = 1, column = 0, sticky = "WE")
        self.pythonSend = tk.Button(self.pythonButtonFrame, text = "Run",
            **padc, **fontc)
        self.pythonSend.pack(side = tk.LEFT, **padc)
        self.pythonHelp = tk.Button(self.pythonButtonFrame, text = "Help",
            **padc, **fontc)
        self.pythonHelp.pack(side = tk.LEFT, **padc)

        # File
        self.fileFrame = tk.LabelFrame(self, text = "Load/Save", **lfconf)
        self.fileFrame.grid(row = row, sticky = "EW")
        row += 1
        self.loadButton = tk.Button(self.fileFrame, text = "Load",
            **padc, **fontc, command = self._load)
        self.loadButton.pack(side = tk.LEFT, **padc)
        self.saveButton = tk.Button(self.fileFrame, text = "Save",
            **padc, **fontc, command = self._save)
        self.saveButton.pack(side = tk.LEFT, **padc)


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

    def _sendPython(self, *E):
        """
        Send a command generated from a Python expression.
        """
        # FIXME
        pass

    def _save(self, *E):
        """
        Save the current state. (Calls the save callback.)
        """
        self.saveCallback()

    def _load(self, *E):
        """
        Load a saved state. (Calls the load callback.)
        """
        self.loadCallback()

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
        l = tk.Label(self, text = "[Dynamic control goes here]")
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

    def __init__(self, master, printr = lambda s:None, printx = lambda e:None):
        # Setup ................................................................
        tk.Frame.__init__(self, master)
        self.grid_columnconfigure(0, weight = 1)
        row = 0

        self.F = fnt.Font(family = 'TkDefaultFont', size = 7)
        self.S = ttk.Style()
        self.S.configure('.', font = self.F)

        # TODO: Callbacks and validations

        # Mode and layer .......................................................
        self.viewFrame = tk.LabelFrame(self, text = "View", **fontc)
        self.viewFrame.grid(row = row, sticky = "EW")
        row += 1

        self.viewVar = tk.IntVar()
        self.viewVar.trace('w', self._onModeChange)
        self.liveButton = tk.Radiobutton(self.viewFrame,
            variable = self.viewVar, value = self.VM_LIVE, text = "Real Time",
            **rbconf)
        self.liveButton.pack(side = tk.LEFT, pady = 5)
        self.builderButton = tk.Radiobutton(self.viewFrame,
            variable = self.viewVar, value = self.VM_BUILDER,
            text = "Flow Builder", **rbconf)
        self.builderButton.pack(side = tk.LEFT, pady = 5)

        self.layerFrame = tk.Frame(self.viewFrame)
        self.layerFrame.pack(side = tk.LEFT, **padc)
        self.layerLabel = tk.Label(self.layerFrame, text = "Layer: ",
            **fontc, **padc)
        self.layerLabel.pack(side = tk.LEFT, **padc)
        self.layerVar = tk.IntVar()
        self.layerVar.trace('w', self._onLayerChange)
        self.layerMenu = tk.OptionMenu(self.layerFrame, self.layerVar, 1)
        self.layerMenu.config(**fontc)
        self.layerMenu.pack(side = tk.LEFT, **padc)

        # Flow control .........................................................
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row = row, sticky = "NEWS")
        row += 1

        # Steady ...............................................................
        self.steady = SteadyControlWidget(self.notebook, printr, printx)
        self.notebook.add(self.steady, text = "Steady Flow")

        # Dynamic ..............................................................
        self.dynamic = DynamicControlWidget(self.notebook, printr, printx)
        self.notebook.add(self.dynamic, text = "Dynamic Flow",
            state = tk.DISABLED)

        # Record ...............................................................
        # Add spacer:
        self.grid_rowconfigure(row, weight = 1)
        row += 1

        self.recordFrame = tk.LabelFrame(self, text = "Record Data", **fontc)
        self.recordFrame.grid(row = row, sticky = "EW")
        row += 1

        self.fileFrame = tk.Frame(self.recordFrame)
        self.fileFrame.pack(side = tk.TOP, fill = tk.X, expand = True)

        self.fileLabel = tk.Label(self.fileFrame, text = "File: ",
            **fontc, **padc)
        self.fileLabel.pack(side = tk.LEFT)
        self.fileField = tk.Entry(self.fileFrame, **fontc, width = 20,
            state = tk.DISABLED)
        self.fileField.pack(side = tk.LEFT, fill = tk.X, expand = True)
        self.fileButton = tk.Button(self.fileFrame, text = "...", **fontc,
            **padc)
        self.fileButton.pack(side = tk.LEFT, **padc)

        self.recordControlFrame = tk.Frame(self.recordFrame)
        self.recordControlFrame.pack(side = tk.TOP, fill = tk.X, expand = True,
            **padc)
        self.recordStartButton = tk.Button(self.recordControlFrame,
            text = "Start", **fontc, **padc)
        self.recordStartButton.pack(side = tk.LEFT)
        self.recordPauseButton = tk.Button(self.recordControlFrame,
            text = "Pause", **fontc, **padc, state = tk.DISABLED)
        self.recordPauseButton.pack(side = tk.LEFT, padx = 10)

        # Matrix count .........................................................
        self.matrixCountFrame = tk.LabelFrame(self, **lfconf,
            text = "Diagnostics")
        self.matrixCountFrame.grid(row = row, sticky = "EW")
        row += 1
        self.matrixCountLabel = tk.Label(self.matrixCountFrame,
            text = "Matrix: ", **fontc, **padc)
        self.matrixCountLabel.pack(side = tk.LEFT, **padc)
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
    def __init__(self, master, R, C, printr = lambda s:None,
        printx = lambda e:None):
        # Setup ................................................................
        gd.BaseGrid.__init__(self, master, R, C)
        self.config(cursor = "fleur")
        self.bind("<ButtonPress-1>", self.d)

        self.d()
        # FIXME

    def d(self, *E):
        self.draw(margin = 10)
        self.canvas.bind("<ButtonPress-1>", self.d)

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
        self.colors.reverse()
        self.steps = len(colors)
        self.config(cursor = "sb_v_double_arrow")

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

        self.canvas.bind("<ButtonPress-1>", self.redraw)

        self._draw()

    # API ......................................................................

    # TODO: Set top and bottom?

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

    # FIXME?


## BASE ########################################################################
class ControlWidget(tk.Frame):
    """
    Container for all the FC control GUI front-end widgets.
    """
    def __init__(self, master, printr = lambda s:None, printx = lambda e:None):
        # Core setup -----------------------------------------------------------
        tk.Frame.__init__(self, master)
        self.main = ttk.PanedWindow(self, orient = tk.HORIZONTAL)
        self.main.pack(fill = tk.BOTH, expand = True)

        # Control panel --------------------------------------------------------
        # FIXME
        self.control = ControlPanelWidget(self.main, printr, printx)
        self.main.add(self.control, weight = 2)
        # Grid -----------------------------------------------------------------
        # FIXME
        self.grid = GridWidget(self.main, 32, 32, printr, printx)
        self.main.add(self.grid, weight = 16)

        # Color Bar ------------------------------------------------------------
        # FIXME
        self.bar = ColorBarWidget(self.main,
            colors = cms.COLORMAP_GALCIT, printr = printr, printx = printx)
        self.main.add(self.bar, weight = 0)
        # Wrap-up --------------------------------------------------------------
        # FIXME

    # FIXME: API

## DEMO ########################################################################
if __name__ == "__main__":
    print("FCMkIV Control GUI demo started")
    mw = tk.Tk()
    CW = ControlWidget(mw, print, print)
    CW.pack(fill = tk.BOTH, expand = True)
    mw.mainloop()

    print("FCMkIV Control GUI demo finished")
