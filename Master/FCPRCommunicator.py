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
import FCCommunicator as cm
import FCWidget as wg
import FCSlave as sv
import auxiliary.errorPopup as ep

## CONSTANTS ###################################################################

COMMAND_QUEUE = 0
MOSI_QUEUE = 1
UPDATE_PIPE = 2
MISO_MATRIX_PIPE = 3

## AUXILIARY ROUTINE ###########################################################

def _processRoutine(
		stopPipeOut,
		profile,
		commandQueue,
		mosiMatrixQueue,
		updatePipeIn,
		misoMatrixPipeIn,
		printQueue,
	): # ===================================================================
	try:

		printQueue.put_nowait(("Starting Comms. Process", 'S'))

		# Create Communicator:
		comms = cm.FCCommunicator(
			profile,
			commandQueue,
			mosiMatrixQueue,
			updatePipeIn,
			misoMatrixPipeIn,
			printQueue
			)

		while True:
			
			# Check shutdown flag ----------------------------------------------
			if stopPipeOut.poll():
				message = stopPipeOut.recv()
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

	# End _communicatorRoutine =================================================

class FCPRCommunicator(wg.FCWidget):
	
	def __init__(self,
			master,
			profile,
			spawnQueue,
			printQueue
		): # ===================================================================
		# ABOUT: Constructor for class FCPRCommunicator.
		try:
			self.printQueue = printQueue
			self.canPrint = True
			self.symbol = "YT"
			printQueue.put(("Initializing Comms. worker process","S"))

			# Create inter-process communication facilities:

			self.manager = pr.Manager()

			# Communicator commands:
			#	NOTE: Input... Use queue
			self.commandQueue = self.manager.Queue()

			# MOSI matrix:
			#	NOTE: Input... Use queue
			self.mosiMatrixQueue = self.manager.Queue()

			# Updates:
			#	NOTE: Output... use pipe
			self.updatePipeOut, self.updatePipeIn = pr.Pipe(False)

			# MISO matrix:
			#	NOTE: Output... use pipe
			self.misoMatrixPipeOut, self.misoMatrixPipeIn = pr.Pipe(False)

			# Spawner queue:
			self.spawnQueue = spawnQueue

			# MW terminal output:
			self.printQueue = printQueue

			# Call parent constructor:
			try:
				super(FCPRCommunicator, self).__init__(
					_communicatorRoutine,
					spawnQueue,
					printQueue,
					(profile, 
						self.commandQueue, 
						self.mosiMatrixQueue,
						self.updatePipeIn,
						self.misoMatrixPipeIn,
						printQueue),
					"CM"
				)
			except:
				ep.errorPopup()	

			# Build widget:
			self.bg = "#e2e2e2"
			self.fg = "black"
			self.green = "#168e07"
			self.red = "red"
			self.mainFrame = Tk.Frame(master)
			self.statusLabel = Tk.Label(
				self.mainFrame,
				text = "Disconnected",
				bg = self.bg,
				fg = self.red)
			self.button = Tk.Button(
				text = "Connect",
				bg = self.bg,
				highlightbackground = self.bg,
				fg = self.fg,
				command = super(FCPRCommunicator, self).start
			)

			self.statusLabel.pack(side = Tk.LEFT)
			self.button.pack(side = Tk.LEFT)
			self.mainFrame.pack()

		except Exception as e: # Print uncaught exceptions
			self._printM("UNHANDLED EXCEPTION IN FCPRCommunicator __init__: "\
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

	def _setStatus(self, newStatus): # =========================================

		# Update widget:

		# Update widget status:
		super(FCPRCommunicator, self)._setStatus(newStatus)

		# End _setStatus =======================================================

	def setProfile(self, newProfile): # ========================================
		
		self.profile = newProfile

		super(FCPRCommunicator, self).setArgs(
				(newProfile, 
					self.commandQueue, 
					self.mosiMatrixQueue,
					self.updatePipeIn,
					self.misoMatrixPipeIn,
					self.printQueue))

		# End setProfile =======================================================
