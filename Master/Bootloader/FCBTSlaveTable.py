################################################################################
## Project: Fan Club Mark II "Master" # File: FCBTSlaveTable                  ##
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
Custom Tkinter widget to represent a table of bootloader-relevant Slave data.

"""
################################################################################


## DEPENDENCIES ################################################################
from mttkinter import mtTkinter as Tk
import tkinter.filedialog
import tkinter.messagebox
import tkinter.ttk

import threading
import traceback

## CLASS DEFINITION ############################################################

class FCBTSlaveTable(Tk.Frame):
	
	def __init__(self, master): # ==============================================
		Tk.Frame.__init__(self, master)

		# Create list:
		self.slaveList = tkinter.ttk.Treeview(self, 
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

		# End __init__ =========================================================
