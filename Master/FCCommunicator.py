################################################################################
## Project: Fan Club Mark II "Master" ## File: FCCommunicator.py              ##
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
This module handles low-level socket communications w/ Slave units.

"""
################################################################################

## DEPENDENCIES ################################################################

# Network:
import socket		# Networking

# System:
import sys			# Exception handling
import traceback	# More exception handling
import random		# Random names, boy
import resource		# Socket limit
import threading	# Multitasking
import thread		# thread.error
import multiprocessing # The big guns

# Data:
import time			# Timing
import Queue
import numpy as np	# Fast arrays and matrices

# FCMkII:
import FCSlave as sv
import FCArchiver as ac
from auxiliary import names

## CONSTANT DEFINITIONS ########################################################

DEBUG = False
VERSION = "Independent 0"
FORCE_IP_ADDRESS = "0.0.0.0"
	#= "192.168.1.129" # (Basement lab)

# Commands:
ADD = 1
DISCONNECT = 2
REBOOT = 3

# Special values:
NONE = -1
ALL = -2

FCPRCONSTS = (ADD, DISCONNECT, REBOOT)

# Outputs:
NEW = 11

# MOSI commands:
MOSI_NO_COMMAND = 20
MOSI_DC = 21
MOSI_CHASE = 22
MOSI_DISCONNECT = 23
MOSI_REBOOT = 24

# Change codes:
NO_CHANGE = 0
CHANGE = 1

## CLASS DEFINITION ############################################################

class FCCommunicator:

	def __init__(self,
			profile,
			# Multiprocessing:
			commandQueue,
			mosiMatrixQueue,
			printQueue
		): # ===================================================================
		# ABOUT: Constructor for class FCPRCommunicator.

		try:
			
			"""
			# Provisional timestamping solution:
			self.canTimestamp = False
			try:
				self.file = open("MkII_test_on_{}".\
					format(time.strftime("%a %d %b %Y %H:%M:%S")), "w")
				self.canTimestamp = True
				
				self.file.write("MkII performance testing started on {}\n".\
					format(time.strftime("%a %d %b %Y %H:%M:%S")))

			except IOError:
				print "IOError Opening timestamp file. Cannot record!"
				self.canTimestamp = False
				
			
			
			self.file.write("Configuring network on {}\n".format(
				time.strftime(
				"%H:%M:%S", time.localtime())))
			"""

			# INITIALIZE DATA MEMBERS ==========================================

			# Store parameters -------------------------------------------------

			self.profile = profile

			# Network:
			self.broadcastPeriodS = profile[ac.broadcastPeriodS]
			self.periodMS = profile[ac.periodMS]
			self.periodS = profile[ac.periodS]
			self.broadcastPort = profile[ac.broadcastPort]
			self.passcode = profile[ac.passcode]
			self.misoQueueSize = profile[ac.misoQueueSize]
			self.maxTimeouts = profile[ac.maxTimeouts]
			self.maxLength = profile[ac.maxLength]

			# Fan array:
			self.maxFans = profile[ac.maxFans]
			self.fanMode = profile[ac.fanMode]
			self.targetRelation = profile[ac.targetRelation]
			self.fanFrequencyHZ = profile[ac.fanFrequencyHZ]
			self.counterCounts = profile[ac.counterCounts]
			self.pulsesPerRotation = profile[ac.pulsesPerRotation]
			self.maxRPM = profile[ac.maxRPM]
			self.minRPM = profile[ac.minRPM]
			self.minDC = profile[ac.minDC]
			self.chaserTolerance = profile[ac.chaserTolerance]
			self.maxFanTimeouts = profile[ac.maxFanTimeouts]
			self.pinout = profile[ac.pinout]
			
			# Multiprocessing:
			self.misoMatrixPipeIn = misoMatrixPipeIn
			self.commandQueue = commandQueue
			self.updatePipeIn = updatePipeIn
			self.mosiMatrixQueue = mosiMatrixQueue

			# Output queues:
			self.printQueue = printQueue
			self.newSlaveQueue = Queue.Queue()

			# Initialize Slave-list-related data:
			self.slavesLock = threading.Lock()

			"""
			# Create a temporary socket to obtain Master's IP address:
			temp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			temp.connect(('192.0.0.8', 1027))
			self.hostIP = temp.getsockname()[0]
			temp.close()
			
			self.printM("\tHost IP: {}".format(self.hostIP))
			"""

			# Use resource library to get OS to give extra sockets, for good
			# measure:
			resource.setrlimit(resource.RLIMIT_NOFILE, 
				(1024, resource.getrlimit(resource.RLIMIT_NOFILE)[1]))
			
			# INITIALIZE MASTER SOCKETS ========================================

			# INITIALIZE LISTENER SOCKET ---------------------------------------

			# Create listener socket:
			self.listenerSocket = socket.socket(
				socket.AF_INET, socket.SOCK_DGRAM)


			# Configure socket as "reusable" (in case of improper closure): 
			self.listenerSocket.setsockopt(
				socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

			# Bind socket to "nothing" (Broadcast on all interfaces and let OS
			# assign port number):
			self.listenerSocket.bind(("", 0))

			self.printM("\tlistenerSocket initialized on " + \
				str(self.listenerSocket.getsockname()))

			self.listenerPort = self.listenerSocket.getsockname()[1]

			# INITIALIZE BROADCAST SOCKET --------------------------------------

			# Create broadcast socket:
			self.broadcastSocket = socket.socket(
				socket.AF_INET, socket.SOCK_DGRAM)

			# Configure socket as "reusable" (in case of improper closure): 
			self.broadcastSocket.setsockopt(
				socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

			# Configure socket for broadcasting:
			self.broadcastSocket.setsockopt(
				socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

			# Bind socket to "nothing" (Broadcast on all interfaces and let OS 
			# assign port number):
			self.broadcastSocket.bind((FORCE_IP_ADDRESS, 0))

			self.broadcastSocketPort = self.broadcastSocket.getsockname()[1]

			self.broadcastLock = threading.Lock()

			self.printM("\tbroadcastSocket initialized on " + \
				str(self.broadcastSocket.getsockname()))

			# Create reboot socket:
			self.rebootSocket = socket.socket(
				socket.AF_INET, socket.SOCK_DGRAM)

			# Configure socket as "reusable" (in case of improper closure): 
			self.rebootSocket.setsockopt(
				socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

			# Configure socket for rebooting:
			self.rebootSocket.setsockopt(
				socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

			# Bind socket to "nothing" (Broadcast on all interfaces and let OS 
			# assign port number):
			self.rebootSocket.bind((FORCE_IP_ADDRESS, 0))

			self.rebootSocketPort = self.rebootSocket.getsockname()[1]

			self.rebootLock = threading.Lock()

			self.printM("\trebootSocket initialized on " + \
				str(self.rebootSocket.getsockname()))

			# Create disconnect socket:
			self.disconnectSocket = socket.socket(
				socket.AF_INET, socket.SOCK_DGRAM)

			# Configure socket as "reusable" (in case of improper closure): 
			self.disconnectSocket.setsockopt(
				socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

			# Configure socket for disconnecting:
			self.disconnectSocket.setsockopt(
				socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

			# Bind socket to "nothing" (Broadcast on all interfaces and let OS 
			# assign port number):
			self.disconnectSocket.bind((FORCE_IP_ADDRESS, 0))

			self.disconnectSocketPort = self.disconnectSocket.getsockname()[1]

			self.disconnectLock = threading.Lock()

			self.printM("\tdisconnectSocket initialized on " + \
				str(self.disconnectSocket.getsockname()))

			# Reset any existing phantom connections:
			self.sendDisconnect()

			# SET UP MASTER THREADS ============================================

			# INITIALIZE BROADCAST THREAD --------------------------------------

			# Configure sentinel value for broadcasts:
			self.broadcastSwitch = True
				# ABOUT: UDP broadcasts will be sent only when this is True
			self.broadcastSwitchLock = threading.Lock() # thread-safe access

			self.broadcastThread = threading.Thread(
				name = "FCMkII_broadcast",
				target = self._broadcastRoutine,
				args = ["N|{}|{}".format(
							self.passcode, 
							self.listenerPort), 
						self.broadcastPeriodS]
				)

			# Set thread as daemon (background task for automatic closure):
			self.broadcastThread.setDaemon(True)

			# INITIALIZE LISTENER THREAD ---------------------------------------

			self.listenerThread =threading.Thread(
				name = "FCMkII_listener",
				target = self._listenerRoutine)

			# Set thread as daemon (background task for automatic closure):
			self.listenerThread.setDaemon(True)

			# INITIALIZE INPUT AND OUTPUT THREADS ------------------------------
			self.outputThread  = threading.Thread(
				name = "FCMkII_output",
				target = self._outputRoutine) 
			self.outputThread.setDaemon(True)

			self.inputThread = threading.Thread(
				name = "FCMkII_input",
				target = self._inputRoutine) 
			self.inputThread.setDaemon(True)

			# SET UP LIST OF KNOWN SLAVES  =====================================
			# NOTE: This list will be a Numpy array of Slave objects.

			# Create a numpy array for storage:
			self.slaves = np.empty(len(savedMACs), object)
				# Create an empty numpy array
			# Loop over savedMACs to instantiate any saved Slaves:
			newSlaves = []
			for index in range(len(savedMACs)):

				# NOTE: Here each sub list, if any, contains data to initialize
				# known Slaves, in the following order:
				#
				# [0]: Name (as a string)
				# [1]: MAC address (as a string)
				# [2]: Number of active fans (as an integer)
			

				self.slaves[index] = \
					sv.FCSlave(
					mac = savedMACs[index],
					status = sv.DISCONNECTED,
					routine = self._slaveRoutine,
					routineArgs = (index,),
					misoQueueSize = misoQueueSize,
					index = index,
					)

				# Add to list:
				newSlaves.append(
					(savedMACs[index], 
					sv.DISCONNECTED, 
					self.maxFans,
					self.slaves[index].getVersion()))

			self.newSlaveQueue.put_nowait(newSlaves)

			# START THREADS:

			# Start inter-process threads:
			self.outputThread.start()
			self.inputThread.start()

			# Start Master threads:
			self.listenerThread.start()
			self.broadcastThread.start()
			
			# Start Slave threads:
			for slave in self.slaves:
				slave.start()

			# DONE
			self.printM("Communicator ready", "G")
		
			"""
			self.file.write("Configured network by {}\n".format(
				time.strftime(
					"%H:%M:%S", time.localtime())))
			"""

		
		except Exception as e: # Print uncaught exceptions
			self.printM("UNHANDLED EXCEPTION IN Communicator __init__: "\
				"\"{}\"".\
				format(traceback.format_exc()), "E")

		# End __init__ =========================================================
	
	# # THREAD ROUTINES # # # # # # # # # # # # # # # # # # # # # # # # # # # #  

	def _inputRoutine(self): # =================================================

		try:		
			self.printM("[CM][IR] Prototype input routine started","G")
			while True:
				try:
					# Input --------------------------------------------------------
					
					# Check commands:
					if not self.commandQueue.empty():
						command = self.commandQueue.get_nowait()
						
						# Classify command:
						if command[0] == ADD:
							self.add(command[1])

						elif command[0] == DISCONNECT:
							if command[1] == ALL:
								self.sendDisconnect()
							else:
								self.slaves[command[1]].setMOSI((MOSI_DISCONNECT,))

						elif command[0] == REBOOT:
							if command[1] == ALL:
								self.sendReboot()
							else:
								self.slaves[command[1]].setMOSI((MOSI_REBOOT,))

					# Check matrix:
					matrix = self.mosiMatrixQueue.get_nowait()
					index = 0
					for row in matrix:
						if row[0] is not NO_COMMAND:
							self.slaves[index].setMOSI(row)

						index += 1
				
				except Queue.Empty:
					continue

				except Exception as e: # Print uncaught exceptions
					self.printM("[CM][IR] EXCEPTION: "\
						"\"{}\"".\
						format(traceback.format_exc()), "E")

		except Exception as e: # Print uncaught exceptions
			self.printM("[CM][IR] UNHANDLED EXCEPTION: "\
				"\"{}\" (BROKE OUT OF LOOP)".\
				format(traceback.format_exc()), "E")
		# End _inputRoutine ====================================================

	def _outputRoutine(self): # ================================================
		# Summarize asynchronous output from each Slave thread into a matrix
		# and send out status changes

		try:
		
			self.printM("Prototype output routine started", "G")
			while True:
				try:
					# Output -------------------------------------------------------

					# Check for new Slaves:
					newSlaves = self.getNewSlaves()
					if newSlaves is not None:
						self.updatePipeIn.send((NEW, newSlaves))


					# Assemble output matrix:
					output = []
					
					for slave in self.slaves:
						output.append(slave.getMISO())

					self.misoMatrixPipeIn.send(output)

				except Exception as e: # Print uncaught exceptions
					self.printM("EXCEPTION IN Comms. outp. thread: "\
						"\"{}\"".\
						format(traceback.format_exc()), "E")

		except Exception as e: # Print uncaught exceptions
			self.printM("UNHANDLED EXCEPTION in Communicator output thread: "\
				"\"{}\" (BROKE OUT OF LOOP)".\
				format(traceback.format_exc()), "E")
		# End _outputRoutine ===================================================

	def _broadcastRoutine(self, broadcastMessage, broadcastPeriod): # ==========
		""" ABOUT: This method is meant to run inside a Communicator instance's
			broadcastThread. 
		"""
		try: # Catch any exception for printing (have no stdout w/ GUI!)

			broadcastSocketPortCopy = self.broadcastSocketPort # Thread safety

			self.printM("[BT] Broadcast thread started w/ period of {}s "\
				"on port {}"\
				.format(broadcastPeriod, self.broadcastPort), "G")

			count = 0

			while(True):

				# Increment counter:
				count += 1

				# Wait designated period:
				time.sleep(broadcastPeriod)

				#self.broadcastLock.acquire()
				#self.broadcastSwitchLock.acquire()
				# Send broadcast only if self.broadcastSwitch is True:
				if self.broadcastSwitch:
					# Broadcast message:
					for i in (1,2):
						self.broadcastSocket.sendto(broadcastMessage, 
							("<broadcast>", self.broadcastPort))

				#self.broadcastSwitchLock.release()
				#self.broadcastLock.release()

				# Guarantee lock release:
			
		except Exception as e:
			self.printM("[BT] UNHANDLED EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")

			#try:
				#self.broadcastSwitchLock.release()
				#self.broadcastLock.release()
			#except thread.error:
				#pass

		# End _broadcastRoutine ================================================

	def _listenerRoutine(self): # ==============================================
		""" ABOUT: This method is meant to run within an instance's listener-
			Thread. It will wait indefinitely for messages to be received by
			the listenerSocket and respond accordingly.
		"""

		self.printM("[LT] Listener thread started. Waiting.", "G")

		# Get standard replies:
		launchMessage = "L|{}".format(self.passcode)


		while(True):
			try:
				# Wait for a message to arrive:
				messageReceived, senderAddress = \
					self.listenerSocket.recvfrom(256)
				
				""" NOTE: The message received from Slave, at this point, 
					should have one of the following forms:

					- STD from MkII:
						A|PCODE|SV:MA:CA:DD:RE:SS|N|SMISO|SMOSI|VERSION
						0     1                 2 3     4     5 6
					- STD from Bootloader:
						B|PCODE|SV:MA:CA:DD:RE:SS|

					- Error from MkII:
						A|PCODE|SV:MA:CA:DD:RE:SS|ERRMESSAGE

					- Error from Bootloader:
						B|PCODE|SV:MA:CA:DD:RE:SS|ERRMESSAGE

					Where SMISO and SMOSI are the Slave's MISO and MOSI 
					port numbers, respectively. Notice separators.
				"""
				messageSplitted = messageReceived.split("|")
					# NOTE: messageSplitted is a list of strings, each of which
					# is expected to contain a string as defined in the comment
					# above.
				
				# Verify passcode:
				if messageSplitted[1] != self.passcode:
					self.printM("Wrong passcode received (\"{}\") "\
						"from {}".format(messageSplitted[1], 
						senderAddress[0]), 'E')
					
					#print "Wrong passcode"

					continue

				# Check who's is sending the message
				if messageSplitted[0][0] == 'A':
					# This message comes from the MkII
					
					try:		
						mac = messageSplitted[2]
						
						# Check message type:
						if messageSplitted[3] == 'N':
							# Standard broadcast reply
							
							misoPort = int(messageSplitted[4])
							mosiPort = int(messageSplitted[5])
							version = messageSplitted[6]
							
							# Verify converted values:
							if (misoPort <= 0 or misoPort > 65535):
								# Raise a ValueError if a port number is invalid:
								self.printM(
									"Bad SMISO ({}). Need [1, 65535]".\
									format(miso), "E")

							if (mosiPort <= 0 or mosiPort > 65535):
								# Raise a ValueError if a port number is invalid:
								raise ValueError(
									"Bad SMOSI ({}). Need [1, 65535]".\
									format(mosi))

							if (len(mac) != 17):
								# Raise a ValueError if the given MAC address is 
								# not 17 characters long.
								raise ValueError("MAC ({}) not 17 chars".\
									format(mac))

							# Search for Slave in self.slaves 
							index = None
							for slave in self.slaves:
								if slave.getMAC() == mac:
									index = slave.getIndex()
									break

							# Check if the Slave is known:
							if index is not None :
								# Slave already recorded

								# If the index is in the Slave dictionary,
								# check its status and proceed accordingly:

								if self.slaves[index].getStatus() == \
									sv.DISCONNECTED:
									# If the Slave is DISCONNECTED but just res-
									# ponded to a broadcast, update its status 
									# for automatic reconnection. (handled by
									# their already existing Slave thread)

									# Update status and networking information:
									self.slaves[index].setStatus(
										sv.KNOWN,
										senderAddress[0],
										misoPort,
										mosiPort,
										version
									)
									
									
								else:
									# All other statuses should be ignored for 
									# now.

									pass

							else:
								# Newly met Slave

								index = len(self.slaves)
								# If the MAC address is not recorded, list it
								# AVAILABLE and move on. The user may choose 
								# to add it later.

								# NOTE: Since numpy.concatenate takes 
								# "array_like" objects, the newly instantiated 
								# Slave is passed as a member of a singleton 
								# (1 element) tuple.

								self.slaves = np.concatenate(
									(self.slaves, 
										(sv.FCSlave(
											mac = mac,
											status = sv.AVAILABLE,
											routine = self._slaveRoutine,
											routineArgs = (index, ),
											version = version,
											misoQueueSize = self.misoQueueSize,
											ip = senderAddress[0],
											misoP = misoPort,
											mosiP = mosiPort,
											index = index,
											),
										)
									)
								)
								
								# Add new Slave's information to newSlaveQueue:
								self.newSlaveQueue.put(
									((mac, 
									sv.AVAILABLE,
									self.maxFans, 
									version),))

								# Start Slave thread:
								self.slaves[index].start()
								
								"""
								self._saveTimeStamp(index, "Discovered")
								"""
					
						
						elif messageSplitted[3] == 'E':
							# Error message

							self.printM("Error message from {} (MkII): "\
								"\"{}\"".format(
									messageSplitted[2], messageSplitted[3]),'E')
						
						else:
							# Invalid code
							raise IndexError

					except IndexError:
						self.printM("Invalid message \"{}\" discarded; "\
							"sent by {}".format(
								messageReceived,senderAddress), "W")

				elif messageSplitted[0][0] == 'B':
					# This message comes from the Bootloader
					
					try:
						# Check message type:

						if messageSplitted[3] == 'N':
							# Standard broadcast
							# TODO: Handle update possibility

							self.listenerSocket.sendto(
								launchMessage,
								senderAddress)
				
						elif messageSplitted[3] == 'E':
							# Error message

							self.printM("Error message from {} "\
								"(Bootloader): \"{}\"".format(
									messageSplitted[2], 
									messageSplitted[3]),
									'E')
							
					except IndexError:
						self.printM("Invalid message \"{}\" discarded; "\
							"sent by {}".format(
								senderAddress[0], messageReceived), "W")

				else:

					# Invalid first character (discard message)
					self.printM("Warning: Message from {} w/ invalid first "\
						"character '{}' discarded".\
						format(senderAddress[0], messageSplitted[0]))

			except Exception as e: # Print uncaught exceptions
				self.printM("[LT] UNCAUGHT EXCEPTION: \"{}\"".\
					format(traceback.format_exc()), "E")	
		# End _listenerRoutine =================================================

	def _slaveRoutine(self, targetIndex, target): # # # # # # # # # # # # # # # # 
		# ABOUT: This method is meant to run on a Slave's communication-handling
		# thread. It handles sending and receiving messages through its MISO and
		# MOSI sockets, at a pace dictated by the Communicator instance's given
		# period. 
		# PARAMETERS:
		# - targetIndex: int, index of the Slave handled
		# - target: Slave controlled by this thread
		# NOTE: This version is expected to run as daemon.

		try:
			
			# Setup ============================================================

			# Get reference to Slave: ------------------------------------------
			slave = target

			# Set up sockets ---------------------------------------------------
			# MISO:
			misoS = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			misoS.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			misoS.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
			misoS.settimeout(self.periodS*2)
			misoS.bind(('', 0))

			# MOSI:
			mosiS = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			mosiS.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			mosiS.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
			mosiS.settimeout(self.periodS)
			mosiS.bind(('', 0))
			
			# Assign sockets:
			slave.setSockets(newMISOS = misoS, newMOSIS = mosiS)

			self.printM("[{:3d}] Slave thread connected: \
			 MMISO: {} MMOSI:{}".\
				format(targetIndex + 1,
					slave._misoSocket().getsockname()[1], 
					slave._mosiSocket().getsockname()[1]))

			# HSK message ------------------------------------------------------

			MHSK = "H|{},{},{},{},{}|{} {} {} {} {} {} {} {} {} {} {}".format(
						slave._misoSocket().getsockname()[1], 
						slave._mosiSocket().getsockname()[1], 
						self.periodMS,
						self.broadcastPeriodS*1000,
						self.maxTimeouts,

						self.fanMode,
						self.maxFans,
						self.fanFrequencyHZ,
						self.counterCounts,
						self.pulsesPerRotation,
						self.maxRPM,
						self.minRPM,
						self.minDC,
						self.chaserTolerance,
						self.maxFanTimeouts,
						self.pinout)
			

			# Set up placeholders and sentinels --------------------------------
			slave.resetIndices()
			periodS = self.periodS
			timeouts = 0
			totalTimeouts = 0
			message = "P"
			tryBuffer = True

			# TEMP. DEBUG:
			timestampedRPMFirst = False
			timestampedDCFirst = False
			
			# Slave loop =======================================================
			while(True):
				time.sleep(periodS)
				try:

					# Acquire lock:
					slave.acquire()	
					status = slave.getStatus()

					# Act according to Slave's state: 
					if status == sv.KNOWN: # = = = = = = = = = = = = = = = =

							
						
						# If the Slave is known, try to secure a connection:
						# print "Attempting handshake"

						# Check for signs of life w/ HSK message:
						self._send(MHSK, slave, 2, True)

						# Give time to process:
						time.sleep(periodS)

						secondChance = True
						while True:
							
							# Try to receive reply:
							reply = self._receive(slave)

							# Check reply:
							if reply is not None and reply[1] == "H":
								# print "Processed reply: {}".format(reply), "G"
								# print "Handshake confirmed"

								# Mark as CONNECTED and get to work:
								slave.setStatus(sv.CONNECTED, lock = False)
								tryBuffer = True
								break

								"""
								self._saveTimeStamp(slave.getIndex(), "Connected")
								"""

							elif reply is not None and reply[1] == "K":
								# HSK acknowledged, give Slave time
								continue
							
							elif secondChance:
								# Try again:
								self._send(MHSK, slave, 1, True)
								secondChance = False
							
							else:
								self._send("R", slave, 1)
								slave.setStatus(sv.DISCONNECTED, lock = False) 
									# NOTE: This call also resets exchange 
									# index.
								break

					elif status > 0: # = = = = = = = = = = = = = = = = = = = 
						# If the Slave's state is positive, it is online and 
						# there is a connection to maintain.

						# A positive state indicates this Slave is online and 
						# its connection need be maintained.

						#DEBUG DEACTV
						## print "[On positive state]"

						# Check queue for message:
						fetchedMessage = slave.getMOSI()

						if fetchedMessage is None:
							# Nothing to fetch. Send previous command
							
							# Send message:
							self._send(message, slave, 2)

						elif fetchedMessage[0] == MOSI_DC:
							# Duty cycle assignment. format message to be sent
							# Raw format: [MOSI_DC, DC, FAN1S,FAN2S...]

							selection = ''
							for fan in fetchedMessage[2:]:
								if fan == 1:
									selection += '1'
								else:
									selection += '0'
							
							message = "S|D:{}:{}".format(
								fetchedMessage[1]*0.01, selection)

							self._send(message, slave, 2)

						elif fetchedMessage[0] == MOSI_CHASE:
							# Chase RPM
							# Raw format: [MOSI_CHASE, RPM, FAN1S,FAN2S...]
							
							selection = ''
							for fan in fetchedMessage[2]:
								if fan == 1:
									selection += '1'
								else:
									selection += '0'
							
							message = "S|C:{}:{}".format(
								fetchedMessage[1], selection)

							self._send(message, slave, 2)

						elif fetchedMessage[0] == MOSI_DISCONNECT:
							self.sendToListener("X", slave, 2)

						elif fetchedMessage[0] == MOSI_REBOOT:
							self._sendToListener("R", slave, 2)
						
						"""
						if not timestampedDCFirst:
							self._saveTimeStamp(slave.getIndex(),
							"First command out")
						
							timestampedDCFirst = True
						"""	
						# DEBUG: 
						# print "Sent: {}".format(message)

						# Get reply:
						reply = self._receive(slave)

						# Check reply: -----------------------------------------
						if reply is not None:
							# print "Processed reply: {}".format(reply)

							# Restore timeout counter after success:
							timeouts = 0
						
							# Check message type:
							if reply[1] == 'T':
								# Standard update

								# Get data index:
								receivedDataIndex = int(reply[2])
							
								# Check for redundant data:
								if receivedDataIndex > slave.getDataIndex():
									# If this data index is greater than the
									# currently stored one, this data is new and
									# should be updated:

									# Update data index:
									slave.setDataIndex(receivedDataIndex)

									# Update RPMs and DCs:
									try:
										# Set up data placeholder as a tuple:
										
										slave.setMISO(
											[slave.getStatus()] +
											map(int,reply[-2].split(','))+
											map(float,reply[-1].split(',')),
											False)
											# FORM: (RPMs, DCs)
										"""		
										if not timestampedRPMFirst:
											for rpm in reply[-2].split(','):
												if int(rpm) != 0:

													self._saveTimeStamp(
														slave.getIndex(),
														"First nonzero RPM confirmed")
													timestampedRPMFirst = True
										"""	
									except Queue.Full:
									
										# If there is no room for this message,
										# drop the packet and alert the user:
										slave.incrementDropIndex()
										

							elif reply[1] == 'I':
								# Reset MISO index
								
								slave.setMISOIndex(0)
								self.printM("[{}] MISO Index reset".format(
									slave.getMAC))

							elif reply[1] == 'P':
								# Ping request
								
								self._send("P", slave)

							elif reply[1] == 'Y':
								# Reconnect reply

								pass
						
							elif reply[1] == 'M':
								# Maintain connection. Pass
								pass

							elif reply[1] == 'H':
								# Old HSK message. Pass
								pass

							elif reply[1] == 'E':
								# Error report

								self.printM("[{}] ERROR: \"{}\"".format(
									slave.getMAC(), reply[2]), "E")

							elif reply[1] == 'Q':
								# Ping reply. Pass
								pass

							else:
								# Unrecognized command

								self.printM("[{}] Warning, unrecognized "\
									"message: \"{}\"".format(
										slave.getMAC(), reply), "W")

						else:
							timeouts += 1
							totalTimeouts += 1
							
							"""
							if message is not None:
								# If a message was sent and no reply was 
								# received, resend it:
								# print "Timed out. Resending"
								# Resend message:
								self._send(message, slave, 1)
								# Increment timeout counter:

							"""

							# Check timeout counter: - - - - - - - - - - - - - -
							if timeouts == self.maxTimeouts -1:
								# If this Slave is about to time out, send a
								# ping request

								self._send("Q", slave, 2)
							
							elif timeouts < self.maxTimeouts:
								# If there have not been enough timeouts to con-
								# sider the connection compromised, continue.
								# print "Reply missed ({}/{})".
								#   format(timeouts, 
								#       self.maxTimeouts)

								# Restart loop:
								pass

							elif tryBuffer:
								self._send("Y", slave, 2)
								tryBuffer = False

							else:
								self.printM("[{}] Slave timed out".\
									format(targetIndex + 1), "W")

								# Terminate connection: ........................

								# Send termination message:
								self._sendToListener("X", slave)

								# Reset timeout counter:
								timeouts = 0
								totalTimeouts = 0

								# Update Slave status:
								slave.setStatus(
									sv.DISCONNECTED, lock = False)

								# Restart loop:
								pass

								# End check timeout counter - - - - - - - - - - 

							# End check reply ---------------------------------

					else: # = = = = = = = = = = = = = = = = = = = = = = = = = = 
						
						# If this Slave is neither online nor waiting to be 
						# contacted, wait for its state to change.

						command = "P"
						message = "P"

						# Check if the Slave is mistakenly connected:
						reply = self._receive(slave)

						if reply is not None:
							# Slave stuck! Send reconnect message:
							if slave.getIP() is not None and \
								slave.getMOSIPort() is not None:
								self._send("Y", slave)

								reply = self._receive(slave)
								
								if reply is not None and reply[1] == "Y":
									# Slave reconnected!
									slave.setStatus(sv.CONNECTED)
							
							else:
								self._sendToListener("X", slave)

				except Exception as e: # Print uncaught exceptions
					self.printM("[{}] UNCAUGHT EXCEPTION: \"{}\"".
					   format(targetIndex + 1, traceback.format_exc()), "E")

				finally:
					# DEBUG DEACTV
					## print "Slave lock released", "D"
					# Guarantee release of Slave-specific lock:

					try:
						slave.lock.release()
					except thread.error:
						pass

				# End Slave loop (while(True)) =================================


		except Exception as e: # Print uncaught exceptions
			self.printM("[{}] UNCAUGHT EXCEPTION: \"{}\"".
			   format(targetIndex + 1, traceback.format_exc()), "E")
		
		self.printM("[{}] WARNING: BROKE OUT OF SLAVE LOOP".
			format(targetIndex + 1), "E")
		# End _slaveRoutine  # # # # # # # # # # # #  # # # # # # # # # # # # # 

	# # AUXILIARY METHODS # # # # # # # # # # # # # # # # # # # # # # # # # # #
		# ABOUT: These methods are to be used within this class. For methods to
		# be accessed by the user of a Communicator instance, see INTERFACE ME-
		# THODS below.

	def _send(self, message, slave, repeat = 1, hsk = False): # # # # # # # # # 
		# ABOUT: Send message to a KNOWN or CONNECTED sv. Automatically add
		# index.
		# PARAMETERS:
		# - message: str, message to send (w/o "INDEX|")
		# - slave: Slave to contact (must be KNOWN or CONNECTED or behavior is
		#   undefined)
		# - repeat: How many times to send message.
		# - hsk: Bool, whether this message is a handshake message.
		# - broadcast: Bool, whether to send this message as a broad
		# WARNING: THIS METHOD ASSUMES THE SLAVE'S LOCK IS HELD BY ITS CALLER.

		if not hsk:
			# Increment exchange index:
			slave.incrementMOSIIndex()
		else:
			# Set index to zero:
			slave.setMOSIIndex(0)

		# Prepare message:
		outgoing = "{}|{}".format(slave.getMOSIIndex(), message)

		# Send message:
		for i in range(repeat):
			slave._mosiSocket().sendto(outgoing,
				(slave.ip, slave.getMOSIPort()))

		# Notify user:
		# print "Sent \"{}\" to {} {} time(s)".
		#   format(outgoing, (slave.ip, slave.mosiP), repeat))

		# End _send # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

	def _sendToListener(self, message, slave, repeat = 1, targetted = True): # #
		# ABOUT: Send a message to a given Slave's listener socket.


		if targetted and slave.ip is not None:
			# Send to listener socket:
			# Prepare message:
			outgoing = "{}|{}".format(message, self.passcode)
			for i in range(repeat):
				slave._mosiSocket().sendto(outgoing, 
				(slave.ip, self.broadcastPort))	
		else:
			# Send through broadcast:
			# Prepare message:
			outgoing = "J|{}|{}|{}".format(
				self.passcode, slave.getMAC(), message)
			for i in range(repeat):
				slave._mosiSocket().sendto(outgoing, 
				("<broadcast>", self.broadcastPort))	

		# End _sendToListener # # # # # # # # # # # # # # # # # # # # # # # # # #

	def _receive(self, slave): # # # # # # # # # # # # # # # # # # # # # # # # # 
		# ABOUT: Receive a message on the given Slave's sockets (assumed to be
		# CONNECTED, BUSY or KNOWN.
		# PARAMETERS:
		# - slave: Slave unit for which to listen.
		# RETURNS:
		# - three-tuple: 
		#       (exchange index (int), keyword (str), command (str) or None)
		#   or None upon failure (socket timeout or invalid message)
		# RAISES: 
		# - What exceptions may arise from passing an invalid argument.
		# WARNING: THIS METHOD ASSUMES THE SLAVE'S LOCK IS HELD BY ITS CALLER.

		try:
			# Keep searching for messages until a message with a matching index
			# is found or the socket times out (no more messages to retrieve)
			index = -1
			indexMatch = False
			count = 0
			while(True): # Receive loop = = = = = = = = = = = = = = = = = = = = 

				# Increment counter: -------------------------------------------
				count += 1
				# DEBUG DEACTV
				## print "Receiving...({})".format(count), "D"

				# Receive message: ---------------------------------------------
				message, sender = slave._misoSocket().recvfrom(
					self.maxLength)

				# DEBUG DEACTV
				"""
				print "Received: \"{}\" from {}".\
				 	format(message, sender)
				"""

				try:
					# Split message: -------------------------------------------
					splitted = message.split("|")

					# Verify index:
					index = int(splitted[0])

					if index <= slave.getMISOIndex():
						# Bad index. Discard message:
						# print "Bad index: ({})".
						#   format(index), "D"

						# Discard message:
						continue

					# Check for possible third element:
					# DEBUG PRINT:
					#print \
					#    "Got {} part(s) from split: {}".\
					#        format(len(splitted), str(splitted)), "D"

					output = None

					if len(splitted) == 2:
						output = (index, splitted[1])
						
					elif len(splitted) == 3:
						output = (index, splitted[1], splitted[2])

					elif len(splitted) == 4:
						output = (index, splitted[1], splitted[2], splitted[3])
					
					elif len(splitted) == 5:
						output = (index, splitted[1], int(splitted[2]), splitted[3], 
							splitted[4])
						
					else:
						# print
						#"ERROR: Unrecognized split amount ({}) on: {}".\
						#format(len(splitted), str(splitted)), "E")
						return None
						
					# Update MISO index:
					slave.setMISOIndex(index)

					# Return splitted message: ---------------------------------
					# DEBUG DEACTV
					## print "Returning {}".format(output), "D"
					return output

				except (ValueError, IndexError, TypeError) as e:
					# Handle potential Exceptions from format mismatches:

					# print "Bad message: \"{}\"".
					#       format(e), "W")

					if not indexMatch:
						# If the correct index has not yet been found, keep lo-
						# oking:

						# DEBUG DEACTV
						## print "Retrying receive", "D"

						continue;
					else:
						# If the matching message is broken, exit w/ error code
						# (None)
						# print
						#   "WARNING: Broken message with matching index: " +\
						#   "\n\t Raw: \"{}\"" +\
						#   "\n\t Splitted: {}" +\
						#   "\n\t Error: \"{}\"".\
						#   format(message, splitted, e), "E")

						return None

				# End receive loop = = = = = = = = = = = = = = = = = = = = = = =

		# Handle exceptions: ---------------------------------------------------
		except socket.timeout: 
			# print "Timed out.", "D"
			return None

		# End _receive # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	
	def getNewSlaves(self): # ==================================================
		# Get new Slaves, if any. Will return either a tuple of MAC addresses
		# or None.

		try:
			return self.newSlaveQueue.get_nowait()

		except Queue.Empty:
			return None

		# End getNewSlaves =====================================================

	def printM(self, output, tag = 'S'): # =====================================
		# ABOUT: Print on corresponding GUI terminal screen by adding a message 
		# to this Communicator's corresponding output Queue.
		# PARAMETERS:
		# - output: str, string to be printed.
		# - tag: str, single character for string formatting.
		# RETURNS: bool, whether the placement of the message was successful.
		# The given message will be added to the corresponding output Queue or
		# will block until it is possible.

		# Place item in corresponding output Queue:
		if DEBUG:
			print "[DEBUG][COMMS] " + output

		try:
			self.printQueue.put_nowait((output, tag))
			return True

		except Queue.Full:
			print "[WARNING] Communications output queue full. "\
				"Could not print the following message:\n\r \"{}\"".\
				format(output)
			return False
		# End printM ===========================================================

	# # INTERFACE METHODS # # # # # # # # # # # # # # # # # # # # # # # # # 
	
	def add(self, targetIndex): # ==============================================
		# ABOUT: Mark a Slave on the network for connection. The given Slave 
		# must be already listed and marked AVAILABLE. This method will mark it 
		# as KNOWN, and its corresponding handler thread will connect automati-
		# cally.
		# PARAMETERS:
		# - targetIndex: int, index of Slave to "add."
		# RAISES:
		# - Exception if targeted Slave is not AVAILABLE.
		# - KeyError if targetIndex is not listed.

		# Check status:
		status = self.slaves[targetIndex].getStatus()

		if status == sv.AVAILABLE:
			self.slaves[targetIndex].setStatus(sv.KNOWN)
			"""
			self._saveTimeStamp(targetIndex, "Connecting")
			"""
		else:
			raise Exception("Targeted Slave [{}] is not AVAILABLE but {}".\
				format(targetIndex + 1, sv.translate(status)))

		# End add ==============================================================

	def setBroadcastSwitch(self, newState): # ==================================
		""" ABOUT: Set whether to send UDP broadcast. Parameter Switch is
			expected to be True or False. Otherwise, a ValueError is raised.
		"""

		# Validate argument:
		if (type(newState) == bool):
			# If input is valid, modify broadcast switch:
			self.broadcastSwitchLock.acquire()
			try:

				self.broadcastSwitch = newState

			finally:

				# Lock will always be released:
				self.broadcastSwitchLock.release()

			if newState:
				self.printB("Broadcast activated", "G")
			else:
				self.printB("Broadcast deactivated")

		else:
			# Raise exception upon invalid input:
			raise ValueError("setBroadcastSwitch expects bool, not {}".\
				format(type(newState)))

		# End setBroadcastSwitch() =========================================

	def getBroadcastSwitch(self): # ============================================
		""" ABOUT: Get the current value of broadcastSwitch.
		"""
		return self.broadcastSwitch

		# End getBroadcastSwitch() =============================================

	def isBroadcastThreadAlive(self): # ========================================
		# ABOUT: Check whether the broadcast thread is alive.
		# RETURNS:
		# - bool: whether the broadcast thread is alive.
		
		try:
			return self.broadcastThread.isAlive()

		except AttributeError:
			# If the broadcastThread does not yet exist as an attribute...
			return False

		# End isBroadcastThreadAlive ===========================================

	def isListenerThreadAlive(self): # =========================================
		# ABOUT: Check whether the listener thread is alive.
		# RETURNS:
		# - bool: whether the listener thread is alive.
		
		try:
			return self.listenerThread.isAlive()

		except AttributeError:
			# if the listenerThread does not yet exist as an attribute...
			return False

		# End isListenerThreadAlive ============================================
	
	def sendReboot(self): # ====================================================
		# ABOUT: Use broadcast socket to send a general "disconnect" message
		# that terminates any existing connection.

		try:
			#self.broadcastLock.acquire()
			self.rebootSocket.sendto(
				"R|{}".format(self.passcode),
				("<broadcast>", self.broadcastPort))

		except Exception as e:
			self.printM("[sD] UNCAUGHT EXCEPTION: \"{}\"".
			   format(traceback.format_exc()), "E")

		#finally:
			#self.broadcastLock.release()

		# End sendReboot =======================================================

	def sendDisconnect(self): # ================================================
		# ABOUT: Use disconenct socket to send a general "disconnect" message
		# that terminates any existing connection.

		try:
			#self.broadcastLock.acquire()
			self.disconnectSocket.sendto(
				"X|{}".format(self.passcode),
				("<broadcast>", self.broadcastPort))

		except Exception as e:
			self.printM("[sD] UNCAUGHT EXCEPTION: \"{}\"".
			   format(traceback.format_exc()), "E")

		# End sendDisconnect ===================================================
	
	def stop(self): # ==========================================================
		# Cleanup routine for termination.

		# Send disconnect signal:
		self.sendDisconnect()

		# NOTE: All threads are set as Daemon and all sockets as reusable.
		return

		# End shutdown =========================================================


	"""
	def _saveTimeStamp(self, index, message):
		# ABOUT: Provisional method to save timestamps for testing.

		self.file.write("{},{},{}\n".format(
			index,
			time.strftime("%H:%M:%S"), 
			message))
	"""

## MODULE'S TEST SUITE #########################################################

if __name__ == "__main__":

	print "FANCLUB MARK II COMMUNICATOR MODULE TEST SUITE INITIATED."
	print "VERSION = " + VERSION


	print "NO TEST SUITE IMPLEMENTED IN THIS VERSION. TERMINATING."
