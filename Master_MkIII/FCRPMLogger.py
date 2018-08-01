################################################################################
## Project: Fan Club Mark II "Master" # File: FCRPMLogger.py                  ##
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
Data logging module

"""
################################################################################


## DEPENDENCIES ################################################################

# System:
import threading
import traceback
import sys # Exception handling
import inspect # get line number for debugging

# Data:
import queue
import time
import numpy as np

# FCMkII:
import FCArchiver as ac
import FCWidget as wg
import FCCommunicator as cm
import FCSlave as sv
from auxiliary import debug as d
from auxiliary import errorPopup as ep

## CONSTANT VALUES #############################################################    

# Printer status codes:
ON = 1
OFF = -1

## AUXILIARY DEFINITIONS #######################################################

def rpmLoggerProcess(
		commandQueue,
		mosiMatrixQueue,
		printQueue,
		profile,
		updatePipeOut,
		misoMatrixPipeOut,

		fileName,
		slaves

	): # =======================================================================

	def _printM(message, tag = 'S'): # -----------------------------------------
		try:
			printQueue.put_nowait(("[LG] " + message, tag))
		
		except:
			ep.errorPopup("Error in RPM Logger print: ")

		# End _printM ----------------------------------------------------------

	try:

		
		_printM("RPM Log started in file \"{}\"".format(fileName))
		
		# Translate fanMode parameter:
		if profile[ac.fanMode] == ac.SINGLE:
			fanModeStr = "single"
		elif profile[ac.fanMode] == ac.DOUBLE:
			fanModeStr = "double"
		else:
			fanModeStr = "[unspecified]"

		with open(fileName, 'w') as f:

			# Set up file:
			# First line:
			f.write("Fan Club MkII data log started on {}  using "\
				"profile \"{}\" with a maximum of {} \"{}\" fans.\n".\
				format(
					time.strftime(
						"%a %d %b %Y %H:%M:%S", time.localtime()), 
					profile[ac.name],
					profile[ac.maxFans],
					fanModeStr
					)
				)
			
			# Second line:
			f.write("MAC Addresses of each index: \n\t")
			for slave in slaves.values():
				f.write("{}: {},\t".\
					format(slave[cm.INDEX] + 1, slave[cm.MAC])) 
			f.write("\n")

			# Third line:
			f.write("NOTE: Columns headers are formatted as FAN#-MODULE#\n")
			
			# Fourth line (blank):
			f.write("\n")
			
			# Headers (fifth line):
			f.write("Time (s),")
			
			# RECALL:
			#
			# slave[0] := index
			# slave[1] := MAC
			# slave[2] := active fans
			# slave[3] := data queue

			# Write RPM headers:
			for slave in slaves.values():
				for fan in range(slave[cm.FANS]):
					f.write("RPM {}-{},".format(fan + 1, slave[cm.INDEX] + 1))
			# Write DC headers:
			for slave in slaves.values():
				for fan in range(slave[cm.FANS]):
					f.write("DC {}-{},".format(fan + 1, slave[cm.INDEX] + 1))
					# Check if this is not the last fan of the last slave,
					# in which case a comma must be added:

		
			# Get placeholder for "previous" time
			startTime = time.time()
			
			_printM("File ready", 'G')

			# Main loop ........................................................
			while True:
					
				# Check pipe for shutdown message:
				if updatePipeOut.poll():
					update = updatePipeOut.recv()

					if update[wg.COMMAND] == wg.STOP:
						_printM("Closing log")
						break

				if misoMatrixPipeOut.poll():
					# New matrix available

					# Get matrix:
					matrix = misoMatrixPipeOut.recv()
					
					# Write timestamp:
					f.write("{},".format(time.time() - startTime))

					# Write data:

					# Print RPM's and store DC's in placeholder:
					dcs = ''
					for index, row in enumerate(matrix):
						# NOTE: Here the ith row in the matrix represents the
						# Slave of index i (or i+1 for the user)
						
						# Check if this Slave has been updated:
						if row[cm.MISO_COLUMN_TYPE] is sv.MISO_UPDATED:
							# Slave updated (this row contains new values)
							# Print new values

							# Print RPM's:
							# (Go from special codes to just before duty cycles)
							for rpm in row[cm.MISO_SPECIALCOLUMNS:\
									slaves[index][cm.FANS] + \
										cm.MISO_SPECIALCOLUMNS]:
								
								f.write("{},".format(rpm))

							# Print DC's:
							for dc in row[slaves[index][cm.FANS] + \
								cm.MISO_SPECIALCOLUMNS:]:
								dcs += "{},".format(dc)

						else:
							# Slave not updated. Add blank cells for each RPM
							# and DC:	
							for rpm in range(slaves[index][cm.FANS]):
								
								f.write(',')
								dcs += ','

					# Print duty cycles and end line:
					f.write(dcs + "\n")

			
			_printM("RPM Log closed")
	
	except:
		ep.errorPopup("Error in RPM Logger process")
		_printM("WARNING: RPM log stopped by exception (See pop-up window)")


	# End rpmLoggerProcess =====================================================

## CLASS DEFINITION ############################################################

class FCRPMLogger(wg.FCWidget):

	def __init__(
		self, 
		master,
		startCallback,
		stopCallback,
		profile,

		spawnQueue,
		printQueue
	): # =======================================================================

		# Store arguments:
		self.startCallback = startCallback
		self.stopCallback = stopCallback
		self.printQueue = printQueue
		super(FCRPMLogger, self).__init__(
			master = master,
			process = rpmLoggerProcess,
			profile = profile,
			spawnQueue = spawnQueue,
			printQueue = printQueue,
			specialArguments = ("Unnamed_RPM_Log.csv", []),
			watchdogType = wg.WIDGET,
			symbol = "LG"
		)


		# End __init__ =========================================================

	def start(self, fileName, slaveList): # ====================================

		self._setSpecialArguments((fileName, slaveList))
		super(FCRPMLogger, self).start()

		# End start ============================================================

	def _setStatus(self, newStatus): # =========================================

		if newStatus is wg.ACTIVE:
			self.startCallback()
		elif newStatus is wg.INACTIVE:
			self.stopCallback()
		
		super(FCRPMLogger, self)._setStatus(newStatus)

		# End _setStatus =======================================================


