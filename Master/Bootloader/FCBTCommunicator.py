################################################################################
## Project: Fan Club Mark II "Master" # File: FCBTCommunicator.py             ##
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
Custom Tkinter widget for bootloader-relevant communications.

"""
################################################################################

## DEPENDENCIES ################################################################
from mttkinter import mtTkinter as Tk
import tkinter.filedialog
import tkinter.messagebox

## CONSTANT DEFINITIONS ########################################################i

EMPTY = 0

## CLASS DEFINITION ############################################################

class FCBTCommunicator(Tk.Frame): # ============================================

	def init(self, master, background = "#e2e2e2"): # ==========================
		Tk.Frame.__init__(self, master)

		# Create list:
		self.slaveList = ttk.Treeview(self, 
			selectmode="extended", height = 5)
		self.slaveList["columns"] = \
			("Index","MAC", "IP", "Version", "Last Reply")

		# Create columns:
		self.slaveList.column('#0', width = 20, stretch = False)
		self.slaveList.column("Index", width = 20, anchor = "center")
		self.slaveList.column("MAC", width = 50, anchor = "center")
		self.slaveList.column("IP", width = 50, anchor = "center")
		self.slaveList.column("Version", width = 50, 
			anchor = "center")
		self.slaveList.column("Last Reply", width = 50, 
			anchor = "center")

		# Configure column headings:
		self.slaveList.heading("Index", text = "Index")
		self.slaveList.heading("MAC", text = "MAC")
		self.slaveList.heading("IP", text = "IP")
		self.slaveList.heading("Version", text = "Version")
		self.slaveList.heading("Last Reply", text = "Last Reply")

		# Configure tags:
		self.slaveList.tag_configure(
			"M", 
			background= '#d1ffcc', 
			foreground = '#0e4707', 
			font = 'TkFixedFont 12 ') # Match
		
		self.slaveList.tag_configure(
			"B", 
			background= '#ccdeff', 
			foreground ='#1b2d4f', 
			font = 'TkFixedFont 12 ') # Bootloader

		self.slaveList.tag_configure(
			"N",
			background= '#fffaba',
			foreground ='#44370b',
			font = 'TkFixedFont 12 bold') # No match

		self.slaveList.tag_configure(
			"A", 
			background= '#ededed', 
			foreground ='#666666',
			font = 'TkFixedFont 12 ') # Unknown

		# Save previous selection:
		self.oldSelection = None

		# Bind command:
		#self.slaveList.bind('<Double-1>', self._slaveListMethod)

		self.slaveList.pack(fill = Tk.BOTH, expand = True, anchor = 's')
		"""

		Tk.Frame.__init__(self, master)

		self.background = background
		
		self.mainFrame = Tk.Frame(self, background = "red")

		# Note label:
		self.noticeLabel = Tk.Label(self, bg = self.background,
			text = "NOTE: Network interface undefined")

		self.noticeLabel.pack(side = Tk.TOP, fill = Tk.X)

		# Standard Broadcast button:
		self.standardBroadcastMessage = ""
		self.standardBroadcastFrame = Tk.Frame(self.mainFrame,
			bg = self.background)

		self.standardBroadcastButton = Tk.Button(
			self.mainFrame, text = "Standard Broadcast"
		)
		self.standardBroadcastButton.pack(side = Tk.LEFT)

		self.standardBroadcastFrame.pack(
			side = Tk.TOP, fill = Tk.X, expand = True)

		# Launch Broadcast button:
		self.launchBroadcastMessage = ""
	
		# Reset Broadcast button:
		self.resetBroadcastMessage = ""

		# Update Broadcast button:

		# Wait Broadcast button:

		# Custom Broadcast button:

		self.mainFrame.pack(side = Tk.TOP, fill = Tk.BOT, expand = True)
		"""
