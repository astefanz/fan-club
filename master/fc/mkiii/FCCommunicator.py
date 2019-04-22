################################################################################
##----------------------------------------------------------------------------##
## CALIFORNIA INSTITUTE OF TECHNOLOGY ## GRADUATE AEROSPACE LABORATORY ##     ##
## CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES                      ##     ##
##----------------------------------------------------------------------------##
##      ____      __      __  __      _____      __      __    __    ____     ##
##     / __/|   _/ /|    / / / /|  _- __ __\    / /|    / /|  / /|  / _  \    ##
##    / /_ |/  / /  /|  /  // /|/ / /|__| _|   / /|    / /|  / /|/ /   --||   ##
##   / __/|/ _/    /|/ /   / /|/ / /|    __   / /|    / /|  / /|/ / _  \|/    ##
##  / /|_|/ /  /  /|/ / // //|/ / /|__- / /  / /___  / -|_ - /|/ /     /|     ##
## /_/|/   /_/ /_/|/ /_/ /_/|/ |\ ___--|_|  /_____/| |-___-_|/  /____-/|/     ##
## |_|/    |_|/|_|/  |_|/|_|/   \|___|-    |_____|/   |___|     |____|/       ##
##                   _ _    _    ___   _  _      __  __   __                  ##
##                  | | |  | |  | T_| | || |    |  ||_ | | _|                 ##
##                  | _ |  |T|  |  |  |  _|      ||   \\_//                   ##
##                  || || |_ _| |_|_| |_| _|    |__|  |___|                   ##
##                                                                            ##
##----------------------------------------------------------------------------##
## Alejandro A. Stefan Zavala ## <astefanz@berkeley.edu>   ##                 ##
## Chris J. Dougherty         ## <cdougher@caltech.edu>    ##                 ##
## Marcel Veismann            ## <mveisman@caltech.edu>    ##                 ##
################################################################################

""" ABOUT ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 + Fan Club networking back-end -- provisional version adapted from MkIII.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## DEPENDENCIES ################################################################

# Network:
import socket		# Networking
import http.server	# For bootloader
import socketserver	# For bootloader

# System:
import sys			# Exception handling
import traceback	# More exception handling
import threading	# Multitasking
import _thread		# thread.error
import multiprocessing # The big guns

import platform # Check OS and Python version
IN_WINDOWS = platform.system() == 'Windows'
if not IN_WINDOWS:
	import resource		# Socket limit

# Data:
import time			# Timing
import queue
import numpy as np	# Fast arrays and matrices

# FCMkIII:
from . import FCSlave as sv
from . import FCWidget as wg
from . import hardcoded as hc

# FCMkIV:
from .. import archive as ac

## CONSTANT DEFINITIONS ########################################################

DEBUG = False
VERSION = "Independent 0"
FORCE_IP_ADDRESS = "0.0.0.0"
	#"0.0.0.0"
	#= "192.168.1.129" # (Basement lab)
FORCE_BROADCAST_IP = "<broadcast>"


# Communicator status codes:
CONNECTED = 31
CONNECTING = 32
DISCONNECTED = 33
DISCONNECTING = 34


# Slave data tuple indices:
# Expected form: (INDEX, MAC, STATUS, FANS, VERSION) + IID
#					0		1	2		3		4		5
INDEX = 0
MAC = 1
STATUS = 2
FANS = 3
VERSION = 4
IID = 5

# Commands: ------------------------------------

ADD = 51
DISCONNECT = 52
REBOOT = 53

# NOTE: Array command e.g.:
#		(COMMUNICATOR, SET_DC, DC, FANS, ALL)
#		(COMMUNICATOR, SET_DC, DC, FANS, 1,2,3,4)
#		(COMMUNICATOR, SET_DC_MANY, DC, SELECTIONS)
#							|
#					(INDEX, FANS)

SET_DC = 54
SET_DC_GROUP = 55
SET_DC_MULTI = 56
SET_RPM = 57

# Bootloader commands:

BOOTLOADER_START = 66
BOOTLOADER_STOP = 67

# End commands -----------------------------------

# Special values:
NONE = -1
ALL = -2

FCPRCONSTS = (ADD, DISCONNECT, REBOOT)

# Outputs:
NEW = 11
UPDATE = 12

# MOSI commands:
MOSI_NO_COMMAND = 20
MOSI_DC = 21
MOSI_DC_ALL = 22
MOSI_RPM = 23
MOSI_RPM_ALL = 24
MOSI_DISCONNECT = 25
MOSI_REBOOT = 26
MOSI_DC_MULTI = 27

# Change codes:
NO_CHANGE = 0
CHANGE = 1

# MISO Matrix special columns:
MISO_COLUMN_STATUS = 0
MISO_COLUMN_TYPE = 1
MISO_SPECIALCOLUMNS = 2

## CLASS DEFINITION ############################################################

# TODO:
# - change profile usage (DONE)
# - change command queue for pipe
# - change pipes
# - change output formatting
# - change input parsing
# - change printing

class FCCommunicator:

	def __init__(self,
			profile,
			# Multiprocessing:
			commandQueue,
			mosiMatrixQueue,
			printQueue,
			updatePipeOut,
			networkPipeSend,
			newMISOMatrixPipeIn
		): # ===================================================================
		# ABOUT: Constructor for class FCPRCommunicator.

		try:


			# INITIALIZE DATA MEMBERS ==========================================

			# Store parameters -------------------------------------------------

			self.profile = profile

			# Network:
			self.broadcastPeriodS = profile[ac.broadcastPeriodMS]*1000
			self.periodMS = profile[ac.periodMS]
			self.periodS = self.periodMS*1000
			self.broadcastPort = profile[ac.broadcastPort]
			self.passcode = profile[ac.passcode]
			self.misoQueueSize = profile[ac.misoQueueSize]
			self.maxTimeouts = profile[ac.maxTimeouts]
			self.maxLength = profile[ac.maxLength]
			self.flashFlag = False
			self.targetVersion = None
			self.flashMessage = None

			# Fan array:
            dsv = profile[ac.defaultSlave]

			self.maxFans = profile[ac.maxFans]
			self.fanMode = profile[ac.defaultSlave][ac.SV_fanMode]
			self.targetRelation = dsv[ac.SV_targetRelation]
			self.fanFrequencyHZ = dsv[ac.SV_fanFrequencyHZ]
			self.counterCounts = dsv[ac.SV_counterCounts]
			self.pulsesPerRotation = dsv[ac.SV_pulsesPerRotation]
			self.maxRPM = dsv[ac.SV_maxRPM]
			self.minRPM = dsv[ac.SV_minRPM]
			self.minDC = dsv[ac.SV_minDC]
			self.chaserTolerance = dsv[ac.SV_chaserTolerance]
			self.maxFanTimeouts = hc.DEF_MAX_FAN_TIMEOUTS
			self.pinout = profile[ac.pinouts][dsv[ac.SV_pinout]]

			self.fullSelection = ''
			for fan in range(self.maxFans):
				self.fullSelection += '1'

			# Multiprocessing and printing:
			self.commandQueue = commandQueue
			self.newMISOMatrixPipeIn = newMISOMatrixPipeIn
			self.updatePipeOut = updatePipeOut
			self.networkPipeSend = networkPipeSend
			self.mosiMatrixQueue = mosiMatrixQueue
			self.stoppedFlag = False

			# Output queues:
			self.printQueue = printQueue
			self.symbol = "[CM] "
			self.newSlaveQueue = queue.Queue()
			self.slaveUpdateQueue = queue.Queue()

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
			self.printM("\tDetected platform: {}".format(platform.system()))

			if not IN_WINDOWS:

				self.printM(
					"\tNOTE: Increasing socket limit w/ \"resource\"",'W')

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

			# SET UP FLASHING HTTP SERVER --------------------------------------
			self.flashHTTPHandler = http.server.SimpleHTTPRequestHandler
			if not IN_WINDOWS:
				TCPServerType = socketserver.ForkingTCPServer
			else:
				TCPServerType = socketserver.ThreadingTCPServer
			self.httpd = TCPServerType(
				("", 0),
				self.flashHTTPHandler
			)

			self.httpd.socket.setsockopt(
				socket.SOL_SOCKET,
				socket.SO_REUSEADDR,
				1
			)
			self.httpd.timeout = 5

			self.flashServerThread = threading.Thread(
				target = self.httpd.serve_forever
			)
			self.flashServerThread.setDaemon(True)
			self.flashServerThread.start()
			self.httpPort = self.httpd.socket.getsockname()[1]
			self.printM("\tHTTP Server initialized on {}".\
				format(self.httpd.socket.getsockname())
			)

			# SET UP MASTER THREADS ============================================

			# INITIALIZE BROADCAST THREAD --------------------------------------

			# Configure sentinel value for broadcasts:
			self.broadcastSwitch = True
				# ABOUT: UDP broadcasts will be sent only when this is True
			self.broadcastSwitchLock = threading.Lock() # thread-safe access

			self.broadcastThread = threading.Thread(
				name = "FCMkII_broadcast",
				target = self._broadcastRoutine,
				args = [bytearray("N|{}|{}".format(
							self.passcode,
							self.listenerPort),'ascii'),
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

			# instantiate any saved Slaves:
            saved = self.profile[ac.savedSlaves]
			self.slaves = [None]*len(saved)
			update = []
			for slave in saved:
                index = slave[ac.SV_index]
				self.slaves[index] = \
					sv.FCSlave(
					mac = slave[ac.SV_mac],
					status = sv.DISCONNECTED,
					routine = self._slaveRoutine,
					routineArgs = (index,),
					misoQueueSize = self.misoQueueSize,
					index = index,
					)

				# Add to list:
				update +=[
                    index,
                    slave[ac.name],
					slave[ac.SV_mac],
					sv.DISCONNECTED,
					slave[ac.SV_maxFans],
					self.slaves[index].getVersion()]
			"""
			self.newSlaveQueue.put_nowait(newSlaves)
			"""
			self.networkPipeSend.send(update)


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
			self.printM("[IR] Prototype input routine started","G")
			while True:

				try:
					# Input --------------------------------------------------------

					# Check commands:
					if self.updatePipeOut.poll():
						command = self.updatePipeOut.recv()

						# Classify command:
						if command[wg.COMMAND] == ADD:

							if command[wg.VALUE] == ALL:
								for index, slave in enumerate(self.slaves):
									self.add(index)
										# NOTE: Unapplicable Slaves will be
										# automatically ignored
							else:
								self.add(command[wg.VALUE])


						elif command[wg.COMMAND] == DISCONNECT:

							if command[wg.VALUE] == ALL:
								self.sendDisconnect()
							else:
								self.slaves[command[wg.VALUE]].\
									setMOSI((MOSI_DISCONNECT,),False)

						elif command[wg.COMMAND] == REBOOT:

							if command[wg.VALUE] == ALL:
								self.sendReboot()
							else:
								self.sendReboot(self.slaves[command[wg.VALUE]])

						elif command[wg.COMMAND] == wg.STOP:
							self.stop()

						elif command[wg.COMMAND] == SET_DC:

							if command[wg.VALUE + 2] == ALL:

								for index, slave in enumerate(self.slaves):
									if slave.getStatus() is sv.CONNECTED:
										slave.setMOSI(
											(	MOSI_DC,
												command[wg.VALUE]) +\
												command[wg.VALUE+1],
											False
										)
							else:

								for index in command[wg.VALUE+2:]:
									if self.slaves[index].getStatus() is \
										sv.CONNECTED:
										self.slaves[index].setMOSI(
											(	MOSI_DC,
												command[wg.VALUE]) + \
												command[wg.VALUE+1],

											False
										)

						elif command[wg.COMMAND] is SET_DC_GROUP:

							dc = command[wg.VALUE]


							for pair in command[wg.VALUE+1]:
								# NOTE: Here 'pair' is a tuple of the form
								# (index, fans)
								# Where 'index' is the index of the selected
								# Slave and 'fans' is an n-tuple of 0's and 1's,
								# (as long as the Slave's fan array) and
								# denoting which fans are selected...

								if self.slaves[pair[0]].getStatus()\
									== sv.CONNECTED:

									self.slaves[pair[0]].setMOSI(
										(MOSI_DC,
										dc) # Duty cycle
										 + pair[1]# Fan selection tuple

									)

						elif command[wg.COMMAND] is SET_DC_MULTI:
							# NOTE: Here wg.VALUE contains a list of tuples
							# of the form (INDEX, DC1, DC2 ... DCN)

							for slaveTuple in command[wg.VALUE]:
								if self.slaves[slaveTuple[0]].getStatus()\
									== sv.CONNECTED:

									self.slaves[slaveTuple[0]].setMOSI(
										(MOSI_DC_MULTI, ) + slaveTuple[1:]
									)

						elif command[wg.COMMAND] is SET_RPM:

							if command[wg.VALUE + 2] is ALL:

								for index, slave in enumerate(self.slaves):
									if slave.getStatus() is sv.CONNECTED:
										slave.setMOSI(
											(	MOSI_RPM,
												command[wg.VALUE],
												command[wg.VALUE+1]
											),
											False
										)
							else:

								for index in command[wg.VALUE+2:]:
									if self.slaves[index].getStatus() is \
										sv.CONNECTED:
										self.slaves[index].setMOSI(
											(	MOSI_RPM,
												command[wg.VALUE],
												command[wg.VALUE+1]
											),
											False
										)

						elif command[wg.COMMAND] is BOOTLOADER_START:

							self.printM("Flash order received:"\
								"\n\tVersion: {} "\
								"\n\tFile: \"{}\""\
								"\n\tSize: {} bytes)".\
									format(
										command[wg.VALUE],
										command[wg.VALUE + 1],
										command[wg.VALUE + 2]
									)
							)

							self.flashFlag = True
							self.targetVersion = command[wg.VALUE]

							fileName = command[wg.VALUE+1]

							self.flashMessage = \
								"U|CT|{}|{}|{}|{}".\
								format(
								self.listenerPort,
								self.httpPort,
								fileName,
								command[wg.VALUE+2]
							)

						elif command[wg.COMMAND] is BOOTLOADER_STOP:

							self.printM("Received order to stop flashing")
							self.flashFlag = False

					# Check matrix:
					matrix = self.mosiMatrixQueue.get_nowait()
					index = 0
					for row in matrix:
						if row[0] is not NO_COMMAND:
							self.slaves[index].setMOSI(row)

						index += 1

				except queue.Empty:
					continue

				except queue.Full:
					continue

				except Exception as e: # Print uncaught exceptions
					self.printM("[IR] EXCEPTION: "\
						"\"{}\"".\
						format(traceback.format_exc()), "E")

		except Exception as e: # Print uncaught exceptions
			self.printM("[IR] UNHANDLED EXCEPTION: "\
				"\"{}\" (BROKE OUT OF LOOP)".\
				format(traceback.format_exc()), "E")
		# End _inputRoutine ====================================================

	def _outputRoutine(self): # ================================================
		# Summarize asynchronous output from each Slave thread into a matrix
		# and send out status changes

		try:

			self.printM("Prototype output routine started", "G")
			while True:
				time.sleep(self.periodS)
				try:
					# Output -------------------------------------------------------

					updates = ()
					for i in range(self.slaveUpdateQueue.qsize()):
						updates += self.slaveUpdateQueue.get_nowait()

					if len(updates) > 0:
						self.networkPipeSend.send((UPDATE, updates))

					# Assemble output matrix:
					output = []
					for slave in self.slaves:
						output.append(slave.getMISO())

					self.newMISOMatrixPipeIn.send(output)


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
					"""
					for i in (1,2):
						self.broadcastSocket.sendto(broadcastMessage,
							(FORCE_BROADCAST_IP, self.broadcastPort))
					"""
					self.broadcastSocket.sendto(broadcastMessage,
						(FORCE_BROADCAST_IP, self.broadcastPort))

				#self.broadcastSwitchLock.release()
				#self.broadcastLock.release()

				# Guarantee lock release:

		except socket.error:
			self.printM("[BT] NETWORK ERROR. COMMUNICATIONS DOWN ({})".\
				format(traceback.format_exc()),'E')
			self.stop()

		except:
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

				# DEBUG: print("Message received")

				""" NOTE: The message received from Slave, at this point,
					should have one of the following forms:

					- STD from MkII:
						A|PCODE|SV:MA:CA:DD:RE:SS|N|SMISO|SMOSI|VERSION
						0     1			2 3	4     5 6
					- STD from Bootloader:
						B|PCODE|SV:MA:CA:DD:RE:SS|N|[BOOTLOADER_VERSION]
						0	  1					2 3					4

					- Error from MkII:
						A|PCODE|SV:MA:CA:DD:RE:SS|E|ERRMESSAGE

					- Error from Bootloader:
						B|PCODE|SV:MA:CA:DD:RE:SS|E|ERRMESSAGE

					Where SMISO and SMOSI are the Slave's MISO and MOSI
					port numbers, respectively. Notice separators.
				"""
				messageSplitted = messageReceived.decode('ascii').split("|")
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

								# Check flashing case:
								if self.flashFlag and version != \
									self.targetVersion:
									# Version mismatch. Send reboot message

									# Send reboot message
									self.listenerSocket.sendto(
										bytearray("R|{}".\
											format(self.passcode),'ascii'),
										senderAddress
									)

								# If the index is in the Slave dictionary,
								# check its status and proceed accordingly:

								elif self.slaves[index].getStatus() in \
									(sv.DISCONNECTED, sv.BOOTLOADER):
									# If the Slave is DISCONNECTED but just res-
									# ponded to a broadcast, update its status
									# for automatic reconnection. (handled by
									# their already existing Slave thread)

									# Update status and networking information:
									self.setSlaveStatus(
										self.slaves[index],
										sv.KNOWN,
										lock = False,
										netargs = (
											senderAddress[0],
											misoPort,
											mosiPort,
											version
											)

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


								self.slaves,append(
									sv.FCSlave(
                                        mac = mac,
                                        status = sv.AVAILABLE,
                                        routine = self._slaveRoutine,
                                        routineArgs = (index, ),
                                        version = version,
                                        misoQueueSize = self.misoQueueSize,
                                        ip = senderAddress[0],
                                        misoP = misoPort,
                                        mosiP = mosiPort,
                                        index = index)
								)

								# Add new Slave's information to newSlaveQueue:
								self.networkPipeSend.send(
									(NEW,
									((index,
									mac,
									sv.AVAILABLE,
									self.maxFans,
									version),))
								)
								"""
								self.newSlaveQueue.put_nowait(
									((index,
									mac,
									sv.AVAILABLE,
									self.maxFans,
									version),))
								print ("Queue: ",self.newSlaveQueue.qsize())
								"""

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

							if not self.flashFlag:
								# No need to flash. Launch MkII:
								self.listenerSocket.sendto(
									bytearray(launchMessage,'ascii'),
									senderAddress)

							else:
								# Flashing in progress. Send flash message:

								self.listenerSocket.sendto(
									bytearray(self.flashMessage,'ascii'),
									senderAddress)

							# Update Slave status:

							# Search for Slave in self.slaves
							index = None
							mac = messageSplitted[2]

							for slave in self.slaves:
								if slave.getMAC() == mac:
									index = slave.getIndex()
									break

							if index is not None:
								# Known Slave. Update status:

								# Try to get bootloader version:
								try:
									version = messageSplitted[4]
								except IndexError:
									version = "Bootloader(?)"

								self.slaves[index].setVersion(version)
								self.setSlaveStatus(
									self.slaves[index],
									sv.BOOTLOADER
								)

							else:

								# Send launch message:
								self.listenerSocket.sendto(
									bytearray(launchMessage,'ascii'),
									senderAddress)


						elif messageSplitted[3] == 'E':
							# Error message

							self.printM("Error message from {} "\
								"on Bootloader: \"{}\"".format(
									messageSplitted[2],
									messageSplitted[4]),
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

			self.printM("[SV] ({:3d}) Slave sockets connected: "\
			 " MMISO: {} MMOSI:{}".\
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

			failedHSKs = 0


			# Slave loop =======================================================
			while(True):

				try:
				#slave.acquire()

					status = slave.getStatus()

					# Act according to Slave's state:
					if status == sv.KNOWN: # = = = = = = = = = = = = = = = =

						# If the Slave is known, try to secure a connection:
						# print "Attempting handshake"

						# Check for signs of life w/ HSK message:
						self._send(MHSK, slave, 2, True)

						# Give time to process:
						#time.sleep(periodS)

						tries = 2
						while True:

							# Try to receive reply:
							reply = self._receive(slave)

							# Check reply:
							if reply is not None and reply[1] == "H":
								# print "Processed reply: {}".format(reply), "G"
								# print "Handshake confirmed"

								# Mark as CONNECTED and get to work:
								#slave.setStatus(sv.CONNECTED, lock = False)
								self.setSlaveStatus(slave,sv.CONNECTED,False)
								tryBuffer = True
								break

								"""
								self._saveTimeStamp(slave.getIndex(), "Connected")
								"""

							elif reply is not None and reply[1] == "K":
								# HSK acknowledged, give Slave time
								continue

							elif tries > 0:
								# Try again:
								self._send(MHSK, slave, 1, True)
								tries -= 1

							elif failedHSKs is 0:
								# Disconnect Slave:
								self._send("X", slave, 2)
								#slave.setStatus(sv.DISCONNECTED, lock = False)

								self.setSlaveStatus(
									slave,sv.DISCONNECTED,False)
									# NOTE: This call also resets exchange
									# index.
								break

							else:
								# Something's wrong. Reset sockets.
								self.printM("Resetting sockets for {} ({})".\
									format(slave.getMAC(), targetIndex + 1),
									'W'
								)

							# MISO:
							slave._misoSocket().close()

							misoS = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
							misoS.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
							misoS.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
							misoS.settimeout(self.periodS*2)
							misoS.bind(('', 0))

							# MOSI:
							slave._misoSocket().close()

							mosiS = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
							mosiS.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
							mosiS.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
							mosiS.settimeout(self.periodS)
							mosiS.bind(('', 0))

							# Assign sockets:
							slave.setSockets(newMISOS = misoS, newMOSIS = mosiS)

							self.printM("[SV] {:3d} Slave sockets re-connected:"\
							 " MMISO: {} MMOSI:{}".\
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


							# Reset counter:
							failedHSKs = 0

							continue

					elif status == sv.CONNECTED: # = = = = = = = = = = = = = = =
						# If the Slave's state is positive, it is online and
						# there is a connection to maintain.

						# A positive state indicates this Slave is online and
						# its connection need be maintained.

						#DEBUG DEACTV
						## print "[On positive state]"

						# Check flashing flag:
						if self.flashFlag and slave.getVersion() != \
							self.targetVersion:

							# If the flashing flag is set and this Slave has
							# the wrong version, reboot it

							self._send("R", slave, 1)
							self.setSlaveStatus(slave, sv.DISCONNECTED, False)

							continue

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

						elif fetchedMessage[0] == MOSI_DC_ALL:
							# Chase RPM
							# Raw format: [MOSI_DC_ALL, RPM]

							message = "S|D:{}:{}".format(
								fetchedMessage[1]*0.01, self.fullSelection)

							self._send(message, slave, 2)

						elif fetchedMessage[0] == MOSI_DC_MULTI:
							message = "S|F:"
							for dc in fetchedMessage[1:]:
								message += str(dc*0.01) + ','

							self._send(message, slave, 2)

						elif fetchedMessage[0] == MOSI_RPM:
							# Chase RPM
							# Raw format: [MOSI_RPM, RPM, FAN1S,FAN2S...]

							selection = ''
							for fan in fetchedMessage[2:]:
								if fan == 1:
									selection += '1'
								else:
									selection += '0'

							message = "S|C:{}:{}".format(
								fetchedMessage[1], selection)

							self._send(message, slave, 2)

						elif fetchedMessage[0] == MOSI_RPM_ALL:
							# Chase RPM
							# Raw format: [MOSI_RPM_ALL, RPM]

							message = "S|C:{}:{}".format(
								fetchedMessage[1], self.fullSelection)

							self._send(message, slave, 2)

						elif fetchedMessage[0] == MOSI_DISCONNECT:
							self._sendToListener("X", slave, 2)

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
											(slave.getStatus(),sv.MISO_UPDATED) +
											tuple(map(int,reply[-2].split(',')))+
											tuple(map(float,reply[-1].split(','))),
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
									except queue.Full:

										# If there is no room for this message,
										# drop the packet and alert the user:
										slave.incrementDropIndex()


							elif reply[1] == 'I':
								# Reset MISO index

								slave.setMISOIndex(0)
								self.printM("[SV] {} MISO Index reset".format(
									slave.getMAC()))

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

								self.printM("[SV] {:3d} ERROR: \"{}\"".format(
									targetIndex + 1, reply[2]), "E")

							elif reply[1] == 'Q':
								# Ping reply. Pass
								pass

							else:
								# Unrecognized command

								self.printM("[SV] {:3d} Warning, unrecognized "\
									"message: \"{}\"".format(
										targetIndex + 1, reply), "W")

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
								#	self.maxTimeouts)

								# Restart loop:
								pass

							elif tryBuffer:
								self._send("Y", slave, 2)
								tryBuffer = False

							else:
								self.printM("[SV] {} Slave timed out".\
									format(targetIndex + 1), "W")

								# Terminate connection: ........................

								# Send termination message:
								self._sendToListener("X", slave)

								# Reset timeout counter:
								timeouts = 0
								totalTimeouts = 0

								# Update Slave status:
								"""
								slave.setStatus(
									sv.DISCONNECTED, lock = False)
								"""
								self.setSlaveStatus(
									slave,sv.DISCONNECTED, False)
								# Restart loop:
								pass

								# End check timeout counter - - - - - - - - - -

							# End check reply ---------------------------------

					elif status == sv.BOOTLOADER:
						time.sleep(self.periodS)

					else: # = = = = = = = = = = = = = = = = = = = = = = = = = =
						time.sleep(self.periodS)
						"""
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
									#slave.setStatus(sv.CONNECTED)
									self.setSlaveStatus(
										slave,sv.CONNECTED, False)

							else:
								self._sendToListener("X", slave)
						"""
				except Exception as e: # Print uncaught exceptions
					self.printM("[{}] UNCAUGHT EXCEPTION: \"{}\"".
					   format(targetIndex + 1, traceback.format_exc()), "E")

				finally:
					# DEBUG DEACTV
					## print "Slave lock released", "D"
					# Guarantee release of Slave-specific lock:
					"""
					try:
						slave.release()
					except _thread.error:
						pass
					"""
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
			slave._mosiSocket().sendto(bytearray(outgoing,'ascii'),
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
				slave._mosiSocket().sendto(bytearray(outgoing,'ascii'),
				(slave.ip, self.broadcastPort))
		else:
			# Send through broadcast:
			# Prepare message:
			outgoing = "J|{}|{}|{}".format(
				self.passcode, slave.getMAC(), message)
			for i in range(repeat):
				slave._mosiSocket().sendto(bytearray(outgoing,'ascii'),
				(FORCE_BROADCAST_IP, self.broadcastPort))

		# End _sendToListener # # # # # # # # # # # # # # # # # # # # # # # # # #

	def _receive(self, slave): # # # # # # # # # # # # # # # # # # # # # # # # #
		# ABOUT: Receive a message on the given Slave's sockets (assumed to be
		# CONNECTED, BUSY or KNOWN.
		# PARAMETERS:
		# - slave: Slave unit for which to listen.
		# RETURNS:
		# - three-tuple:
		#	(exchange index (int), keyword (str), command (str) or None)
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
					splitted = message.decode('ascii').split("|")

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
					#	 format(len(splitted), str(splitted)), "D"

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
					#	format(e), "W")

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

		except queue.Empty:
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
			print(("[DEBUG][COMMS] " + output))

		try:
			self.printQueue.put_nowait((self.symbol + output, tag))
			return True

		except queue.Full:
			print(("[WARNING] Communications output queue full. "\
				"Could not print the following message:\n\r \"{}\"".\
				format(output)))
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
			self.setSlaveStatus(self.slaves[targetIndex],sv.KNOWN)
		else:
			pass

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

	def sendReboot(self, target = None): # =====================================
		# ABOUT: Use broadcast socket to send a general "disconnect" message
		# that terminates any existing connection.

		try:
			#self.broadcastLock.acquire()
			if target is None:
				# General broadcast
				self.rebootSocket.sendto(
					bytearray("R|{}".format(self.passcode),'ascii'),
					(FORCE_BROADCAST_IP, self.broadcastPort))

			elif target.getIP() is not None:
				# Targetted broadcast w/ valid IP:
				self.rebootSocket.sendto(
					bytearray("R|{}".format(self.passcode),'ascii'),
					(target.getIP(), self.broadcastPort))

			else:
				# Targetted broadcast w/o IP (use MAC):
				self.rebootSocket.sendto(
					bytearray("r|{}|{}".format(self.passcode, target.getMAC()),
						'ascii'
					),
					(FORCE_BROADCAST_IP, self.broadcastPort)
				)


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
				bytearray("X|{}".format(self.passcode),'ascii'),
				(FORCE_BROADCAST_IP, self.broadcastPort))

		except Exception as e:
			self.printM("[sD] UNCAUGHT EXCEPTION: \"{}\"".
			   format(traceback.format_exc()), "E")

		# End sendDisconnect ===================================================

	def setSlaveStatus(self, slave, newStatus, lock = True, netargs = None): # =

		# Update status:
		if netargs is None:
			slave.setStatus(newStatus, lock = lock)

		else:

			slave.setStatus(
				newStatus,
				netargs[0],
				netargs[1],
				netargs[2],
				netargs[3],
				lock = lock,
			)

		# Send update to handlers:
		self.slaveUpdateQueue.put_nowait(
					((slave.index,
					slave.mac,
					newStatus,
					self.maxFans,
					slave.version
					),)
			)
		# End setSlaveStatus ===================================================

	def stop(self): # ==========================================================
		# Cleanup routine for termination.


		print("Terminating")
		# Send disconnect signal:
		self.sendDisconnect()
		self.stoppedFlag = True

		print("Terminated")

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

	print("FANCLUB MARK II COMMUNICATOR MODULE TEST SUITE INITIATED.")
	print(("VERSION = " + VERSION))


	print("NO TEST SUITE IMPLEMENTED IN THIS VERSION. TERMINATING.")
