################################################################################
## Project: Fan Club Mark II "Master" ## File: FCPRCommunicator.py            ##
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
This module is a multiprocessing wrapper around FCCommunicator.

"""
################################################################################

## DEPENDENCIES ################################################################

# FCMkII:
import FCCommunicator as cm
import FCSlave as sv

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
import FCInterface
import FCSlave as sv

## CONSTANTS ###################################################################

## AUXILIARY ROUTINE ###########################################################

def _communicatorProcessRoutine(
		# Network:
		savedMACs, broadcastPeriodS, periodMS, periodS,
		broadcastPort, passcode, misoQueueSize, maxTimeouts, maxLength,
		# Fan array:
		maxFans, fanMode, targetRelation, fanFrequencyHZ, counterCounts, 
		pulsesPerRotation,
		maxRPM, minRPM, minDC, chaserTolerance, maxFanTimeouts, pinout,
		# Multiprocessing:
		updateIn,
		misoIn,
		printQueue,
		commandQueue,
		mosiMatrixQueue,
		updatePipeIn,
		misoMatrixPipeIn,
		shutdownPipeOut
	): # ===================================================================
	try:

		printQueue.put_nowait(("Starting Comms. Process", 'S'))

		# Create Communicator:
		comms = cm.FCCommunicator(
			# Network:
			savedMACs, broadcastPeriodS, periodMS, periodS,
			broadcastPort, passcode, misoQueueSize, maxTimeouts, maxLength,
			# Fan array:
			maxFans, fanMode, targetRelation, fanFrequencyHZ, counterCounts, 
			pulsesPerRotation,
			maxRPM, minRPM, minDC, chaserTolerance, maxFanTimeouts, pinout,
			# Multiprocessing:
			commandQueue,
			updatePipeIn,
			mosiMatrixQueue,
			misoMatrixPipeIn,
			printQueue
			)

		while True:
			
			# Check shutdown flag ----------------------------------------------
			if shutdownPipeOut.poll():
				message = shutdownPipeOut.recv()
				if message == 1:
					printQueue.put_nowait(("Shutting down comms.","W"))
					comms.shutdown()
					break

				else:
					printQueue.put_nowait(
						("WARNING: Unrecognized message in comms. "\
						"shutdown pipe (ignored): \"{}\"".\
						format(message),"E"))
					continue
					
			# Check STD input stream -------------------------------------------
			update = updateIn()
			del update

			miso = misoIn()
			del miso

	except Exception as e: # Print uncaught exceptions
		printQueue.put(("UNHANDLED EXCEPTION terminated Comms. Process: "\
			"\"{}\"".format(traceback.format_exc()), "E")
			)

	# End _communicatorProcessRoutine ==========================================

class FCPRCommunicator:
	
	def __init__(self,
			# Network:
			savedMACs,broadcastPeriodS, periodMS, periodS,
			broadcastPort, passcode, misoQueueSize, maxTimeouts, maxLength,
			# Fan array:
			maxFans, fanMode, targetRelation, fanFrequencyHZ, counterCounts, 
			pulsesPerRotation,
			maxRPM, minRPM, minDC, chaserTolerance, maxFanTimeouts, pinout,
			# Multiprocessing:
			printQueue
		): # ===================================================================
		# ABOUT: Constructor for class FCPRCommunicator.
		try:
			
			printQueue.put(("Initializing Comms. worker process","S"))

			# Create inter-process communication facilities:

			# Communicator commands:
			#	NOTE: Input... Use queue
			self.commandQueue = pr.Queue()

			# MOSI matrix:
			#	NOTE: Input... Use queue
			self.mosiMatrixQueue = pr.Queue()

			# Updates:
			#	NOTE: Output... use pipe
			self.updatePipeOut, self.updatePipeIn = pr.Pipe(False)

			# MISO matrix:
			#	NOTE: Output... use pipe
			self.misoMatrixPipeOut, self.misoMatrixPipeIn = pr.Pipe(False)

			# Input functions:
			self._updateIn = lambda: None
			self._misoIn = lambda: None
			self.inputLock = threading.Lock()

			# FCI terminal output:
			self.printQueue = printQueue
			
			# Pipe for shutdown message:
			self.shutdownPipeOut, self.shutdownPipeIn = pr.Pipe(False)

			self.communicatorProcess = pr.Process(
				name = "FCMkII_Comms",
				target = _communicatorProcessRoutine,
				args = (	
				# Network:
				savedMACs, broadcastPeriodS, periodMS, periodS,
				broadcastPort, passcode, misoQueueSize, maxTimeouts, maxLength,
				# Fan array:
				maxFans, fanMode, targetRelation, fanFrequencyHZ, counterCounts, 
				pulsesPerRotation,
				maxRPM, minRPM, minDC, chaserTolerance, maxFanTimeouts, pinout,
				# Multiprocessing:
				self.updateIn,
				self.misoIn,
				self.printQueue,
				self.commandQueue,
				self.mosiMatrixQueue,
				self.updatePipeIn,
				self.misoMatrixPipeIn,
				self.shutdownPipeOut
					)
				)
		
			self.communicatorProcess.start()
			printQueue.put(("Comms. worker process initialized", "G"))
		except Exception as e: # Print uncaught exceptions
			self.printM("UNHANDLED EXCEPTION IN FCPRCommunicator __init__: "\
				"\"{}\"".\
				format(traceback.format_exc()), "E")

		# End __init__ =========================================================

	def commandIn(self, command): # ============================================
		# Send a command to the Communicator Process. The command is expected
		# to be an iterable of integers of the form:
		#         					(COMMAND, VALUE)
		# Where COMMAND must be a valid FCPRC constant.
		
		if command in FCPRCONSTS:	
			self.commandQueue.put_nowait(command)
		else:
			raise ValueError("Given command must be a valid constant, not {}".\
				format(command))	
		# End commandIn ========================================================

	def setIn(self, newUpdateIn, newMISOIn): # =================================
		# Set input methods
		try:
			self.inputLock.acquire()
			self._updateIn = newUpdateIn
			self._misoIn = newMISOIn
		finally:
			self.inputLock.release()
		# End setIn ============================================================

	def updateIn(self): # ======================================================
		# Fetch update from Communicator, return it, and place it in own 
		# update pipe.

		try:
			self.inputLock.acquire()
			update = self._updateIn()
			return update

		finally:
			self.inputLock.release()

		# End updateIn =========================================================


	def updateOut(self): # =====================================================
		# Get output from the Communicator Process, if any is available.
		# The following possible outputs are expected:
		#
		# - New Slave(s): 
		#					(NEW, (Slave...))
		#		Where the second item is a list of Slave MAC address - version
		#       pairs in the order in which they have been indexed
		#
		# - If there is no output to fetch, None is returned.

		if self.updatePipeOut.poll():
			return self.updatePipeOut.recv()
		else:
			return None

		# End updateOut =======================================================

	def mosiIn(self, matrix): # ===============================================
		# Input a control matrix into the Communicator Process. The matrix is
		# expected to have the following form, as a numpy matrix:
		#
		#	      	|COMMAND| FAN1| FAN2| FAN3 |.... |FANN|
		# MODULE 1  |       |     |
		# ----------+-------+-----+-----
        # MODULE 2  |
		#   ...     .
		# MODULE N  | 
		#
		# Where COMMAND is an integer code simbolizing a command to be sent.

		self.mosiMatrixQueue.put_nowait(matrix)
		# End matrixIn =========================================================
	
	def misoIn(self): # ========================================================
		# Fetch MISO matrix from Communicator, return it, and place it in own
		# MISO matrix pipe.

		try:
			self.inputLock.acquire()
			misoM = self._misoIn()
			return misoM

		finally:
			self.inputLock.release()

		# End misoIn ===========================================================
	def misoOut(self): # =======================================================
		# Try to fetch an output matrix from the Communicator Process. The 
		# matrix is expected to have the following form, as a numpy matrix:
		#
		#	      	|CHANGE |STATUS |RPM1 |RPM2 |... | DC 1 |.... |DC 2|
		# MODULE 1  |       |       |
		# ----------+-------+-------+-----
        # MODULE 2  |
		#   ...     .
		# MODULE N  | 
		#
		# If there is no matrix to fetch, None is returned.		

		if self.misoMatrixPipeOut.poll():
			return self.misoMatrixPipeOut.recv()
		else:
			return None
		# End misoOut ==========================================================
	
	def setInput(self, newUpdateIn, newMISOIn): # ==============================
		# Set input methods for FCMkII data pipeline
		# NOTE: In this case, this method only exists for consistency with the
		# pipeline's standards, since the FCPRCommunicator automatically
		# deletes update and MISO input.

		pass

		# End setInput =========================================================

	def printM(self, output, tag = 'S'): # =====================================
		
		try:
			self.printQueue.put_nowait((output, tag))
			return True

		except Queue.Full:
			print "[WARNING] Communications output queue full. "\
				"Could not print the following message:\n\r \"{}\"".\
				format(output)
			return False

		# End printM ===========================================================

	def shutdown(self): # ======================================================
		# "Shutdown" Communicator by closing all sockets and terminating 
		# the Communicator process, performing any necessary cleanup.

		self.shutdownPipeIn.send(1)
		self.communicatorProcess.join()

		# End shutdown =========================================================

	def getStatus(self): # =====================================================
		# Get Communicator status as an integer code defined in 
		# FCCommunicator.py.
		# Possible status codes:
		# - CONNECTING
		# - CONNECTED
		# - DISCONNECTED

		# TODO: IMPLEMENT
		pass

		# End setStatus ========================================================

	def restart(self, args = None): # ==========================================
		
		# TODO: IMPLEMENT
		pass

		# End restart ==========================================================
