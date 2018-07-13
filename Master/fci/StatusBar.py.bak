################################################################################
## Project: Fan Club Mark II "Master" # File: StatusBar.py                    ##
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
Custom Tkinter widget to display general parameters

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



# Broadcast status color codes:
GREEN = 1
GREEN2 = 2
BLUE = 3
RED = 0


class StatusBar(Tk.Frame): # ===================================================

	def __init__(self, master, version): # =====================================
		try:
			# CONFIGURE ------------------------------------------------------------
			Tk.Frame.__init__(self, master)
			self.background = "#d3d3d3"
			self.foreground = "black"
			self.config(bg = self.background, relief = Tk.SUNKEN, borderwidth = 2)
		
			# BUILD ----------------------------------------------------------------
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
			
		except Exception as e: # Print uncaught exceptions
			tkMessageBox.showerror(title = "FCMkII Fatal Error",
				message = "Warning: Uncaught exception in "\
				"StatusBar constructor: \"{}\"".\
				format(traceback.format_exc()))
		
		# End __init__ =========================================================
