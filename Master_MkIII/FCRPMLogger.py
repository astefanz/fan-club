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
		MISOMatrixPipeOut,

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

		printM("RPM Log started into file \"{}\"".format(fileName))
		
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
			for slave in slaves[:-1]:
				f.write("{}: {} |".\
					format(slave[0] + 1, slave[1])) 
			f.write("{}: {}\n".\
				format(slaves[-1][0] + 1, slaves[-1][1]))

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
			for slave in slaves:
				for fan in range(slave[2]):

					f.write("RPM {}-{},".format(fan + 1, slave[0] + 1))
			# Write DC headers:
			for slave in slaves:
				for fan in range(slave[2]):
					f.write("DC {}-{}".format(fan + 1, slave[0] + 1))
					# Check if this is not the last fan of the last slave,
					# in which case a comma must be added:
					if not ((fan == slave[2] - 1) \
						and (slave[0] == slaves[-1][0])):
						f.write(',')

			# Move to next line:
			f.write('\n')
		
			# Get placeholder for "previous" time
			previousT = time.time()
			currentT = previousT
			
			printM("File ready", 'G')

			# Main loop ........................................................
			while True:

	
	except:
		ep.errorPopup("Error in RPM Logger process")


	# End rpmLoggerProcess =====================================================

## CLASS DEFINITION ############################################################

class FCRPMLogger(wg.FCWidget):

	def __init__(
		self, 
		master,
		process,	
		profile,

		spawnQueue,
		printQueue
	): # =======================================================================

		# Store arguments:
		self.printQueue = printQueue
		super(FCRPMLogger, self).__init__(
			master = master,
			process = FCRPMLoggerProcess,
			profile = profile,
			spawnQueue = spawnQueue,
			printQueue = printQueue
			specialArguments = ([]),
			symbol = "LG"
		)


		# End __init__ =========================================================

	def start(self, fileName, slaveList): # ====================================
		pass


		# End start ============================================================
