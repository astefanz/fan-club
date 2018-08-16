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

# System:
import sys			# Exception handling
import traceback	# More exception handling
import random		# Random names, boy
import threading	# Multitasking
import _thread		# thread.error
import multiprocessing as pr # The big guns

# Data:
import time			# Timing
import queue
import numpy as np	# Fast arrays and matrices

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
COLOR_EMPTY = 'white'

COLOR_SELECTOR_STD = '#939292'
COLOR_SELECTOR_CLICKED = '#7c7c7c'

# Special index values:

# Slave-to-selection list:
STS_COUNTER = 0
STS_LIST = 1

# IIDsToFans list:
ITF_INDEX = 0

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
		
		self.maxRPM = self.profile[ac.maxRPM]

		self.startDisplacement = 2
		self.endDisplacement = 2 + self.profile[ac.maxFans]

		self._printM("Building Grid")

		# Grid data ............................................................
		self.colormap = cs.COLORMAP_GALCIT
		self.colormapSize = len(self.colormap)
		self.minimumDelta = int(self.maxRPM/self.colormapSize)

		self.numberOfRows = self.profile[ac.rows]
		self.numberOfColumns = self.profile[ac.columns]
		self.numberOfLayers = self.profile[ac.layers]
		self.modules = self.profile[ac.modules]
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

		# The IIDs will be generated when the matrix is drawn. The following
		# dictionary will serve as an intermediate. It will go from 
		# grid coordinates to the (index, fan...) tuples expected in the 
		# IID to fan dictionary:

		# Allocate:
		self.coordsToFans = {}
		for row in range(self.numberOfRows):
			self.coordsToFans[row] = {}

		self.coordsToIIDs = {}
		for row in range(self.numberOfRows):
			self.coordsToIIDs[row] = {}

		# Loop over the module list to add each relevant Slave to the 
		# Grid:

		for module in self.modules:
			
			# For each module, loop over its rows and columns and 
			# Assign fans from its own assignment list:
			
			cellIndex = 0
			cells = module[ac.M_ASSIGNMENT]
			if cells == '':
				cells = self.defaultAssignment.split(',')

			for moduleRow in range(module[ac.M_NUMROWS]):

				for moduleColumn in range(module[ac.M_NUMCOLUMNS]):

					self.coordsToFans\
						[module[ac.M_ROW] + moduleRow]\
						[module[ac.M_COLUMN] + moduleColumn] = \
							(module[ac.M_INDEX], ) + tuple(map(int,cells[cellIndex].split('-')))
						
					cellIndex += 1

		# Lastly, track selection


		self.cellLength = 0

		self.layers = ("All", ) + \
			tuple(map(str, tuple(range(1,self.numberOfLayers+1))))
		self.selectedLayer = 2

		# Commands:
		SELECT = "Select"
		TRACE = "Trace"

		self.commands = (
			SELECT,
			TRACE
		)


		# BUILD WIDGET
		
		self.grid_rowconfigure(0, weight = 0)

		self.grid_columnconfigure(0, weight = 1)
		
		self.grid_rowconfigure(1, weight = 1)

		self.grid_propagate(True)

		# TOP BAR ..............................................................

		self.topBar = Tk.Frame(
			self,
			bg = self.bg
		)
		self.topBar.grid(row = 0, column = 0, sticky = "EW")

		# Control layer
		self.targetLabel = Tk.Label(
			self.topBar,
			bg = self.bg,
			fg = self.fg,
			text = "  Control: "
		)
		self.targetLabel.pack(side = Tk.LEFT)
		self.targetMenuVar = Tk.StringVar()
		self.targetMenuVar.trace('w', self._targetMenuCallback)
		self.targetMenuVar.set(self.layers[0])
		self.targetMenu = Tk.OptionMenu(
			self.topBar,
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
		self.targetMenu.pack(side = Tk.LEFT)

		# Display layer
		self.displayLabel = Tk.Label(
			self.topBar,
			bg = self.bg,
			fg = self.fg,
			text = "  Display: "
		)
		self.displayLabel.pack(side = Tk.LEFT)
		self.displayMenuVar = Tk.StringVar()
		self.displayMenuVar.trace('w', self._displayMenuCallback)
		self.displayMenuVar.set(self.layers[0])
		self.displayMenu = Tk.OptionMenu(
			self.topBar,
			self.displayMenuVar,
			*self.layers
		)
		self.displayMenu.config(
			width = 3,
			background = self.bg,
			highlightbackground = self.bg,
			foreground = self.fg,
			state = Tk.DISABLED
		)
		self.displayMenu.pack(side = Tk.LEFT)

		# Matrix counter
		self.matrixCounterLabel = Tk.Label(
			self.topBar,
			bg = self.bg,
			fg = self.fg,
			text = "  Matrices: "
		)
		self.matrixCounterLabel.pack(side = Tk.LEFT)
		self.matrixCount = 0
		self.matrixCounterVar = Tk.IntVar()
		self.matrixCounterVar.set(0)
		self.matrixCounterDisplay = Tk.Label(
			self.topBar,
			textvariable = self.matrixCounterVar,
			relief = Tk.SUNKEN,
			bd = 1,
			bg = self.bg,
			fg = self.fg,
			width = 10
		)
		self.matrixCounterDisplay.pack(side = Tk.LEFT)

		# Command input
		
		# Unit:
		self.unitLabel = Tk.Label(
			self.topBar,
			bg = self.bg,
			fg = self.fg,
			text = "  Unit: "
		)
		self.unitLabel.pack(side = Tk.LEFT)
		self.unitMenuVar = Tk.StringVar()
		self.unitMenuVar.trace('w', self._unitMenuCallback)
		self.unitMenuVar.set("DC")
		self.unitMenu = Tk.OptionMenu(
			self.topBar,
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
		self.unitMenu.pack(side = Tk.LEFT)

		# Command:
		self.commandLabel = Tk.Label(
			self.topBar,
			bg = self.bg,
			fg = self.fg,
			text = "  Command: "
		)
		self.commandLabel.pack(side = Tk.LEFT)
		self.commandMenuVar = Tk.StringVar()
		self.commandMenuVar.trace('w', self._commandMenuCallback)
		self.commandMenuVar.set(self.commands[0])
		self.commandMenu = Tk.OptionMenu(
			self.topBar,
			self.commandMenuVar,
			*self.commands
		)
		self.commandMenu.config(
			width = 7,
			background = self.bg,
			highlightbackground = self.bg,
			foreground = self.fg,
		)
		self.commandMenu.pack(side = Tk.LEFT)

		# Entry:
		validateCE = self.register(self._validateCommandEntry)
		self.commandEntry = Tk.Entry(
			self.topBar, 
			highlightbackground = self.bg,
			bg = 'white',
			fg = self.fg,
			width = 7, validate = 'key', validatecommand = \
				(validateCE, '%S', '%s', '%d'))
		self.commandEntry.insert(0, '0')
		self.commandEntry.pack(side = Tk.LEFT)
		self.commandEntry.bind('<Return>', self._send)
		self.commandEntry.focus_set()
		
		# Send Button:
		self.sendButton = Tk.Button(
			self.topBar,
			bg = self.bg,
			fg = self.fg,
			highlightbackground = self.bg,
			width = 11,
			text = "Send",
			command = self._send,
		)
		self.sendButton.pack(side = Tk.LEFT)

		
		self.rememberValueToggleVar = Tk.BooleanVar()
		self.rememberValueToggle = Tk.Checkbutton(
			self.topBar, 
			text ="Remember value", 
			variable = self.rememberValueToggleVar, 
			bg = self.bg, 
			fg = self.fg, 
			)
		self.rememberValueToggleVar.set(False)
		self.rememberValueToggle.pack(side = Tk.LEFT)

		self.rememberSelectionToggleVar = Tk.BooleanVar()
		self.rememberSelectionToggle = Tk.Checkbutton(
			self.topBar, 
			text ="Remember selection", 
			variable = self.rememberSelectionToggleVar, 
			bg = self.bg, 
			fg = self.fg, 
			)
		self.rememberSelectionToggleVar.set(False)
		self.rememberSelectionToggle.pack(side = Tk.LEFT)

		# GRID .................................................................

		self.gridFrame = Tk.Frame(
			self,
			bg = self.bg,
			bd = 5,
			relief = Tk.SUNKEN
		)
		self.gridFrame.grid(row = 1, column = 0, sticky = "NSEW")

		
		# Get canvas starting size:
		self.pack(fill = Tk.BOTH, expand = True)
		self.update_idletasks()

		self.canvas = Tk.Canvas(
			self.gridFrame,
			bg = self.bg,
			bd = 2,
			relief = Tk.RIDGE
		)
		self.canvas.pack(fill = "none", expand = True)
		
		self.canvas.config(
			width = self.gridFrame.winfo_width(),
			height = int(3*self.gridFrame.winfo_width()/4)
		)
		self.update_idletasks()

		# Build grid:
		self._buildGrid()

		# WRAP UP ..............................................................
		self._updateRoutine()
		
		# End __init__ =========================================================

	def _stop(self, *event): # =================================================
		
		self._printM("Closing Grid")

		self.destroy()
		self.master.quit()

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
			for index, matrixRow in enumerate(newMatrix):
				
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
						matrixRow[self.startDisplacement:self.endDisplacement:2]):
						
						if abs(fanValue - self.slavesToRecords[index][fanIndex*2])\
							>= self.minimumDelta:

							self.slavesToRecords[index][fanIndex*2] = fanValue

							self.canvas.itemconfig(
								self.slavesToCells[index][fanIndex*2],
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
				text = str(row)
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
				text = str(column)
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

				"""
				self.canvas.tag_bind(
					newIID,
					'<B1-Motion>',
					self._onCellDrag
				)
				"""

				self.canvas.tag_bind(
					newIID,
					'<ButtonRelease-1>',
					self._onCellRelease
				)
				
				self.canvas.tag_bind(
					newIID,
					'<Double-Button-1>',
					self._deselectGridAll
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
				y + stepHeight + (1 if stepResidue != 0 and i%stepResidue == 0 else 0),
				fill = COLORMAP[i],
				width = 0
			)

			y += stepHeight + (1 if stepResidue != 0 and i%stepResidue == 0 else 0)
	
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
			text = "{} RPM -- 100% DC".format(self.maxRPM), 
			anchor = "nw",
			fill = 'white'
		)	
		
		self.canvas.create_text(
			xmargin + self.cellLength + self.numberOfRows*self.cellLength + xborder,
			colormapLower + yborder,
			text = "0 RPM -- 0% DC", 
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

			# Check updates:
			if self.updatePipeOut.poll():
				self.updateIn(self.updatePipeOut.recv())
				
			# Check matrices:
			if self.misoMatrixPipeOut.poll():
				self.matrixIn(self.misoMatrixPipeOut.recv())

		except:
			self._printE("Exception in Grid update routine: ")

		finally:
			self.after(100, self._updateRoutine)

		# End _updateRoutine ===================================================

	# CALLBACKS (GRID) ---------------------------------------------------------

	def _onRowSelectorClick(self, event): # ====================================
		try:
			
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

	def _onColumnSelectorClick(self, event): # =================================
		try:

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

	def _onCellClick(self, event): # ===========================================
		try:

			# Get clicked cell:
			cell = self.canvas.find_closest(
				self.canvas.canvasx(event.x),
				self.canvas.canvasy(event.y))[0]
			
			if cell >= self.gridIIDLow and cell <= self.gridIIDHigh:

				self.gridDragStartIID = cell	

		except:
			self._printE("Exception in Cell Callback:")
		
		# End _onCellClick =====================================================

	def _onCellDrag(self, event): # ============================================
		try:

			# Get clicked cell:
			cell = self.canvas.find_closest(
				self.canvas.canvasx(event.x),
				self.canvas.canvasy(event.y))[0]
			
			if cell > self.gridIIDLow and cell < self.gridIIDHigh:
				self.canvas.itemconfig(
					cell,
					fill = 'red'
				)

		except:
			self._printE("Exception in Cell Callback:")
		
		# End _onCellDrag ======================================================

	def _onCellRelease(self, event): # =========================================
		try:

			# Get clicked cell:
			cell = self.canvas.find_closest(
				self.canvas.canvasx(event.x),
				self.canvas.canvasy(event.y))[0]
			
			if cell >= self.gridIIDLow and cell <= self.gridIIDHigh:
				
				if cell != self.gridDragStartIID:
					startRow = int((self.gridDragStartIID-self.gridIIDLow)/self.numberOfRows)
					endRow = int((cell-self.gridIIDLow)/self.numberOfRows)

					startColumn = int((self.gridDragStartIID-self.gridIIDLow)%self.numberOfRows)
					endColumn = int((cell-self.gridIIDLow)%self.numberOfRows)

					
					# Drag-select:
					for selectedRow in range(min(startRow,endRow), max(startRow, endRow) + 1):

						for selectedColumn in range(min(startColumn, endColumn), max(startColumn, endColumn) + 1):
						
							self._selectGridCell(self.coordsToIIDs[selectedRow][selectedColumn])
				
				else:
					self._toggleGridCell(cell)


		except:
			self._printE("Exception in Cell Callback:")
		
		# End _onCellRelease ===================================================

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
					record[STS_LIST][fanIndex] = 1
				
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
			for iid in self.iidsToSelection:
				if not self.iidsToSelection[iid]:
					self._selectGridCell(iid)

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

	# CALLBACKS (TOOLS) --------------------------------------------------------
	def _send(self, *event): # =================================================
		try:

			# Update button:
			self.sendButton.config(
				state = Tk.DISABLED,
				text = "Sending..."
			)

			# Get duty cycle to send:
			dc = float(self.commandEntry.get())
			
			"""
			for index in self.slavesToCells:
				# For each module, check if it has any fans selected. If so,
				# format a command to send and send it down the update 
				# pipe

				selected = False
				selection = ()

				for fan in self.slavesToCells[index]:
					if self.iidsToSelection[self.slavesToCells[index][fan]]:
						selection += (1,)
						selected = True

					else:
						selection += (0,)

				# If at least one fan is selected, send it down the 
				# command pipe:
				
				if selected:
					self.commandQueue.put_nowait(
					(mw.COMMUNICATOR, cm.SET_DC, dc, selection, index)
					)
			
			"""
			
			# Cache data to be sent for better synchronization:
			selection = []
			
			for index in self.selectedSlaves:
				
				selection.append(
					(
						index,
						tuple(self.slavesToSelections[index][STS_LIST]), 
					)
				)

			
			self.commandQueue.put_nowait(
				(mw.COMMUNICATOR,
				cm.SET_DC_GROUP,
				dc,
				selection)
			)

			# Check "remember" settings:

			if not self.rememberValueToggleVar.get():
				# Clear value entry:
				self.commandEntry.delete(0, Tk.END)

			if not self.rememberSelectionToggleVar.get():
				# Clear selection:
				self._deselectGridAll()

			# Update button:
			self.sendButton.config(
				state = Tk.NORMAL,
				text = "Send"
			)

		except:
			self._printE("Exception in Grid send")
		# End =================================================================
	
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

			self._printM("_displayMenuCallback", 'W')

		except:
			self._printE()
		# End _displayMenuCallback =============================================

	def _commandMenuCallback(self, *event): # ==================================
		try:

			self._printM("_commandMenuCallback", 'W')

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
