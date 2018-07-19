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

#from mttkinter import mtTkinter as Tk
import tkinter as Tk

# System:
import sys			# Exception handling
import traceback	# More exception handling
import random		# Random names, boy
import resource		# Socket limit
import threading	# Multitasking
import _thread		# thread.error
import multiprocessing as pr # The big guns

# Data:
import time			# Timing
import queue
import numpy as np	# Fast arrays and matrices

# FCMkII:
import FCCommunicator as cm
import FCWidget as wg
import FCSlave as sv
import FCSpawner as sw

import fci.FCCSlaveList as sl
import fci.FCCControlBar as cb
import fci.FCCStatusBar as sb

import auxiliary.errorPopup as ep

## CONSTANTS ###################################################################

COMMAND_QUEUE = 0
MOSI_QUEUE = 1
UPDATE_PIPE = 2
MISO_MATRIX_PIPE = 3

## AUXILIARY ROUTINE ###########################################################

def _communicatorRoutine(
		commandQueue,
		mosiMatrixQueue,
		printQueue,
		profile,
		updatePipeOut,
		oldMISOMatrixPipeOut,
		networkUpdatePipeIn,
		newMISOMatrixPipeIn,
	): # ===================================================================
	try:

		printQueue.put_nowait(("[CR] Starting Comms. Process", 'S'))

		# Create Communicator:
		comms = cm.FCCommunicator(
			profile = profile,
			commandQueue = commandQueue,
			mosiMatrixQueue = mosiMatrixQueue,
			printQueue = printQueue,
			updatePipeOut = updatePipeOut,
			networkUpdatePipeIn = networkUpdatePipeIn,
			newMISOMatrixPipeIn = newMISOMatrixPipeIn
			)

		while True:
			
			# Check shutdown flag ----------------------------------------------
			if comms.stoppedFlag:
				printQueue.put_nowait(("[CR] Communications stopped",'W'))
				break

	except Exception as e: # Print uncaught exceptions
		printQueue.put(("[CR] UNHANDLED EXCEPTION terminated Network Process: "\
			"\"{}\"".format(traceback.format_exc()), "E")
			)

	# End _communicatorRoutine =================================================

class FCPRCommunicator(wg.FCWidget):
	
	def __init__(self,
			master,
			profile,
			commandQueue,
			mosiMatrixQueue,
			spawnQueue,
			printQueue
		): # ===================================================================
		# ABOUT: Constructor for class FCPRCommunicator.
		try:
			printQueue.put(("[CM] Initializing Comms. worker process","S"))
			
			# Create inter-process communication facilities:
			
			self.profile = profile
			self.commandQueue = commandQueue
			self.mosiMatrixQueue = mosiMatrixQueue


			# Updates:
			#	NOTE: Output... use pipe
			self.networkUpdatePipeOut, self.networkUpdatePipeIn = pr.Pipe(False)

			# New MISO matrices:
			self.newMISOMatrixPipeOut, self.newMISOMatrixPipeIn = pr.Pipe(False)

			# Spawner queue:
			self.spawnQueue = spawnQueue

			# MW terminal output:
			self.printQueue = printQueue

			# Call parent constructor:
			try:
				super(FCPRCommunicator, self).__init__(
					master = master,
					process = _communicatorRoutine,
					spawnQueue = spawnQueue,
					printQueue = printQueue,
					profile = profile,
					specialArguments = (	
						self.networkUpdatePipeIn,
						self.newMISOMatrixPipeIn
					),
					symbol = "CM"
				)
			except:
				ep.errorPopup()	

			# Build Graphical Interface:
			
			"""
			+-------------------------------------------------------------------
			|[x] Communications
			| [ LIST]
			+-------------------------------------------------------------------
			|...
			"""

			self.statusMap = {
				wg.ACTIVE : cm.CONNECTED,
				wg.INACTIVE : cm.DISCONNECTED,
				wg.STARTING : cm.CONNECTING,
				wg.STOPPING : cm.DISCONNECTING
			}

			self.bg = "#e2e2e2"
			self.fg = "black"

			self.frame = Tk.Frame(
				self.master,
				bg = self.bg
			)
			self.toggleFrame = Tk.Frame(
				self.frame,
				bg = self.bg
			)
			self.checkButtonVar = Tk.BooleanVar()
			self.checkButtonVar.set(True)
			self.packed = True
			self.checkButton = Tk.Checkbutton(
				self.toggleFrame,
				text = "Communications",
				bg = self.bg,
				fg = self.fg,
				command = self._toggle,
				variable = self.checkButtonVar
			)
			self.checkButton.pack(side = Tk.LEFT)
			self.toggleFrame.pack(side = Tk.TOP, fill = Tk.X, expand = True)

			self.frame.pack(side = Tk.TOP, fill = Tk.BOTH, expand = True)

			self.widgetFrame = Tk.Frame(
				self.frame,
				bg = self.bg
			)
			self.widgetFrame.pack(side = Tk.TOP, fill = Tk.BOTH, expand = True)

			self.slaveList = sl.FCCSlaveList(self.widgetFrame)
			self.slaveList.pack(side = Tk.TOP, fill = Tk.BOTH, expand = True)

			self.controlBar = cb.FCCControlBar(
				self.widgetFrame, self.slaveList, self.commandQueue) 
			self.controlBar.pack(side = Tk.TOP, fill = Tk.X, expand = True)
			self.controlBar.setStatus(cm.DISCONNECTED)

			self.statusBar = sb.FCCStatusBar(
				self.widgetFrame, self.start, self.stop)
			self.statusBar.setStatus(cm.DISCONNECTED)

			self.statusBar.pack(fill = Tk.X, expand = False)

		except Exception as e: # Print uncaught exceptions
			self._printM("UNHANDLED EXCEPTION IN FCPRCommunicator __init__: "\
				"\"{}\"".\
				format(traceback.format_exc()), "E")

		# End __init__ =========================================================

	def getMISOMatrix(self): # =================================================

		if self.newMISOMatrixPipeOut.poll():
			return self.newMISOMatrixPipeOut.recv()

		else:	
			return None

		# End getMISOMatrix ====================================================

	def getNetworkUpdate(self): # ==============================================

		if self.networkUpdatePipeOut.poll():
			return self.networkUpdatePipeOut.recv()

		else:
			return None

		# End getNetworkUpdate =================================================

	def misoMatrixIn(self, matrix): # ==========================================
		# Input a new MISO matrix
		# NOTE: This widget does not need "old" MISO matrices 

		del matrix

		# End misoMatrixIn =====================================================


	""""
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
	"""

	def _setStatus(self, newStatus): # =========================================

		# Update widget:

		# Update widget status:
		super(FCPRCommunicator, self)._setStatus(newStatus)

		# Update GUI:
		self.controlBar.setStatus(self.statusMap[newStatus])
		self.statusBar.setStatus(self.statusMap[newStatus])

		if newStatus is (wg.INACTIVE):
			self.slaveList.clear()
			self.statusBar.clear()

		# End _setStatus =======================================================

	def _toggle(self, event = None): # =========================================
		
		if self.checkButtonVar.get() and not self.packed:
			self.widgetFrame.pack(side = Tk.TOP, fill = Tk.BOTH, expand = True)
			self.packed = True

		elif not self.checkButtonVar.get() and self.packed:
			self.widgetFrame.pack_forget()
			self.packed = False

		# End _toggle ==========================================================

	def _updateMethod(self): # =================================================


		if self.networkUpdatePipeOut.poll():
			# Try to fetch update:
			update = self.networkUpdatePipeOut.recv()
			print("fetched: ",update)

			# Apply:
			if update[0] is cm.NEW:
				self.slaveList.addSlaves(update[1])
				self.statusBar.addSlaves(update[1])

			if update[0] is cm.UPDATE:
				self.slaveList.updateSlaves(update[1])
				self.statusBar.updateSlaves(update[1])

		# End _updateMethod ====================================================

