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
		savedSlaves, broadcastPeriodS, periodMS, periodS,
		broadcastPort, passcode, misoQueueSize, maxTimeouts, maxLength,
		# Fan array:
		maxFans, fanMode, targetRelation, fanFrequencyHZ, counterCounts, 
		pulsesPerRotation,
		maxRPM, minRPM, minDC, chaserTolerance, maxFanTimeouts, pinout,
		# Multiprocessing:
		matrixPipe,
		commandPipe,
		printQueue
	): # ===================================================================
	try:

		printQueue.put_nowait(("Starting Comms. Process", 'S'))

		# Create Communicator:
		comms = cm.FCCommunicator(
			# Network:
			savedSlaves, broadcastPeriodS, periodMS, periodS,
			broadcastPort, passcode, misoQueueSize, maxTimeouts, maxLength,
			# Fan array:
			maxFans, fanMode, targetRelation, fanFrequencyHZ, counterCounts, 
			pulsesPerRotation,
			maxRPM, minRPM, minDC, chaserTolerance, maxFanTimeouts, pinout,
			# Multiprocessing:
			matrixPipe,
			commandPipe,
			printQueue
			)

	threading.wait(None)

	except Exception as e: # Print uncaught exceptions
		printQ.put(("UNHANDLED TERMINATED COMMS. PROCESS: "\
			"\"{}\"".format(traceback.format_exc()), "E")
			)

	# End _communicatorProcessRoutine ======================================

class FCPRCommunicator:
	
	def __init__(self,
			# Network:
			savedSlaves, mainQueueSize, broadcastPeriodS, periodMS, periodS,
			broadcastPort, passcode, misoQueueSize, maxTimeouts, maxLength,
			# Fan array:
			maxFans, fanMode, targetRelation, fanFrequencyHZ, counterCounts, 
			pulsesPerRotation,
			maxRPM, minRPM, minDC, chaserTolerance, maxFanTimeouts, pinout
			# Multiprocessing:
			printQueue
		): # ===================================================================
		# ABOUT: Constructor for class FCPRCommunicator.
		try:

			# Create inter-process communication facilities:
				# NOTE: Here RE stands for "ReceiverEnd," SE stands for 
				# "SenderEnd" and the "I" in "IRE" and "ISE" stands for 
				# "Internal"
			
			# Output matrix and Input matrix:
			self.matrixExternal, self.matrixInternal = pr.Pipe(True)
			
			# Command input and new Slave and status change output:
			self.commandExternal, self.commandInternal = pr.Pipe(True)

			# Console feedback:
			self.printQ = printQueue
			
			self.communicatorProcess = pr.Process(
				target = _communicatorProcessRoutine,
				name = "FCMkII_Comms",
				args = (	
				# Network:
				savedSlaves, mainQueueSize, broadcastPeriodS, periodMS, periodS,
				broadcastPort, passcode, misoQueueSize, maxTimeouts, maxLength,
				# Fan array:
				defaultModuleDimensions, defaultModuleAssignment,
				maxFans, fanMode, targetRelation, fanFrequencyHZ, counterCounts, 
				pulsesPerRotation,
				maxRPM, minRPM, minDC, chaserTolerance, maxFanTimeouts, pinout,
				# Multiprocessing:
				self.matrixInternal,
				self.commandInternal,
				self.printQ
					)
				)
		
		except Exception as e: # Print uncaught exceptions
			self.printM("UNHANDLED EXCEPTION IN FCPRCommunicator __init__: "\
				"\"{}\"".\
				format(traceback.format_exc()), "E")

		# End __init__ =========================================================

	# "PRIVATE" METHODS # # # # # # # # # # # # # # # # # # # # # # # # # # # #  
	
	def printM(self, output, tag = 'S'): # =====================================
		
		try:
			self.printQ.put_nowait((output, tag))
			return True

		except Queue.Full:
			print "[WARNING] Communications output queue full. "\
				"Could not print the following message:\n\r \"{}\"".\
				format(output)
			return False

		# End printM ===========================================================

	# "PUBLIC" METHODS # # # # # # # # # # # # # # # # # # # # # # # # # # # # #	

	def matrixIn(self, matrix): # ==============================================
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

		self.matrixExternal.send(matrix)

		# End matrixIn =========================================================

	def matrixOut(self, matrix): # =============================================
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

		if self.matrixExternal.poll():
			return self.matrixExternal.recv()
		else:
			return None

		# End matrixOut ========================================================

	def commandIn(self, command): # ============================================
		# Send a command to the Communicator Process. The command is expected
		# to be a numpy array of integers of the form:
		#         					(COMMAND, VALUE)
		# Where COMMAND must be a valid FCPRC constant.
		
		if command in FCPRCONSTS:	
			self.commandExternal.send(command)
		else:
			raise ValueError("Given command must be a valid constant, not {}".\
				format(command))
	
		# End commandIn ========================================================

	def commandOut(self): # ====================================================
		# Get output from the Communicator Process, if any is available.
		# The following possible outputs are expected:
		#
		# - New Slave(s): 
		#					(NEW, (Slave...))
		#		Where the second item is a list of Slave MAC addresses in the 
		#		order in which they are indexed
		#
		# - If there is no output to fetch, None is returned.

		if self.commandExternal.poll():
			return self.commandExternal.recv()
		else:
			return None

		# End commandOut =======================================================

	def printOut(self): # ======================================================
		# Get console output from the Communicator Process, if any.
		# Returns console output in the form (message, tag) or None if there is
		# nothing to return

		try:
			return self.printQ.get_nowait()		
		except Queue.Full:
			return None

		# End getPrintM ========================================================

