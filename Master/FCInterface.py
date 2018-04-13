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
import sys # Exception handling
import inspect # get line number for debugging

import Communicator
import Slave
import Profiler

## CONSTANT VALUES #############################################################    

# Selection change codes:
INCREASE = True
DECREASE = False

# FanDisplay status codes:
ACTIVE = True
INACTIVE = False

# Broadcast status codes:
GREEN = 1
GREEN2 = 2
BLUE = 3
RED = 0

# AUXILIARY DEBUG PRINT:
db = 0
def d():
	print inspect.currentframe().f_back.f_lineno

## AUXILIARY CLASSES ###########################################################
class MainGrid(Tk.Frame, object):
	# ABOUT: 2D grid to represent fan array.

	def __init__(self, master, m, n):
		# ABOUT: Constructor for class MainGrid.
		
		# Call parent constructor (for class Canvas):
		super(MainGrid, self).__init__(
			master
			)
		
		# Assign member variables:
		self.m = m
		self.n = n
			
		# Build cavas:
		self.canvas = Tk.Canvas(self)
		#self.canvas.place(relx = .5, rely = .5, anchor = Tk.CENTER)
		self.canvas.pack(fill = "none", expand = True)
		
		# Set a margin for grid edges to show:
		self.margin = 5

		# Initialize data representation:
		# TODO: Create custom class for each fan
		self.matrix = []
		for i in range(m):
			self.matrix.append([])
			for j in range(n):
				self.matrix[i].append(None)
			
		self.pack(fill = Tk.BOTH, expand = True)
		# End MainGrid constructor =============================================
		
	def draw(self, l): # ===================================================
		# ABOUT: Draw a grid in which each cell has side l.

		# Initialize coordinates:
		x, y = self.margin, self.margin

		for i in range(self.m):
			x = self.margin
			for j in range(self.n):
				# Draw rectangle ij:
				self.matrix[i][j] = \
					self.canvas.create_rectangle(
					x,y, x+l,y+l,
					)
				x += l
			y += l
		
		#self.canvas.config(
		#	width = l*self.m + self.margin, height = l*self.n + self.margin)

		# End draw =========================================================

	# End Main Grid #=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=

class SlaveContainer:
	# ABOUT: Represent GUI-relevant Slave data in the Communicator module.
	# Here each SlaveInterface instance corresponds to one Slave unit in the
	# Communicator, whether connected or not.

	def __init__(self, # =======================================================
		name, mac, status, maxFans, activeFans, ip, misoMethod, mosiMethod,
		master, period_ms, slaveListIID):
		# ABOUT: Constructor for class SlaveContainer.

		# ATTRIBUTE SUMMARY ----------------------------------------------------
		#
		#	ATTRIBUTE			KIND		DATA TYPE		
		#	--------------------------------------------------------------------
		#	Name				constant	str	
		#	MAC Address			constant	str
		#	Status				variable	int w/ changes in updater and SVar
		#   ....................................................................
		#	Max fans			constant	int
		#	Active fans			constant	int	
		#	....................................................................
		#	MOSI index			variable	StringVar
		#	MISO index			variable	StringVar
		#	IP Address			variable	StringVar
		#	....................................................................
		#	Duty cycles			variables	List of FanContainers
		#	RPM's				variables	List of FanContainers
		# 	....................................................................
		#	Update period (ms)	variable	int
		# ----------------------------------------------------------------------

		# Initialize "constant" attributes -----------------------------
		
		# Name:
		self.name = name
		# MAC Address:
		self.mac = mac
		
		# Max fans:
		self.maxFans = maxFans
		
		# Active fans:
		self.activeFans = activeFans
		
		# Tkinter master:
		self.master = master

		# TKinter slaveList IID:
		self.slaveListIID = slaveListIID

		# Refresh period:
		self.period_ms = period_ms # (milliseconds)

		# Initialize "variable" attributes -----------------------------
		
		# Status:
		self.status = status
		self.statusStringVar = Tk.StringVar()
		self.statusStringVar.set(Slave.translate(status))	
		# IP Address:
		self.ip = Tk.StringVar()
		self.ip.set(ip)
		
		# Selection:
		self.selectionCounterVar = Tk.IntVar()
		self.selectionCounterVar.set(0)
		
		self.activeCounterVar = Tk.IntVar()
		self.activeCounterVar.set(self.activeFans)
		# FanContainers:
		self.fans = []
		for i in range(maxFans):
			self.fans.append(FanContainer(INACTIVE, self))

		# Indices:
		self.mosiIndex = Tk.StringVar()
		self.mosiIndex.set("RIP")
		self.misoIndex = Tk.StringVar()
		self.misoIndex.set("RIP")
		
		# MISO and MOSI queuing methods:
		self.misoMethod = misoMethod
		self.mosiMethod = mosiMethod

		self.selected = 0
		
		# Displays:
		self.slaveDisplay = None
		self.moduleDisplay = None

		# Increment slave count:
		self.master.totalSlaves += 1
		self.master.totalSlavesVar.set(self.master.totalSlaves)

		self.master.statusInts[self.status] += 1
		self.master.statusVars[self.status].set(
			self.master.statusInts[self.status])
		
		if self.status == Slave.AVAILABLE and not \
			self.master.connectAllButtonPacked:
			self.master.connectAllButton.pack(side = Tk.RIGHT)
			self.master.connectAllButtonPacked = True
		
		# Start update method ------------------------------------------
		self.update()

		# End __init__ =================================================
		
	def update(self): # ====================================================
		# ABOUT: Update this SlaveContainer instance. 
		
		try:
			# Fetch update:
			fetchedUpdate  = self.misoMethod()	
			
			# Check if an update was fetched
			if fetchedUpdate != None:
				
				# Check update type:
				if fetchedUpdate[0] == Slave.STATUS_CHANGE:
					
					# Update status:
				

					# Remove old status:
					self.master.statusInts[self.status] -= 1
					self.master.statusVars[self.status].set(
						self.master.statusInts[self.status])

					# Check AVAILABLE:
					if self.status == Slave.AVAILABLE and \
						self.master.statusInts[Slave.AVAILABLE] == 0:
						self.master.connectAllButton.pack_forget()
						self.master.connectAllButtonPacked = False

					elif fetchedUpdate[1] == Slave.AVAILABLE and not \
						self.master.connectAllButtonPacked:

						self.master.connectAllButton.pack(
							side = Tk.RIGHT)
						self.master.connectAllButtonPacked = True
				
					# Add new status:
					self.status = fetchedUpdate[1]
					self.statusStringVar.set(Slave.translate(fetchedUpdate[1]))

					self.master.statusInts[self.status] += 1
					self.master.statusVars[self.status].set(
						self.master.statusInts[self.status])

					# Check for disconnection:
					if self.status == Slave.DISCONNECTED:
						# Reset all connection variables:
						self.ip.set("None")
						self.mosiIndex.set("RIP")
						self.misoIndex.set("RIP")

						# Reset fan array information:
						for fan in self.fans:
							fan.reset()
							fan.setActive(INACTIVE)

					else:
						# Otherwise, update indices and IP:
						self.mosiIndex.set(str(fetchedUpdate[2]))
						self.misoIndex.set(str(fetchedUpdate[3]))
						self.ip.set(fetchedUpdate[4])

						# Update fan activity:
						for fan in self.fans[:self.activeFans]:
							fan.setActive(ACTIVE)

				elif fetchedUpdate[0] == Slave.VALUE_UPDATE:
					# Update indices and fan array values:
					self.mosiIndex.set(str(fetchedUpdate[1]))
					self.misoIndex.set(str(fetchedUpdate[2]))
					
					# Update fan array values:
					for i in range(self.activeFans):
						self.fans[i].dc.set(fetchedUpdate[3][0][i])
						self.fans[i].rpm.set(fetchedUpdate[3][1][i])

				else:
					self.printMain("ERROR: Unrecognized update code {} in "\
						"SlaveContainer update method.".\
						format(fetchedUpdate[0]),
						"E")

				# Update slaveList ---------------------------------------------
				if fetchedUpdate[0] == Slave.STATUS_CHANGE:
					self.master.slaveList.item(self.slaveListIID, 
						values = [
							self.name, 
							self.mac, 
							self.statusStringVar.get(),
							self.ip.get(), 
							self.activeFans],
						tag = Slave.translate(self.status, True)
						)
				elif fetchedUpdate[0] == Slave.VALUE_UPDATE:

					self.master.slaveList.item(self.slaveListIID, 
						values = [
							self.name, 
							self.mac, 
							self.statusStringVar.get(),
							self.ip.get(), 
							self.activeFans]
						)

				# Update slaveDisplay ------------------------------------------
				if fetchedUpdate[0] == Slave.STATUS_CHANGE and \
					self.slaveDisplay != None:
					self.slaveDisplay.setStatus(self.status)
									
			else:
				# Nothing to do for now.
				pass
		
		except Exception as e:
			self.master.printMain("[SU][{}] UNCAUGHT EXCEPTION: \"{}\"".\
				format(self.mac, traceback.format_exc()), "E")

		# Schedule next update -------------------------------------------------
		self.master.after(self.period_ms, self.update)

		# End update ===========================================================
	
	def setSlaveDisplay(self, slaveDisplay): # =================================
		# ABOUT: Set the SlaveDisplay targetting this container, if any.
		# PARAMETERS:
		# slaveDisplay: either a SlaveDisplay object  or None.

		self.slaveDisplay = slaveDisplay

		# End setSlaveDisplay ==================================================

	def setModuleDisplay(self, slaveDisplay): # ================================
		# ABOUT: Set the module targetting this container, if any.
		# PARAMETERS:
		# slaveDisplay: either a module object  or None.

		self.moduleDisplay = moduleDisplay

		# End setModuleDisplay =================================================

	def getAttributes(self): # =================================================
		# ABOUT: Get a tuple containing all the relevant attributes of this Sla-
		# ve container (either str or int for constant variables or StringVar, 
		# IntVar or DoubleVar for variables)

		return (self.name, 
				self.mac, 
				self.status, 
				self.statusStringVar, 
				self.mosiIndex,
				self.misoIndex,
				self.maxFans, 
				self.activeFans,
				self.ip, 
				self.dcs, 
				self.rpms)

		# End getAttributes ====================================================

	def select(self, fan = None, selection = True): # ==========================
		# ABOUT: Select fan(s) (by setting them as selected or not selected.
		# Will do nothing to fans set as "inactive."
		# PARAMETERS:
		# - fan: int, fan to set. Prints error to terminal upon indexing out of
		# bounds. Defaults to None to affect all fans.
		# - selection: whether to set fan to selected or not selected. Defaults
		# to True (selected).
		# RAISES:
		# - IndexError if fan is out of bounds of fan array.
		
		if self.status != Slave.CONNECTED:
			# No selection for disconnected boards
			return

		if fan == None:
			# Select all active fans:
			for fan in self.fans:
				if fan.selected != selection:
					fan.select(selection)
			
		elif fan < self.activeFans:
			if selection and not self.fans[fan].selected:
				# Selecting a deselected fan:
				self.fans[fan].select(True)
				
			elif not selection and self.fans[fan].selected:
				# Deselecting a selected fan:
				self.fans[fan].select(False)

		# End select ===========================================================
	
	def selectAll(self): # =====================================================
		# ABOUT: Select all fans.
		self.select(None, True)
		
		# End selectAll ========================================================

	def deselectAll(self): # ===================================================
		# ABOUT: Deselect all fans.
		self.select(None,False)

		# End deselectAll ======================================================

	def toggle(self, fan): # ===================================================
		# ABOUT: Invert selection of a given fan.
		# PARAMETERS:
		# - fan: int, fan to toggle.
		# RAISES:
		# IndexError if fan index is out of bounds of fan array.
		self.select(fan, not self.fans[fan].selected)
	
		# End toggle ===========================================================

	def getSelection(self): # ==================================================
		# ABOUT: Get this Slave's current "selection string"
		# RETURNS:
		# - str, selected fans as 1's and 0's.
		
		# Assemble selection string:
		selection = ""
		for fan in self.fans:
			selection += fan.selectionChar
		return selection 

		# End getSelected ======================================================

	def hasSelected(self): # ===================================================
		# ABOUT: Get whether this Slave has at least one fan currently selected.
		# RETURNS:
		# - bool, whether this Slave has at least one fan currently selected.
		return self.status == Slave.CONNECTED and self.selected > 0 

		# End hasSelected ======================================================

	# End SlaveContainer #=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#

class FanContainer:
	# ABOUT: To serve as a member of class SlaveContainer and hold data abo-
	# ut a specific fan of a specific Slave's fan array.

	def __init__(self, isActive, slaveContainer): # ============================
		# ABOUT: Constructor for class FanContainer.
		# PARAMETERS:
		# - isActive: bool, whether this Fan is active.
		# - slaveContainer: SlaveContainer object that contains this instance.

		# ATTRIBUTES:
		# - Active (bool)
		# - Selected (bool)
		# - Duty Cycle (DoubleVar)
		# - RPM (IntVar)
		
		self.active = isActive
		self.slaveContainer = slaveContainer

		self.selected = False
		self.selectionChar = '0'

		self.dc = Tk.DoubleVar()
		self.dc.set(0)

		self.rpm = Tk.IntVar()
		self.rpm.set(0)
		
		self.fanDisplay = None
		self.fanGrid = None


		# End FanContainer constructor =========================================
	
	def toggle(self): # ========================================================
		# ABOUT: Alternate between selection states.
		# RETURNS: 
		# - bool new selection state.
		self.select(not self.selected)	
		return self.selected
		# End toggle =======================================================

	def setFanDisplay(self, newFanDisplay): # ==============================
		# ABOUT: Set this instance's FanDisplay, if any.
		# PARAMETERS:
		# - newFanDisplay: either FanDisplay instance or None.
		self.fanDisplay = newFanDisplay
		# End setFanDisplay ================================================

	def select(self, selected = True): # ===================================
		# ABOUT: Set whether this fan is selected.
		# PARAMETERS:
		# - selected: bool, whether this fan is selected.
		if selected and not self.selected:
			#       \-------------------/ <-- Avoid redundant selections
			self.selectionChar = '1'
			self.slaveContainer.selected += 1
			self.slaveContainer.selectionCounterVar.set(
				self.slaveContainer.selected)
			if self.fanDisplay != None:
				self.fanDisplay.select(True)
			self.selected = selected

			# Update selected Fans counter:
			self.slaveContainer.master.selectedFans += 1
			self.slaveContainer.master.selectedFansVar.set(
				self.slaveContainer.master.selectedFans)

			# Update selected Slaves counter:
			if self.slaveContainer.selected == 1:
				# (i.e if this is the first Fan to be selected, then this
				# SlaveContainer has been, until now, being counted as not
				# selected.)

				self.slaveContainer.master.selectedSlaves +=1
				self.slaveContainer.master.selectedSlavesVar.set(
					self.slaveContainer.master.selectedSlaves)

		elif not selected and self.selected:
			#              \--------------/ <-- Avoid redundant deselections
			self.selectionChar = '0'
			self.slaveContainer.selected -= 1 
			self.slaveContainer.selectionCounterVar.set(
				self.slaveContainer.selected)
			if self.fanDisplay != None:
				self.fanDisplay.deselect(True)
			self.selected = selected

			# Update total counter:
			self.slaveContainer.master.selectedFans -= 1
			self.slaveContainer.master.selectedFansVar.set(
				self.slaveContainer.master.selectedFans)

			# Update selected Slaves counter:
			if self.slaveContainer.selected == 0:
				# (i.e if this is the last Fan to be deselected, then this
				# SlaveContainer has been, until now, being counted as
				# selected.)

				self.slaveContainer.master.selectedSlaves -=1
				self.slaveContainer.master.selectedSlavesVar.set(
					self.slaveContainer.master.selectedSlaves)
		# End select =======================================================

	def deselect(self): # ==================================================
		# ABOUT: Equivalent to FanContainer.select(False).
		self.select(False)
		# End deselect ====================================================

	def isSelected(self): # ================================================
		# ABOUT: Get whether this fan is selected (bool).
		# RETURNS: 
		# - bool, whether this fan is selected
		return self.selected

		# End isSelected ===================================================

	def getChar(self): # ===================================================
		# ABOUT: Get selection character for this fan.
		# RETURNS:
		# - char (str of length 1), '1' if selected and '0' if not.
		if selected:
			return '1'
		else:
			return '0'

		# End getChar ======================================================

	def setActive(self, active): # =========================================
		# ABOUT: Set whether this fan will be active.
		# PARAMETERS:
		# - active: bool, new activity setting of this fan.

		if active and not self.active:
			# Activate inactive fan:
			self.active = True
			if self.fanDisplay != None:
				self.fanDisplay.setStatus(ACTIVE)

		elif not active and self.active:
			# Deactivate active fan:
			self.active = False
			if self.fanDisplay != None:
				self.fanDisplay.setStatus(INACTIVE)

	def isActive(self): # ==================================================
		# ABOUT: Get whether this fan is active (bool).
		# RETURNS:
		# - bool, whether this fan is active.

		return self.active

		# End isActive =====================================================
	
	def reset(self): # =====================================================
		# ABOUT: Reset fan values to defaults for not CONNECTED slaves.

		self.dc.set(0)
		self.rpm.set(0)
		
		self.deselect()
		# End reset ========================================================

	# End FanContainer #=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#
		

class SlaveDisplay(Tk.Frame):

	def __init__(self, master, communicator,  maxFans): # ======================
		# ABOUT: Constructor for class SlaveDisplay.
		# PARAMETERS:
		# - master: Tkinter container widget.
		# - communicator: Communicator instance.
		# - maxFans: maximum number of fans to be displayed.

		self.background = "#d3d3d3"
		self.target = None
		self.maxFans = maxFans
		self.status = Slave.DISCONNECTED
		self.isPacked = False
		self.communicator = communicator

		# CONFIGURE ------------------------------------------------------------
		Tk.Frame.__init__(self, master)
		self.config(bg = self.background, relief = Tk.SUNKEN, borderwidth = 2)

		# ADD LABELS -----------------------------------------------------------

		# GENERAL INFORMATION - - - - - - - - - - - - - - - - - - - - - - - - - 

		self.generalFrame = Tk.Frame(self, bg = self.background)
		self.generalFrame.pack(fill = Tk.Y, side = Tk.LEFT)
		
		self.topFrame = Tk.Frame(self.generalFrame, bg = self.background)
		self.topFrame.pack(fill = Tk.X, side = Tk.TOP)
		
		# ......................................................................
		self.nameLabel = Tk.Label(self.topFrame,
			text = "", relief = Tk.SUNKEN, bd = 1,
			bg = self.background, font = ('TkFixedFont', 12, 'bold'),
			padx = 5, width = 20)
		self.nameLabel.pack(side = Tk.LEFT, 
			anchor = 'w',fill = Tk.X, expand = False)

		# ......................................................................
		self.macLabel = Tk.Label(self.topFrame,
			text = " ",relief = Tk.SUNKEN, bd = 1,
			bg = self.background, font = ('TkFixedFont', 12),
			padx = 5, width = 18)
		self.macLabel.pack(side = Tk.LEFT, 
			anchor = 'w',fill = Tk.X, expand = False)

		# ......................................................................
		self.mosiIndexLabel = Tk.Label(self.topFrame, text = "MOSI:",
			bg = self.background, font = 'TkDefaultFont 8')
		self.mosiIndexLabel.pack(side = Tk.LEFT)
		
		self.mosiIndexCounter = Tk.Label(self.topFrame, 
			text = "RIP", relief = Tk.SUNKEN, bd = 1,
			bg = "white", font = 'TkFixedFont 8',
			width = 10)
		self.mosiIndexCounter.pack(side = Tk.LEFT, 
			anchor = 'w',fill = Tk.X, expand = False)

		# ......................................................................
		self.misoIndexLabel = Tk.Label(self.topFrame, text = "MISO:",
			bg = self.background, font = 'TkDefaultFont 8')
		self.misoIndexLabel.pack(side = Tk.LEFT)

		self.misoIndexCounter = Tk.Label(self.topFrame, 
			text = "RIP", relief = Tk.SUNKEN, bd = 1,
			bg = "white", font = 'TkFixedFont 8',
			width = 10)
		self.misoIndexCounter.pack(side = Tk.LEFT, 
			anchor = 'w', fill = Tk.X, expand = False)
		
		# ......................................................................
		self.connectButtonFrame = Tk.Frame(self.topFrame, bg = self.background,
			padx = 2)
		self.connectButtonFrame.pack(side = Tk.LEFT)

		self.connectButton = Tk.Button(
			self.connectButtonFrame,
			text = "Connect",
			command = self.connect,
			highlightbackground = self.background
		)
		self.connectButton.pack()
		self.connectButtonShown = True

		# ......................................................................
		self.buttonFrame = Tk.Frame(self.topFrame, bg = self.background)
		self.buttonFrame.pack(side = Tk.RIGHT)

		self.toggled = False

		self.selectAllText = Tk.StringVar()
		self.selectAllText.set("Select")
		self.selectAllButton = Tk.Button(
			self.buttonFrame, textvariable = self.selectAllText, 
			command = self.selectAll, 
			highlightbackground = self.background)
		
		self.deselectAllText = Tk.StringVar()
		self.deselectAllText.set("Deselect")
		self.deselectAllButton = Tk.Button(
			self.buttonFrame, textvariable = self.deselectAllText, 
			command = self.deselectAll, 
			highlightbackground = self.background)

		self.selectAllButton.pack(side = Tk.LEFT)
		self.deselectAllButton.pack(side = Tk.LEFT)
		
		self.selectionCounterFrame = Tk.Frame(
			self.buttonFrame,
			bg = self.background,
			relief = Tk.SUNKEN,
			bd = 1
			)

		self.selectionCounter = Tk.Label(
			self.selectionCounterFrame,
			bg = self.background,
			justify = Tk.RIGHT,
			font = ('TkFixedFont', '9'),
			width = 3)	

		self.slashLabel = Tk.Label(
			self.selectionCounterFrame,
			bg = self.background,
			text = '/',
			padx = 0,
			font = ('TkFixedFont', '9'),
			width = 1)

		self.activeCounter = Tk.Label(
			self.selectionCounterFrame,
			justify = Tk.LEFT,
			bg = self.background,
			font = ('TkFixedFont', '9'),
			width = 2)

		self.selectionCounter.pack(side = Tk.LEFT)
		self.slashLabel.pack(side = Tk.LEFT)
		self.activeCounter.pack(side = Tk.LEFT)
		self.selectionCounterFrame.pack(side = Tk.LEFT)

		# FAN ARRAY - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
		self.fanArrayFrame = Tk.Frame(self.generalFrame, bg = self.background)
		self.fanArrayFrame.pack(fill = Tk.X)

		self.fans = []
		for i in range(self.maxFans):
			self.fans.append(FanDisplay(self.fanArrayFrame, i))


		# SELECTED FLAG - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
			# Keep track of whether one or more fans in this Slave are selected
		self.selected = []
		self.selectionCount = 0
		for i in range(self.maxFans):
			self.selected.append("0")

		# Run status-dependent routines:
		self.setStatus(self.status, True)
		# End __init__ =========================================================

	def setTarget(self, newTarget): # ==========================================
		# ABOUT: Change target Slave to be displayed.
		# PARAMETERS:
		# - target: SlaveContainer instance to display.
		
		# Remove past target, if any:
		if self.target != None:
			self.target.setSlaveDisplay(None)

		# Assign target:
		self.target = newTarget
		self.target.setSlaveDisplay(self)

		# Adjust name:
		self.nameLabel.config(text = self.target.name)

		# Adjust MAC:
		self.macLabel.config(text = self.target.mac)

		# Adjust fan array:
		for i in range(self.target.maxFans):
			self.fans[i].setTarget(self.target.fans[i])
		
		# Adjust indices:
		self.misoIndexCounter.config(textvariable =  self.target.misoIndex)
		self.mosiIndexCounter.config(textvariable = self.target.mosiIndex)
		
		# Adjust selection:
		self.selectionCounter.\
			config(textvariable = self.target.selectionCounterVar)

		self.activeCounter.config(textvariable = self.target.activeCounterVar)
		# Adjust status:
		self.setStatus(self.target.status, True)

		# End setTarget ========================================================
		

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
			self.selectAllButton.configure(state = Tk.NORMAL)
			self.deselectAllButton.configure(state = Tk.NORMAL)
			
			self.connectButton.configure(state = Tk.DISABLED)
			self.showConnectButton(False)

		elif newStatus == Slave.DISCONNECTED:
			self.selectAllButton.configure(state = Tk.DISABLED)
			self.deselectAllButton.configure(state = Tk.DISABLED)

			self.connectButton.configure(state = Tk.DISABLED)
			self.showConnectButton()

		elif newStatus == Slave.KNOWN:
			self.selectAllButton.configure(state = Tk.DISABLED)
			self.deselectAllButton.configure(state = Tk.DISABLED)

			self.connectButton.configure(state = Tk.DISABLED)
			self.showConnectButton()

		elif newStatus == Slave.AVAILABLE:
			self.selectAllButton.configure(state = Tk.DISABLED)
			self.deselectAllButton.configure(state = Tk.DISABLED)

			self.connectButton.configure(state = Tk.NORMAL)
			self.showConnectButton()

		# End setStatus ========================================================

	def showConnectButton(self, show = True): # ================================
		# ABOUT: Pack or unpakc the connect button (redundancy safe).
		# PARAMETERS:
		# - show: bool, whether to show the connect button (hide it if False).

		if show and not self.connectButtonShown:
			self.connectButton.pack()
			self.connectButtonShown = True

		elif not show and self.connectButtonShown:
			self.connectButton.pack_forget()
			self.connectButtonFrame.config(width = 0)
			self.connectButtonShown = False

		# End showConnectButton ================================================

	def connect(self): # =======================================================
		# ABOUT: Connect to AVAILABLE Slave.

		if self.status == Slave.AVAILABLE:
			self.communicator.add(self.target.mac)

	def selectAll(self): # =====================================================
		# ABOUT: Set all fans as selected:
		if self.target != None:
			self.target.selectAll()

	def deselectAll(self): # ====================================================
		# ABOUT: Set all fans as selected:
		if self.target != None:
			self.target.deselectAll()

	# End SlaveDisplay #=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#

class FanDisplay(Tk.Frame):
	# ABOUT: Graphically represent each fan

	def __init__(self, master, index): # =======================================
		# ABOUT: Constructor for class FanDisplay

		self.background = "white"
		size = 40 # px per side
		self.rpm = 0
		self.dc = 0
		self.index = index
		self.status = ACTIVE
		self.target = None

		# SELECTION ------------------------------------------------------------
		self.selected = False


		# CONFIGURE FRAME = = = = = = = = = = = = = = = = = = = = = = = = = = = 
		Tk.Frame.__init__(self, 
			master = master, bg = "white", width = size, height = size)
		self.config(relief = Tk.SUNKEN, borderwidth = 1)
		self.bind('<Button-1>', self.toggle)

		# Index display = = = = = = = = = = = = = = = = = = = = = = = = = = = =
		self.indexLabel = Tk.Label(self, text = self.index + 1, 
			font = ('TkFixedFont', 7, 'bold'), background = '#282828',
			foreground = "white",  pady = 0)
		self.indexLabel.bind('<Button-1>', self.toggle)
		self.indexLabel.pack(fill = Tk.X)

		# RPM display = = = = = = = = = = = = = = = = = = = = = = = = = = = = = 
		self.rpmDisplay = Tk.Label(self, 
			font = ('TkFixedFont', 7), pady = -100)
		self.rpmDisplay.pack()

		self.rpmDisplay.bind('<Button-1>', self.toggle)

		# DC display = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

		self.dcDisplay = Tk.Label(self,
			font = ('TkFixedFont', 7), pady = -100)

		self.dcDisplay.pack()
		self.dcDisplay.bind('<Button-1>', self.toggle)

		# PACK = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
		self.pack(side = Tk.LEFT)
		self.pack_propagate(False)
		

	# End FanDisplay constructor ===============================================

	def setTarget(self, newTarget): # ==========================================
		# ABOUT: Change this FanDisplay's target.
		# PARAMETERS:
		# - newTarget: FanContainer to display.
		
		# Remove past target, if any:
		if self.target != None:
			self.target.setFanDisplay(None)

		# Assign target:
		self.target = newTarget
		self.target.setFanDisplay(self)
		# Check activiy:
		self.setStatus(self.target.isActive())
		# Set variables:
		self.dcDisplay.config(textvariable = self.target.dc)
		self.rpmDisplay.config(textvariable = self.target.rpm)

		# Set selection:
		if self.target.isSelected():
			self.select(None)
		else:
			self.deselect(None)

		# End setTarget ========================================================

	def toggle(self, event): # =================================================
		# ABOUT: To be activated on click. Toggles fan selection.
		if(self.selected):
			self.deselect(None)
		else:
			self.select(None)
	
	def select(self, event): # =================================================
		# ABOUT: Set this fan as selected.
		if not self.selected and self.status == ACTIVE: 
			self.selected =  True
			self.rpmDisplay.configure(bg = "orange")
			self.dcDisplay.configure(bg = "orange")
			self.configure(bg = "orange")
			if event != True:
				# Use placeholder also as flag to indicate call was made by
				# FanContainer (which means selecting it again would be redun-
				# dant)
				self.target.select()

	def deselect(self, event): # ===============================================
		# ABOUT: Set this fan as not selected.
		if self.selected:
			self.selected =  False
			if self.status == ACTIVE:
				self.rpmDisplay.configure(bg = "white")
				self.dcDisplay.configure(bg = "white")
				self.configure(bg = "white")
			if event != True:
				# Use placeholder also as flag to indicate call was made by
				# FanContainer (which means selecting it again would be redun-
				# dant)
				self.target.deselect()

	def setStatus(self, newStatus): # ==========================================
		# ABOUT: Set the status of this fan. Inactive fans cannot be selected.
		# Check for redundancy:
		if self.status != newStatus:
			# Check new status:
			if newStatus == ACTIVE:
				# Set style of an active fan:
				self.dcDisplay.configure(background = 'white')
				self.dcDisplay.bind('<Button-1>', self.toggle)

				self.rpmDisplay.configure(background = 'white')
				self.rpmDisplay.bind('<Button-1>', self.toggle)

				self.configure(background = "white")

				self.status = newStatus

			elif newStatus == INACTIVE:
				# Set style of an inactive fan:
				self.dcDisplay.configure(background = '#141414')
				self.dcDisplay.unbind('<Button-1>')

				self.rpmDisplay.configure(background = '#141414')
				self.rpmDisplay.unbind('<Button-1>')

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

		self.mainGrid = MainGrid(self.arrayFrame, 36,36)

		"""
		# TEMPORARY RPM LIST DISPLAY -------------------------------------------
		self.tempDisplay = ttk.Treeview(self.arrayFrame, 
			selectmode="none", height = 5)
		self.tempDisplay["columns"] = \
			("Name", "RPM 1", "RPM 2",  "RPM 3",  "RPM 4",  "RPM 5",  "RPM 6",  "RPM 7",  "RPM 8",  "RPM 9",  "RPM 10",  "RPM 11",  "RPM 12",  "RPM 13",  "RPM 14",  "RPM 15",  "RPM 16",  "RPM 17",  "RPM 18",  "RPM 19",  "RPM 20",  "RPM 21")

		style = ttk.Style()
		#style.configure(".", font=('Helvetica', 8), foreground="white")
		style.configure("Treeview.Heading", font = 'Helvetica 10')

		# Create columns:
		self.tempDisplay.column('#0', width = 20, stretch = False)
		self.tempDisplay.column("Name", width = 20)
		self.tempDisplay.column("RPM 1", width = 20)
		self.tempDisplay.column("RPM 2", width = 20)
		self.tempDisplay.column("RPM 3", width = 20)
		self.tempDisplay.column("RPM 4", width = 20)
		self.tempDisplay.column("RPM 5", width = 20)
		self.tempDisplay.column("RPM 6", width = 20)
		self.tempDisplay.column("RPM 7", width = 20)
		self.tempDisplay.column("RPM 8", width = 20)
		self.tempDisplay.column("RPM 9", width = 20)
		self.tempDisplay.column("RPM 10", width = 20)
		self.tempDisplay.column("RPM 11", width = 20)
		self.tempDisplay.column("RPM 12", width = 20)
		self.tempDisplay.column("RPM 13", width = 20)
		self.tempDisplay.column("RPM 14", width = 20)
		self.tempDisplay.column("RPM 15", width = 20)
		self.tempDisplay.column("RPM 16", width = 20)
		self.tempDisplay.column("RPM 17", width = 20)
		self.tempDisplay.column("RPM 18", width = 20)
		self.tempDisplay.column("RPM 19", width = 20)
		self.tempDisplay.column("RPM 20", width = 20)
		self.tempDisplay.column("RPM 21", width = 20)

		# Configure column headings:
		self.tempDisplay.heading("Name", text = "Name")
		self.tempDisplay.heading("RPM 1", text = "RPM 1")
		self.tempDisplay.heading("RPM 2", text = "RPM 2")
		self.tempDisplay.heading("RPM 3", text = "RPM 3")
		self.tempDisplay.heading("RPM 4", text = "RPM 4")
		self.tempDisplay.heading("RPM 5", text = "RPM 5")
		self.tempDisplay.heading("RPM 6", text = "RPM 6")
		self.tempDisplay.heading("RPM 7", text = "RPM 7")
		self.tempDisplay.heading("RPM 8", text = "RPM 8")
		self.tempDisplay.heading("RPM 9", text = "RPM 9")
		self.tempDisplay.heading("RPM 10", text = "RPM 10")
		self.tempDisplay.heading("RPM 11", text = "RPM 11")
		self.tempDisplay.heading("RPM 12", text = "RPM 12")
		self.tempDisplay.heading("RPM 13", text = "RPM 13")
		self.tempDisplay.heading("RPM 14", text = "RPM 14")
		self.tempDisplay.heading("RPM 15", text = "RPM 15")
		self.tempDisplay.heading("RPM 16", text = "RPM 16")
		self.tempDisplay.heading("RPM 17", text = "RPM 17")
		self.tempDisplay.heading("RPM 18", text = "RPM 18")
		self.tempDisplay.heading("RPM 19", text = "RPM 19")
		self.tempDisplay.heading("RPM 20", text = "RPM 20")
		self.tempDisplay.heading("RPM 21", text = "RPM 21")

		# Configure tag:
		self.tempDisplay.tag_configure("STD", font = 'TkFixedFont 7 ') # Connected

		self.tempDisplay.pack(fill =Tk.BOTH, expand = True)
		"""
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
		self.slaveDisplayFrame = Tk.Frame(self.slaveListFrame,
			bg = self.background)
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
		self.commandLabelText.set("  DC: ")
		self.commandLabel = Tk.Label(self.arrayControlFrame, 
			textvariable = self.commandLabelText, 
			width = 4,
			justify = Tk.LEFT,
			background = self.background)

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

		# Hold toggle:
		self.keepSelectionVar = Tk.BooleanVar()
		self.keepSelectionVar.set(True)

		self.keepSelectionButton = Tk.Checkbutton(self.arrayControlFrame, 
			variable = self.keepSelectionVar, 
			bg = self.background)

		self.keepSelectionButton.pack(side = Tk.LEFT)

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



		# STATUS ---------------------------------------------------------------
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

		self.statusInts[Slave.CONNECTED] = 0
		self.statusVars[Slave.CONNECTED] = Tk.IntVar()

		self.statusInts[Slave.DISCONNECTED] = 0
		self.statusVars[Slave.DISCONNECTED] = Tk.IntVar()

		self.statusInts[Slave.KNOWN] = 0
		self.statusVars[Slave.KNOWN] = Tk.IntVar()

		self.statusInts[Slave.AVAILABLE] = 0
		self.statusVars[Slave.AVAILABLE] = Tk.IntVar()

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
			textvariable = self.statusVars[Slave.CONNECTED],
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
			textvariable = self.statusVars[Slave.DISCONNECTED],
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
			textvariable = self.statusVars[Slave.KNOWN],
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
			textvariable = self.statusVars[Slave.AVAILABLE],
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

		"""
		# Label:
		self.selectionCounterLabel = Tk.Label(
			self.selectionCounterFrame,
			bg = self.background,
			text = "Selected: ",
			fg = 'black',
			font = ('TkDefaultFont', '10')
			)
		self.selectionCounterLabel.pack(side = Tk.LEFT)
		"""


		# Selected Slaves:
		self.selectedSlavesLabel = Tk.Label(
			self.selectionCounterFrame,
			bg = self.background,
			text = "Selected M: ",
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
			text = "Selected F: ",
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
		self.master.update() # Required to set minimum size	
		self.printMain("Fan Club MkII Interface initialized", "G")

	
		# Set minimum size:
		self.master.minsize(
			self.master.winfo_width(), self.master.winfo_height())
		
		# Draw Grid:
		self.mainGrid.draw(self.mainGrid.winfo_height()/36)

		# INITIALIZE DATA MEMBERS = = = = = = = = = = = = = = = = = = = = = = = 
		 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
		# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
		 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

		# Initialize Profiler --------------------------------------------------
		self.profiler = Profiler.Profiler() 
		self.printMain("Profiler initialized", "G")
		print "Profiler ready"
		
		# Initialize Slave data structure --------------------------------------
		self.slaveContainers = {}

		# Initialize Communicator ----------------------------------------------
		self.communicator = Communicator.Communicator(
			self.profiler.slaveList,
			self.profiler.profile, 
			self.broadcastDisplayUpdate, self.listenerDisplayUpdate)
		self.printMain("Communicator initialized", "G")
		print "Communicator ready"
		self.slaves = self.communicator.slaves
		
		# Initialize SlaveDisplay (requires Communicator):
		self.slaveDisplay = SlaveDisplay(
			self.slaveDisplayFrame, 
			self.communicator, 
			self.profiler.profile["maxFans"])

		# INITIALIZE UPDATE ROUTINES = = = = = = = = = = = = = = = = = = = = = =

		# ----------------------------------------------------------------------
		self._mainPrinterRoutine()
		
		self._newSlaveChecker()

		# End constructor ======================================================

## UPDATE ROUTINES # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

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

	def _newSlaveChecker(self): # ===================================
		# ABOUT: Check periodically for the addition of new Slaves.
		# PARAMETERS: 
		# - period_ms: int, milliseconds before next call using TKinter's after.

		# Check for new Slaves:
		fetched = self.communicator.getNewSlave()
		try:
			if fetched == None:
				# Nothing to do here
				pass
			else:
				# Slave fetched. Add it to the interface:

				# Create new SlaveContainer:
				newSlaveContainer = \
					SlaveContainer(
						name = fetched[0],
						mac = fetched[1],
						status = fetched[2],
						maxFans = fetched[3],
						activeFans = fetched[4],
						ip = fetched[5],
						misoMethod = fetched[6],
						mosiMethod = fetched[7],
						master = self,
						period_ms = 100,
						slaveListIID = 	self.slaveList.insert(
							'', 'end', 
							values = (
							fetched[0], # name 
							fetched[1], # MAC 
							Slave.translate(fetched[2]), # Status as str
							fetched[5],	 # IP as str
							fetched[4]), # Active fans as int 
							tag = Slave.translate(fetched[2], True))
										#        \------/ Status (int)
					)
				
				# Add to Slave dictionary:
				self.slaveContainers[fetched[1]] = newSlaveContainer
			
			# Schedule next call -----------------------------------------------
			self.main.after(100, self._newSlaveChecker)

		except Exception as e: # Print uncaught exceptions
			self.printMain("[NS] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")
		# End _newSlaveChecker =================================================

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
				self.slaveDisplay.pack_forget()
				self.slaveDisplayFrame.configure(height = 1)
				self.slaveDisplay.isPacked = False
		
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
		
		currentSelection = self.slaveList.item(
			self.slaveList.selection()[0],"values")[1]

		if self.oldSelection != currentSelection:
			self.slaveDisplay.setTarget(self.slaveContainers[currentSelection])
			self.oldSelection = currentSelection

		if not self.slaveDisplay.isPacked:
			self.slaveDisplay.pack()
			self.slaveDisplay.isPacked = True
	
	def _send(self): # =========================================================
		# ABOUT: Send a message to the MOSI queue of applicable Slaves
		# Loop over each Slave unit and check whether it has any selected fans:
			# NOTE: No need to check whether these are connected. This is opera-
			# tionally equivalent to them having no selected fans.
		try:
			# Check if there is a command to send:
			if self.commandEntry.get() == "":
				# Ignore this button press:
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
				commandKeyword += "C~{}".format(self.commandEntry.get())

			else:
				# Unrecognized command (wat):
				raise ValueError(
					"ERROR: UNRECOGNIZED COMMAND IN COMMAND MENU: {}".format(
						commandMenu.get()))	
			
			# Set sentinel for whether this message was sent:
			sent = False

			for mac in self.slaveContainers:

				if self.slaveContainers[mac].hasSelected():
					# If it has at least one fan selected, add this to its queue:
					try:
						command = "{}~{}".format(
							commandKeyword, \
							self.slaveContainers[mac].getSelection())
						self.slaveContainers[mac].mosiMethod(command, False)
						# Deselect fans:
						if not self.keepSelectionVar.get():
							self.slaveContainers[mac].select(None, False)
						# Update sentinel:
						sent = True
						
					except Queue.Full:
						self.printMain( "[{}] "\
							"Warning: Outgoing command Queue full. "\
							"Could not send message".\
							format(mac), "E")

			# Check sentinel:
			if sent:
				# Erase text:
				self.commandEntry.delete(0, Tk.END)
				
		except Exception as e:
			self.printMain("[_send()] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")

	def _connectAllSlaves(self): # =============================================
		# ABOUT: Connect to all AVAILABLE Slaves, if any.

		# Loop over Slaves and add all AVAILABLE ones:
		for mac in self.slaveContainers:
			if self.slaveContainers[mac].status == Slave.AVAILABLE:
				self.communicator.add(mac)

		# End addAllSlaves =====================================================

## INTERFACE METHODS # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

	def selectAllSlaves(self): # ===============================================
		# ABOUT: To be bound to the "Select All" button (selects all fans in all
		# Slaves)
		
		for mac in self.slaveContainers:
			self.slaveContainers[mac].selectAll()
		# End selectAllSlaves ==================================================

	def deselectAllSlaves(self): # =============================================
		# ABOUT: To be bound to the "Deselect All" button (deselects all fans 
		# in all Slaves)
		
		for mac in self.slaveContainers:
			self.slaveContainers[mac].deselectAll()
		
		# End deselectAllSlaves ================================================



