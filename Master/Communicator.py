################################################################################
## Project: Fan Club Mark II "Master" ## File: Communicator.py                ##
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

import socket     	# Networking
import threading  	# Multitasking
import thread     	# thread.error
import time       	# Timing
import Queue
import sys        	# Exception handling
import traceback  	# More exception handling
import random		# Random names, boy
import numpy		# Fast arrays and matrices

import FCInterface
import Profiler    # Custom representation of wind tunnel
import Slave
import Fan
import names


VERSION = "Separate 0"
FORCE_IP_ADDRESS = ""
	#= "192.168.1.129" # (Basement lab)

## CLASS DEFINITION ############################################################

class Communicator:

	def __init__(self, slaveList, profile, bcupdate, ltupdate): # ==============
		# ABOUT: Constructor for class Communicator.

		try:

			# INITIALIZE DATA MEMBERS ==========================================

			# Output queues:
			self.mainQueue = Queue.Queue(profile["mainQueueSize"])
			self.newSlaveQueue = Queue.Queue()

			self.printM("Initializing Communicator instance")

			# Interface:
			self.ltupdate = ltupdate
			self.bcupdate = bcupdate

			# Profiler:
			self.profile = profile
			
			# Initialize Slave dictionary:
			self.slaves = {}
			self.slavesLock = threading.Lock()

			# Communications:
			self.broadcastPeriodS = profile["broadcastPeriodS"]
			self.periodMS = profile["periodMS"]
			self.broadcastPort = profile["broadcastPort"]
			self.password = profile["passcode"]

			# Create a temporary socket to obtain Master's IP address:
			temp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			temp.connect(('192.0.0.8', 1027))
			self.hostIP = temp.getsockname()[0]
			temp.close()

			self.printM("\tHost IP: {}".format(self.hostIP))

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

			self.printM("\tbroadcastSocket initialized on " + \
				str(self.broadcastSocket.getsockname()))
			
			# SET UP MASTER THREADS ============================================

			# INITIALIZE BROADCAST THREAD --------------------------------------

			# Configure sentinel value for broadcasts:
			self.broadcastSwitch = True
				# ABOUT: UDP broadcasts will be sent only when this is True
			self.broadcastSwitchLock = threading.Lock() # thread-safe access

			self.broadcastThread = threading.Thread(
				name = "FCMkII_broadcast",
				target = self._broadcastRoutine,
				args = ["00000000|{}|{}".format(self.password, 
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

			# Loop over slaveList to instantiate any saved Slaves:
			for subList in slaveList:
				# NOTE: Here each sub list, if any, contains data to initialize
				# known Slaves, in the following order:
				#
				# subList[0]: Name (as a string)
				# subList[1]: MAC address (as a string)
				# subList[2]: Number of active fans (as an integer)


				self.slaves[subList[1]] = Slave.Slave( # Use MAC as dict. key
					name = subList[0],
					mac = subList[1],
					status = Slave.DISCONNECTED,
					maxFans = self.profile["maxFans"],
					activeFans = subList[2],
					routine = self._slaveRoutine,
					routineArgs = (subList[1],),
					misoQueueSize = profile["misoQueueSize"]
					)
				
				# Add Slave to newSlaveQueue:
				self.putNewSlave(subList[1])

			# START MASTER THREADS =============================================
			self.listenerThread.start()
			self.broadcastThread.start()
			
			# DONE
			self.printM("Communicator ready", "G")
			
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

				self.broadcastSwitchLock.acquire()
				try:
					# Send broadcast only if self.broadcastSwitch is True:
					if self.broadcastSwitch:
						# Broadcast message:
						self.broadcastSocket.sendto(broadcastMessage, 
							("<broadcast>", 65000))

					# Blink broadcast display:
					self.bcupdate()

				finally:
					# Guarantee lock release:
					self.broadcastSwitchLock.release()

		except Exception as e:
			self.printM("[BT] UNHANDLED EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")

		self.bcupdate("R")

		# End _broadcastRoutine ================================================

	def _listenerRoutine(self): # ==============================================
		""" ABOUT: This method is meant to run within an instance's listener-
			Thread. It will wait indefinitely for messages to be received by
			the listenerSocket and respond accordingly.
		"""

		try:    

			self.printM("[LT] Listener thread started. Waiting.", "G")

			while(True):
				self.ltupdate()

				# Wait for a message to arrive:
				messageReceived, senderAddress = \
					self.listenerSocket.recvfrom(256)

				self.ltupdate("B")
				""" NOTE: The message received from Slave, at this point, 
					should have the following form:

						000000000|PASSWORD|SV:MA:CA:DD:RE:SS|SMISO|SMOSI|

					Where SMISO and SMOSI are the Slave's MISO and MOSI 
					port numbers, respectively. Notice separators.
				"""

				messageSplitted = messageReceived.split("|")
					# NOTE: messageSplitted is a list of strings, each of which
					# is expected to contain a string as defined in the comment
					# above.

				# Validate message ---------------------------------------------

				try:

					# Verify password:
					if messageSplitted[1] != self.password:
						raise ValueError("Wrong password received ({})".\
							format(messageSplitted[1]))

					# Attempt conversion into corresponding containers:
					misoPort = int(messageSplitted[3])
					mosiPort = int(messageSplitted[4])
					mac = messageSplitted[2]
					# A ValueError will be raised if invalid port numbers are
					# given and an IndexError will be raised if the given 
					# message yields less than three strings when splitted.

					# DEBUG DEACTV:
					"""
					self.printL("Parsed:\
								\n\t\t Password: {}\
								\n\t\t MAC: {}\
								\n\t\t MMISO: {}\
								\n\t\t MMOSI: {}\n".\
								format(
								messageSplitted[1],
								messageSplitted[2],
								messageSplitted[3],
								messageSplitted[4]))
					"""

					# Verify converted values:
					if (misoPort <= 0 or misoPort > 65535):
						# Raise a ValueError if a port number is invalid:
						raise ValueError("Bad SMISO ({}). Need [1, 65535]".\
							format(miso))

					if (mosiPort <= 0 or mosiPort > 65535):
						# Raise a ValueError if a port number is invalid:
						raise ValueError("Bad SMOSI ({}). Need [1, 65535]".\
							format(mosi))

					if (len(mac) != 17):
						# Raise a ValueError if the given MAC address is not 17
						# characters long.
						raise ValueError("MAC ({}) not 17 chars ({})")


				except (ValueError, IndexError) as e:

					# If the given message is invalid, discard it and move on:

					self.printM("[LT ]Error: \"{}\"\n\tObtained when parsing \"\
						{}\" from {}. (Message discarded)"\
					.format(e, messageReceived, senderAddress), "E")

					# Move on:
					continue

				# Check Slave against self.slaves and respond accordingly ------
					# (Message validation completed successfully by this point)
				
				# Check if the Slave is known:
				if(mac in self.slaves):

					# If the MAC address is in the Slave dictionary, check its
					# recorded status and proceed accordingly:

					if self.slaves[mac].getStatus() == Slave.DISCONNECTED:
						# If the Slave is recorded as DISCONNECTED but just res-
						# ponded to a broadcast, update its status and mark it
						# for automatic reconnection.
						
						# NOTE:  
						#	DISCONNECTED Slaves were previously connected to
						#   and later anomalously disconnected. Since have
						#   been chosen by the user, they should be recon-
						#   nected to automatically. Changing their state to
						#	KNOWN will trigger a response from the corres-
						#	ponding Slave thread to connect automatically.

						# Update status and networking information:
						self.slaves[mac].setStatus(
							Slave.KNOWN,
							senderAddress[0],
							misoPort,
							mosiPort
							)

					else:
						# All other statuses should be ignored for now.
						pass

				else:
					# If the MAC address is not recorded, list this board as A-
					# VAILABLE and move on. The user may choose to add it later:

					# NOTE: Slaves that are not connected will have either port
					# numbers or None as their "miso" and "mosi" attributes.
					# When a connection is secured, these port numbers will be
					# replaced by UDP sockets CONNECTED to said port numbers --
					# notice these are CONNECTED to, not BINDED to, said port
					# numbers.

					# Create a new Slave instance and store it:

					self.slaves[mac] = Slave.Slave( # Use MAC as dict. key
						name = random.choice(names.coolNames),
						mac = mac,
						status = Slave.AVAILABLE,
						maxFans = self.profile["maxFans"],
						activeFans = self.profile["maxFans"],
						routine = self._slaveRoutine,
						routineArgs = (mac, ),
						misoQueueSize = self.profile["misoQueueSize"],
						ip = senderAddress[0],
						misoP = misoPort,
						mosiP = mosiPort
						)
			
					# Add new Slave's information to newSlaveQueue:
					self.putNewSlave(mac)

		except Exception as e: # Print uncaught exceptions
			self.printM("[LT] UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")

		self.ltupdate("R")
				
		# End _listenerRoutine =================================================

	def _slaveRoutine(self, targetMAC, target): # # # # # # # # # # # # # # # # 
		# ABOUT: This method is meant to run on a Slave's communication-handling
		# thread. It handles sending and receiving messages through its MISO and
		# MOSI sockets, at a pace dictated by the Communicator instance's given
		# period. 
		# PARAMETERS:
		# - targetMAC: String, MAC address of the Slave handled by
		#   this thread.
		# - target: Slave controlled by this thread
		# NOTE: This current version is expected to run as daemon.

		try:

			# Setup ============================================================
			self.printM("[{}] Slave thread started".\
				format(targetMAC, "G"))

			# Get reference to Slave: ------------------------------------------
			slave = target

			# Set up sockets ---------------------------------------------------
			# MISO:
			misoS = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			misoS.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			misoS.settimeout(self.profile["masterTimeoutS"])
				# The communications period is defined in milliseconds. The 
				# socket timeout should be one-fifth of said period, and this
				# method expects a value in seconds.
			misoS.bind(('', 0))

			# MOSI:
			mosiS = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			mosiS.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			mosiS.settimeout(self.profile["masterTimeoutS"])
				# The communications period is defined in milliseconds. The 
				# socket timeout should be one-fifth of said period, and this
				# method expects a value in seconds.
			mosiS.bind(('', 0))
			
			# Assign sockets:
			slave.setSockets(newMISOS = misoS, newMOSIS = mosiS)

			self.printM("[{}] Sockets set up successfully: \
			 \n\t\tMMISO: {}\n\t\tMMOSI:{}".\
				format(slave.mac,
					slave.misoS.getsockname(), slave.mosiS.getsockname()))

			# HSK message ------------------------------------------------------

			MHSK = "MHSK|{},{},{},S~{},{},{},{},{},{},{},{},{}".format(
						slave.misoS.getsockname()[1], 
						slave.mosiS.getsockname()[1], 
						self.profile["periodMS"],
						self.profile["fanMode"],
						self.profile["targetRelation"][0],
						self.profile["targetRelation"][1],
						self.slaves[targetMAC].activeFans,
						self.profile["counterCounts"],
						self.profile["pulsesPerRotation"],
						self.profile["maxRPM"],
						self.profile["minRPM"],
						self.profile["minDC"])

			# Set up placeholders and sentinels --------------------------------
			slave.resetIndices()
			timeouts = 0
			message = None

			# Slave loop =======================================================
			while(True):
				time.sleep(self.profile["interimS"])

				try:

					# Acquire lock:
					slave.acquire()
					
					status = slave.getStatus()

					# Act according to Slave's state: 
					if status == Slave.KNOWN: # = = = = = = = = = = = = = = = =

						# If the Slave is known, try to secure a connection:
						# print "Attempting handshake"

						# Check for signs of life w/ HSK message:
						self._send(MHSK, slave, 1, True)

						# Try to receive reply:
						reply = self._receive(slave)

						# Check reply:
						if reply != None and reply[1] == "SHSK":
							# print "Processed reply: {}".format(reply), "G"
							# print "Handshake confirmed"

							# Mark as CONNECTED and get to work:
							slave.setStatus(Slave.CONNECTED, lock = False)
							
						else:
							# If there was an error, restart attempt:
							# print
							#   "Missed handshake. Retrying."
							# Set Slave to disconnected:
							slave.setStatus(Slave.DISCONNECTED, lock = False) 
								# NOTE: This call also resets exchange index.
								

					elif slave.status > 0: # = = = = = = = = = = = = = = = = = = 
						# If the Slave's state is positive, it is online and 
						# there is a connection to maintain.

						# A positive state indicates this Slave is online and 
						# its connection need be maintained.

						#DEBUG DEACTV
						## print "[On positive state]"

						# Check queue for message:
						
						command = slave.getMOSI()
							
						if command != None:
							message = "MSTD|" + command
							# Send message, if any:
							self._send(message, slave, 4)

							# DEBUG: 
							# print "Sent: {}".format(message)

						# Get reply:
						reply = self._receive(slave)

						# Check reply: -----------------------------------------
						if reply != None:
							# print "Processed reply: {}".format(reply)

							# Restore timeout counter after success:
							timeouts = 0

							# Check if there are DCs and RPMs:
							if len(reply) > 2:
								# Update RPMs and DCs:
								try:
									slave.update(
										Slave.VALUE_UPDATE,
										(numpy.array(
											map(float,reply[-1].split(','))),
										numpy.array(
											map(int,reply[-2].split(',')))
										))

								except Queue.Full:
									# If there is no room for the queue, dismiss
									# this update and warn the user:
									
									self.printM("[{}] WARNING: MISO Queue Full. "\
										"GUI thread falling behind. "\
										"Maybe the system "\
										"is set to run too fast for "\
										"its own good?".\
										format(slave.mac), "E")
						else:
							timeouts += 1

							if message != None:
								# If a message was sent and no reply was 
								# received, resend it:
								# print "Timed out. Resending"
								# Resend message:
								self._send(message, slave, 4)
								# Increment timeout counter:

							# Check timeout counter: - - - - - - - - - - - - - -
							if timeouts < self.profile["maxTimeouts"]:
								# If there have not been enough timeouts to con-
								# sider the connection compromised, continue.
								# print "Reply missed ({}/{})".
								#   format(timeouts, 
								#       self.profile["maxTimeouts"])

								# Restart loop:
								pass

							else:
								self.printM("[{}] Slave timed out".\
									format(targetMAC), "W")

								# Terminate connection: ........................

								# Send termination message:
								self._send("MRIP", slave)

								# Reset timeout counter:
								timeouts = 0

								# Update Slave status:
								slave.setStatus(
									Slave.DISCONNECTED, lock = False)

								# Restart loop:
								pass

								# End check timeout counter - - - - - - - - - - 

							# End check reply ---------------------------------

					else: # = = = = = = = = = = = = = = = = = = = = = = = = = = 
						
						# If this Slave is neither online nor waiting to be 
						# contacted, wait for its state to change.

						# Reset index:
						slave.resetIndices()

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
			   format(targetMAC, traceback.format_exc()), "E")
		
		self.printM("[{}] WARNING: BROKE OUT OF SLAVE LOOP".
			format(targetMAC), "E")
		# End _slaveRoutine  # # # # # # # # # # # #  # # # # # # # # # # # # # 

	# # AUXILIARY METHODS # # # # # # # # # # # # # # # # # # # # # # # # # # #
		# ABOUT: These methods are to be used within this class. For methods to
		# be accessed by the user of a Communicator instance, see INTERFACE ME-
		# THODS below.

	def _send(self, message, slave ,repeat = 1, hsk = False): # # # # # # # # # 
		# ABOUT: Send message to a KNOWN or CONNECTED Slave. Automatically add
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
					self.profile["maxLength"])

				# DEBUG DEACTV
				## print "Received: \"{}\" from {}".
				 #   format(message, sender), "D")

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
	
	def putNewSlave(self, mac): # ==============================================
		# ABOUT: Add relevant information of a new Slave to the newSlaveQueue,
		# for the interface module to access.
		# RAISES:
		#	- KeyError if the given MAC address is not found.
		
		# Add Slave to Queue:
		self.newSlaveQueue.put_nowait((
			self.slaves[mac].getName(),
			mac,
			self.slaves[mac].getStatus(),
			self.slaves[mac].getMaxFans(),
			self.slaves[mac].getActiveFans(),
			self.slaves[mac].getIP(),
			self.slaves[mac].getUpdate, # NOTE: Here the method itself is passed.
			self.slaves[mac].setMOSI
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
			return self.newSlaveQueue.get(False)

		except Queue.Empty:
			return None

		# End getNewSlave ======================================================

	def printM(self, output, tag = 'S'): # =====================================
		# ABOUT: Print on corresponding GUI terminal screen by adding a message to
		# this Communicator's corresponding output Queue.
		# PARAMETERS:
		# - output: str, string to be printed.
		# - tag: str, single character for string formatting.
		# RETURNS: bool, whether the placement of the message was successful.
		# The given message will be added to the corresponding output Queue or
		# will block until it is possible.

		# Place item in corresponding output Queue:
		return self.mainQueue.put((output, tag))
		
		# End printM ===========================================================

	# # INTERFACE METHODS # # # # # # # # # # # # # # # # # # # # # # # # # 
	
	def add(self, targetMAC): # ================================================
		# ABOUT: Mark a Slave on the network for connection. The given Slave 
		# must be already listed and marked AVAILABLE. This method will mark it 
		# as KNOWN, and its corresponding handler thread will connect automati-
		# cally.
		# PARAMETERS:
		# - targetMAC: String, MAC address of Slave to "add."
		# RAISES:
		# - Exception if targeted Slave is not AVAILABLE.
		# - KeyError if targetMAC is not in Slave dictionary.

		# Check status:
		status = self.slaves[targetMAC].getStatus()

		if status == Slave.AVAILABLE:
			self.slaves[targetMAC].setStatus(Slave.KNOWN)

		else:
			raise Exception("Targeted Slave [{}] is not AVAILABLE but {}".\
				format(targetMAC, Slave.translate(status)))

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





## MODULE'S TEST SUITE #########################################################

if __name__ == "__main__":

	print "FANCLUB MARK II COMMUNICATOR MODULE TEST SUITE INITIATED."
	print "VERSION = " + VERSION


	print "NO TEST SUITE IMPLEMENTED IN THIS VERSION. TERMINATING."
