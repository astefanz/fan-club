################################################################################
## Project: Fan Club Mark II "Master" ## File: GarbageCollector.py            ##
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
Auxiliary class to end the flow of data through the FCI modules/

"""
################################################################################

## DEPENDENCIES ################################################################


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

## CLASS DEFINITION ############################################################

class FCGarbageCollector:

	def __init__(self, misoMatrixMethod = None, updatePipeMethod = None, 
			printQueue): # =====================================================
		self.printQ = None

		try:
			self.printQ = self.printQueue
			self.printM("Initializing G.Collector")
			
			self.misoMatrixMethod = misoMatrixMethod
			self.updateMethod = updateMethod

			self.pipeLock = threading.Lock()
			self.ready = False

			if self.misoMatrixMethod is not None and \
				self.updateMethod is not None:
				self.ready = True

			self.garbageCollectorThread = threading.Thread(
				name = "FCMkII_GCThread",
				target = self._garbageCollectorRoutine)
			self.garbageCollectorThread.setDaemon(True)

			self.garbageCollectorThread.start()

		except Exception as e:
			if self.printQ is not None:
				self.printM("ERROR: Unhandled exception in GUI output"\
					" routine: \"{}\"".\
					format(traceback.format_exc()), "E")
			else:
				raise e

		# End __init__ =========================================================

	# THREAD ROUTINES ----------------------------------------------------------

	def _garbageCollectorRoutine(self): # ======================================
		# This routine serves as an endpoint for the stream of MISO matrices
		# and update messages.
		
		self.printM("G.Collector Routine started", "G")
	
		# SET UP LOOP ----------------------------------------------------------
		self.printM("[GC] Waiting for input methods")
		while True:
			self.pipeLock.acquire()
			if self.ready:
				break
			self.pipeLock.release()

		# MAIN LOOP ------------------------------------------------------------
		self.printM("[GC] Input methods received. Entering main loop", "G")
		locked = False
		while True:
			try:
				self.pipeLock.acquire()
				locked = True

				# Check update pipe:
				update = self.updateMethod()
				if update is not None:
					del update

				# Check MISO matrix pipe:
				misoMatrix = self.misoMatrixMethod()
				if misoMatrix is not None:
					del misoMatrix

				self.pipeLock.release()
				locked = False
		
			except Exception as e:
				self.printM("ERROR: Unhandled exception in GUI G.Collector"\
					" routine: \"{}\"".\
					format(traceback.format_exc()), "E")

			finally:
				if locked:
					self.pipeLock.release()

		# End _garbageCollectorRoutine =========================================

	# INTERFACE METHODS --------------------------------------------------------

	def setGetters(self, newUpdateMethod, newMISOMatrixMethod): # ==============

		try:
			# Acquire lock:
			self.pipeLock.acquire()
			
			self.updateMethod = newUpdateMethod
			self.misoMatrixMethod = newMISOMatrixMethod

			self.ready = True

		except Exception as e:
			self.printM("ERROR: Unhandled exception in GUI GC setMethods: "\
				"\"{}\"".\
				format(traceback.format_exc()), "E")

		finally:
			self.pipeLock.release()

		# End setPipes =========================================================

	# UTILITY METHODS ----------------------------------------------------------

	def printM(self, message, tag = 'S'): # ====================================
		
		self.printQ.put_nowait((message, tag))

		# End printM ===========================================================


