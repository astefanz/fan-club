################################################################################
## Project: Fan Club Mark II "Master" # File: FCMainWindow.py                 ##
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
Main GUI module for FCMkII

"""
################################################################################


## DEPENDENCIES ################################################################

# GUI:
#from mttkinter import mtTkinter as Tk
import tkinter as Tk
import tkinter.filedialog 
import tkinter.messagebox
import tkinter.font
import tkinter.ttk # "Notebooks"

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
import queue

# FCMkII:
import FCCommunicator as cm
import FCPRCommunicator as pc
import FCArchiver as ac
import FCPrinter as pt
import FCSlave as sv
import FCWidget as wg

import fci.FCPRGrid as gd
import fci.LiveTable as lt
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

# FC Widget names:
COMMUNICATOR = 0
LIVETABLE = 1

## CLASS DEFINITION ############################################################

class FCMainWindow(Tk.Frame):      

	def __init__(self, 
		version,
		commandQueue,
		mosiMatrixQueue,
		spawnQueue,
		printQueue,
		master = None): # ======================================================

		try:
			
			# CONFIGURE MAIN WINDOW = = = = = = = = = = = = = = = = = = = = = = 
			Tk.Frame.__init__(self, master)
			
			# Set title:
			self.master.title("Fan Club MkII [BETA]")

			# Set background:
			self.background = "#e2e2e2"
			self.foreground = "black"
			self.config(bg = self.background)

			self.commandQueue = commandQueue
			self.mosiMatrixQueue = mosiMatrixQueue
			self.spawnQueue = spawnQueue

			# CREATE COMPONENTS = = = = = = = = = = = = = = = = = = = = = = = = 

			# MAIN FRAME -------------------------------------------------------
			self.main = Tk.Frame(self, bg = 'darkgray')
			self.main.pack(fill = Tk.BOTH, expand = True, anchor = 'n')
			self.gridRows = 0
			self.gridColumns = 0
			self.main.grid_columnconfigure(self.gridColumns, weight = 1)

			# TOOLS ------------------------------------------------------------
			self.toolFrame = Tk.Frame(
				self.main,
				bg = self.background, 
				relief = Tk.GROOVE, 
				bd = 1
			) 

			# Passive widget toggle buttons ....................................
			self.widgetToggleFrame = Tk.Frame(
				self.toolFrame,
				bg = self.background
			)
			self.widgetToggleFrame.pack(side = Tk.LEFT)
			
			# Outside widget buttons ...........................................
			self.widgetButtonFrame = Tk.Frame(
				self.toolFrame, bg=self.background)
	
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

			# Pack tool frame ..................................................
			"""
			self.toolFrame.pack(side = Tk.TOP, fill = Tk.X, expand = False,
				anchor = "n")
			"""
			self.toolFrameRow = self.gridRows
			self.gridRows += 1
			self.toolFrame.grid(row = self.toolFrameRow, sticky = Tk.E + Tk.W)

			# RPM LOG ---------------------------------------------------------
			self.rpmLoggerContainerFrame = Tk.Frame(
				self.main, 
				relief = Tk.GROOVE, borderwidth = 1,
				bg=self.background)

			self.rpmLoggerRow = self.gridRows
			self.gridRows += 1
			self.rpmLoggerContainerFrame.grid(
				row = self.rpmLoggerRow, sticky = "EW")

			self.rpmLoggerFrame = Tk.Frame(self.rpmLoggerContainerFrame,
				bg = self.background)
			self.rpmLoggerFrame.pack(anchor = 'c')
			
			# Print timer:
			self.rpmLoggerTimerVar = Tk.StringVar()
			self.rpmLoggerTimerVar.set("00:00:00s")

			self.rpmLoggerTimerSeconds = 0
			self.rpmLoggerTimerMinutes = 0
			self.rpmLoggerTimerHours = 0
			self.rpmLoggerTimerStopFlag = False

			self.rpmLoggerTimerLabel = Tk.Label(
				self.rpmLoggerFrame,
				bg = self.background,
				bd = 1,
				fg = self.foreground,
				relief = Tk.SUNKEN,
				font = ('TkFixedFont', '12'),
				width = 12,
				padx = 4,
				textvariable = self.rpmLoggerTimerVar
			)

			self.rpmLoggerTimerLabel.pack(side = Tk.RIGHT)


			self.rpmLoggerTimerPadding = Tk.Frame(
				self.rpmLoggerFrame,
				width = 20,
				bg = self.background
			)
			self.rpmLoggerTimerPadding.pack(side = Tk.RIGHT, expand = False)

			# Print target (file) label:
			self.rpmLoggerTargetLabel = Tk.Label(self.rpmLoggerFrame,
				background = self.background,
				text = "Record data to: ",
				fg = self.foreground
				)

			self.rpmLoggerTargetLabel.pack(side = Tk.LEFT)

			# Log target text field:

			self.entryRedBG = "#ffc1c1"
			self.entryOrangeBG = "#ffd8b2"
			self.entryWhiteBG = "white"

			self.rpmLoggerTargetVar = Tk.StringVar()
			self.rpmLoggerTargetVar.trace('w', self._fileNameEntryCheck)


			self.rpmLoggerTargetEntry = Tk.Entry(self.rpmLoggerFrame, 
				highlightbackground = self.background,
				width = 17, bg = self.entryRedBG,
				textvariable = self.rpmLoggerTargetVar)
			self.rpmLoggerTargetEntry.pack(side = Tk.LEFT)
	 
			self.rpmLoggerTargetStatus = EMPTY

			# rpmLoggerTarget button:
			self.rpmLoggerTargetButton = Tk.Button(self.rpmLoggerFrame, 
				highlightbackground = self.background, text = "...", 
				command = self._rpmLoggerTargetButtonRoutine)

			self.rpmLoggerTargetButton.pack(side = Tk.LEFT)
			
			# Print padding:
			self.rpmLoggerPadding2 = Tk.Frame(self.rpmLoggerFrame,
				bg = self.background,
				width = 5
				)
			self.rpmLoggerPadding2.pack(side = Tk.LEFT)
			
			# rpmLoggerTarget feedback:
			self.rpmLoggerTargetFeedbackLabel = Tk.Label(
				self.rpmLoggerFrame,
				bg = self.background,
				text = '(No filename)',
				fg = 'darkgray',
				anchor = 'w',
				width = 12
				)
			self.rpmLoggerTargetFeedbackLabel.pack(side = Tk.LEFT)
		
			# Print padding:
			self.rpmLoggerPadding1 = Tk.Frame(self.rpmLoggerFrame,
				bg = self.background,
				width = 20
				)
			self.rpmLoggerPadding1.pack(side = Tk.LEFT)

			# rpmLoggerStartStop button:
			self.rpmLoggerStartStopButton = Tk.Button(self.rpmLoggerFrame, 
				highlightbackground = self.background, text = "Start Recording",
				width = 12,
				command = self._rpmLoggerButtonRoutine,
				)

			self.rpmLoggerStartStopButton.config(state = Tk.DISABLED)

			self.rpmLoggerStartStopButton.pack(side = Tk.LEFT)
			

			# TERMINAL ---------------------------------------------------------

			# Print queue:
			self.printQueue = printQueue

			"""
			self.terminalFrame = Tk.Frame(self.main, 
				bg = self.background,relief = Tk.RIDGE, bd = 1)
			"""
			self.terminal = tm.Terminal(self.main, self.printQueue)

			#self.terminal.pack(side = Tk.TOP, fill = Tk.BOTH, expand = True)
			
			"""
			self.terminalFrame.pack(
				side = Tk.TOP, fill = Tk.BOTH, expand = True, anchor = "n")
			"""
			#self.terminalFrame.grid(row = 1, sticky = Tk.N + Tk.W + Tk.E + Tk.S)
			self.terminalRow = self.gridRows
			self.gridRows += 1
			self.terminal.grid(
				row = self.terminalRow, 
				sticky = Tk.N + Tk.W + Tk.E + Tk.S
			)
			self.main.grid_rowconfigure(self.terminalRow, weight = 1)

			self.terminalCheckButtonVar = Tk.BooleanVar()
			self.terminalCheckButtonVar.set(True)
			self.terminalCheckButton = Tk.Checkbutton(
				self.widgetToggleFrame,
				text = "Terminal",
				bg = self.background,
				fg = self.foreground,
				command = self._terminalToggle,
				variable = self.terminalCheckButtonVar
			)
			self.terminalCheckButton.pack(side = Tk.LEFT)
			
			# FILLER ROW .......................................................
			self.dummy = Tk.Frame(
				self.main,
				bg = 'purple'
			)
			self.dummyRow = self.gridRows
			self.gridRows += 1
			self.main.grid_rowconfigure(self.dummyRow, weight = 0)
			
			"""
			# Add logos:
			self.logoFrame = Tk.Frame(
				self.toolFrame,
				bg = self.background
			)

			self.logoFrame.pack(side = Tk.LEFT)

			self.caltechLogo = Tk.PhotoImage(
				file = "fci/ct.png",
			)
			self.caltechLogo = self.caltechLogo.subsample(3,3)
			self.caltechLogoLabel = Tk.Label(
				self.logoFrame,
				bg = self.background,
				image = self.caltechLogo,
				anchor = Tk.CENTER,
				height = 30,
				bd = 1,
				relief = Tk.SUNKEN
			)
			self.caltechLogoLabel.pack(side = Tk.LEFT)
			
			self.galcitLogo = Tk.PhotoImage(
				file = "fci/galcit.png",
			)
			self.galcitLogo = self.galcitLogo.subsample(20,20)
			self.galcitLogoLabel = Tk.Label(
				self.logoFrame,
				bg = self.background,
				image = self.galcitLogo,
				anchor = Tk.CENTER,
				height = 30,
				bd = 1,
				relief = Tk.SUNKEN
			)
			self.galcitLogoLabel.pack(side = Tk.LEFT)
			"""
	

			# STATUS -----------------------------------------------------------	
			"""
			self.statusBar = sb.StatusBar(self, version)
			self.statusBar.pack(side = Tk.BOTTOM, anchor = "s",
				fill = Tk.X, expand = True)
			"""
			# START UPDATE ROUTINES = = = = = = = = = = = = = = = = = = = = = = 
			
			# Focus on the main window:
			self.master.lift()
			self.pack(fill = Tk.BOTH, expand = True)

			# MODULES ----------------------------------------------------------

			# Inter-process communication:
			#self.updatePipeOut, self.updatePipeIn = pr.Pipe(False)
			#self.misoMatrixPipeOut, self.misoMatrixPipeIn = pr.Pipe(False)

			#self._updateIn = lambda: None
			#self._misoIn = lambda: None

			self.inputLock = threading.Lock()

			# Data structures:
			self.fcWidgets = {}

			# Base modules:
			self.communicator = None
			self.archiver = None

		
			# INITIALIZATION -------------------------------------------------------
			self.printM("GUI \"manager\" thread initializing")

			self.printM("Initializing Archive")
			self.archiver = ac.FCArchiver() 
			self.profile = self.archiver.getProfile()
			self.printM("Archiver initialized", "G")

			macs = []
			for slave in self.archiver.get(ac.savedSlaves):
				macs.append(slave[1])
			self.printM("[UI][OR] Initializing Communicator")

			self.communicator = pc.FCPRCommunicator(
				master = self.main,
				profile = self.profile,
				commandQueue = self.commandQueue,
				mosiMatrixQueue = self.mosiMatrixQueue,
				spawnQueue = self.spawnQueue,
				printQueue = self.printQueue
				)

			self.fcWidgets[COMMUNICATOR] = self.communicator
			
			self.communicatorRow = self.gridRows
			self.gridRows += 1
			self.communicator.grid(
				row = self.communicatorRow, 
				sticky = Tk.S + Tk.W + Tk.E + Tk.N
			)
			self.main.grid_rowconfigure(self.communicatorRow, weight = 1)

			self.communicatorCheckButtonVar = Tk.BooleanVar()
			self.communicatorCheckButtonVar.set(True)
			self.communicatorCheckButton = Tk.Checkbutton(
				self.widgetToggleFrame,
				text = "List",
				bg = self.background,
				fg = self.foreground,
				command = self._communicatorToggle,
				variable = self.communicatorCheckButtonVar
			)
			self.communicatorCheckButton.pack(side = Tk.LEFT)

			# Set up shutdown behavior:
			self.master.protocol("WM_DELETE_WINDOW", self._deactivationRoutine)


			# Set up widgets:	
			profile = self.archiver.getProfile()

			# Grid:
			"""
			self.grid = gd.FCPRGrid(
				self.toolFrame, 
				profile,
				self.commandQueue, 
				self.mosiMatrixQueue, 
				self.printQueue)

			self.grid.pack(side = Tk.RIGHT)
			self.fcWidgets.append(self.grid)
			"""

			# Live table:
			self.liveTable = lt.LiveTable(
				self.toolFrame,
				profile,
				self.spawnQueue,
				self.printQueue
			)
			self.liveTable.pack(side = Tk.RIGHT)
			self.fcWidgets[LIVETABLE] = self.liveTable

			# Launch handlers and start processes:
			self._commandHandler()
			self._misoHandler()
			self.communicator.start()

			# Set minimum sizes:
			self.update_idletasks()

			self.minWidth = max(
				self.toolFrame.winfo_width(),
				self.communicator.getMinSize()[0],
				self.terminal.getMinSize()[0]
			)
			
			self.minHeight = \
				self.toolFrame.winfo_height() + \
				self.communicator.getMinSize()[1] + \
				self.terminal.getMinSize()[1]

			self.master.minsize(
				self.minWidth,
				self.minHeight
			)

		except Exception as e: # Print uncaught exceptions
			tkinter.messagebox.showerror(title = "FCMkII Fatal Error",
				message = "Warning: Uncaught exception in "\
				"GUI constructor: \"{}\"".\
				format(traceback.format_exc()))
			self.master.quit()
		
		# End FCInterface Constructor ==========================================

	# THREADS AND ROUTINES -----------------------------------------------------

	def _misoHandler(self): # =========================================
		
	
		# MAIN LOOP ------------------------------------------------------------
		try:
			# Get Communicator output and update GUI -----------------------
					
			# OUTPUT MATRIX ------------------------------------------------
			matrix = self.communicator.getMISOMatrix()
			if matrix is not None:
				#print("Matrix received: {}".format(matrix))
				for fcWidgetKey, fcWidget in self.fcWidgets.items():
					fcWidget.misoMatrixIn(matrix)

			else:
				del matrix
		
		except Exception as e:
			self.printM("ERROR: Unhandled exception in GUI MISO"\
				" handler: \"{}\"".\
				format(traceback.format_exc()), "E")

		finally:
			self.after(100, self._misoHandler)

		# End _misoHandler =====================================================
	
	def _commandHandler(self): # ===============================================

	
		# MAIN LOOP ------------------------------------------------------------
		try:

			# Get commands from commandQueue and distribute them to their
			# designated target:

			if not self.commandQueue.empty():
				command = self.commandQueue.get_nowait()
				
				self.fcWidgets[command[wg.TARGET]].updateIn(command)
		
		except:
			self.printM("ERROR: Unhandled exception in GUI Command"\
				" handler: \"{}\"".\
				format(traceback.format_exc()), "E")

		finally:
			self.after(100, self._commandHandler)

		# End _commandHandler ==================================================

	# CALLBACKS ----------------------------------------------------------------

	def _settingsButtonRoutine(self): # ========================================
		# TODO: IMPLEMENT
		
		pass

		# End _settingsButtonRoutine ===========================================

	def _bootloaderButtonRoutine(self): # ======================================
		# TODO: IMPLEMENT
		
		pass 

		# End _bootloaderButtonRoutine =========================================

	def _deactivationRoutine(self): # ==========================================
	
		# Close GUI:
		self.destroy()
		self.master.quit()
		
		for fcWdgetKey, fcWidget in self.fcWidgets.items():
			fcWidget.stop()

		# End _deactivationRoutine =============================================

	def _terminalToggle(self, event = None, force = None): # ====================
		
		if force is True or \
			(self.terminalCheckButtonVar.get() is True and force is not False):
			self.terminalCheckButtonVar.set(True)
			self.main.grid_rowconfigure(self.terminalRow, weight = 1)
			self.main.grid_rowconfigure(self.dummyRow, weight = 0)
			self.dummy.grid_forget()
			self.terminal.toggle(force = True)

		else:
			self.terminalCheckButtonVar.set(False)
			self.main.grid_rowconfigure(self.terminalRow, weight = 0)

			if self._areAllCheckButtonsFalse():
				self.main.grid_rowconfigure(self.dummyRow, weight = 1)
				self.dummy.grid(row = self.dummyRow)
			else:
				self.main.grid_rowconfigure(self.dummyRow, weight = 0)
				self.dummy.grid_forget()
			
			self.terminal.toggle(force = False)
		
		# End _terminalToggle ==================================================

	def _communicatorToggle(self, event = None, force = False): # ==============
		
		if self.communicatorCheckButtonVar.get() is True or force is True:
			self.communicatorCheckButtonVar.set(True)
			self.main.grid_rowconfigure(self.communicatorRow, weight = 1)
			self.main.grid_rowconfigure(self.dummyRow, weight = 0)
			self.dummy.grid_forget()
			self.communicator.toggle(force = True)

		else:
			self.communicatorCheckButtonVar.set(False)
			self.main.grid_rowconfigure(self.communicatorRow, weight = 0)
			
			if self._areAllCheckButtonsFalse():
				self.main.grid_rowconfigure(self.dummyRow, weight = 1)
				self.dummy.grid(row = self.dummyRow)

			else:
				self.main.grid_rowconfigure(self.dummyRow, weight = 0)
				self.dummy.grid_forget()
			
				"""
				self._terminalToggle(force = False)
				self._terminalToggle(force = True)
				"""

			self.communicator.toggle(force = False)
		
		# End _communicatorToggle ==============================================
	
	def _areAllCheckButtonsFalse(self): # ======================================
		return (not self.terminalCheckButtonVar.get()) and \
			(not self.communicatorCheckButtonVar.get())

		# End _areAllCheckButtonsFalse =========================================

	def _fileNameEntryCheck(self, *args): # ====================================
		# ABOUT: Validate the file name entered.
		# Get file name:
		prospectiveFileName = self.rpmLoggerTargetVar.get()
		# Set sentinel:
		normal = True
	
		# Check file name:
		if prospectiveFileName == '' and self.rpmLoggerTargetStatus != EMPTY:
			#                           \-----------------------------/
			#								Avoid redundant changes
			# Can't rpmLogger:
			self.rpmLoggerStartStopButton.config(state = Tk.DISABLED)
			self.rpmLoggerTargetEntry.config(bg = self.entryRedBG)
			self.rpmLoggerTargetFeedbackLabel.config(text = "(No filename)")
			self.rpmLoggerTargetStatus = EMPTY

			# Done
			return

		elif '.' not in prospectiveFileName:
			# No extension. Assume .txt and warn:
			normal = False
			
			if self.rpmLoggerTargetStatus != NODOT:

				self.rpmLoggerTargetEntry.config(bg = self.entryWhiteBG)
				self.rpmLoggerTargetFeedbackLabel.config(text = '(.txt assumed)')
				self.rpmLoggerStartStopButton.config(state = Tk.NORMAL)
				prospectiveFileName += ".txt"

				self.rpmLoggerTargetStatus = NODOT

		elif prospectiveFileName.split('.')[-1] == '':
			# Invalid extension:
			normal = False

			if self.rpmLoggerTargetStatus != BADEXT:

				self.rpmLoggerStartStopButton.config(state = Tk.DISABLED)
				self.rpmLoggerTargetEntry.config(bg = self.entryRedBG)
				self.rpmLoggerTargetFeedbackLabel.config(text = "(Bad extension)")

				self.rpmLoggerTargetStatus = BADEXT

		# Check for repetition
		if os.path.isfile(prospectiveFileName) and \
			self.rpmLoggerTargetStatus != REPEATED:
			# Change color and warn:
			self.rpmLoggerTargetEntry.config(bg = self.entryOrangeBG)
			self.rpmLoggerTargetFeedbackLabel.config(text = 'FILE EXISTS')
			self.rpmLoggerStartStopButton.config(state = Tk.NORMAL)
			
			if self.rpmLoggerTargetStatus == NODOT:
				self.rpmLoggerTargetStatus = NODOT_REPEATED
			else:
				self.rpmLoggerTargetStatus = REPEATED

		elif normal and self.rpmLoggerTargetStatus != NORMAL:
			# If this block of code is reached, then the prospective filename is
			# - Not empty
			# - Not missing an extension, and
			# - Not repeated
		
			# Therefore, mark it as NORMAL:
			self.rpmLoggerTargetEntry.config(bg = self.entryWhiteBG)
			self.rpmLoggerTargetFeedbackLabel.config(text = '')
			self.rpmLoggerStartStopButton.config(state = Tk.NORMAL)

			self.rpmLoggerTargetStatus = NORMAL

		# End _fileNameEntryCheck ==============================================

	def _rpmLoggerTargetButtonRoutine(self): # =================================
		# ABOUT: To be used by file name button. 
		# Sets file name and stops Printer.
		try:
			
			# Proceed in accordance w/ Printer status:
			if self.rpmLogger.getStatus() == pt.OFF:
				# If the rpmLoggerer is off, choose a file name.

				# Disable rpmLogger button while choosing file:
				self.rpmLoggerStartStopButton.config(state = Tk.DISABLED)

				self.rpmLoggerTargetVar.set(tkinter.filedialog.asksaveasfilename(
					initialdir = os.getcwd(), # Get current working directory
					title = "Choose file",
					filetypes = (("Text files","*.txt"),("CSV files", "*.csv"),
						("All files","*.*"))
					))
				
				# Set the visibility to the right end of the file name:
				self.rpmLoggerTargetEntry.xview_moveto(1)

			elif self.rpmLogger.getStatus() is pt.ON:
					
				raise RuntimeError("Cannot use target file specifier while "\
					"rpmLogging")
			else:
				# Unrecognized rpmLoggerer status (wot)
				raise RuntimeError("Unrecognized Logger status {} (wot)".\
					format(self.rpmLoggerer.getStatus()))
		except Exception as e:
			self.printM("[printTargetButton] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")


		# End _rpmLoggerTargetButtonRoutine ====================================
	
	def _rpmLoggerStopRoutine(self): # =========================================
		# ABOUT: Schedules itself for future calls until the Printer module is
		# done terminating. When the Printer module is done, restores buttons
		# and fields.

		# Check Printer status:
		if self.rpmLogger.getStatus() == pt.OFF:
			# Restore buttons 
			self.rpmLoggerStartStopButton.config(text = "Start Recording")
			self.rpmLoggerTargetEntry.config(state = Tk.NORMAL)
			self.rpmLoggerTargetButton.config(state = Tk.NORMAL)
			self.rpmLoggerTimerLabel.config(state = Tk.NORMAL)
			self.rpmLoggerTargetStatus = RESTORE
				# "Modify" targetFileVar to fire its trace callback:
			self.rpmLoggerTargetVar.set(self.rpmLoggerTargetVar.get())
			

		else:
			# Schedule future call to check again:
			self.after(200, self._rpmLoggerStopRoutine)

		# End _rpmLoggerStopRoutine ============================================
	
	def _rpmLoggerTimerRoutine(self): # ========================================
		# ABOUT: Update the RPM log timer periodically for as long as it is
		# active. This method is meant to be called by whatever component acti-
		# vates the Printer (i.e starts rpmLoggering).

		# Check Printer status:
		if not self.rpmLoggerTimerStopFlag:
			# Update timer label
			self.rpmLoggerTimerSeconds += 1

			if self.rpmLoggerTimerSeconds >= 60:
				self.rpmLoggerTimerSeconds = 0
				self.rpmLoggerTimerMinutes += 1

				if self.rpmLoggerTimerMinutes >= 60:
					self.rpmLoggerTimerMinutes = 0
					self.rpmLoggerTimerHours += 1
					
					if self.rpmLoggerTimerHours >= 99:
						self.rpmLoggerTimerHours = 99
			
			self.rpmLoggerTimerVar.set("{:02d}:{:02d}:{:02d}s".format(
				self.rpmLoggerTimerHours,
				self.rpmLoggerTimerMinutes,
				self.rpmLoggerTimerSeconds))

			self.after(1000, self._rpmLoggerTimerRoutine)

		else:
			# Reset timer label and end chain of calls:
			self.rpmLoggerTimerSeconds = 0
			self.rpmLoggerTimerMinutes = 0
			self.rpmLoggerTimerHours = 0
			self.rpmLoggerTimerVar.set("00:00:00s")
			return


		# End _rpmLoggerTimerRoutine ===========================================


	def _rpmLoggerButtonRoutine(self): # =======================================
		pass

		# End _rpmLoggerStartStopButton ========================================

	# UTILITY FUNCTIONS --------------------------------------------------------
	def printM(self, message, tag = 'S'): # ====================================
		self.printQueue.put_nowait(("[MW] " + message, tag))

		# End printM ===========================================================
