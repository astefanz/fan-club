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
import time

import Slave

## CONSTANT PARAMETERS #########################################################

STD_BROADCAST_PORT  = 65000
STD_BROADCAST_PERIOD = 1 # (second(s))
STD_SOCKET_TIMEOUT = 1 # (second(s))

VERSION = "UDP_REVENGE"

## CLASS DEFINITION ############################################################

class Communicator:

	def __init__(self, knownMACs = None, broadcastPort = STD_BROADCAST_PORT):
		""" ABOUT: Constructor for class Communicator. Parameter knownMACs is a
			list of MAC addresses of known Slaves, to which to connect automa-
			cally, as strings. (This parameter is optional.)
		"""

		print "[C] Initializing Communicator instance"

		# INITIALIZE DATA MEMBERS ==============================================

		self.broadcastPort = broadcastPort

		self.slaves = {} 
			# ABOUT: This dictionary stores information of all Slaves known to
			# this Communicator instance, w/ MACaddresses as keys.

		# Check if a list of known MAC addresses is given:
		if knownMACs is not None:
			# Store information as "known" Slaves:
			for macAddress in knownMACs:
				self.slaves[macAddress] = Slaves.Slave(macAddress, Slaves.KNOWN)
		
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

		# Configure sentinel value for "graceful" thread death:
		self.broadcastSwitch = 2
			# ABOUT: Thread will end when this variable is allowed to go 1
		self.broadcastSwitchLock = threading.Lock() # for thread-safe access

		self.broadcastThread =threading.Thread(target = self._broadcastRoutine,
			args = ["{},fcmkii".format(self.listenerPort) ] )

		# Set thread as daemon (background task for automatic closure):
			# NOTE: A better approach, to be taken in future versions, is to use
			# events and/or signals to trigger cleanup measures.
		self.broadcastThread.setDaemon(True)

		# START MASTER THREADS =================================================

		self.broadcastThread.start()


	# # END __init__() # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


	# # THREAD ROUTINES # # # # # # # # # # # # # # # # # # # # # # # # # # # #  

	def _broadcastRoutine(self, broadcastMessage,
		broadcastPeriod = STD_BROADCAST_PERIOD): # =============================
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

			# Broadcast message:
			self.broadcastSocket.sendto(broadcastMessage, 
				("<broadcast>", broadcastSocketPortCopy))

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

					# Retrieve status for consecutive uses:
					status = self.slaves[mac].status 

					if (status == Slave.KNOWN or
						status == Slave.DISCONNECTED):
						# ABOUT: 
						#
						# - KNOWN Slaves have been approved by the user and
						#	should be connected to automatically.
						#
						# - DISCONNECTED Slaves were previosuly added during
						#	execution and later lost due to an anomaly. Since
						#	they were already chosen by the user, they should
						#	be reconnected automatically.


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
						#	an error. The Slave's connection should be reset.

						# If there is an obsolete connection with this Slave, terminate
						# it before reconnecting.

						# Send "end of communications" message:
						self.slaves[mac].mosi.send("RIP")

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

						# Connect:
						self.connect(mac)

					else:
						# ABOUT: The remaining statuses (AVAILABLE and BLOCKED)
						# indicate a connection should not yet be attempted by
						# Master, until otherwise indicated by the user.

						# Update networking information:
						self.slaves[mac].ip = senderAddress[0]
						self.slaves[mac].miso = misoPort
						self.slaves[mac].mosi = mosiPort

						continue



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
						mac, 				# MAC address
						Slave.AVAILABLE, 	# Status
						senderAddress[0], 	# IP address
						misoPort, 			# Master in/Slave out port number
						mosiPort			# Slave in/Master out port number
						)

					print "New Slave detected: \"{}\"".format(mac)


			finally:

				# Lock will always be released:
				self.slavesLock.release()







			
	# End _listenerRoutine =====================================================


	

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

		# Firstly, look up targetMAC in self.slaves:
			# NOTE: An IndexError will be raised if the given MAC address is
			# not recorded in self.slaves.

		print "[C][CN] Initiating connection to " + targetMAC

		self.slavesLock.acquire()
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
			misoSocket.settimeout(STD_SOCKET_TIMEOUT)
			mosiSocket.settimeout(STD_SOCKET_TIMEOUT)

			# Secure connection ------------------------------------------------

			print "[C][CN]\tSecuring connection..."

			# Send standard connection message to Slave's MOSI socket:
			# 	NOTE: A message of the following form will cause the receiving
			#	Slave to secure a connection with this Master, when sent to its
			#	MOSI socket:
			#					MISOP,MOSIP,SL:MA:CA:DD:RE:SS
			#
			# Where MISOP and MOSIP are the >MASTER'S< Master in/Slave out and
			# Master out/Slave in sockets, respectively, followed by the tar-
			# getted Slave's MAC address. The Slave will validate this message
			# and reply to Master's MISO socket, in which case communications
			# will be secured.

			# Use Master's MOSI socket w/ given Slave MOSI port and Slave IP
			# to send message:

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
					message = "{},{},{}".format(
						misoSocket.getsockname()[1], 
						mosiSocket.getsockname()[1],
						targetMAC)

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

			else:

				print "[C][CN]\t\tConnection unsuccessful"

				# If a connection could not be secured, update this Slave accor-
				# dingly:
				self.slaves[targetMAC].miso = None
				self.slaves[targetMAC].mosi = None
				self.slaves[targetMAC].ip = None
				self.slaves[targetMAC].status = Slave.DISCONNECTED

				# Send end of connection message to Slave's MOSI, in case Slave
				# interpretted the connection as secured:
				mosiSocket.send("RIP")
				mosiSocket.send("RIP") # Can't be too sure w/ UDP

				# Shutdown and close sockets:

				mosiSocket.shutdown(2)
				misoSocket.shutdown(2)

				mosiSocket.close()
				misoSocket.close()

				# Another attempt will be made when this Slave responds to ano-
				# ther general broadcast.


		finally:
			self.slavesLock.release()

		# End connect() ========================================================





## MODULE'S TEST SUITE ########################################################

if __name__ == "__main__":

	print "FANCLUB MARK II COMMUNICATOR MODULE TEST SUITE INITIATED"
	print "VERSION = " + VERSION

	instance = Communicator()

	while (True):
		pass