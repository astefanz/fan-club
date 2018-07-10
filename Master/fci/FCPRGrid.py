################################################################################
## Project: Fan Club Mark II "Master" ## File: FCPRGrid.py                    ##
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
This module is a multiprocessing wrapper around the FC Grid widget.

"""
################################################################################

## DEPENDENCIES ################################################################

# GUI:
from mttkinter import mtTkinter as Tk

# System:
import sys			# Exception handling
import traceback	# More exception handling
import random		# Random names, boy
import resource		# Socket limit
import threading	# Multitasking
import thread		# thread.error
import multiprocessing as pr # The big guns

# Data:
import time			# Timing
import Queue
import numpy as np	# Fast arrays and matrices

# FCMkII:
import fci.MainGrid as mg
import FCCommunicator as cm
import FCSlave as sv
import FCArchiver as ac

import auxiliary.spawner as sp
from auxiliary.debug import d

## CONSTANTS ###################################################################

# Commands:
STOP = -1
# Button text:
START_TEXT = "Activate Grid"
STOP_TEXT = "Deactivate Grid"
STARTING_TEXT = "Activating Grid"
STOPPING_TEXT = "Deactivating Grid"

## PROCESS ROUTINE #############################################################

def testRoutine():
	import Tkinter as Tk
	print " test routine"
	tl = Tk.Toplevel()
	print " activating mainloop"
	tl.mainloop()

def _FCPRGridProcessRoutine(
	profile,
	commandPipeOut,
	updatePipeOut,
	misoPipeOut,
	mosiQueue,
	commandQueue,
	printQueue): # =============================================================

	#try:	

	print "FCPR Process started"
	itl = Tk.Toplevel()
	print "Starting mainloop"
	itl.mainloop()
	print " FCPR Process done"

	# End _FCPRGridProcessRoutine ==============================================
		

## CLASS DEFINITION ############################################################

class FCPRGrid(Tk.Frame): 

	def __init__(self, master, profile, commandQueue, mosiQueue,  printQueue):
		
		canPrint = False

		try:

			# DATA -------------------------------------------------------------
			
			# Store arguments:
			self.printQueue = printQueue
			canPrint = True

			self.master = master

			self.profile = profile
			self.mosiQueue = mosiQueue
			self.commandQueue = commandQueue

			self.printM("Initializing Grid widget")
			
			# Create data members:
			self.commandPipeOut, self.commandPipeIn = pr.Pipe(False)
			self.updatePipeOut, self.updatePipeIn = pr.Pipe(False)
			self.misoPipeOut, self.misoPipeIn = pr.Pipe(False)
			
			self.stopFlag = False	
			self.activeFlag = False
			self.watchdogThread = False

			# INTERFACE WIDGET -------------------------------------------------
			Tk.Frame.__init__(self, master)
		
			self.bg = "#e2e2e2"
			self.fg = "black"

			# Build button: 
			self.button = Tk.Button(
				self,
				text = START_TEXT, 
				width = 10,
				bg = self.bg,
				highlightbackground = self.bg,
				fg = self.fg,
				command = self.start
			)

			self.button.pack()

			self.printM("Grid widget initialized", "G")

		except Exception as e: # Print uncaught exceptions
			if not canPrint:
				tkMessageBox.showerror(title = "FCMkII Constructor Error",
					message = "Warning: Uncaught exception in "\
					"FCPRGrid constructor: \"{}\"".\
					format(traceback.format_exc()))
			else:
				self.printM("Warning: Uncaught exception in "\
					"FCPRGrid constructor: \"{}\"".\
					format(traceback.format_exc()), "E")

		# End __init__ =========================================================

	def inputCommand(self, command): # =========================================
		
		if self.isActive():
			self.commandPipeIn.send(command)

		else:
			self.printM(
				"WARNING: Tried to send command \"{}\" to inactive Grid".\
				format(command)
			)

		# End inputCommand =====================================================

	def inputUpdate(self, update): # ===========================================
		
		if self.isActive():
			self.updatePipeIn.send(update)

		else:
			self.printM(
				"WARNING: Tried to send update \"{}\" to inactive Grid".\
				format(command)
			)

		# End inputUpdate ======================================================

	def inputMISO(self, miso): # ===============================================
		
		if self.isActive():
			self.misoPipeIn.send(miso)

		else:
			self.printM(
				"WARNING: Tried to send MISO matrix to inactive Grid")


		# End inputMISO ========================================================

	def isActive(self): # ======================================================
	
		return self.activeFlag
		
		# End isActive =========================================================

	def updateProfile(self, newProfile): # =====================================
		
		self.profile = newProfile
		
		# End updateProfile ====================================================

	def start(self): # =========================================================

		# Check activity:
		if not self.isActive():
			
			# Start watchdog routine:
			self.watchdogThread = threading.Thread(
				name = "FCMkII_Grid_watchdog",
				target = self._watchdogRoutine
			)

			self.watchdogThread.setDaemon(True)
			self.watchdogThread.start()

		
		else:
			self.printM("WARNING: Tried to start active Grid", 'E')

		# End start ============================================================

	def stop(self): # ==========================================================
		
		# Check state:
		if self.isActive():
			
			# Change button state:
			self.button.config(
			text = STOPPING_TEXT,
				state = Tk.DISABLED
			)
			# Set stop flag:
			self.stopFlag = True


		else:
			self.printM("WARNING: Tried to stop inactive Grid", 'E')
		

		# NOTE: Handle case of widget window closure

		# End stop =============================================================

	def printM(self, message, tag = 'S'): # ====================================
	
		self.printQueue.put_nowait(("[GD] " + message, tag))
		# End printM ===========================================================

	def _watchdogRoutine(self): # ==============================================
		try:
			
			self.printM("[WD] Starting Grid")

			if self.isActive():
				self.printM("[WD] WARNING: watchdog thread started with an "\
					"already active process", 'E')
				return

			# Lock button:
			self.button.config(
				state = Tk.DISABLED,
				text = STARTING_TEXT
			)

			self.printM("[WD] Spawning process")
			sp.spawn(givenTarget = testRoutine)
			"""
				givenArgs = (
					self.profile,
					self.commandPipeOut,
					self.updatePipeOut,
					self.misoPipeOut,
					self.commandQueue,
					self.mosiQueue,
					self.printQueue
				)
			)
			"""


			# Update state:
			self.stopFlag = False
			self.activeFlag = True

			self.button.config(
				text = STOP_TEXT,
				state = Tk.NORMAL,
				command = self.stop
			)
			

			self.printM("[WD] Process spawned")
			while True:
				
				if self.stopFlag:
					self.printM("[WD] Grid stop flag detected")
					
					self.commandPipeIn.send((STOP))

					break
		
			# Check for anomalous termination:
			if not self.stopFlag:
				self.printM(
					"[WD] WARNING: Grid process terminated w/o stop flag", 'E')

			# Restore state:
			self.stopFlag  = False

			self.button.config(
				text = START_TEXT,
				command = self.start,
				state = Tk.NORMAL

			)
	
		except Exception as e:
			self.printM("ERROR: Unhandled exception in Grid watchdog routine: "\
				"\"{}\"".\
				format(traceback.format_exc()), "E")

		# End _activityWatchdog ================================================



