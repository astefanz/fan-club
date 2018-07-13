################################################################################
## Project: Fan Club Mark II "Master" # File: FanContainer.py                 ##
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
Specialized container for all Fan-specific data within FCInterface.

"""
################################################################################

## DEPENDENCIES ################################################################

# System:
import traceback

# GUI:
from mttkinter import mtTkinter as Tk

# Data:
import queue

# FCMkII:
from . import MainGrid as mg

## CONSTANTS ###################################################################

ACTIVE = True
INACTIVE = False

## CLASS DEFINITION ############################################################

class FanContainer:
	# ABOUT: To serve as a member of class SlaveContainer and hold data abo-
	# ut a specific fan of a specific Slave's fan array.

	def __init__(self, isActive, slaveContainer, index): # ==================
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
		self.index = index
		self.selected = False
		self.selectionChar = '0'

		self.dc = Tk.DoubleVar()
		self.dc.set(0)

		self.rpm = Tk.IntVar()
		self.rpm.set(0)
		
		self.fanDisplay = None
		self.fanGrid = None

		self.cell = None
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

	def setGridCell(self, cell): # =============================================
		# ABOUT: Link this fan to a cell in the grid, which may be None to indi-
		# cate this fan is linked to no cell.
		
		self.cell = cell

		# End setGridCell ====================================================== 

	def select(self, selected = True): # ===================================
		# ABOUT: Set whether this fan is selected.
		# PARAMETERS:
		# - selected: bool, whether this fan is selected.
	
		if selected == self.selected:
			# Do nothing if this selection is redundant:
			return

		elif selected:
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
			
				
		elif not selected:
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
	

		# Update grid cell if possible:
		if self.cell is not None:
			self.slaveContainer.master.grid.select(self.cell, selected)

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
			
			# Grid (temp):
			if self.slaveContainer.master.grid is not None:
				self.slaveContainer.master.grid.canvas.itemconfig(
					self.cell,
					fill = mg.MAINGRID_INACTIVE)
		
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
		

