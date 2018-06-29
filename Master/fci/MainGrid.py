################################################################################
## Project: Fan Club Mark II "Master" # File: MainGrid.py                     ##
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
Graphical representation of the fan array as a TkInter widget.

"""
################################################################################

## DEPENDENCIES ################################################################
from mttkinter import mtTkinter as Tk
import cellcolors as cc

## CONSTANTS ###################################################################

# MainGrid cell colors
MAINGRID_EMPTY = "white"
MAINGRID_NOTSELECTED = "darkgray"
MAINGRID_SELECTED = "orange"
MAINGRID_INACTIVE = "#282828" 

## CLASS DEFINITION ############################################################

class MainGrid(Tk.Frame, object):
	# ABOUT: 2D grid to represent fan array.

	def __init__(self, master, rows, columns, cellLength, slaves, maxRPM):
		# ABOUT: Constructor for class MainGrid.

		# Call parent constructor (for class Frame):
		super(MainGrid, self).__init__(master)
		self.config(cursor = "crosshair")

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
