################################################################################
## Project: Fan Club Mark II "Master" # File: SlaveList.py                    ##
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
Custom Tkinter widget to display Slave statuses.

"""
################################################################################


## DEPENDENCIES ################################################################

# GUI:
from mttkinter import mtTkinter as Tk
import tkFileDialog 
import tkMessageBox
import tkFont
import ttk # "Notebooks"

# System:
import os # Get current working directory & check file names
import sys # Exception handling
import inspect # get line number for debugging
import traceback

# FCMkII:
import FCSlave as sv

## CONSTANTS ###################################################################

## CLASS DEFINITION ############################################################

class SlaveList(Tk.Frame): # ===================================================

	# NOTE: Slaves are stored as: 
	# [Index + 1, MAC, status, fans, version, iid]
	#          0    1       2     3    4      5

	def __init__(self, master): # ==============================================
		try:
			# Parameters displayed:
			# - Index 
			# - MAC
			# - Status
			# - Fans
			# - Version

			# CONFIGURE --------------------------------------------------------
			Tk.Frame.__init__(self, master)
			self.background = "#d3d3d3"
			self.foreground = "black"
			self.config(
				bg = self.background, relief = Tk.SUNKEN, borderwidth = 2)
		
			# BUILD ------------------------------------------------------------
			# Create list:
			self.slaveList = ttk.Treeview(self, 
				selectmode="none")
			self.slaveList["columns"] = \
				("Index","MAC","Status","Fans", "Version")

			# Create columns:
			self.slaveList.column('#0', width = 20, stretch = False)
			self.slaveList.column("Index", width = 20, anchor = "center")
			self.slaveList.column("MAC", width = 50, anchor = "center")
			self.slaveList.column("Status", width = 30, anchor = "center")
			self.slaveList.column("Fans", width = 50, stretch = False, 
				anchor = "center")
			self.slaveList.column("Version", width = 50, 
				anchor = "center")

			# Configure column headings:
			self.slaveList.heading("Index", text = "Index")
			self.slaveList.heading("MAC", text = "MAC")
			self.slaveList.heading("Status", text = "Status")
			self.slaveList.heading("Fans", text = "Fans")
			self.slaveList.heading("Version", text = "Version")

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
			#self.slaveList.bind('<Double-1>', self._onDoubleClick)

			self.slaveList.pack(fill = Tk.BOTH, expand = True, anchor = 's')

			# DATA -------------------------------------------------------------
			self.slaves = []
			self.numSlaves = 0
		
		except Exception as e: # Print uncaught exceptions
			tkMessageBox.showerror(title = "FCMkII Fatal Error",
				message = "Warning: Uncaught exception in "\
				"SList constructor: \"{}\"".\
				format(traceback.format_exc()))
		
		# End __init__ =========================================================

	def add(self, newSlave): # =================================================
		# Expected format:
		# (MAC, Status, Fans, Version)
	
		self.slaves.append(
			[self.numSlaves + 1,      	# Index (W/ start at 1)
			newSlave[0],  				# MAC
			sv.translate(newSlave[1]),	# Status
			newSlave[2], 				# Fans
			newSlave[3]])				# Version

		# Add to list and append IID:
		self.slaves[self.numSlaves].append(self.slaveList.insert(
			'', 'end', 
			values = self.slaves[self.numSlaves],# Version
			tag = sv.translate(newSlave[1], True)))
		# Increase count:
		self.numSlaves += 1	

		# End add ==============================================================

	def setStatus(self, index, newStatus): # ===================================

		self.slaves[index][2] = sv.translate(newStatus)
		self.slaveList.item(self.slaves[index][-1], # <- IID 
			values = self.slaves[index],
			tag = sv.translate(newStatus, True))

		# Move atop due to activity
		self.slaveList.move(self.slaves[index][-1], '', 0)
			
		# End setStatus ========================================================

	#def remove(self, iid): # ===================================================

	#def getSelection(self): # ==================================================

	def setSelection(self, selected): # ========================================
		pass
