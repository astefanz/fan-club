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

	def __init__(self, master, name, mac, initialStatus, maxFans, activeFans): #

		self.background = "#d3d3d3"
		self.mac = mac
		self.maxFans = maxFans
		self.activeFans = activeFans

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
			bg = "white")
		self.nameLabel.pack(side = Tk.LEFT)

		# ......................................................................
		self.macVar = Tk.StringVar()
		self.macVar.set(" ["+mac+"] ")

		self.macLabel = Tk.Label(self.generalFrame, textvariable = self.macVar, 
			fg = "blue",relief = Tk.SUNKEN, bd = 1,
			bg = "white")
		self.macLabel.pack(side = Tk.LEFT)

		# ......................................................................
		self.statusVar = Tk.StringVar()
		self.statusVar.set(Slave.translate(initialStatus))

		self.statusLabel = Tk.Label(self.generalFrame, 
			textvariable = self.statusVar, font = 'TkFixedFont 12 bold',
			bg = "white", relief = Tk.SUNKEN, bd = 1)
		self.statusLabel.pack(side = Tk.LEFT)

		# ......................................................................
		self.ipVar = Tk.StringVar()
		self.ipVar.set("IP: [NONE]")

		self.ipLabel = Tk.Label(self.generalFrame, textvariable = self.ipVar,
			bg = "white", relief = Tk.SUNKEN, bd = 1)
		self.ipLabel.pack(side = Tk.LEFT)

		# ......................................................................
		self.exchangeVar = Tk.StringVar()
		self.exchangeVar.set("E: 0")
		self.exchangeLabel = Tk.Label(self.generalFrame, 
			textvariable = self.exchangeVar, relief = Tk.SUNKEN, bd = 1,
			bg = "white")
		self.exchangeLabel.pack(side = Tk.LEFT)

		# ......................................................................
		self.activeFansVar = Tk.StringVar()
		self.activeFansVar.set("Active Fans: {}/{}".\
			format(activeFans, maxFans))
		self.activeFansLabel = Tk.Label(self.generalFrame, 
			textvariable = self.activeFansVar, relief = Tk.SUNKEN, bd = 1,
			bg = "white")
		self.activeFansLabel.pack(side = Tk.LEFT)

		# ......................................................................

		self.toggled = False
		self.selectText = Tk.StringVar()
		self.selectText.set("Select")
		self.selectButton = Tk.Button(self.generalFrame, textvariable = self.selectText, 
			command = self.toggleAll, highlightbackground = self.background)

		self.selectButton.pack(side =Tk.RIGHT)

		# FAN ARRAY - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
		self.fanArrayFrame = Tk.Frame(self, bg = self.background)
		self.fanArrayFrame.pack(fill = Tk.X)

		self.fans = []
		for i in range(maxFans):
			self.fans.append(FanDisplay(self.fanArrayFrame, i, 
				self.setSelection))
		
		self.master.create_window((0,0), window = self, anchor = 'w', width = 781)
		self.pack(fill = Tk.X, side = Tk.TOP)

		# OLD VALUES: - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
			# Keep track of old values to 
			# only update values that need updating...

		self.oldRPMs = []
		self.oldDCs = []

		# Populate lists w/ placeholders:
		for i in range(maxFans):
			self.oldRPMs.append(-1)
			self.oldDCs.append(-1)


		# SELECTED FLAG - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
			# Keep track of whether one or more fans in this Slave are selected
		self.selected = []
		self.selectionCount = 0
		for i in range(maxFans):
			self.selected.append("0")
		# End __init__ =========================================================

	def setName(self, newName): # ==========================================
		# ABOUT: Update name.
		# PARAMETERS: 
		# - newName: new name.

		self.nameVar.set(newName)

	def setStatus(self, newStatus): # ==========================================
		# ABOUT: Update status.
		# PARAMETERS: 
		# - newStatus: code of the new status.

		self.statusVar.set(Slave.translate(newStatus))

		# End setStatus ========================================================

	def setMAC(self, newMAC): # ================================================
		# ABOUT: Update MAC.
		# PARAMETERS: 
		# - MAC: new MAC address.

		self.macVar.set(newMAC)

	def setExchange(self, newExchange): # ======================================
		# ABOUT: Update exchange index.
		# PARAMETERS: 
		# - newExchange: new exchange index.

		self.exchangeVar.set(newExchange)

	def setIP(self, newIP): # ==================================================
		# ABOUT: Update IP address.
		# PARAMETERS: 
		# - newExchange: new IP address

		self.ipVar.set(newIP)

	def setRPM(self, rpm, fan): # ==============================================
		# ABOUT: Update RPM of one fan.
		# PARAMETERS:
		# - rpm: new RPM value
		# - fan: index of the fan to update

		# Check old values and update only when there is a change:
		if self.oldRPMs[fan] != rpm:
			self.fans[fan].setRPM(str(rpm) + ' R')
			self.oldRPMs[fan] = rpm
		else:
			pass

	def setDC(self, dc, fan): # ================================================
		# ABOUT: Update DC of one fan.
		# PARAMETERS:
		# - dc: new DC value
		# - fan: index of fan to update

		# Check old values and update only when there is a change:
		if self.oldDCs[fan] != dc:
			self.fans[fan].setDC(str(dc) + '%')
			self.oldDCs[fan] = dc
		else:
			pass

	def setActiveFans(self, newActiveFans): # ==================================
		# ABOUT: Update activeFans value
		# PARAMETERS:
		# - newActiveFans: new value for activeFans

		self.activeFansVar.set("Active Fans: {}/{}".\
			format(newActiveFans, self.maxFans))

	def toggleAll(self): # =====================================================
		# ABOUT: Set all fans as selected or deselected (Alternate):
		if not self.toggled:
			for fan in self.fans:
				fan.select(None)
				self.selectText.set("Deselect")
		else:
			for fan in self.fans:
				fan.deselect(None)
				self.selectText.set("Select")

		self.toggled = not self.toggled

	def selectAll(self): # =====================================================
		# ABOUT: Set all fans as selected:
		for fan in self.fans:
			fan.select(None)
			self.selectText.set("Deselect")

		self.toggled = True

	def deselectAll(self): # ====================================================
		# ABOUT: Set all fans as selected:
		for fan in self.fans:
			fan.deselect(None)
			self.selectText.set("Select")

		self.toggled = False

	def setSelection(self, selected, index): # =================================
		# ABOUT: Set whether a fan in the array is selected:
		# PARAMETERS:
		# - selected: bool, whether the fan in question is selected.
		# - index: int, index of the fan in question

		if selected:
			self.selected[index] = '1'
			self.selectionCount += 1
		else:
			self.selected[index] = '0'
			self.selectionCount -= 1

	def getSelection(self): # ==================================================
		# ABOUT: Get list of selected fans
		# RETURNS:
		# List of selected fans as string of 1's and 0's

		result = ''

		for fan in self.selected:
			result += fan

		return result

class FanDisplay(Tk.Frame):
	# ABOUT: Graphically represent each fan

	def __init__(self, master, index, selectMethod): # =========================
		# ABOUT: Constructor for class FanDisplay

		self.background = "white"
		size = 20 # px per side
		self.rpm = 0
		self.dc = 0
		self.index = index
		self.selectMethod = selectMethod

		# SELECTION ------------------------------------------------------------
		self.selected = False


		# CONFIGURE FRAME = = = = = = = = = = = = = = = = = = = = = = = = = = = 
		Tk.Frame.__init__(self, master = master, bg = "white")
		self.config(relief = Tk.SUNKEN, borderwidth = 1)
		self.bind('<Button-1>', self.toggle)

		# Index display = = = = = = = = = = = = = = = = = = = = = = = = = = = =
		self.indexLabel = Tk.Label(self, text = self.index, 
			font = ('TkFixedFont', 7, 'bold'), background = '#282828',
			foreground = "white",  pady = 0)
		self.indexLabel.bind('<Button-1>', self.toggle)
		self.indexLabel.pack(fill = Tk.X)

		# RPM display = = = = = = = = = = = = = = = = = = = = = = = = = = = = = 
		self.rpmVar = Tk.StringVar()
		self.rpmVar.set("NR")
		self.rpmDisplay = Tk.Label(self, textvariable = self.rpmVar, 
			font = ('TkFixedFont', 7), pady = -100)
		self.rpmDisplay.pack()

		self.rpmDisplay.bind('<Button-1>', self.toggle)

		# DC display = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

		self.dcVar = Tk.StringVar()
		self.dcVar.set("N%")
		self.dcDisplay = Tk.Label(self, textvariable = self.dcVar, 
			font = ('TkFixedFont', 7), pady = -100)

		self.dcDisplay.pack()
		self.dcDisplay.bind('<Button-1>', self.toggle)

		# SETTERS = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = 
		self.setRPM = self.rpmVar.set
		self.setDC = self.dcVar.set

		# PACK = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
		self.pack(side = Tk.LEFT)

	def toggle(self, event): # =================================================
		# ABOUT: To be activated on click. Toggles fan selection.
		if(self.selected):
			self.deselect(None)
		else:
			self.select(None)
	
	def select(self, event): # =================================================
		# ABOUT: Set this fan as selected.
		if(not self.selected):
			self.selected =  True
			self.rpmDisplay.configure(bg = "orange")
			self.dcDisplay.configure(bg = "orange")
			self.configure(bg = "orange")
			self.selectMethod(True, self.index)


	def deselect(self, event): # ===============================================
		# ABOUT: Set this fan as not selected.
		if(self.selected):
			self.selected =  False
			self.rpmDisplay.configure(bg = "white")
			self.dcDisplay.configure(bg = "white")
			self.configure(bg = "white")
			self.selectMethod(False, self.index)



## CLASS DEFINITION ############################################################

class FCInterface(Tk.Frame):      

	def __init__(self, version, master=None): # ================================
		Tk.Frame.__init__(self, master)

		# CONFIGURE MAIN WINDOW = = = = = = = = = = = = = = = = = = = = = = = = 


		# Deactivate resizing:
		#self.master.resizable(False,False)

		# Set title:
		self.master.title("Fan Club MkII [ALPHA]")

		# Set background:
		self.background = "#e2e2e2"
		self.config(bg = self.background)

		# Set debug foreground:
		self.debugColor = "#ff007f"

		# CREATE COMPONENTS = = = = = = = = = = = = = = = = = = = = = = = = = = 

		# ARRAY ----------------------------------------------------------------
		self.arrayFrame = Tk.Frame(self, relief = Tk.RIDGE, 
			borderwidth = 2, width = 1500, height = 100)

		self.arrayCanvas = Tk.Canvas(self.arrayFrame, height = 300, 
			bg = 'darkgray',highlightthickness=0)

		self.arrayFrameLabelFrame = Tk.Label(self.arrayFrame,
			bg = self.background, borderwidth = 1, relief = Tk.GROOVE)


		self.shutdownButtonFrame = Tk.Frame(self.arrayFrameLabelFrame, relief = Tk.SUNKEN,
			borderwidth = 1)

		self.shutdownButton = Tk.Button(self.shutdownButtonFrame, 
			highlightbackground = "#890c0c", text = "SHUT DOWN", 
			command = self._shutdownButton)

		self.shutdownButtonFrame.pack(side = Tk.RIGHT)
		self.shutdownButton.pack()

		self.arrayFrameLabel = Tk.Label(self.arrayFrameLabelFrame, 
			text = "Slaves", bg = self.background, anchor = Tk.CENTER)
		

		self.arrayFrameLabel.pack()
		self.arrayFrameLabelFrame.pack(fill = Tk.BOTH)

		# ARRAY SCROLLBAR: 

		self.arrayScrollbar = Tk.Scrollbar(self.arrayFrame)
		self.arrayScrollbar.pack(side = Tk.RIGHT, fill=Tk.Y)
		self.arrayScrollbar.config(command=self.arrayCanvas.yview)
		self.arrayCanvas.config(yscrollcommand = self.arrayScrollbar.set)
		self.arrayCanvas.configure(scrollregion=(0,0,1500,1200))


		self.arrayFrame.pack(fill = Tk.X)

		self.arrayCanvas.pack(fill = Tk.X, expand = False)
		self.arrayCanvas.pack_propagate(False)

		# CONTROL --------------------------------------------------------------
		self.controlFrame = Tk.Frame(self, relief = Tk.GROOVE, borderwidth = 1,
			 bg=self.background)

		self.controlContainer = Tk.Frame(self.controlFrame, 
			bg = self.background)

		self.selectedCommand = Tk.StringVar()
		self.selectedCommand.set("Set Duty Cycle")
		self.commandMenu = Tk.OptionMenu(self.controlContainer, 
			self.selectedCommand,"Set Duty Cycle", "Chase RPM", 
			command = self._changeCommandMenu)

		self.commandLabelText = Tk.StringVar()
		self.commandLabelText.set("RPM: ")
		self.commandLabel = Tk.Label(self.controlContainer, 
			textvariable = self.commandLabelText, background = self.background)

		self.commandMenu.configure(highlightbackground = self.background)
		self.commandMenu.configure(background = self.background)

		self.commandMenu.pack(side = Tk.LEFT)
		self.commandLabel.pack(side = Tk.LEFT)

		validateC = self.register(self._validateN)
		self.commandEntry = Tk.Entry(self.controlContainer, 
			highlightbackground = self.background,
			width = 7, validate = 'key', validatecommand = \
				(validateC, '%S', '%s', '%d'))
		self.commandEntry.pack(side = Tk.LEFT)

		self.sendButton = Tk.Button(self.controlContainer, 
			highlightbackground = self.background, text = "Send")

		self.sendButton.pack(side = Tk.LEFT)



		self.selectedAll = False
		self.selectAllButton = Tk.Button(self.controlFrame, 
			highlightbackground = self.background, text = "Select All", 
			command = self.selectAllSlaves)

		self.selectAllButton.pack(side = Tk.RIGHT)

		self.controlContainer.pack()
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
		self.master.geometry('%dx%d+%d+%d' % (960, 630, \
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
		self.profiler = Profiler.Profiler(self.arrayCanvas) 
		self.printMain("Profiler initialized", "G")
		print "Profiler ready"
		self.slaves = self.profiler.slaves

		# Initialize Communicator ----------------------------------------------
		self.communicator = Communicator.Communicator(self.profiler, self.arrayCanvas)
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

	def _validateN(self, newCharacter, textBeforeCall, action): # ==============
		# ABOUT: To be used by TkInter to validate text in "Send" Entry.
		if action == '0':
			return True
		elif self.selectedCommand.get() == "Set Duty Cycle" and \
			len(textBeforeCall) < 8:
			if newCharacter in '0123456789':
				try:
					total = float(textBeforeCall + newCharacter)
					return total <= 1
				except ValueError:
					return False
			elif newCharacter == '.' and not '.' in textBeforeCall:
				return True
			else:
				return False

		elif self.selectedCommand.get() == "Set RPM" and newCharacter \
			in '0123456789' and len(textBeforeCall) < 5:
			return True

		else:
			return False

	def _changeCommandMenu(self, newValue): # ==================================
		# ABOUT: Handle changes in commandMenu

		# Check value and update command frame in accordance:
		if newValue == "Set Duty Cycle":
			self.commandLabelText.set("DC: ")

		elif newValue == "Chase RPM":
			self.commandLabelText.set("RPM: ")

	def _shutdownButton(self): # ===============================================
		# ABOUT: To be bound to shutdownButton

		self.printMain("WARNING: SHUTDOWN BUTTON NOT YET IMPLEMENTED", "E")

## INTERFACE METHODS # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

	def selectAllSlaves(self): # ===============================================
		# ABOUT: To be bound to the "Select All" button (selects all fans in all
		# Slaves)

		if not self.selectedAll:
			for mac in self.profiler.slaves:
				self.profiler.slaves[mac].slaveDisplay.selectAll()
			self.selectAllButton.configure(text = "Deselect All")
		else:
			for mac in self.profiler.slaves:
				self.profiler.slaves[mac].slaveDisplay.deselectAll()
				self.selectAllButton.configure(text = "Select All")

		self.selectedAll = not self.selectedAll






