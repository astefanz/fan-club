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

# Data:
import numpy as np
import Queue

# FCMkII:
import FCCommunicator
import FCArchiver as ac
import FCPrinter as pt
import FCSlave as sv

from fci import MainGrid as mg
from fci import SlaveDisplay as sd

from fci import SlaveContainer as sc

from auxiliary.debug import d

## CONSTANTS ###################################################################

# Debug flag (for printing):
DEBUG = False

# Selection change codes:
INCREASE = True
DECREASE = False

# Broadcast status color codes:
GREEN = 1
GREEN2 = 2
BLUE = 3
RED = 0

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

	def __init__(self, version, master=None): # ================================
		
		try:


			self.ableToPrint = False	# Keep track in case of an error during
										# construction...

			Tk.Frame.__init__(self, master)
			
			# Build "loading" window
			init_lw = Tk.Toplevel()
			init_lw.title("")
			init_lw.lift()
			init_lw.focus_force()
			init_lw.grab_set()
			
			init_lw.geometry('+%d+%d' % ( \
				(init_lw.winfo_screenwidth()/4),
				(init_lw.winfo_screenheight()/7)
				)
			)
			init_pbar = ttk.Progressbar(init_lw, orient = "horizontal", 
				length = 490, mode = "determinate")	

			init_pbar.pack(side = Tk.TOP, fill = Tk.X, expand = True)
			init_pbar["value"] = 0
			init_pbar["maximum"] = 56

			init_label = Tk.Label(init_lw, 
				text = "FCMkII -- Loading", anchor = 'c')

			init_label.pack(side = Tk.TOP, fill = Tk.BOTH, expand = True)

			init_pbar["value"] = 1

			# Initialization order:
			# 1. Build and display GUI
			# 2. Build Archiver and Printer and try to load profile
			# 3. Build Communicator and try to start a connection

			# INITIALIZATION STEP 1: BUILD AND DISPLAY GUI #########################

			# CONFIGURE MAIN WINDOW = = = = = = = = = = = = = = = = = = = = = = = =

			# Set title:
			self.master.title("Fan Club MkII [BETA]")

			# Set background:
			self.background = "#e2e2e2"
			self.foreground = "black"
			self.config(bg = self.background)

			# Set debug foreground:
			self.debugColor = "#ff007f"

			init_pbar["value"] = 2
			# CREATE COMPONENTS = = = = = = = = = = = = = = = = = = = = = = = = = = 

			# MAIN FRAME -----------------------------------------------------------
			self.main = Tk.Frame(self)
			self.main.pack(fill = Tk.BOTH, expand = True)

			
			init_pbar["value"] = 3
			# OPTIONS BAR ----------------------------------------------------------
			self.optionsBarFrame = Tk.Frame(
				self.main,
				relief = Tk.GROOVE,
				bd = 1,
				bg = self.background
			)

			self.optionsBarFrame.pack(side = Tk.TOP, fill = Tk.X)

			init_pbar["value"] = 4
			# TERMINAL TOGGLE ......................................................
			self.terminalToggleVar = Tk.BooleanVar()
			self.terminalToggleVar.set(False)

			self.terminalToggle = Tk.Checkbutton(self.optionsBarFrame, 
				text ="Terminal", variable = self.terminalToggleVar, 
				bg = self.background, fg = self.foreground, 
				command = self._terminalToggle)
			self.terminalToggle.config( state = Tk.NORMAL)
			self.terminalToggle.pack(side = Tk.LEFT)

			init_pbar["value"] = 5
			# SLAVE LIST TOGGLE ....................................................
			self.slaveListToggleVar = Tk.BooleanVar()
			self.slaveListToggleVar.set(False)

			self.slaveListToggle = Tk.Checkbutton(self.optionsBarFrame,
				text ="List", variable = self.slaveListToggleVar, 
				bg = self.background, fg = self.foreground,
				command = self._slaveListToggle)

			self.slaveListToggle.config( state = Tk.NORMAL)
			self.slaveListToggle.pack(side = Tk.LEFT)

			init_pbar["value"] = 6
			# SLAVE DISPLAY TOGGLE .................................................
			self.slaveDisplayToggleVar = Tk.BooleanVar()
			self.slaveDisplayToggleVar.set(False)

			self.slaveDisplayToggle = Tk.Checkbutton(self.optionsBarFrame,
				text ="Display", variable = self.slaveDisplayToggleVar, 
				bg = self.background, fg = self.foreground,
				command = self._slaveDisplayToggle)

			self.slaveDisplayToggle.config( state = Tk.NORMAL)
			self.slaveDisplayToggle.pack(side = Tk.LEFT)

			init_pbar["value"] = 7
			# SETTINGS BUTTON ......................................................
			self.settingsButton = Tk.Button(
				self.optionsBarFrame,
				text = "Help",
				highlightbackground = self.background,
				state = Tk.DISABLED
			)
			self.settingsButton.pack(side = Tk.RIGHT)	

			init_pbar["value"] = 8
			# SETTINGS BUTTON ......................................................
			self.settingsButton = Tk.Button(
				self.optionsBarFrame,
				text = "Settings",
				highlightbackground = self.background
			)
			self.settingsButton.pack(side = Tk.RIGHT)	

			init_pbar["value"] = 9
			# PLOT BUTTON ..........................................................
			self.plotButton = Tk.Button(
				self.optionsBarFrame,
				text = "Activate Plot",
				highlightbackground = self.background,
				state = Tk.DISABLED
			)
			self.plotButton.pack(side = Tk.RIGHT)	

			init_pbar["value"] = 10
			# GRID BUTTON ..........................................................
			self.gridButton = Tk.Button(
				self.optionsBarFrame,
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

			init_pbar["value"] = 11
			# MAIN DISPLAY ---------------------------------------------------------

			# Main display frame ..................................................
			self.mainDisplayFrame = Tk.Frame(
				self.main, height = 100, bg = '#212121')

			#self.mainDisplayFrame.pack(
				#fill = Tk.BOTH, expand = True, side = Tk.TOP)

			init_pbar["value"] = 12
			# ARRAY ----------------------------------------------------------------

			# Array Frame ..........................................................
			self.arrayFrame = Tk.Frame(self.mainDisplayFrame, bg = 'white',
				relief = Tk.SUNKEN, borderwidth = 3)
			
			init_pbar["value"] = 13
			# TERMINAL -------------------------------------------------------------
			self.terminalContainerFrame = Tk.Frame(self.main, bg = self.background)
			self.terminalContainerFrame.pack(
				side = Tk.BOTTOM, fill = Tk.X, expand = False, anchor = 's')

			self.terminalFrame = Tk.Frame(self.terminalContainerFrame,
				bg = self.background, bd = 1, relief = Tk.GROOVE)
			#self.terminalFrame.pack(fill = Tk.BOTH, expand = False)
			# Comment out to not start w/ hidden terminal by default

			init_pbar["value"] = 14
			# MAIN TERMINAL - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
			self.mainTerminal = ttk.Frame(self.terminalFrame)
			self.mainTerminal.pack(fill = Tk.BOTH, expand = False)
			self.mainTLock = threading.Lock()
			self.mainTText = Tk.Text(self.mainTerminal, height = 10, 
				fg = "#424242", bg=self.background, font = ('TkFixedFont'),
				selectbackground = "#cecece",
				state = Tk.DISABLED)
			self.mainTScrollbar = Tk.Scrollbar(self.mainTerminal)
			self.mainTScrollbar.pack(side = Tk.RIGHT, fill=Tk.Y)
			self.mainTScrollbar.config(command=self.mainTText.yview)
			self.mainTText.config(yscrollcommand = self.mainTScrollbar.set)
			self.mainTText.bind("<1>", 
				lambda event: self.mainTText.focus_set())
			self.mainTText.pack(fill =Tk.BOTH, expand = True)
			# Configure tags:
			self.mainTText.tag_config("S")
			self.mainTText.tag_config("G", foreground = "#168e07")
			self.mainTText.tag_config(\
				"W", underline = 1, foreground = "orange")
			self.mainTText.tag_config(\
				"E", underline = 1, foreground = "red", background = "#510000")
			self.mainTText.tag_config(\
				"D", foreground = self.debugColor)
			
			init_pbar["value"] = 15
			# TERMINAL CONTROL FRAME ...............................................

			self.terminalControlFrame = Tk.Frame(self.terminalFrame, 
				bg = self.background)

			# Autoscroll checkbox:
			self.autoscrollVar = Tk.IntVar()

			self.autoscrollButton = Tk.Checkbutton(self.terminalControlFrame, 
				text ="Auto-scroll", variable = self.autoscrollVar, 
				bg = self.background, fg = self.foreground)

			self.terminalControlFrame.pack(fill = Tk.X)

			# Debug checkbox:
			self.debugVar = Tk.IntVar()

			self.debugButton = Tk.Checkbutton(self.terminalControlFrame, 
				text ="Debug prints", variable = self.debugVar, 
				bg = self.background, fg = self.foreground)

			# Terminal print:
			self.terminalVar = Tk.IntVar()
			self.terminalVar.set(1)

			self.terminalButton = Tk.Checkbutton(self.terminalControlFrame, 
				text ="Terminal output", variable = self.terminalVar, 
				bg = self.background, fg = self.foreground)

			init_pbar["value"] = 16
			# TERMINAL SETUP:

			self.autoscrollButton.pack(side = Tk.LEFT)
			self.debugButton.pack(side = Tk.LEFT)
			self.terminalButton.pack(side = Tk.LEFT)
			self.autoscrollButton.select()

			init_pbar["value"] = 17
			# SLAVE LIST -----------------------------------------------------------

			# Slave list container .................................................
			self.slaveListContainer = Tk.Frame(self.main)
			self.slaveListContainer.pack(
				side = Tk.BOTTOM, fill = Tk.BOTH, expand = True, anchor = 's')

			# Slave list frame .....................................................
			self.slaveListFrame = Tk.Label(self.slaveListContainer,
				bg = self.background, borderwidth = 1, relief = Tk.GROOVE)
			#self.slaveListFrame.pack(fill = Tk.BOTH, expand = True)

			# List of Slaves .......................................................

			# Create list:
			self.slaveList = ttk.Treeview(self.slaveListFrame, 
				selectmode="browse", height = 5)
			self.slaveList["columns"] = \
				("Index", "Name","MAC","Status","IP","Fans", "Version")

			# Create columns:
			self.slaveList.column('#0', width = 20, stretch = False)
			self.slaveList.column("Index", width = 20, anchor = "center")
			self.slaveList.column("Name", width = 40)
			self.slaveList.column("MAC", width = 50, anchor = "center")
			self.slaveList.column("Status", width = 30, anchor = "center")
			self.slaveList.column("IP", width = 50, anchor = "center")
			self.slaveList.column("Fans", width = 50, stretch = False, 
				anchor = "center")
			self.slaveList.column("Version", width = 50, 
				anchor = "center")

			# Configure column headings:
			self.slaveList.heading("Index", text = "Index")
			self.slaveList.heading("Name", text = "Name")
			self.slaveList.heading("MAC", text = "MAC")
			self.slaveList.heading("Status", text = "Status")
			self.slaveList.heading("IP", text = "IP")
			self.slaveList.heading("Fans", text = "Fans")
			self.slaveList.heading("Version", text = "Version")

			# Configure tags:
			self.slaveList.tag_configure(
				"C", 
				background= '#d1ffcc', 
				foreground = '#0e4707', 
				font = 'TkFixedFont 12 ') # Connected
			
			self.slaveList.tag_configure(
				"B", 
				background= '#ccdeff', 
				foreground ='#1b2d4f', 
				font = 'TkFixedFont 12 ') # Busy

			self.slaveList.tag_configure(
			"D", 
			background= '#ffd3d3', 
			foreground ='#560e0e', 
			font = 'TkFixedFont 12 bold')# Disconnected

			self.slaveList.tag_configure(
			"K",
			background= '#fffaba',
			foreground ='#44370b',
			font = 'TkFixedFont 12 bold') # Known

			self.slaveList.tag_configure(
			"A", 
			background= '#ededed', 
			foreground ='#666666',
			font = 'TkFixedFont 12 ') # Available

			# Save previous selection:
			self.oldSelection = None

			# Bind command:
			self.slaveList.bind('<Double-1>', self._slaveListMethod)

			self.slaveList.pack(fill = Tk.BOTH, expand = True, anchor = 's')

			
			init_pbar["value"] = 18
			# SLAVE DISPLAY --------------------------------------------------------
			# Slave display frame ..................................................
			self.slaveDisplayFrame = Tk.Frame(self.main,
				bg = self.background,
				bd = 1,
				relief = Tk.GROOVE)
			self.slaveDisplayFrame.pack(
				side = Tk.BOTTOM, fill = Tk.X, expand = False, anchor = 's')


			# CONTROL --------------------------------------------------------------
			self.controlFrame = Tk.Frame(self, 
				relief = Tk.GROOVE, borderwidth = 1,
				bg=self.background)

			self.controlFrame.pack(fill = Tk.X, expand = False)

			
			init_pbar["value"] = 19
			# ARRAY CONTROL ........................................................

			self.arrayControlFrame = Tk.Frame(self.controlFrame, 
				bg = self.background)

			self.arrayControlFrame.pack(expand = False)

			self.selectedCommand = Tk.StringVar()
			self.selectedCommand.set("Set Duty Cycle")
			self.commandMenu = Tk.OptionMenu(self.arrayControlFrame, 
				self.selectedCommand,"Set Duty Cycle", "Chase RPM", 
				command = self._changeCommandMenu)

			self.commandLabelText = Tk.StringVar()
			self.commandLabelText.set("  DC: ")
			self.commandLabel = Tk.Label(self.arrayControlFrame, 
				textvariable = self.commandLabelText, 
				width = 4,
				justify = Tk.LEFT,
				background = self.background,
				fg = self.foreground)

			self.commandMenu.configure(highlightbackground = self.background)
			self.commandMenu.configure(background = self.background)

			self.commandMenu.pack(side = Tk.LEFT)
			self.commandLabel.pack(side = Tk.LEFT)

			validateC = self.register(self._validateN)
			self.commandEntry = Tk.Entry(self.arrayControlFrame, 
				highlightbackground = self.background,
				width = 7, validate = 'key', validatecommand = \
					(validateC, '%S', '%s', '%d'))
			self.commandEntry.pack(side = Tk.LEFT)

			self.sendButton = Tk.Button(self.arrayControlFrame, 
				highlightbackground = self.background, text = "Send",
				command = self._send)

			self.sendButton.pack(side = Tk.LEFT)

			self.bind("<Return>", self._send)

			# Hold toggle:
			self.keepSelectionVar = Tk.BooleanVar()
			self.keepSelectionVar.set(True)

			self.keepSelectionButton = Tk.Checkbutton(self.arrayControlFrame, 
				variable = self.keepSelectionVar, 
				bg = self.background)

			self.keepSelectionButton.pack(side = Tk.LEFT)
			

			# Shutdown button frame:
			self.shutdownButtonFrame = Tk.Frame(
				self.arrayControlFrame, 
				relief = Tk.RIDGE, 
				borderwidth = 1)
			self.shutdownButtonFrame.pack(
				side = Tk.RIGHT, expand = False)

			# Shutdown button:
			self.shutdownButton = Tk.Button(self.shutdownButtonFrame,
				highlightbackground = "#890c0c", text = "SHUTDOWN",
				command = self._shutdownButton, font = 'TkFixedFont 12 bold ')
			self.shutdownButton.pack()
			
			# Disconnect all button frame:
			self.disconnectAllButtonFrame = Tk.Frame(
				self.arrayControlFrame, 
				relief = Tk.RIDGE, 
				borderwidth = 1)
			self.disconnectAllButtonFrame.pack(
				side = Tk.RIGHT, expand = False)

			# Disconnect all button:
			self.disconnectAllButton = Tk.Button(self.disconnectAllButtonFrame,
				highlightbackground = "#890c0c", text = "DISCONNECT ALL",
				command = self._disconnectAllButton, font = 'TkFixedFont 12 bold ')
			self.disconnectAllButton.pack()
			
			# Connect All button:
			self.connectAllButtonFrame = Tk.Frame(
				self.arrayControlFrame,
				bg = self.background
				)
			self.connectAllButtonFrame.pack(side = Tk.RIGHT)

			self.connectAllButtonPacked = False
			self.connectAllButton = Tk.Button(self.connectAllButtonFrame, 
				highlightbackground = self.background, text = "Add All", 
				command = self._connectAllSlaves)

			# Deselect All button:
			self.deselectAllButton = Tk.Button(self.arrayControlFrame, 
				highlightbackground = self.background, text = "Deselect All", 
				command = self.deselectAllSlaves)

			self.deselectAllButton.pack(side = Tk.RIGHT)

			# Select All button:
			self.selectAllButton = Tk.Button(self.arrayControlFrame, 
				highlightbackground = self.background, text = "Select All", 
				command = self.selectAllSlaves)

			self.selectAllButton.pack(side = Tk.RIGHT)


			init_pbar["value"] = 20
			# PRINTING -------------------------------------------------------------
			self.printContainerFrame = Tk.Frame(self, 
				relief = Tk.GROOVE, borderwidth = 1,
				bg=self.background)

			self.printContainerFrame.pack(fill = Tk.X, expand = False)

			self.printFrame = Tk.Frame(self.printContainerFrame,
				bg = self.background)
			self.printFrame.pack(anchor = 'c')
			
			# Print timer:
			self.printTimerVar = Tk.StringVar()
			self.printTimerVar.set("00:00:00s")

			self.printTimerSeconds = 0
			self.printTimerMinutes = 0
			self.printTimerHours = 0
			self.printTimerStopFlag = False

			self.printTimerLabel = Tk.Label(
				self.printFrame,
				bg = self.background,
				bd = 1,
				fg = self.foreground,
				relief = Tk.SUNKEN,
				font = ('TkFixedFont', '12'),
				width = 12,
				padx = 4,
				textvariable = self.printTimerVar
			)

			self.printTimerLabel.pack(side = Tk.RIGHT)


			self.printTimerPadding = Tk.Frame(
				self.printFrame,
				width = 20,
				bg = self.background
			)
			self.printTimerPadding.pack(side = Tk.RIGHT, expand = False)

			# Print target (file) label:
			self.printTargetLabel = Tk.Label(self.printFrame,
				background = self.background,
				text = "Record data to: ",
				fg = self.foreground
				)

			self.printTargetLabel.pack(side = Tk.LEFT)

			init_pbar["value"] = 21
			# Print target text field:

			self.entryRedBG = "#ffc1c1"
			self.entryOrangeBG = "#ffd8b2"
			self.entryWhiteBG = "white"

			self.printTargetVar = Tk.StringVar()
			self.printTargetVar.trace('w', self._fileNameEntryCheck)


			self.printTargetEntry = Tk.Entry(self.printFrame, 
				highlightbackground = self.background,
				width = 17, bg = self.entryRedBG,
				textvariable = self.printTargetVar)
			self.printTargetEntry.pack(side = Tk.LEFT)
	 
			self.printTargetStatus = EMPTY

			# printTarget button:
			self.printTargetButton = Tk.Button(self.printFrame, 
				highlightbackground = self.background, text = "...", 
				command = self._printTargetButtonRoutine)

			self.printTargetButton.pack(side = Tk.LEFT)
			
			# Print padding:
			self.printPadding2 = Tk.Frame(self.printFrame,
				bg = self.background,
				width = 5
				)
			self.printPadding2.pack(side = Tk.LEFT)
			
			# printTarget feedback:
			self.printTargetFeedbackLabel = Tk.Label(
				self.printFrame,
				bg = self.background,
				text = '(No filename)',
				fg = 'darkgray',
				anchor = 'w',
				width = 12
				)
			self.printTargetFeedbackLabel.pack(side = Tk.LEFT)
		
			# Print padding:
			self.printPadding1 = Tk.Frame(self.printFrame,
				bg = self.background,
				width = 20
				)
			self.printPadding1.pack(side = Tk.LEFT)

			# printStartStop button:
			self.printStartStopButton = Tk.Button(self.printFrame, 
				highlightbackground = self.background, text = "Start Recording",
				width = 12,
				command = self._printButtonRoutine,
				)

			self.printStartStopButton.config(state = Tk.DISABLED)

			self.printStartStopButton.pack(side = Tk.LEFT)
			
			init_pbar["value"] = 22
			# STATUS ---------------------------------------------------------------
			self.statusFrame = Tk.Frame(self, relief = Tk.GROOVE, borderwidth = 1,
				 bg=self.background, height = 10)
				
			self.versionLabel = Tk.Label(
				self.statusFrame, text = "Version: " + version,
				bg = self.background, fg = "#424242")
			self.versionLabel.pack(side = Tk.RIGHT)

			self.statusFrame.pack(
				fill = Tk.X, expand = False, side =Tk.BOTTOM, anchor = 's')

			# TRACKED VARIABLES ....................................................

			# Slave counter variables:
			self.totalSlaves = 0
			self.totalSlavesVar = Tk.IntVar()
			self.totalSlavesVar.set(0)

			self.statusVars = {}
			self.statusInts = {}

			self.statusInts[sv.CONNECTED] = 0
			self.statusVars[sv.CONNECTED] = Tk.IntVar()

			self.statusInts[sv.DISCONNECTED] = 0
			self.statusVars[sv.DISCONNECTED] = Tk.IntVar()

			self.statusInts[sv.KNOWN] = 0
			self.statusVars[sv.KNOWN] = Tk.IntVar()

			self.statusInts[sv.AVAILABLE] = 0
			self.statusVars[sv.AVAILABLE] = Tk.IntVar()

			# Slave count labels:

			self.slaveCounterPaddedFrame = Tk.Frame(
				self.statusFrame,
				bg = self.background,
				pady = 3
				)

			self.slaveCounterPaddedFrame.pack(side = Tk.LEFT)

			self.slaveCounterFrame = Tk.Frame(
				self.slaveCounterPaddedFrame,
				bg = self.background,
				relief = Tk.SUNKEN,
				bd = 1,
				pady = 0	)
			self.slaveCounterFrame.pack(side = Tk.LEFT)

			# Total Slaves:
			self.totalSlavesLabel = Tk.Label(
				self.slaveCounterFrame,
				bg = self.background,
				text = "Total: ",
				font = ('TkDefaultFont', '10')
				)
			self.totalSlavesLabel.pack(side = Tk.LEFT)

			self.totalSlavesCounter = Tk.Label(
				self.slaveCounterFrame,
				bg = self.background,
				width = 3, anchor = "e",
				textvariable = self.totalSlavesVar,
				font = ('TkFixedFont', '10')
				)
			self.totalSlavesCounter.pack(side = Tk.LEFT)

			# Connected Slaves:
			self.connectedSlavesLabel = Tk.Label(
				self.slaveCounterFrame,
				bg = self.background,
				text = "Cn: ",
				fg = "#168e07",
				font = ('TkDefaultFont', '10')
				)
			self.connectedSlavesLabel.pack(side = Tk.LEFT)

			self.connectedSlavesCounter = Tk.Label(
				self.slaveCounterFrame,
				bg = self.background,
				width = 3, anchor = "e",
				textvariable = self.statusVars[sv.CONNECTED],
				font = ('TkFixedFont', '10'),
				fg = "#168e07"
				)
			self.connectedSlavesCounter.pack(side = Tk.LEFT)
			
			# Disconnected Slaves:
			self.disconnectedSlavesLabel = Tk.Label(
				self.slaveCounterFrame,
				bg = self.background,
				fg = "#510000",
				text = "Dc: ",
				font = ('TkDefaultFont', '10')
				)
			self.disconnectedSlavesLabel.pack(side = Tk.LEFT)

			self.disconnectedSlavesCounter = Tk.Label(
				self.slaveCounterFrame,
				bg = self.background,
				fg = "#510000",
				width = 3, anchor = "e",
				textvariable = self.statusVars[sv.DISCONNECTED],
				font = ('TkFixedFont', '10')
				)
			self.disconnectedSlavesCounter.pack(side = Tk.LEFT)

			# Known Slaves:
			self.knownSlavesLabel = Tk.Label(
				self.slaveCounterFrame,
				bg = self.background,
				text = "Kn: ",
				fg = 'orange',
				font = ('TkDefaultFont', '10')
				)
			self.knownSlavesLabel.pack(side = Tk.LEFT)

			self.knownSlavesCounter = Tk.Label(
				self.slaveCounterFrame,
				bg = self.background,
				width = 3, anchor = "e",
				textvariable = self.statusVars[sv.KNOWN],
				font = ('TkFixedFont', '10'),
				fg = 'orange'
				)
			self.knownSlavesCounter.pack(side = Tk.LEFT)
			
			# Available Slaves:
			self.availableSlavesLabel = Tk.Label(
				self.slaveCounterFrame,
				bg = self.background,
				text = "Av: ",
				fg = 'darkgray',
				font = ('TkDefaultFont', '10')
				)
			self.availableSlavesLabel.pack(side = Tk.LEFT)

			self.availableSlavesCounter = Tk.Label(
				self.slaveCounterFrame,
				bg = self.background,
				width = 3, anchor = "e",
				textvariable = self.statusVars[sv.AVAILABLE],
				font = ('TkFixedFont', '10'),
				fg = 'darkgray'
				)
			self.availableSlavesCounter.pack(side = Tk.LEFT)


			# Selection counter variables:
			self.selectedSlaves = 0
			self.selectedSlavesVar = Tk.IntVar()
			self.selectedSlavesVar.set(0)

			self.selectedFans = 0
			self.selectedFansVar = Tk.IntVar()
			self.selectedFansVar.set(0)


			self.selectionCounterFrame = Tk.Frame(
				self.slaveCounterPaddedFrame,
				bg = self.background,
				relief = Tk.SUNKEN,
				bd = 1,
				pady = 0	)
			self.selectionCounterFrame.pack(side = Tk.LEFT)

			# Selected Slaves:
			self.selectedSlavesLabel = Tk.Label(
				self.selectionCounterFrame,
				bg = self.background,
				text = "Selected Modules: ",
				fg = 'black',
				font = ('TkDefaultFont', '10')
				)
			self.selectedSlavesLabel.pack(side = Tk.LEFT)

			self.selectedSlavesCounter = Tk.Label(
				self.selectionCounterFrame,
				bg = self.background,
				width = 3, anchor = "e",
				textvariable = self.selectedSlavesVar,
				font = ('TkFixedFont', '10'),
				fg = 'orange'
				)
			self.selectedSlavesCounter.pack(side = Tk.LEFT)

			# Selected Fans:
			self.selectedFansLabel = Tk.Label(
				self.selectionCounterFrame,
				bg = self.background,
				text = "Selected Fans: ",
				fg = 'black',
				font = ('TkDefaultFont', '10')
				)
			self.selectedFansLabel.pack(side = Tk.LEFT)

			self.selectedFansCounter = Tk.Label(
				self.selectionCounterFrame,
				bg = self.background,
				width = 5, anchor = "e",
				textvariable = self.selectedFansVar,
				font = ('TkFixedFont', '10'),
				fg = 'orange'
				)
			self.selectedFansCounter.pack(side = Tk.LEFT)

			init_pbar["value"] = 23
			# THREAD ACTIVITY DISPLAYS .............................................

			self.displayRED = "red"
			self.displayGREEN1 = "#13590b"
			self.displayGREEN2 = "#33ed1e"
			self.displayBLUE = "#4fa7ff"

			# Connection status:
			self.connectionStatusFrame = Tk.Frame(self.statusFrame, 
				bg = self.background, padx = 10)

			self.connectionStatusFrame.pack(side = Tk.RIGHT)

			# BROADCAST DISPLAY:

			# Frame:
			self.broadcastDisplayFrame = Tk.Frame(self.connectionStatusFrame, 
				bg = self.background, padx = 5)
			self.broadcastDisplayFrame.pack(side = Tk.LEFT)

			# Label:
			self.broadcastDisplayLabel = Tk.Label(self.broadcastDisplayFrame, 
				text = "Broadcast: ", background = self.background,
				fg = self.foreground)
			self.broadcastDisplayLabel.pack(side = Tk.LEFT)

			# Display:
			self.broadcastDisplay = Tk.Frame(self.broadcastDisplayFrame, 
				background = "#510000", relief = Tk.SUNKEN, borderwidth = 1,
				width = 10, height = 10)
			self.broadcastDisplay.pack(side = Tk.RIGHT)

			# Status sentinel and colors:
			self.broadcastStatus = RED
			self.broadcastRED = self.displayRED
			self.broadcastGREEN1 = self.displayGREEN1
			self.broadcastGREEN2 = self.displayGREEN2

			# LISTENER DISPLAY:

			# Frame:
			self.listenerDisplayFrame = Tk.Frame(self.connectionStatusFrame, 
				bg = self.background, padx = 5)
			self.listenerDisplayFrame.pack(side = Tk.LEFT)

			# Label:
			self.listenerDisplayLabel = Tk.Label(self.listenerDisplayFrame, 
				text = "Listener: ", background = self.background,
				fg = self.foreground)
			self.listenerDisplayLabel.pack(side = Tk.LEFT)

			# Display:
			self.listenerDisplay = Tk.Frame(self.listenerDisplayFrame, 
				background = "#510000", relief = Tk.SUNKEN, borderwidth = 1,
				width = 10, height = 10)
			self.listenerDisplay.pack(side = Tk.RIGHT)

			# Status sentinel and colors:
			self.listenerStatus = RED
			self.listenerRED = self.displayRED
			self.listenerGREEN = self.displayGREEN1
			self.listenerBLUE = self.displayBLUE
			
			
			# Initialize SlaveDisplay:
			self.slaveDisplay = sd.SlaveDisplay(
				self.slaveDisplayFrame, 
				self.connectSlave,
				self.disconnectSlave,
				self.rebootSlave,
				self.printMain)
			
			init_pbar["value"] = 24
			# DRAW WINDOW = = = = = = = = = = = = = = = = = = = = = = = = = = = = = 
			
			# Finally show window:
			#print "Calculating sizes... [1/6]"
			self.master.update_idletasks() # Required to set minimum size	
			self.pack(fill = Tk.BOTH, expand = True)
			
			# PACK -----------------------------------------------------------------
			# Center starting place:
			#                         Y-place
			#                      X-place  |       
			#                    Height  |  |
			#                  Width  |  |  |
			#                      |  |  |  |
			
			self.master.geometry('+%d+%d' % ( \
				(self.master.winfo_screenwidth()/5),
				(self.master.winfo_screenheight()/8)
				)
			)
			#print "Calculating sizes... [2/6]"
			self.master.update_idletasks() # Required to set minimum size	
			self.printMain("Fan Club MkII Interface initialized", "G")
			
			# Activate resizing:
			self.master.resizable(True, True)
			
			"""
			self.master.geometry('%dx%d+%d+%d' % (960, 630, \
				(self.master.winfo_screenwidth()/5),      \
				(self.master.winfo_screenheight()/8)        \
				)                                           \
			)
			self.master.update() # Required to set minimum size	
			"""

			init_pbar["value"] = 28
			# DETERMINE MINIMUM SIZES:
			self.master.withdraw()
			# When only the essential "bars" are packed:
			#print "Calculating sizes... [3/6]"
			self.master.update_idletasks() # Required to set minimum size	
			self.masterMinimumSize = \
				(self.master.winfo_width(),self.master.winfo_height())

			init_pbar["value"] = 32
			# When only the slave display is packed:
			self._slaveDisplayToggle(False)
			#print "Calculating sizes... [4/6]"
			self.master.update_idletasks() # Required to set minimum size	
			self.slaveDisplayMinimumSize = \
				(self.master.winfo_width(),self.master.winfo_height())
			
			init_pbar["value"] = 36
			# When the slave list is packed:	
			self.slaveDisplayToggleVar.set(False)
			self._slaveDisplayToggle(False)
			self.slaveListToggleVar.set(True)
			self._slaveListToggle(False)
			
			#print "Calculating sizes... [5/6]"
			self.master.update_idletasks() # Required to set minimum size	
			self.slaveListMinimumSize = \
				(self.master.winfo_width(),self.master.winfo_height())

			init_pbar["value"] = 40
			# When the terminal is packed:	
			self.slaveDisplayToggleVar.set(False)
			self._slaveDisplayToggle(False)
			self.slaveListToggleVar.set(False)
			self._slaveListToggle(False)
			self.terminalToggleVar.set(True)
			self._terminalToggle(False)
			
			#print "Calculating sizes... [5/6]"
			self.master.update_idletasks() # Required to set minimum size	
			self.terminalMinimumSize = \
				(self.master.winfo_width(),self.master.winfo_height())
			
			# Pack widgets after determining minimum size:
			self.slaveDisplayToggleVar.set(True)
			self._slaveDisplayToggle()
			self.slaveListToggleVar.set(True)
			self._slaveListToggle()
			self.terminalToggleVar.set(False)
			self._terminalToggle()
			init_pbar["value"] = 50
			#print "Calculating sizes... [6/6]"
			self.master.update_idletasks()
			self.master.deiconify()

		
			# INITIALIZATION STEP 2: BUILD AND START ARCHIVER AND PRINTER ##########

			init_pbar["value"] = 51
			# Initialize Archiver --------------------------------------------------
			self.printMain("Initializing Archiver...")
			self.archiver = ac.FCArchiver() 
			self.printMain("Archiver initialized", "G")
		
			# Update SlaveDisplay maxFans:
			self.slaveDisplay.setMaxFans(self.archiver.get(ac.maxFans))

			# Initialize Slave data structure --------------------------------------
			self.slaveContainers = np.empty(0, dtype = object)

			# Initialize Printer ---------------------------------------------------
			self.printMain("Initializing Printer...")
			self.printer = pt.FCPrinter(
				queueSize = self.archiver.get(ac.printerQueueSize),
				fanMode = self.archiver.get(ac.fanMode)
				)
			self.printMain("Printer Initialized", "G")


			# INITIALIZATION STEP 4: BUILD AND START COMMUNICATOR ##################
			# Initialize Communicator ----------------------------------------------
			self.printMain("Initializing Communicator...")
			self.communicator = FCCommunicator.FCCommunicator(
				savedSlaves = self.archiver.get(ac.savedSlaves),
				mainQueueSize = self.archiver.get(ac.mainQueueSize),
				broadcastPeriodS = self.archiver.get(ac.broadcastPeriodS),
				periodMS = self.archiver.get(ac.periodMS),
				periodS = self.archiver.get(ac.periodS),
				broadcastPort = self.archiver.get(ac.broadcastPort),
				passcode = self.archiver.get(ac.passcode),
				misoQueueSize = self.archiver.get(ac.misoQueueSize),
				maxTimeouts = self.archiver.get(ac.maxTimeouts),
				maxLength = self.archiver.get(ac.maxLength),
				defaultModuleDimensions = self.archiver.get(ac.defaultModuleDimensions),
				defaultModuleAssignment = self.archiver.get(ac.defaultModuleAssignment),
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
				pinout = self.archiver.get(ac.defaultPinout)
				)
			
			self.master.protocol("WM_DELETE_WINDOW", 
				self._deactivationRoutine)
			
			self.printMain("Communicator initialized", "G")
			
			init_pbar["value"] = 55
			# START UPDATE ROUTINES = = = = = = = = = = = = = = = = = = = = = =
			self._mainPrinterRoutine()
			self.ableToPrint = True # Errors can now be printed using the 
									# standard GUI
			
			self._newSlaveChecker()
			self._broadcastThreadChecker()
			self._listenerThreadChecker()

			init_pbar["value"] = 56
			init_lw.destroy()
			
			# Focus on the main window:
			self.master.lift()
				

		except Exception as e: # Print uncaught exceptions
			
			if not self.ableToPrint:
				tkMessageBox.showerror("Warning: Uncaught exception in "\
					"Terminal printer routine: \"{}\"".\
					format(traceback.format_exc()), "E")
		
		# End FCInterface Constructor ==========================================

## UPDATE ROUTINES # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

	def _mainPrinterRoutine(self): # ===========================================
		# ABOUT: Keep main terminal window updated w/ Communicator output. To be
		
		try:
			if self.terminalVar.get() == 0:
				pass

			else: 

				# COMMUNICATOR QUEUE

				try: # NOTE: Use try/finally to guarantee lock release.

					# Fetch item from Communicator queue:
					output, tag = self.printer.mainQueue.get_nowait()

					# If there is an item, print it (otherwise, Empty exception is
					# raised and handled)
					
					# Check for debug tag:
					if tag is "D" and self.debugVar.get() == 0:
						# Do not print if the debug variable is set to 0
						pass

					else:

						# Switch focus to this tab in case of errors of warnings:
						if tag is "E":
							self.terminalToggleVar.set(True)
							self._terminalToggle()

						self.mainTText.config(state = Tk.NORMAL)
							# Must change state to add text.
						self.mainTText.insert(Tk.END, output + "\n", tag)
						self.mainTText.config(state = Tk.DISABLED)

						# Check for auto scroll:
						if self.autoscrollVar.get() == 1:
							self.mainTText.see("end")

				except Queue.Empty:
					# If there is nothing to print, try again.
					pass

				# PRINTER QUEUE

				try: # NOTE: Use try/finally to guarantee lock release.

					# Fetch item from Communicator queue:
					output, tag = self.communicator.mainQueue.get_nowait()
					# If there is an item, print it (otherwise, Empty exception is
					# raised and handled)
					
					# Check for debug tag:
					if tag is "D" and self.debugVar.get() == 0:
						# Do not print if the debug variable is set to 0
						pass

					else:

						# Switch focus to this tab in case of errors of warnings:
						if tag is "E":
							self.terminalToggleVar.set(True)
							self._terminalToggle()

						self.mainTText.config(state = Tk.NORMAL)
							# Must change state to add text.
						self.mainTText.insert(Tk.END, output + "\n", tag)
						self.mainTText.config(state = Tk.DISABLED)

						# Check for auto scroll:
						if self.autoscrollVar.get() == 1:
							self.mainTText.see("end")

				except Queue.Empty:
					# If there is nothing to print, try again.
					pass

			self.mainTText.after(100, self._mainPrinterRoutine)
	
		except Exception as e: # Print uncaught exceptions
			tkMessageBox.showerror("Warning: Uncaught exception in Terminal "\
				"printer routine: \"{}\"".\
				format(traceback.format_exc()), "E")

			self.mainTText.after(100, self._mainPrinterRoutine)
		# End _mainPrintRoutine ================================================

	def _newSlaveChecker(self): # ===================================
		# ABOUT: Check periodically for the addition of new Slaves.
		
		# Check for new Slaves:
		fetched = self.communicator.getNewSlave()
		try:
			if fetched is None:
				# Nothing to do here
				pass
			else:
				# Slave fetched. Add it to the interface:
				
				# Create new SlaveContainer:
				newSlaveContainer = \
					sc.SlaveContainer(
						name = fetched[0][0],
						mac = fetched[0][1],
						status = fetched[0][2],
						maxFans = fetched[0][3],
						maxRPM = self.archiver.get(ac.maxRPM),
						activeFans = fetched[0][4],
						ip = fetched[0][5],
						misoMethod = fetched[0][6],
						mosiMethod = fetched[0][7],
						master = self,
						periodMS = self.archiver.get(ac.periodMS),
						slaveListIID =	self.slaveList.insert(
							'', 'end', 
							values = (
							fetched[0][8] + 1,
							fetched[0][0], # name 
							fetched[0][1], # MAC 
							sv.translate(fetched[0][2]), # Status as str
							fetched[0][5],	 # IP as str
							fetched[0][4], # Active fans as int 
							fetched[0][12]),# Version
							tag = sv.translate(fetched[0][2], True)),
										#        \------/ Status (int)
						index = fetched[0][8],
						coordinates = fetched[0][9],
						moduleDimensions = fetched[0][10],
						moduleAssignment = fetched[0][11],
						version = fetched[0][12]
					)
				
				# Add to SlaveContainer array:
				self.slaveContainers = \
					np.concatenate((
						self.slaveContainers, 
						(newSlaveContainer,)
						))

				# Add to Printer's list:
				self.printer.add(
					mac = fetched[0][1], # MAC
					index = fetched[0][8], # Index
					activeFans = fetched[0][4], # Active fans
				)
			
			# Schedule next call -----------------------------------------------
			if fetched is not None and fetched[1]:
				self.after(
					self.archiver.get(ac.periodMS)/10, self._newSlaveChecker)
			else:
				self.after(
					self.archiver.get(ac.periodMS)/10, self._newSlaveChecker)

		except Exception as e: # Print uncaught exceptions
			self.printMain("[NS] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")
			self.main.after(self.archiver.get(ac.periodMS), self._newSlaveChecker)
		# End _newSlaveChecker =================================================

	def _broadcastThreadChecker(self): # =======================================
		# ABOUT: Check whether the communicator's broadcast thread is alive and
		# update the corresponding GUI display. 
		# NOTE: This is a "periodic" method, in that it will schedule a future
		# call to itself using Tkinter's "after" method.

		# Check thread:
		if self.communicator.isBroadcastThreadAlive():
			# Use update method to alternate between greens:
			self.broadcastDisplayUpdate()	
		
		else:
			# Use update method to set red color:
			self.broadcastDisplayUpdate("R")

		# Schedule future call:
		self.after(self.archiver.get(ac.broadcastPeriodMS), 
			self._broadcastThreadChecker)

		# End _broadcastThreadChecker ==========================================

	def _listenerThreadChecker(self): # ========================================
		# ABOUT: Check whether the communicator's listener thread is alive and
		# update the corresponding GUI display. 
		# NOTE: This is a "periodic" method, in that it will schedule a future
		# call to itself using Tkinter's "after" method.

		# Check thread:
		if self.communicator.isListenerThreadAlive():
			# Use update method to alternate between greens:
			self.listenerDisplayUpdate()	
		
		else:
			# Use update method to set red color:
			self.listenerDisplayUpdate("R")

		# Schedule future call:
		self.after(1000, self._listenerThreadChecker)

		# End _listenerThreadChecker ===========================================

	def listenerDisplayUpdate(self, code = "G"):
		# ABOUT: Update listenerDisplay widget.
		# PARAMETERS:
		# - code: str, representing the new status of the widget. Defaults to 
		# "G" to alternate between green tones. Valid codes are "R", "B" and "G"
		# defined in FCInterface.py.

		# Check given code:
		if code == "G" and self.listenerStatus != GREEN:
			# Set status to green:
			self.listenerDisplay.config(background = self.listenerGREEN)
			self.listenerStatus = GREEN

		elif code == "G":
			# Set status to alternate green:
			self.listenerDisplay.config(background = self.broadcastGREEN2)
			self.listenerStatus = GREEN2
			

		elif code == "R" and self.listenerStatus != RED:
			# Switch to red:
			self.listenerDisplay.config(background = self.listenerRED)

		elif code == "B":
			# Blue is used to indicate the reception of a message.

			self.listenerDisplay.config(background = self.listenerBLUE)
			self.listenerStatus = BLUE

		elif not code in ["R", "G", "B"]:
			# Bad value. Raise exception:
			raise ValueError("Bad listener status code \"{}\" \
				expected GREEN or RED".format(code))

	def broadcastDisplayUpdate(self, code = "G"):
		# ABOUT: Update broadcastDisplay widget.
		# PARAMETERS:
		# - code: str, representing the new status of the widget. Defaults to 
		# "G" to alternate between green tones. Valid codes are "R", "B" and "G"
		# defined in FCInterface.py.

		# Check given code:
		if code == "G":
			# Alternate between colors
			if self.broadcastStatus == GREEN:
				# Use alternate green:
				self.broadcastDisplay.config(background = self.broadcastGREEN2)
				self.broadcastStatus = GREEN2

			else:
				# Use first green:
				self.broadcastDisplay.config(background = self.broadcastGREEN1)
				self.broadcastStatus = GREEN

		elif code == "R" and self.broadcastStatus != RED:
			# Switch to red:
			self.broadcastDisplay.config(background = self.broadcastRED)

		elif not code in ["R", "G"]:
			# Bad value. Raise exception:
			raise ValueError("Bad broadcast status code \"{}\" \
				expected GREEN or RED".format(code))

## AUXILIARY METHODS # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

	def printMain(self, output, tag = "S"): # ==================================
		# ABOUT: Print to main terminal window in a thread-safe manner.
		# PARAMETERS:
		# - output: str, text to print.
		# - tag: str, single character representing type of text to be prin-
		#	ted. Can be "S" for "Standard," "W" for "Warning,"  "E" for Er-
		#	ror or "G" for "Green". Defaults to "S"

		if DEBUG:
			print "[DEBUG] " + output
	
		if self.terminalVar.get() == 0:
			return

		self.mainTLock.acquire()

		try: # NOTE: Use try/finally to guarantee lock release.

			# Check for debug tag:
			if tag is "D" and self.debugVar.get() == 0:
				# Do not print if the debug variable is set to 0
				return

			# Switch focus to this tab in case of errors of warnings:
			if tag is "E":
				self.terminalToggleVar.set(True)
				self._terminalToggle()

			self.mainTText.config(state = Tk.NORMAL)
				# Must change state to add text.
			self.mainTText.insert(Tk.END, output + "\n", tag)
			self.mainTText.config(state = Tk.DISABLED)

			# Check for auto scroll:
			if self.autoscrollVar.get() == 1:
				self.mainTText.see("end")

		finally:
			self.mainTLock.acquire(False)
			self.mainTLock.release()

		# End printMain ========================================================

	def _gridButtonRoutine(self): # ============================================
		# ABOUT: To be called by the grid button. Hides and shows grid in popup
		# window.
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
						self.slaveContainers,
						self.archiver.get(ac.maxRPM)
						)

				self.gridOuterFrame.bind("<Button-1>", _expand)
				self.gridOuterFrame.focus_set()

				self.grid = mg.MainGrid(
					self.gridOuterFrame,
					self.archiver.get(ac.dimensions)[0],
					self.archiver.get(ac.dimensions)[1],
					600/self.archiver.get(ac.dimensions)[0],
					self.slaveContainers,
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
			self.printMain("[_gridButtonRoutine] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")

		# End gridButtonRoutine ================================================

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
			self.printMain("[_gridButtonRoutine] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")
		# End _gridDeactivationRoutine =========================================

	def _printTimerRoutine(self): # ============================================
		# ABOUT: Update the Printer timer periodically for as long as it is
		# active. This method is meant to be called by whatever component acti-
		# vates the Printer (i.e starts printing).

		# Check Printer status:
		if not self.printTimerStopFlag:
			# Update timer label
			self.printTimerSeconds += 1

			if self.printTimerSeconds >= 60:
				self.printTimerSeconds = 0
				self.printTimerMinutes += 1

				if self.printTimerMinutes >= 60:
					self.printTimerMinutes = 0
					self.printTimerHours += 1
					
					if self.printTimerHours >= 99:
						self.printTimerHours = 99
			
			self.printTimerVar.set("{:02d}:{:02d}:{:02d}s".format(
				self.printTimerHours,
				self.printTimerMinutes,
				self.printTimerSeconds))

			self.after(1000, self._printTimerRoutine)

		else:
			# Reset timer label and end chain of calls:
			self.printTimerSeconds = 0
			self.printTimerMinutes = 0
			self.printTimerHours = 0
			self.printTimerVar.set("00:00:00s")
			return


		# End _printTimerRoutine ===============================================

	def _printTargetButtonRoutine(self): # =====================================
		# ABOUT: To be used by file name button. 
		# Sets file name and stops Printer.
		try:
			
			# Proceed in accordance w/ Printer status:
			if self.printer.getStatus() == pt.OFF:
				# If the printer is off, choose a file name.

				# Disable print button while choosing file:
				self.printStartStopButton.config(state = Tk.DISABLED)

				self.printTargetVar.set(tkFileDialog.asksaveasfilename(
					initialdir = os.getcwd(), # Get current working directory
					title = "Choose file",
					filetypes = (("Text files","*.txt"),("CSV files", "*.csv"),
						("All files","*.*"))
					))
				
				# Set the visibility to the right end of the file name:
				self.printTargetEntry.xview_moveto(1)

			elif self.printer.getStatus() is pt.ON:
					
				raise RuntimeError("Cannot use target file specifier while "\
					"printing")
			else:
				# Unrecognized printer status (wot)
				raise RuntimeError("Unrecognized Printer status {} (wot)".\
					format(self.printer.getStatus()))
		except Exception as e:
			self.printMain("[printTargetButton] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")

		# End _printTargetButtonRoutine ========================================

	def _printButtonRoutine(self): # ===========================================
		# ABOUT: To be used by Printer Start/Stop button. Starts and stops 
		# Printer.
		try:
			# Deactivate print target button to prevent timing conflicts:
			self.printTargetButton.config(state = Tk.DISABLED) 
			self.printTargetEntry.config(state=Tk.DISABLED)

			# Check state of printer:
			if self.printer.getStatus() == pt.OFF:
				# If the printer is not active, activate it:
				
				# Fetch file name:
				fetchedFileName = self.printTargetVar.get()

				# Validate statuses:
				if self.printTargetStatus in (EMPTY, BADEXT):
					raise RuntimeError("Cannot print to file with target file "\
						"status code {}".format(self.printTargetStatus))

				elif self.printTargetStatus in (NODOT, NODOT_REPEATED):
					# Add extension:
					fetchedFileName += ".txt"

				# Start printer:
				self.printer.start(
					fileName = fetchedFileName,
					profileName = self.archiver.get(ac.name),
					maxFans = self.archiver.get(ac.maxFans),
					periodS = self.archiver.get(ac.periodS)
				)

				# Modify buttons upon successful printer startup:

				# Check if the change was successful:
				if self.printer.getStatus() == pt.ON:
					self.printStartStopButton.config(text = "Stop Recording")
					
					# Start timer:
					self.printTimerStopFlag = False
					self._printTimerRoutine()
				else:
					# Reactivate printTargetButton (upon init. failure)
					self.printTargetButton.config(state = Tk.NORMAL)

			elif self.printer.getStatus() == pt.ON:
				# If the printer is active, shut it down
				
				# Deactivate Printer-related components while shutdown completes:
				self.printTargetButton.config(state = Tk.DISABLED)
				self.printStartStopButton.config(state = Tk.DISABLED)
				self.printTargetEntry.config(state = Tk.DISABLED)
				self.printTargetFeedbackLabel.config(text = "Stopping...")
				self.printTimerLabel.config(state = Tk.DISABLED)
				self.printTimerStopFlag = True

				# Stop Printer. Use short-lived thread to keep GUI responsive:
				temp = threading.Thread(target = self.printer.stop)
				temp.setDaemon(True)
				temp.start() # Will end on its own

				# Start "check" routine to restore interface once Printer is
				# done shutting down:
				self._printStopRoutine()
					
			else: 
				# Unrecognized printer status (Wot)
				raise RuntimeError("Unrecognized Printer status {} (wot)".\
					format(self.printer.getStatus()))
			
		except Exception as e:
			self.printMain("[printButton] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")

		# End _printButtonRoutine ==============================================

	def _printStopRoutine(self): # ===========================================
		# ABOUT: Schedules itself for future calls until the Printer module is
		# done terminating. When the Printer module is done, restores buttons
		# and fields.

		# Check Printer status:
		if self.printer.getStatus() == pt.OFF:
			# Restore buttons 
			self.printStartStopButton.config(text = "Start Recording")
			self.printTargetEntry.config(state = Tk.NORMAL)
			self.printTargetButton.config(state = Tk.NORMAL)
			self.printTimerLabel.config(state = Tk.NORMAL)
			self.printTargetStatus = RESTORE
				# "Modify" targetFileVar to fire its trace callback:
			self.printTargetVar.set(self.printTargetVar.get())
			

		else:
			# Schedule future call to check again:
			self.after(200, self._printStopRoutine)

		# End _printerStopRoutine ==============================================

	def _validateN(self, newCharacter, textBeforeCall, action): # ==============
		# ABOUT: To be used by TkInter to validate text in "Send" Entry.
		if action == '0':
			return True
		elif self.selectedCommand.get() == "Set Duty Cycle" and \
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

		elif self.selectedCommand.get() == "Chase RPM" and newCharacter \
			in '0123456789' and len(textBeforeCall) < 5:
			return True

		else:
			return False

	def _changeCommandMenu(self, newValue): # ==================================
		# ABOUT: Handle changes in commandMenu

		# Erase text:
		self.commandEntry.delete(0, Tk.END)

		# Check value and update command frame in accordance:
		if newValue == "Set Duty Cycle":
			self.commandLabelText.set("  DC: ")

		elif newValue == "Chase RPM":
			self.commandLabelText.set("RPM: ")

	def _terminalToggle(self, updateMinSize = True): # =========================
		# ABOUT: Hide and show the terminal

		# Update geometry:
		if updateMinSize:
			self._updateMinSize()
		
		# Check variable:
		if self.terminalToggleVar.get():
			# Build terminal:
			self.terminalFrame.pack(fill = Tk.BOTH, expand = False)
			self.terminalVar.set(1)
		else:
			# Hide terminal:
			self.terminalFrame.pack_forget()
			self.terminalContainerFrame.configure(height = 1)

	def _slaveListToggle(self, updateMinSize = True): # ========================
		# ABOUT: Hide and show the Slave list

		# Update geometry:
		if updateMinSize:
			self._updateMinSize()

		# Check variable:
		if self.slaveListToggleVar.get():
			# Build slaveList:
			self.slaveListFrame.pack(fill = Tk.BOTH, expand = True)
		else:
			# Hide slaveList:
			self.slaveListFrame.pack_forget()
			self.slaveListContainer.configure(height = 1)

	def _slaveDisplayToggle(self, updateMinSize = True): # =====================
		# ABOUT: Hide and show the Slave list

		# Update geometry:
		if updateMinSize:
			self._updateMinSize()

		# Check variable:
		if self.slaveDisplayToggleVar.get():
			self.slaveDisplay.pack()
			self.slaveDisplay.isPacked = True
		else:
			self.slaveDisplay.pack_forget()
			self.slaveDisplayFrame.configure(height = 1)
			self.slaveDisplay.isPacked = False

	def _updateMinSize(self): # =================================================
		# ABOUT: Check whether the current window size is enough for the current
		# widget configuration and update geometry and minimum size accordingly.
		# (Relies on the minimums set during configuration.)

		# Determine required minimum size:
			# NOTE: Add the minimum size requirement of each currently activated
			# widget.
		
		baseReqY = self.masterMinimumSize[1]
		baseReqX = self.masterMinimumSize[0]
		totalReqY = baseReqY
		totalReqX = baseReqX
		

		if self.slaveDisplayToggleVar.get():
			totalReqY += self.slaveDisplayMinimumSize[1]
			totalReqX += self.slaveDisplayMinimumSize[0] - baseReqX
		if self.slaveListToggleVar.get():
			totalReqY += self.slaveListMinimumSize[1] - baseReqY
		if self.terminalToggleVar.get():
			totalReqY += self.terminalMinimumSize[1] - baseReqY


		self.master.update_idletasks()
		# Update minimum size:
		self.master.minsize(
			totalReqX,
			totalReqY
		)

		# Check against current size:
		if self.master.winfo_width() < self.masterMinimumSize[0] or\
			self.master.winfo_height() < totalReqY:
			self.master.update_idletasks()
			# Reset geometry to allow for automatic window resizing:
			self.winfo_toplevel().wm_geometry("")
		return

	def _shutdownButton(self): # ===============================================
		# ABOUT: To be bound to shutdownButton

		self.printMain("Shutting down fan array", "W")

		this.communicator.sendReboot();

	def _disconnectAllButton(self): # ===============================================
		# ABOUT: To be bound to disconnectAllButton

		self.printMain("Shutting down fan array", "W")

		this.communicator.sendDisconnect();

	def _slaveListMethod(self, event): # =======================================
		# ABOUT: Handle selections on SlaveList
	
		# Ensure the list is not empty:
		if self.totalSlaves == 0:
			# If there are no Slaves, there is nothing to select
			return

		currentSelection = self.slaveList.item(
			self.slaveList.selection()[0],"values")[0]

		if self.oldSelection != currentSelection:
			self.slaveDisplay.setTarget(
				self.slaveContainers[int(currentSelection) - 1])
				#                                          \--/
				#                 Compensate displacement <-/
			self.oldSelection = currentSelection

		if not self.slaveDisplay.isPacked:
			self.slaveDisplay.pack()
			self.slaveDisplayToggleVar.set(True)
			self.slaveDisplay.isPacked = True
	
	def _send(self): # =========================================================
		# ABOUT: Send a message to the MOSI queue of applicable Slaves
		# Loop over each Slave unit and check whether it has any selected fans:
			# NOTE: No need to check whether these are connected. This is opera-
			# tionally equivalent to them having no selected fans.
		try:
			# Check if there is a command to send:
			if self.commandEntry.get() == "":
				# Ignore this button press:
				return
	
			# Assemble the shared side of the command to be sent: ------------
			#       [INDEX]|S|command~arg~fans
			#       \-----------/\----------/\--/
			#              |            |      |
			#              |            |     Added here. Specific of each Slave
			#              |          Added here. Common to all selected Slaves
			#             Added by Communicator

			# Get command: 
				# NOTE: Validity of command argument entered by user is ensured by 
				# the widget's validation handler. 
				# See validateN() method.
			
			commandKeyword = ""

			if self.selectedCommand.get() == "Set Duty Cycle":
				commandKeyword += "S|D:{}".format(float(
					self.commandEntry.get())/100.0)
			elif self.selectedCommand.get() == "Chase RPM":
				commandKeyword += "S|C:{}".format(self.commandEntry.get())

			else:
				# Unrecognized command (wat):
				raise ValueError(
					"ERROR: UNRECOGNIZED COMMAND IN COMMAND MENU: {}".format(
						commandMenu.get()))	
			
			# Set sentinel for whether this message was sent:
			sent = False

			for slaveContainer in self.slaveContainers:

				if slaveContainer.hasSelected():
					# If it has at least one fan selected, add this to its queue:
					try:
						command = "{}:{}".format(
							commandKeyword, \
							slaveContainer.getSelection())
						slaveContainer.mosiMethod(command, False)
						# Deselect fans if instructed to do so:
						if not self.keepSelectionVar.get():
							slaveContainer.select(None, False)
						# Update sentinel:
						sent = True
						
					except Queue.Full:
						self.printMain( "[{}] "\
							"Warning: Outgoing command Queue full. "\
							"Could not send message".\
							format(slaveContainer.index + 1), "E")

			# Check sentinel:
			if sent:
				# Erase text:
				self.commandEntry.delete(0, Tk.END)
				
		except Exception as e:
			self.printMain("[_send()] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")

	def connectSlave(self, targetIndex): # =====================================
		# ABOUT: Tell Communicator to connect to specified Slave.

		# NOTE: At least for now, this method is, no more than a wrapper around
		# FCCommunicator's add() method...
		
		self.communicator.add(targetIndex)

		# End connectSlave =====================================================
	
	def disconnectSlave(self, targetIndex): # ==================================
		# ABOUT: Tell Communicator to disconnect specified Slave.

		# NOTE: At least for now, this method is, no more than a wrapper around
		# FCCommunicator's add() method...
		
		self.communicator.disconnectSlave(targetIndex)

		# End disconnectSlave ==================================================
	
	def rebootSlave(self, targetIndex): # ======================================
		# ABOUT: Tell Communicator to connect to specified Slave.

		# NOTE: At least for now, this method is, no more than a wrapper around
		# FCCommunicator's add() method...
		
		self.communicator.rebootSlave(targetIndex)

		# End rebootSlave ======================================================

	def _connectAllSlaves(self): # =============================================
		# ABOUT: Connect to all AVAILABLE Slaves, if any.

		# Loop over Slaves and add all AVAILABLE ones:
		for slaveContainer in self.slaveContainers:
			if slaveContainer.status == sv.AVAILABLE:
				self.communicator.add(slaveContainer.index)

		# End addAllSlaves =====================================================

	def _deactivationRoutine(self):
		# ABOUT: To be executed upon exit

		# Reboot all Slaves:
		self.communicator.sendDisconnect()

		# Close:
		self.master.quit()

		# End _deactivationRoutine =============================================
	
	def _fileNameEntryCheck(self, *args): # ====================================
		# ABOUT: Validate the file name entered.
		# Get file name:
		prospectiveFileName = self.printTargetVar.get()
		# Set sentinel:
		normal = True
	
		# Check file name:
		if prospectiveFileName == '' and self.printTargetStatus != EMPTY:
			#                           \-----------------------------/
			#								Avoid redundant changes
			# Can't print:
			self.printStartStopButton.config(state = Tk.DISABLED)
			self.printTargetEntry.config(bg = self.entryRedBG)
			self.printTargetFeedbackLabel.config(text = "(No filename)")
			self.printTargetStatus = EMPTY

			# Done
			return

		elif '.' not in prospectiveFileName:
			# No extension. Assume .txt and warn:
			normal = False
			
			if self.printTargetStatus != NODOT:

				self.printTargetEntry.config(bg = self.entryWhiteBG)
				self.printTargetFeedbackLabel.config(text = '(.txt assumed)')
				self.printStartStopButton.config(state = Tk.NORMAL)
				prospectiveFileName += ".txt"

				self.printTargetStatus = NODOT

		elif prospectiveFileName.split('.')[-1] == '':
			# Invalid extension:
			normal = False

			if self.printTargetStatus != BADEXT:

				self.printStartStopButton.config(state = Tk.DISABLED)
				self.printTargetEntry.config(bg = self.entryRedBG)
				self.printTargetFeedbackLabel.config(text = "(Bad extension)")

				self.printTargetStatus = BADEXT

		# Check for repetition
		if os.path.isfile(prospectiveFileName) and \
			self.printTargetStatus != REPEATED:
			# Change color and warn:
			self.printTargetEntry.config(bg = self.entryOrangeBG)
			self.printTargetFeedbackLabel.config(text = 'FILE EXISTS')
			self.printStartStopButton.config(state = Tk.NORMAL)
			
			if self.printTargetStatus == NODOT:
				self.printTargetStatus = NODOT_REPEATED
			else:
				self.printTargetStatus = REPEATED

		elif normal and self.printTargetStatus != NORMAL:
			# If this block of code is reached, then the prospective filename is
			# - Not empty
			# - Not missing an extension, and
			# - Not repeated
		
			# Therefore, mark it as NORMAL:
			self.printTargetEntry.config(bg = self.entryWhiteBG)
			self.printTargetFeedbackLabel.config(text = '')
			self.printStartStopButton.config(state = Tk.NORMAL)

			self.printTargetStatus = NORMAL

		# End _fileNameEntryCheck ==============================================

## INTERFACE METHODS # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

	def selectAllSlaves(self): # ===============================================
		# ABOUT: To be bound to the "Select All" button (selects all fans in all
		# Slaves)
		
		for slaveContainer in self.slaveContainers:
			slaveContainer.selectAll()
		# End selectAllSlaves ==================================================

	def deselectAllSlaves(self): # =============================================
		# ABOUT: To be bound to the "Deselect All" button (deselects all fans 
		# in all Slaves)
		
		for slaveContainer in self.slaveContainers:
			slaveContainer.deselectAll()
		
		# End deselectAllSlaves ================================================
