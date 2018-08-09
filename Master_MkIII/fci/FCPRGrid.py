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

		self._printM("Building Grid")

		# Grid data ............................................................
		self.numberOfRows = self.profile[ac.rows]
		self.numberOfColumns = self.profile[ac.columns]
		self.numberOfLayers = self.profile[ac.layers]
		self.modules = self.profile[ac.modules]
		
		self.indicesToFansToCells = {}  # Index -> Fans -> Cells
		#for module in self.modules:
		# TODO	
		
		
		self.cellsToFans = {} # Index, fan number(s)



		self.rows = {}

		self.cellLength = 0

		self.layers = ("All", ) + \
			tuple(map(str, tuple(range(1,self.numberOfLayers+1))))

		# Commands:
		SELECT = "Select"
		TRACE = "Trace"

		self.commands = (
			SELECT,
			TRACE
		)

		self.maxRPM = self.profile[ac.maxRPM]

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
		self.rememberSelectionToggleVar.set(True)
		self.rememberSelectionToggle.pack(side = Tk.LEFT)

		# Select All:
		self.selectAllButton = Tk.Button(
			self.topBar,
			bg = self.bg,
			fg = self.fg,
			highlightbackground = self.bg,
			width = 11,
			text = "Redraw",
			command = self._redraw
		)
		self.selectAllButton.pack(side = Tk.LEFT)

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

			self.matrixCount += 1
			self.matrixCounterVar.set(self.matrixCount)

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
	
		
		cornerSelectorIID = self.canvas.create_rectangle(
			xborder, 
			yborder, 
			x+self.cellLength, 
			y+self.cellLength, 
			
			fill = 'darkgray',
			width = 2
		)
	
		y += self.cellLength

		for row in range(self.numberOfRows):
			
			y += self.cellLength

			newRowSelectorIID = self.canvas.create_rectangle(
			xborder, y, x+self.cellLength, y+self.cellLength, fill = 'darkgray', width = 2
			)


		y = ymargin
		
		x += self.cellLength

		for column in range(self.numberOfColumns):
			
			x += self.cellLength

			newColumnSelectorIID = self.canvas.create_rectangle(
			x, yborder, x+self.cellLength, y+self.cellLength, fill = 'darkgray', width = 2
			)

		
		x = xmargin

		# Build cells and tie them to fans:

		xmargin += 2*self.cellLength
		ymargin += 2*self.cellLength

		x = xmargin
		y = ymargin

		for row in range(self.numberOfRows):

			for column in range(self.numberOfColumns):
				
				newIID = self.canvas.create_rectangle(
					x, y, x+self.cellLength, y+self.cellLength, fill = 'white'
				)

				x += self.cellLength
			
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

	# CALLBACKS ----------------------------------------------------------------
	
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
			return True
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
