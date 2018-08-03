###############################################################################
## Project: Fan Club Mark II "Master" # File: FCCControlBar.py                ##
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
Simple controls for FCCommunicator.

"""
################################################################################


## DEPENDENCIES ################################################################

# GUI:
#from mttkinter import mtTkinter as Tk
import tkinter as Tk
import tkinter.messagebox
import tkinter.filedialog 
import tkinter.font
import tkinter.ttk # "Notebooks"

# System:
import os # Get current working directory & check file names & sizes
import sys # Exception handling
import inspect # get line number for debugging
import traceback
import shutil as sh

# STD:
import itertools as it # Chaining ranges


# FCMkII:
import FCSlave as sv
import FCCommunicator as cm
import auxiliary.errorPopup as ep
import FCMainWindow as mw

## AUXILIARY DEFINITIONS #######################################################

# Menu items:
SET_DC = "DC%"
SET_RPM = "RPM"

# Bootloader statuses:
FLASHING = 1
NOT_FLASHING = 0

## CLASS DEFINITION ############################################################

class FCCControlBar(Tk.Frame, object):

	def __init__(
		self, 
		master, 
		maxFans, 
		maxRPM,
		periodMS,
		selectionSource, 
		commandQueue, 
		printQueue
		): # ===================================================================

		self.canPrint = False

		try:

			# CONFIGURE --------------------------------------------------------
			self.maxFans = maxFans
			self.maxRPM = maxRPM
			self.periodMS = periodMS
			self.mininumIntervalMS = 2*self.periodMS
			self.selectionSource = selectionSource
			self.commandQueue = commandQueue
			self.printQueue = printQueue
			self.canPrint = True

			self.background = "#d3d3d3"
			self.foreground = "black"

			super(FCCControlBar, self).__init__(
				master,
				bg = self.background
				)

			self.status = None

			""" ----------------------------------------------------------------
			Scratch...
			 __________________________________________________________________
			|Send: [v| Connect ]   To: [v| All (Broadcast) ]  [Send]           |
			 ------------------------------------------------------------------
			---------------------------------------------------------------- """

			# BUILD INTERFACE --------------------------------------------------
		
			self.activeWidgets = []

			self.notebook = tkinter.ttk.Notebook(
				self	
			)

			self.notebook.enable_traversal()

			self.notebook.pack(side = Tk.LEFT, fill = Tk.X, expand = True)

			# NETWORK CONTROL ..................................................
			self.networkControlFrame = Tk.Frame(
				None,
				background = self.background
			)
			self.networkControlFrame.pack(fill = Tk.BOTH, expand = True)

			self.notebook.add(
				self.networkControlFrame,
				text = "Network Control"
			)


			# Main Label .......................................................
			"""
			self.mainLabel = Tk.Label(
				self,
				text = "Network Control:",
				font = ('TkStandardFont', '13'),
				bg = self.background,
				fg = self.foreground,
			)
			self.mainLabel.pack(side = Tk.LEFT)
			"""
			# Target Menu ......................................................

			# Label:
			self.networkTargetMenuLabel = Tk.Label(
				self.networkControlFrame,
				bg = self.background,
				fg = self.foreground,
				text = "Target: "
			)

			self.networkTargetMenuLabel.pack(side = Tk.LEFT)

			# Menu:

			self.selectedNetworkTarget = Tk.StringVar()
			self.selectedNetworkTarget.set("All")
			self.networkTargetMenu = Tk.OptionMenu(self.networkControlFrame, 
				self.selectedNetworkTarget,
				"Selected", 
				"All"
			)

			self.networkTargetMenu.pack(side = Tk.LEFT)

			self.networkTargetMenu.config(
				width = 10,
				background = self.background,
				highlightbackground = self.background,
				foreground = self.foreground
			)

			self.activeWidgets.append(self.networkTargetMenu)
			
			"""
			# Channel Menu ......................................................

			# Label:
			self.channelMenuLabel = Tk.Label(
				self.networkControlFrame,
				bg = self.background,
				fg = self.foreground,
				text = "Channel: "
			)

			self.channelMenuLabel.pack(side = Tk.LEFT)

			# Menu:

			self.selectedChannel = Tk.StringVar()
			self.selectedChannel.set("Broadcast")
			self.channelMenu = Tk.OptionMenu(self.networkControlFrame, 
				self.selectedChannel,
				"Connection", 
				"Broadcast",
				command = self._changeChannelMenu)

			self.channelMenu.pack(side = Tk.LEFT)

			self.channelMenu.config(
				width = 10,
				background = self.background,
				highlightbackground = self.background,
				foreground = self.foreground
			)

			self.activeWidgets.append(self.channelMenu)
			"""
			# Command Menu .....................................................

			# Label:
			self.commandMenuLabel = Tk.Label(
				self.networkControlFrame,
				bg = self.background,
				fg = self.foreground,
				text = "Message: "
			)

			self.commandMenuLabel.pack(side = Tk.LEFT)

			# Menu:

			self.selectedCommand = Tk.StringVar()
			self.selectedCommand.set("Add")
			self.commandMenu = Tk.OptionMenu(self.networkControlFrame, 
				self.selectedCommand,
				"Add",
				"Disconnect", 
				"Reboot",
				)

			self.commandMenu.config(
				width = 10,
				background = self.background,
				highlightbackground = self.background,
				foreground = self.foreground
			)

			self.commandMenu.pack(side = Tk.LEFT)

			self.activeWidgets.append(self.commandMenu)
			# Send button ......................................................

			self.sendNetworkCommandButton = Tk.Button(
				self.networkControlFrame,
				bg = self.background,
				fg = self.foreground,
				text = "Send",
				command = self._sendNetworkCommand,
				highlightbackground = self.background
				)

			self.sendNetworkCommandButton.pack(side = Tk.LEFT)

			self.activeWidgets.append(self.sendNetworkCommandButton)

			# Shutdown button ..................................................
			"""
			self.shutdownButtonPadding = Tk.Frame(
				self.networkControlFrame,
				bg = self.background,
				width = 40
				)

			self.shutdownButtonPadding.pack(side = Tk.LEFT)
			"""
			self.shutdownButton = Tk.Button(
				self,
				bg = self.background,
				fg = self.foreground,
				text = "SHUTDOWN",
				font = ('TkDefaultFont','12','bold'),
				command = self._shutdown,
				highlightbackground = 'red'
				)

			self.shutdownButton.pack(side = Tk.RIGHT, fill = Tk.Y)

			self.activeWidgets.append(self.shutdownButton)
		
			"""
			# ADD/REMOVE .......................................................
			self.addRemoveFrame = Tk.Frame(
				None,
				background = self.background
			)
			self.addRemoveFrame.pack(fill = Tk.BOTH, expand = True)

			self.notebook.add(
				self.addRemoveFrame,
				text = "Add/Remove"
			)

			self.addAllButton = Tk.Button(
				self.addRemoveFrame,
				bg = self.background,
				highlightbackground = self.background,
				fg = self.foreground,
				text = "Add All",
				command = self._addAll
			)

			self.addAllButton.pack(side = Tk.LEFT)
			
			self.addSelectedButton = Tk.Button(
				self.addRemoveFrame,
				bg = self.background,
				highlightbackground = self.background,
				fg = self.foreground,
				text = "Add Selected",
				command = self._addSelected
			)
			self.addSelectedButton.pack(side = Tk.LEFT)

			self.addLabel = Tk.Label(
				self.addRemoveFrame,
				text = "(NOTE: Only \"Available\" boards will respond)       ",
				bg = self.background,
				fg = "darkgray"
			)
			self.addLabel.pack(side = Tk.LEFT)

			self.removeAllButton = Tk.Button(
				self.addRemoveFrame,
				bg = self.background,
				highlightbackground = self.background,
				fg = self.foreground,
				text = "Remove All",
				state = Tk.DISABLED
			)
			self.removeAllButton.pack(side = Tk.LEFT)
			
			self.removeSelectedButton = Tk.Button(
				self.addRemoveFrame,
				bg = self.background,
				highlightbackground = self.background,
				fg = self.foreground,
				text = "Remove Selected",
				state = Tk.DISABLED
			)
			self.removeSelectedButton.pack(side = Tk.LEFT)
			"""
			
			# QUICK ARRAY CONTROL ..............................................
			self.controlFrame = Tk.Frame(
				None,
				background = self.background
			)
			self.controlFrame.pack(fill = Tk.BOTH, expand = True)

			# Top frame:
			self.controlTopFrame = Tk.Frame(
				self.controlFrame,
				background = self.background
			)
			self.controlTopFrame.pack(
				side = Tk.TOP, fill = Tk.BOTH, expand = True)
			
			# Target Menu:

			# TM Label:
			self.arrayTargetMenuLabel = Tk.Label(
				self.controlTopFrame,
				bg = self.background,
				fg = self.foreground,
				text = "Target: "
			)

			self.arrayTargetMenuLabel.pack(side = Tk.LEFT)

			# TM Menu:

			self.selectedArrayTarget = Tk.StringVar()
			self.selectedArrayTarget.set("All")
			self.arrayTargetMenu = Tk.OptionMenu(
				self.controlTopFrame, 
				self.selectedArrayTarget,
				"Selected", 
				"All"
			)

			self.arrayTargetMenu.pack(side = Tk.LEFT)

			self.arrayTargetMenu.config(
				width = 10,
				background = self.background,
				highlightbackground = self.background,
				foreground = self.foreground
			)

			self.activeWidgets.append(self.arrayTargetMenu)

			# Label(1/4):
			self.arrayCommandMenuLabel1 = Tk.Label(
				self.controlTopFrame,
				bg = self.background,
				fg = self.foreground,
				text = "  Set: "
			)

			self.arrayCommandMenuLabel1.pack(side = Tk.LEFT)

			# Menu:

			self.selectedArrayCommand = Tk.StringVar()
			self.selectedArrayCommand.set(SET_DC)
			self.arrayCommandMenu = Tk.OptionMenu(
				self.controlTopFrame, 
				self.selectedArrayCommand,
				SET_DC,
				SET_RPM,
				)

			self.arrayCommandMenu.config(
				width = 5,
				background = self.background,
				highlightbackground = self.background,
				foreground = self.foreground
			)

			self.arrayCommandMenu.pack(side = Tk.LEFT)

			self.activeWidgets.append(self.arrayCommandMenu)
			
			# Label (2/4):
			self.arrayCommandMenuLabel2 = Tk.Label(
				self.controlTopFrame,
				bg = self.background,
				fg = self.foreground,
				text = "  To: "
			)

			self.arrayCommandMenuLabel2.pack(side = Tk.LEFT)


			# Value entry:
			validateAE = self.register(self._validateArrayEntry)
			self.arrayEntry = Tk.Entry(
				self.controlTopFrame, 
				highlightbackground = self.background,
				bg = 'white',
				fg = self.foreground,
				width = 7, validate = 'key', validatecommand = \
					(validateAE, '%S', '%s', '%d'))
			self.arrayEntry.insert(0, '0')
			self.arrayEntry.pack(side = Tk.LEFT)
			self.activeWidgets.append(self.arrayEntry)
			
			self.keepOnSendToggleVar = Tk.BooleanVar()
			self.keepOnSendToggle = Tk.Checkbutton(
				self.controlTopFrame, 
				text ="Remember value", 
				variable = self.keepOnSendToggleVar, 
				bg = self.background, 
				fg = self.foreground, 
				)
			self.keepOnSendToggleVar.set(False)
			self.keepOnSendToggle.pack(side = Tk.LEFT)
			self.activeWidgets.append(self.keepOnSendToggle)
			
			
			# Label (3/4):
			self.arrayCommandMenuLabel3 = Tk.Label(
				self.controlTopFrame,
				bg = self.background,
				fg = self.foreground,
				text = "     "
			)

			self.arrayCommandMenuLabel3.pack(side = Tk.LEFT)
			
			# Send button:
			self.sendArrayCommandButton = Tk.Button(
				self.controlTopFrame,
				bg = self.background,
				fg = self.foreground,
				text = "Send",
				command = self._sendArrayCommand,
				highlightbackground = self.background
				)
			
			"""	
			# Label (4/4):
			self.arrayCommandMenuLabel4 = Tk.Label(
				self.controlTopFrame,
				bg = self.background,
				fg = 'darkgray',
				font = ('TkDefaultFont', 10),
				text = "  ('Empty' send defaults to 0)  "
			)

			self.arrayCommandMenuLabel4.pack(side = Tk.RIGHT)
			"""
			self.sendArrayCommandButton.pack(side = Tk.LEFT)
			self.activeWidgets.append(self.sendArrayCommandButton)
			
			"""	
			# DC Cap label:
			self.capLabel = Tk.Label(
				self.controlTopFrame,
				bg = self.background,
				fg = self.foreground,
				text = "    DC Cap: "
			)

			self.capLabel.pack(side = Tk.LEFT)

			# DC Cap:
			self.capEntry = Tk.Entry(
				self.controlTopFrame, 
				highlightbackground = self.background,
				bg = 'white',
				fg = self.foreground,
				width = 7,
				validate = 'key', 
				validatecommand = \
					(validateAE, '%S', '%s', '%d')
			)
			self.capEntry.insert(Tk.END, '4')
			self.capEntry.insert(Tk.END, '0')
			self.capEntry.pack(side = Tk.LEFT)
			self.activeWidgets.append(self.capEntry)
			
			# Set DC cap button:
			self.setCapButton = Tk.Button(
				self.controlTopFrame,
				bg = self.background,
				fg = self.foreground,
				text = "Set",
				command = self._setCap,
				highlightbackground = self.background
				)
			
			self.setCapButton.pack(side = Tk.LEFT)
			self.activeWidgets.append(self.setCapButton)
			
			# Label (4/4):
			self.arrayCommandMenuLabel4 = Tk.Label(
				self.controlTopFrame,
				bg = self.background,
				fg = self.foreground,
				text = "    "
			)

			self.arrayCommandMenuLabel4.pack(side = Tk.RIGHT)
			"""

			# Bottom frame:
			self.controlBottomFrame = Tk.Frame(
				self.controlFrame,
				bd = 1,
				relief = Tk.RIDGE,
				background = self.background,
			)
			self.controlBottomFrame.pack(
				side = Tk.TOP, fill = Tk.BOTH, expand = True)
			
			# Array selection:
			
			self.arraySelectionLabel = Tk.Label(
				self.controlBottomFrame,
				bg = self.background,
				fg = self.foreground,
				text = "  Fans: "
			)
			self.arraySelectionLabel.pack(side = Tk.LEFT)

			self.arraySelectionFrame = Tk.Frame(
				self.controlBottomFrame,
				bg = self.background
			)
			self.arraySelectionFrame.pack(side = Tk.LEFT)
			
			# Fan checks:
			self.fanBooleanVars = ()
			self.fanCheckButtons = ()
			for fan in range(self.maxFans):
				self.fanBooleanVars += (
					Tk.BooleanVar(),
				)
				self.fanCheckButtons += (
					Tk.Checkbutton(
						self.arraySelectionFrame,
						text = " {:2d} ".format(fan+1),
						font = ('TkFixedFont','12'),
						bg = self.background,
						fg = self.foreground,
						indicatoron = False,
						selectcolor = 'orange',
						variable = self.fanBooleanVars[fan]
					),
				)
				self.activeWidgets.append(self.fanCheckButtons[fan])
				self.fanCheckButtons[fan].pack(side = Tk.LEFT)

			self.selectAllFansButton = Tk.Button(
				self.controlBottomFrame,
				text = "All",
				font = ("TkDefaultFont", 8),
				padx = 3,	
				fg = self.foreground,
				bg = self.background,
				highlightbackground = self.background,
				command = self._selectAllFans
			)
			self.activeWidgets.append(self.selectAllFansButton)
			self.selectAllFansButton.pack(side = Tk.LEFT)
			
			self.deselectAllFansButton = Tk.Button(
				self.controlBottomFrame,
				text = "None",
				font = ("TkDefaultFont", 8),
				padx = 3,	
				fg = self.foreground,
				bg = self.background,
				highlightbackground = self.background,
				command = self._deselectAllFans
			)
			self.activeWidgets.append(self.deselectAllFansButton)
			self.deselectAllFansButton.pack(side = Tk.LEFT)
			
			self.selectOddFansButton = Tk.Button(
				self.controlBottomFrame,
				text = "Odd",
				font = ("TkDefaultFont", 8),
				padx = 3,	
				fg = self.foreground,
				bg = self.background,
				highlightbackground = self.background,
				command = self._selectOddFans
			)
			self.activeWidgets.append(self.selectOddFansButton)
			self.selectOddFansButton.pack(side = Tk.LEFT)

			self.selectEvenFansButton = Tk.Button(
				self.controlBottomFrame,
				text = "Even",
				font = ("TkDefaultFont", 8),
				padx = 3,	
				fg = self.foreground,
				bg = self.background,
				highlightbackground = self.background,
				command = self._selectEvenFans
			)
			self.activeWidgets.append(self.selectEvenFansButton)
			self.selectEvenFansButton.pack(side = Tk.LEFT)

			self.invertFanSelectionButton = Tk.Button(
				self.controlBottomFrame,
				text = "Invert",
				font = ("TkDefaultFont", 8),
				padx = 3,	
				fg = self.foreground,
				bg = self.background,
				highlightbackground = self.background,
				command = self._invertFanSelection
			)
			self.activeWidgets.append(self.invertFanSelectionButton)
			self.invertFanSelectionButton.pack(side = Tk.LEFT)

			self._selectAllFans()

			self.notebook.add(
				self.controlFrame,
				text = "Array Control",
				state = Tk.NORMAL
			)


			self.bind("<Return>", self._onEnter)
			self.sendNetworkCommandButton.bind("<Return>", self._onEnter)
			self.sendArrayCommandButton.bind("<Return>", self._onEnter)
			self.controlFrame.bind("<Return>", self._onEnter)
			self.networkControlFrame.bind("<Return>", self._onEnter)

			self.arrayEntry.bind("<Return>", self._onEnter)
			self.arrayEntry.bind("<Control-a>", self._selectAllFans)
			self.arrayEntry.bind("<Control-A>", self._selectAllFans)
			self.arrayEntry.bind("<Control-n>", self._deselectAllFans)
			self.arrayEntry.bind("<Control-N>", self._deselectAllFans)
			self.arrayEntry.bind("<Control-o>", self._selectOddFans)
			self.arrayEntry.bind("<Control-O>", self._selectOddFans)
			self.arrayEntry.bind("<Control-e>", self._selectEvenFans)
			self.arrayEntry.bind("<Control-E>", self._selectEvenFans)
			self.arrayEntry.bind("<Control-i>", self._invertFanSelection)
			self.arrayEntry.bind("<Control-I>", self._invertFanSelection)

			self.notebook.bind("<Return>", self._onEnter)

				

			#self.bind("<Enter>", lambda e: self.focus_set())

			# RAMP CONTROL .....................................................
			
			# General ..........................................................
			self.rampFrame = Tk.Frame(
				None,
				bg = self.background
			)
			self.rampDCString = "(DC%)"
			self.rampRPMString = "(RPM)"

			# Top Frame ........................................................
			self.rampTopFrame = Tk.Frame(
				self.rampFrame,
				bg = self.background
			)
			self.rampTopFrame.pack(side = Tk.TOP, fill = Tk.BOTH, expand = True)
			self.isRampActive = False
			self.rampActiveWidgets = []
			self.rampUnitLabels = []
			self.ramp = []
			self.rampIndex = 0
			self.rampLength = 0
			self.rampSign = 1
			self.rampEndValue = 0
			self.rampCommand = cm.SET_DC
			self.rampTargets = (cm.ALL,)
			self.rampReturnFlag = False
			self.rampFans = tuple(map(lambda x: 1, range(self.maxFans)))
				# NOTE: This ramp will affect all fans

			# StartStop Button
			self.rampStartStopButton = Tk.Button(
				self.rampTopFrame,
				bg = self.background,
				highlightbackground = self.background,
				fg = self.foreground,
				text = "Start",
				width = 9,
				command = self._rampStartStopCommand,
				)

			self.rampStartStopButton.pack(side = Tk.LEFT)
			self.activeWidgets.append(self.rampStartStopButton)
			
			# Clear Button
			self.rampClearButton = Tk.Button(
				self.rampTopFrame,
				bg = self.background,
				highlightbackground = self.background,
				fg = self.foreground,
				text = "Clear",
				command = self._rampClearCommand,
				)

			self.rampClearButton.pack(side = Tk.LEFT)
			self.rampActiveWidgets.append(self.rampClearButton)
			self.activeWidgets.append(self.rampClearButton)

			# Loop Checkbutton
			self.rampLoopToggleVar = Tk.BooleanVar()
			self.rampLoopToggle = Tk.Checkbutton(
				self.rampTopFrame, 
				text ="Loop", 
				variable = self.rampLoopToggleVar, 
				bg = self.background, 
				fg = self.foreground, 
				)
			self.rampLoopToggleVar.set(False)
			self.rampLoopToggle.pack(side = Tk.LEFT)
			self.rampActiveWidgets.append(self.rampLoopToggle)
			self.activeWidgets.append(self.rampLoopToggle)

			# Return Checkbutton
			self.rampReturnToggleVar = Tk.BooleanVar()
			self.rampReturnToggle = Tk.Checkbutton(
				self.rampTopFrame, 
				text ="Ramp Back", 
				variable = self.rampReturnToggleVar, 
				bg = self.background, 
				fg = self.foreground, 
				)
			self.rampReturnToggleVar.set(False)
			self.rampReturnToggle.pack(side = Tk.LEFT)
			self.rampActiveWidgets.append(self.rampReturnToggle)
			self.activeWidgets.append(self.rampReturnToggle)

			# Unit Menu
			self.rampUnitMenuLabel = Tk.Label(
				self.rampTopFrame,
				bg = self.background,
				fg = self.foreground,
				text = "  Unit: "
			)
			self.rampUnitMenuLabel.pack(side = Tk.LEFT)

			self.selectedRampUnit = Tk.StringVar()
			self.selectedRampUnit.set(SET_DC)
			self.selectedRampUnit.trace('w', self._rampUnitMenuCallback)
			self.rampUnitMenu = Tk.OptionMenu(
				self.rampTopFrame, 
				self.selectedRampUnit,
				SET_DC,
				SET_RPM,
				)
			self.rampUnitMenu.config(
				width = 5,
				background = self.background,
				highlightbackground = self.background,
				foreground = self.foreground,
			)
			self.rampUnitMenu.pack(side = Tk.LEFT)
			self.rampActiveWidgets.append(self.rampUnitMenu)
			self.activeWidgets.append(self.rampUnitMenu)

			# Target Menu
			self.rampTargetMenuLabel = Tk.Label(
				self.rampTopFrame,
				bg = self.background,
				fg = self.foreground,
				text = "  Target: "
			)
			self.rampTargetMenuLabel.pack(side = Tk.LEFT)

			# Menu:
			self.selectedRampTarget = Tk.StringVar()
			self.selectedRampTarget.set("All")
			self.rampTargetMenu = Tk.OptionMenu(
				self.rampTopFrame, 
				self.selectedRampTarget,
				"Selected", 
				"All"
			)
			self.rampTargetMenu.pack(side = Tk.LEFT)
			self.rampTargetMenu.config(
				width = 10,
				background = self.background,
				highlightbackground = self.background,
				foreground = self.foreground
			)
			self.rampActiveWidgets.append(self.rampTargetMenu)
			self.activeWidgets.append(self.rampTargetMenu)
		
			# Progress Bar
			self.rampProgressBarLabel = Tk.Label(
				self.rampTopFrame,
				bg = self.background,
				fg = self.foreground,
				text = "  Progress: "
			)
			self.rampProgressBarLabel.pack(side = Tk.LEFT)

			
			self.rampProgressBar = Tk.ttk.Progressbar(
				self.rampTopFrame, 
				orient = "horizontal", 
				mode = "determinate"
			)
			self.rampProgressBar.pack(
				side = Tk.LEFT, fill = Tk.X, expand = True)
			
			self.rampProgressBarPadding = Tk.Label(
				self.rampTopFrame,
				bg = self.background,
				fg = self.foreground,
				text = "  "
			)
			self.rampProgressBarPadding.pack(side = Tk.LEFT)

			# Bottom Frame .....................................................
			
			self.rampBottomFrame = Tk.Frame(
				self.rampFrame,
				bg = self.background
			)
			self.rampBottomFrame.pack(
				side = Tk.TOP, fill = Tk.BOTH, expand = True)
			
			# Start value
			self.rampStartValueLabel = Tk.Label(
				self.rampBottomFrame,
				bg = self.background,
				fg = self.foreground,
				text = " From: "
			)
			self.rampStartValueLabel.pack(side = Tk.LEFT)

			validateRS = self.register(self._validateRampEntry)
			self.rampStartEntry = Tk.Entry(
				self.rampBottomFrame, 
				highlightbackground = self.background,
				bg = 'white',
				fg = self.foreground,
				width = 7, validate = 'key', validatecommand = \
					(validateRS, '%S', '%s', '%d'))
			self.rampStartEntry.pack(side = Tk.LEFT)
			self.rampActiveWidgets.append(self.rampStartEntry)
			self.activeWidgets.append(self.rampStartEntry)

			self.rampStartUnitLabel = Tk.Label(
				self.rampBottomFrame,
				width = 6,
				bg = self.background,
				fg = 'darkgray',
				text = self.rampDCString
			)
			self.rampStartUnitLabel.pack(side = Tk.LEFT)
			self.rampUnitLabels.append(self.rampStartUnitLabel)

			# End value
			self.rampEndValueLabel = Tk.Label(
				self.rampBottomFrame,
				bg = self.background,
				fg = self.foreground,
				text = " To: "
			)
			self.rampEndValueLabel.pack(side = Tk.LEFT)

			validateRE = self.register(self._validateRampEntry)
			self.rampEndEntry = Tk.Entry(
				self.rampBottomFrame, 
				highlightbackground = self.background,
				bg = 'white',
				fg = self.foreground,
				width = 7, validate = 'key', validatecommand = \
					(validateRE, '%S', '%s', '%d'))
			self.rampEndEntry.pack(side = Tk.LEFT)
			self.rampActiveWidgets.append(self.rampEndEntry)
			self.activeWidgets.append(self.rampEndEntry)

			self.rampEndUnitLabel = Tk.Label(
				self.rampBottomFrame,
				width = 6,
				bg = self.background,
				fg = 'darkgray',
				text = self.rampDCString
			)
			self.rampEndUnitLabel.pack(side = Tk.LEFT)
			self.rampUnitLabels.append(self.rampEndUnitLabel)

			# Step value
			self.rampStepValueLabel = Tk.Label(
				self.rampBottomFrame,
				bg = self.background,
				fg = self.foreground,
				text = " Step: "
			)
			self.rampStepValueLabel.pack(side = Tk.LEFT)

			validateRP = self.register(self._validateRampEntry)
			self.rampStepEntry = Tk.Entry(
				self.rampBottomFrame, 
				highlightbackground = self.background,
				bg = 'white',
				fg = self.foreground,
				width = 7, validate = 'key', validatecommand = \
					(validateRP, '%S', '%s', '%d'))
			self.rampStepEntry.pack(side = Tk.LEFT)
			self.rampActiveWidgets.append(self.rampStepEntry)
			self.activeWidgets.append(self.rampStepEntry)

			self.rampStepUnitLabel = Tk.Label(
				self.rampBottomFrame,
				width = 6,
				bg = self.background,
				fg = 'darkgray',
				text = self.rampDCString
			)
			self.rampStepUnitLabel.pack(side = Tk.LEFT)
			self.rampUnitLabels.append(self.rampStepUnitLabel)

			# Time interval
			self.rampIntervalValueLabel = Tk.Label(
				self.rampBottomFrame,
				bg = self.background,
				fg = self.foreground,
				text = " Interval: "
			)
			self.rampIntervalValueLabel.pack(side = Tk.LEFT)

			validateRP = self.register(self._validateRampIntervalEntry)
			self.rampIntervalEntry = Tk.Entry(
				self.rampBottomFrame, 
				highlightbackground = self.background,
				bg = 'white',
				fg = self.foreground,
				width = 7, validate = 'key', validatecommand = \
					(validateRP, '%S', '%s', '%d'))
			self.rampIntervalEntry.pack(side = Tk.LEFT)
			self.rampActiveWidgets.append(self.rampIntervalEntry)
			self.activeWidgets.append(self.rampIntervalEntry)
			
			self.rampIntervalUnitLabel = Tk.Label(
				self.rampBottomFrame,
				bg = self.background,
				fg = self.foreground,
				text = "(ms) (min. {}ms)".format(self.mininumIntervalMS)
			)
			self.rampIntervalUnitLabel.pack(side = Tk.LEFT)

			# Build general ....................................................
			self.notebook.add(
				self.rampFrame,
				text = "Ramp Control",
				state = Tk.NORMAL
			)

			# Bind active widgets to Enter:
			for widget in self.rampActiveWidgets + [self.rampStartStopButton]:
				widget.bind("<Return>", self._rampStartStopCommand)

			# BOOTLOADER .......................................................
			self.bootloaderFrame = Tk.Frame(
				None,
				background = self.background
			)
			self.bootloaderFrame.pack(fill = Tk.BOTH, expand = True)

			self.bootloaderStatus = NOT_FLASHING

			# File chooser:
			self.fileChooserLabel = Tk.Label(
				self.bootloaderFrame,
				bg = self.background,
				fg = self.foreground,
				text = "File:  "
			)
			self.fileChooserLabel.pack(side = Tk.LEFT)

			self.bootloaderTargetVar = Tk.StringVar()

			self.chosenFileEntry = Tk.Entry(
				self.bootloaderFrame, 
				textvariable = self.bootloaderTargetVar,
				highlightbackground = self.background,
				bg = self.background,
				fg = self.foreground,
				width = 20, 
			)
			self.chosenFileEntry.pack(side = Tk.LEFT)

			self.activeWidgets.append(self.chosenFileEntry)

			self.targetFile = None
			
			self.chosenFileSeparator = Tk.Label(
				self.bootloaderFrame,
				bg = self.background,
				fg = self.foreground,
				width = 1,
			)
			self.chosenFileSeparator.pack(side = Tk.LEFT)
			
			self.fileSize = 0 # Bytes	
			self.fileChooserButton = Tk.Button(
				self.bootloaderFrame,
				bg = self.background,
				fg = self.foreground,
				text = "...",
				font = ('TkDefaultFont',8),
				command = self._fileChooser,
				highlightbackground = self.background
				)

			self.fileChooserButton.pack(side = Tk.LEFT)
			self.activeWidgets.append(self.fileChooserButton)


			# Version name:

			self.versionNameLabel = Tk.Label(
				self.bootloaderFrame,
				bg = self.background,
				fg = self.foreground,
				text = "  Version Name:  "
			)
			self.versionNameLabel.pack(side = Tk.LEFT)
			
			validateVN = self.register(self._validateVersionNameEntry)
			self.versionNameEntry = Tk.Entry(
				self.bootloaderFrame, 
				highlightbackground = self.background,
				bg = 'white',
				fg = self.foreground,
				width = 10, 
				validate = 'key', validatecommand = \
					(validateVN, '%S', '%s', '%d'))
			self.versionNameEntry.pack(side = Tk.LEFT)
			self.activeWidgets.append(self.versionNameEntry)
			
			self.versionNameSeparator = Tk.Label(
				self.bootloaderFrame,
				bg = self.background,
				fg = self.foreground,
				width = 1,
			)
			self.versionNameSeparator.pack(side = Tk.LEFT)
			


			# Start button:
			self.bootloaderStartStopButton = Tk.Button(
				self.bootloaderFrame,
				bg = self.background,
				fg = self.foreground,
				text = "Start Flashing",
				command = self._bootloaderStartStop,
				highlightbackground = self.background
				)

			self.bootloaderStartStopButton.pack(side = Tk.LEFT)
			self.activeWidgets.append(self.bootloaderStartStopButton)
	
			# Add to notebook:
			self.notebook.add(
				self.bootloaderFrame,
				text = "Bootloader"
			)

			# CUSTOM MESSAGE ...................................................
			self.customMessageFrame = Tk.Frame(
				None,
				background = self.background
			)
			self.customMessageFrame.pack(fill = Tk.BOTH, expand = True)

			self.notebook.add(
				self.customMessageFrame,
				text = "Custom Message",
				state = Tk.DISABLED
			)

			# BUILD DATA -------------------------------------------------------

			# PACK -------------------------------------------------------------

			self.pack(fill = Tk.X, expand = True)
			self.setStatus(cm.DISCONNECTED)
			self.notebook.select(1)
			self.arrayEntry.focus_set()

		except:
			ep.errorPopup("Error in FCCControlBar")

		# End __init__ =========================================================
	
	def setStatus(self, newStatus): # ==========================================
		

		if newStatus is cm.CONNECTED:
			# Activate all widgets:
			for widget in self.activeWidgets:
				widget.config(state = Tk.NORMAL)

		else:
			# Deactivate all widgets:
			for widget in self.activeWidgets:
				widget.config(state = Tk.DISABLED)

			# Deactivate ongoing ramp, if any:
			self.isRampActive = False
		
		self.status = newStatus

		# End setStatus ========================================================

	def _bootloaderStartStop(self, event = None): # ============================

		try:

			# Check status:
			if self.bootloaderStatus is NOT_FLASHING:
				# Start flashing

				# Check file and update file size:	

				try:
					self.fileSize = os.path.getsize(self.bootloaderTargetVar.get())

				except FileNotFoundError:
					self._printM(
						"Error starting bootloader (file not found)",'E')
					return

				else:
					self._printM("Binary file size: {}".format(self.fileSize))

				# Check version name:
				
				if self.versionNameEntry.get() == '':
					self._printM("Error starting bootloader (no version name)", 'E')
					return

				# Send command:
				self.commandQueue.put_nowait(
					(
						mw.COMMUNICATOR, 
						cm.BOOTLOADER_START,
						self.versionNameEntry.get(),
						self.targetFile, 
						self.fileSize
					)
				)

				# Update interface:
				self.chosenFileEntry.config(state = Tk.DISABLED)
				self.fileChooserButton.config(state = Tk.DISABLED)
				self.versionNameEntry.config(state = Tk.DISABLED)
				
				"""
				self.notebook.tab(
					0,
					state = Tk.DISABLED
				)
				"""

				self.notebook.tab(
					1,
					state = Tk.DISABLED
				)
			
				

				self.bootloaderStartStopButton.config(
					text = "Stop Flashing"
				)

				# Update status:
				self.bootloaderStatus = FLASHING
		
				self._printM("Flashing started", 'G')

			else:
				# Stop flashing

				# Send stop command:
				self.commandQueue.put_nowait(
					(
						mw.COMMUNICATOR, 
						cm.BOOTLOADER_STOP
					)
				)

				# Update interface:
				self.bootloaderStatus = NOT_FLASHING
				self.chosenFileEntry.config(state = Tk.NORMAL)
				self.fileChooserButton.config(state = Tk.NORMAL)
				self.versionNameEntry.config(state = Tk.NORMAL)

				# Remove file:
				os.remove(self.targetFile)
				self.bootloaderTargetVar.set("")
				self.versionNameEntry.delete(0, Tk.END)
			
				self.notebook.tab(
					0,
					state = Tk.NORMAL
				)

				self.notebook.tab(
					1,
					state = Tk.NORMAL
				)
				self.bootloaderStartStopButton.config(
					text = "Start Flashing"
				)

				# Update status:
				self.bootloaderStatus = NOT_FLASHING
		
		except:
			ep.errorPopup("Error starting bootloader: ")
			self._printM("Flashing stopped by exception", 'E')
			self.bootloaderStatus = NOT_FLASHING
			self.chosenFileEntry.config(state = Tk.NORMAL)
			self.fileChooserButton.config(state = Tk.NORMAL)
			self.versionNameEntry.config(state = Tk.NORMAL)
			
			self.notebook.tab(
				0,
				state = Tk.NORMAL
			)

			self.notebook.tab(
				1,
				state = Tk.NORMAL
			)
			
			self.bootloaderStartStopButton.config(
				text = "Start Flashing"
			)



		# End _bootloaderStartStop =============================================

	def _validateVersionNameEntry(self, newCharacter, textBeforeCall, action): 

		return True

		# End _validateVersionNameEntry ========================================

	def _validateArrayEntry(self, newCharacter, textBeforeCall, action): # =====
		try:
			# ABOUT: To be used by TkInter to validate text in "Send" Entry.
			if action == '0':
				return True
			
			elif self.selectedArrayCommand.get() == SET_DC and \
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

			elif self.selectedArrayCommand.get() == SET_RPM and newCharacter \
				in '0123456789' and len(textBeforeCall) < 5:
				return True

			else:
				return False

		except:
			ep.errorPopup("Error in FCCControlBar")

		# End _validateN =======================================================
	
	def _validateRampEntry(self, newCharacter, textBeforeCall, action): # ======
		try:
			# ABOUT: To be used by TkInter to validate text in Ramp Step Entry.
			if action == '0':
				return True
		
			return \
				(
					self.selectedRampUnit.get() == SET_DC and \
					newCharacter in '0123456789' and \
					int(textBeforeCall + newCharacter) <= 100 and \
					int(textBeforeCall + newCharacter) >= 0
				) or \
				(
					self.selectedRampUnit.get() == SET_RPM and \
					newCharacter in '0123456789' and \
					int(textBeforeCall + newCharacter) <= self.maxRPM and \
					int(textBeforeCall + newCharacter) >= 0
				)
		
		except ValueError:
			return False

		except:
			ep.errorPopup("Error in FCCControlBar")

		# Step _validateRampEntry ==============================================
	
	def _validateRampIntervalEntry(self, newCharacter, textBeforeCall, action):
		try:
			if action == '0':
				return True

			elif newCharacter in '0123456789':
				return True

			else:
				return False

		except:
			ep.errorPopup("Error in FCCControlBar")

		# Interval _validateRampIntervalEntry ==================================


	def _validateArrayEntry(self, newCharacter, textBeforeCall, action): # =====
		try:
			# ABOUT: To be used by TkInter to validate text in "Send" Entry.
			if action == '0':
				return True
			
			elif self.selectedArrayCommand.get() == SET_DC and \
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

			elif self.selectedArrayCommand.get() == SET_RPM and newCharacter \
				in '0123456789' and len(textBeforeCall) < 5:
				return True

			else:
				return False

		except:
			ep.errorPopup("Error in FCCControlBar")

		# End _validateN =======================================================


	def _sendNetworkCommand(self, event = None): # =============================
	
		try:

			# Get targets:
			if self.selectedNetworkTarget.get() == "All":
				targets = (cm.ALL,)
			else:
				targets = self.selectionSource.getSelection()
		
			# Assemble message:
			if self.selectedCommand.get() == "Disconnect":
				commandCode = cm.DISCONNECT

			elif self.selectedCommand.get() == "Reboot":
				commandCode = cm.REBOOT
			
			elif self.selectedCommand.get() == "Add":
				commandCode = cm.ADD

			else:
				# TODO: Handle errors
				return

			# Store in Queue:
			for target in targets:
				self.commandQueue.put_nowait(
					(mw.COMMUNICATOR, commandCode, target)
				)
		
		except:
			ep.errorPopup("Error in FCCControlBar")

		# End _sendNetworkCommand ==============================================

	def _sendArrayCommand(self, event = None): # ===============================
		try:
			
			# NOTE. Parts of an array command:
			#	- Target (All or Selection)
			#	- Command (DC or RPM)
			#	- Fans	(Str of 1's and 0's)

			# Get targets:
			arrayCommand = ()

			if self.selectedArrayTarget.get() == "All":
				targets = (cm.ALL,)
			elif self.selectedArrayTarget.get() == "Selected":
				targets = self.selectionSource.getSelection()

				if len(targets) == 0:
					return
			else:
				self._printM("Error: Unrecognized Target Menu entry \"{}\"".\
					format(self.selectedArrayTarget.get()), 'E')

			# Get command and value (First check for empty value)
			if self.arrayEntry.get() == '':
				self._printM("NOTE: Empty array value defaulted to 0", 'W')
				self.arrayEntry.insert(0, '0')

			if self.selectedArrayCommand.get() == SET_DC:
				command = cm.SET_DC
				value = float(self.arrayEntry.get())

			elif self.selectedArrayCommand.get() == SET_RPM:
				command = cm.SET_RPM
				value = int(self.arrayEntry.get())

			else:
				return

			# Get selection
			fans = ()
			for fanBooleanVar in self.fanBooleanVars:
				if fanBooleanVar.get():
					fans += (1,)
				else:
					fans += (0,)

			arrayCommand += (mw.COMMUNICATOR, command, value, fans)
			arrayCommand += targets

			self.commandQueue.put_nowait(
				arrayCommand
				
			)
			
			print(
				arrayCommand
			)

			if not self.keepOnSendToggleVar.get():
				self.arrayEntry.delete(0,Tk.END)
		except:
			ep.errorPopup("Error in FCCControlBar")

		# End _sendArrayCommand ================================================

	def _setCap(self, event = None): # =========================================
		try:		

			self._printM("SETCAP NOT IMPLEMENTED", 'E')

		except:
			ep.errorPopup("Error in FCCControlBar")
		# End _setCap ==========================================================

	def _selectAllFans(self, event = None): # ==================================
		try:		
			
			for fanBooleanVar in self.fanBooleanVars:
				fanBooleanVar.set(True)

		except:
			ep.errorPopup("Error in FCCControlBar")
		
		# End _selectAllFans ===================================================

	def _deselectAllFans(self, event = None): # ================================
		try:		
			
			for fanBooleanVar in self.fanBooleanVars:
				fanBooleanVar.set(False)

		except:
			ep.errorPopup("Error in FCCControlBar")
		
		# End _deselectAllFans =================================================

	def _selectOddFans(self, event = None): # ==================================
		# NOTE: Selects odd fans as seen by the user (starting at 1)
		try:		
			
			for fanBooleanVar in self.fanBooleanVars[0:-1:2]:
				fanBooleanVar.set(True)

		except:
			ep.errorPopup("Error in FCCControlBar")
		# End _selectOddFans ===================================================

	def _selectEvenFans(self, event = None): # =================================
		# NOTE: Selects even fans as seen by the user (starting at 1)
		try:		
			
			for fanBooleanVar in self.fanBooleanVars[1::2]:
				fanBooleanVar.set(True)

		except:
			ep.errorPopup("Error in FCCControlBar")
		# End _selectEvenFans ==================================================

	def _invertFanSelection(self, event = None): # =============================
		try:		
			
			for fanBooleanVar in self.fanBooleanVars:
				fanBooleanVar.set(not fanBooleanVar.get())

		except:
			ep.errorPopup("Error in FCCControlBar")

		# End _invertFanSelection ==============================================

	def	_sendToCommunicator(self, command, value, fans, targets): # ============
		try:		
			
			self.commandQueue.put_nowait(
				(mw.COMMUNICATOR,
				command,
				value,
				fans)
				+ targets
			)

		except:
			ep.errorPopup("Error in FCCControlBar")
		# End _sendToCommunicator ==============================================

	def _rampStartStopCommand(self, *event): # =================================
		try:		
		
			if self.isRampActive:
				# Ramp active. Stop Ramp
				
				# Lock button:
				self.rampStartStopButton.config(
					text = "Stopping",
					state = Tk.DISABLED
				)

				# Set flag:
				self.isRampActive = False 
					# NOTE: Ramp routine will handle the rest
	
			elif self.rampStartEntry.get() != '' and\
				self.rampEndEntry.get() != '' and\
				self.rampStepEntry.get() != ''and\
				self.rampIntervalEntry.get() != '' and\
				int(self.rampIntervalEntry.get()) >= self.mininumIntervalMS and\
				int(self.rampStepEntry.get()) > 0 and\
				self.rampStartEntry.get() != self.rampEndEntry.get():
				# Ramp inactive w/ valid values. Start Ramp

				# Lock Button:
				self.rampStartStopButton.config(
					state = Tk.DISABLED
				)

				# Lock widgets:
				for widget in self.rampActiveWidgets:
					widget.config(
						state = Tk.DISABLED
					)

				# Assemble ramp:	
				if int(self.rampStartEntry.get())>int(self.rampEndEntry.get()):
					self.rampSign = -1
				else:
					self.rampSign = 1

				self.ramp = range(
					int(self.rampStartEntry.get()),
					int(self.rampEndEntry.get()),
					int(self.rampStepEntry.get())*self.rampSign
				)

				self.rampIndex = 0
				self.rampLength = len(self.ramp)

				self.rampEndValue = int(self.rampEndEntry.get())

				# Set flag:
				self.isRampActive = True
				
				# Get units:
				if self.selectedRampUnit.get() == SET_DC:
					unit = "% DC"
					self.rampCommand = cm.SET_DC
				elif self.selectedRampUnit.get() == SET_RPM:
					unit = "RPM"
					self.rampCommand = cm.SET_RPM
				else:
					raise RuntimeError(
						"Unrecognized Ramp Unit Menu value \"{}\"".\
							format(self.selectedRampUnit.get())
					)

				# Get selection:
				if self.selectedRampTarget.get() == "All":
					self.rampTargets = (cm.ALL,)
					selection = "All"
				elif self.selectedRampTarget.get() == "Selected":
					self.rampTargets = self.selectionSource.getSelection()
					selection = "{} Modules".format(len(self.rampTargets))
				else:
					raise RuntimeError(
						"Unrecognized Ramp Target Menu value \"{}\"".\
							format(self.selectedRampTarget.get())
					)
				
				# Check return flag:
				self.rampReturnFlag = self.rampReturnToggleVar.get()

				# Update progress bar:
				self.rampProgressBar["maximum"] = self.rampEndValue
				self.rampProgressBar["value"] = 0

				# Start ramp:
				self._printM(
					"Starting ramp from {}{} to {}{} "\
						"in steps of {}{} every {} ms ({} steps) on {}".\
							format(
								self.ramp[0],
								unit,
								self.rampEndEntry.get(),
								unit,
								self.rampStepEntry.get(),
								unit,
								self.rampIntervalEntry.get(),
								self.rampLength,
								selection
							)
				)
				self._rampRoutine()

				# Configure button:
				self.rampStartStopButton.config(
					text = "Stop",
					state = Tk.NORMAL
				)

			else:
				# Ramp inactive w/ invalid values. Print error message
				self._printM(
					"Error: Tried to start ramp with invalid paramters. "\
						"Ensure that:\n"\
						"-\tNo parameters are empty\n"\
						"-\tThe start and stop values are different\n"\
						"-\tAll parameters are greater than 0 as integers\n"
						"-\tThe time interval is greater than {} ms".\
							format(self.mininumIntervalMS),
					'E'
				)


		except:
			self.isRampActive = False
			ep.errorPopup("Error in FCCControlBar")
	
		# End _rampStartStopCommand ============================================
	
	def _rampClearCommand(self, *event): # =====================================
		try:		
			if self.isRampActive:
				self._printM(
					"ERROR: Tried to Clear Ramp entries while active", 'E')	
				return

			else:
				for activeWidget in self.rampActiveWidgets:
					if type(activeWidget) == Tk.Checkbutton:
						activeWidget.deselect()
					elif type(activeWidget) == Tk.Entry:
						activeWidget.delete(0, Tk.END)	

		except:
			ep.errorPopup("Error in FCCControlBar")
	
		# End _rampClearCommand ================================================

	def _rampRoutine(self): # ==================================================

		try:		
			if self.isRampActive:
				
				if self.rampIndex < self.rampLength:
					# Within ramp
					
					# Assign next value:
					self._sendToCommunicator(
						command = self.rampCommand,
						value = self.ramp[self.rampIndex],
						fans = self.rampFans, 
						targets = self.rampTargets,
					)

					self._printM("Ramp {}/{}: {}".\
						format(
							self.rampIndex, 
							self.rampLength, 
							self.ramp[self.rampIndex]
						)
					)

					# Increment index:
					self.rampProgressBar["value"] = self.ramp[self.rampIndex]
					self.rampIndex += 1

				elif self.rampIndex == self.rampLength:
					# At last step
					
					# Assign last value:
					self._sendToCommunicator(
						command = self.rampCommand,
						value = int(self.rampEndValue),
						fans = self.rampFans, 
						targets = self.rampTargets,
					)
					
					self._printM("Ramp {}/{}: {}".\
						format(
							self.rampIndex, 
							self.rampLength, 
							self.rampEndValue
						)
					)

					# Increment index:
					self.rampProgressBar["value"] = self.rampEndValue
					self.rampIndex += 1

				elif self.rampReturnFlag:
					# Done with ramp, but told to ramp back

					# Rebuild ramp (backwards):
					self.ramp = range(
						int(self.rampEndEntry.get()),
						int(self.rampStartEntry.get()),
						int(self.rampStepEntry.get())*self.rampSign*(-1)
					)
					self.rampEndValue = int(self.rampStartEntry.get())

					# Restart counters and update flags:
					self.rampIndex = 0
					self.rampReturnFlag = False

					self._printM("Ramping back...")

				elif self.rampLoopToggleVar.get():
					# Done with ramp, but told to restart when done

					# Rebuild ramp:
					self.ramp = range(
						int(self.rampStartEntry.get()),
						int(self.rampEndEntry.get()),
						int(self.rampStepEntry.get())*self.rampSign
					)

					# Restart counter and flags:
					self.rampIndex = 0
					self.rampEndValue = int(self.rampEndEntry.get())
					self.rampReturnFlag = self.rampReturnToggleVar.get()

					self._printM("Restarting ramp...")

				else:
					# Done with ramp
					self.isRampActive = False

				# Schedule next call:
				self.after(
					int(self.rampIntervalEntry.get()), self._rampRoutine)

			elif self.status == cm.CONNECTED:
				# Ramp stopped while ControlBar is active. 
				# Return to pre-start state:

				# Activate widgets:
				for widget in self.rampActiveWidgets:
					widget.config(
						state = Tk.NORMAL
					)

				# Configure button:
				self.rampStartStopButton.config(
					state = Tk.NORMAL,
					text = "Start"
				)
				
				self._printM("Ramp Ended")
				self.rampProgressBar["value"] = 0

				return

			elif self.status != cm.CONNECTED:
				# Ramp stopped while ControlBar is inactive.
				# Revert button and stop ramp without activating widgets:

				self.rampStartStopButton.config(
					text = "Start"
				)
				print(self.status)	
				self._printM("Ramp Terminated")
				self.rampProgressBar["value"] = 0

				return
		
		except:
			ep.errorPopup("Error in FCCControlBar")
			self.isRampActive = False
			self._rampRoutine()

		# End _rampRoutine =====================================================
	
	def _rampUnitMenuCallback(self, *event): # =================================
		try:		
			
			if self.selectedRampUnit.get() == SET_DC:
				for label in self.rampUnitLabels:
					label.config(text = self.rampDCString)

			elif self.selectedRampUnit.get() == SET_RPM:
				for label in self.rampUnitLabels:
					label.config(text = self.rampRPMString)

			else:
				self._printM("WARNING: Unknown unit on Ramp Unit Menu \"{}\"".\
					format(self.rampUnitMenu.get()))

		except:
			ep.errorPopup("Error in FCCControlBar")

		# End _rampUnitMenuCallback ============================================

	def _onEnter(self, event = None): # ========================================
		try:
			# Check context:
			if self.notebook.select() == ".!frame":
				# In network control context:
				self._sendNetworkCommand()

			elif self.notebook.select() == ".!frame2":
				# In array control context:
				self._sendArrayCommand()

		except:
			ep.errorPopup("Error in FCCControlBar")

		# End _onEnter =========================================================


	def _fileChooser(self, event = None): # ====================================
		
		try:
			
			# Disable buttons while choosing file:
			self.fileChooserButton.config(state = Tk.DISABLED)
			self.bootloaderStartStopButton.config(state = Tk.DISABLED)

			self.bootloaderTargetVar.set(
				tkinter.filedialog.askopenfilename(
					initialdir = os.getcwd(), # Get current working directory
					title = "Choose file",
					filetypes = (("Binary files","*.bin"),("All files","*.*"))
				)
			)	

			self.chosenFileEntry.xview_moveto(1.0)

			if len(self.bootloaderTargetVar.get()) > 0:

				self.fileSize = os.path.getsize(self.bootloaderTargetVar.get())

				# Move file to current directory:
				newFileName = os.getcwd() + \
						os.sep + \
						os.path.basename(self.bootloaderTargetVar.get())

				sh.copyfile(
					self.bootloaderTargetVar.get(), 
					newFileName
				)
				
				self.targetFile = os.path.basename(newFileName)
				

				self._printM(
					"Target binary:\n\tFile: {}"\
					"\n\tSize: {} bytes"\
					"\n\tCopied as \"{}\" for flashing".\
					format(
						self.bootloaderTargetVar.get(), 
						self.fileSize,
						self.targetFile
					)
				)
			
			# Re-enable button:
			self.fileChooserButton.config(state = Tk.NORMAL)
			self.bootloaderStartStopButton.config(state = Tk.NORMAL)
		
		except:
			ep.errorPopup("Error in FCCControlBar")

		# End _fileChooser =====================================================

	def _shutdown(self, event = None): # =======================================
		
		try:
		
			self.commandQueue.put_nowait((mw.COMMUNICATOR, cm.REBOOT, cm.ALL))	

		except:
			ep.errorPopup("Error in FCCControlBar")

		# End _shutdown ========================================================

	def _printM(self, message, tag = 'S'): # ===================================

		try:

			self.printQueue.put_nowait(("[CM][CB] " + message, tag))

		except:
			ep.errorPopup("Error in FCCControlBar")
		# ======================================================================

## TEST SUITE ##################################################################

if __name__ is '__main__':

	import threading as tr
	import queue
	import time as tm

	frame = Tk.Frame(None)
	frame.master.title("FCMkII FCCControlBar Unit Test")
	frame.master.minsize(width = 800, height = 10)

	commandQueue = queue.Queue()

	class DummySource:
		
		def getSelection(self):
			print(("[ss] Returning..{}".format([1,2,3,4])))
			return [1,2,3,4]

	cb = FCCControlBar(frame, DummySource(), commandQueue)
	
	def _testRoutine(cb, q):
		
		tm.sleep(.2)
		cb.setStatus(cm.CONNECTED)
		tm.sleep(.2)
		cb.setStatus(cm.DISCONNECTED)
		tm.sleep(.2)
		cb.setStatus(cm.CONNECTED)

		while(True):
			try:
				print((q.get_nowait()))
			except queue.Empty:
				pass

	testThread = tr.Thread(
		target = _testRoutine,
		args = (cb, commandQueue)
	)
	testThread.setDaemon(True)
	testThread.start()

	frame.pack()

	frame.mainloop()
