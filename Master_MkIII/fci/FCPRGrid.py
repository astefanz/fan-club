################################################################################
## Project: Fan Club Mark II "Master" ## File: FCPRGrid.py                    ##
##----------------------------------------------------------------------------##
## CALIFORNIA INSTITUTE OF TECHNOLOGY ## GRADUATE AEROSPACE LABORATORY ##     ##
## CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES                             ##
##----------------------------------------------------------------------------##
##      ____      __      __  __      _____      __      __    __    ____     ##
##     / __/|   _/ /|    / / / /|  _- __ __\    / /|    / /|  / /|  / _  \    ##
##    / /_ |/  / /  /|  /  // /|/ / /|__| _|   / /|    / /|  / /|/ /   --||   ##
##   / __/|/ _/    /|/ /   / /|/ / /|    __   / /|    / /|  / /|/ / _  \|/    ##
##  / /|_|/ /  /  /|/ / // //|/ / /|__- / /  / /___  / -|_ - /|/ /     /|     ##
## /_/|/   /_/ /_/|/ /_/ /_/|/ |\ ___--|_|  /_____/| |-___-_|/  /____-/|/     ##
## |_|/    |_|/|_|/  |_|/|_|/   \|___|-    |_____|/   |___|     |____|/       ##
##                   _ _    _    ___   _  _      __   __                      ##
##                  | | |  | |  | T_| | || |    |  | |  |                     ##
##                  | _ |  |T|  |  |  |  _|      ||   ||                      ##
##                  || || |_ _| |_|_| |_| _|    |__| |__|                     ##
##                                                                            ##
##----------------------------------------------------------------------------##
## Alejandro A. Stefan Zavala ## <alestefanz@hotmail.com> ##                  ##
################################################################################

## ABOUT #######################################################################
"""
This module is a multiprocessing wrapper around the FC Grid widget.

"""
################################################################################

## DEPENDENCIES ################################################################

# GUI:
#from mttkinter import mtTkinter as Tk
import tkinter as Tk
import tkinter.ttk
import tkinter.font

# System:
import sys            # Exception handling
import traceback    # More exception handling
import random        # Random names, boy
import threading    # Multitasking
import _thread        # thread.error
import multiprocessing as pr # The big guns

# Data:
import time            # Timing
import queue
import copy as cp
import random as rd
import parser
from math import * # Use this way for parser

# FCMkII:
import FCCommunicator as cm
import FCSlave as sv
import FCArchiver as ac
import FCWidget as wg
import FCMainWindow as mw

import auxiliary.colormaps as cs
from auxiliary.debug import d

## CONSTANTS ###################################################################

# Commands:
STOP = -1
# Button text:
START_TEXT = "Activate Grid"
STOP_TEXT = "Deactivate Grid"
STARTING_TEXT = "Activating Grid"
STOPPING_TEXT = "Deactivating Grid"

# Color map
COLORMAP = list(reversed(cs.COLORMAP_GALCIT))

# Special colors:
OUTLINE_SELECTED = 'orange'
OUTLINE_DESELECTED = 'black'
COLOR_OFF = '#282828'
COLOR_EMPTY = 'red' # 'darkgray'

COLOR_SELECTOR_STD = '#939292'
COLOR_SELECTOR_CLICKED = '#7c7c7c'

# Special index values:

# Slave-to-selection list:
STS_COUNTER = 0
STS_LIST = 1

# IIDsToFans list:
ITF_INDEX = 0

# Display variable values:
ARRAY = 1
PREVIEW = 2

# Commands:
SELECT = "Select"
TRACE = "Trace"

SELECT_CODE = 1
TRACE_CODE = 2

# Cursors:
SELECT_CURSOR = "cross"
TRACE_CURSOR = "pencil"


## PROCESS WIDGET ##############################################################

class FCPRGridProcessWidget(Tk.Frame):

    def __init__(
        self,
        profile,
        updatePipeOut,
        misoMatrixPipeOut,
        commandQueue,
        printQueue
    ): # =======================================================================

        # INITIAL DATA SETUP
        Tk.Frame.__init__(self)
        self.master.protocol("WM_DELETE_WINDOW", self._stop)
        self.master.title("FCMkII Grid")

        self.bg = "#e2e2e2"
        self.fg = "black"

        self.profile = profile
        self.updatePipeOut = updatePipeOut
        self.misoMatrixPipeOut = misoMatrixPipeOut
        self.commandQueue = commandQueue
        self.printQueue = printQueue

        self.symbol = "[GD][GR] "
        self.popup = None
        
        self.maxRPM = self.profile[ac.maxRPM]

        self.startDisplacement = 2
        self.endDisplacement = 2 + self.profile[ac.maxFans]

        self.updateLock = threading.Lock()
        self.stopCalled = False
        self.isActive = False
        self.readyToClose = False

        self._printM("Building Grid")

        # Grid data ............................................................
        self.colormap = cs.COLORMAP_GALCIT
        self.colormapSize = len(self.colormap)
        self.minimumDelta = int(self.maxRPM/self.colormapSize)

        self.numberOfRows = self.profile[ac.rows]
        self.numberOfColumns = self.profile[ac.columns]
        self.numberOfLayers = self.profile[ac.layers]
        self.layerDisplacement = 0

        self.modules = self.profile[ac.modules]
        self.numberOfModules = len(self.modules)
        self.defaultAssignment = self.profile[ac.defaultModuleAssignment]

        self.gridIIDLow = -1
        self.gridIIDHigh = 0

        self.gridDragStartIID = 0
        

        # For fast communication between the Grid and the rest of the software,
        # we need an efficient way to go from IIDs (ID's of drawn, colored cells)
        # To the corresponding Slave index and fan index, for control; and a 
        # way to go from Slave indices and fan indices to the corresponding 
        # IID, for feedback display. Python dictionaries will be used for fast
        # indexing:
        
        self.iidsToFans = {} # IID -> (index, fan1...)
        self.iidsToSelection = {}
        self.slavesToSelections = {} # Index -> [count, [sel1, sel2 ...]]
        self.selectedSlaves = set([])

        self.slavesToCells = {} # Index ->  Fan number -> IID
        self.slavesToRecords = {} # Index ->  Fan number -> Previous RPM
        self.slavesToDCs = [None]*self.numberOfModules # Index -> Fan number -> DC
        
        self.selectorIIDsToRows = {} # IID (Of "row selector") -> row
        self.selectorIIDsToColumns = {} # IID (Of "column selector") -> column

        self.columnSelectorIIDs = []
        self.rowSelectorIIDs = []
        
        for module in self.modules:
            
            self.slavesToCells[module[ac.M_INDEX]] = {}
            
            self.slavesToRecords[module[ac.M_INDEX]] = {}
            
            self.slavesToSelections[module[ac.M_INDEX]] = \
                [
                    0,
                    [0]*module[ac.M_NUMFANS]
                ]

            self.slavesToDCs[module[ac.M_INDEX]] = [0.0]*module[ac.M_NUMFANS]

        self.previousSlavesToDCs = None

        # The IIDs will be generated when the matrix is drawn. The following
        # dictionary will serve as an intermediate. It will go from 
        # grid coordinates to the (index, fan...) tuples expected in the 
        # IID to fan dictionary:

        # Allocate:
        self.coordsToFans = {}
        self.coordsToIIDs = {}

        for row in range(self.numberOfRows):
            self.coordsToFans[row] = {}
            self.coordsToIIDs[row] = {}

        # Loop over the module list to add each relevant Slave to the 
        # Grid:

        for module in self.modules:
            
            # For each module, loop over its rows and columns and 
            # Assign fans from its own assignment list:
            
            cellIndex = 0
            cells = module[ac.M_ASSIGNMENT]
            if cells == '':
                cells = self.defaultAssignment
            cells = cells.split(',')
            # DEBUG: print(cells)
            for moduleRow in range(module[ac.M_NUMROWS]):
                for moduleColumn in range(module[ac.M_NUMCOLUMNS]):                    
                        cell = cells[cellIndex]
                        if cell != '':
                                self.coordsToFans[module[ac.M_ROW] + moduleRow][module[ac.M_COLUMN] + moduleColumn] = (module[ac.M_INDEX], ) 
                        
                                for fan_index in cell.split('-'):
                                        self.coordsToFans[module[ac.M_ROW] + moduleRow][module[ac.M_COLUMN] + moduleColumn] += (int(fan_index),)

                                        
                                #print(module[ac.M_ROW]+moduleRow, module[ac.M_COLUMN]+moduleColumn,':',self.coordsToFans[module[ac.M_ROW] + moduleRow][module[ac.M_COLUMN] + moduleColumn])
                        cellIndex += 1
                """                                                
                self.coordsToFans\
                [module[ac.M_ROW] + moduleRow]\
                [module[ac.M_COLUMN] + moduleColumn] = \
                (module[ac.M_INDEX], ) +\
                tuple(map(lambda e: int(e) if e not in ('',',') else None,
                cells[cellIndex].split('-')))
                
                cellIndex += 1
                """
        # Lastly, track selection


        self.cellLength = 0

        self.layers = tuple(map(str, tuple(range(1,self.numberOfLayers+1))))
        
        # BUILD WIDGET
        
        self.grid_rowconfigure(0, weight = 0)

        self.grid_columnconfigure(0, weight = 1)
        
        self.grid_rowconfigure(1, weight = 1)

        self.grid_propagate(True)
        
        # SIDE PANEL -----------------------------------------------------------
        # This panel will contain all control and user input widgets
        self.sidePanel = Tk.Frame(
            self,
            bd = 4,
            relief = Tk.RIDGE,
            bg = self.bg
        )
        self.sidePanel.grid(row = 0, column = 0, sticky = "WENS")
        self.grid_rowconfigure(0, weight = 2)
        self.sidePanel.grid_columnconfigure(0, weight = 1)

        # TOP BAR --------------------------------------------------------------
        self.topBar = Tk.Frame(
            self.sidePanel,
            bg = self.bg
        )
        self.topBar.grid(row = 0, column = 0, sticky = "EW")

        # Display switch:
        # (Switch between showing the state of the tunnel or a preview)
        self.modeSwitchLabel = Tk.Label(
            self.topBar,
            bg = self.bg,
            fg = self.fg,
            text = "Mode:  "
        )
        self.modeSwitchLabel.pack(side = Tk.LEFT)
        
        self.modeVar = Tk.IntVar()
        self.modeVar.set(ARRAY)
        self.modeVar.trace('w', self._modeVarCallback)

        self.modeArrayButton = Tk.Radiobutton(
            self.topBar,
            variable = self.modeVar,
            text = "Live Control",
            value = ARRAY,
            indicatoron = 0
        )
        self.modeArrayButton.pack(side = Tk.LEFT)

        self.modePreviewButton = Tk.Radiobutton(
            self.topBar,
            variable = self.modeVar,
            text = "Flow Builder",
            value = PREVIEW,
            indicatoron = 0
        )
        self.modePreviewButton.pack(side = Tk.LEFT)

        # CONTROL BAR ----------------------------------------------------------
        self.controlBar = Tk.Frame(
            self.sidePanel,
            bg = self.bg
        )
        self.controlBar.grid(row = 1, column = 0, sticky = "NEWS")
        self.sidePanel.grid_rowconfigure(1, weight = 1)

        self.notebook = tkinter.ttk.Notebook(
            self.controlBar
        )
        self.notebook.enable_traversal()
        self.notebook.pack(fill = Tk.BOTH, expand = True)

        self.tabCount = 0

        # MANUAL CONTROL .......................................................
        self.manualControlFrame = Tk.Frame(
            None,
            bg = self.bg
        )

        self.notebook.add(
            self.manualControlFrame,
            text = "Steady Flow Generator"
        )
        self.manualControlTabIndex = self.tabCount
        self.tabCount += 1
        
        self.manualControlRows = 0
        
        # Matrix counter
        self.matrixCounterLabel = Tk.Label(
            self.manualControlFrame,
            bg = self.bg,
            fg = self.fg,
            text = "  Matrices: "
        )
        self.matrixCounterLabel.grid(sticky = 'W',row =self.manualControlRows, column = 0)

        self.matrixCount = 0
        self.matrixCounterVar = Tk.IntVar()
        self.matrixCounterVar.set(0)
        self.matrixCounterDisplay = Tk.Label(
            self.manualControlFrame,
            textvariable = self.matrixCounterVar,
            relief = Tk.SUNKEN,
            bd = 1,
            bg = self.bg,
            fg = self.fg,
            width = 10
        )
        self.matrixCounterDisplay.grid(
            sticky = 'WE',row = self.manualControlRows, column = 1)
        self.manualControlRows += 1


        # Control layer
        # TODO: Implement
        """
        self.targetLabel = Tk.Label(
            self.manualControlFrame,
            bg = self.bg,
            fg = self.fg,
            text = "Control: "
        )
        self.targetLabel.grid(sticky = 'W',row = self.manualControlRows, column = 0)

        self.targetMenuVar = Tk.StringVar()
        self.targetMenuVar.trace('w', self._targetMenuCallback)
        self.targetMenuVar.set(self.layers[0])
        self.targetMenu = Tk.OptionMenu(
            self.manualControlFrame,
            self.targetMenuVar,
            *self.layers
        )
        self.targetMenu.config(
            width = 3,
            background = self.bg,
            highlightbackground = self.bg,
            foreground = self.fg,
            state = Tk.DISABLED
        )
        self.targetMenu.grid(sticky = 'W',row = self.manualControlRows, column = 1)
        self.manualControlRows += 1
        """

        # Display layer
        self.displayLabel = Tk.Label(
            self.manualControlFrame,
            bg = self.bg,
            fg = self.fg,
            text = "  Display Layer: "
        )
        self.displayLabel.grid(sticky = 'W',row = self.manualControlRows, column = 0)

        self.displayMenuFrame = Tk.Frame(
            self.manualControlFrame,
            bg = self.bg
        )
        self.displayMenuFrame.grid(
            sticky = 'W', row = self.manualControlRows, column = 1)
        
        self.displayMenuVar = Tk.StringVar()
        self.displayMenuVar.trace('w', self._displayMenuCallback)
        self.displayMenuVar.set(self.layers[0])
        self.displayMenu = Tk.OptionMenu(
            self.displayMenuFrame,
            self.displayMenuVar,
            *self.layers
        )
        self.displayMenu.config(
            width = 3,
            background = self.bg,
            highlightbackground = self.bg,
            foreground = self.fg,
        )
        self.displayMenu.pack(side = Tk.LEFT)

        self.displayCountLabel = Tk.Label(
            self.displayMenuFrame,
            bg = self.bg,
            fg = self.fg,
            text = "Out of {}".format(self.numberOfLayers)
        )
        self.displayCountLabel.pack(side = Tk.LEFT)
        
        self.manualControlRows += 1

        # Command input
        
        # Unit:
        self.unitLabel = Tk.Label(
            self.manualControlFrame,
            bg = self.bg,
            fg = self.fg,
            text = "  Unit: "
        )
        self.unitLabel.grid(sticky = 'W',row =self.manualControlRows, column = 0)
        self.unitMenuVar = Tk.StringVar()
        self.unitMenuVar.trace('w', self._unitMenuCallback)
        self.unitMenuVar.set("DC")
        self.unitMenu = Tk.OptionMenu(
            self.manualControlFrame,
            self.unitMenuVar,
            "DC",
            "RPM"
        )
        self.unitMenu.config(
            width = 3,
            background = self.bg,
            highlightbackground = self.bg,
            foreground = self.fg,
            state = Tk.DISABLED
        )
        self.unitMenu.grid(sticky = 'W',row = self.manualControlRows, column = 1)
        self.manualControlRows += 1

        # Command:

        self.canvas = None

        self.commands = (
            SELECT,
            TRACE
        )
        self.commandCode = SELECT_CODE

        self.commandLabel = Tk.Label(
            self.manualControlFrame,
            bg = self.bg,
            fg = self.fg,
            text = "  Command: "
        )
        self.commandLabel.grid(sticky = 'W',row =self.manualControlRows, column = 0)
        self.commandMenuVar = Tk.StringVar()
        self.commandMenuVar.trace('w', self._commandMenuCallback)
        self.commandMenuVar.set(self.commands[0])
        self.commandMenu = Tk.OptionMenu(
            self.manualControlFrame,
            self.commandMenuVar,
            *self.commands
        )
        self.commandMenu.config(
            width = 7,
            background = self.bg,
            highlightbackground = self.bg,
            foreground = self.fg,
        )
        self.commandMenu.grid(sticky = 'W',row = self.manualControlRows, column = 1)
        self.manualControlRows += 1

        # Entry:
        validateCE = self.register(self._validateCommandEntry)
        self.commandEntry = Tk.Entry(
            self.manualControlFrame, 
            highlightbackground = self.bg,
            bg = 'white',
            fg = self.fg,
            width = 7, validate = 'key', validatecommand = \
                (validateCE, '%S', '%s', '%d'))
        self.commandEntry.grid(sticky = 'E',row = self.manualControlRows, column = 0)
        self.commandEntry.bind('<Return>', self._send)
        self.commandEntry.focus_set()
        self.commandEntry.bind('<Control-a>', self._selectGridAll)
        self.commandEntry.bind('<Control-A>', self._selectGridAll)
        self.commandEntry.bind('<Control-d>', self._deselectGridAll)
        self.commandEntry.bind('<Control-D>', self._deselectGridAll)
        
        # Send Button:
        self.sendButton = Tk.Button(
            self.manualControlFrame,
            bg = self.bg,
            fg = self.fg,
            highlightbackground = self.bg,
            width = 11,
            text = "Send",
            command = self._send,
        )
        self.sendButton.grid(sticky = 'W',row = self.manualControlRows, column = 1)

        self.manualControlRows += 1

        
        self.rememberValueToggleVar = Tk.BooleanVar()
        self.rememberValueToggle = Tk.Checkbutton(
            self.manualControlFrame, 
            text ="Remember value", 
            variable = self.rememberValueToggleVar, 
            bg = self.bg, 
            fg = self.fg, 
            )
        self.rememberValueToggleVar.set(False)
        self.rememberValueToggle.grid(sticky = 'W',row = self.manualControlRows, column = 0)

        self.rememberSelectionToggleVar = Tk.BooleanVar()
        self.rememberSelectionToggle = Tk.Checkbutton(
            self.manualControlFrame, 
            text ="Remember selection", 
            variable = self.rememberSelectionToggleVar, 
            bg = self.bg, 
            fg = self.fg, 
            )
        self.rememberSelectionToggleVar.set(False)
        self.rememberSelectionToggle.grid(sticky = 'W',
            row = self.manualControlRows, column = 1)
        self.manualControlRows += 1

        # Randomizer:
        self.randomizerFrame = Tk.Frame(
            self.manualControlFrame,
            bg = self.bg,
            bd = 1,
            relief = Tk.RIDGE
        )
        self.randomizerFrame.grid(
            row =self.manualControlRows, column = 0, 
            columnspan = 3, sticky = "WE")
        self.manualControlRows += 1

        self.randomizerLabel = Tk.Label(
            self.randomizerFrame,
            bg = self.bg,
            fg = self.fg,
            text = "  Random Generator",
        )
        self.randomizerLabel.pack(side = Tk.TOP, fill = Tk.X)

        self.randomizerRangeFrame = Tk.Frame(
            self.randomizerFrame,
            bg = self.bg
        )
        self.randomizerRangeFrame.pack(side = Tk.TOP, fill = Tk.X)

        self.randomizerRangeLabel = Tk.Label(
            self.randomizerRangeFrame,
            bg = self.bg,
            fg = self.fg,
            text = "  Range: ["
        )
        self.randomizerRangeLabel.pack(side = Tk.LEFT)

        self.randomizerLowBoundEntry = Tk.Entry(
            self.randomizerRangeFrame,
            highlightbackground = self.bg,
            bg = 'white',
            fg = self.fg,
            width = 4, validate = 'key', validatecommand = \
                (validateCE, '%S', '%s', '%d'))
        self.randomizerLowBoundEntry.pack(side = Tk.LEFT)
        self.randomizerLowBoundEntry.bind('<Return>', self._applyRandomizer)
        self.randomizerLowBoundEntry.bind('<Control-a>', self._selectGridAll)
        self.randomizerLowBoundEntry.bind('<Control-A>', self._selectGridAll)
        self.randomizerLowBoundEntry.bind('<Control-d>', self._deselectGridAll)
        self.randomizerLowBoundEntry.bind('<Control-D>', self._deselectGridAll)
        
        self.randomizerCommaLabel = Tk.Label(
            self.randomizerRangeFrame, 
            bg = self.bg,
            fg = self.fg,
            text = ","
        )
        self.randomizerCommaLabel.pack(side = Tk.LEFT)

        self.randomizerHighBoundEntry = Tk.Entry(
            self.randomizerRangeFrame, 
            highlightbackground = self.bg,
            bg = 'white',
            fg = self.fg,
            width = 4, validate = 'key', validatecommand = \
                (validateCE, '%S', '%s', '%d'))
        self.randomizerHighBoundEntry.pack(side = Tk.LEFT)
        self.randomizerHighBoundEntry.bind('<Return>', self._applyRandomizer)
        self.randomizerHighBoundEntry.bind('<Control-a>', self._selectGridAll)
        self.randomizerHighBoundEntry.bind('<Control-A>', self._selectGridAll)
        self.randomizerHighBoundEntry.bind('<Control-d>', self._deselectGridAll)
        self.randomizerHighBoundEntry.bind('<Control-D>', self._deselectGridAll)
        
        self.randomizerClosingLabel = Tk.Label(
            self.randomizerRangeFrame, 
            bg = self.bg,
            fg = self.fg,
            text = "] (in [0.0, 100.0])"
        )
        self.randomizerClosingLabel.pack(side = Tk.LEFT)

        self.randomizerButton = Tk.Button(
            self.randomizerFrame,
            bg = self.bg,
            highlightbackground = self.bg,
            fg = self.fg,
            text = "Apply to Selection",
            command = self._applyRandomizer
        )
        self.randomizerButton.pack(side = Tk.TOP, fill =Tk.X)
        
        # Spatial function parser:
        self.steadyFormulaFrame = Tk.Frame(
            self.manualControlFrame,
            bg = self.bg,
            bd = 1,
            relief = Tk.RIDGE
        )
        self.steadyFormulaFrame.grid(
            row =self.manualControlRows, column = 0, 
            columnspan = 2, sticky = "WE")
        self.manualControlRows += 1

        self.steadyFormulaLabel = Tk.Label(
            self.steadyFormulaFrame,
            bg = self.bg,
            fg = self.fg,
            text = "  Input Formula",
        )
        self.steadyFormulaLabel.pack(side = Tk.TOP, fill = Tk.X)
        
        self.steadyFormulaVariablesLabel = Tk.Label(
            self.steadyFormulaFrame,
            bg = self.bg,
            fg = 'darkgray',
            justify = Tk.LEFT,
            text = \
                "  - r : Fan's row\n"\
                "  - c : Fan's column\n"\
                "  - R : Number of rows\n"\
                "  - C : Number of columns\n",
            font = 'TkFixedFont'
        )
        self.steadyFormulaVariablesLabel.pack(side = Tk.TOP, fill = Tk.X)

        self.steadyFormulaInputFrame = Tk.Frame(
            self.steadyFormulaFrame,
            bg = self.bg
        )
        self.steadyFormulaInputFrame.pack(side = Tk.TOP, fill = Tk.X)
        
        self.steadyFormulaLabel = Tk.Label(
            self.steadyFormulaInputFrame,
            bg = self.bg,
            fg = 'darkgray',
            text = "DC(r,c) = ",
            font = ('TkFixedFont', 9)
        )
        self.steadyFormulaLabel.pack(side = Tk.LEFT)
        
        self.steadyFormulaEntry = Tk.Entry(
            self.steadyFormulaInputFrame, 
            highlightbackground = self.bg,
            bg = 'lightgray',
            fg = '#424242',
            selectbackground = 'darkgray',
            font = 'TkFixedFont',
        )
        self.steadyFormulaEntry.pack(side = Tk.LEFT, fill = Tk.X, expand = True)
        self.steadyFormulaEntry.bind('<Return>', self._applySteadyFormula)
        self.steadyFormulaEntry.bind('<Control-a>', self._selectGridAll)
        self.steadyFormulaEntry.bind('<Control-A>', self._selectGridAll)
        self.steadyFormulaEntry.bind('<Control-d>', self._deselectGridAll)
        self.steadyFormulaEntry.bind('<Control-D>', self._deselectGridAll)
        
        self.steadyFormulaButton = Tk.Button(
            self.steadyFormulaFrame,
            bg = self.bg,
            highlightbackground = self.bg,
            fg = self.fg,
            text = "Apply to Selection",
            command = self._applySteadyFormula
        )
        self.steadyFormulaButton.pack(side = Tk.TOP, fill =Tk.X)
        


        # FLOW BUILDER .........................................................

        self.flowBuilderFrame = Tk.Frame(
            None,
            bg = self.bg
        )

        self.notebook.add(
            self.flowBuilderFrame,
            text = "Unsteady Flow Generator",
            state = Tk.DISABLED
        )
        self.flowBuilderTabIndex = self.tabCount
        self.tabCount += 2

        # GRID -----------------------------------------------------------------

        self.gridFrame = Tk.Frame(
            self,
            bg = self.bg,
        )
        self.gridFrame.grid(row = 0, column = 1, sticky = "NSEW")
        self.grid_columnconfigure(1, weight = 1)

        
        # Get canvas starting size:
        self.pack(fill = Tk.BOTH, expand = True)
        self.update_idletasks()
        
        self.canvas = Tk.Canvas(
            self.gridFrame,
            bg = self.bg,
            width  = int(self.master.winfo_screenwidth()*0.6),
            height = int(self.master.winfo_screenheight()*0.8),
            cursor = SELECT_CURSOR
        )
        self.canvas.pack(fill = "none", expand = True)
        
        self.update_idletasks()
        self.canvas.config(
            height = self.gridFrame.winfo_height(),
            width = self.gridFrame.winfo_width()
        )
        self.update_idletasks()

        # Build grid:
        self._buildGrid()

        # WRAP UP ..............................................................
        self.isActive = True
        self._updateRoutine()
        
        # End __init__ =========================================================

    def _stop(self, event=None): # =============================================
        
        if not self.stopCalled:
            self._printM("Closing Grid...")
            self.stopCalled = True
        
        self.isActive = False

        if self.readyToClose:

            self.master.destroy()

        else:
            self.after(100, self._stop)

        # End _stop ============================================================

    def updateIn(self, newUpdate): # ===========================================
        try:
            if newUpdate[wg.COMMAND] == wg.STOP:
                self._stop()

        except:
            self._printE()

        # End updateIn =========================================================

    def matrixIn(self, newMatrix): # ===========================================
        try:

            # Update matrix counter:
            self.matrixCount += 1
            self.matrixCounterVar.set(self.matrixCount)

            # Apply RPMs:
            for index, matrixRow in enumerate(newMatrix[:self.numberOfModules]):
                
                if matrixRow[0] != sv.CONNECTED:
                    # Slave disconnected
                    # TODO
                    for fanIndex in range(self.modules[index][ac.M_NUMFANS]):
                        self.slavesToRecords[index][fanIndex] = \
                            -self.maxRPM

                    for iid in self.slavesToCells[index].values():
                        self.canvas.itemconfig(
                            iid,
                            fill = COLOR_OFF
                        )

                else:
                    for fanIndex, fanValue in enumerate(
                        matrixRow[
                            self.startDisplacement+self.layerDisplacement:\
                            self.endDisplacement+self.layerDisplacement:2]):

                        if abs(fanValue - \
                            self.slavesToRecords\
                                [index][fanIndex*2+self.layerDisplacement])\
                                >= self.minimumDelta:

                            self.slavesToRecords\
                                [index][fanIndex*2+self.layerDisplacement] = \
                                    fanValue

                            self.canvas.itemconfig(
                                self.slavesToCells\
                                    [index][fanIndex*2+self.layerDisplacement],
                                fill = self.colormap[
                                    int(fanValue*self.colormapSize/self.maxRPM) if \
                                        fanValue <= self.maxRPM and \
                                        fanValue >= 0 else self.colormapSize-1
                                ]
                            )
                            


        except:
            self._printE()

        # End matrixIn =========================================================

    # GRID METHODS -------------------------------------------------------------

    def _buildGrid(self): # ====================================================
            
        # Calculate cell size ..................................................
        
        # Get minimum window dimension:
        minWindowDimension = \
            min(self.gridFrame.winfo_width(), self.gridFrame.winfo_height())

        # Get maximum cell number:
        maxGridDimension = \
            max(self.numberOfRows, self.numberOfColumns)
            
        # NOTE: Add extra cells to each dimension to make room for column
        # and row selectors

        self.cellLength = \
            max(int(minWindowDimension*0.9/(maxGridDimension)), 1)

        # Get margins to center grid:
        xmargin = \
            int(
                (self.canvas.winfo_width()-\
                    self.cellLength*self.numberOfColumns-2*self.cellLength)\
                    /2) - self.cellLength

        ymargin = \
            int((self.canvas.winfo_height()-\
                    self.cellLength*self.numberOfRows-2*self.cellLength)\
                    /2) - self.cellLength

        xborder = 4
        yborder = 4

        # Build row and column selectors:
        x = xmargin
        y = ymargin
    
        
        selectAllCornerIID = self.canvas.create_rectangle(
            xborder, 
            yborder, 
            x+self.cellLength, 
            y+self.cellLength, 
            
            fill = COLOR_SELECTOR_STD,
            width = 2
        )
        
        selectAllLabelIID = self.canvas.create_text(
                xborder + int(self.cellLength/2), y + int(self.cellLength/2),
                text = "Select All",
                anchor = 'w'

        )
        
        self.canvas.tag_bind(
            selectAllCornerIID,
            '<ButtonPress-1>',
            self._selectGridAll
        )
        self.canvas.tag_bind(
            selectAllLabelIID,
            '<ButtonPress-1>',
            self._selectGridAll
        )
    
        self.canvas.tag_bind(
            selectAllCornerIID,
            '<ButtonPress-3>',
            self._deselectGridAll
        )
        self.canvas.tag_bind(
            selectAllLabelIID,
            '<ButtonPress-3>',
            self._deselectGridAll
        )
    

        y += self.cellLength

        for row in range(self.numberOfRows):
            
            y += self.cellLength

            newRowSelectorIID = self.canvas.create_rectangle(
                xborder, y, x+self.cellLength, y+self.cellLength, 
                fill = COLOR_SELECTOR_STD, 
                width = 2
            )
            
            self.rowSelectorIIDs.append(newRowSelectorIID)

            newRowLabelIID = self.canvas.create_text(
                xborder + int(self.cellLength/2), y + int(self.cellLength/2),
                anchor = 'w',
                text = str(row + 1)
            )

            
            for iid in (newRowSelectorIID, newRowLabelIID):
            
                self.selectorIIDsToRows[iid] = row

                self.canvas.tag_bind(
                    iid,
                    "<ButtonPress-1>",
                    self._onRowSelectorClick
                )

                self.canvas.tag_bind(
                    iid,
                    "<B1-Motion>",
                    self._onRowSelectorClick
                )

                self.canvas.tag_bind(
                    iid,
                    "<ButtonRelease-1>",
                    self._onRowSelectorRelease
                )
                
                self.canvas.tag_bind(
                    iid,
                    "<ButtonPress-3>",
                    self._onRowSelectorClick2
                )

                self.canvas.tag_bind(
                    iid,
                    "<B3-Motion>",
                    self._onRowSelectorClick2
                )

                self.canvas.tag_bind(
                    iid,
                    "<ButtonRelease-3>",
                    self._onRowSelectorRelease2
                )
    
        y = ymargin
        
        x += self.cellLength

        for column in range(self.numberOfColumns):
            
            x += self.cellLength

            newColumnSelectorIID = self.canvas.create_rectangle(
                x, yborder, x+self.cellLength, y+self.cellLength, 
                fill = COLOR_SELECTOR_STD, 
                width = 2
            )
            self.columnSelectorIIDs.append(newColumnSelectorIID)
            
            newColumnLabelIID = self.canvas.create_text(
                x + int(self.cellLength/2), yborder + int(self.cellLength/2),
                text = str(column + 1)
            )
        
            for iid in (newColumnSelectorIID, newColumnLabelIID):

                self.selectorIIDsToColumns[iid] = column

                self.canvas.tag_bind(
                    iid,
                    "<ButtonPress-1>",
                    self._onColumnSelectorClick
                )

                self.canvas.tag_bind(
                    iid,
                    "<B1-Motion>",
                    self._onColumnSelectorClick
                )

                self.canvas.tag_bind(
                    iid,
                    "<ButtonRelease-1>",
                    self._onColumnSelectorRelease
                )

                self.canvas.tag_bind(
                    iid,
                    "<ButtonPress-3>",
                    self._onColumnSelectorClick2
                )

                self.canvas.tag_bind(
                    iid,
                    "<B3-Motion>",
                    self._onColumnSelectorClick2
                )

                self.canvas.tag_bind(
                    iid,
                    "<ButtonRelease-3>",
                    self._onColumnSelectorRelease2
                )

        
        x = xmargin

        # Build cells and tie them to fans:

        xmargin += 2*self.cellLength
        ymargin += 2*self.cellLength

        x = xmargin
        y = ymargin

        # Create cells
        # NOTE: FOR PERFORMANCE, THE CLICK AND DRAG CALLBACKS WILL ASSUME 
        # CONSECUTIVE IIDS FOR GRID CELLS. KEEP THIS IN MIND IF ANY OTHER 
        # GRID ITEM IS TO BE DRAWN WITHIN THIS LOOP!

        for row in range(self.numberOfRows):

            for column in range(self.numberOfColumns): # .......................
                
                # Build cell:
                newIID = self.canvas.create_rectangle(
                    x, y, x+self.cellLength, y+self.cellLength, fill = COLOR_EMPTY
                )

                if self.gridIIDLow == -1:
                    self.gridIIDLow = newIID
                else:
                    self.gridIIDHigh = newIID
                
                # Add cell data to data structures:
                try:
                    self.iidsToFans[newIID] = self.coordsToFans[row][column]
                    self.iidsToSelection[newIID] = False
                    self.coordsToIIDs[row][column] = newIID
                    
                    for fanIndex in self.coordsToFans[row][column][1:]:
                        self.slavesToCells[self.coordsToFans[row][column][0]][fanIndex] =\
                            newIID
                        
                        self.slavesToRecords[self.coordsToFans[row][column][0]][fanIndex] = -self.maxRPM
                except KeyError:
                    # This cell is not paired to a fan
                    pass

                # Add click behavior:
                
                self.canvas.tag_bind(
                    newIID,
                    '<ButtonPress-1>',
                    self._onCellClick
                )

                self.canvas.tag_bind(
                    newIID,
                    '<ButtonPress-3>',
                    self._onCellClick2
                )
                self.canvas.tag_bind(
                    newIID,
                    '<B1-Motion>',
                    self._onCellDrag
                )
                
                self.canvas.tag_bind(
                    newIID,
                    '<ButtonRelease-1>',
                    self._onCellRelease
                )
                
                self.canvas.tag_bind(
                    newIID,
                    '<ButtonRelease-3>',
                    self._onCellRelease2
                )
                
                self.canvas.tag_bind(
                    newIID,
                    '<Double-Button-1>',
                    self._onCellDoubleClick
                )
                
                self.canvas.tag_bind(
                    newIID,
                    '<Double-Button-3>',
                    self._onCellDoubleClick2
                )

                # DEBUG: Show text:
                """
                self.canvas.create_text(
                    x + int(self.cellLength/2),
                    y + int(self.cellLength/2),
                    text = "{}".format(self.iidsToFans[newIID][0]),
                    font = ('TkFixedWidth', '8')
                )
                """

                # Move forward in X (next column)
                x += self.cellLength

                # ..............................................................

            # Reset X and move forward in Y (next row, first column)
            x = xmargin
            y += self.cellLength

        
        # Grid border:
        gridBorderIID = self.canvas.create_rectangle(
            xmargin, 
            ymargin, 
            xmargin + self.cellLength*self.numberOfColumns, 
            ymargin + self.cellLength*self.numberOfRows, 
            width = 2
        )


        # Build deselect corner:
    
        x = xmargin + self.cellLength + self.numberOfColumns*self.cellLength
        y = yborder
        
        deselectAllCornerIID = self.canvas.create_rectangle(
            x, y, self.canvas.winfo_width()-xborder,y + ymargin-self.cellLength, 
            fill = 'darkgray',
            width = 2
        )
        
        deselectAllLabel = self.canvas.create_text(
                x + int(self.cellLength/2), y + int(self.cellLength/2),
                text = "Deselect All",
                anchor = 'w'

        )

        self.canvas.tag_bind(
            deselectAllCornerIID,
            '<ButtonPress-1>',
            self._deselectGridAll
        )
        self.canvas.tag_bind(
            deselectAllLabel,
            '<ButtonPress-1>',
            self._deselectGridAll
        )


        # Build colormap:

        x = xmargin + self.cellLength + self.numberOfRows*self.cellLength
        y = ymargin

        colorMapBackgroundIID = self.canvas.create_rectangle(
            x, 
            y, 
            self.canvas.winfo_width() - xborder, 
            y + self.numberOfRows*self.cellLength, 
            
            fill = COLORMAP[-1],
            width = 0
        )

        # Build color spectrum:
        stepHeight = \
            int(self.numberOfRows*self.cellLength/len(COLORMAP))

        stepResidue = int(
            (((self.numberOfRows*self.cellLength)/len(COLORMAP))%1)*10)
        
        print(stepResidue)

        print(self.numberOfRows, self.cellLength, len(COLORMAP), stepHeight)

        for i in range(len(COLORMAP)):
            
            newColorIID = self.canvas.create_rectangle(
                x,
                y,
                x + self.canvas.winfo_width() - xborder,
                y + stepHeight,
                fill = COLORMAP[i],
                width = 0
            )

            y += stepHeight
    
        colormapLower = y

        self.canvas.create_line(
            x,y,
            x + self.canvas.winfo_width() - xborder, y,
            dash = ". "
        )

        x = xmargin + self.cellLength + self.numberOfRows*self.cellLength
        y = ymargin
        
        colorMapBorderIID = self.canvas.create_rectangle(
            x, 
            y, 
            self.canvas.winfo_width() - xborder, 
            y + self.numberOfRows*self.cellLength, 
            
            fill = '',
            width = 2
        )
    
        self.canvas.create_text(
            xmargin + self.cellLength + self.numberOfRows*self.cellLength + xborder,
            ymargin + yborder,
            text = "{} RPM".format(self.maxRPM), 
            anchor = "nw",
            fill = 'white'
        )    
        
        self.canvas.create_text(
            xmargin + self.cellLength + self.numberOfRows*self.cellLength + xborder,
            colormapLower + yborder,
            text = "0 RPM", 
            anchor = "nw",
            fill = 'black'
        )    

        self.canvas.bind(
            '<KeyRelease-Escape>',
            self._deselectGridAll()
        )

        # End _buildGrid =======================================================

    # ROUTINES -----------------------------------------------------------------

    def _updateRoutine(self): # ================================================
        try:
            active = self.isActive
            
            if active:
                # Check updates:
                if self.updatePipeOut.poll():
                    self.updateIn(self.updatePipeOut.recv())
                    

                # Check matrices:
                if self.misoMatrixPipeOut.poll():

                    
                    # Check if live feedback is to be displayed:
                    if self.modeVar.get() == ARRAY:
                        self.matrixIn(self.misoMatrixPipeOut.recv())

                    else:
                        # No live feedback for now... discard matrix to 
                        # avoid backlogs and display the current preview 
                        # matrix:
                        self.misoMatrixPipeOut.recv()
                        self.matrixCount += 1

            else:
                self.readyToClose = True

        except:
            self._printE("Exception in Grid update routine: ")

        finally:
            if active:
                self.after(90, self._updateRoutine)
            
        # End _updateRoutine ===================================================

    # CALLBACKS (GRID) ---------------------------------------------------------

    def _onRowSelectorClick(self, event): # ====================================
        try:
            
            if self.commandCode == SELECT_CODE:

                # Get clicked cell:
                cell = self.canvas.find_closest(
                    self.canvas.canvasx(event.x),
                    self.canvas.canvasy(event.y))[0]

                # Select clicked row:
                self._selectGridRow(self.selectorIIDsToRows[cell])

                # Change color:
                self.canvas.itemconfig(
                    self.rowSelectorIIDs[self.selectorIIDsToRows[cell]],
                    fill = COLOR_SELECTOR_CLICKED
                )

        except KeyError:
            # If an unapplicable widget is selected by accident, ignore it
            return

        except:
            self._printE("Exception in Canvas row-selector callback")
        # End _onRowSelectorClick ==============================================

    def _onRowSelectorRelease(self, event): # ==================================
        try:
            
            if self.commandCode == SELECT_CODE:
                
                for iid in self.rowSelectorIIDs:

                    # Change color:
                    self.canvas.itemconfig(
                        iid,
                        fill = COLOR_SELECTOR_STD
                    )

        except KeyError:
            # If an unapplicable widget is selected by accident, ignore it
            return

        except:
            self._printE("Exception in Canvas row-selector callback")
        # End _onRowSelectorRelease ============================================


    def _onRowSelectorClick2(self, event): # ===================================
        try:
            
            if self.commandCode == SELECT_CODE:

                # Get clicked cell:
                cell = self.canvas.find_closest(
                    self.canvas.canvasx(event.x),
                    self.canvas.canvasy(event.y))[0]

                # Select clicked row:
                self._deselectGridRow(self.selectorIIDsToRows[cell])

                # Change color:
                self.canvas.itemconfig(
                    self.rowSelectorIIDs[self.selectorIIDsToRows[cell]],
                    fill = COLOR_SELECTOR_CLICKED
                )

        except KeyError:
            # If an unapplicable widget is selected by accident, ignore it
            return

        except:
            self._printE("Exception in Canvas row-selector callback")
        # End _onRowSelectorClick2 =============================================

    def _onRowSelectorRelease2(self, event): # =================================
        try:
            
            if self.commandCode == SELECT_CODE:
                
                for iid in self.rowSelectorIIDs:

                    # Change color:
                    self.canvas.itemconfig(
                        iid,
                        fill = COLOR_SELECTOR_STD
                    )

        except KeyError:
            # If an unapplicable widget is selected by accident, ignore it
            return

        except:
            self._printE("Exception in Canvas row-selector callback")
        # End _onRowSelectorRelease2 ===========================================

    def _onColumnSelectorClick(self, event): # =================================
        try:

            if self.commandCode == SELECT_CODE:

                # Get clicked cell:
                cell = self.canvas.find_closest(
                    self.canvas.canvasx(event.x),
                    self.canvas.canvasy(event.y))[0]

                # Select clicked row:
                self._selectGridColumn(self.selectorIIDsToColumns[cell])

                # Change color:
                self.canvas.itemconfig(
                    self.columnSelectorIIDs[self.selectorIIDsToColumns[cell]],
                    fill = COLOR_SELECTOR_CLICKED
                )

        except KeyError:
            # If an unapplicable widget is selected by accident, ignore it
            return

        except:
            self._printE("Exception in Canvas column-selector callback")
        # End _onColumnSelectorClick ===========================================

    def _onColumnSelectorRelease(self, event): # ===============================
        try:
            
            if self.commandCode == SELECT_CODE:
                
                for iid in self.columnSelectorIIDs:

                    # Change color:
                    self.canvas.itemconfig(
                        iid,
                        fill = COLOR_SELECTOR_STD
                    )

        except KeyError:
            # If an unapplicable widget is selected by accident, ignore it
            return

        except:
            self._printE("Exception in Canvas column-selector callback")
        # End _onColumnSelectorRelease =========================================

    def _onColumnSelectorClick2(self, event): # ================================
        try:

            if self.commandCode == SELECT_CODE:

                # Get clicked cell:
                cell = self.canvas.find_closest(
                    self.canvas.canvasx(event.x),
                    self.canvas.canvasy(event.y))[0]

                # Select clicked row:
                self._deselectGridColumn(self.selectorIIDsToColumns[cell])

                # Change color:
                self.canvas.itemconfig(
                    self.columnSelectorIIDs[self.selectorIIDsToColumns[cell]],
                    fill = COLOR_SELECTOR_CLICKED
                )

        except KeyError:
            # If an unapplicable widget is selected by accident, ignore it
            return

        except:
            self._printE("Exception in Canvas column-selector callback")
        # End _onColumnSelectorClick2 ==========================================

    def _onColumnSelectorRelease2(self, event): # ==============================
        try:
            
            if self.commandCode == SELECT_CODE:
                
                for iid in self.columnSelectorIIDs:

                    # Change color:
                    self.canvas.itemconfig(
                        iid,
                        fill = COLOR_SELECTOR_STD
                    )

        except KeyError:
            # If an unapplicable widget is selected by accident, ignore it
            return

        except:
            self._printE("Exception in Canvas column-selector callback")
        # End _onColumnSelectorRelease2 ========================================

    def _onCellClick(self, event): # ===========================================
        try:

            # Get clicked cell:
            cell = self.canvas.find_closest(
                self.canvas.canvasx(event.x),
                self.canvas.canvasy(event.y))[0]
            
            if cell >= self.gridIIDLow and cell <= self.gridIIDHigh:
                
                if self.commandCode == SELECT_CODE:
                    self.gridDragStartIID = cell    
                    self._toggleGridCell(cell)
                
                elif self.commandCode == TRACE_CODE:
                    self._selectGridCell(cell)

        except:
            self._printE("Exception in Cell Callback:")
        
        # End _onCellClick =====================================================
    
    def _onCellClick2(self, event): # ==========================================
        try:

            # Get clicked cell:
            cell = self.canvas.find_closest(
                self.canvas.canvasx(event.x),
                self.canvas.canvasy(event.y))[0]
            
            if cell >= self.gridIIDLow and cell <= self.gridIIDHigh:
                
                if self.commandCode == SELECT_CODE:
                    self.gridDragStartIID = cell    
                    self._deselectGridCell(cell)
                
                elif self.commandCode == TRACE_CODE:
                    self._deselectGridCell(cell)

        except:
            self._printE("Exception in Cell Callback:")
        
        # End _onCellClick2 ====================================================

    def _onCellDrag(self, event): # ===========================================
        try:
                
            # Get mode:
            if self.commandCode == SELECT_CODE:
                return
            
            elif self.commandCode == TRACE_CODE:

                # Get clicked cell:
                cell = self.canvas.find_closest(
                    self.canvas.canvasx(event.x),
                    self.canvas.canvasy(event.y))[0]
            
                # Check if the object clicked is actually part of the grid:
                if cell >= self.gridIIDLow and cell <= self.gridIIDHigh:
        
                    self._selectGridCell(cell)

        except:
            self._printE("Exception in Cell Callback:")

        # End _onCellDrag ======================================================

    def _onCellDrag2(self, event): # ==========================================
        try:
                
            # Get mode:
            if self.commandCode == SELECT_CODE:
                return
            
            elif self.commandCode == TRACE_CODE:
                return

        except:
            self._printE("Exception in Cell Callback:")

        # End _onCellDrag2 =====================================================

    def _onCellRelease(self, event): # =========================================
        try:

            # Get clicked cell:
            cell = self.canvas.find_closest(
                self.canvas.canvasx(event.x),
                self.canvas.canvasy(event.y))[0]
            
            # Check if the object clicked is actually part of the grid:
            if cell >= self.gridIIDLow and cell <= self.gridIIDHigh:
                
                if self.commandCode == SELECT_CODE:

                    if cell != self.gridDragStartIID:
                        startRow = int((self.gridDragStartIID-self.gridIIDLow)/self.numberOfRows)
                        endRow = int((cell-self.gridIIDLow)/self.numberOfRows)

                        startColumn = int((self.gridDragStartIID-self.gridIIDLow)%self.numberOfRows)
                        endColumn = int((cell-self.gridIIDLow)%self.numberOfRows)

                        
                        # Drag-select:
                        for selectedRow in range(min(startRow,endRow), max(startRow, endRow) + 1):

                            for selectedColumn in \
                                range(min(startColumn, endColumn), max(startColumn, endColumn) + 1):
                            
                                self._selectGridCell(self.coordsToIIDs[selectedRow][selectedColumn])
                    
                    else:
                        pass

                elif self.commandCode == TRACE_CODE:
                    
                    self._send()
                    self._deselectGridAll()

        except:
            self._printE("Exception in Cell Callback:")
        
        # End _onCellRelease ===================================================

    def _onCellRelease2(self, event): # ========================================
        try:

            # Get clicked cell:
            cell = self.canvas.find_closest(
                self.canvas.canvasx(event.x),
                self.canvas.canvasy(event.y))[0]
            
            # Check if the object clicked is actually part of the grid:
            if cell >= self.gridIIDLow and cell <= self.gridIIDHigh:
                
                if self.commandCode == SELECT_CODE:

                    if cell != self.gridDragStartIID:
                        startRow = int((self.gridDragStartIID-self.gridIIDLow)/self.numberOfRows)
                        endRow = int((cell-self.gridIIDLow)/self.numberOfRows)

                        startColumn = int((self.gridDragStartIID-self.gridIIDLow)%self.numberOfRows)
                        endColumn = int((cell-self.gridIIDLow)%self.numberOfRows)

                        
                        # Drag-select:
                        for selectedRow in range(min(startRow,endRow), max(startRow, endRow) + 1):

                            for selectedColumn in \
                                range(min(startColumn, endColumn), max(startColumn, endColumn) + 1):
                            
                                self._deselectGridCell(self.coordsToIIDs[selectedRow][selectedColumn])
                    
                    else:
                        pass

                elif self.commandCode == TRACE_CODE:
                    
                    self._send()
                    self._deselectGridAll()

        except:
            self._printE("Exception in Cell Callback:")
        
        # End _onCellRelease2 ==================================================

    def _selectGridCell(self, iid): # ==========================================

        try:
            
            # NOTE: Assuming a cell selects all fans it represents
            # TODO: Generalize to allow for different layers of selection

            if not self.iidsToSelection[iid]:
                
                # Get selection record for this Slave:
                record = self.slavesToSelections[\
                    self.iidsToFans[iid][ITF_INDEX]]                
                fanIndices = self.iidsToFans[iid][1:]
                
                # Update record counter:
                # NOTE: Assuming two fans for now
                record[STS_COUNTER] += 2
                
                # Update list:
                for fanIndex in fanIndices:
                    try:
                        record[STS_LIST][fanIndex] = 1
                    except IndexError:
                        print('SV: ', self.iidsToFans[iid][0])
                        print("FanIndices: ", fanIndices)
                        print(fanIndex, len(record[STS_LIST]), record[STS_LIST])
                # Update list of selected Slaves:
                self.selectedSlaves.add(self.iidsToFans[iid][ITF_INDEX])

                self.canvas.itemconfig(
                    iid,
                    outline = OUTLINE_SELECTED,
                    width = 4
                )
                
                self.iidsToSelection[iid] = True
                
        except:
            self._printE("Exception in Cell selection callback:")

        # End _selectGridCell ==================================================

    def _onCellDoubleClick(self, event): # =====================================
        try:
            
            if self.commandCode == SELECT_CODE:
                # Select module:
                
                # Get iid:
                cell = self.canvas.find_closest(
                    self.canvas.canvasx(event.x),
                    self.canvas.canvasy(event.y))[0]

                # Get all fans under this Slave and select it:
                for iid in self.slavesToCells[self.iidsToFans[cell][0]].values():
                    self._selectGridCell(iid)
                    

            elif self.commandCode == TRACE_CODE:
                pass

        except:
            self._printE("Exception in Cell callback:")

        # End _onCellDoubleClick ===============================================

    def _onCellDoubleClick2(self, event): # ====================================
        try:
            
            if self.commandCode == SELECT_CODE:
                # Select module:
                
                # Get iid:
                cell = self.canvas.find_closest(
                    self.canvas.canvasx(event.x),
                    self.canvas.canvasy(event.y))[0]

                # Get all fans under this Slave and select it:
                for iid in self.slavesToCells[self.iidsToFans[cell][0]].values():
                    self._deselectGridCell(iid)
                    

            elif self.commandCode == TRACE_CODE:
                pass

        except:
            self._printE("Exception in Cell callback:")

        # End _onCellDoubleClick2 ==============================================

    def _deselectGridCell(self, iid): # ========================================
        try:
            
            if self.iidsToSelection[iid]:
                
                # Get selection record for this Slave:
                record = self.slavesToSelections[\
                    self.iidsToFans[iid][ITF_INDEX]]
                
                fanIndices = self.iidsToFans[iid][1:]
                
                # Update record counter:
                # NOTE: Assuming two fans for now
                record[STS_COUNTER] -= 2
                
                # Update list:
                for fanIndex in fanIndices:
                    record[STS_LIST][fanIndex] = 0

                # Update list of selected Slaves:
                if record[STS_COUNTER] == 0:
                    self.selectedSlaves.remove(\
                        self.iidsToFans[iid][ITF_INDEX])

                self.canvas.itemconfig(
                    iid,
                    outline = OUTLINE_DESELECTED,
                    width = 1
                )
                
                self.iidsToSelection[iid] = False

        except:
            self._printE("Exception in Cell deselection callback:")

        # End _deselectGridCell ================================================
    
    def _toggleGridCell(self, iid): # ==========================================
        try:
            
            if self.iidsToSelection[iid]:
                # Cell selected. Deselect:
                self._deselectGridCell(iid)

            else:
                # Cell deselected. Select:
                self._selectGridCell(iid)

        except:
            self._printE("Exception in Cell selection callback:")

        # End _toggleGridCell ==================================================
    
    def _selectGridAll(self, *event): # ========================================
        try:
            
            if self.commandCode == SELECT_CODE:

                for iid in self.iidsToSelection:
                    if not self.iidsToSelection[iid]:
                        self._selectGridCell(iid)

            elif self.commandCode == TRACE_CODE:
                pass

        except:
            self._printE("Exception in Cell select-all callback")

        # End _selectGridAll ===================================================


    def _deselectGridAll(self, *event): # ======================================
        try:
            for iid in self.iidsToSelection:
                if self.iidsToSelection[iid]:
                    self._deselectGridCell(iid)

        except:
            self._printE("Exception in Cell deselect-all callback")

        # End _deselectGridAll =================================================

    def _selectGridRow(self, row, *event): # ===================================
        try:
            
            for iid in self.coordsToIIDs[row].values():

                self._selectGridCell(iid)

        except:
            self._printE("Exception in Cell select-row callback")
        # End _selectGridRow ===================================================

    def _selectGridColumn(self, column, *event): # =============================
        try:
            
            for row in self.coordsToIIDs.values():

                self._selectGridCell(row[column])

        except:
            self._printE("Exception in Cell select-row callback")
        # End _selectGridColumn ================================================

    def _deselectGridRow(self, row, *event): # =================================
        try:
            
            for iid in self.coordsToIIDs[row].values():

                self._deselectGridCell(iid)

        except:
            self._printE("Exception in Cell select-row callback")
        # End _deselectGridRow =================================================

    def _deselectGridColumn(self, column, *event): # ===========================
        try:
            
            for row in self.coordsToIIDs.values():

                self._deselectGridCell(row[column])

        except:
            self._printE("Exception in Cell select-row callback")
        # End _deselectGridColumn ==============================================

    # CALLBACKS (TOOLS) --------------------------------------------------------
    def _send(self, *event): # =================================================
        try:

            if self.commandEntry.get() == '':
                # Nothing to send
                return

            else:
                # Update button:
                self.sendButton.config(
                    state = Tk.DISABLED,
                    text = "Sending..."
                )
                self.commandEntry.config(
                    state = Tk.DISABLED
                )

                # Get duty cycle to send:
                dc = float(self.commandEntry.get())
                
                # Proceed according to control mode:
                if self.modeVar.get() == ARRAY:
                    # Controlling array
                    
                    # Cache data to be sent for better synchronization:
                    selection = []
                    
                    for slaveIndex in self.selectedSlaves:
                        
                        # Save DC:
                        for fanIndex, fanSelection in enumerate(
                            self.slavesToSelections[slaveIndex][STS_LIST]):

                            if fanSelection == 1:
                                self.slavesToDCs[slaveIndex][fanIndex] = dc
                        
                        # Prepare cache of commands to send:
                        selection.append(
                            (
                                slaveIndex,
                                tuple(\
                                    self.slavesToSelections[slaveIndex][STS_LIST]), 
                            )
                        )
                    
                    # Send command:
                    self.commandQueue.put_nowait(
                        (mw.COMMUNICATOR,
                        cm.SET_DC_GROUP,
                        dc,
                        selection)
                    )

                elif self.modeVar.get() == PREVIEW:
                    # Displaying a preview... Change grid colors only:
                    
                    for slaveIndex in self.selectedSlaves:

                        # Save DC:
                        for fanIndex, fanSelection in enumerate(
                            self.slavesToSelections[slaveIndex][STS_LIST]):

                            if fanSelection == 1:
                                self.slavesToDCs[slaveIndex][fanIndex] = dc
                            
                                # Apply color:
                                self.canvas.itemconfig(
                                    self.slavesToCells[slaveIndex][fanIndex],
                                    fill = self.colormap\
                                        [int(dc/100*(self.colormapSize-1))]
                                )
            
                # Done. Now restore interface:
                
                # Check "remember" settings:
                if not self.rememberValueToggleVar.get():
                    # Clear value entry:
                    self.commandEntry.config(state = Tk.NORMAL)
                    self.commandEntry.delete(0, Tk.END)

                if not self.rememberSelectionToggleVar.get():
                    # Clear selection:
                    self._deselectGridAll()

                # Update button:
                self.sendButton.config(
                    state = Tk.NORMAL,
                    text = "Send"
                )
                self.commandEntry.config(state = Tk.NORMAL)

        except:
            self._printE("Exception in Grid send")
        # End _send ============================================================

    def _sendSteady(self, event = None): # =====================================
        try:
            # Send the current Duty Cycle data structure in one command,
            # using the MULTI Slave-side command to assign several individual
            # duty cycles throughout each Slave's array at once...
            
            selections = []

            # Loop over the list of Slaves and compile a command for each
            for slaveIndex, slaveDCs in enumerate(self.slavesToDCs):
                selections.append(
                    (slaveIndex, ) + tuple(slaveDCs)
                )    
            
            # Place in command Queue:
            self.commandQueue.put_nowait(
                (mw.COMMUNICATOR,
                cm.SET_DC_MULTI,
                selections
                )
            )

        except:
            self._printE("Exception in Grid send S")

        # End _sendSteady ======================================================

    def _applyRandomizer(self, event = None): # ===============================
        try:

            # Check for missing entries:
            if self.randomizerLowBoundEntry.get() == '' or \
                self.randomizerHighBoundEntry.get() == '':
                # Missing entry
                return

            else:

                # Get values to be used:
                low = float(self.randomizerLowBoundEntry.get())
                high = float(self.randomizerHighBoundEntry.get())

                # Validate:
                if low >= high:
                    return
                

                # Get selection and apply random values to each:
                for slaveIndex in self.selectedSlaves:
                    
                    for fanIndex, fanSelection in enumerate(
                        self.slavesToSelections[slaveIndex][STS_LIST]):
                        

                        # Modify duty cycle data structure:
                        if fanSelection == 1:
                            
                            dc = rd.uniform(low, high)
                            self.slavesToDCs[slaveIndex][fanIndex] = dc
                        
                            if self.modeVar.get() == PREVIEW:
                                # If previewing, modify colors appropriately:
                                self.canvas.itemconfig(
                                    self.slavesToCells[slaveIndex][fanIndex],
                                    fill = self.colormap\
                                        [int(dc/100*(self.colormapSize-1))]
                                )


                
                # Once done assigning duty cycles, check if the Grid is actually
                # in Live Control mode, in which case the commands should be 
                # sent immedately
                
                if self.modeVar.get() == ARRAY:
                    self._sendSteady()


        except:
            self._printE("Exception in Grid randomizer callback")
        
        # End _applyRandomizer =================================================

    def _applySteadyFormula(self, event = None): # =============================
        try:
            
            if self.steadyFormulaEntry.get() == '':
                return

            else:

                # See https://stackoverflow.com/questions/594266/
                #    equation-parsing-in-python
                self.steadyFormulaButton.config(
                    text = "Applying...",
                    state = Tk.DISABLED
                )
                self.steadyFormulaEntry.config(state = Tk.DISABLED)
                    
                raw = self.steadyFormulaEntry.get()
                code = parser.expr(raw).compile()

                R = self.numberOfRows
                C = self.numberOfColumns
                    
                for r in self.coordsToIIDs:
                    for c in self.coordsToIIDs[r]:
                        
                        iid = self.coordsToIIDs[r][c]

                        if self.iidsToSelection[iid]:
                            dc = eval(code)
                            
                            for fan in self.iidsToFans[iid][1:]:
                                self.slavesToDCs[self.iidsToFans[iid][0]][fan] = dc

                            if self.modeVar.get() == PREVIEW:

                                self.canvas.itemconfig(
                                    iid,
                                    fill = self.colormap\
                                        [int(dc/100*(self.colormapSize-1))]
                                )


                if self.modeVar.get() == ARRAY:
                    self._sendSteady()

                # Check "remember" settings:
                if not self.rememberValueToggleVar.get():
                    # Clear value entry:
                    self.steadyFormulaEntry.config(state = Tk.NORMAL)
                    self.steadyFormulaEntry.delete(0, Tk.END)

                if not self.rememberSelectionToggleVar.get():
                    # Clear selection:
                    self._deselectGridAll()
                    
                self.steadyFormulaEntry.config(state = Tk.NORMAL)
                self.steadyFormulaButton.config(
                    text = "Apply to Selection",
                    state = Tk.NORMAL
                )

        except:
            self._printE("Exception in Grid Steady Formula")
    
    def _targetMenuCallback(self, *event): # ===================================
        try:

            self._printM("_targetMenuCallback", 'W')

        except:
            self._printE()
        # End _targetMenuCallback ==============================================

    def _targetMenuCallback(self, *event): # ===================================
        try:

            self._printM("_targetMenuCallback", 'W')

        except:
            self._printE()
        # End _targetMenuCallback ==============================================

    def _displayMenuCallback(self, *event): # ==================================
        try:
            
            # Adjust displacement:
            self.layerDisplacement = int(self.displayMenuVar.get())-1
            
            # Remove cache of old RPM's so that current ones will
            # necessarily be displayed again:
            for slaveIndex in self.slavesToRecords:
                for fanIndex in self.slavesToRecords[slaveIndex]:
                    self.slavesToRecords[slaveIndex][fanIndex] = \
                        -self.maxRPM

        except:
            self._printE()
        # End _displayMenuCallback =============================================

    def _commandMenuCallback(self, *event): # ==================================
        try:
            
            if self.commandMenuVar.get() == SELECT:
                self.commandCode = SELECT_CODE

                if self.canvas is not None:
                    self.canvas.config(
                        cursor = SELECT_CURSOR
                    )
                    self.rememberValueToggle.config(
                        state = Tk.NORMAL
                    )
                    self.rememberSelectionToggle.config(
                        state = Tk.NORMAL
                    )

            elif self.commandMenuVar.get() == TRACE:
                self.commandCode = TRACE_CODE
                self._deselectGridAll()
                
                if self.canvas is not None:
                    self.canvas.config(
                        cursor = TRACE_CURSOR
                    )
                    self.rememberValueToggleVar.set(True)
                    self.rememberSelectionToggleVar.set(False)

                    self.rememberValueToggle.config(
                        state = Tk.DISABLED
                    )
                    self.rememberSelectionToggle.config(
                        state = Tk.DISABLED
                    )

        except:
            self._printE()
        # End _commandMenuCallback =============================================

    def _unitMenuCallback(self, *event): # =====================================
        try:

            self._printM("_unitMenuCallback", 'W')

        except:
            self._printE()
        # End _unitMenuCallback ================================================

    def _validateCommandEntry(self, newCharacter, textBeforeCall, action): # ===
        try:

            # ABOUT: To be used by TkInter to validate text in "Send" Entry.
            if action == '0':
                return True
            
            elif self.unitMenuVar.get() == "DC" and \
                len(textBeforeCall) < 10:
                if newCharacter in '0123456789':
                    try:
                        total = float(textBeforeCall + newCharacter)
                        return total <= 100.000000
                    except ValueError:
                        return False
                elif newCharacter == '.' and not '.' in textBeforeCall:
                    return True
                else:
                    return False

            elif self.unitMenuVar.get() == "RPM" and newCharacter \
                in '0123456789' and \
                int(textBeforeCall + newCharacter) < self.maxRPM:
                return True

            else:
                return False

        except:
            self._printE()
        # End _validateCommandEntry ============================================

    def _modeVarCallback(self, *event): # ======================================
        try:
            
            # Check new mode:
            if self.modeVar.get() == ARRAY and \
                self.notebook.index(self.notebook.select()) == 0:
                
                # If switching to live control on steady flows, 
                # choose between 1) discarding 
                # the current DC values and doing nothing, 2) applying the 
                # current DC values to the array, or 3) saving the current
                # DC values to a file

                # Remove cache of old RPM's so that current ones will
                # necessarily be displayed again:
                for slaveIndex in self.slavesToRecords:
                    for fanIndex in self.slavesToRecords[slaveIndex]:
                        self.slavesToRecords[slaveIndex][fanIndex] = \
                            -self.maxRPM


                # Reset colors:
                for cellIID in range(self.gridIIDLow, self.gridIIDHigh + 1):
                    self.canvas.itemconfig(
                        cellIID,
                        fill = COLOR_EMPTY
                    )

                
                self.popup = Tk.Toplevel(bg = self.bg)
                self.popup.title("Switch to Live Control")
                
                message = Tk.Label(
                    self.popup,
                    bg = self.bg,
                    fg = self.fg,
                    text = "The previewed duty cycles are cached and ready to "\
                        "be sent."\
                        "\nWhat would you like to do?"
                )
                message.grid(row = 0, column = 0, columnspan = 2)
                
                parenthesis = Tk.Label(
                    self.popup,
                    bg = self.bg,
                    fg = self.fg,
                    font = ('TkDefaultFont', 10),
                    text = "\n(If you already saved this set of duty cycles, "\
                        "you may safely discard this cache)\n"
                )
                parenthesis.grid(row = 1, column = 0, columnspan = 2)

                applyButton = Tk.Button(
                    self.popup,
                    bg = self.bg,
                    fg = self.fg,
                    highlightbackground = self.bg,
                    command = self._popupApplyDutyCycles,
                    text = "Apply Duty Cycles"
                )
                applyButton.grid(row = 2, column = 0)
                
                discardButton = Tk.Button(
                    self.popup,
                    bg = self.bg,
                    fg = self.fg,
                    highlightbackground = self.bg,
                    command = self._popupDiscardDutyCycles,
                    text = "Discard Them"
                )
                discardButton.grid(row = 2, column = 1)

                saveAsButton = Tk.Button(
                    self.popup,
                    bg = self.bg,
                    fg = self.fg,
                    highlightbackground = self.bg,
                    command = self._popupSaveDutyCycles,
                    text = "Save for Later"
                )
                saveAsButton.grid(row = 2, column = 2)
                
                self.popup.wait_visibility()
                self.popup.focus_force()
                self.popup.grab_set()
                
                # Center widget on screen:
                self.popup.update_idletasks()
                width = self.popup.winfo_width()
                height = self.popup.winfo_height()
                x = (self.popup.winfo_screenwidth() // 2) - (width // 2)
                y = (self.popup.winfo_screenheight() // 2) - (height // 2)
                self.popup.geometry('{}x{}+{}+{}'.format(width, height, x, y))

            elif self.modeVar.get() == PREVIEW:

                # Set fan colors to currently stored DC's:
                for slaveIndex, slave in enumerate(self.slavesToDCs):
                    for i, dc in \
                        enumerate(slave[self.layerDisplacement::2]):
                        
                        self.canvas.itemconfig(
                            self.slavesToCells[slaveIndex]\
                                [i*2+self.layerDisplacement],
                            fill = self.colormap\
                                [int(dc/100*(self.colormapSize-1))]
                        )

                # Save currently stored DC's in case of discard:
                self.previousSlavesToDCs = cp.deepcopy(self.slavesToDCs)



        except:
            self._printE()

        # End _modeVarCallback =================================================

    def _popupApplyDutyCycles(self, event = None): # ===========================
        try:
            
            self._sendSteady()
            self.popup.destroy()
            self.popup = None

        except:
            _printE("Exception in Grid popup")

        # End _popupApplyDutyCycles ============================================

    def _popupDiscardDutyCycles(self, event = None): # =========================
        try:
            
            del self.slavesToDCs
            self.slavesToDCs = self.previousSlavesToDCs
            self.previousSlavesToDCs = None

            self.popup.destroy()
            self.popup = None

        except:
            _printE("Exception in Grid popup")

        # End _popupDiscardDutyCycles ==========================================

    def _popupSaveDutyCycles(self, event = None): # ============================
        try:
            # TODO:
            pass
            self.popup.destroy()
            self.popup = None

        except:
            _printE("Exception in Grid popup")

        # End _popupSaveDutyCycles =============================================
    
    def _redraw(self, *event): # ===============================================
        try:

            self._printM("_redraw", 'W')
            
            # Fit canvas to frame:
            self.update_idletasks()
                
            # TODO

            self.update_idletasks()

        except:
            self._printE()
        # End _redraw ==========================================================

    # AUXILIARY METHODS --------------------------------------------------------

    def _printM(self, message, tag = 'S'): # ===================================

        try:

            self.printQueue.put_nowait((self.symbol + message, tag))

        except:
            ep.errorPopup("Error in Grid print: ")

        # End _printM ==========================================================

    def _printE(self, prelude = "Error in Grid: "): # ==========================

        self._printM(prelude + traceback.format_exc(), 'E')

        # End _printE ==========================================================

## PROCESS ROUTINE #############################################################

def _FCPRGridProcessRoutine(
    
    commandQueue,
    mosiMatrixQueue,
    printQueue,

    profile,
    updatePipeOut,
    misoMatrixPipeOut

    ): # ==========================================
    
    try:

        gd = FCPRGridProcessWidget(
            profile = profile,
            updatePipeOut = updatePipeOut,
            misoMatrixPipeOut = misoMatrixPipeOut,
            commandQueue = commandQueue,
            printQueue = printQueue
        )

        gd.mainloop()

        printQueue.put_nowait(("[GD][GR] Grid terminated", 'W'))

    except:
        printQueue.put_nowait(
            ("[GD][GR] UNCAUGHT EXCEPTION in Grid routine "\
            "(Process terminated): \"{}\"".format(traceback.format_exc()),'E'))

    # End _FCPRGridProcessRoutine ==============================================

## CLASS DEFINITION ############################################################

class FCPRGrid(wg.FCWidget):

    def __init__(self, master, profile, spawnQueue, printQueue): # =============

        # OOP

        super(FCPRGrid, self).__init__(
            master = master,
            process = _FCPRGridProcessRoutine,
            profile = profile,
            spawnQueue = spawnQueue,
            printQueue = printQueue,
            watchdogType = wg.WIDGET,
            symbol = "GD"
        )

        # Widget
        self.background = "#e2e2e2"
        self.foreground = "black"

        # Button status code -> text and function correspondence

        self.buttonTexts = {
            wg.ACTIVE : STOP_TEXT,
            wg.STARTING : STARTING_TEXT,
            wg.INACTIVE : START_TEXT,
            wg.STOPPING : STOPPING_TEXT
        }

        self.buttonStates = {
            wg.ACTIVE : Tk.NORMAL,
            wg.STARTING : Tk.DISABLED,
            wg.INACTIVE : Tk.NORMAL,
            wg.STOPPING : Tk.DISABLED
        }

        self.buttonCommands = {
            wg.ACTIVE : self.stop,
            wg.STARTING : self.start,
            wg.INACTIVE : self.start,
            wg.STOPPING : self.stop
        }
    
        self.button = Tk.Button(
            self,
            text = START_TEXT,
            bg = self.background,
            fg = self.foreground,
            command = self.start,
        )

        self.button.pack()

        self._printM("Grid widget initialized", 'G')

        # End __init__ =========================================================

    def _setStatus(self, newStatus): # =========================================

        # Adjust button:
        try:
            self.button.config(
                text = self.buttonTexts[newStatus],
                state = self.buttonStates[newStatus],
                command = self.buttonCommands[newStatus]
            )

        except KeyError:
            raise ValueError("Invalid status code \"{}\"".format(newStatus))

        # Call parent method:
        super(FCPRGrid, self)._setStatus(newStatus)

        # End _setStatus =======================================================
