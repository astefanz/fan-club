################################################################################
## Project: Fan Club Mark II "Master" # File: FCCStatusBar.py                 ##
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
Display connection status

"""
################################################################################


## DEPENDENCIES ################################################################

# GUI:
#from mttkinter import mtTkinter as Tk
import tkinter as Tk
import tkinter.messagebox
import tkinter.font

# System:
import os # Get current working directory & check file names
import sys # Exception handling
import inspect # get line number for debugging
import traceback

# FCMkII:
import FCSlave as sv
import FCCommunicator as cm


# Status data tuple indices:
# Form: (LABEL_TEXT, LABEL_COLOR, BUTTON_TEXT, BUTTON_STATE, BUTTON_COMMAND)
#			0			1			2			3				4
LABEL_TEXT = 0
LABEL_COLOR = 1
BUTTON_TEXT = 2
BUTTON_STATE = 3
BUTTON_COMMAND = 4

# Broadcast status color codes (Obsolete):
GREEN = 1
GREEN2 = 2
BLUE = 3
RED = 0


## AUXILIARY DEFINITIONS #######################################################

## CLASS DEFINITION ############################################################

class FCCStatusBar(Tk.Frame): # ================================================

	def __init__(self, master, connectMethod, disconnectMethod): # =============
		try:
			# CONFIGURE ------------------------------------------------------------
			Tk.Frame.__init__(self, master)
			self.background = "#d3d3d3"
			self.foreground = "black"
			self.config(bg = self.background, relief = Tk.SUNKEN, borderwidth = 2)
		
			self.connectMethod = connectMethod
			self.disconnectMethod = disconnectMethod
			
			def noMethod():
				pass
			
			self.noMethod = noMethod

			# BUILD ----------------------------------------------------------------
			self.statusFrame = Tk.Frame(self, relief = Tk.GROOVE, borderwidth = 1,
				 bg=self.background, height = 10)
				
			self.statusFrame.pack(
				fill = Tk.X, expand = False, side =Tk.BOTTOM, anchor = 's')

			# TRACKED VARIABLES ....................................................
			
			# Slave data:
			# Note: store data as dictionary of the form INDEX:STATUS
			self.slaves = {}

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

			# MASTER CONNECTION ................................................ 
			self.connectionButton = Tk.Button(
				self.statusFrame,
				bg = self.background,
				fg = self.foreground,
				highlightbackground = self.background,
				text = "[NO_COMMAND]",
				width = 10
			)
			self.connectionButton.pack(side = Tk.RIGHT)

			self.statusFont = ('TkFixedFont','12','bold')
		
			self.statusData = {}

			self.statusData[cm.DISCONNECTED] = \
				("DISCONNECTED",'#560e0e',"Connect", Tk.NORMAL,
					self.connectMethod)

			self.statusData[cm.DISCONNECTING] = \
				("DISCONNECTING", self.statusData[cm.DISCONNECTED][LABEL_COLOR],
					"Disconnecting", Tk.DISABLED, self.noMethod)

			self.statusData[cm.CONNECTED] = \
				("CONNECTED",  '#0e4707', "Disconnect", Tk.NORMAL, 
					self.disconnectMethod)

			self.statusData[cm.CONNECTING] = \
				("CONNECTING", self.statusData[cm.CONNECTED][LABEL_COLOR], 
					"Connecting", Tk.DISABLED, self.noMethod)

			self.networkStatusFrame = Tk.Frame(
				self.statusFrame,
				bg = self.background,
				relief = Tk.SUNKEN,
				bd = 1
			)
			
			self.networkStatusLabel = Tk.Label(
				self.networkStatusFrame,
				bg = self.background,
				fg = self.foreground,
				text = "Network: "
			)
			self.networkStatusLabel.pack(side = Tk.LEFT)
			
			self.networkStatusDisplayLabel = Tk.Label(
				self.networkStatusFrame,
				bg = self.background,
				fg = self.foreground,
				text = "[NO_STATUS]",
				font = self.statusFont,
				width = 17
			)
			self.networkStatusDisplayLabel.pack(side = Tk.RIGHT)

			self.networkStatusLabel.pack(side = Tk.LEFT)
			self.networkStatusFrame.pack(side = Tk.RIGHT)

		except Exception as e: # Print uncaught exceptions
			tkinter.messagebox.showerror(title = "FCMkII Fatal Error",
				message = "Warning: Uncaught exception in "\
				"StatusBar constructor: \"{}\"".\
				format(traceback.format_exc()))
		
		# End __init__ =========================================================

	def addSlaves(self, newSlaves): # ==========================================

		for newSlave in newSlaves:
			
			index = newSlave[cm.INDEX]
			status = newSlave[cm.STATUS]

			self.slaves[index] = status

			self.statusInts[status] += 1
			self.statusVars[status].set(self.statusInts[status])

			self.totalSlaves += 1
			self.totalSlavesVar.set(self.totalSlaves)

		# End addSlaves ========================================================

	def setSlaveStatus(self, index, newStatus): # ==============================

		previousStatus = self.slaves[index]

		if previousStatus == newStatus:
			return

		else:
			self.slaves[index] = newStatus

			self.statusInts[previousStatus] -= 1
			self.statusVars[previousStatus].set(self.statusInts[previousStatus])

			self.statusInts[newStatus] += 1
			self.statusVars[newStatus].set(self.statusInts[newStatus])

		# End setSlaveStatus ===================================================
	
	def updateSlaves(self, slaves): # ==========================================
		
		for slave in slaves:
			self.setSlaveStatus(slave[cm.INDEX], slave[cm.STATUS])

		# End updateSlaves =====================================================


	def remove(self, index): # =================================================
		
		status = self.slaves[index]
		self.statusInts[status] -= 1
		self.statusVars[status].set(self.statusInts[status])

		self.totalSlaves -= 1
		self.totalSlavesVar.set(self.totalSlaves)

		del self.slaves[index]

		# End remove ===========================================================

	def clear(self): # =========================================================

		for status in self.statusInts:
			self.statusInts[status] = 0
			self.statusVars[status].set(0)

		self.totalSlaves = 0
		self.totalSlavesVar.set(0)

		del self.slaves
		self.slaves = {}

		# End clear ============================================================

	def setStatus(self, newStatus): # ==========================================

		# Set label
		self.networkStatusDisplayLabel.config(
			text = self.statusData[newStatus][LABEL_TEXT],
			fg = self.statusData[newStatus][LABEL_COLOR]
		)
		
		# Set button
		self.connectionButton.config(
			text = self.statusData[newStatus][BUTTON_TEXT],
			state = self.statusData[newStatus][BUTTON_STATE],
			command = self.statusData[newStatus][BUTTON_COMMAND]
		)

		# Update slave count, if applicable
		if newStatus is cm.DISCONNECTED:
			self.clear()

		# End setStatus ========================================================

## TEST SUITE ##################################################################

if __name__ == "__main__":

	import threading as tr
	import time as tm

	def c():	
		print("Connect called")

	def d():
		print("Disconnect called")

	testWindow = Tk.Frame(None)
	testWindow.master.title("FC Communicator Status Bar Unit Test")
	testWindow.master.minsize(width = 800, height = 10)
	widget = FCCStatusBar(testWindow, c, d)
	testWindow.pack(fill = Tk.X, expand = True)

	def _testRoutine(sbar): # ----
		
		sbar.setStatus(cm.CONNECTING)
		tm.sleep(1)
		sbar.setStatus(cm.CONNECTED)

		for i in range(10):
			sbar.add(i, sv.KNOWN)
			tm.sleep(0.1)

		for i in range(10):
			sbar.setSlaveStatus(i, sv.DISCONNECTED)
			tm.sleep(0.1)

		for i in range(10):
			sbar.remove(i)
			tm.sleep(0.1)

		tm.sleep(.5)

		for i in range(10):
			sbar.add(i, sv.AVAILABLE)
	
		tm.sleep(.5)
		sbar.clear()
		
		for i in range(10):
			sbar.add(i, sv.CONNECTED)
			tm.sleep(0.1)

		tm.sleep(1)
		sbar.setStatus(cm.DISCONNECTING)
		tm.sleep(1)
		sbar.setStatus(cm.DISCONNECTED)


		# End _testRoutine -------

	testThread = tr.Thread(target = _testRoutine, args = (widget,))
	testThread.setDaemon(True)
	testThread.start()

	testWindow.mainloop()


