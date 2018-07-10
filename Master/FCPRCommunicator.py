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
import FCCommunicator as cm
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
				self.printQueue,
				self.commandQueue,
				self.mosiMatrixQueue,
				self.updatePipeIn,
				self.misoMatrixPipeIn,
				self.shutdownPipeOut
					)
				)
	
			self.communicatorProcess.daemon = True

			self.communicatorProcess.start()
			printQueue.put(("Comms. worker process initialized", "G"))
		except Exception as e: # Print uncaught exceptions
			self.printM("UNHANDLED EXCEPTION IN FCPRCommunicator __init__: "\
				"\"{}\"".\
				format(traceback.format_exc()), "E")

		# End __init__ =========================================================

	def getOutputPipes(self): # ================================================
		# Get receiving end of Communicator's output pipes as a tuple of the
		# form
		#				(UPDATE_PIPE_OUT, MISO_PIPE_OUT)
		# Where both items are Connection objects from the corresponding pipes.

		return (self.updatePipeOut, self.misoMatrixPipeOut)

		# End getOutputPipes ===================================================

	def getInputQueues(self): # ================================================
		# Get a reference to Communicator's input Queues as a tuple of the form
		#				(COMMAND_QUEUE, MOSI_QUEUE)
		
		return (self.commandQueue, self.mosiMatrixQueue)

		# End getInputQueues ===================================================

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
