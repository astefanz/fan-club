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
import Fan

## CONSTANT VALUES #############################################################      

# Broadcast status codes:
GREEN = 1
GREEN2 = 2
BLUE = 3
RED = 0

## AUXILIARY CLASSES ###########################################################

class SlaveDisplay(Tk.Frame):

	def __init__(self, master, slave): #

		self.background = "#d3d3d3"
		self.mac = slave.mac
		self.maxFans = slave.maxFans
		self.activeFans = slave.activeFans
		self.status = slave.status
		self.slave = slave

		# CONFIGURE ------------------------------------------------------------
		Tk.Frame.__init__(self, master)
		self.config(bg = self.background, relief = Tk.SUNKEN, borderwidth = 2)

		# ADD LABELS -----------------------------------------------------------

		# GENERAL INFORMATION - - - - - - - - - - - - - - - - - - - - - - - - - 

		self.generalFrame = Tk.Frame(self, bg = self.background)
		self.generalFrame.pack(fill = Tk.Y, side = Tk.LEFT)

		# ......................................................................
		self.exchangeVar = Tk.StringVar()
		self.exchangeVar.set("O: 0")
		self.exchangeLabel = Tk.Label(self.generalFrame, 
			textvariable = self.exchangeVar, relief = Tk.SUNKEN, bd = 1,
			bg = "white", font = 'TkFixedFont 8')
		self.exchangeLabel.pack(side = Tk.TOP, anchor = 'w',fill = Tk.X, expand =True)

		# ......................................................................
		self.misoIndexVar = Tk.StringVar()
		self.misoIndexVar.set("I: 0")
		self.misoIndexLabel = Tk.Label(self.generalFrame, 
			textvariable = self.misoIndexVar, relief = Tk.SUNKEN, bd = 1,
			bg = "white", font = 'TkFixedFont 8')
		self.misoIndexLabel.pack(side = Tk.TOP, anchor = 'w', fill = Tk.X, expand =True)

		# ......................................................................
		self.buttonFrame = Tk.Frame(self)
		self.buttonFrame.pack(side = Tk.RIGHT)

		self.toggled = False
		self.selectText = Tk.StringVar()

		self.selectText.set("Select")
		self.selectButton = Tk.Button(self.buttonFrame, textvariable = self.selectText, 
			command = self.toggleAll, highlightbackground = self.background,pady = 0)

		self.selectButton.pack(side = Tk.LEFT)

		# FAN ARRAY - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
		self.fanArrayFrame = Tk.Frame(self, bg = self.background)
		self.fanArrayFrame.pack(fill = Tk.X)

		self.fans = []
		for i in range(self.maxFans):
			self.fans.append(FanDisplay(self.fanArrayFrame, i, 
				self.setSelection))
		
		#self.pack(fill = Tk.X, side = Tk.TOP)

		# OLD VALUES: - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
			# Keep track of old values to 
			# only update values that need updating...
		self.oldRPMs = []
		self.oldDCs = []

		# Populate lists w/ placeholders:
		for i in range(self.maxFans):
			self.oldRPMs.append(-1)
			self.oldDCs.append(-1)


		# SELECTED FLAG - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
			# Keep track of whether one or more fans in this Slave are selected
		self.selected = []
		self.selectionCount = 0
		for i in range(self.maxFans):
			self.selected.append("0")

		# Run status-dependent routines:
		self.setStatus(slave.status, True)
		# End __init__ =========================================================

	def setStatus(self, newStatus, redundant = False): # =======================
		# ABOUT: Update status.
		# PARAMETERS: 
		# - newStatus: code of the new status.
		# - redundant: bool, whether to run again for the current status

		# Check for redundancy:
		if newStatus == self.status and not redundant:
			return
		else:
			self.status = newStatus

		if newStatus == Slave.CONNECTED:
			self.setActiveFans(self.activeFans)
			self.selectButton.configure(state = Tk.NORMAL)

		elif newStatus == Slave.DISCONNECTED:
			self.setActiveFans(0)
			self.selectButton.configure(state = Tk.DISABLED)
			# Reset lists:
			for i in range(self.maxFans):
				self.oldRPMs[i] = -1
				self.oldDCs[i] = -1

		elif newStatus == Slave.KNOWN:
			self.setActiveFans(0)
			self.selectButton.configure(state = Tk.DISABLED)
			# Reset lists:
			for i in range(self.maxFans):
				self.oldRPMs[i] = -1
				self.oldDCs[i] = -1

		elif newStatus == Slave.AVAILABLE:
			self.selectText.set("Connect")
			self.selectButton.configure(state = Tk.NORMAL)
			self.setActiveFans(0)
			# Reset lists:
			for i in range(self.maxFans):
				self.oldRPMs[i] = -1
				self.oldDCs[i] = -1

		# End setStatus ========================================================

	def setExchange(self, newExchange): # ======================================
		# ABOUT: Update exchange index.
		# PARAMETERS: 
		# - newExchange: new exchange index.

		self.exchangeVar.set(newExchange)

	def setMISOIndex(self, newMISOIndex): # ====================================
		# ABOUT: Update MISO index.
		# PARAMETERS: 
		# - newMISOIndex: new MISO index.

		self.misoIndexVar.set(newMISOIndex)

	def setRPM(self, rpm, fan): # ==============================================
		# ABOUT: Update RPM of one fan.
		# PARAMETERS:
		# - rpm: new RPM value
		# - fan: index of the fan to update

		# Check old values and update only when there is a change:
		print "setRPM called w/ {}...".format(rpm),
		if self.oldRPMs[fan] != rpm:
			self.fans[fan].setRPM(str(rpm) + ' R')
			self.oldRPMs[fan] = rpm
			print "updated"
		else:
			print "... passed"
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

		# Update fan array display:
		for fan in self.fans:
			if fan.index < newActiveFans:
				fan.setStatus(Fan.ACTIVE)
			else:
				fan.setStatus(Fan.INACTIVE)


	def toggleAll(self): # =====================================================
		# ABOUT: Set all fans as selected or deselected (Alternate):

		# Check status:
		if self.status == Slave.CONNECTED:

			if not self.toggled:
				for fan in self.fans:
					fan.select(None)
					self.selectText.set("Deselect")
			else:
				for fan in self.fans:
					fan.deselect(None)
					self.selectText.set("Select")

			self.toggled = not self.toggled

		elif self.status == Slave.AVAILABLE:
			self.slave.setStatus(Slave.KNOWN)
			self.selectText.set("Select")

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
		# - index: int, index of the fan in question.

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
		# DEBUG
		for fan in self.selected:
			result += fan
		return result

	def hasSelected(self): # =====================================================
		# ABOUT: Get whether this Slave unit has fans selected, as a bool.
		# RETURNS: bool, whether at least one fan is selected.
		return self.selectionCount > 0

class FanDisplay(Tk.Frame):
	# ABOUT: Graphically represent each fan

	def __init__(self, master, index, selectMethod): # =========================
		# ABOUT: Constructor for class FanDisplay

		self.background = "white"
		size = 40 # px per side
		self.rpm = 0
		self.dc = 0
		self.index = index
		self.selectMethod = selectMethod
		self.status = Fan.ACTIVE

		# SELECTION ------------------------------------------------------------
		self.selected = False


		# CONFIGURE FRAME = = = = = = = = = = = = = = = = = = = = = = = = = = = 
		Tk.Frame.__init__(self, master = master, bg = "white", width = size, height = size)
		self.config(relief = Tk.SUNKEN, borderwidth = 1)
		self.bind('<Button-1>', self.toggle)

		# Index display = = = = = = = = = = = = = = = = = = = = = = = = = = = =
		self.indexLabel = Tk.Label(self, text = self.index + 1, 
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
		self.pack_propagate(False)

	def toggle(self, event): # =================================================
		# ABOUT: To be activated on click. Toggles fan selection.
		if(self.selected):
			self.deselect(None)
		else:
			self.select(None)
	
	def select(self, event): # =================================================
		# ABOUT: Set this fan as selected.
		if not self.selected and self.status == Fan.ACTIVE: 
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

	def setStatus(self, newStatus): # ==========================================
		# ABOUT: Set the status of this fan. Inactive fans cannot be selected.

		# Check for redundancy:
		if self.status != newStatus:
			# Check new status:
			if newStatus == Fan.ACTIVE:
				# Set style of an active fan:
				self.dcDisplay.configure(background = 'white')
				self.dcDisplay.bind('<Button-1>', self.toggle)

				self.rpmDisplay.configure(background = 'white')
				self.rpmDisplay.bind('<Button-1>', self.toggle)

				self.configure(background = "white")

				self.status = newStatus

			elif newStatus == Fan.INACTIVE:
				# Set style of an inactive fan:
				self.dcDisplay.configure(background = '#141414')
				self.dcDisplay.unbind('<Button-1>')
				self.dcVar.set("N%")

				self.rpmDisplay.configure(background = '#141414')
				self.rpmDisplay.unbind('<Button-1>')
				self.rpmVar.set("NR")

				self.configure(background = "#141414")

				self.status = newStatus

			else:
				raise ValueError(
					"Invalid FanDisplay status code: {}".format(newStatus))

		else: 
			# In case of redundancy, do nothing:
			pass

		# End setStatus ========================================================

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

		# SHUTDOWN -------------------------------------------------------------

		# Shutdown button frame:
		self.shutdownButtonFrame = Tk.Frame(self, relief = Tk.RIDGE, 
			borderwidth = 1)
		self.shutdownButtonFrame.pack(
			side = Tk.TOP, fill = Tk.X, expand = False)

		# Shutdown button:
		self.shutdownButton = Tk.Button(self.shutdownButtonFrame,
			highlightbackground = "#890c0c", text = "SHUTDOWN",
			command = self._shutdownButton, font = 'TkFixedFont 17 bold ')
		self.shutdownButton.pack(fill = Tk.X)

		# MAIN FRAME -----------------------------------------------------------
		self.main = Tk.Frame(self)
		self.main.pack(fill = Tk.BOTH, expand = True)

		# MAIN DISPLAY ---------------------------------------------------------

		# Main display frame ..................................................
		self.mainDisplayFrame = Tk.Frame(
			self.main, height = 100, bg = '#212121')

		self.mainDisplayFrame.pack(
			fill = Tk.BOTH, expand = True, side = Tk.TOP)

		# SETTINGS -------------------------------------------------------------

		# Settings container:
		self.settingsContainer = Tk.Frame(self.mainDisplayFrame,
			bg = self.background)
		self.settingsContainer.pack(
			fill =Tk.Y, side = Tk.LEFT, expand = False,)

		# Settings frame:
		self.settingsFrame = Tk.Frame(self.settingsContainer,
			bg = self.background, width = 500,
			borderwidth = 1, relief = Tk.RIDGE)

		#self.settingsFrame.pack(fill =Tk.BOTH, expand = True)
		# Comment this to start w/ widget hidden


		# Settings Label:
		self.settingsLabelFrame = Tk.Frame(self.settingsFrame,
			bg = self.background)
		self.settingsLabelFrame.pack(fill = Tk.X, expand = False)

		self.settingsLabel = Tk.Label(self.settingsLabelFrame,
			bg = self.background, text = "Settings [Unimplemented]")
		self.settingsLabel.pack(side = Tk.LEFT)

		# ARRAY ----------------------------------------------------------------

		# Array Frame ..........................................................
		self.arrayFrame = Tk.Frame(self.mainDisplayFrame, bg = 'white',
			relief = Tk.SUNKEN, borderwidth = 3)
		self.arrayFrame.pack(fill =Tk.BOTH, expand = True)

		# LIVE PLOT ------------------------------------------------------------

		# Plot container .......................................................
		self.plotContainer = Tk.Frame(self.main)
		self.plotContainer.pack(fill = Tk.X, expand = False)

		# Plot frame ...........................................................
		self.plotFrame = Tk.Frame(self.plotContainer,
			bg = self.background, borderwidth = 1, relief = Tk.GROOVE, padx = 10)
		#self.plotFrame.pack(fill = Tk.X, expand = False)
		# Comment this to start w/ widget hidden

		# Plot controls ........................................................
		self.plotControlFrame = Tk.Frame(self.plotFrame, 
			background = self.background)
		self.plotControlFrame.pack(fill = Tk.X, expand = False)

		# Variable 1:
		self.plotVar1 = Tk.IntVar()

		self.plotOption1 = Tk.Checkbutton(self.plotControlFrame, 
			text ="Variable 1", variable = self.plotVar1, 
			bg = self.background, state = Tk.DISABLED)
		self.plotOption1.pack(side = Tk.LEFT)

		# Variable 2:
		self.plotVar2 = Tk.IntVar()

		self.plotOption2 = Tk.Checkbutton(self.plotControlFrame, 
			text ="Variable 2", variable = self.plotVar2, 
			bg = self.background, state = Tk.DISABLED)
		self.plotOption2.pack(side = Tk.LEFT)

		# Variable 3:
		self.plotVar3 = Tk.IntVar()

		self.plotOption3 = Tk.Checkbutton(self.plotControlFrame, 
			text ="Variable 3", variable = self.plotVar3, 
			bg = self.background, state = Tk.DISABLED)
		self.plotOption3.pack(side = Tk.LEFT)

		# Variable 4:
		self.plotVar4 = Tk.IntVar()

		self.plotOption4 = Tk.Checkbutton(self.plotControlFrame, 
			text ="Variable 4", variable = self.plotVar4, 
			bg = self.background, state = Tk.DISABLED)
		self.plotOption4.pack(side = Tk.LEFT)


		self.plotSaveButton = Tk.Button(self.plotControlFrame, text = 'Save', 
			highlightbackground = self.background, padx = 10, 
			state = Tk.DISABLED)
		self.plotSaveButton.pack(side = Tk.RIGHT)

		# Plot placeholder .....................................................
		self.plot = Tk.Frame(self.plotFrame, height = 100, bg = 'white')
		self.plot.pack(fill = Tk.X, expand = False, anchor = 's')
		# Comment this to start w/ widget hidden

		self.plotLabel = Tk.Label(self.plot, height = 5,
			text = "[Fancy plot will go here]", font = 'TkFixedFont', fg = 'gray')
		self.plotLabel.pack()

		# SLAVE LIST -----------------------------------------------------------

		# Slave list container .................................................
		self.slaveListContainer = Tk.Frame(self.main)
		self.slaveListContainer.pack(fill = Tk.X, expand = False)

		# Slave list frame .....................................................
		self.slaveListFrame = Tk.Label(self.slaveListContainer,
			bg = self.background, borderwidth = 1, relief = Tk.GROOVE)
		self.slaveListFrame.pack(fill = Tk.X, expand = False)

		# Slave display frame ..................................................
		self.slaveDisplayFrame = Tk.Frame(self.slaveListFrame)
		self.slaveDisplayFrame.pack(fill = Tk.X, expand = False)

		# List of Slaves .......................................................

		# Create list:
		self.slaveList = ttk.Treeview(self.slaveListFrame, 
			selectmode="browse", height = 5)
		self.slaveList["columns"] = \
			("Name","MAC","Status","IP","Fans")

		# Create columns:
		self.slaveList.column('#0', width = 20, stretch = False)
		self.slaveList.column("Name", width = 50)
		self.slaveList.column("MAC", width = 50, 
			anchor = "center")
		self.slaveList.column("Status", width = 50, 
			anchor = "center")
		self.slaveList.column("IP", width = 50, 
			anchor = "center")
		self.slaveList.column("Fans", width = 50, stretch = False, 
			anchor = "center")

		# Configure column headings:
		self.slaveList.heading("Name", text = "Name")
		self.slaveList.heading("MAC", text = "MAC")
		self.slaveList.heading("Status", text = "Status")
		self.slaveList.heading("IP", text = "IP")
		self.slaveList.heading("Fans", text = "Fans")

		# Configure tags:
		self.slaveList.tag_configure("C", background= '#d1ffcc', foreground = '#0e4707', font = 'TkFixedFont 12 ') # Connected
		self.slaveList.tag_configure("B", background= '#ccdeff', foreground ='#1b2d4f', font = 'TkFixedFont 12 ') # Busy
		self.slaveList.tag_configure("D", background= '#ffd3d3', foreground ='#560e0e', font = 'TkFixedFont 12 bold')# Disconnected
		self.slaveList.tag_configure("K", background= '#fffaba', foreground ='#44370b', font = 'TkFixedFont 12 bold') # Known
		self.slaveList.tag_configure("A", background= '#ededed', foreground ='#666666', font = 'TkFixedFont 12 ') # Available

		# Save previous selection:
		self.oldSelection = None

		# Bind command:
		self.slaveList.bind('<Double-1>', self._slaveListMethod)

		self.slaveList.pack(fill = Tk.X, expand = False, anchor = 's')

		
		# TERMINAL -------------------------------------------------------------
		self.terminalContainerFrame = Tk.Frame(self.main, relief = Tk.GROOVE, 
		borderwidth = 1, bg = self.background)
		self.terminalContainerFrame.pack(fill = Tk.X, expand = False, anchor = 's')

		self.terminalFrame = Tk.Frame(self.terminalContainerFrame,
			bg = self.background)
		#self.terminalFrame.pack(fill = Tk.BOTH, expand = False)
		# Comment out to not start w/ hidden terminal by default

		# MAIN TERMINAL - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
		self.mainTerminal = ttk.Frame(self.terminalFrame)
		self.mainTerminal.pack(fill = Tk.BOTH, expand = False)
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
		
		# TERMINAL CONTROL FRAME ...............................................

		self.terminalControlFrame = Tk.Frame(self.terminalFrame, 
			bg = self.background)

		# Autoscroll checkbox:
		self.autoscrollVar = Tk.IntVar()

		self.autoscrollButton = Tk.Checkbutton(self.terminalControlFrame, 
			text ="Auto-scroll", variable = self.autoscrollVar, 
			bg = self.background)

		self.terminalControlFrame.pack(fill = Tk.X)

		# Debug checkbox:
		self.debugVar = Tk.IntVar()

		self.debugButton = Tk.Checkbutton(self.terminalControlFrame, 
			text ="Debug prints", variable = self.debugVar, 
			bg = self.background)

		# Terminal print:
		self.terminalVar = Tk.IntVar()
		self.terminalVar.set(1)

		self.terminalButton = Tk.Checkbutton(self.terminalControlFrame, 
			text ="Terminal output", variable = self.terminalVar, 
			bg = self.background)

		# TERMINAL SETUP:

		self.autoscrollButton.pack(side = Tk.LEFT)
		self.debugButton.pack(side = Tk.LEFT)
		self.terminalButton.pack(side = Tk.LEFT)
		self.autoscrollButton.select()


		# CONTROL --------------------------------------------------------------
		self.controlFrame = Tk.Frame(self, 
			relief = Tk.GROOVE, borderwidth = 1,
			bg=self.background)

		self.controlFrame.pack(fill = Tk.X, expand = False)

		# SETTINGS TOGGLE ......................................................
		self.settingsToggleVar = Tk.IntVar()
		self.settingsToggleVar.set(0)

		self.settingsToggle = Tk.Checkbutton(self.controlFrame, 
			text ="Settings", variable = self.settingsToggleVar, 
			bg = self.background, command = self._settingsToggle)

		self.settingsToggle.pack(side = Tk.LEFT)

		# TERMINAL TOGGLE ......................................................
		self.terminalToggleVar = Tk.IntVar()
		self.terminalToggleVar.set(0)

		self.terminalToggle = Tk.Checkbutton(self.controlFrame, 
			text ="Terminal", variable = self.terminalToggleVar, 
			bg = self.background, command = self._terminalToggle)

		self.terminalToggle.pack(side = Tk.LEFT)

		# SLAVE LIST TOGGLE ....................................................
		self.slaveListToggleVar = Tk.IntVar()
		self.slaveListToggleVar.set(1)

		self.slaveListToggle = Tk.Checkbutton(self.controlFrame, 
			text ="List", variable = self.slaveListToggleVar, 
			bg = self.background, command = self._slaveListToggle)

		self.slaveListToggle.pack(side = Tk.LEFT)

		# LIVE PLOTTING TOGGLE .................................................
		self.plotToggleVar = Tk.IntVar()
		self.plotToggleVar.set(0)

		self.plotToggle = Tk.Checkbutton(self.controlFrame, 
			text ="Plot", variable = self.plotToggleVar, 
			bg = self.background, command = self._plotToggle)

		self.plotToggle.pack(side = Tk.LEFT)

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
		self.commandLabelText.set("DC: ")
		self.commandLabel = Tk.Label(self.arrayControlFrame, 
			textvariable = self.commandLabelText, background = self.background)

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

		# Select All button:
		self.selectedAll = False
		self.selectAllButton = Tk.Button(self.arrayControlFrame, 
			highlightbackground = self.background, text = "Select All", 
			command = self.selectAllSlaves)

		self.selectAllButton.pack(side = Tk.RIGHT)



		# STATUS ---------------------------------------------------------------
		self.statusFrame = Tk.Frame(self, relief = Tk.GROOVE, borderwidth = 1,
			 bg=self.background)

		self.versionLabel = Tk.Label(self.statusFrame, text = "Version: " + version,
			bg = self.background, fg = "#424242")
		self.versionLabel.pack(side = Tk.RIGHT)

		self.statusFrame.pack(fill = Tk.X, expand = False, side =Tk.BOTTOM, anchor = 's')

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
			text = "Broadcast: ", background = self.background,)
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
			text = "Listener: ", background = self.background,)
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
		self.profiler = Profiler.Profiler(self.slaveList,self.slaveDisplayFrame) 
		self.printMain("Profiler initialized", "G")
		print "Profiler ready"
		self.slaves = self.profiler.slaves

		# Initialize Communicator ----------------------------------------------
		self.communicator = Communicator.Communicator(self.profiler, 
			self.slaveDisplayFrame,
			self.slaveList, 
			self.broadcastDisplayUpdate, self.listenerDisplayUpdate)
		self.printMain("Communicator initialized", "G")
		print "Communicator ready"

		# INITIALIZE UPDATING THREADS = = = = = = = = = = = = = = = = = = = = = 

		# ----------------------------------------------------------------------
		self._mainPrinterRoutine()
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
						self.terminalToggleVar.set(1)
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
		# End _mainPrintRoutine ================================================

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
				self.terminalToggleVar.set(1)
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
			self.commandLabelText.set("DC: ")

		elif newValue == "Chase RPM":
			self.commandLabelText.set("RPM: ")

	def _settingsToggle(self): # ===============================================
		# ABOUT: Hide and show settings

		# Check variable:
		if self.settingsToggleVar.get() == 1:
			# Build settings:
			self.settingsFrame.pack(fill =Tk.BOTH, expand = True)
		else:
			# Hide settings:
			self.settingsFrame.pack_forget()
			self.settingsContainer.configure(width = 1)	

	def _terminalToggle(self): # ===============================================
		# ABOUT: Hide and show the terminal

		# Check variable:
		if self.terminalToggleVar.get() == 1:
			# Build terminal:
			self.terminalFrame.pack(fill = Tk.BOTH, expand = False)
			self.terminalVar.set(1)
		else:
			# Hide terminal:
			self.terminalFrame.pack_forget()
			self.terminalContainerFrame.configure(height = 1)

	def _slaveListToggle(self): # ==============================================
		# ABOUT: Hide and show the Slave list

		# Check variable:
		if self.slaveListToggleVar.get() == 1:
			# Build slaveList:
			self.slaveListFrame.pack(fill = Tk.X, expand = False)
		else:
			# Hide slaveList:
			self.slaveListFrame.pack_forget()
			self.slaveListContainer.configure(height = 1)
			if self.oldSelection != None:
				self.slaves[self.oldSelection].slaveDisplay.pack_forget()
				self.slaveDisplayFrame.configure(height = 1)

	def _plotToggle(self): # ===================================================
		# ABOUT: Hide and show plot

		# Check variable:
		if self.plotToggleVar.get() == 1:
			# Build plot:
			self.plotFrame.pack(fill = Tk.X, expand = False, anchor = 's')
		else:
			# Hide plot:
			self.plotFrame.pack_forget()
			self.plotContainer.configure(height = 1)


	def _shutdownButton(self): # ===============================================
		# ABOUT: To be bound to shutdownButton

		self.printMain("WARNING: SHUTDOWN BUTTON NOT YET IMPLEMENTED", "E")

	def _slaveListMethod(self, event): # =======================================
		# ABOUT: Handle selections on SlaveList

		# Unpack previous selection:
		if self.oldSelection != None:
			self.slaves[self.oldSelection].slaveDisplay.pack_forget()
		if len(self.slaveList.selection()) > 0:
			self.oldSelection = self.slaveList.item(self.slaveList.selection()[0], "values")[1]
			self.slaves[self.oldSelection].slaveDisplay.pack()


	def _send(self): # =========================================================
		# ABOUT: Send a message to the MOSI queue of applicable Slaves

		# Loop over each Slave unit and check whether it has any selected fans:
			# NOTE: No need to check whether these are connected. This is opera-
			# tionally equivalent to them having no selected fans.

		# Check if there is a command to send:
		if self.commandEntry.get() == "":
			# Ignore this button press:
			print "Empty command entry ignored" # DEBUG ....................................................*
			return

		# Assemble the shared side of the command to be sent: ------------
		#       [INDEX]|MSTD|command~arg~fans
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
			commandKeyword += "W~{}".format(float(
				self.commandEntry.get())/100.0)

		elif self.selectedCommand.get() == "Chase RPM":
			commandKeyword += "C~" + self.commandEntry.get()

		else:
			# Unrecognized command (wat):
			raise ValueError(
				"ERROR: UNRECOGNIZED COMMAND IN COMMAND MENU: {}".format(
					commandMenu.get()))

		# Get command argument:
			

		# Set sentinel for whether this message was sent:
		sent = False

		for mac in self.slaves:
			if self.slaves[mac].slaveDisplay.hasSelected():
				# If it has at least one fan selected, add this to its queue:
				try:
					command = "{}~{}".format(
						commandKeyword, \
						self.slaves[mac].slaveDisplay.getSelection())

					self.slaves[mac].mosiQueue.put_nowait(command)

					# Deselect fans:
					self.slaves[mac].slaveDisplay.deselectAll()

					# Update sentinel:
					sent = True
				except Queue.Full:
					self.printS(self.slaves[mac], 
						"Warning: Queue full. Could not send last message", "E")

		
		# Check sentinel:
		if sent:
			# Erase text:
			self.commandEntry.delete(0, Tk.END)




## INTERFACE METHODS # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

	def selectAllSlaves(self): # ===============================================
		# ABOUT: To be bound to the "Select All" button (selects all fans in all
		# Slaves)

		if not self.selectedAll:
			for mac in self.slaves:
				self.slaves[mac].slaveDisplay.selectAll()
			self.selectAllButton.configure(text = "Deselect All")
		else:
			for mac in self.slaves:
				self.slaves[mac].slaveDisplay.deselectAll()
				self.selectAllButton.configure(text = "Select All")

		self.selectedAll = not self.selectedAll






