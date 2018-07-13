################################################################################
## Project: Fan Club Mark II "Master" # File: BasicController.py              ##
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
Custom Tkinter widget to send simple control commands to the fan array.

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
import os # Get current working directory & check file names
import sys # Exception handling
import inspect # get line number for debugging
import traceback

# FCMkII:
import FCSlave as sv

## CONSTANTS ###################################################################

## CLASS DEFINITION ############################################################

class BasicController(Tk.Frame): # =============================================

	# NOTE: Slaves are stored as: 
	# [Index + 1, MAC, status, fans, version, iid]
	#          0    1       2     3    4      5

	def __init__(self, master):
	#	self, master, slaves,  inputCommandQueue, inputMatrixQueue, printQueue):
		try:
			
			# CONFIGURE --------------------------------------------------------
			Tk.Frame.__init__(self, master)
			self.background = "#d3d3d3"
			self.foreground = "black"
			self.config(
				bg = self.background, relief = Tk.SUNKEN, borderwidth = 2)
		
			# BUILD ------------------------------------------------------------
			
			self.controlFrame = Tk.Frame(self, 
				relief = Tk.GROOVE, borderwidth = 1,
				bg=self.background)

			self.controlFrame.pack(fill = Tk.X, expand = False)

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



			# DATA -------------------------------------------------------------
			self.slaves = []
			self.numSlaves = 0
		
		except Exception as e: # Print uncaught exceptions
			tkMessageBox.showerror(title = "FCMkII Fatal Error",
				message = "Warning: Uncaught exception in "\
				"SList constructor: \"{}\"".\
				format(traceback.format_exc()))
		
		# End __init__ =========================================================

	def add(self, newSlave): # =================================================
		# Expected format:
		# (MAC, Status, Fans, Version)
	
		pass

		# End add ==============================================================

	# WIDGET CALLBACKS ---------------------------------------------------------
	
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

	def selectAllSlaves(self): # ===============================================
		# ABOUT: To be bound to the "Select All" button (selects all fans in all
		# Slaves)
		
		self.printMain("WARNING: BUTTON NOT IMPLEMENTED", "E")
		# End selectAllSlaves ==================================================

	def deselectAllSlaves(self): # =============================================
		# ABOUT: To be bound to the "Deselect All" button (deselects all fans 
		# in all Slaves)
		
		self.printMain("WARNING: BUTTON NOT IMPLEMENTED", "E")
		
		# End deselectAllSlaves ================================================

	def _shutdownButton(self): # ===============================================
		# ABOUT: To be bound to shutdownButton



		self.printMain("WARNING: BUTTON NOT IMPLEMENTED", "E")

	def _disconnectAllButton(self): # ===============================================
		# ABOUT: To be bound to disconnectAllButton

		self.printMain("WARNING: BUTTON NOT IMPLEMENTED", "E")

	def _connectAllSlaves(self): # =============================================
		# ABOUT: Connect to all AVAILABLE Slaves, if any.

		self.printMain("WARNING: BUTTON NOT IMPLEMENTED", "E")

		# End _connectAllSlaves ================================================

	def _send(self, event = None): # ===========================================
		
		self.printMain("WARNING: SEND BUTTON NOT IMPLEMENTED", "E")

		# End _send ============================================================		
