################################################################################
## Project: Fan Club Mark II "Master" # File: FCInterface.py                  ##
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
User interface module

"""
################################################################################


## DEPENDENCIES ################################################################

# GUI:
from mttkinter import mtTkinter as Tk
import tkFileDialog 
import tkMessageBox
import tkFont
import ttk # "Notebooks"

# System:
import threading
import time
import traceback
import os # Get current working directory & check file names
import sys # Exception handling
import inspect # get line number for debugging
import multiprocessing

# Data:
import numpy as np
import Queue

# FCMkII:
import FCCommunicator
import FCArchiver as ac
import FCPrinter as pt
import FCSlave as sv

import fci.SlaveList as sl
import fci.Terminal as tm

from auxiliary.debug import d

## CONSTANTS ###################################################################

# Debug flag (for printing):
DEBUG = False

# Printer file name status codes:
BADEXT = -1
EMPTY = 0
NODOT = 1
REPEATED = 2
NODOT_REPEATED = 3
NORMAL = 4
RESTORE = 5

## CLASS DEFINITION ############################################################

class FCInterface(Tk.Frame):      

	def __init__(self, version, master = None): # ==============================

		try:
			
			# CONFIGURE MAIN WINDOW = = = = = = = = = = = = = = = = = = = = = = 
			Tk.Frame.__init__(self, master)
			
			# Set title:
			self.master.title("Fan Club MkII [BETA]")

			# Set background:
			self.background = "#e2e2e2"
			self.foreground = "black"
			self.config(bg = self.background)

			
			# CREATE COMPONENTS = = = = = = = = = = = = = = = = = = = = = = = = 

			# MAIN FRAME -------------------------------------------------------
			self.main = Tk.Frame(self)
			self.main.pack(fill = Tk.BOTH, expand = True)

			# TOOLS ------------------------------------------------------------
			self.toolFrame = Tk.Frame(self.main,
				bg = self.background, relief = Tk.GROOVE, bd = 1) 

			# Base widget toggles ..............................................
			self.toggleFrame = Tk.Frame(self.toolFrame, bg = self.background)
			
			# List toggle:
			self.slaveListToggleVar = Tk.BooleanVar()
			self.slaveListToggleVar.set(True)

			self.slaveListToggle = Tk.Checkbutton(self.toggleFrame,
				text ="List", variable = self.slaveListToggleVar, 
				bg = self.background, fg = self.foreground,
				command = self._slaveListToggle)

			self.slaveListToggle.config( state = Tk.NORMAL)
			self.slaveListToggle.pack(side = Tk.LEFT)
			
			# Terminal toggle:
			self.terminalToggleVar = Tk.BooleanVar()
			self.terminalToggleVar.set(True)

			self.terminalToggle = Tk.Checkbutton(self.toggleFrame, 
				text ="Terminal", variable = self.terminalToggleVar, 
				bg = self.background, fg = self.foreground, 
				command = self._terminalToggle)
			self.terminalToggle.config( state = Tk.NORMAL)
			self.terminalToggle.pack(side = Tk.LEFT)

			self.toggleFrame.pack(side = Tk.LEFT, anchor = "w")
			# Outside widget buttons ...........................................
			self.widgetButtonFrame = Tk.Frame(
				self.toolFrame, bg=self.background)
	
			# Grid:
			self.gridButton = Tk.Button(
				self.toolFrame,
				text = "Activate Grid",
				width = 10,
				highlightbackground = self.background,
				command = self._gridButtonRoutine
			)
			self.gridButton.pack(side = Tk.RIGHT)	

			# Keep track of grid activity:
			self.isGridActive = False
			# Placeholder for reference to popup window:
			self.gridWindow = None
			self.grid = None

			# TODO: Implement grid:
			self.gridButton.config(state = Tk.DISABLED)

			# Settings:
			self.settingsButton = Tk.Button(
				self.toolFrame,
				text = "Settings",
				width = 10,
				highlightbackground = self.background,
				command = self._settingsButtonRoutine
			)
			self.settingsButton.pack(side = Tk.RIGHT)	

			# Keep track of settings activity:
			self.isSettingsActive = False
			# Placeholder for reference to popup window:
			self.settingsWindow = None
			self.settings = None

			# TODO: Implement settings:
			self.settingsButton.config(state = Tk.DISABLED)

			# Bootloader:
			self.bootloaderButton = Tk.Button(
				self.toolFrame,
				text = "Bootloader",
				width = 10,
				highlightbackground = self.background,
				command = self._bootloaderButtonRoutine
			)
			self.bootloaderButton.pack(side = Tk.RIGHT)	

			# Keep track of bootloader activity:
			self.isBootloaderActive = False
			# Placeholder for reference to popup window:
			self.bootloaderWindow = None
			self.bootloader = None

			# TODO: Implement bootloader:
			self.bootloaderButton.config(state = Tk.DISABLED)

			# Pack tool frame ..................................................
			self.toolFrame.pack(side = Tk.TOP, fill = Tk.X, expand = True,
				anchor = "n")

			# SLAVE LIST -------------------------------------------------------
			self.slaveListFrame = Tk.Frame(self.main, bg = self.background,
				relief = Tk.GROOVE, bd = 1)

			self.slaveList = sl.SlaveList(self.slaveListFrame)
			self.slaveList.pack(side = Tk.TOP, fill = Tk.BOTH, expand = True,
				anchor = "n")

			self.slaveListFrame.pack(side = Tk.TOP, fill = Tk.BOTH, 
				expand = True, anchor = "n")

			# TERMINAL ---------------------------------------------------------

			# Print queue:
			self.printQ = multiprocessing.Queue()

			self.terminalFrame = Tk.Frame(self.main, 
				bg = self.background,relief = Tk.RIDGE, bd = 1)

			self.terminal = tm.Terminal(self.terminalFrame, self.printQ,
				self._terminalToggle, self.terminalToggleVar)

			self.terminal.pack(side = Tk.TOP, fill = Tk.BOTH, expand = True)
			
			self.terminalFrame.pack(
				side = Tk.TOP, fill = Tk.BOTH, expand = True, anchor = "n")

			# CONTROL ----------------------------------------------------------
			# STATUS -----------------------------------------------------------	
			
			# START UPDATE ROUTINES = = = = = = = = = = = = = = = = = = = = = = 
			
			# Focus on the main window:
			self.master.lift()
			self.pack(fill = Tk.BOTH, expand = True)

			# MODULES ----------------------------------------------------------

			# Inter-process communications:
			self.matrixPipeFCI, self.matrixPipeFCC = multiprocessing.Pipe()
			self.commandPipeFCI, self.commandPipeFCC = multiprocessing.Pipe()

			self.comms = None
			self.archiver = None
	
			self.managerThread = \
				threading.Thread(target = self._managerRoutine)
			self.managerThread.setDaemon(True)

			self.managerThread.start()


		except Exception as e: # Print uncaught exceptions
			tkMessageBox.showerror(title = "FCMkII Fatal Error",
				message = "Warning: Uncaught exception in "\
				"GUI constructor: \"{}\"".\
				format(traceback.format_exc()))
		
		# End FCInterface Constructor ==========================================

	# THREADS AND ROUTINES -----------------------------------------------------

	def _managerRoutine(self): # ===============================================

	
		# INITIALIZATION -------------------------------------------------------
		try:
			self.printM("GUI \"manager\" thread initializing")

			self.printM("Initializing Archive")
			self.archiver = ac.FCArchiver() 
			self.printM("Archiver initialized", "G")

			self.printM("Initializing Communicator...")
			self.communicator = FCCommunicator.FCCommunicator(
				savedMACs = [],
				broadcastPeriodS = self.archiver.get(ac.broadcastPeriodS),
				periodMS = self.archiver.get(ac.periodMS),
				periodS = self.archiver.get(ac.periodS),
				broadcastPort = self.archiver.get(ac.broadcastPort),
				passcode = self.archiver.get(ac.passcode),
				misoQueueSize = self.archiver.get(ac.misoQueueSize),
				maxTimeouts = self.archiver.get(ac.maxTimeouts),
				maxLength = self.archiver.get(ac.maxLength),
				maxFans = self.archiver.get(ac.maxFans),
				fanMode = self.archiver.get(ac.fanMode),
				targetRelation = self.archiver.get(ac.targetRelation),
				fanFrequencyHZ = self.archiver.get(ac.fanFrequencyHZ),
				counterCounts = self.archiver.get(ac.counterCounts),
				pulsesPerRotation = self.archiver.get(ac.pulsesPerRotation),
				maxRPM = self.archiver.get(ac.maxRPM),
				minRPM = self.archiver.get(ac.minRPM),
				minDC = self.archiver.get(ac.minDC),
				chaserTolerance = self.archiver.get(ac.chaserTolerance),
				maxFanTimeouts = self.archiver.get(ac.maxFanTimeouts),
				pinout = self.archiver.get(ac.defaultPinout),
				matrixPipe = self.matrixPipeFCC,
				commandPipe = self.commandPipeFCC,
				printQueue = self.printQ
				)

		except Exception as e: # Print uncaught exceptions
			self.printM("ERROR: Unhandled exception in GUI manager thread: "\
				"\"{}\"".\
				format(traceback.format_exc()), "E")
		
		# MAIN LOOP ------------------------------------------------------------
			
			# Get Communicator output and update GUI ---------------------------
			


			# Get GUI input and send to Communicator ---------------------------

		# End _managerRoutine ==================================================

	# CALLBACKS ----------------------------------------------------------------

	def _terminalToggle(self): # ===============================================
		# Check variable:
		if self.terminalToggleVar.get():
			# Build terminal:
			self.terminalFrame.pack(fill = Tk.BOTH, expand = False)
		else:
			# Hide terminal:
			self.terminalFrame.pack_forget()
		# End terminal toggle ==================================================

	def _slaveListToggle(self): # ==============================================
		# Check variable:
		if self.slaveListToggleVar.get():
			# Build slaveList:
			self.slaveListFrame.pack(fill = Tk.BOTH, expand = True)
		else:
			# Hide slaveList:
			self.slaveListFrame.pack_forget()

		# End _slaveList Toggle ================================================

	def _gridButtonRoutine(self): # ============================================
		pass 

		# End _gridButtonRoutine ===============================================
	
	def _settingsButtonRoutine(self): # ========================================
		pass 

		# End _settingsButtonRoutine ===========================================

	def _bootloaderButtonRoutine(self): # ========================================
		pass 

		# End _bootloaderButtonRoutine ===========================================


	# UTILITY FUNCTIONS --------------------------------------------------------

	def printM(self, message, tag = 'S'): # ====================================
		self.printQ.put_nowait((message, tag))

		# End printM ===========================================================
