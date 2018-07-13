################################################################################
## Project: Fan Club Mark II "Master" # File: FanDisplay.py                   ##
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
Custom TkInter widget to display fan-specific information.

"""
################################################################################

## DEPENDENCIES ################################################################

# GUI:
from mttkinter import mtTkinter as Tk

# FCMkII:
from . import FanContainer as fr

## CLASS DEFINITION ############################################################

class FanDisplay(Tk.Frame):
	# ABOUT: Graphically represent each fan

	def __init__(self, master, index): # =======================================
		# ABOUT: Constructor for class FanDisplay

		self.background = "white"
		size = 40 # px per side
		self.rpm = 0
		self.dc = 0
		self.index = index
		self.status = fr.ACTIVE
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
		self.dcFrame = Tk.Frame(self, bg = '#141414')
		self.dcFrame.pack()

		self.dcDisplay = Tk.Label(
			self.dcFrame,
			font = ('TkFixedFont', 7), 
			pady = -100,
			padx = -20,
			justify = Tk.RIGHT,
			anchor = 'e')
		
		self.dcPercentage = Tk.Label(
			self.dcFrame,
			font = ('TkFixedFont', 7),
			pady = -100,
			anchor = 'w',
			text = '%',
			bg = '#141414',
			padx = -20,
			justify = Tk.LEFT
			)
		self.dcPercentage.pack(side = Tk.RIGHT)
		self.dcDisplay.pack(side = Tk.LEFT)
		
		self.dcFrame.bind('<Button-1>', self.toggle)
		self.dcPercentage.bind('<Button-1>', self.toggle)
		self.dcDisplay.bind('<Button-1>', self.toggle)

		# PACK = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =	
		self.setStatus(fr.INACTIVE)

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
		if not self.selected and self.status == fr.ACTIVE: 
			self.selected =  True
			self.rpmDisplay.configure(bg = "orange")
			self.dcDisplay.configure(bg = "orange")
			self.dcPercentage.configure(bg = "orange")
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
			if self.status == fr.ACTIVE:
				self.rpmDisplay.configure(bg = "white")
				self.dcDisplay.configure(bg = "white")
				self.configure(bg = "white")
				self.dcPercentage.configure(bg = "white")
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
			if newStatus == fr.ACTIVE:
				# Set style of an active fan:
				self.dcDisplay.configure(background = 'white')
				self.dcPercentage.configure(bg = "white")
				self.dcDisplay.bind('<Button-1>', self.toggle)

				self.rpmDisplay.configure(background = 'white')
				self.rpmDisplay.bind('<Button-1>', self.toggle)

				self.configure(background = "white")

				self.status = newStatus

			elif newStatus == fr.INACTIVE:
				# Set style of an inactive fan:
				self.dcDisplay.configure(background = '#141414')
				self.dcPercentage.configure(bg = "#141414")
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

	# End FanDisplay #=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#
