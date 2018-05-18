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

from mttkinter import mtTkinter as Tk # GUI
import tkFileDialog 
import tkMessageBox
import tkFont
import ttk # "Notebooks"
import threading
import Queue
import time
import traceback
import os # Get current working directory & check file names
import sys # Exception handling
import inspect # get line number for debugging
import numpy as np

import Communicator
import Profiler
import Printer
import Slave
import CellColors as cc

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

# Printer file name status codes:
BADEXT = -1
EMPTY = 0
NODOT = 1
REPEATED = 2
NODOT_REPEATED = 3
NORMAL = 4
RESTORE = 5

# MainGrid cell colors
MAINGRID_EMPTY = "white"
MAINGRID_NOTSELECTED = "darkgray"
MAINGRID_SELECTED = "orange"
MAINGRID_INACTIVE = "#282828" 

# AUXILIARY DEBUG PRINT:
db = 0
def d():
	print inspect.currentframe().f_back.f_lineno

## AUXILIARY CLASSES ###########################################################
class Grid(Tk.Frame, object):
	# ABOUT: Basic 2D grid to be used as parent class.

	def __init__(self, master, rows, columns, cellLength, margin = 5):
		# ABOUT: Constructor for class Grid.

		# Call parent constructor (for class Frame):
		super(Grid, self).__init__(master)
		
		# Assign member variables:
		self.rows = rows
		self.columns = columns
		self.cellLength = cellLength
			
		# Build cavas:
		self.canvas = Tk.Canvas(self)
		#self.canvas.place(relx = .5, rely = .5, anchor = Tk.CENTER)
		self.canvas.pack(fill = "none", expand = True)
			# NOTE: The above is a workaround for centering
		
		# Set a margin for grid edges to show:
		self.margin = margin
		
		# Set IID dictionary:
		self.iids = {}
			# NOTE: Initialized by self._draw method

		# Initialize data representation:
		# TODO: Create custom class for each fan
		self.pack(fill = Tk.BOTH, expand = True)

		self._draw(self.cellLength)
		# End Grid constructor =================================================
	
	def _draw(self, l): # ======================================================
		# ABOUT: Draw a grid in which each cell has side l.

		# Initialize coordinates:
		x, y = self.margin, self.margin

		for i in range(self.rows):
			x = self.margin
			for j in range(self.columns):
				# Draw rectangle ij:
				iid = \
					self.canvas.create_rectangle(
					x,y, x+l,y+l, fill = MAINGRID_EMPTY)
				self.iids[iid] = (i, j)
				self.canvas\
					.tag_bind(iid, '<ButtonPress-1>', self._onClick)
				x += l
			y += l
		
		self.canvas.config(
			width = l*self.columns + self.margin, 
			height = l*self.rows + self.margin)
		# End _draw ============================================================
	
	def _onClick(self, event):
		# ABOUT: Base method to be called when a cell is clicked.
		# RETURNS: IID of cell clicked.

		# Get selected rectangle:
		return self.canvas.find_closest(
			self.canvas.canvasx(event.x), 
			self.canvas.canvasy(event.y))[0]
		
	# End _onClick =============================================================

# End class Grid =#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=

class MainGrid(Tk.Frame, object):
	# ABOUT: 2D grid to represent fan array.

	def __init__(self, master, rows, columns, cellLength, slaves, maxRPM):
		# ABOUT: Constructor for class MainGrid.

		# Call parent constructor (for class Frame):
		super(MainGrid, self).__init__(master)
		
		# Assign member variables:
		self.rows = rows
		self.columns = columns
		self.cellLength = cellLength
		self.maxRPM = maxRPM

		# Build cavas:
		self.canvas = Tk.Canvas(self)
		#self.canvas.place(relx = .5, rely = .5, anchor = Tk.CENTER)
		self.canvas.pack(fill = "none", expand = True)
			# NOTE: The above is a workaround for centering
		
		# Set a margin for grid edges to show:
		self.margin = 16
		
		# Set IID dictionary:
		self.iids = {}

		# Initialize data representation:
		# TODO: Create custom class for each fan
		self.matrix = []
		for i in range(rows):
			self.matrix.append([])
			for j in range(columns):
				self.matrix[i].append([None, None])
						#              IID  Fan    Selection
				

		# Pack widgets:
		self.pack(fill = Tk.BOTH, expand = True)
		
		# Draw grid:
		self._draw(self.cellLength)

		# Create placeholders for drag-select:
		self.dragging = False
		self.dragOriginRow = -1
		self.dragOriginColumn = -1
		self.dragEndRow = -1
		self.dragEndColumn = -1

		# Link Slaves to grid:
		for slave in slaves:
			self._linkSlave(slave)
		
		# End MainGrid constructor =============================================
	
	def select(self, iid, selected = True): # ==================================
		# ABOUT: Set selection color of a given fan.

		if selected:
			self.canvas.itemconfig(iid, 
				outline = MAINGRID_SELECTED,
				width = 4)
		else:
		
			self.canvas.itemconfig(iid, 
				outline = "black",
				width = 1)
		
		# End select ===========================================================

	def destroy(self): # =======================================================
		# Destroy grid widget. Overrides standard Tkinter destroy method to 
		# unlink fans.

		# Unlink all fans:
		self._unlinkAllFans()

		# Destroy:
		super(MainGrid, self).destroy()
		
		# End destroy ==========================================================
	
	# Private methods ----------------------------------------------------------
	
	def _linkFan(self, fan, row, column): # ====================================
		# ABOUT: Link given fan to cell in given row and column, if possible.
		
		# Check if there was a previously linked fan:
		if self.matrix[row][column][1] is not None:
			# Unlink fan:
			self.matrix[row][column][1].setGridCell(None)
		
		try:	
			# Set grid-to-fan link
			self.matrix[row][column][1] = fan
			
			# Set fan-to-grid link
			fan.setGridCell(self.matrix[row][column][0])
				#           \-------------------------/
				#             IID of linked grid cell

			# Update cell color:
			if fan.isActive():
				if fan.isSelected():
					self.select(self.matrix[row][column][0])
				else:	
					self.select(self.matrix[row][column][0],
						False)
			else:
				self.canvas.itemconfig(
					self.matrix[row][column][0], # IID of cell
					fill = MAINGRID_INACTIVE)

		except IndexError:
			# Having certain cells go out of bounds is allowed, in which case
			# these will be ignored.
			pass

		# End _linkFan =========================================================

	def _unlinkFan(self, row, column): # =======================================
		# Unlink a currently linked fan from its cell, if possible.

		# Check if there is no fan to unlink:
		if self.matrix[row][column][1] is None:
			return		
		try:	
			# Remove fan-to-grid link
			self.matrix[row][column][1].setGridCell(None)
			# \-----------------------/
			#  Fan object linked to cell in this row and column

			# Remove grid-to-fan link
			self.matrix[row][column][1] = None
		
			# Reset cell color:
			self.canvas.itemconfig(
				self.matrix[row][column][0], # IID of cell
				fill = MAINGRID_EMPTY,
				outline = "black",
				width = 1)
			
		except IndexError:
			# Having certain cells go out of bounds is allowed, in which case
			# these will be ignored.
			pass

		# End _unlinkFan =======================================================

	def _unlinkAllFans(self): # ================================================
		# ABOUT: Unlink fans from the entire matrix.

		# Loop through the entire matrix and unlink.
		# NOTE: Empty cells will be automatically ignored.
	
		rowNumber = 0
		columnNumber = 0
		
		for row in self.matrix:
			for column in self.matrix[0]:
				self._unlinkFan(rowNumber, columnNumber)
				columnNumber += 1

			columnNumber = 0
			rowNumber += 1

		# End _unlinkAllFans ===================================================

	def _linkSlave(self, slaveContainer): # ====================================
		# ABOUT: Link given SlaveContainer to grid (must have valid coordinates)

		# Verify:
		if slaveContainer.coordinates is None:
			# Ignore Slaves without coordinates (these have not been added to
			# the grid.)

			return

		else:
			# Loop over the Slave's module and link fans accordingly.
			
			# NOTE: Here the "coordinates" of a Slave are those of the fan
			# at the top-left position of its module's grid.

			splittedModuleAssignment = \
				slaveContainer.moduleAssignment.split(',')
			
			fansToLink = len(splittedModuleAssignment)
                        
			rowDisplacement = slaveContainer.coordinates[0]
			columnDisplacement = slaveContainer.coordinates[1]

			for row in range(slaveContainer.moduleDimensions[0]):
				for column in range(slaveContainer.moduleDimensions[1]):
					
					if fansToLink is 0:
						# Done linking this Slave
						return
					elif splittedModuleAssignment[-fansToLink] is '':
						# Empty cell, skip       
						pass
					else:
						# Link fan
						self._linkFan(\
							# First argument: fan to link:
							slaveContainer.fans[
								int(splittedModuleAssignment[-fansToLink])-1],
								#   \-----------------------------/
								#      Index of fan to link. Get fan
								#	from SlaveContainer's fan list.
							
							# Second argument: row of cell to link:
							row + rowDisplacement,
					
							# Third argument: column of cell to link:
							column + columnDisplacement
						)
					
                                                # Decrement counter
                                        fansToLink -= 1

		# End _linkSlave =======================================================

	def _unlinkSlave(self, slaveContainer): # ==================================
		# ABOUT: Unlink given SlaveContainer from grid 
		# (must have valid coordinates)
		# NOTE: Usefulness replaced by _unlinkAllFans. Delete later if it proves
		# unnecessary.

		# Verify:
		if slaveContainer.coordinates is None:
			raise ValueError("Argument 'coordinates' must not be None to allow "\
				"Grid linking")
		
		else:
			# Loop over the Slave's module and unlink fans accordingly.
			
			# NOTE: Here the "coordinates" of a Slave are those of the fan
			# at the top-left position of its module's grid.

			rowDisplacement = slaveContainer.coordinates[0]
			columnDisplacement = slaveContainer.coordinates[1]

			for row in range((slaveContainer.moduleDimensions[0])):
				for column in slaveContainer.moduleDimensions[1]:
					
					# Unlink fan
					self._unlinkFan(\
						# Row of cell to unlink:
						row + rowDisplacement,
				
						# Column of cell to unlink:
						column + columnDisplacement
					)					

		# End _unlinkSlave =====================================================

	def _draw(self, l): # ======================================================
		# ABOUT: Draw a grid in which each cell has side l.

		# Initialize coordinates:
		x, y = self.margin, self.margin

		for row in range(self.rows):
			x = self.margin
			
			self.canvas.create_text(
				self.margin/2,
				y+self.cellLength/2,
				text = str(row + 1),
				font = ('TkFixedFont', 7))
			
			for column in range(self.columns):
				
				self.canvas.create_text(
					x+self.cellLength/2,
					self.margin/2,
					text = str(column + 1),
					font = ('TkFixedFont', 7))

				# Draw rectangle ij:
				iid = \
					self.canvas.create_rectangle(
					x,y, x+l,y+l, fill = MAINGRID_EMPTY)
				self.matrix[row][column][0] = iid
				self.iids[iid] = (row, column)
				
				#self.canvas.create_text(x + l/2, y + l/2, text = "{},{}".format(row,column))
				
				#self.canvas.create_text(x + l/2, y + 2*l/3, text = "{}".format(iid))
				self.canvas\
					.tag_bind(iid, '<ButtonPress-1>', self._onClick)
				
				self.canvas\
					.tag_bind(iid, '<B1-Motion>', self._onDrag)
				
				self.canvas\
					.tag_bind(iid, '<ButtonRelease-1>', self._onRelease)
				
				self.canvas\
					.tag_bind(iid, '<Double-Button-1>', 
					self._onLeftDoubleClick)
				
				self.canvas\
					.tag_bind(iid, '<Double-Button-2>', 
					self._onRightDoubleClick)
				
				x += l
			y += l
	
		# Draw color gradient:


		# Labels:

		# 0 RPM:
		self.canvas.create_text(
			2.5*self.margin, # x
			2.25*self.margin+self.cellLength*self.rows, # y
			text = "0 RPM",
			font = ('TkFixedFont', 10, 'bold'),
			anchor = 'c'
		)

		# MAX RPM:
		self.canvas.create_text(
			self.cellLength*self.columns - self.margin/2, # x
			2.25*self.margin+self.cellLength*self.rows, # y
			text = "{}\nRPM".format(self.maxRPM),
			font = ('TkFixedFont', 7, 'bold'),
			anchor = 'c',
			justify = Tk.CENTER
		)

		# Draw gradient:
		step = (self.cellLength*self.columns-6*self.margin)/255.0
			#   \---Total length of inner rectangle-----/   \--/
			#                              Total number of different colors

		leftX = 4*self.margin
		rightX = leftX + step
		constTopY = 1.5*self.margin+self.cellLength*self.rows
		constBotY = 3*self.margin+self.cellLength*self.rows
		

		for i in range(255):
			self.canvas.create_rectangle(
				leftX + step*i,
				constTopY,
				rightX + step* i,
				constBotY,
				fill = cc.MAP_VIRIDIS[i],
				width = 0
			)
		
		# Border:
		self.canvas.create_rectangle(
			# Top left corner:
			self.margin, # x
			3.0*self.margin/2+self.cellLength*self.rows, # y

			# Bottom right corner:
			self.margin+self.cellLength*self.columns, # x
			3*self.margin+self.cellLength*self.rows,  # y
			)

		# Inner border:
		self.canvas.create_rectangle(
			# Top left corner:
			4*self.margin, # x
			1.5*self.margin+self.cellLength*self.rows, # y

			# Bottom right corner:
			self.margin+self.cellLength*self.columns-3*self.margin, # x
			3*self.margin+self.cellLength*self.rows,  # y
			)

		self.canvas.config(
			width = l*self.columns + self.margin*2, 
			height = l*self.rows + self.margin*3)
		# End _draw ============================================================

	def _onClick(self, event): # ===============================================
		# ABOUT: To be called when a cell is clicked.
	
		# Get selected rectangle:
		rect = self.canvas.find_closest(
			self.canvas.canvasx(event.x), 
			self.canvas.canvasy(event.y))[0]
		
		i, j = self.iids[rect]

		# Determine status of selected rectangle:
		if self.matrix[i][j][1] is not None and \
			self.matrix[i][j][1].isActive():
			# If there is a fan linked, toggle its selection:
			self.matrix[i][j][1].toggle()

		else:
			# Do nothing is the cell is empty
			return

		# End _onClick =========================================================

	def _onDrag(self, event): # ================================================
		# ABOUT: To be called when the mouse click is "dragged."

		# Check if this is the beginning of a drag motion:
		if not self.dragging:
			# Start recording drag by saving the initial coordinates:
			self.dragOriginRow, self.dragOriginColumn = self.iids[
				self.canvas.find_closest(self.canvas.canvasx(event.x),
					self.canvas.canvasy(event.y))[0]
				]
			self.dragEndRow = self.dragOriginRow
			self.dragEndColumn = self.dragOriginColumn

			self.dragging = True
		else:
			# Update "end" coordinates:
			
			self.dragEndRow, self.dragEndColumn = self.iids[
				self.canvas.find_closest(self.canvas.canvasx(event.x),
					self.canvas.canvasy(event.y))[0]
				]

		# End _onDrag ==========================================================

	def _onRelease(self, event): # =============================================
		# ABOUT: To be called when the mouse is released. Handles possible 
		# drag-selection.
		
		# Check if there was a drag-selection:
		if self.dragging:
			# If there was a drag-selection, select all fans in the rectangle
			# with the initial and final selection as its opposite corners:

			# Go over all cells within range and select the viable fans:
			# NOTE: max and min functions are used to cover drags in all
			# directions, including those in which the initial value is 
			# greater than the final value (such as when going to the left)


			# Check drag range to ignore "single-fan" drags:
			if not (self.dragOriginRow == self.dragEndRow and \
				self.dragOriginColumn == self.dragEndColumn):
				
				for row in range(
					min(self.dragOriginRow,self.dragEndRow),
					max(self.dragOriginRow,self.dragEndRow) + 1):
					
					for column in range(
						min(self.dragOriginColumn, self.dragEndColumn),
						max(self.dragOriginColumn, self.dragEndColumn)+ 1):

						if self.matrix[row][column][1] is not None and \
							self.matrix[row][column][1].isActive():
								
							self.matrix[row][column][1].select()
			
			# Reset counters:

			self.dragging = False
			self.dragOriginColumn = -1
			self.dragOriginRow = -1
			self.dragEndColumn = -1
			self.dragEndRow = -1

		else:
			pass
		
		# End _onRelease =======================================================

	def _onLeftDoubleClick(self, event): # =====================================
		# ABOUT: To be called when the grid is double clicked (left). Selects 
		# all selectable fans.

		# Loop over the entire grid and select all possible fans:

		for row in self.matrix:
			for cell in row:
				if cell[1] is not None and cell[1].isActive():
					cell[1].select()

		# End _onLeftDoubleClick ===============================================

	def _onRightDoubleClick(self, event): # ====================================
		# ABOUT: To be called when the grid is double clicked (right). Deselects 
		# all fans.

		# Loop over the entire grid and select all possible fans:

		for row in self.matrix:
			for cell in row:
				if cell[1] is not None and cell[1].isActive():
					cell[1].select(False)

		# End _onLeftDoubleClick ===============================================


	# End Main Grid #=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=

class SlaveContainer:
	# ABOUT: Represent GUI-relevant Slave data in the Communicator module.
	# Here each SlaveInterface instance corresponds to one Slave unit in the
	# Communicator, whether connected or not.

	def __init__(self, # =======================================================
		name, mac, status, maxFans, activeFans, ip, misoMethod, mosiMethod,
		master, period_ms, slaveListIID, index, coordinates, moduleDimensions,
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
		#	Update period (ms)	variable	int
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
			self.fans.append(FanContainer(INACTIVE, self, i))

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
						self.dataIndex.set("RIP")
						self.timeouts.set("RIP")

						# Reset fan array information:
						for fan in self.fans:
							fan.reset()
							fan.setActive(INACTIVE)

					else:
						# Otherwise, update indices and IP:
						self.mosiIndex.set(str(fetchedUpdate[2]))
						self.misoIndex.set(str(fetchedUpdate[3]))
						self.timeouts.set('0')
						self.ip.set(fetchedUpdate[4])
						self.dataIndex.set(str(fetchedUpdate[5]))

						# Update fan activity:
						for fan in self.fans[:self.activeFans]:
							fan.setActive(ACTIVE)

				elif fetchedUpdate[0] == Slave.VALUE_UPDATE:
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
									int(255*(1.0*fetchedUpdate[3][0][i]/self.master.profiler.profile["maxRPM"]))]
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
				if fetchedUpdate[0] == Slave.STATUS_CHANGE:
					self.master.slaveList.item(self.slaveListIID, 
						values = [
							self.index + 1,
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
							self.index + 1,
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
				format(self.index + 1, traceback.format_exc()), "E")

		# Schedule next update -------------------------------------------------
		self.master.after(self.master.profiler.profile["periodMS"], self.update)

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
		
		if self.status != Slave.CONNECTED:
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
		return self.status == Slave.CONNECTED and self.selected > 0 

		# End hasSelected ======================================================

	# End SlaveContainer #=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#

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
					fill = MAINGRID_INACTIVE)
		
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

	def __init__(self, master, communicator,  maxFans, printM): # ==============
		# ABOUT: Constructor for class SlaveDisplay.
		# PARAMETERS:
		# - master: Tkinter container widget.
		# - communicator: Communicator instance.
		# - maxFans: maximum number of fans to be displayed.
		# - printM: Method with which to print to main terminal.

		self.background = "#d3d3d3"
		self.target = None
		self.maxFans = maxFans
		self.status = Slave.DISCONNECTED
		self.isPacked = False
		self.communicator = communicator
		self.printMain = printM
		
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
		self.indexLabel = Tk.Label(self.topFrame,
			text = "[INDEX]", relief = Tk.SUNKEN, bd = 1,
			bg = self.background, font = ('TkFixedFont', 10, 'bold'),
			padx = 5, width = 6)
		self.indexLabel.pack(side = Tk.LEFT, 
			anchor = 'w',fill = Tk.X, expand = False)

		# ......................................................................
		self.nameLabel = Tk.Label(self.topFrame,
			text = "[NAME]", relief = Tk.SUNKEN, bd = 1,
			bg = self.background, font = ('TkFixedFont', 10, 'bold'),
			padx = 5, width = 20)
		self.nameLabel.pack(side = Tk.LEFT, 
			anchor = 'w',fill = Tk.X, expand = False)

		# ......................................................................
		self.macLabel = Tk.Label(self.topFrame,
			text = "[MAC]",relief = Tk.SUNKEN, bd = 1,
			bg = self.background, font = ('TkFixedFont', 10, 'bold'),
			padx = 5, width = 18, height = 1)
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
		self.dataIndexLabel = Tk.Label(self.topFrame, text = "Data:",
			bg = self.background, font = 'TkDefaultFont 8')
		self.dataIndexLabel.pack(side = Tk.LEFT)

		self.dataIndexCounter = Tk.Label(self.topFrame, 
			text = "RIP", relief = Tk.SUNKEN, bd = 1,
			bg = "white", font = 'TkFixedFont 8',
			width = 10)
		self.dataIndexCounter.pack(side = Tk.LEFT, 
			anchor = 'w', fill = Tk.X, expand = False)
	
		# ......................................................................
		self.timeoutsLabel = Tk.Label(self.topFrame, text = "Timeouts:",
			bg = self.background, font = 'TkDefaultFont 8')
		self.timeoutsLabel.pack(side = Tk.LEFT)

		self.timeoutsCounter = Tk.Label(self.topFrame, 
			text = "RIP", relief = Tk.SUNKEN, bd = 1,
			bg = "white", font = 'TkFixedFont 8',
			width = 10)
		self.timeoutsCounter.pack(side = Tk.LEFT, 
			anchor = 'w', fill = Tk.X, expand = False)
	
		# ......................................................................
		self.selectionCounterFrame = Tk.Frame(
			self.topFrame,
			bg = self.background,
			)

		self.selectionCounter = Tk.Label(
			self.selectionCounterFrame,
			bg = self.background,
			justify = Tk.RIGHT,
			text = '--',
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
			text = '--',
			bg = self.background,
			font = ('TkFixedFont', '9'),
			width = 2)

		self.selectionCounter.pack(side = Tk.LEFT)
		self.slashLabel.pack(side = Tk.LEFT)
		self.activeCounter.pack(side = Tk.LEFT)
		self.selectionCounterFrame.pack(side = Tk.RIGHT)
	
		# BUTTONS - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
		# ......................................................................
		self.buttonFrame = Tk.Frame(self.generalFrame, bg = self.background)
		self.buttonFrame.pack(side = Tk.TOP, fill = Tk.X)

		self.connectButtonFrame = Tk.Frame(self.buttonFrame, bg = self.background,
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
		
		self.isModuleWindowActive = False
		self.moduleWindow = None
		self.customizeModuleButton = Tk.Button(
			self.buttonFrame, 
			state = Tk.DISABLED,
			text = "Customize Module",
			width = 15,
			highlightbackground = self.background,
			command = self._customizeModuleRoutine
			)

		self.customizeModuleButton.pack(side = Tk.LEFT)
		
		self.coordinatesButton = Tk.Button(
			self.buttonFrame, 
			state = Tk.DISABLED,
			text = "Set Grid Placement", 
			highlightbackground = self.background)

		self.coordinatesButton.pack(side = Tk.LEFT)

		self.swapButton = Tk.Button(
			self.buttonFrame, 
			text = "Swap", 
			state = Tk.DISABLED,
			highlightbackground = self.background)

		self.swapButton.pack(side = Tk.LEFT)

		self.removeButton = Tk.Button(
			self.buttonFrame, 
			text = "Remove", 
			state = Tk.DISABLED,
			highlightbackground = self.background)

		self.removeButton.pack(side = Tk.LEFT)


	
		# ............................................................................
		self.coordinatesFrame = Tk.Frame(
			self.buttonFrame,
			bg = self.background
			)
		
		self.coordinatesVar = Tk.StringVar()
		self.coordinatesVar.set("No Coordinates")
		self.coordinatesLabel = Tk.Label(
			self.coordinatesFrame,
			bg = self.background,
			textvariable = self.coordinatesVar,
			padx = 0,
			font = ('TkFixedFont', '9')
			)

		self.coordinatesLabel.pack()
		self.coordinatesFrame.pack(side = Tk.RIGHT)
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

		# Enable configure and swap buttons:
		#self.customizeModuleButton.config(state = Tk.NORMAL)
		self.swapButton.config(state = Tk.NORMAL)

		# Assign target:
		self.target = newTarget
		self.target.setSlaveDisplay(self)
		
		# Adjust index:
		self.indexLabel.config(text = self.target.index + 1)

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
		self.dataIndexCounter.config(textvariable = self.target.dataIndex)
		self.timeoutsCounter.config(textvariable = self.target.timeouts)
		
		# Adjust coordinates:
		if self.target.coordinates is None:
			self.coordinatesVar.set("No Coordinates")
		else:
			self.coordinatesVar.set("({},{})".\
				format(self.target.coordinates[0],
					self.target.coordinates[1]))

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
			self.communicator.add(self.target.index
			)

	def selectAll(self): # =====================================================
		# ABOUT: Set all fans as selected:
		if self.target != None:
			self.target.selectAll()

	def deselectAll(self): # ===================================================
		# ABOUT: Set all fans as selected:
		if self.target != None:
			self.target.deselectAll()

	def _customizeModuleRoutine(self): # =======================================
		# ABOUT: To be called by the grid button. Hides and shows grid in popup
		# window.
		try:
			# Check status:
			if not self.isModuleWindowActive:
				# If the grid is not active, this method activates the grid:
				
				# Error-check:
				if self.moduleWindow is not None:
					raise RuntimeError("Grid activation routine called while "\
						"grid window placeholder is active.")

				# Create pop-up window:
				self.moduleWindow = Tk.Toplevel()
				self.moduleWindow.protocol("WM_DELETE_WINDOW", 
					self._deactivateModuleWindowRoutine)
				
				# Shift focus to pop-up window:
				self.moduleWindow.lift()
				self.moduleWindow.focus_force()

				# Keep the user from using the main window before closing
				# this one:
				self.moduleWindow.grab_set()

				self.moduleGridFrame = Tk.Frame(self.moduleWindow)
				self.moduleGridFrame.pack(side = Tk.LEFT, fill = Tk.BOTH)

			

				# Disable button until pop-up is closed:
				self.customizeModuleButton.config(state = Tk.DISABLED)
				
				# Update sentinel:
				self.isModuleWindowActive = True

			else:
				# If the grid is active, this method deactivates the grid:

				# Error-check:
				if self.moduleWindow is  None:
					raise RuntimeError("Grid deactivation routine called while "\
						"grid window placeholder is inactive.")

				# Call the designated grid deactivation routine:
				self._gridDeactivationRoutine()

		except Exception as e: # Print uncaught exceptions
			self.printMain(
				"[_customizeModuleRoutine]( UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")

		# End _customizeModuleRoutine  =========================================

	def _deactivateModuleWindowRoutine(self): # ================================
			# ABOUT: Dismantle grid and grid's popup window.
			
		try:
			
			# Error-check:
			if not self.isModuleWindowActive:
				raise RuntimeError("Grid deactivation routine called on "\
					"inactive grid.")
			# Disable button to avoid conflicts:
			self.customizeModuleButton.config( state = Tk.DISABLED)

			# Destroy popup window:
			self.moduleWindow.grab_release()
			self.moduleWindow.destroy()
			self.moduleWindow = None

			# Update sentinel:
			self.isModuleWindowActive = False

			# Reconfigure button:
			self.customizeModuleButton.config(
				text = "Customize Module",
				state = Tk.ENABLED)
			
			# Done
			return

		except Exception as e: # Print uncaught exceptions
			self.printMain(
				"[_deactivateModuleWindowRoutine] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")
		# End _gridDeactivationRoutine =========================================
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
		self.setStatus(INACTIVE)

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
			if self.status == ACTIVE:
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
			if newStatus == ACTIVE:
				# Set style of an active fan:
				self.dcDisplay.configure(background = 'white')
				self.dcPercentage.configure(bg = "white")
				self.dcDisplay.bind('<Button-1>', self.toggle)

				self.rpmDisplay.configure(background = 'white')
				self.rpmDisplay.bind('<Button-1>', self.toggle)

				self.configure(background = "white")

				self.status = newStatus

			elif newStatus == INACTIVE:
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

## CLASS DEFINITION ############################################################

class FCInterface(Tk.Frame):      

	def __init__(self, version, master=None): # ================================
		Tk.Frame.__init__(self, master)

		# Initialization order:
		# 1. Build and display GUI
		# 2. Load Profile
		# 3. Start Communicator

		# INITIALIZATION STEP 1: BUILD AND DISPLAY GUI #########################

		# CONFIGURE MAIN WINDOW = = = = = = = = = = = = = = = = = = = = = = = =

		# Set title:
		self.master.title("Fan Club MkII [ALPHA]")

		# Set background:
		self.background = "#e2e2e2"
		self.config(bg = self.background)

		# Set debug foreground:
		self.debugColor = "#ff007f"

		# CREATE COMPONENTS = = = = = = = = = = = = = = = = = = = = = = = = = = 

		# MAIN FRAME -----------------------------------------------------------
		self.main = Tk.Frame(self)
		self.main.pack(fill = Tk.BOTH, expand = True)

		# OPTIONS BAR ----------------------------------------------------------
		self.optionsBarFrame = Tk.Frame(
			self.main,
			relief = Tk.GROOVE,
			bd = 1,
			bg = self.background
		)

		self.optionsBarFrame.pack(side = Tk.TOP, fill = Tk.X)

		# TERMINAL TOGGLE ......................................................
		self.terminalToggleVar = Tk.BooleanVar()
		self.terminalToggleVar.set(False)

		self.terminalToggle = Tk.Checkbutton(self.optionsBarFrame, 
			text ="Terminal", variable = self.terminalToggleVar, 
			bg = self.background, command = self._terminalToggle)
		self.terminalToggle.config( state = Tk.NORMAL)
		self.terminalToggle.pack(side = Tk.LEFT)

		# SLAVE LIST TOGGLE ....................................................
		self.slaveListToggleVar = Tk.BooleanVar()
		self.slaveListToggleVar.set(False)

		self.slaveListToggle = Tk.Checkbutton(self.optionsBarFrame,
			text ="List", variable = self.slaveListToggleVar, 
			bg = self.background, command = self._slaveListToggle)

		self.slaveListToggle.config( state = Tk.NORMAL)
		self.slaveListToggle.pack(side = Tk.LEFT)

		# SLAVE DISPLAY TOGGLE .................................................
		self.slaveDisplayToggleVar = Tk.BooleanVar()
		self.slaveDisplayToggleVar.set(False)

		self.slaveDisplayToggle = Tk.Checkbutton(self.optionsBarFrame,
			text ="Display", variable = self.slaveDisplayToggleVar, 
			bg = self.background, command = self._slaveDisplayToggle)

		self.slaveDisplayToggle.config( state = Tk.NORMAL)
		self.slaveDisplayToggle.pack(side = Tk.LEFT)

		# SETTINGS BUTTON ......................................................
		self.settingsButton = Tk.Button(
			self.optionsBarFrame,
			text = "Help",
			highlightbackground = self.background,
			state = Tk.DISABLED
		)
		self.settingsButton.pack(side = Tk.RIGHT)	

		# SETTINGS BUTTON ......................................................
		self.settingsButton = Tk.Button(
			self.optionsBarFrame,
			text = "Settings",
			highlightbackground = self.background
		)
		self.settingsButton.pack(side = Tk.RIGHT)	

		# PLOT BUTTON ..........................................................
		self.plotButton = Tk.Button(
			self.optionsBarFrame,
			text = "Activate Plot",
			highlightbackground = self.background,
			state = Tk.DISABLED
		)
		self.plotButton.pack(side = Tk.RIGHT)	

		# GRID BUTTON ..........................................................
		self.gridButton = Tk.Button(
			self.optionsBarFrame,
			text = "Activate Grid",
			width = 10,
			highlightbackground = self.background,
			command = self._gridButtonRoutine
		)
		self.gridButton.pack(side = Tk.RIGHT)	
		
		# Keep track of grid activity:
		self.isGridActive = False
		# Placeholder for reference to popup window:
		self.gridWindow = None
		self.grid = None

		# MAIN DISPLAY ---------------------------------------------------------

		# Main display frame ..................................................
		self.mainDisplayFrame = Tk.Frame(
			self.main, height = 100, bg = '#212121')

		#self.mainDisplayFrame.pack(
			#fill = Tk.BOTH, expand = True, side = Tk.TOP)

		# ARRAY ----------------------------------------------------------------

		# Array Frame ..........................................................
		self.arrayFrame = Tk.Frame(self.mainDisplayFrame, bg = 'white',
			relief = Tk.SUNKEN, borderwidth = 3)
		
		# TERMINAL -------------------------------------------------------------
		self.terminalContainerFrame = Tk.Frame(self.main, bg = self.background)
		self.terminalContainerFrame.pack(
			side = Tk.BOTTOM, fill = Tk.X, expand = False, anchor = 's')

		self.terminalFrame = Tk.Frame(self.terminalContainerFrame,
			bg = self.background, bd = 1, relief = Tk.GROOVE)
		#self.terminalFrame.pack(fill = Tk.BOTH, expand = False)
		# Comment out to not start w/ hidden terminal by default

		# MAIN TERMINAL - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
		self.mainTerminal = ttk.Frame(self.terminalFrame)
		self.mainTerminal.pack(fill = Tk.BOTH, expand = False)
		self.mainTLock = threading.Lock()
		self.mainTText = Tk.Text(self.mainTerminal, height = 10, 
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

		# SLAVE LIST -----------------------------------------------------------

		# Slave list container .................................................
		self.slaveListContainer = Tk.Frame(self.main)
		self.slaveListContainer.pack(
			side = Tk.BOTTOM, fill = Tk.BOTH, expand = True, anchor = 's')

		# Slave list frame .....................................................
		self.slaveListFrame = Tk.Label(self.slaveListContainer,
			bg = self.background, borderwidth = 1, relief = Tk.GROOVE)
		#self.slaveListFrame.pack(fill = Tk.BOTH, expand = True)

		# List of Slaves .......................................................

		# Create list:
		self.slaveList = ttk.Treeview(self.slaveListFrame, 
			selectmode="browse", height = 5)
		self.slaveList["columns"] = \
			("Index", "Name","MAC","Status","IP","Fans")

		# Create columns:
		self.slaveList.column('#0', width = 20, stretch = False)
		self.slaveList.column("Index", width = 20, anchor = "center")
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
		self.slaveList.heading("Index", text = "Index")
		self.slaveList.heading("Name", text = "Name")
		self.slaveList.heading("MAC", text = "MAC")
		self.slaveList.heading("Status", text = "Status")
		self.slaveList.heading("IP", text = "IP")
		self.slaveList.heading("Fans", text = "Fans")

		# Configure tags:
		self.slaveList.tag_configure(
			"C", 
			background= '#d1ffcc', 
			foreground = '#0e4707', 
			font = 'TkFixedFont 12 ') # Connected
		
		self.slaveList.tag_configure(
			"B", 
			background= '#ccdeff', 
			foreground ='#1b2d4f', 
			font = 'TkFixedFont 12 ') # Busy

		self.slaveList.tag_configure(
		"D", 
		background= '#ffd3d3', 
		foreground ='#560e0e', 
		font = 'TkFixedFont 12 bold')# Disconnected

		self.slaveList.tag_configure(
		"K",
		background= '#fffaba',
		foreground ='#44370b',
		font = 'TkFixedFont 12 bold') # Known

		self.slaveList.tag_configure(
		"A", 
		background= '#ededed', 
		foreground ='#666666',
		font = 'TkFixedFont 12 ') # Available

		# Save previous selection:
		self.oldSelection = None

		# Bind command:
		self.slaveList.bind('<Double-1>', self._slaveListMethod)

		self.slaveList.pack(fill = Tk.BOTH, expand = True, anchor = 's')

		
		# SLAVE DISPLAY --------------------------------------------------------
		# Slave display frame ..................................................
		self.slaveDisplayFrame = Tk.Frame(self.main,
			bg = self.background,
			bd = 1,
			relief = Tk.GROOVE)
		self.slaveDisplayFrame.pack(
			side = Tk.BOTTOM, fill = Tk.X, expand = False, anchor = 's')


		# CONTROL --------------------------------------------------------------
		self.controlFrame = Tk.Frame(self, 
			relief = Tk.GROOVE, borderwidth = 1,
			bg=self.background)

		self.controlFrame.pack(fill = Tk.X, expand = False)

		
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
		

		# Shutdown button frame:
		self.shutdownButtonFrame = Tk.Frame(
			self.arrayControlFrame, 
			relief = Tk.RIDGE, 
			borderwidth = 1)
		self.shutdownButtonFrame.pack(
			side = Tk.RIGHT, expand = False)

		# Shutdown button:
		self.shutdownButton = Tk.Button(self.shutdownButtonFrame,
			highlightbackground = "#890c0c", text = "SHUTDOWN",
			command = self._shutdownButton, font = 'TkFixedFont 12 bold ')
		self.shutdownButton.pack()
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


		# PRINTING -------------------------------------------------------------
		self.printContainerFrame = Tk.Frame(self, 
			relief = Tk.GROOVE, borderwidth = 1,
			bg=self.background)

		self.printContainerFrame.pack(fill = Tk.X, expand = False)

		self.printFrame = Tk.Frame(self.printContainerFrame,
			bg = self.background)
		self.printFrame.pack(anchor = 'c')
		
		# Print timer:
		self.printTimerVar = Tk.StringVar()
		self.printTimerVar.set("00:00:00s")

		self.printTimerSeconds = 0
		self.printTimerMinutes = 0
		self.printTimerHours = 0
		self.printTimerStopFlag = False

		self.printTimerLabel = Tk.Label(
			self.printFrame,
			bg = self.background,
			bd = 1,
			relief = Tk.SUNKEN,
			font = ('TkFixedFont', '12'),
			width = 12,
			padx = 4,
			textvariable = self.printTimerVar
		)

		self.printTimerLabel.pack(side = Tk.RIGHT)


		self.printTimerPadding = Tk.Frame(
			self.printFrame,
			width = 20,
			bg = self.background
		)
		self.printTimerPadding.pack(side = Tk.RIGHT, expand = False)

		# Print target (file) label:
		self.printTargetLabel = Tk.Label(self.printFrame,
			background = self.background,
			text = "Record data to: "
			)

		self.printTargetLabel.pack(side = Tk.LEFT)

		# Print target text field:

		self.entryRedBG = "#ffc1c1"
		self.entryOrangeBG = "#ffd8b2"
		self.entryWhiteBG = "white"

		self.printTargetVar = Tk.StringVar()
		self.printTargetVar.trace('w', self._fileNameEntryCheck)


		self.printTargetEntry = Tk.Entry(self.printFrame, 
			highlightbackground = self.background,
			width = 17, bg = self.entryRedBG,
			textvariable = self.printTargetVar)
		self.printTargetEntry.pack(side = Tk.LEFT)
 
		self.printTargetStatus = EMPTY

		# printTarget button:
		self.printTargetButton = Tk.Button(self.printFrame, 
			highlightbackground = self.background, text = "...", 
			command = self._printTargetButtonRoutine)

		self.printTargetButton.pack(side = Tk.LEFT)
		
		# Print padding:
		self.printPadding2 = Tk.Frame(self.printFrame,
			bg = self.background,
			width = 5
			)
		self.printPadding2.pack(side = Tk.LEFT)
		
		# printTarget feedback:
		self.printTargetFeedbackLabel = Tk.Label(
			self.printFrame,
			bg = self.background,
			text = '(No filename)',
			fg = 'darkgray',
			anchor = 'w',
			width = 12
			)
		self.printTargetFeedbackLabel.pack(side = Tk.LEFT)
	
		# Print padding:
		self.printPadding1 = Tk.Frame(self.printFrame,
			bg = self.background,
			width = 20
			)
		self.printPadding1.pack(side = Tk.LEFT)

		# printStartStop button:
		self.printStartStopButton = Tk.Button(self.printFrame, 
			highlightbackground = self.background, text = "Start Recording",
			width = 12,
			command = self._printButtonRoutine,
			)

		self.printStartStopButton.config(state = Tk.DISABLED)

		self.printStartStopButton.pack(side = Tk.LEFT)
		
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

		# Selected Slaves:
		self.selectedSlavesLabel = Tk.Label(
			self.selectionCounterFrame,
			bg = self.background,
			text = "Selected Modules: ",
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
			text = "Selected Fans: ",
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


		# Initialize Profiler --------------------------------------------------
		self.profiler = Profiler.Profiler() 
		self.printMain("Profiler initialized", "G")
		
		# Initialize Slave data structure --------------------------------------
		self.slaveContainers = np.empty(0, dtype = object)

		# Initialize Printer ---------------------------------------------------
		self.printer = Printer.Printer(
			queueSize = self.profiler.profile["printerQueueSize"],
			fanMode = self.profiler.profile["fanMode"]
		)

		# Initialize Communicator ----------------------------------------------
		self.communicator = Communicator.Communicator(
			self.profiler.slaveList,
			self.profiler.profile
			)
		self.printMain("Communicator initialized", "G")
		
		# Initialize SlaveDisplay (requires Communicator):
		self.slaveDisplay = SlaveDisplay(
			self.slaveDisplayFrame, 
			self.communicator, 
			self.profiler.profile["maxFans"],
			self.printMain)

		# START UPDATE ROUTINES = = = = = = = = = = = = = = = = = = = = = =

		# PACK -----------------------------------------------------------------
		self.pack(fill = Tk.BOTH, expand = True)
		# Center starting place:
		#                         Y-place
		#                      X-place  |       
		#                    Height  |  |
		#                  Width  |  |  |
		#                      |  |  |  |
		
		self.master.geometry('+%d+%d' % ( \
			(self.master.winfo_screenwidth()/5),      \
			(self.master.winfo_screenheight()/8)        \
			)                                           \
		)
		self.master.update_idletasks() # Required to set minimum size	
		self.printMain("Fan Club MkII Interface initialized", "G")
		
		# Deactivate resizing:
		self.master.resizable(True, True)

		"""
		self.master.geometry('%dx%d+%d+%d' % (960, 630, \
			(self.master.winfo_screenwidth()/5),      \
			(self.master.winfo_screenheight()/8)        \
			)                                           \
		)
		self.master.update() # Required to set minimum size	
		self.printMain("Fan Club MkII Interface initialized", "G")
		"""
	
		# DETERMINE MINIMUM SIZES:
		self.master.withdraw()
		# When only the essential "bars" are packed:
		self.masterMinimumSize = \
			(self.master.winfo_width(),self.master.winfo_height())

		# When only the slave display is packed:
		self.slaveDisplayToggleVar.set(True)
		self._slaveDisplayToggle(False)
		self.master.update_idletasks() # Required to set minimum size	
		self.slaveDisplayMinimumSize = \
			(self.master.winfo_width(),self.master.winfo_height())
		
		# When the slave list is packed:	
		self.slaveDisplayToggleVar.set(False)
		self._slaveDisplayToggle(False)
		self.slaveListToggleVar.set(True)
		self._slaveListToggle(False)
		
		self.master.update_idletasks() # Required to set minimum size	
		self.slaveListMinimumSize = \
			(self.master.winfo_width(),self.master.winfo_height())

		# When the terminal is packed:	
		self.slaveDisplayToggleVar.set(False)
		self._slaveDisplayToggle(False)
		self.slaveListToggleVar.set(False)
		self._slaveListToggle(False)
		self.terminalToggleVar.set(True)
		self._terminalToggle(False)
		
		self.master.update_idletasks() # Required to set minimum size	
		self.terminalMinimumSize = \
			(self.master.winfo_width(),self.master.winfo_height())
	
		# Pack widgets after determining minimum size:
		self.slaveDisplayToggleVar.set(True)
		self._slaveDisplayToggle()
		self.slaveListToggleVar.set(True)
		self._slaveListToggle()
		self.terminalToggleVar.set(False)
		self._terminalToggle()
		
		self.master.update_idletasks()
		self.master.deiconify()

		# ----------------------------------------------------------------------
		self._mainPrinterRoutine()	
		self._newSlaveChecker()
		self._broadcastThreadChecker()
		self._listenerThreadChecker()
		

		# Focus on the main window:
		self.master.lift()
		
		# End FCInterface Constructor ==========================================

## UPDATE ROUTINES # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

	def _mainPrinterRoutine(self): # ===========================================
		# ABOUT: Keep main terminal window updated w/ Communicator output. To be
		
		if self.terminalVar.get() == 0:
			pass

		else: 

			# COMMUNICATOR QUEUE

			try: # NOTE: Use try/finally to guarantee lock release.

				# Fetch item from Communicator queue:
				output, tag = self.printer.mainQueue.get_nowait()

				# If there is an item, print it (otherwise, Empty exception is
				# raised and handled)
				
				# Check for debug tag:
				if tag is "D" and self.debugVar.get() == 0:
					# Do not print if the debug variable is set to 0
					pass

				else:

					# Switch focus to this tab in case of errors of warnings:
					if tag is "E":
						self.terminalToggleVar.set(True)
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

			# PRINTER QUEUE

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
						self.terminalToggleVar.set(True)
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
			if fetched is None:
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
						period_ms = self.profiler.profile["periodMS"],
						slaveListIID =	self.slaveList.insert(
							'', 'end', 
							values = (
							fetched[8] + 1,
							fetched[0], # name 
							fetched[1], # MAC 
							Slave.translate(fetched[2]), # Status as str
							fetched[5],	 # IP as str
							fetched[4]), # Active fans as int 
							tag = Slave.translate(fetched[2], True)),
										#        \------/ Status (int)
						index = fetched[8],
						coordinates = fetched[9],
						moduleDimensions = fetched[10],
						moduleAssignment = fetched[11]
					)
				
				# Add to SlaveContainer array:
				self.slaveContainers = \
					np.concatenate((
						self.slaveContainers, 
						(newSlaveContainer,)
						))

				# Add to Printer's list:
				self.printer.add(
					mac = fetched[1], # MAC
					index = fetched[8], # Index
					activeFans = fetched[4], # Active fans
				)
			
			# Schedule next call -----------------------------------------------
			self.after(
				self.profiler.profile["periodMS"], self._newSlaveChecker)

		except Exception as e: # Print uncaught exceptions
			self.printMain("[NS] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")
			self.main.after(self.profiler.profile["periodMS"], self._newSlaveChecker)
		# End _newSlaveChecker =================================================

	def _broadcastThreadChecker(self): # =======================================
		# ABOUT: Check whether the communicator's broadcast thread is alive and
		# update the corresponding GUI display. 
		# NOTE: This is a "periodic" method, in that it will schedule a future
		# call to itself using Tkinter's "after" method.

		# Check thread:
		if self.communicator.isBroadcastThreadAlive():
			# Use update method to alternate between greens:
			self.broadcastDisplayUpdate()	
		
		else:
			# Use update method to set red color:
			self.broadcastDisplayUpdate("R")

		# Schedule future call:
		self.after(self.profiler.profile["broadcastPeriodMS"], 
			self._broadcastThreadChecker)

		# End _broadcastThreadChecker ==========================================

	def _listenerThreadChecker(self): # ========================================
		# ABOUT: Check whether the communicator's listener thread is alive and
		# update the corresponding GUI display. 
		# NOTE: This is a "periodic" method, in that it will schedule a future
		# call to itself using Tkinter's "after" method.

		# Check thread:
		if self.communicator.isListenerThreadAlive():
			# Use update method to alternate between greens:
			self.listenerDisplayUpdate()	
		
		else:
			# Use update method to set red color:
			self.listenerDisplayUpdate("R")

		# Schedule future call:
		self.after(1000, self._listenerThreadChecker)

		# End _listenerThreadChecker ===========================================

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

		elif code == "G":
			# Set status to alternate green:
			self.listenerDisplay.config(background = self.broadcastGREEN2)
			self.listenerStatus = GREEN2
			

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
				self.terminalToggleVar.set(True)
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

	def _gridButtonRoutine(self): # ============================================
		# ABOUT: To be called by the grid button. Hides and shows grid in popup
		# window.
		try:
			# Check status:
			if not self.isGridActive:
				# If the grid is not active, this method activates the grid:
				
				# Error-check:
				if self.gridWindow is not None:
					raise RuntimeError("Grid activation routine called while "\
						"grid window placeholder is active.")

				# Activate grid:
				self.gridWindow = Tk.Toplevel()
				self.gridWindow.protocol("WM_DELETE_WINDOW", 
					self._gridDeactivationRoutine)

				self.grid = MainGrid(
					self.gridWindow,
					self.profiler.profile["dimensions"][0],
					self.profiler.profile["dimensions"][1],
					600/self.profiler.profile["dimensions"][0],
					self.slaveContainers,
					self.profiler.profile["maxRPM"]
					)
			
				# Update button format:
				self.gridButton.config(text = "Deactivate Grid")
				
				# Update sentinel:
				self.isGridActive = True

			else:
				# If the grid is active, this method deactivates the grid:

				# Error-check:
				if self.gridWindow is  None:
					raise RuntimeError("Grid deactivation routine called while "\
						"grid window placeholder is inactive.")

				# Call the designated grid deactivation routine:
				self._gridDeactivationRoutine()

		except Exception as e: # Print uncaught exceptions
			self.printMain("[_gridButtonRoutine] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")

		# End gridButtonRoutine ================================================

	def _gridDeactivationRoutine(self): # ======================================
			# ABOUT: Dismantle grid and grid's popup window.
			
		try:
			
			# Error-check:
			if not self.isGridActive:
				raise RuntimeError("Grid deactivation routine called on "\
					"inactive grid.")
			# Disable button to avoid conflicts:
			self.gridButton.config( state = Tk.DISABLED)

			# Destroy grid:
			self.grid.destroy()
			self.grid = None

			# Destroy popup window:
			self.gridWindow.destroy()
			self.gridWindow = None

			# Update sentinel:
			self.isGridActive = False

			# Reconfigure button:
			self.gridButton.config(
				text = "Activate Grid",
				state = Tk.NORMAL)
			
			# Done
			return

		except Exception as e: # Print uncaught exceptions
			self.printMain("[_gridButtonRoutine] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")
		# End _gridDeactivationRoutine =========================================

	def _printTimerRoutine(self): # ============================================
		# ABOUT: Update the Printer timer periodically for as long as it is
		# active. This method is meant to be called by whatever component acti-
		# vates the Printer (i.e starts printing).

		# Check Printer status:
		if not self.printTimerStopFlag:
			# Update timer label
			self.printTimerSeconds += 1

			if self.printTimerSeconds >= 60:
				self.printTimerSeconds = 0
				self.printTimerMinutes += 1

				if self.printTimerMinutes >= 60:
					self.printTimerMinutes = 0
					self.printTimerHours += 1
					
					if self.printTimerHours >= 99:
						self.printTimerHours = 99
			
			self.printTimerVar.set("{:02d}:{:02d}:{:02d}s".format(
				self.printTimerHours,
				self.printTimerMinutes,
				self.printTimerSeconds))

			self.after(1000, self._printTimerRoutine)

		else:
			# Reset timer label and end chain of calls:
			self.printTimerSeconds = 0
			self.printTimerMinutes = 0
			self.printTimerHours = 0
			self.printTimerVar.set("00:00:00s")
			return


		# End _printTimerRoutine ===============================================

	def _printTargetButtonRoutine(self): # =====================================
		# ABOUT: To be used by file name button. 
		# Sets file name and stops Printer.
		try:
			
			# Proceed in accordance w/ Printer status:
			if self.printer.getStatus() == Printer.OFF:
				# If the printer is off, choose a file name.

				# Disable print button while choosing file:
				self.printStartStopButton.config(state = Tk.DISABLED)

				self.printTargetVar.set(tkFileDialog.asksaveasfilename(
					initialdir = os.getcwd(), # Get current working directory
					title = "Choose file",
					filetypes = (("Text files","*.txt"),("CSV files", "*.csv"),
						("All files","*.*"))
					))
				
				# Set the visibility to the right end of the file name:
				self.printTargetEntry.xview_moveto(1)

			elif self.printer.getStatus() is Printer.ON:
					
				raise RuntimeError("Cannot use target file specifier while "\
					"printing")
			else:
				# Unrecognized printer status (wot)
				raise RuntimeError("Unrecognized Printer status {} (wot)".\
					format(self.printer.getStatus()))
		except Exception as e:
			self.printMain("[printTargetButton] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")

		# End _printTargetButtonRoutine ========================================

	def _printButtonRoutine(self): # ===========================================
		# ABOUT: To be used by Printer Start/Stop button. Starts and stops 
		# Printer.
		try:
			# Deactivate print target button to prevent timing conflicts:
			self.printTargetButton.config(state = Tk.DISABLED) 
			self.printTargetEntry.config(state=Tk.DISABLED)

			# Check state of printer:
			if self.printer.getStatus() == Printer.OFF:
				# If the printer is not active, activate it:
				
				# Fetch file name:
				fetchedFileName = self.printTargetVar.get()

				# Validate statuses:
				if self.printTargetStatus in (EMPTY, BADEXT):
					raise RuntimeError("Cannot print to file with target file "\
						"status code {}".format(self.printTargetStatus))

				elif self.printTargetStatus in (NODOT, NODOT_REPEATED):
					# Add extension:
					fetchedFileName += ".txt"

				# Start printer:
				self.printer.start(
					fileName = fetchedFileName,
					profileName = self.profiler.profile["name"],
					maxFans = self.profiler.profile["maxFans"],
					periodS = self.profiler.profile["periodS"]
				)

				# Modify buttons upon successful printer startup:

				# Check if the change was successful:
				if self.printer.getStatus() == Printer.ON:
					self.printStartStopButton.config(text = "Stop Recording")
					
					# Start timer:
					self.printTimerStopFlag = False
					self._printTimerRoutine()
				else:
					# Reactivate printTargetButton (upon init. failure)
					self.printTargetButton.config(state = Tk.NORMAL)

			elif self.printer.getStatus() == Printer.ON:
				# If the printer is active, shut it down
				
				# Deactivate Printer-related components while shutdown completes:
				self.printTargetButton.config(state = Tk.DISABLED)
				self.printStartStopButton.config(state = Tk.DISABLED)
				self.printTargetEntry.config(state = Tk.DISABLED)
				self.printTargetFeedbackLabel.config(text = "Stopping...")
				self.printTimerLabel.config(state = Tk.DISABLED)
				self.printTimerStopFlag = True

				# Stop Printer. Use short-lived thread to keep GUI responsive:
				temp = threading.Thread(target = self.printer.stop)
				temp.setDaemon(True)
				temp.start() # Will end on its own

				# Start "check" routine to restore interface once Printer is
				# done shutting down:
				self._printStopRoutine()
					
			else: 
				# Unrecognized printer status (Wot)
				raise RuntimeError("Unrecognized Printer status {} (wot)".\
					format(self.printer.getStatus()))
			
		except Exception as e:
			self.printMain("[printButton] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")

		# End _printButtonRoutine ==============================================

	def _printStopRoutine(self): # ===========================================
		# ABOUT: Schedules itself for future calls until the Printer module is
		# done terminating. When the Printer module is done, restores buttons
		# and fields.

		# Check Printer status:
		if self.printer.getStatus() == Printer.OFF:
			# Restore buttons 
			self.printStartStopButton.config(text = "Start Recording")
			self.printTargetEntry.config(state = Tk.NORMAL)
			self.printTargetButton.config(state = Tk.NORMAL)
			self.printTimerLabel.config(state = Tk.NORMAL)
			self.printTargetStatus = RESTORE
				# "Modify" targetFileVar to fire its trace callback:
			self.printTargetVar.set(self.printTargetVar.get())
			

		else:
			# Schedule future call to check again:
			self.after(200, self._printStopRoutine)

		# End _printerStopRoutine ==============================================

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
			self.commandLabelText.set("  DC: ")

		elif newValue == "Chase RPM":
			self.commandLabelText.set("RPM: ")

	def _terminalToggle(self, updateMinSize = True): # =========================
		# ABOUT: Hide and show the terminal

		# Update geometry:
		if updateMinSize:
			self._updateMinSize()
		
		# Check variable:
		if self.terminalToggleVar.get():
			# Build terminal:
			self.terminalFrame.pack(fill = Tk.BOTH, expand = False)
			self.terminalVar.set(1)
		else:
			# Hide terminal:
			self.terminalFrame.pack_forget()
			self.terminalContainerFrame.configure(height = 1)

	def _slaveListToggle(self, updateMinSize = True): # ========================
		# ABOUT: Hide and show the Slave list

		# Update geometry:
		if updateMinSize:
			self._updateMinSize()

		# Check variable:
		if self.slaveListToggleVar.get():
			# Build slaveList:
			self.slaveListFrame.pack(fill = Tk.BOTH, expand = True)
		else:
			# Hide slaveList:
			self.slaveListFrame.pack_forget()
			self.slaveListContainer.configure(height = 1)

	def _slaveDisplayToggle(self, updateMinSize = True): # =====================
		# ABOUT: Hide and show the Slave list

		# Update geometry:
		if updateMinSize:
			self._updateMinSize()

		# Check variable:
		if self.slaveDisplayToggleVar.get():
			self.slaveDisplay.pack()
			self.slaveDisplay.isPacked = True
		else:
			self.slaveDisplay.pack_forget()
			self.slaveDisplayFrame.configure(height = 1)
			self.slaveDisplay.isPacked = False

	def _updateMinSize(self): # =================================================
		# ABOUT: Check whether the current window size is enough for the current
		# widget configuration and update geometry and minimum size accordingly.
		# (Relies on the minimums set during configuration.)

		# Determine required minimum size:
			# NOTE: Add the minimum size requirement of each currently activated
			# widget.
		
		baseReqY = self.masterMinimumSize[1]
		baseReqX = self.masterMinimumSize[0]
		totalReqY = baseReqY
		totalReqX = baseReqX
		

		if self.slaveDisplayToggleVar.get():
			totalReqY += self.slaveDisplayMinimumSize[1] - baseReqY
			totalReqX += self.slaveDisplayMinimumSize[0] - baseReqX
		if self.slaveListToggleVar.get():
			totalReqY += self.slaveListMinimumSize[1] - baseReqY
		if self.terminalToggleVar.get():
			totalReqY += self.terminalMinimumSize[1] - baseReqY


		self.master.update_idletasks()
		# Update minimum size:
		self.master.minsize(
			totalReqX,
			totalReqY
		)

		# Check against current size:
		if self.master.winfo_width() < self.masterMinimumSize[0] or\
			self.master.winfo_height() < totalReqY:
			self.master.update_idletasks()
			# Reset geometry to allow for automatic window resizing:
			self.winfo_toplevel().wm_geometry("")
		return

	def _shutdownButton(self): # ===============================================
		# ABOUT: To be bound to shutdownButton

		self.printMain("WARNING: SHUTDOWN BUTTON NOT YET IMPLEMENTED", "E")

	def _slaveListMethod(self, event): # =======================================
		# ABOUT: Handle selections on SlaveList
	
		# Ensure the list is not empty:
		if self.totalSlaves == 0:
			# If there are no Slaves, there is nothing to select
			return

		currentSelection = self.slaveList.item(
			self.slaveList.selection()[0],"values")[0]

		if self.oldSelection != currentSelection:
			self.slaveDisplay.setTarget(
				self.slaveContainers[int(currentSelection) - 1])
				#                                          \--/
				#                 Compensate displacement <-/
			self.oldSelection = currentSelection

		if not self.slaveDisplay.isPacked:
			self.slaveDisplay.pack()
			self.slaveDisplayToggleVar.set(True)
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

			for slaveContainer in self.slaveContainers:

				if slaveContainer.hasSelected():
					# If it has at least one fan selected, add this to its queue:
					try:
						command = "{}~{}".format(
							commandKeyword, \
							slaveContainer.getSelection())
						slaveContainer.mosiMethod(command, False)
						# Deselect fans if instructed to do so:
						if not self.keepSelectionVar.get():
							slaveContainer.select(None, False)
						# Update sentinel:
						sent = True
						
					except Queue.Full:
						self.printMain( "[{}] "\
							"Warning: Outgoing command Queue full. "\
							"Could not send message".\
							format(slaveContainer.index + 1), "E")

			# Check sentinel:
			if sent:
				# Erase text:
				self.commandEntry.delete(0, Tk.END)
				
		except Exception as e:
			self.printMain("[_send()] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")

	def _connectAllSlaves(self): # =========================================
		# ABOUT: Connect to all AVAILABLE Slaves, if any.

		# Loop over Slaves and add all AVAILABLE ones:
		for slaveContainer in self.slaveContainers:
			if slaveContainer.status == Slave.AVAILABLE:
				self.communicator.add(slaveContainer.index)

		# End addAllSlaves =============================================
	
	def _fileNameEntryCheck(self, *args): # ====================================
		# ABOUT: Validate the file name entered.
		# Get file name:
		prospectiveFileName = self.printTargetVar.get()
		# Set sentinel:
		normal = True
	
		# Check file name:
		if prospectiveFileName == '' and self.printTargetStatus != EMPTY:
			#                           \-----------------------------/
			#								Avoid redundant changes
			# Can't print:
			self.printStartStopButton.config(state = Tk.DISABLED)
			self.printTargetEntry.config(bg = self.entryRedBG)
			self.printTargetFeedbackLabel.config(text = "(No filename)")
			self.printTargetStatus = EMPTY

			# Done
			return

		elif '.' not in prospectiveFileName:
			# No extension. Assume .txt and warn:
			normal = False
			
			if self.printTargetStatus != NODOT:

				self.printTargetEntry.config(bg = self.entryWhiteBG)
				self.printTargetFeedbackLabel.config(text = '(.txt assumed)')
				self.printStartStopButton.config(state = Tk.NORMAL)
				prospectiveFileName += ".txt"

				self.printTargetStatus = NODOT

		elif prospectiveFileName.split('.')[-1] == '':
			# Invalid extension:
			normal = False

			if self.printTargetStatus != BADEXT:

				self.printStartStopButton.config(state = Tk.DISABLED)
				self.printTargetEntry.config(bg = self.entryRedBG)
				self.printTargetFeedbackLabel.config(text = "(Bad extension)")

				self.printTargetStatus = BADEXT

		# Check for repetition
		if os.path.isfile(prospectiveFileName) and \
			self.printTargetStatus != REPEATED:
			# Change color and warn:
			self.printTargetEntry.config(bg = self.entryOrangeBG)
			self.printTargetFeedbackLabel.config(text = 'FILE EXISTS')
			self.printStartStopButton.config(state = Tk.NORMAL)
			
			if self.printTargetStatus == NODOT:
				self.printTargetStatus = NODOT_REPEATED
			else:
				self.printTargetStatus = REPEATED

		elif normal and self.printTargetStatus != NORMAL:
			# If this block of code is reached, then the prospective filename is
			# - Not empty
			# - Not missing an extension, and
			# - Not repeated
		
			# Therefore, mark it as NORMAL:
			self.printTargetEntry.config(bg = self.entryWhiteBG)
			self.printTargetFeedbackLabel.config(text = '')
			self.printStartStopButton.config(state = Tk.NORMAL)

			self.printTargetStatus = NORMAL

		# End _fileNameEntryCheck ==============================================

## INTERFACE METHODS # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

	def selectAllSlaves(self): # ===============================================
		# ABOUT: To be bound to the "Select All" button (selects all fans in all
		# Slaves)
		
		for slaveContainer in self.slaveContainers:
			slaveContainer.selectAll()
		# End selectAllSlaves ==================================================

	def deselectAllSlaves(self): # =============================================
		# ABOUT: To be bound to the "Deselect All" button (deselects all fans 
		# in all Slaves)
		
		for slaveContainer in self.slaveContainers:
			slaveContainer.deselectAll()
		
		# End deselectAllSlaves ================================================



