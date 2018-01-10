################################################################################
## Project: Fanclub Mark II "Master" ## File: comms.py  - Networking          ##
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

import socket
import threading
import Queue
import time

import Slave

## CONSTANT PARAMETERS #########################################################

STD_BROADCAST_PORT  = 65000
STD_PERIOD = 0.4 # (second(s))

VERSION = "UDP_REVENGE"

## CLASS DEFINITION ############################################################

class Communicator:

	def __init__(self, knownMACs = None, 
		broadcastPort = STD_BROADCAST_PORT, periodSeconds = STD_PERIOD):
		""" ABOUT: Constructor for class Communicator. Parameter knownMACs is a
			list of MAC addresses of known Slaves, to which to connect automa-
			cally, as strings. (This parameter is optional.)
			Parameter periodSeconds determines the time between MOSI messages
			and the MISO timeout: Under normal operating conditions, one period
			should be the time between one MOSI command and a subsequent MISO
			reply, which means the socket timeouts will be set to HALF the given
			period.
		"""

		print "[C] Initializing Communicator instance"

		# INITIALIZE DATA MEMBERS ==============================================

		self.periodSeconds = periodSeconds

		self.broadcastPort = broadcastPort

		self.slaves = {} 
			# ABOUT: This dictionary stores information of all Slaves known to
			# this Communicator instance, w/ MACaddresses as keys.

		# Check if a list of known MAC addresses is given:
		if knownMACs is not None:
			# Store information as "known" Slaves:
			for macAddress in knownMACs:
				self.slaves[macAddress] = Slaves.Slave(
					mac = macAddress, 
					status = Slaves.KNOWN,
					lock = threading.Lock())
		
		# Create lock for thread-safe access to self.slaves:
		self.slavesLock = threading.Lock()

		# Create a temporary socket to obtain Master's IP address for reference:
		temp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		temp.connect(('192.0.0.8', 1027))
		self.hostIP = temp.getsockname()[0]
		temp.close()

		print "[C]\tHost IP: {}".format(self.hostIP)

		# INITIALIZE MASTER SOCKETS ============================================

		# INITIALIZE LISTENER SOCKET -------------------------------------------

		# Create listener socket:
		self.listenerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


		# Configure socket as "reusable" (in case of improper closure): 
		self.listenerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		# Bind socket to "nothing" (Broadcast on all interfaces and let system 
		# assign port number):
		self.listenerSocket.bind(("", 0))

		print "[C]\tlistenerSocket initialized on " + \
			str(self.listenerSocket.getsockname())

		self.listenerPort = self.listenerSocket.getsockname()[1]

		# INITIALIZE BROADCAST SOCKET ------------------------------------------

		# Create broadcast socket:
		self.broadcastSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		# Configure socket as "reusable" (in case of improper closure): 
		self.broadcastSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		# Configure socket for broadcasting:
		self.broadcastSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

		# Bind socket to "nothing" (Broadcast on all interfaces and let system 
		# assign port number):
		self.broadcastSocket.bind(("", 0))

		self.broadcastSocketPort = self.broadcastSocket.getsockname()[1]

		print "[C]\tbroadcastSocket initialized on " + \
			str(self.broadcastSocket.getsockname())


		# INITIALIZE SPECIFIC SOCKET ------------------------------------------
			# ABOUT: The sniper socket is to be used to contact known Slaves to
			# secure a connection. See self._specificBroadcast() Method.

		# Create socket:
		self.specificSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		# Configure socket for broadcasting:
		self.specificSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

		# Configure socket as "reusable" (in case of improper closure): 
		self.specificSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		# Bind socket to "nothing":
		self.specificSocket.bind(("", 0))

		print "[C]\tspecificSocket initialized on " + \
			str(self.specificSocket.getsockname())


		# SET UP MASTER THREADS ================================================

		# INITIALIZE BROADCAST THREAD ------------------------------------------

		# Configure sentinel value for broadcasts:
		self.broadcastSwitch = True
			# ABOUT: UDP broadcasts will be sent only when this switch is True
		self.broadcastSwitchLock = threading.Lock() # for thread-safe access

		self.broadcastThread =threading.Thread(
			name = "FanclubMk2_broadcast",
			target = self._broadcastRoutine,
			args = ["{},fcmkii".format(self.listenerPort) ] )

		# Set thread as daemon (background task for automatic closure):
			# NOTE: A better approach, to be taken in future versions, is to use
			# events and/or signals to trigger cleanup measures.
		self.broadcastThread.setDaemon(True)

		# INITIALIZE LISTENER THREAD -------------------------------------------

		self.listenerThread =threading.Thread(
			name = "FanclubMk2_listener",
			target = self._listenerRoutine)

		# Set thread as daemon (background task for automatic closure):
			# NOTE: A better approach, to be taken in future versions, is to use
			# events and/or signals to trigger cleanup measures.
		self.listenerThread.setDaemon(True)

		# START MASTER THREADS =================================================

		self.listenerThread.start()


	# # END __init__() # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


	# # THREAD ROUTINES # # # # # # # # # # # # # # # # # # # # # # # # # # # #  

	def _broadcastRoutine(self, broadcastMessage,
		broadcastPeriod = STD_PERIOD): # =======================================
		""" ABOUT: This method is meant to run inside a Communicator instance's
			broadcastThread.
		"""

		broadcastSocketPortCopy = self.broadcastSocketPort # For thread safety

		print "[C]\tBroadcast thread started w/ period of {} second(s)"\
			.format(broadcastPeriod)

		print "[C]\t\tBroadcasting \"{}\""\
			.format(broadcastMessage)

		while(True):

			# Wait designated period:
			time.sleep(broadcastPeriod)

			self.broadcastSwitchLock.acquire()
			try:
				# Send broadcast only if self.broadcastSwitch is set to True:
				if broadcastSwitch:
					# Broadcast message:
					self.broadcastSocket.sendto(broadcastMessage, 
						("<broadcast>", broadcastSocketPortCopy))
			finally:
				# Guarantee lock release:
				self.broadcastSwitchLock.release()

	# End _broadcastRoutine ====================================================

	def _listenerRoutine(self): # ==============================================
		""" ABOUT: This method is meant to run within an instance's listener-
			Thread. It will wait indefinitely for messages to be received by
			the listenerSocket and respond accordingly.
		"""

		print "[C]\tListener thread started. Waiting."

		while(True):

			# Wait for a message to arrive:
			messageReceived, senderAddress = self.listenerSocket.recvfrom(256)

			print "[C][LR] \"{}\" received from {}".\
				format(messageReceived, senderAddress)

			""" NOTE: The message received from Slave, at this point, should ha-
				ve the following form:

								"MISOP,MOSIP,SL:MA:CA:DD:RE:SS"

				Where MISOP and MOSIP are the Slave's MISO and MOSI port numb-
				ers, respectively.
			"""

			messageSplitted = messageReceived.split(",")
				# NOTE: messageSplitted is a list of strings, each of which is
				# expected to contain a string as defined in the comment above.

			# Validate message -------------------------------------------------

			try:

				# Attempt conversion into corresponding containers:
				misoPort = int(messageSplitted[0])
				mosiPort = int(messageSplitted[1])
				mac = messageSplitted[2]
				# A ValueError will be raised if invalid port numbers are given
				# and an IndexError will be raised if the given message yields 
				# less than three strings when splitted.

				# Verify converted values:
				if (misoPort <= 0 or misoPort > 65535):
					# Raise a ValueError if a port number is invalid:
					raise ValueError("Given MISO port number ({}) outside of\
						acceptable range [1, 65535]".format(miso))

				if (mosiPort <= 0 or mosiPort > 65535):
					# Raise a ValueError if a port number is invalid:
					raise ValueError("Given MOSI port number ({}) outside of\
						acceptable range [1, 65535]".format(mosi))

				if (len(mac) != 17):
					# Raise a ValueError if the given MAC address is not 17
					# characters long.
					raise ValueError("Given MAC ({}) is not 17 characters long\
						, but {}")


			except ValueError, IndexError as e:

				# If the given message is invalid, discard it and move on:

				print "[C][LR] Error: \"{}\"\n Obtained when parsing \"{}\" \
				from {}. (Message discarded)"\
				.format(e, messageReceived, senderAddress)

				# Move on:
				continue

			# Check Slave against self.slaves and respond accordingly ----------
				# (Message validation completed successfully by this point)

			try:
				# (NOTE: try/finally clause guarantees lock release)

				# Acquire lock:
				self.slavesLock.acquire()

				# Check if the Slave is known:
				if(mac in self.slaves):
					# If the MAC address is in the Slave dictionary, check its re-
					# corded status and proceed accordingly:

					try:
						# Acquire Slave-specific lock:
						self.slaves[mac].lock.acquire()

						# Retrieve status for consecutive uses:
						status = self.slaves[mac].status 

						if (status == Slave.KNOWN or
							status == Slave.DISCONNECTED):
							# ABOUT: 
							#
							# - KNOWN Slaves have been approved by the user and
							#	should be connected to automatically.
							#
							# - DISCONNECTED Slaves were previously connected to
							#	and later anomalously disconnected. Since have
							#	been chosen by the user, they should be recon-
							#	nected to automatically.


							# Update status and networking information:
							self.slaves[mac].ip = senderAddress[0]
							self.slaves[mac].miso = misoPort
							self.slaves[mac].mosi = mosiPort
							self.slaves[mac].status = Slave.KNOWN

							# Connect:
							self.connect(mac)

							pass

						elif(status == Slave.CONNECTED):
							# ABOUT:
							#
							# - CONNECTED Slaves are not supposed to respond to
							#	this socket and, therefore, this message implies
							#	an error and a need to reconnect.

							# Send "end of communications" message:
							self.slaves[mac].mosi.send("RIP")

							# End thread:
							self.slaves[mac].status = Slave.DISCONNECTED

							print "[C][LR] Reconnecting to \"{}\"".format(mac)

							print "[C][LR]\tJoining thread"
							self.slaves[mac].thread.join()
							print "[C][LR]\t...Done"

							self.slaves[mac].thread = None

							# Terminate Queues:

							while not self.slaves[mac].mosiQueue.empty():
								self.slaves[mac].mosiQueue.get()
								self.slaves[mac].mosiQueue.task_done()

							print "[C][LR]\tJoining mosiQueue"
							self.slaves[mac].mosiQueue.join()
							print "[C][LR]\t...Done"

							while not self.slaves[mac].misoQueue.empty():
								self.slaves[mac].misoQueue.get()
								self.slaves[mac].misoQueue.task_done()

							print "[C][LR]\tJoining misoQueue"
							self.slaves[mac].misoQueue.join()
							print "[C][LR]\t...Done"


							self.slaves[mac].mosiQueue = None
							self.slaves[mac].misoQueue = None

							print "[C][LR]\tTerminating sockets"

							# Terminate sockets:
							self.slaves[mac].miso.shutdown(2)
							self.slaves[mac].mosi.shutdown(2)

							self.slaves[mac].miso.close()
							self.slaves[mac].miso.close()

							# Update status and networking information:
							self.slaves[mac].ip = senderAddress[0]
							self.slaves[mac].miso = misoPort
							self.slaves[mac].mosi = mosiPort
							self.slaves[mac].status = Slave.KNOWN

							print "[C][LR]\tDone disconnecting. Reconnecting..."

							# Connect:
							self.connect(mac)

						else:
							# ABOUT: The remaining statuses (AVAILABLE, BLOCKED)
							# indicate a connection should not be attempted by
							# Master, until subsequently indicated by the user.

							# Update networking information:
							self.slaves[mac].ip = senderAddress[0]
							self.slaves[mac].miso = misoPort
							self.slaves[mac].mosi = mosiPort

							continue

					finally:

						# Ensure Slave-specific lock release:
						self.slaves[mac].lock.release()


				else:
					# If the MAC address is not recorded, list this board as A-
					# VAILABLE and move on. The user may choose to add it later:

					# NOTE: Slaves that are not connected will have either port
					# numbers or None as their "miso" and "mosi" attributes.
					# When a connection is secured, these port numbers will be
					# replaced by UDP sockets CONNECTED to said port numbers --
					# notice: CONNECTED, not BINDED.

					# Create a new Slave instance and store it:
					self.slaves[mac] = Slave.Slave(
						mac = mac, 				# MAC address
						status = Slave.AVAILABLE, 	# Status
						ip = senderAddress[0], 	# IP address
						lock = threading.Lock(),
						miso = misoPort, 	# Master in/Slave out port number
						mosi = mosiPort		# Slave in/Master out port number
						)

					print "[C][LR] New Slave detected ({}) on:\
						\n\tIP: {}\
						\n\tMISO PORT: {}\
						\n\tMOSI PORT: {}"\
						.format(mac, senderAddress[0], misoPort, mosiPort)


			finally:

				# Lock will always be released:
				self.slavesLock.release()
			
	# End _listenerRoutine =====================================================


	def _slaveRoutine(self, targetMAC, mosiMasterPort):
		# ABOUT: This method is meant to run on a Slave's communication-handling
		# thread. It handles sending and receiving messages through its MISO and
		# MOSI sockets, at a pace dictated by the Communicator instance's given
		# period. Parameter targetMAC is the MAC address of the Slave handled by
		# this thread. Parameter mosiMasterPort is the port number of the MOSI
		# socket in the particular connection handled by this thread. If the MO-
		# SI socket used by the Slave w/ targetMAC changes, this thread is to be
		# replaced and will end automaticallys.
		#
		# NOTE: This current version is designed to run as daemon.

		print "[C][ST] Slave \"{}\" thread started".format(targetMAC)

		while(True):

			# Acquire Slave-specific lock:
			if self.slaves[targetMAC].lock.acquire(False):
				# NOTE: This call is non-blocking, which means this thread will
				# not wait for the lock to become available if it isn't. Ins-
				# tead, this thread will check the Slave's recorded status and
				# if it is no longer connected, then this thread must finish its
				# execution.

				try:
					
					# Check connection status: . . . . . . . . . . . . . . . . .

					if(self.slaves[targetMAC].status == Slave.DISCONNECTED or 
						type(self.slaves[targetMAC].mosi)\
													!= socket._socketobject or
						self.slaves[targetMAC].mosi.getsockname()[1] \
						!= mosiMasterPort):

						# If this Slave has been marked as DISCONECTED or is in
						# a new connection, this thread should shut down.

						print "[C][ST] Slave \"{}\" thread: Connection change \
							detected. Ending thread".format(targetMAC)

						break

					# (Connection verified by this point.)

					# Get message to be sent: . . . . . . . . . . . . . . . . . 

					message = "V {} MOSI".format(targetMAC)
						# NOTE: this standardized message will be sent in the
						# absence of a specific message in the queue. Its purpo-
						# se is to verify the connection.

					if not self.slaves[targetMAC].queue.empty():
						# If there is a message waiting to be sent, retrieve it:
						message = self.slaves[targetMAC].queue.get_nowait()
							# NOTE: Queue method get_nowait() will raise
							# Queue.Empty if there is no item to retrieve. 
							# The presence of such item has just been verified,
							# so no exception handling is done at this point.

					# Send message . . . . . . . . . . . . . . . . . . . . . . .

					# Send message:
					self.slaves[targetMAC].mosi.send(message)
						# By now, after the verification steps above, it is as-
						# sumed that the "mosi" attribute is a working socket.
					
					# Mark item as handled (for Queue):
					self.slaves[targetMAC].queue.task_done()

					# Receive reply: . . . . . . . . . . . . . . . . . . . . . .

					try:
						reply = self.slaves[targetMAC].miso.recvfrom(256)

					except socket.timeout:

						# TODO: Implement me pls









				finally:

					# Guarantee release of Slave-specific lock
					self.slaves[targetMAC].lock.release()

			elif self.slaves[targetMAC].status != Slave.CONNECTED:
				# If this Slave is no longer registered as connected, then
				# the connection handled by this thread has ended, and this
				# thread should therefore end.

				# WARNING: The above read operation (to check Slave's status)
				# is done w/o acquiring lock, and thus relies on the atomici-
				# ty of said operation (See Python's Global Interpreter Lock).
				# Beware of portability issues when using nonstandard versions
				# of Python.

				print "[C][ST] Slave \"{}\" connection change detected"\
				.format(targetMAC)

				break

			else:
				# If the Slave is still connected, try to acquire lock again.
				pass

		print "[C][ST] Slave \"{}\" thread ended".format(targetMAC)
			
	

	# # AUXILIARY METHODS # # # # # # # # # # # # # # # # # # # # # # # # # # #
		# ABOUT: These methods are to be used within this class. For methods to
		# be accessed by the user of a Communicator instance, see INTERFACE ME-
		# THODS below.


	def _specificBroadcast(self, targetMAC): # =================================
		""" ABOUT: Given the MAC address of a known Slave, send a "specific"
			UDP broadcast: one of the form "PORTN,MACADDRESS"  where PORTN is
			the port number of this instance's listenerSocket and MACADDRESS is
			the MAC address of said Slave. Only the targetted Slave, if present
			in the network, is programmed to respond to this broadcast.

			NOTE: A connected Slave board that receives a specific broadcast
			will terminate its existing connection and try to create a new one
			with the sender of said broadcast.
		"""
		print "[C] Sending specific broadcast to {}".format(targetMAC)

		self.specificSocket.sendto("{},{}".format(self.listenerPort,targetMAC),
			("<broadcast>",self.broadcastPort))

		print "[C] Sent specific broadcast to {}".format(targetMAC)

	# End _specificBroadcast ===================================================




	# # INTERFACE METHODS # # # # # # # # # # # # # # # # # # # # # # # # # # #


	def connect(self, targetMAC): # ============================================
		""" ABOVE: Given the MAC address of a known Slave, try to secure a
			connection. Read usage notes below.

			NOTE: This Slave is expected to be already recorded in self.slaves.
			FURTHERMORE this method assumes the given Slave has port numbers as
			its "miso" and "mosi" attributes, which will be replaced by sockets
			w/ corresponding functionality. Calling this method on a Slave that
			is CONNECTED, DISCONNECTED, or in any other state that has a socket
			or None in said attributes will result in a socket.error exception
			being raised. Modify these self.slaves entries before calling this
			method. (LIKEWISE, AN IP ADDRESS ATTRIBUTE IS ALSO EXPECTED.)
		"""

		"""	"HANDSHAKE" PROCESS: . . . . . . . . . . . . . . . . . . . . . . . .

			1. Master and Slave initialize their ethernet interfaces separately.
			2. Master sends UDP "general broadcast."
			3. Slave finds broadcast and sends reply to given listener socket.
			4. Master receives reply and lists Slave for user to choose.
			(*. The following steps happen within connect())
			5. Master reaches out to Slave using port numbers given in step 4.
				NOTE: In this step, Master sends its MISO and MOSI addresses.
			6. Slave receives message in MOSI socket and sends "ACK" to MISO.
			7. Master receives "ACK" from Slave, sends one last "ACK" and
				marks Slave as CONNECTED.

			NOTE: Errors in 5. and 6. will result in Slave being marked as DIS-
			CONNECTED and its network attributes (ip, mosi and miso) set to
			None and "RIP" sent to Slave. In step 7, Slave may request verifica-
			tion by sending "VER" to MISO. Errors in previous steps will result
			in a new attempt in the next broadcast. Note that once a Slave is 
			chosen by the user, unless BLOCKED, Master will automatically go for
			reconnection whenever possible. Lastly, "errors" in this context re-
			fer solely to UDP messages being lost.
		
		. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 
		"""

		# Firstly, look up targetMAC in self.slaves:
			# NOTE: An IndexError will be raised if the given MAC address is
			# not recorded in self.slaves.

		print "[C][CN] Initiating connection to " + targetMAC

		self.slaves[targetMAC].lock.acquire()
		try:
			# NOTE: try/finally clause guarantees lock release.

			print "[C][CN]\tValidating network attributes..."

			# Validate networking attributes -----------------------------------
			if(type(self.slaves[targetMAC].miso) != int):
				# WARNING: IndexError will be raised here if there is no such
				# MAC address in self.slaves.

				print "[C][CN]\t\tERROR: bad MISO"
				# If the "miso" attribute is not an integer, raise an exception:
				raise socket.error("MISO attribute of {} is not int, but {}".\
			 		format(targetMAC, type(self.slaves[targetMAC].miso)))

			elif(type(self.slaves[targetMAC].mosi) != int):

				print "[C][CN]\t\tERROR: bad MOSI"
				# If the "mosi" attribute is not an integer, raise an exception:
				raise socket.error("MOSI attribute of {} is not int, but {}".\
					format(targetMAC, type(self.slaves[targetMAC].mosi)))

			elif(type(self.slaves[targetMAC].ip) != str):

				print "[C][CN]\t\tERROR: bad IP"
				# If the IP address attribute is not a string, raise an excep-
				# tion:
				raise socket.error("IP address attribute of {} is not\
					 a string, but {}".\
					format(targetMAC, type(self.slaves[targetMAC].ip)))


			print "[C][CN]\tNetwork attributes successfully validated"
			# Once networking attributes have been validated, proceed to secure
			# a connection:

			# Create sockets ---------------------------------------------------


			print "[C][CN]\tCreating Master-side sockets"

			# Create prospective MISO and MOSI sockets:
			misoSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			mosiSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

			# Bind sockets to addresses:
			misoSocket.bind(("", 0))
			mosiSocket.bind(("", 0))

			print "[C][CN]\t\tMaster MISO: {}".format(misoSocket.getsockname())
			print "[C][CN]\t\tMaster MOSI: {}".format(mosiSocket.getsockname())

			# Set addresses as "reusable" in case of improper closure:
			misoSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			mosiSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

			# Set a timeout for message reception:
			misoSocket.settimeout(self.periodSeconds/2)
			mosiSocket.settimeout(self.periodSeconds/2)

			# Secure connection ------------------------------------------------

			print "[C][CN]\tSecuring connection..."

			# Send standard connection message to Slave's MOSI socket:
			# 	NOTE: A message of the following form will cause the receiving
			#	Slave to secure a connection with this Master, when sent to its
			#	MOSI socket:
			#					MISOP,MOSIP,SL:MA:CA:DD:RE:SS,PPPP
			#
			# Where MISOP and MOSIP are the >MASTER'S< Master in/Slave out and
			# Master out/Slave in sockets, respectively, followed by the tar-
			# getted Slave's MAC address and, lastly, the "period" of the ex-
			# change. The Slave will validate this message and reply to Master's
			# MISO socket, in which case communications will be secured.
			#
			# Use Master's MOSI socket w/ given Slave MOSI port and Slave IP
			# to send message:
			#
			# Connect Master's MOSI socket to Slave's MOSI socket's address:
			mosiSocket.connect(
				(self.slaves[targetMAC].ip, self.slaves[targetMAC].mosi))

			# Connect Master's MISO socket to Slave's MISO socket's address:
			misoSocket.connect(
				(self.slaves[targetMAC].ip, self.slaves[targetMAC].miso))

			# Attempt a connection:

			attempts = 2
			attemptsLeft = attempts
			success = False # How optimistic

			while(attemptsLeft > 0)
				try:
					attemptsLeft = attemptsLeft-1 

					print "[C][CN]\t\tAttempting connection ({}/{})".\
						format(attempts - attemptsLeft, attempts)

					# Format message to be sent:
					message = "{},{},{},{}".format(
						misoSocket.getsockname()[1], 
						mosiSocket.getsockname()[1],
						targetMAC,
						self.periodSeconds*1000)

						# NOTE: See message standard above.

						# NOTE: getsockname() returns a socket's address
						# as a tuple of the form (IP, PORTN).

					# Send message through MOSI:


					print "[C][CN]\t\t\tSending \"{}\"".format(message)

					mosiSocket.send(message)

					# Wait for reply:

					print "[C][CN]\t\t\tWaiting..."
					
					messageReceived, senderAddress = misoSocket.recv(3)

					print "[C][CN]\t\t\t\"{}\" Received from {}"\
						.format(messageReceived, senderAddress)

					# Validate message received:
					if (messageReceived == "ACK"):
						mosiSocket.send("ACK")
					else:
						raise socket.timeout("Bad ACK")

					# Signal success and break out of loop:
					success = True
					break

				except socket.timeout as e:

					print "[C][CN]\t\t\tERROR: {}".format(e)
					continue
			
			# Check success:
			if success:

				print "[C][CN]\t\tConnection secured"

				# If the connection was secured successfully, update this Slave
				# accordingly:
				self.slaves[targetMAC].miso = misoSocket
				self.slaves[targetMAC].mosi = mosiSocket
				self.slaves[targetMAC].status = Slave.CONNECTED

				# Add comms handling thread and queues:

				self.slaves[targetMAC].misoQueue = Queue.Queue(1)
					# ABOUT: Created a 1-item FIFO queue

				self.slaves[targetMAC].mosiQueue = Queue.Queue(1)
					# ABOUT: Created a 1-item FIFO queue

				self.slaves[targetMAC].thread = threading.Thread(
					name = "FanclubMk2_slv_{}".format(targetMAC),
					target = self._slaveRoutine, args = [targetMAC, 
					mosiSocket.getsockname()[1]])

				self.slaves[targetMAC].thread.setDaemon(True)

					# ABOUT: Create and comms-handling thread, store it, and set
					# it as daemon.

				# Start comms-handling thread
				self.slaves[targetMAC].thread.start()

			else:

				print "[C][CN]\t\tConnection unsuccessful"

				# If a connection could not be secured, update this Slave accor-
				# dingly:
				self.slaves[targetMAC].miso = None
				self.slaves[targetMAC].mosi = None
				self.slaves[targetMAC].ip = None
				self.slaves[targetMAC].misoQueue = None
				self.slaves[targetMAC].mosiQueue = None
				self.slaves[targetMAC].thread = None
				self.slaves[targetMAC].status = Slave.DISCONNECTED



				# Send end of connection message to Slave's MOSI, in case Slave
				# interpretted the connection as secured:
				mosiSocket.send("RIP")

				# Shutdown and close sockets:

				mosiSocket.shutdown(2)
				misoSocket.shutdown(2)

				mosiSocket.close()
				misoSocket.close()

				# Another attempt will be made when this Slave responds to ano-
				# ther general broadcast.


		finally:
			self.slaves[targetMAC].lock.release()

		# End connect() ========================================================

		def setBroadcastSwitch(self, newState): # ==============================
			""" ABOUT: Set whether to send UDP broadcast. Parameter Switch is
				expected to be True or False. Otherwise, ValueError is raised.
			"""

			# Validate parameter:
			if (type(newState) == bool):
				# If input is valid, modify broadcast switch:
				self.broadcastSwitchLock.acquire()
				try:

					self.broadcastSwitch = newState

				finally:

					# Lock will always be released:
					self.broadcastSwitchLock.release()

			else:
				# Raise exception upon invalid input:
				raise ValueError("setBroadcastSwitch expects bool, not {}".\
					format(type(newState)))

		# End setBroadcastSwitch() =============================================

		def getBroadcastSwitch(self): # ========================================
			""" ABOUT: Get the current value of broadcastSwitch.
			"""

			self.broadcastSwitchLock.acquire()
			try:
				return self.broadcastSwitch
			finally:
				# Lock will always be released:
				self.broadcastSwitchLock.release()

		# End getBroadcastSwitch() =============================================


## MODULE'S TEST SUITE #########################################################

if __name__ == "__main__":

	print "FANCLUB MARK II COMMUNICATOR MODULE TEST SUITE INITIATED"
	print "VERSION = " + VERSION

	instance = Communicator()

	while (True):
		pass