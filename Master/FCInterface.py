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

import Tkinter as Tk # GUI
import tkFont
import ttk # "Notebooks"
import threading


import Communicator
import Profiler

## CONSTANT VALUES #############################################################      


## CLASS DEFINITION ############################################################

class FCInterface(Tk.Frame):      

	def __init__(self, version, master=None): # ===================================
		Tk.Frame.__init__(self, master)

		# CONFIGURE MAIN WINDOW = = = = = = = = = = = = = = = = = = = = = = = = 

		# Deactivate resizing:
		#self.master.resizable(False,False)


		# Set title:
		self.master.title("Fan Club MkII")

		# Set background:
		self.background = "#e2e2e2"
		self.config(bg = self.background)

		# Set debug foreground:
		self.debugColor = "#ff007f"

		# CREATE COMPONENTS = = = = = = = = = = = = = = = = = = = = = = = = = = 

		# CONTROL --------------------------------------------------------------
		self.controlFrame = Tk.Frame(self, relief = Tk.GROOVE, borderwidth = 1,
			 bg=self.background)

		self.l1 = Tk.Label(self.controlFrame, text = "Controls:" , bg = self.background)
		self.l1.pack(side = Tk.LEFT)

		self.b1 = Tk.Button(self.controlFrame, text='Button', bg = self.background)
		self.b1.pack(side = Tk.LEFT)

		self.b2 = Tk.Button(self.controlFrame, text='Button', bg = self.background)
		self.b2.pack(side = Tk.LEFT)

		self.b3 = Tk.Button(self.controlFrame, text='Test')
		self.b3.pack(side = Tk.RIGHT)

		self.controlFrame.pack(fill = Tk.X, expand = False)

		# ARRAY ----------------------------------------------------------------
		self.arrayFrame = Tk.Frame(self, relief = Tk.GROOVE, borderwidth = 1,
			width = 50, height = 300, bg=self.background)


		self.arrayFrame.pack(fill = Tk.BOTH, expand = True)

		# TERMINAL -------------------------------------------------------------
		self.terminalFrame = Tk.Frame(self, relief = Tk.GROOVE, borderwidth = 1,
			bg = self.background)

		self.terminal = ttk.Notebook(self.terminalFrame)
		

		# Autoscroll checkbox:
		self.autoscrollVar = Tk.IntVar()

		self.autoscrollButton = Tk.Checkbutton(self.terminalFrame, 
			text ="Auto-scroll", variable = self.autoscrollVar, 
			bg = self.background)

		# Debug checkbox:
		self.debugVar = Tk.IntVar()

		self.debugButton = Tk.Checkbutton(self.terminalFrame, 
			text ="Debug prints", variable = self.debugVar, 
			bg = self.background)

		# Terminal print:
		self.terminalVar = Tk.IntVar()

		self.terminalButton = Tk.Checkbutton(self.terminalFrame, 
			text ="Terminal output", variable = self.terminalVar, 
			bg = self.background)

		# MAIN TERMINAL - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
		self.mainTerminal = ttk.Frame(self.terminal)
		self.mainTLock = threading.Lock()
		self.mainTText = Tk.Text(self.mainTerminal, height = 10, width = 120, 
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

		# SLAVE TERMINAL - - - - - - - - - - - - - - - - - - - - - - - - - - - -
		self.slavesTerminal = ttk.Frame(self.terminal)
		self.slavesTLock = threading.Lock()
		self.slavesTText = Tk.Text(self.slavesTerminal, height = 10, width = 120, 
			fg = "black", bg= "white", font = ('TkFixedFont'),
			selectbackground = "#f4f1be",
			state = Tk.DISABLED)
		self.slavesTScrollbar = Tk.Scrollbar(self.slavesTerminal)
		self.slavesTScrollbar.pack(side = Tk.RIGHT, fill=Tk.Y)
		self.slavesTScrollbar.config(command=self.slavesTText.yview)
		self.slavesTText.config(yscrollcommand = self.slavesTScrollbar.set)
		self.slavesTText.bind("<1>", 
			lambda event: self.slavesTText.focus_set())
		self.slavesTText.pack(fill =Tk.BOTH, expand = True)
		# Configure tags:
		self.slavesTText.tag_config("S")
		self.slavesTText.tag_config("G", foreground = "#168e07")
		self.slavesTText.tag_config(\
			"W", underline = 1, foreground = "#e5780b")
		self.slavesTText.tag_config(\
			"E", underline = 1, foreground = "red", background = "#510000")
		self.slavesTText.tag_config(\
			"B", foreground = "blue")
		self.slavesTText.tag_config(\
			"D", foreground = self.debugColor)


		# LISTENER TERMINAL - - - - - - - - - - - - - - - - - - - - - - - - - - 
		self.listenerTerminal = ttk.Frame(self.terminal)
		self.listenerTLock = threading.Lock()
		self.listenerTText = Tk.Text(self.listenerTerminal, height = 10, 
			width = 120, 
			fg = "#34635f", bg="#bcdbd6", font = ('TkFixedFont'),
			selectbackground = "#a2c1bc", selectforeground = "white",
			state = Tk.DISABLED)
		self.listenerTScrollbar = Tk.Scrollbar(self.listenerTerminal)
		self.listenerTScrollbar.pack(side = Tk.RIGHT, fill=Tk.Y)
		self.listenerTScrollbar.config(command=self.listenerTText.yview)
		self.listenerTText.config(yscrollcommand = self.listenerTScrollbar.set)
		self.listenerTText.bind("<1>", 
			lambda event: self.listenerTText.focus_set())
		self.listenerTText.pack(fill =Tk.BOTH, expand = True)
		# Configure tags:
		self.listenerTText.tag_config("S")
		self.listenerTText.tag_config("G", foreground = "#389b1d")
		self.listenerTText.tag_config(\
			"W", underline = 1, foreground = "orange")
		self.listenerTText.tag_config(\
			"E", underline = 1, foreground = "red", background = "#510000")
		self.listenerTText.tag_config(\
			"D", foreground = self.debugColor)


		# BROADCAST TERMINAL - - - - - - - - - - - - - - - - - - - - - - - - - -
		self.broadcastTerminal = ttk.Frame(self.terminal)
		self.broadcastTLock = threading.Lock()
		self.broadcastTText = Tk.Text(self.broadcastTerminal, height = 10, 
			selectbackground = "#8b96a8",
			width = 120, 
			fg = "#004763", bg="#b5bece", font = ('TkFixedFont'),
			state = Tk.DISABLED)
		self.broadcastTScrollbar = Tk.Scrollbar(self.broadcastTerminal)
		self.broadcastTScrollbar.pack(side = Tk.RIGHT, fill=Tk.Y)
		self.broadcastTScrollbar.config(command=self.broadcastTText.yview)
		self.broadcastTText.config(yscrollcommand = self.broadcastTScrollbar.set)
		self.broadcastTText.bind("<1>", 
			lambda event: self.broadcastTText.focus_set())
		self.broadcastTText.pack(fill =Tk.BOTH, expand = True)
		# Configure tags:
		self.broadcastTText.tag_config("S")
		self.broadcastTText.tag_config("G", foreground = "#008c15")
		self.broadcastTText.tag_config(\
			"W", underline = 1, foreground = "orange")
		self.broadcastTText.tag_config(\
			"E", underline = 1, foreground = "red",	background = "#510000")
		self.broadcastTText.tag_config(\
			"D", foreground = self.debugColor)

		# TERMINAL SETUP - - - - - - - - - - - - - - - - - - - - - - - - - - - -
		self.terminal.add(self.mainTerminal, text = 'Main')
		self.terminal.add(self.slavesTerminal, text = 'Slaves')
		self.terminal.add(self.listenerTerminal, text = 'Listener')
		self.terminal.add(self.broadcastTerminal, text = 'Broadcast')

		self.terminal.pack(fill = Tk.BOTH, expand = True)
		self.autoscrollButton.pack(side = Tk.LEFT)
		self.debugButton.pack(side = Tk.LEFT)
		self.terminalButton.pack(side = Tk.LEFT)
		self.terminalFrame.pack(fill = Tk.BOTH, expand = False)
		self.autoscrollButton.select()




		# STATUS ---------------------------------------------------------------
		self.statusFrame = Tk.Frame(self, relief = Tk.GROOVE, borderwidth = 1,
			 bg=self.background)

		self.versionLabel = Tk.Label(self.statusFrame, text = "Version: " + version,
			bg = self.background, fg = "#424242")
		self.versionLabel.pack(side = Tk.RIGHT)

		self.statusFrame.pack(fill = Tk.X, expand = False)

		# PACK -----------------------------------------------------------------

		self.pack(fill = Tk.BOTH, expand = True)

		# Center starting place:
		#                         Y-place
		#                      X-place  |       
		#                    Height  |  |
		#                  Width  |  |  |
		#                      |  |  |  |
		self.master.geometry('%dx%d+%d+%d' % (800, 650, \
			(self.master.winfo_screenwidth()/5),      \
			(self.master.winfo_screenheight()/8)        \
			)                                           \
		)
		
		self.printMain("Fan Club MkII Interface initialized")
		


	# End constructor ==========================================================

	def printMain(self, output, tag = "S"): # =========================
		# ABOUT: Print to main terminal window in a thread-safe manner.
		# PARAMETERS:
		# - output: str, text to print.
		# - tag: str, single character representing type of text to be prin-
		#	ted. Can be "S" for "Standard," "W" for "Warning,"  "E" for Er-
		#	ror or "G" for "Green". Defaults to "S"

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
				self.terminal.select(0)

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


	def printSlave(self, slave, output, tag = "S"): # =========================
		# ABOUT: Print to slave terminal window in a thread-safe manner.
		# PARAMETERS:
		# - mac: Slave object about which to print
		# - output: str, text to print.
		# - tag: str, single character representing type of text to be prin-
		#	ted. Can be "S" for "Standard," "W" for "Warning,"  "E" for Er-
		#	ror or "G" for "Green". Defaults to "S"

		if self.terminalVar.get() == 0:
			return

		self.slavesTLock.acquire()

		try: # NOTE: Use try/finally to guarantee lock release.

			# Check for debug tag:
			if tag is "D" and self.debugVar.get() == 0:
				# Do not print if the debug variable is set to 0
				return

			# Switch focus to this tab in case of errors of warnings:
			if tag is "E":
				self.terminal.select(1)

			self.slavesTText.config(state = Tk.NORMAL)
				# Must change state to add text.

			# Add MAC address first:
			self.slavesTText.insert(Tk.END, 
				"[{}][{}] ".format(slave.mac, slave.exchange), "B")
			self.slavesTText.insert(Tk.END, output + "\n", tag)
			self.slavesTText.config(state = Tk.DISABLED)

			# Check for auto scroll:
			if self.autoscrollVar.get() == 1:
				self.slavesTText.see("end")

		finally:
			self.slavesTLock.acquire(False)
			self.slavesTLock.release()

		# End printSlave =======================================================

	def printListener(self, output, tag = "S"): # =========================
		# ABOUT: Print to listener terminal window in a thread-safe manner.
		# PARAMETERS:
		# - output: str, text to print.
		# - tag: str, single character representing type of text to be prin-
		#	ted. Can be "S" for "Standard," "W" for "Warning,"  "E" for Er-
		#	ror or "G" for "Green". Defaults to "S"

		if self.terminalVar.get() == 0:
			return

		self.listenerTLock.acquire()

		try: # NOTE: Use try/finally to guarantee lock release.

			# Check for debug tag:
			if tag is "D" and self.debugVar.get() == 0:
				# Do not print if the debug variable is set to 0
				return

			# Switch focus to this tab in case of errors of warnings:
			if tag is "E":
				self.terminal.select(2)

			self.listenerTText.config(state = Tk.NORMAL)
				# Must change state to add text.
			self.listenerTText.insert(Tk.END, "[LT] " + output + "\n", tag)
			self.listenerTText.config(state = Tk.DISABLED)

			# Check for auto scroll:
			if self.autoscrollVar.get() == 1:
				self.listenerTText.see("end")

		finally:
			self.listenerTLock.acquire(False)
			self.listenerTLock.release()

		# End printListener ====================================================

	def printBroadcast(self, output, tag = "S"): # =========================
		# ABOUT: Print to broadcast terminal window in a thread-safe manner.
		# PARAMETERS:
		# - output: str, text to print.
		# - tag: str, single character representing type of text to be prin-
		#	ted. Can be "S" for "Standard," "W" for "Warning,"  "E" for Er-
		#	ror or "G" for "Green". Defaults to "S"

		if self.terminalVar.get() == 0:
			return

		self.broadcastTLock.acquire()

		try: # NOTE: Use try/finally to guarantee lock release.

			# Check for debug tag:
			if tag is "D" and self.debugVar.get() == 0:
				# Do not print if the debug variable is set to 0
				return

			# Switch focus to this tab in case of errors of warnings:
			if tag is "E":
				self.terminal.select(3)

			self.broadcastTText.config(state = Tk.NORMAL)
				# Must change state to add text.
			self.broadcastTText.insert(Tk.END, output + "\n", tag)
			self.broadcastTText.config(state = Tk.DISABLED)

			# Check for auto scroll:
			if self.autoscrollVar.get() == 1:
				self.broadcastTText.see("end")

		finally:
			self.broadcastTLock.acquire(False)
			self.broadcastTLock.release()

		# End printBroadcast ===================================================

	def dataLog(mac, rpm, dc):
		# Temporary dataLog function for Communicator.
		pass




