################################################################################
## Project: Fan Club Mark II "Master" # File: SlaveContainer.py               ##
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
Specialized container for all Slave-specific data within FCInterface.

"""
################################################################################

## DEPENDENCIES ################################################################

# System:
import traceback

# GUI:
from mttkinter import mtTkinter as Tk

# Data:
import Queue

# FCMkII:
import FCSlave as sv
import cellcolors as cc
import FanContainer as fr

## CLASS DEFINITION ############################################################

class SlaveContainer:
	# ABOUT: Represent GUI-reevant Slave data in the Communicator module.
	# Here each SlaveInterface instance corresponds to one Slave unit in the
	# Communicator, whether connected or not.

	def __init__(self, # =======================================================
		name, mac, status, maxFans, maxRPM, activeFans, 
		ip, misoMethod, mosiMethod,
		master, periodMS, slaveListIID, index, coordinates, moduleDimensions,
		moduleAssignment):
		# ABOUT: Constructor for class SlaveContainer.

		# ATTRIBUTE SUMMARY ----------------------------------------------------
		#
		#	ATTRIBUTE			KIND		DATA TYPE		
		#	--------------------------------------------------------------------
		#	Name				constant	str	
		#	MAC Address			constant	str
		#	Status				variable	int w/ changes in updater and SVar
		#   Index				constant	int
		#   ....................................................................
		#	Max fans			constant	int
		#	Max RPM				constant	int
		#	Active fans			constant	int	
		#	Coordinates			variable	int tuple
		#	Module dimensions	variable	int tuple
		#	Module assignment	variable	str
		#	....................................................................
		#	MOSI index			variable	StringVar
		#	MISO index			variable	StringVar
		#	IP Address			variable	StringVar
		#	....................................................................
		#	Duty cycles			variables	List of FanContainers
		#	RPM's				variables	List of FanContainers
		#	....................................................................
		#	Period (MS)			constant	int
		# ----------------------------------------------------------------------

		# Initialize "constant" attributes -----------------------------
		
		# Name:
		self.name = name
		# MAC Address:
		self.mac = mac
		
		# Index:
		self.index = index

		# Max fans:
		self.maxFans = maxFans
		
		# Max RPM
		self.maxRPM = maxRPM

		# Active fans:
		self.activeFans = activeFans
		
		# Coordinates:
		self.coordinates = coordinates

		# Module dimensions:
		self.moduleDimensions = moduleDimensions

		# Module assignment: 
		self.moduleAssignment = moduleAssignment

		# Tkinter master:
		self.master = master

		# TKinter slaveList IID:
		self.slaveListIID = slaveListIID

		# Refresh period:
		self.periodMS = periodMS # (milliseconds)

		# Initialize "variable" attributes -----------------------------
		
		# Status:
		self.status = status
		self.statusStringVar = Tk.StringVar()
		self.statusStringVar.set(sv.translate(status))	
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
			self.fans.append(fr.FanContainer(fr.INACTIVE, self, i))

		# Indices:
		self.mosiIndex = Tk.StringVar()
		self.mosiIndex.set("RIP")
		self.misoIndex = Tk.StringVar()
		self.misoIndex.set("RIP")
		self.dataIndex = Tk.StringVar()
		self.dataIndex.set("RIP")
		self.timeouts = Tk.StringVar()
		self.timeouts.set("RIP")
		
		# MISO and MOSI queuing methods:
		self.misoMethod = misoMethod
		self.mosiMethod = mosiMethod

		self.selected = 0
		
		# Displays:
		self.slaveDisplay = None

		# Increment slave count:
		self.master.totalSlaves += 1
		self.master.totalSlavesVar.set(self.master.totalSlaves)

		self.master.statusInts[self.status] += 1
		self.master.statusVars[self.status].set(
			self.master.statusInts[self.status])
		
		if self.status == sv.AVAILABLE and not \
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
				if fetchedUpdate[0] == sv.STATUS_CHANGE:
					
					# Update status:
				

					# Remove old status:
					self.master.statusInts[self.status] -= 1
					self.master.statusVars[self.status].set(
						self.master.statusInts[self.status])

					# Check AVAILABLE:
					if self.status == sv.AVAILABLE and \
						self.master.statusInts[sv.AVAILABLE] == 0:
						self.master.connectAllButton.pack_forget()
						self.master.connectAllButtonPacked = False

					elif fetchedUpdate[1] == sv.AVAILABLE and not \
						self.master.connectAllButtonPacked:

						self.master.connectAllButton.pack(
							side = Tk.RIGHT)
						self.master.connectAllButtonPacked = True
				
					# Add new status:
					self.status = fetchedUpdate[1]
					self.statusStringVar.set(sv.translate(fetchedUpdate[1]))

					self.master.statusInts[self.status] += 1
					self.master.statusVars[self.status].set(
						self.master.statusInts[self.status])

					# Check for disconnection:
					if self.status == sv.DISCONNECTED:
						# Reset all connection variables:
						self.ip.set("None")
						self.mosiIndex.set("RIP")
						self.misoIndex.set("RIP")
						self.dataIndex.set("RIP")
						self.timeouts.set("RIP")

						# Reset fan array information:
						for fan in self.fans:
							fan.reset()
							fan.setActive(fr.INACTIVE)

					else:
						# Otherwise, update indices and IP:
						self.mosiIndex.set(str(fetchedUpdate[2]))
						self.misoIndex.set(str(fetchedUpdate[3]))
						self.timeouts.set('0')
						self.ip.set(fetchedUpdate[4])
						self.dataIndex.set(str(fetchedUpdate[5]))

						# Update fan activity:
						for fan in self.fans[:self.activeFans]:
							fan.setActive(fr.ACTIVE)

				elif fetchedUpdate[0] == sv.VALUE_UPDATE:
					# Update indices and fan array values:
					self.mosiIndex.set(str(fetchedUpdate[1]))
					self.misoIndex.set(str(fetchedUpdate[2]))
					self.dataIndex.set(str(fetchedUpdate[4]))	
					self.timeouts.set(str(fetchedUpdate[5]))
					# Update fan array values:
					for i in range(self.activeFans):
						self.fans[i].rpm.set(fetchedUpdate[3][0][i])
						self.fans[i].dc.set("{:0.1f}".format(fetchedUpdate[3][1][i]*100))
						
						# Update grid:
						if self.master.grid is not None and self.fans[i].cell is not None:
							# If this fan is linked to a cell that can change
							# colors...
							self.master.grid.canvas.itemconfig(
								self.fans[i].cell,
								fill = cc.MAP_VIRIDIS[
									int(255*(1.0*fetchedUpdate[3][0][i]/self.maxRPM))]
								)
							
					# Update Printer (if it is active):
					try:
						if self.master.printer.getStatus() == Printer.ON:
							self.master.printer.put(
								self.index,
								(fetchedUpdate[3][0], fetchedUpdate[3][1])
							)
						else:
							format(self.master.printer.status)
					except Queue.Full:
						pass
				else:
					self.master.\
						printMain("ERROR: Unrecognized update code {} in "\
						"SlaveContainer ({}) update method.".\
						format(fetchedUpdate[0], self.index + 1),
						"E")

				# Update slaveList ---------------------------------------------
				if fetchedUpdate[0] == sv.STATUS_CHANGE:
					self.master.slaveList.item(self.slaveListIID, 
						values = [
							self.index + 1,
							self.name, 
							self.mac, 
							self.statusStringVar.get(),
							self.ip.get(), 
							self.activeFans],
						tag = sv.translate(self.status, True)
						)
				elif fetchedUpdate[0] == sv.VALUE_UPDATE:

					self.master.slaveList.item(self.slaveListIID, 
						values = [
							self.index + 1,
							self.name, 
							self.mac, 
							self.statusStringVar.get(),
							self.ip.get(), 
							self.activeFans]
						)

				# Update slaveDisplay ------------------------------------------
				if fetchedUpdate[0] == sv.STATUS_CHANGE and \
					self.slaveDisplay != None:
					self.slaveDisplay.setStatus(self.status)
			
			else:
				# Nothing to do for now.
				pass
		
		except Exception as e:
			self.master.printMain("[SU][{}] UNCAUGHT EXCEPTION: \"{}\"".\
				format(self.index + 1, traceback.format_exc()), "E")

		# Schedule next update -------------------------------------------------
		self.master.after(self.periodMS, self.update)

		# End update ===========================================================
	
	def setSlaveDisplay(self, slaveDisplay): # =================================
		# ABOUT: Set the SlaveDisplay targetting this container, if any.
		# PARAMETERS:
		# slaveDisplay: either a SlaveDisplay object  or None.

		self.slaveDisplay = slaveDisplay

		# End setSlaveDisplay ==================================================

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
		
		if self.status != sv.CONNECTED:
			# No selection for disconnected boards
			return

		if fan is None:
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
		return self.status == sv.CONNECTED and self.selected > 0 

		# End hasSelected ======================================================

	# End SlaveContainer #=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#
