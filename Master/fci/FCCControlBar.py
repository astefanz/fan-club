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
import tkinter.font
import tkinter.ttk # "Notebooks"

# System:
import os # Get current working directory & check file names
import sys # Exception handling
import inspect # get line number for debugging
import traceback

# FCMkII:
import FCSlave as sv
import FCCommunicator as cm
import auxiliary.errorPopup as ep
import FCMainWindow as mw

## CLASS DEFINITION ############################################################

class FCCControlBar(Tk.Frame, object):

	def __init__(self, master, selectionSource, commandQueue): # ===============

		try:

			# CONFIGURE --------------------------------------------------------
			self.selectionSource = selectionSource
			self.commandQueue = commandQueue

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

			self.notebook.pack(side = Tk.TOP, fill = Tk.X, expand = True)

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
			self.targetMenuLabel = Tk.Label(
				self.networkControlFrame,
				bg = self.background,
				fg = self.foreground,
				text = "Target: "
			)

			self.targetMenuLabel.pack(side = Tk.LEFT)

			# Menu:

			self.selectedTarget = Tk.StringVar()
			self.selectedTarget.set("All")
			self.targetMenu = Tk.OptionMenu(self.networkControlFrame, 
				self.selectedTarget,
				"Selected", 
				"All",
			)

			self.targetMenu.pack(side = Tk.LEFT)

			self.targetMenu.config(
				width = 10,
				background = self.background,
				highlightbackground = self.background,
				foreground = self.foreground
			)

			self.activeWidgets.append(self.targetMenu)
			
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

			self.sendButton = Tk.Button(
				self.networkControlFrame,
				bg = self.background,
				fg = self.foreground,
				text = "Send",
				command = self._send,
				highlightbackground = self.background
				)

			self.sendButton.pack(side = Tk.LEFT)

			self.activeWidgets.append(self.sendButton)

			# Shutdown button ..................................................

			self.shutdownButtonPadding = Tk.Frame(
				self.networkControlFrame,
				bg = self.background,
				width = 40
				)

			self.shutdownButtonPadding.pack(side = Tk.LEFT)

			self.shutdownButton = Tk.Button(
				self.networkControlFrame,
				bg = self.background,
				fg = self.foreground,
				text = "SHUTDOWN",
				font = ('TkDefaultFont','12','bold'),
				command = self._shutdown,
				highlightbackground = 'red'
				)

			self.shutdownButton.pack(side = Tk.RIGHT)

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
			self.quickControlFrame = Tk.Frame(
				None,
				background = self.background
			)
			self.quickControlFrame.pack(fill = Tk.BOTH, expand = True)

			self.notebook.add(
				self.quickControlFrame,
				text = "Quick Array Control",
				state = Tk.DISABLED
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

	def _send(self, event = None): # ===========================================
		

		# Get targets:
		if self.selectedTarget.get() == "All":
			targets = [cm.ALL]
		else:
			targets = map(lambda x: x-1,self.selectionSource.getSelection())
	
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
			self.commandQueue.put_nowait((mw.COMMUNICATOR, commandCode, target))

		# End _send ============================================================

	def _shutdown(self, event = None): # =======================================
		
		self.commandQueue.put_nowait((mw.COMMUNICATOR, cm.REBOOT, cm.ALL))

		# End _shutdown ========================================================

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