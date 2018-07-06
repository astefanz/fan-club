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
import multiprocessing as pr

# Data:
import numpy as np
import Queue

# FCMkII:
import FCCommunicator as cm
import FCPRCommunicator as pc
import FCArchiver as ac
import FCPrinter as pt
import FCSlave as sv

import fci.FCPRGrid as gd
import fci.SlaveList as sl
import fci.Terminal as tm
import fci.StatusBar as sb
import fci.BasicController as bc

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
			self.printQueue = pr.Queue()

			self.terminalFrame = Tk.Frame(self.main, 
				bg = self.background,relief = Tk.RIDGE, bd = 1)

			self.terminal = tm.Terminal(self.terminalFrame, self.printQueue,
				self._terminalToggle, self.terminalToggleVar)

			self.terminal.pack(side = Tk.TOP, fill = Tk.BOTH, expand = True)
			
			self.terminalFrame.pack(
				side = Tk.TOP, fill = Tk.BOTH, expand = True, anchor = "n")


			# STATUS -----------------------------------------------------------	
			self.statusBar = sb.StatusBar(self, version)
			self.statusBar.pack(side = Tk.BOTTOM, anchor = "s",
				fill = Tk.X, expand = True)

			# START UPDATE ROUTINES = = = = = = = = = = = = = = = = = = = = = = 
			
			# Focus on the main window:
			self.master.lift()
			self.pack(fill = Tk.BOTH, expand = True)

			# MODULES ----------------------------------------------------------

			# Inter-process communication:
			self.updatePipeOut, self.updatePipeIn = pr.Pipe(None)
			self.misoMatrixPipeOut, self.misoMatrixPipeIn = pr.Pipe(None)

			self._updateIn = lambda: None
			self._misoIn = lambda: None

			self.inputLock = threading.Lock()

			# Data structures:
			self.dataPipeline = [self]
			self.numModules = 0

			# Base modules:

			self.communicator = None
			self.archiver = None

			self.outputHandlerThread = \
				threading.Thread(target = self._outputHandlerRoutine)
			self.outputHandlerThread.setDaemon(True)

			self.outputHandlerThread.start()


		except Exception as e: # Print uncaught exceptions
			tkMessageBox.showerror(title = "FCMkII Fatal Error",
				message = "Warning: Uncaught exception in "\
				"GUI constructor: \"{}\"".\
				format(traceback.format_exc()))
			self.master.quit()
		
		# End FCInterface Constructor ==========================================

	# THREADS AND ROUTINES -----------------------------------------------------

	def _outputHandlerRoutine(self): # =========================================
	
		# INITIALIZATION -------------------------------------------------------
		try:
			self.printM("GUI \"manager\" thread initializing")

			self.printM("Initializing Archive")
			self.archiver = ac.FCArchiver() 
			self.printM("Archiver initialized", "G")

			macs = []
			for slave in self.archiver.get(ac.savedSlaves):
				macs.append(slave[1])
			self.printM("[UI][OR] Initializing Communicator")
			self.communicator = pc.FCPRCommunicator(
				savedMACs = macs,
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
				printQueue = self.printQueue
				)

			# Set up data pipeline:
			self.setIn(self.communicator.updateOut, self.communicator.misoOut)
			self.communicator.setIn(self.updateOut, self.misoOut)

			# Set up shutdown behavior:
			self.master.protocol("WM_DELETE_WINDOW", self._deactivationRoutine)

			# Add Grid:
			self.addModule(gd.FCPRGrid)

		except Exception as e:
			self.printM("ERROR: Unhandled exception in output handler setup: "\
				"\"{}\"".\
				format(traceback.format_exc()), "E")

		# MAIN LOOP ------------------------------------------------------------
		while True:
			try:
				# Get Communicator output and update GUI -----------------------
				
				# COMMAND PIPE -------------------------------------------------
				update = self.updateIn()
				if update is not None:	
					if update[0] == cm.NEW:
						for newSlave in update[1]:
							# TODO: Add Slave data structure
							self.slaveList.add(newSlave)
						
				# OUTPUT MATRIX ------------------------------------------------
				matrix = self.misoIn()
				if matrix is not None:
					del matrix
			
			except Exception as e:
				self.printM("ERROR: Unhandled exception in GUI output"\
					" routine: \"{}\"".\
					format(traceback.format_exc()), "E")

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
			self.slaveListFrame.pack(side = Tk.TOP,
				fill = Tk.BOTH, expand = True)
		else:
			# Hide slaveList:
			self.slaveListFrame.pack_forget()

		# End _slaveList Toggle ================================================

	def _gridDeactivationRoutine(self): # ======================================
			# ABOUT: Dismantle grid and grid's popup window.
			
		try:
			
			# Error-check:
			if not self.isGridActive:
				raise RuntimeError("Grid deactivation routine called on "\
					"inactive grid.")
			# Disable button to avoid conflicts:
			self.gridButton.config( state = Tk.DISABLED)

			# Destroy grid:
			self.grid.destroy()
			self.grid = None

			# Destroy popup window:
			self.gridWindow.destroy()
			self.gridWindow = None

			# Update sentinel:
			self.isGridActive = False

			# Reconfigure button:
			self.gridButton.config(
				text = "Activate Grid",
				state = Tk.NORMAL)
			
			# Done
			return

		except Exception as e: # Print uncaught exceptions
			self.printM("[_gridButtonRoutine] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")
		# End _gridDeactivationRoutine =========================================

	def _gridButtonRoutine(self): # ============================================
		try:
			# Check status:
			if not self.isGridActive:
				# If the grid is not active, this method activates the grid:
				
				# Error-check:
				if self.gridWindow is not None:
					raise RuntimeError("Grid activation routine called while "\
						"grid window placeholder is active.")

				# Activate grid:
				self.gridWindow = Tk.Toplevel()
				self.gridWindow.protocol("WM_DELETE_WINDOW", 
					self._gridDeactivationRoutine)

				self.gridOuterFrame = Tk.Frame(
					self.gridWindow, padx = 3, pady = 3, 
					relief = Tk.RIDGE, borderwidth = 2, cursor = "hand1")

				self.gridOuterFrame.pack(fill = Tk.BOTH, expand = True)


				def _expand(event):
					self.grid.destroy()
					del self.grid
					self.grid = mg.MainGrid(
						self.gridOuterFrame,
						self.archiver.get(ac.dimensions)[0],
						self.archiver.get(ac.dimensions)[1],
						0.9*(min(self.gridOuterFrame.winfo_height(),
							self.gridOuterFrame.winfo_width(),))/\
								(min(self.archiver.get(ac.dimensions)[0],
								self.archiver.get(ac.dimensions)[1])),
						[],
						self.archiver.get(ac.maxRPM)
						)

				self.gridOuterFrame.bind("<Button-1>", _expand)
				self.gridOuterFrame.focus_set()

				self.grid = mg.MainGrid(
					self.gridOuterFrame,
					self.archiver.get(ac.dimensions)[0],
					self.archiver.get(ac.dimensions)[1],
					600/self.archiver.get(ac.dimensions)[0],
					[],
					self.archiver.get(ac.maxRPM)
					)
			
				# Update button format:
				self.gridButton.config(text = "Deactivate Grid")
				
				# Update sentinel:
				self.isGridActive = True

			else:
				# If the grid is active, this method deactivates the grid:

				# Error-check:
				if self.gridWindow is  None:
					raise RuntimeError("Grid deactivation routine called while "\
						"grid window placeholder is inactive.")

				# Call the designated grid deactivation routine:
				self._gridDeactivationRoutine()

		except Exception as e: # Print uncaught exceptions
			self.printM("[_gridButtonRoutine] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")


		# End _gridButtonRoutine ===============================================
	
	def _settingsButtonRoutine(self): # ========================================
		# TODO: IMPLEMENT
		
		pass

		# End _settingsButtonRoutine ===========================================

	def _bootloaderButtonRoutine(self): # ======================================
		# TODO: IMPLEMENT
		
		pass 

		# End _bootloaderButtonRoutine =========================================

	def _deactivationRoutine(self): # ==========================================
		
		# Shutdown processes:
		self.communicator.shutdown()
		
		for module in self.dataPipeline:
			module.shutdown()

		# Close GUI:
		self.master.quit()

		# End _deactivationRoutine =============================================

	# UTILITY FUNCTIONS --------------------------------------------------------

	def updateIn(self): # ======================================================
		# Fetch update from Communicator, return it, and place it in own 
		# update pipe.

		try:
			self.inputLock.acquire()
			update = self._updateIn()
			
			if update is not None:
				self.updatePipeIn.send(update)
			
			return update

		finally:
			self.inputLock.release()

		# End updateIn =========================================================

	def updateOut(self): # =====================================================
		# Fetch update from own update pipe

		if self.updatePipeOut.poll():
			return self.updatePipeOut.recv()
		else:
			return None
		# End updateOut ========================================================

	def misoIn(self): # ========================================================
		# Fetch MISO matrix from Communicator, return it, and place it in own
		# MISO matrix pipe.

		try:
			self.inputLock.acquire()
			misoM = self._misoIn()

			if misoM is not None:
				self.misoMatrixPipeIn.send(misoM)

			return misoM

		finally:
			self.inputLock.release()

		# End misoIn ===========================================================

	def misoOut(self): # =======================================================
		# Fetch MISO matrix from own MISO matrix pipe.

		if self.misoMatrixPipeOut.poll():
			return self.misoMatrixOut.recv()

		else:
			return None

		# End misoOut ==========================================================

	def setIn(self, newUpdateIn, newMISOIn): # =================================
		try:
			self.inputLock.acquire()

			self._updateIn = newUpdateIn
			self._misoIn = newMISOIn

		finally:
			self.inputLock.release()
		# End setIn ============================================================

	def printM(self, message, tag = 'S'): # ====================================
		self.printQueue.put_nowait((message, tag))

		# End printM ===========================================================

	def addModule(self, newModuleConstructor): # ===============================
		# Add an FCMkII module to the dataPipeline
		# NOTE: Here newModule is expected to be the constructor of a 
		# standardized FCMkII module:

		newModule = newModuleConstructor(
			self.archiver.getProfile(),
			self.communicator.commandQueue,
			self.communicator.mosiMatrixQueue,
			self.printQueue
		)

		# Connect newModule's output to pipeline's end:
		self.communicator.setIn(newModule.updateOut, newModule.misoOut)

		# Connect newModule's input to pipeline's last output:
		newModule.setIn(
			self.dataPipeline[-1].updateOut, 
			self.dataPipeline[-1].misoOut
		)

		# Add newModule to list:
		self.dataPipeline.append(newModule)

		# End addModule ========================================================

	def shutdown(self): # ======================================================
		# NOTE: Added for standard compliance

		self.printM("[UI] Shutting down...")

		# End shutdown =========================================================
