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
import Queue
import time
import traceback

import Communicator
import Slave
import Profiler

## CONSTANT VALUES #############################################################      

## AUXILIARY CLASSES ###########################################################

class SlaveDisplay(Tk.Frame):

	def __init__(self, master, name, mac, initialStatus, maxFans): # ===========

		self.background = "#d3d3d3"
		self.mac = mac
		self.maxFans = maxFans

		# CONFIGURE ------------------------------------------------------------
		Tk.Frame.__init__(self, master)
		self.config(bg = self.background, relief = Tk.SUNKEN, borderwidth = 2)

		# ADD LABELS -----------------------------------------------------------

		# GENERAL INFORMATION - - - - - - - - - - - - - - - - - - - - - - - - - 

		self.generalFrame = Tk.Frame(self, bg = self.background)
		self.generalFrame.pack(fill = Tk.X)

		# ......................................................................
		self.nameVar = Tk.StringVar()
		self.nameVar.set('- "' + name + '"')
		self.nameLabel = Tk.Label(self.generalFrame, textvariable = self.nameVar,
			fg = "black", relief = Tk.SUNKEN, bd = 1, font = 'TkFixedFont 12 bold',
			bg = self.background)
		self.nameLabel.pack(side = Tk.LEFT)

		# ......................................................................
		self.macVar = Tk.StringVar()
		self.macVar.set(" ["+mac+"] ")

		self.macLabel = Tk.Label(self.generalFrame, textvariable = self.macVar, 
			fg = "blue",relief = Tk.SUNKEN, bd = 1,
			bg = self.background)
		self.macLabel.pack(side = Tk.LEFT)

		# ......................................................................
		self.statusVar = Tk.StringVar()
		self.statusVar.set(initialStatus)

		self.statusLabel = Tk.Label(self.generalFrame, 
			textvariable = self.statusVar, font = 'TkFixedFont 12 bold',
			bg = self.background, relief = Tk.SUNKEN, bd = 1)
		self.statusLabel.pack(side = Tk.LEFT)

		# ......................................................................
		self.ipVar = Tk.StringVar()
		self.ipVar.set("IP: [NONE]")

		self.ipLabel = Tk.Label(self.generalFrame, textvariable = self.ipVar,
			bg = self.background, relief = Tk.SUNKEN, bd = 1)
		self.ipLabel.pack(side = Tk.LEFT)

		# ......................................................................
		self.portVar = Tk.StringVar()
		self.portVar.set("Port: [NONE]")

		self.portLabel = Tk.Label(self.generalFrame, 
			textvariable = self.portVar, relief = Tk.SUNKEN, bd = 1,
			bg = self.background)
		self.portLabel.pack(side = Tk.LEFT)

		# ......................................................................
		self.exchangeVar = Tk.StringVar()
		self.exchangeVar.set("I: [NONE]")
		self.exchangeLabel = Tk.Label(self.generalFrame, 
			textvariable = self.exchangeVar, relief = Tk.SUNKEN, bd = 1,
			bg = self.background)
		self.exchangeLabel.pack(side = Tk.LEFT)

		# ......................................................................
		self.activeFansLabel = Tk.Label(self.generalFrame, 
			text = "Active Fans: [N\A]", relief = Tk.SUNKEN, bd = 1,
			bg = self.background)
		self.activeFansLabel.pack(side = Tk.LEFT)

		# FAN ARRAY - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
		self.fanArrayFrame = Tk.Frame(self, bg = self.background)
		self.fanArrayFrame.pack(fill = Tk.X)

		self.fans = []
		for i in range(maxFans):
			self.fans.append(FanDisplay(self))
		
		self.pack(fill = Tk.X)

		# End __init__ =========================================================

	def update(self, data): # ==================================================
		# ABOUT: Update target Slave's Display according to given data.
		# PARAMETER:
		# - data: tuple w/ as many elements as in Slave update (see Communicator
		#	Slave routine)

		# Update each parameter accordingly = = = = = = = = = = = = = = = = = = 

		# name -----------------------------------------------------------------
		pass
		# mac ------------------------------------------------------------------
		pass
		# status ---------------------------------------------------------------
		if data[2] == Slave.DISCONNECTED:
			self.statusVar.set("DISCONNECTED")
			self.statusLabel.config(fg = "red")

		elif data[2] == Slave.CONNECTED:
			self.statusVar.set("CONNECTED")
			self.statusLabel.config(fg = "#34c111")

		elif data[2] == Slave.KNOWN:
			self.statusVar.set("KNOWN")
			self.statusLabel.config(fg = "yellow")

		elif data[2] == Slave.BUSY:
			self.statusVar.set("BUSY")
			self.statusLabel.config(fg = "blue")

		elif data[2] == Slave.AVAILABLE:
			self.statusVar.set("AVAILABLE")
			self.statusLabel.config(fg = "yellow")

		# fans -----------------------------------------------------------------
		pass # data[3]
		# activeFans -----------------------------------------------------------
		pass # data[4]
		# ip -------------------------------------------------------------------
		if data[5] == "None":
			self.ipVar.set("[NO IP]")
		else:
			self.ipVar.set(data[5])
		# misoP ----------------------------------------------------------------
		if data[6] == "None":
			self.portVar.set("[NO PORT]")
		else:
			self.portVar.set(data[6])
		# exchange -------------------------------------------------------------
		self.exchangeVar.set("I: " + data[8])

        # End update ===========================================================


class FanDisplay(Tk.Frame):
	# ABOUT: Graphically represent each fan

	def __init__(self, master): # ==============================================

		self.background = "red"
		size = 20 # px per side

		# CONFIGURE FRAME = = = = = = = = = = = = = = = = = = = = = = = = = = = 
		Tk.Frame.__init__(self, master = master, bg = "black")
		self.config(relief = Tk.SUNKEN, borderwidth = 1)

		# CONFIGURE CANVAS = = = = = = = = = = = = = = = = = = = = = = = = = = =
		self.canvas = Tk.Canvas(self, bg = self.background, 
			width = size, height = size)


		# PACK = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
		self.pack(side = Tk.LEFT, expand = False)
		self.canvas.pack()



## CLASS DEFINITION ############################################################

class FCInterface(Tk.Frame):      

	def __init__(self, version, master=None): # ================================
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

		# ARRAY ----------------------------------------------------------------
		self.arrayFrame = Tk.Frame(self, relief = Tk.GROOVE, borderwidth = 1,
			width = 50, height = 300, bg=self.background)

		self.arrayFrameLabelFrame = Tk.Label(self.arrayFrame,
			bg = self.background)

		self.arrayFrameLabel = Tk.Label(self.arrayFrameLabelFrame, 
			text = "Slaves", bg = self.background)
		self.arrayFrameLabel.pack()

		self.arrayFrameLabelFrame.pack(fill = Tk.X)


		self.arrayFrame.pack(fill = Tk.BOTH, expand = True)

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
		self.terminalVar.set(1)

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
		
		self.printMain("Fan Club MkII Interface initialized", "G")


		# INITIALIZE MEMBERS = = = = = = = = = = = = = = = = = = = = = = = = = =
		 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
		# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
		 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

		# Initialize Profiler --------------------------------------------------
		self.profiler = Profiler.Profiler() 
		self.printMain("Profiler initialized", "G")
		print "Profiler ready"
		self.slaves = self.profiler.slaves

		# Initialize Communicator ----------------------------------------------
		self.communicator = Communicator.Communicator(self.profiler)
		self.printMain("Communicator initialized", "G")
		print "Communicator ready"

		# INITIALIZE UPDATING THREADS = = = = = = = = = = = = = = = = = = = = = 

		# ----------------------------------------------------------------------
		self._mainPrinterRoutine()

		
		# ----------------------------------------------------------------------
		self._slavesPrinterRoutine()

		
		# ----------------------------------------------------------------------
		self._broadcastPrinterRoutine()
		
		# ----------------------------------------------------------------------
		self._listenerPrinterRoutine()


		# ----------------------------------------------------------------------
		self._slaveDisplayRoutine()

		
		# Start printer threads ------------------------------------------------


		# End constructor ==========================================================

## THREAD ROUTINES # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	
	## PRINTER ROUTINES # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

	def _mainPrinterRoutine(self): # ===========================================
		# ABOUT: Keep main terminal window updated w/ Communicator output. To be
		
		if self.terminalVar.get() == 0:
			pass

		else: 
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
						self.terminal.select(3)

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
		# End _mainPrintRoutine ================================================

	def _slavesPrinterRoutine(self): # =========================================
		# ABOUT: Keep slaves terminal window updated w/ Communicator output. To
		# be executed by slavesPrinterThread
		#
		
			if self.terminalVar.get() == 0:
				pass

			else:
				try:

					# Fetch item from Communicator queue:
					target, output, tag = self.communicator.slaveQueue.get_nowait()
					# If there is an item, print it (otherwise, Empty exception is
					# raised and handled)

					# Check for debug tag:
					if tag is "D" and self.debugVar.get() == 0:
						# Do not print if the debug variable is set to 0
						pass

					# Switch focus to this tab in case of errors of warnings:
					else:
						if tag is "E":
							self.terminal.select(1)

						self.slavesTText.config(state = Tk.NORMAL)
							# Must change state to add text.

						# Print MAC address:
						self.slavesTText.insert(Tk.END, "[" + target.mac + "] ", "B")

						# Print text:
						self.slavesTText.insert(Tk.END, output + "\n", tag)
						self.slavesTText.config(state = Tk.DISABLED)

						# Check for auto scroll:
						if self.autoscrollVar.get() == 1:
							self.slavesTText.see("end")

				except Queue.Empty:
					# If there is nothing to print, try again.
					pass

			self.mainTText.after(100, self._slavesPrinterRoutine)

		# End _slavesPrinterRoutine ============================================

	def _broadcastPrinterRoutine(self): # ======================================
		# ABOUT: Keep broadcast terminal window updated w/ Communicator output.

		if self.terminalVar.get() == 0:
			pass

		else: 
			try: # NOTE: Use try/finally to guarantee lock release.

				# Fetch item from Communicator queue:
				output, tag = self.communicator.broadcastQueue.get_nowait()
				# If there is an item, print it (otherwise, Empty exception is
				# raised and handled)

				# Check for debug tag:
				if tag is "D" and self.debugVar.get() == 0:
					# Do not print if the debug variable is set to 0
					pass

				else:

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

			except Queue.Empty:
				# If there is nothing to print, try again.
				pass

		self.broadcastTText.after(500, self._broadcastPrinterRoutine)


		# End _broadcastPrintRoutine ================================================

	def _listenerPrinterRoutine(self): # =======================================
		# ABOUT: Keep listener terminal window updated w/ Communicator output.

		if self.terminalVar.get() == 0:
			pass

		else: 
			try: # NOTE: Use try/finally to guarantee lock release.

				# Fetch item from Communicator queue:
				output, tag = self.communicator.listenerQueue.get_nowait()
				# If there is an item, print it (otherwise, Empty exception is
				# raised and handled)

				# Check for debug tag:
				if tag is "D" and self.debugVar.get() == 0:
					# Do not print if the debug variable is set to 0
					pass

				else:

					# Switch focus to this tab in case of errors of warnings:
					if tag is "E":
						self.terminal.select(3)

					self.listenerTText.config(state = Tk.NORMAL)
						# Must change state to add text.
					self.listenerTText.insert(Tk.END, output + "\n", tag)
					self.listenerTText.config(state = Tk.DISABLED)

					# Check for auto scroll:
					if self.autoscrollVar.get() == 1:
						self.listenerTText.see("end")

			except Queue.Empty:
				# If there is nothing to print, try again.
				pass

		self.listenerTText.after(500, self._listenerPrinterRoutine)

		# End _listenerPrintRoutine ================================================

	def _slaveDisplayRoutine(self): # ==========================================
		# ABOUT: Loop over each Slave and display is relevant information.
		try:

			# Loop over Slave list -----------------------------------------
			for mac in self.slaves:

				# Check if this Slave has a display:
				if self.slaves[mac].slaveDisplay == None:

					# If it does not, give it a new one:
					self.slaves[mac].slaveDisplay = \
						SlaveDisplay(self.arrayFrame, 
							self.slaves[mac].name, mac,
							Slave.translate(
								self.slaves[mac].status,
								), self.profiler.maxFans)

				else:
					# If it does have a display, try to update it:
					try:

						# Get data:
						data = \
							self.slaves[mac].\
							updateQueue.get_nowait()

						# Update display w/ such data:
						self.slaves[mac].\
							slaveDisplay.update(data)

					except Queue.Empty:
						# If there is nothing to retrieve, move on
						pass


		except Exception as e:
			self.printMain("UNCAUGHT EXCEPTION: \"{}\"".\
               format(traceback.format_exc()), "E")

		self.after(300, self._slaveDisplayRoutine)

		# End _slaveDisplayRoutine =============================================

## AUXILIARY METHODS # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

	def printMain(self, output, tag = "S"): # ==================================
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

## INTERFACE METHODS # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #




