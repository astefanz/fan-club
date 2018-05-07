################################################################################
## Project: Fan Club Mark II "Master" # File: Printer.py                      ##
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

import threading
import Queue
import time
import traceback
import sys # Exception handling
import inspect # get line number for debugging
import numpy as np

import inspect # get line number for debugging
import Profiler
## CONSTANT VALUES #############################################################    

def d():
	print inspect.currentframe().f_back.f_lineno
# Printer status codes:
ON = 1
OFF = -1

## CLASS DEFINITION ############################################################

class Printer:

	def __init__(self, fanMode, queueSize): # ==================================
		# ABOUT: Constructor for class Printer.
		# PARAMETERS:
		# - fanMode: int, predefined code indicating fan configuration.
		# - printMethod: Method with which to print to Interface.

		# Sentinels to track printing:
		self.printLock = threading.Lock()
		self.stopFlag = False
	
		self.status = OFF
		self.statusLock = threading.Lock()

		# List of Slaves from which to print:
		self.slaves = np.empty((0,4), dtype = object)
		self.slavesLock = threading.Lock()
	
		# Placholder for fan mode:
		self.fanMode = fanMode
		# Placeholder for queue size:
		self.queueSize = queueSize
		
		# Printer queue:
		self.mainQueue = Queue.Queue(queueSize)

		# Placeholder for Printer thread:
		self.thread = None

		self.printM("Printer initialized")
		# End Printer constructor ==============================================

	# THREAD ROUTINES ----------------------------------------------------------
	def _printerRoutine(self, # ================================================
		fileName, 
		profileName, maxFans, periodS,
		append = True):
		# ABOUT: Thread routine for printing.
		# PARAMETERS:
		# - fileName: str, name of the file to open
		# - profileName: str, name of the "profile" to write on the file
		# - maxFans: int, maximum number of fans to be displayed
		# - periodS: float, seconds between checks to the queue.
		# - append: bool, whether to append to a preexisting file or overwrite
		#	it.

		# PRINTING ALGORITHM SUMMARY:
		# - Add general timestamp and slave MAC legend
		# - For each "cycle":
		#	- Get a timestamp
		# 	- For each Slave in the list:
		# 		- Try to get list of RPM's and DC's.
		#		- Format data as a single row, w/ '' for failures to fetch
		#	- Append data to file

		# PRINTING FORMAT EXAMPLE:
		#
		# Fan Club MkII data log opened on DATE TIME with profile "PROFILE_NAME"
		# 0: MA:CA:DD:RE:SS, 1: MA:CA:DD:RE:SS, 2: MA:CA:DD:RE:SS
		#
		# TIME, ID, RPM1, RPM2, RPM3, DC1, DC2, DC3
		# 01233141123, 0, 10000, 11500, 9801, 0.90, 0.10, 0.85 

		try:
			
			# THREAD SETUP -----------------------------------------------------
			self.printM("Printer thread started w/ file name {} and profile "\
				"\"{}\"".\
				format(fileName, profileName))
			
			# Translate fanMode parameter:
			if self.fanMode == Profiler.SINGLE:
				fanModeStr = "single"
			elif self.fanMode == Profiler.DOUBLE:
				fanModeStr = "double"
			else:
				fanModeStr = "[unspecified]"

			# MAIN LOOP --------------------------------------------------------
			with open(fileName, 'w') as f:
				# File setup ...................................................
				
				# First line:
				f.write("Fan Club MkII data log started on {}  using "\
					"profile \"{}\" with a maximum of {} \"{}\" fans.\n".\
					format(
						time.strftime(
							"%a %d %b %Y %H:%M:%S", time.localtime()), 
						profileName,
						maxFans,
						fanModeStr
						)
					)
				
				# Second line:
				f.write("MAC Addresses of each index: \n\t")
				for slave in self.slaves[:-1]:
					f.write("{}: {} |".\
						format(slave[0] + 1, slave[1])) 
				f.write("{}: {}\n".\
					format(self.slaves[-1][0], self.slaves[-1][1]))

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
				for slave in self.slaves:
					for fan in range(slave[2]):

						f.write("RPM {}-{},".format(fan + 1, slave[0] + 1))
				# Write DC headers:
				for slave in self.slaves:
					for fan in range(slave[2]):
						f.write("DC {}-{}".format(fan + 1, slave[0] + 1))
						# Check if this is not the last fan of the last slave,
						# in which case a comma must be added:
						if not ((fan == slave[2] - 1) \
							and (slave[0] == self.slaves[-1][0])):
							f.write(',')

				# Move to next line:
				f.write('\n')
			
				# Get placeholder for "previous" time
				previousT = time.time()
				currentT = previousT
				# Main loop ....................................................
				while True:
					try:
						# Acquire lock:
						self.printLock.acquire()
						# Check for pause or terminate variables:
						
						if self.stopFlag:
							# Break out of loop and stop thread:
							break
						# Set up placeholders:
						rpms = ''
						dcs = ''
						
						# Keep track of whether at least one Slave was updated:
						updateFound = False

						# Loop over Slave list to fetch data
						for slave in self.slaves:
							# Try to fetch RPM's
							try:
								# Check for stop flags:

								if self.stopFlag:
									# Break out of loop and stop thread:
									break

								# Get from queue w/o blocking:
								fetched = slave[3].get_nowait()
								# If this line is reached, an update was
								# found:
								updateFound = True

								# First of the two elements is a list of rpms:
								for rpm in fetched[0]:
									
									# Append to the rpms string and add a comma:
									rpms += str(rpm) + ','

								# Loop over all DC's:
								for dc in fetched[1]:
									dcs += str(dc) + ','
							except Queue.Empty:
								# If the Queue is empty, fill portion w/ '':
								
								for NaN in range(slave[2]):
									rpms += ","
									dcs += ","

						# Once all the RPM's and DC's have been obtained, check
						# if at least one Slave was updated:
						
						if updateFound:
							f.write("{},{},{}\n".format(
								time.time() - previousT, rpms[:-1], dcs[:-1]))
								#                           \---/     \---/
								#                     Remove trailing commas

						time.sleep(periodS)
					finally:
						self.printLock.release()
				
				# If the loop is broken, this thread must terminate:
				self.printM("Printer thread terminated")
			
		except Exception as e:
			self.printM("[PT][routine] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")
		
		# end _printerRoutine ==================================================

	def getStatus(self): # =====================================================
		# ABOUT: Get integer status code in a thread-safe manner.
		
		try:
			# Acquire lock:
			self.statusLock.acquire()
			# Fetch status as placeholder to return after releasing lock:
			placeholder = self.status

			# Notice lock will be released by finally clause:
			return placeholder

		except Exception as e:
			self.printM("[PT][routine] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")

		finally:
			self.statusLock.release()
			
			# End getStatus ====================================================

	def _setStatus(self, newStatus, block = True): # ===========================
		# ABOUT: Get integer status code in a thread-safe manner.

		try:
			# Acquire lock:
			if block:
				self.statusLock.acquire()
			
			# Validate input:
			if newStatus not in (ON, OFF):
				raise ValueError("Argument 'newStatus' must be valid int code,"\
					" not {}".format(newStatus))

			# After validating, set new status code:
			self.status = newStatus
			
			# Print new Status:
			if newStatus == ON:
				self.printM("[PT][_sS] Printer thread ON")
			elif newStatus == OFF: 
				self.printM("[PT][_sS] Printer thread OFF")
			# Done (lock will be released in finally clause)
			return
			
		except Exception as e:
			self.printM("[PT][routine] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")

		finally:

			if block:
				self.statusLock.release()
			
			# End getStatus ====================================================



	def add(self, mac, index, activeFans): # ===================================
		# ABOUT: Add a new Slave to the list.
		# PARAMETERS:
		# - mac: str, MAC address of the new Slave.
		# - index: int, index of the new Slave.
		
		try:
			if self.getStatus() != OFF:
				# No Slaves can be added while printing.
				raise RuntimeError("Cannot add Slaves while printing")
			
			self.printLock.acquire()
			
			# Add Slave to data structure:
			self.slaves = np.concatenate(
				(
			 	self.slaves,
				((index, mac, activeFans,
				  Queue.Queue(self.queueSize)),)
				)
			)

		except Exception as e:

			self.printM("[PT][add] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")

		finally:
			# Guarantee lock release:
			self.printLock.release()

		# End add ==============================================================

	def start(self, # ==========================================================
		fileName,
		profileName, 
		maxFans,
		periodS): 
		# ABOUT: Start the printer thread.
		try:
			# Validate input:
			if type(fileName) not in (str, unicode):
				raise TypeError("Argument 'fileName' must be of type str, "\
					"not {}".format(type(fileName)))
			elif type(profileName) is not str:
				raise TypeError("Argument 'profileName' must be of type str, "\
					"not {}".format(type(profileName)))
			elif type(maxFans) is not int:
				raise TypeError("Argument 'maxFans' must be of type int, "\
					"not {}".format(type(maxFans)))

			# Check if this Slave is printing:
			if self.getStatus() == ON:
				# Only one printer thread at a time.
				raise threading.ThreadError(
					"Printer error: Printer thread already running")
		
			# Check if the Slave list is empty:
			if len(self.slaves) == 0:
				raise RuntimeError("Printer error: empty Slave list")
			
			else:
				
				# Set sentinel variable:
				self.stopFlag = False

				# Start Printer thread:
				self.thread = threading.Thread(
					name = "FCMkII_Printer",
					target = self._printerRoutine,
					args = (fileName, profileName, maxFans, periodS)
					)
				
				self.thread.setDaemon(True)
				self.thread.start()
				
				self._setStatus(ON)

				# Done
				return

		except Exception as e:

			self.printM("[PT][start] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")
		
		# End start ============================================================
	
	def stop(self): # ==========================================================
		# ABOUT: Terminate the current printer thread.
		try:
			# Check if the thread is running:
			if self.getStatus() == OFF:
				raise threading.ThreadingError("Tried to stop stopped Printer")

			else:
				# Set flag for thread to end execution:
				self.printLock.acquire()
				self.stopFlag = True
				self.printLock.release()
				
				# Join thread:
				self.thread.join()
				
				# Thread is done. Set placeholder to None:
				self.thread = None
				
				# Update status:
				self._setStatus(OFF)

				# Done
				return

		except Exception as e:

			self.printM("[PT][terminate] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")

		finally:
			# Guarantee lock release:
			try:
				self.printLock.release()
			except threading.ThreadError:
				pass
	
		# End stop  ============================================================

	def put(self, index, data): # ==============================================
		# ABOUT: Store data into the printing Queue of a specific Slave.
		# PARAMETERS:
		# - index: int, index of Slave.
		# - data: 2-tuple of two numpy.array instances, where the first item
		#	(data[0]) is an array of integers representing measured RPM values
		#	and (data[1]) is an array of floats representing measured DC's.
		# RAISES:
		# - IndexError if index is not a valid index.
		# - Queue.Full if the data queue is full.
		# - RuntimeError if the Printer is inactive.

		try:
			if self.getStatus() != ON:
				raise RuntimeError("Tried to pass data to inactive Printer")
		
			
			self.slaves[index][3].put_nowait(data)

		except Queue.Full as e:
			raise e
		except Exception as e:

			self.printM("[PT][put] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")

		# End put ==============================================================

	def printM(self, message, tag = 'S'): # ===================================
		# ABOUT: Print a message by placing it in the print Queue.
		# NOTE: See printM in module Communicator.py

		return self.mainQueue.put((message, tag))

		# End printM ===========================================================
