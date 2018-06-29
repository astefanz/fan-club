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
import threading	# Multitasking
import thread		# thread.error

# System:
import sys			# Exception handling
import traceback	# More exception handling
import random		# Random names, boy
import resource		# Socket limit

# Data:
import time			# Timing
import Queue
import numpy as np	# Fast arrays and matrices

# FCMkII:
import FCInterface
import FCSlave as sv
import FCPrinter
from auxiliary import names

## CONSTANT DEFINITIONS ########################################################

DEBUG = False
VERSION = "Independent 0"
FORCE_IP_ADDRESS = ""
	#= "192.168.1.129" # (Basement lab)

## CLASS DEFINITION ############################################################

class FCCommunicator:

	def __init__(self,
			# Network:
			savedSlaves, mainQueueSize, broadcastPeriodS, periodMS, periodS,
			broadcastPort, passcode, misoQueueSize, maxTimeouts, maxLength,
			# Fan array:
			defaultModuleDimensions, defaultModuleAssignment,
			maxFans, fanMode, targetRelation, fanFrequencyHZ, counterCounts, 
			pulsesPerRotation,
			maxRPM, minRPM, minDC, chaserTolerance, maxFanTimeouts, pinout
		): # ===================================================================
		# ABOUT: Constructor for class Communicator.

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

			# Network:
			self.mainQueueSize = mainQueueSize
			self.broadcastPeriodS = broadcastPeriodS
			self.periodMS = periodMS
			self.periodS = periodS
			self.broadcastPort = broadcastPort
			self.passcode = passcode
			self.misoQueueSize = misoQueueSize
			self.maxTimeouts = maxTimeouts
			self.maxLength = maxLength

			# Fan array:
			self.defaultModuleDimensions = defaultModuleDimensions
			self.defaultModuleAssignment = defaultModuleAssignment
			self.maxFans = maxFans
			self.fanMode = fanMode
			self.targetRelation = targetRelation
			self.fanFrequencyHZ = fanFrequencyHZ
			self.counterCounts = counterCounts
			self.pulsesPerRotation = pulsesPerRotation
			self.maxRPM = maxRPM
			self.minRPM = minRPM
			self.minDC = minDC
			self.chaserTolerance = chaserTolerance
			self.maxFanTimeouts = maxFanTimeouts
			self.pinout = pinout

			# Output queues:
			self.mainQueue = Queue.Queue(mainQueueSize)
			self.newSlaveQueue = Queue.Queue()

			# Initialize Slave-list-related data:
			self.slavesLock = threading.Lock()

			# Create a temporary socket to obtain Master's IP address:
			temp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			temp.connect(('192.0.0.8', 1027))
			self.hostIP = temp.getsockname()[0]
			temp.close()
			
			self.printM("\tHost IP: {}".format(self.hostIP))
			
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

			# Reset any existing phantom connections:
			self._sendDisconnect()

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

			# SET UP LIST OF KNOWN SLAVES  =====================================
			# NOTE: This list will be a Numpy array of Slave objects.

			# Create a numpy array for storage:
			self.slaves = np.empty(len(savedSlaves), object)
				# Create an empty numpy array of objects w/ space for as many
				# Slave units as there are in savedSlaves
			# Loop over savedSlaves to instantiate any saved Slaves:
			print "Initializing Sv's"
			for index in range(len(savedSlaves)):

				# NOTE: Here each sub list, if any, contains data to initialize
				# known Slaves, in the following order:
				#
				# [0]: Name (as a string)
				# [1]: MAC address (as a string)
				# [2]: Number of active fans (as an integer)
			

				self.slaves[index] = \
					sv.FCSlave(
					name = savedSlaves[index][0],
					mac = savedSlaves[index][1],
					status = sv.DISCONNECTED,
					maxFans = self.maxFans,
					activeFans = savedSlaves[index][2],
					routine = self._slaveRoutine,
					routineArgs = (index,),
					misoQueueSize = misoQueueSize,
					index = index,
					pinout = self.pinout,
					coordinates = savedSlaves[index][3],
					moduleDimensions = savedSlaves[index][4],
					moduleAssignment = savedSlaves[index][5]
					)

				# Start Slave thread:
				self.slaves[index].start()

				# Add Slave to newSlaveQueue:
				self.putNewSlave(index)
		
			# START MASTER THREADS =============================================
			self.listenerThread.start()
			self.broadcastThread.start()
			
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

	def _broadcastRoutine(self, broadcastMessage, broadcastPeriod): # ==========
		""" ABOUT: This method is meant to run inside a Communicator instance's
			broadcastThread. 
		"""
		try: # Catch any exception for printing (have no stdout w/ GUI!)

			broadcastSocketPortCopy = self.broadcastSocketPort # Thread safety

			self.printM("[BT] Broadcast thread started w/ period of {} "\
				"second(s)"\
				.format(broadcastPeriod), "G")

			count = 0

			while(True):

				# Increment counter:
				count += 1

				# Wait designated period:
				time.sleep(broadcastPeriod)

				self.broadcastLock.acquire()
				self.broadcastSwitchLock.acquire()
				try:
					# Send broadcast only if self.broadcastSwitch is True:
					if self.broadcastSwitch:
						# Broadcast message:
						for i in (1,2):
							self.broadcastSocket.sendto(broadcastMessage, 
								("<broadcast>", 65000))


				finally:
					# Guarantee lock release:
					self.broadcastSwitchLock.release()
					self.broadcastLock.release()
			
		except Exception as e:
			self.printM("[BT] UNHANDLED EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")


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
				
				""" DEBUG
				print "Message recevied: {}".format(messageReceived)
				"""

				""" NOTE: The message received from Slave, at this point, 
					should have one of the following forms:

					- STD from MkII:
						A|PCODE|SV:MA:CA:DD:RE:SS|SMISO|SMOSI|VERSION
						0     1                 2     3     4       5
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
					
					print "Wrong passcode"

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
											name = random.choice(names.coolNames),
											mac = mac,
											status = sv.AVAILABLE,
											maxFans = self.maxFans,
											activeFans = self.maxFans,
											routine = self._slaveRoutine,
											routineArgs = (index, ),
											pinout = self.pinout,
											version = version,
											misoQueueSize = self.misoQueueSize,
											ip = senderAddress[0],
											misoP = misoPort,
											mosiP = mosiPort,
											index = index,
											coordinates = None,
											moduleDimensions = 
												self.defaultModuleDimensions,
											moduleAssignment = 
												self.defaultModuleAssignment
											),
										)
									)
								)

								# Start Slave thread:
								self.slaves[index].start()
								
								"""
								self._saveTimeStamp(index, "Discovered")
								"""
					
								# Add new Slave's information to newSlaveQueue:
								self.putNewSlave(index)

						
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
								senderAddress[0], messageReceived), "W")

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
			self.printM("[{}] Slave thread started".\
				format(targetIndex + 1, "G"))

			# Get reference to Slave: ------------------------------------------
			slave = target

			# Set up sockets ---------------------------------------------------
			# MISO:
			misoS = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			misoS.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			misoS.settimeout(self.periodS*2)
			misoS.bind(('', 0))

			# MOSI:
			mosiS = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			mosiS.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			mosiS.settimeout(self.periodS)
			mosiS.bind(('', 0))
			
			# Assign sockets:
			slave.setSockets(newMISOS = misoS, newMOSIS = mosiS)

			self.printM("[{}] Sockets set up successfully: \
			 \n\t\tMMISO: {}\n\t\tMMOSI:{}".\
				format(targetIndex + 1,
					slave._misoSocket().getsockname(), 
					slave._mosiSocket().getsockname()))

			# HSK message ------------------------------------------------------

			MHSK = "H|{},{},{},{},{}|{} {} {} {} {} {} {} {} {} {} {}".format(
						slave._misoSocket().getsockname()[1], 
						slave._mosiSocket().getsockname()[1], 
						self.periodMS,
						self.broadcastPeriodS*1000,
						self.maxTimeouts,

						self.fanMode,
						self.slaves[targetIndex].activeFans,
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
			message = None

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
						self._send(MHSK, slave, 1, True)

						# Give time to process:
						time.sleep(periodS)

						# Try to receive reply:
						reply = self._receive(slave)
						# Check reply:
						if reply is not None and reply[1] == "H":
							# print "Processed reply: {}".format(reply), "G"
							# print "Handshake confirmed"

							# Mark as CONNECTED and get to work:
							slave.setStatus(sv.CONNECTED, lock = False)
							
							"""
							self._saveTimeStamp(slave.getIndex(), "Connected")
							"""

						else:
							self._send("X", slave, 1)
							slave.setStatus(sv.DISCONNECTED, lock = False) 
								# NOTE: This call also resets exchange 
								# index.
							

					elif slave.getStatus() > 0: # = = = = = = = = = = = = = = = 
						# If the Slave's state is positive, it is online and 
						# there is a connection to maintain.

						# A positive state indicates this Slave is online and 
						# its connection need be maintained.

						#DEBUG DEACTV
						## print "[On positive state]"

						# Check queue for message:
						
						command = slave.getMOSI()
							
						if command is not None:
							# Classify command:
							if command == "X":
								# Disconnect message. Terminate connection.
								message = "X"
							
							else: 
								# Standard command
								message = "S|" + command

							# Send message, if any:
							self._send(message, slave, 2)
						
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
										
										slave.update(
											sv.VALUE_UPDATE,
											(
												np.array(
													map(int,reply[-2].split(',')))
												,
												np.array(
													map(float,reply[-1].split(',')))
											),
											totalTimeouts)
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
								
								self.send("P", slave)
						
							elif reply[1] == 'M':
								# Maintain connection. Pass
								pass

							elif reply[1] == 'E':
								# Error report

								self.printM("[{}] ERROR: \"{}\"".format(
									slave.getMAC(), reply[2]), "E")

							else:
								# Unrecognized command

								self.printM("[{}] Warning, unrecognized "\
									"message: \"{}\"".format(
										slave.getMAC(), reply))

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
							if timeouts < self.maxTimeouts:
								# If there have not been enough timeouts to con-
								# sider the connection compromised, continue.
								# print "Reply missed ({}/{})".
								#   format(timeouts, 
								#       self.maxTimeouts)

								# Restart loop:
								pass

							else:
								self.printM("[{}] Slave timed out".\
									format(targetIndex + 1), "W")

								# Terminate connection: ........................

								# Send termination message:
								self._send("X", slave)

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

						command = "Blank"
						
					
						pass
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

	def _send(self, message, slave ,repeat = 1, hsk = False): # # # # # # # # # 
		# ABOUT: Send message to a KNOWN or CONNECTED sv. Automatically add
		# index.
		# PARAMETERS:
		# - message: str, message to send (w/o "INDEX|")
		# - slave: Slave to contact (must be KNOWN or CONNECTED or behavior is
		#   undefined)
		# - repeat: How many times to send message.
		# - hsk: Bool, whether this message is a handshake message.
		# WARNING: THIS METHOD ASSUMES THE SLAVE'S LOCK IS HELD BY ITS CALLER.

		if not hsk:
			# Increment exchange index:
			slave.incrementMOSIIndex()
		else:
			# Set index to zero:
			slave.setMOSIIndex(0)

		# Send message:
		for i in range(repeat):
			outgoing = "{}|{}".format(
			slave.getMOSIIndex(), message)
			slave._mosiSocket().sendto(outgoing,
				(slave.ip, slave.getMOSIPort()))

		# Notify user:
		# print "Sent \"{}\" to {} {} time(s)".
		#   format(outgoing, (slave.ip, slave.mosiP), repeat))

		# End _send # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

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
	
	def putNewSlave(self, index): # ============================================
		# ABOUT: Add relevant information of a new Slave to the newSlaveQueue,
		# for the interface module to access.
		# RAISES:
		#	- KeyError if the given MAC address is not found.
		
		# Get target Slave:
		target = self.slaves[index]

		# Add Slave to Queue:
		self.newSlaveQueue.put_nowait((
			target.getName(),
			target.getMAC(),
			target.getStatus(),
			target.getMaxFans(),
			target.getActiveFans(),
			target.getIP(),
			target.getUpdate, # NOTE: Here the method itself is passed.
			target.setMOSI,
			index,
			target.getCoordinates(),
			target.getModuleDimensions(),
			target.getModuleAssignment(),
			target.getVersion()
			))

		# Done
		return

		# End putNewSlave ======================================================

	def getNewSlave(self): # ===================================================
		# ABOUT: Check if there is at least one "new Slave" in the newSlaveQueue
		# and retrieve and return its value. The data, if any, will be formatted
		# as a tuple of the following form:
		# 
		# (Name, MAC_Address, Status, Max_Fans, Active_Fans, 
		#	IP, getUpdate, setMOSI)
		#
		# If the newSlaveQueue is empty, return None.

		try:
			return self.newSlaveQueue.get_nowait()

		except Queue.Empty:
			return None

		# End getNewSlave ======================================================

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
			self.mainQueue.put_nowait((output, tag))
			return True

		except Queue.Full:
			print "[ERROR][COMMS] Warning. Communications output queue full. "\
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

	def _sendDisconnect(self):
		# ABOUT: Use broadcast socket to send a general "disconnect" message
		# that terminates any existing connection.

		try:
			self.broadcastLock.acquire()
			self.broadcastSocket.sendto(
				"X|{}".format(self.passcode),
				("<broadcast>", 65000))

		except Exception as e:
			self.printM("[sD] UNCAUGHT EXCEPTION: \"{}\"".
			   format(traceback.format_exc()), "E")

		finally:
			self.broadcastLock.release()

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
