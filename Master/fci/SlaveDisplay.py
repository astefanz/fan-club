################################################################################
## Project: Fan Club Mark II "Master" # File: SlaveDisplay.py                 ##
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
Custom TkInter widget to display Slave-specific information.

"""
################################################################################

## DEPENDENCIES ################################################################

# System:
import traceback

# GUI:
from mttkinter import mtTkinter as Tk

# FCMkII:
import FCSlave as sv
import FanContainer as fr
import FanDisplay as fd

## CLASS DEFINITION ############################################################

class SlaveDisplay(Tk.Frame):

	def __init__(self, master, connectM, disconnectM, killM, printM): # ============================
		# ABOUT: Constructor for class SlaveDisplay.
		# PARAMETERS:
		# - master: Tkinter container widget.
		# - connectM: Method to call to connect to a Slave (will pass index)
		# - printM: Method with which to print to main terminal.

		self.background = "#d3d3d3"
		self.foreground = "black"
		self.target = None
		self.maxFans = 0
		self.status = sv.DISCONNECTED
		self.isPacked = False
		self.printMain = printM
		self.connectMethod = connectM
		self.disconnectMethod = disconnectM
		self.rebootMethod = killM
		
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
			padx = 5, width = 6, fg = self.foreground)
		self.indexLabel.pack(side = Tk.LEFT, 
			anchor = 'w',fill = Tk.X, expand = False)

		# ......................................................................
		self.nameLabel = Tk.Label(self.topFrame,
			text = "[NAME]", relief = Tk.SUNKEN, bd = 1,
			bg = self.background, font = ('TkFixedFont', 10, 'bold'),
			padx = 5, width = 20, fg = self.foreground)
		self.nameLabel.pack(side = Tk.LEFT, 
			anchor = 'w',fill = Tk.X, expand = False)

		# ......................................................................
		self.macLabel = Tk.Label(self.topFrame,
			text = "[MAC]",relief = Tk.SUNKEN, bd = 1,
			bg = self.background, font = ('TkFixedFont', 10, 'bold'),
			padx = 5, width = 18, height = 1, fg = self.foreground)
		self.macLabel.pack(side = Tk.LEFT, 
			anchor = 'w',fill = Tk.X, expand = False)


		# ......................................................................
		self.mosiIndexLabel = Tk.Label(self.topFrame, text = "MOSI:",
			bg = self.background, font = 'TkDefaultFont 8',
			fg = self.foreground)
		self.mosiIndexLabel.pack(side = Tk.LEFT)
		
		self.mosiIndexCounter = Tk.Label(self.topFrame, 
			text = "RIP", relief = Tk.SUNKEN, bd = 1,
			bg = "white", font = 'TkFixedFont 8',
			width = 10, fg = self.foreground)
		self.mosiIndexCounter.pack(side = Tk.LEFT, 
			anchor = 'w',fill = Tk.X, expand = False)

		# ......................................................................
		self.misoIndexLabel = Tk.Label(self.topFrame, text = "MISO:",
			bg = self.background, font = 'TkDefaultFont 8', 
			fg = self.foreground)
		self.misoIndexLabel.pack(side = Tk.LEFT)

		self.misoIndexCounter = Tk.Label(self.topFrame, 
			text = "RIP", relief = Tk.SUNKEN, bd = 1,
			bg = "white", font = 'TkFixedFont 8',
			width = 10,
			fg = self.foreground)
		self.misoIndexCounter.pack(side = Tk.LEFT, 
			anchor = 'w', fill = Tk.X, expand = False)
	
		# ......................................................................
		self.dataIndexLabel = Tk.Label(self.topFrame, text = "Data:",
			bg = self.background, font = 'TkDefaultFont 8',
			fg = self.foreground)
		self.dataIndexLabel.pack(side = Tk.LEFT)

		self.dataIndexCounter = Tk.Label(self.topFrame, 
			text = "RIP", relief = Tk.SUNKEN, bd = 1,
			bg = "white", font = 'TkFixedFont 8',
			width = 10, fg = self.foreground)
		self.dataIndexCounter.pack(side = Tk.LEFT, 
			anchor = 'w', fill = Tk.X, expand = False)
	
		# ......................................................................
		self.timeoutsLabel = Tk.Label(self.topFrame, text = "Timeouts:",
			bg = self.background, font = 'TkDefaultFont 8', 
			fg = self.foreground)
		self.timeoutsLabel.pack(side = Tk.LEFT)

		self.timeoutsCounter = Tk.Label(self.topFrame, 
			text = "RIP", relief = Tk.SUNKEN, bd = 1,
			bg = "white", font = 'TkFixedFont 8',
			width = 10, fg = self.foreground)
		self.timeoutsCounter.pack(side = Tk.LEFT, 
			anchor = 'w', fill = Tk.X, expand = False)
	
		# ......................................................................
		self.dropLabel = Tk.Label(self.topFrame, text = "Drops:",
			bg = self.background, font = 'TkDefaultFont 8', 
			fg = self.foreground)
		self.dropLabel.pack(side = Tk.LEFT)

		self.dropCounter = Tk.Label(self.topFrame, 
			text = "RIP", relief = Tk.SUNKEN, bd = 1,
			bg = "white", font = 'TkFixedFont 8',
			width = 10, fg = self.foreground)
		self.dropCounter.pack(side = Tk.LEFT, 
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
			width = 3, 
			fg = self.foreground)	

		self.slashLabel = Tk.Label(
			self.selectionCounterFrame,
			bg = self.background,
			text = '/',
			padx = 0,
			font = ('TkFixedFont', '9'),
			width = 1,
			fg = self.foreground)

		self.activeCounter = Tk.Label(
			self.selectionCounterFrame,
			justify = Tk.LEFT,
			text = '--',
			bg = self.background,
			font = ('TkFixedFont', '9'),
			width = 2,
			fg = self.foreground)

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
		
		self.disconnectButtonFrame = Tk.Frame(self.buttonFrame, bg = self.background,
			padx = 2)
		self.disconnectButtonFrame.pack(side = Tk.LEFT)

		self.disconnectButton = Tk.Button(
			self.disconnectButtonFrame,
			text = "Disconnect",
			command = self.disconnect,
			highlightbackground = self.background
		)
		self.disconnectButton.pack()
		self.disconnectButtonShown = True
		
		self.rebootButtonFrame = Tk.Frame(self.buttonFrame, bg = self.background,
			padx = 2)
		self.rebootButtonFrame.pack(side = Tk.LEFT)

		self.rebootButton = Tk.Button(
			self.rebootButtonFrame,
			text = "Reboot",
			command = self.reboot,
			highlightbackground = self.background
		)
		self.rebootButton.pack()
		self.rebootButtonShown = True

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
			font = ('TkFixedFont', '9'),
			fg = self.foreground
			)

		self.coordinatesLabel.pack()
		self.coordinatesFrame.pack(side = Tk.RIGHT)
		# FAN ARRAY - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
		self.fanArrayFrame = Tk.Frame(self.generalFrame, bg = self.background)
		self.fanArrayFrame.pack(fill = Tk.X)

		self.fans = []
		# SELECTED FLAG - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
			# Keep track of whether one or more fans in this Slave are selected
		self.selected = []
		self.selectionCount = 0

		# Run status-dependent routines:
		self.setStatus(self.status, True)
		
		# End __init__ =========================================================

	def setMaxFans(self, newMaxFans): # ========================================
		# ABOUT: Update MaxFans parameter. Useful after initialization with
		# null values.

		# DEBUG:
		# Destroy old values, if any exist:
		if len(self.fans) > 0:
			for fanDisplay in self.fans:
				fanDisplay.pack_forget()
				fanDisplay.destroy()
				del fanDisplay
			del self.selected
			self.selected = []
			
		# Create new values:
		self.maxFans = newMaxFans

		for i in range(self.maxFans):
			self.fans.append(fd.FanDisplay(self.fanArrayFrame, i))
		
		for i in range(self.maxFans):
			self.selected.append("0")


		# End setMaxFans =======================================================

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
		self.dropCounter.config(textvariable = self.target.dropIndex)

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

		if newStatus == sv.CONNECTED:
			self.selectAllButton.configure(state = Tk.NORMAL)
			self.deselectAllButton.configure(state = Tk.NORMAL)
			
			self.connectButton.configure(state = Tk.DISABLED)
			self.showConnectButton(False)

		elif newStatus == sv.DISCONNECTED:
			self.selectAllButton.configure(state = Tk.DISABLED)
			self.deselectAllButton.configure(state = Tk.DISABLED)

			self.connectButton.configure(state = Tk.DISABLED)
			self.showConnectButton()

		elif newStatus == sv.KNOWN:
			self.selectAllButton.configure(state = Tk.DISABLED)
			self.deselectAllButton.configure(state = Tk.DISABLED)
			self.connectButton.configure(state = Tk.DISABLED)
			self.showConnectButton()

		elif newStatus == sv.AVAILABLE:
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
		# ABOUT: Connect to AVAILABLE sv.

		if self.status == sv.AVAILABLE:
			self.connectMethod(self.target.index)

	def disconnect(self): # ====================================================
		# ABOUT: Disconnect from a CONNECTED sv.

		if self.status == CONNECTED:
			self.disconnectMethod(self.target.index)

	def reboot(self): # ========================================================
		# ABOUT: Disconnect from a CONNECTED sv.
		
		self.rebootMethod(self.target.index)

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
