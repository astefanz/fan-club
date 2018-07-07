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
import tkFileDialog 
import tkMessageBox
import tkFont
import ttk # "Notebooks"

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
import MainGrid as mg
import FCCommunicator as cm
import FCSlave as sv
import FCArchiver as ac

from auxiliary.debug import d

## CONSTANTS ###################################################################

## AUXILIARY ROUTINE ###########################################################

def _gridProcessRoutine(
	profile,
	updateIn,
	misoIn,
	commandQueue,
	mosiQueue,
	shutdownPipe,
	printQueue
): # ===========================================================================
	try:
		
		# SETUP ----------------------------------------------------------------
		# TODO: startup sequence
		printQueue.put(("[UI][GD] Activating Grid",'S'))
		
		# Build window:
		window = Tk.Toplevel()
		window.title("FCMkII Grid")

		# TODO: window.protocol("WM_DELETE_WINDOW")	
		d()
		# Build widget:
		gridOuterFrame = Tk.Frame(
			window, padx = 3, pady = 3, 
			relief = Tk.RIDGE, borderwidth = 2, cursor = "hand1")

		d()
		gridOuterFrame.pack(fill = Tk.BOTH, expand = True)
		"""
		d()
		grid = mg.MainGrid(
			gridOuterFrame,
			profile[ac.dimensions][0],
			profile[ac.dimensions][1],
			600/profile[ac.dimensions][0],
			[],
			profile[ac.maxRPM]
			)
				
		
		d()
		def _expand(event):
			grid.destroy()
			del grid
			grid = mg.MainGrid(
				gridOuterFrame,
				profile[ac.dimensions][0],
				profile[ac.dimensions][1],
				0.9*(min(gridOuterFrame.winfo_height(),
					gridOuterFrame.winfo_width(),))/\
						(min(profile[ac.dimensions][0],
						profile[ac.dimensions][1])),
				[],
				profile[ac.maxRPM]
				)
		
		d()
		gridOuterFrame.bind("<Button-1>", _expand)
		"""
		gridOuterFrame.focus_set()
		printQueue.put_nowait(("[UI][GD][GP] Grid ready", "G"))

		d()
		# MAIN LOOP ------------------------------------------------------------
		while True:
			try:
				
				d()
				# Check shutdown flag:
				if shutdownPipe.poll():
					shutdownCode = shutdownPipe.recv()
					if shutdownCode is 1:
						# TODO: Shutdown sequence
						# destroy grid:
						grid.destroy()

						# destroy popup window:
						window.destroy()
						break
					else:
						raise RuntimeError("Invalid shutdown code \"{}\"".\
							format(shutdownCode))
		
				# Update input values:
				# TODO
				updateIn()
				misoIn()
				

				d()
			except Exception as e: # Print uncaught exceptions
				printQueue.put(("[UI][GD][GP] EXCEPTION: "\
					"\"{}\"".format(traceback.format_exc()), "E")
					)

		printQueue.put_nowait(("[UI][GD][GP] Grid process ended"))

	except Exception as e: # Print uncaught exceptions
		printQueue.put(("[UI][GD][GP] EXCEPTION (GP terminated): "\
			"\"{}\"".format(traceback.format_exc()), "E")
			)

	# End _communicatorProcessRoutine ==========================================

class FCPRGrid:
	
	def __init__(self,
			profile,
			commandQueue,
			mosiQueue,
			printQueue,
			updateIn = lambda: None,
			misoIn = lambda: None,
		): # ===================================================================
		# ABOUT: Constructor for class FCPRGrid.
		
		self.printQueue = None

		try:
			
			self.printQueue = printQueue
			self._printM("[UI][GD][init] Initializing Grid handler")

			self.profile = profile
			
			# Set up standard data pipeline and inter-process communication:
			
			# Arguments:
			self.__updateIn = updateIn
			self.__misoIn = misoIn
			self.commandQueue = commandQueue
			self.mosiQueue = mosiQueue
			self.printQueue = printQueue

			# Internals:
			self.inputLock = threading.Lock()

			self.updatePipeOut, self.updatePipeIn = pr.Pipe(False)
			self.misoPipeOut, self.misoPipeIn = pr.Pipe(False)

			self.activeFlag = False
			self.activeLock = threading.Lock()

			self.shutdownPipeOut, self.shutdownPipeIn = pr.Pipe(False)

			self.process = None 
			self.temp_external_close = lambda: None

			# Placeholders for graphical interface:
			self.window = None

		except Exception as e: # Print uncaught exceptions
			self._printM("[UI][GD][init] EXCEPTION: "\
				"\"{}\"".\
				format(traceback.format_exc()), "E")

		# End __init__ =========================================================

	def _commandOut(self, command): # ==========================================
		self.commandQueue.put_nowait(command)
		# End _commandOut ======================================================

	def _updateIn(self): # =====================================================
		try:
			self.inputLock.acquire()
			update = self.__updateIn()
			
			if update is not None:
				self.updatePipeIn.send(update)

			return update

		finally:
			self.inputLock.release()

		# End _updateIn ========================================================

	def updateOut(self): # =====================================================
		
		if self.updatePipeOut.poll():
			return self.updatePipeOut.recv()
		else:
			return None

		# End updateOut ========================================================

	def _misoIn(self): # =======================================================
		try:
			self.inputLock.acquire()
			miso = self.__misoIn()

			if miso is not None:
				self.misoPipeIn.send(miso)

			return miso

		finally:
			self.inputLock.release()

		# End _misoIn ==========================================================


	def misoOut(self): # =======================================================
		if self.misoPipeOut.poll():
			return self.misoPipeOut.recv()
		else:
			return None

		# End misoOut ==========================================================

	def setIn(self, newUpdateIn, newMISOIn): # =================================
		try:
			self.inputLock.acquire()
			
			self.__updateIn = newUpdateIn
			self.__misoIn = newMISOIn

		finally:
			self.inputLock.release()

		# End setIn ============================================================

	def start(self, readyCallback = lambda: None): # ===========================
		# Start up grid 
		if not self.isActive():
			self.process = pr.Process(
				name = "FCMkII_Grid",
				target = _gridProcessRoutine,
				args = (
					self.profile,
					self._updateIn,
					self._misoIn,
					self.commandQueue,
					self.mosiQueue,
					self.shutdownPipeOut,
					self.printQueue
				)
			)
			self.process.start()
			self._setActive(True)
			readyCallback()
		else:
			raise RuntimeError("Tried to start already active FCGrid")

		# End start ============================================================

	def stop(self, readyCallback = lambda: None): # ============================
		# Stop grid
		if self.isActive():
			# TODO: Stop sequence

			self._printM("[UI][GD] Deactivating Grid")

			# End process:
			self.shutdown(False)
			self.process = None
			

			self.temp_external_close()
			self._setActive(False)

		else:
			raise RuntimeError("Tried to stop already inactive FCGrid")

		# End stop =============================================================
	 
	def shutdown(self, checkActive = True): # ==================================
		
		self._printM("[UI][GD][sd] Shutting down Grid process", "W")
		
		# Stop grid if it is active:
		if checkActive and self.isActive():
			self.stop()

		# Cleanly terminate process:
		if self.process is not None:
			self._printM("[UI][GD][sd] Joining Grid Process")
			self.shutdownPipeIn.send(1)
			self.process.join()
		
		self._printM("[UI][GD][sd] Grid shutdown complete")
		# End shutdown =========================================================
	
	def isActive(self): # =====================================================
		try:
			self.activeLock.acquire()
			value = self.activeFlag
			return value
		finally:
			self.activeLock.release()

		# End isActive ========================================================

	def _setActive(self, newValue): # ==========================================

		try:
			self.activeLock.acquire()
			self.activeFlag = newValue

		finally:
			self.activeLock.release()

		# End _setActive =======================================================

	def _printM(self, message, tag = 'S'): # ===================================
		self.printQueue.put_nowait((message, tag))
		# End _printM ==========================================================


