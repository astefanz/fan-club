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


# FCMkII:
import FCSlave as sv
import FCCommunicator as cm
import auxiliary.errorPopup as ep
import FCMainWindow as mw

## AUXILIARY DEFINITIONS #######################################################

# Menu items:
SET_DC = "DC%"
SET_RPM = "RPM"

# Bootloader states:
FLASHING = 1
NOT_FLASHING = 0

## CLASS DEFINITION ############################################################

class FCCControlBar(Tk.Frame, object):

	def __init__(
		self, 
		master, 
		maxFans, 
		selectionSource, 
		commandQueue, 
		printQueue
		): # ===================================================================

		self.canPrint = False

		try:

			# CONFIGURE --------------------------------------------------------
			self.maxFans = maxFans
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

			self.status = cm.DISCONNECTED

			""" ----------------------------------------------------------------
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
						text = "{}".format(fan+1),
						font = ('TkFixedFont','8'),
						bg = self.background,
						fg = self.foreground,
						variable = self.fanBooleanVars[fan]
					),
				)
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
