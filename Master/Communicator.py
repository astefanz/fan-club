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

import socket     # Networking
import threading  # Multitasking
import time       # Timing
import Queue
import sys        # Exception handling
import traceback  # More exception handling

import Profiler    # Custom representation of wind tunnel
import Slave
import Fan

VERSION = "GO_1"

## CLASS DEFINITION ############################################################

class Communicator:

	def __init__(self, profiler,\
		printMain, printSlave, printBroadcast, printListener, dataLog):
	#   \-----------------------------------------------------------/
	#	Interface methods

		# ABOUT: Constructor for class Communicator.
		# PARAMETERS:
		# - profiler: Initialized Profiler object from which to load configu-
		#	ration.
		# [See FCInterface for interface methods]

		try:
			printMain("Initializing Communicator instance")

			# INITIALIZE DATA MEMBERS ==============================================

			# Profiler, Interface, and their methods:
			self.profiler = profiler

			self.printM = printMain
			self.printS = printSlave
			self.printB = printBroadcast
			self.printL = printListener
			self.dataLog = dataLog

			# Wind tunnel:
			self.slaves = profiler.slaves
			self.slavesLock = profiler.slavesLock

			# Communications:
			self.broadcastPeriodS = profiler.get_broadcastPeriodS()
			self.periodMS = profiler.get_periodMS()
			self.broadcastPort = profiler.get_broadcastPort()
			self.password = profiler.get_password()

			# Create a temporary socket to obtain Master's IP address for reference:
			temp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			temp.connect(('192.0.0.8', 1027))
			self.hostIP = temp.getsockname()[0]
			temp.close()

			self.printM("\tHost IP: {}".format(self.hostIP))

			# INITIALIZE MASTER SOCKETS ============================================

			# INITIALIZE LISTENER SOCKET -------------------------------------------

			# Create listener socket:
			self.listenerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


			# Configure socket as "reusable" (in case of improper closure): 
			self.listenerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

			# Bind socket to "nothing" (Broadcast on all interfaces and let system 
			# assign port number):
			self.listenerSocket.bind(("", 0))

			self.printM("\tlistenerSocket initialized on " + \
				str(self.listenerSocket.getsockname()))

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

			self.printM("\tbroadcastSocket initialized on " + \
				str(self.broadcastSocket.getsockname()))


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

			self.printM("\tspecificSocket initialized on " + \
				str(self.specificSocket.getsockname()))


			# SET UP MASTER THREADS ================================================

			# INITIALIZE BROADCAST THREAD ------------------------------------------

			# Configure sentinel value for broadcasts:
			self.broadcastSwitch = True
				# ABOUT: UDP broadcasts will be sent only when this switch is True
			self.broadcastSwitchLock = threading.Lock() # for thread-safe access

			self.broadcastThread = threading.Thread(
				name = "FCMkII_broadcast",
				target = self._broadcastRoutine,
				args = ["00000000|{}|{}".format(self.password, 
							self.listenerPort), 
						self.broadcastPeriodS]
				)

			# Set thread as daemon (background task for automatic closure):
				# NOTE: A better approach, to be taken in future versions, is to use
				# events and/or signals to trigger cleanup measures.
			self.broadcastThread.setDaemon(True)

			# INITIALIZE LISTENER THREAD -------------------------------------------

			self.listenerThread =threading.Thread(
				name = "FCMkII_listener",
				target = self._listenerRoutine)

			# Set thread as daemon (background task for automatic closure):
				# NOTE: A better approach, to be taken in future versions, is to use
				# events and/or signals to trigger cleanup measures.
			self.listenerThread.setDaemon(True)

			# START MASTER THREADS =================================================

			self.listenerThread.start()
			self.broadcastThread.start()

			self.printM("\tCommunicator initialized", "G")

		except Exception as e: # Print uncaught exceptions
			self.printM("UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")


	# # END __init__() # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


	# # THREAD ROUTINES # # # # # # # # # # # # # # # # # # # # # # # # # # # #  

	def _broadcastRoutine(self, broadcastMessage, broadcastPeriod): # ==========
		""" ABOUT: This method is meant to run inside a Communicator instance's
			broadcastThread. 
		"""
		try: # Catch any exception for printing (have no stdout w/ GUI!)

			broadcastSocketPortCopy = self.broadcastSocketPort # Thread safety

			self.printB("Broadcast thread started w/ period of {} second(s)"\
				.format(broadcastPeriod), "G")

			self.printB("\tBroadcasting \"{}\""\
				.format(broadcastMessage))

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

						self.printB("Broadcast sent ({})".format(count))

				finally:
					# Guarantee lock release:
					self.broadcastSwitchLock.release()

		except Exception as e:
			self.printM("UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")

		# End _broadcastRoutine ================================================

	def _listenerRoutine(self): # ==============================================
		""" ABOUT: This method is meant to run within an instance's listener-
			Thread. It will wait indefinitely for messages to be received by
			the listenerSocket and respond accordingly.
		"""

		try:

			self.printL("Listener thread started. Waiting.", "G")

			while(True):

				# Wait for a message to arrive:
				messageReceived, senderAddress = self.listenerSocket.recvfrom(256)

				self.printL("\"{}\" received from {}".\
					format(messageReceived, senderAddress))

				""" NOTE: The message received from Slave, at this point, should ha-
					ve the following form:

						000000000|PASSWORD|SV:MA:CA:DD:RE:SS|SMISO|SMOSI| 

					Where SMISO and SMOSI are the Slave's MISO and MOSI port numb-
					ers, respectively. Notice separator.
				"""

				messageSplitted = messageReceived.split("|")
					# NOTE: messageSplitted is a list of strings, each of which is
					# expected to contain a string as defined in the comment above.

				# Validate message -------------------------------------------------

				try:

					# Verify password:
					if messageSplitted[1] != self.password:
						raise ValueError("Wrong password ({})".\
							format(messageSplitted[1]))

					# Attempt conversion into corresponding containers:
					misoPort = int(messageSplitted[3])
					mosiPort = int(messageSplitted[4])
					mac = messageSplitted[2]
					# A ValueError will be raised if invalid port numbers are given
					# and an IndexError will be raised if the given message yields 
					# less than three strings when splitted.

					self.printL("Parsed:\
								\n\t\t Password: {}\
								\n\t\t MAC: {}\
								\n\t\t MMISO: {}\
								\n\t\t MMOSI: {}".\
								format(
								messageSplitted[1],
								messageSplitted[2],
								messageSplitted[3],
								messageSplitted[4]))

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

					self.printL("Error: \"{}\"\n\tObtained when parsing \"\
						{}\" from {}. (Message discarded)"\
					.format(e, messageReceived, senderAddress))

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
						self.slaves[mac].lock.acquire()
						try:
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

							else:
								# ABOUT: The remaining statuses (AVAILABLE...)
								# indicate a connection should not be attempted by
								# Master, until subsequently indicated by the user.

								# Update networking information:
								self.slaves[mac].ip = senderAddress[0]
								self.slaves[mac].miso = misoPort
								self.slaves[mac].mosi = mosiPort

								continue

						finally:

							# Guarantee release of Slave-specific lock:
							self.slaves[mac].lock.acquire(False)
								#								 ^ Non-blocking
								#
								# Note: if the lock was released within the "try" clause
								# then this statement will prevent a threading exception
								# when an attempt to release an unlocked lock is made.
							
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

						# Create default list of fans:
						fList = []
						for i in range(21):
							fList.append(Fan.Fan(i+1, Fan.OFF))

						self.slaves[mac] = Slave.Slave(
							name = "Unnamed",
							mac = mac, 				# MAC address
							status = Slave.AVAILABLE, 	# Status
							fans = fList,
							activeFans = 21,
							ip = senderAddress[0], 	# IP address
							miso = misoPort, 	# Master in/Slave out port number
							mosi = mosiPort		# Slave in/Master out port number
							)

						self.printL("New Slave detected ({}) on:\
							\n\tIP: {}\
							\n\tMISO PORT: {}\
							\n\tMOSI PORT: {}"\
							.format(mac, senderAddress[0], misoPort, mosiPort),
							"G")


				finally:

					# Guarantee release of general Slave lock:
					self.slavesLock.acquire(False)
						#					  ^ Non-blocking
						#
						# Note: if the lock was released within the "try" clause
						# then this statement will prevent a threading exception
						# when an attempt to release an unlocked lock is made.
					
					self.slavesLock.release()

		except Exception as e: # Print uncaught exceptions
			self.printM("UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")
				
		# End _listenerRoutine =================================================


	def _slaveRoutine(self, targetMAC, mosiMasterPort):
		# ABOUT: This method is meant to run on a Slave's communication-handling
		# thread. It handles sending and receiving messages through its MISO and
		# MOSI sockets, at a pace dictated by the Communicator instance's given
		# period. 
		# PARAMETERS:
		# - targetMAC: String, MAC address of the Slave handled by
		#	this thread.
		# - mosiMasterPort: Int, port number of the MOSI socket in the particular 
		#	connection handled by this thread. If the MOSI socket used by the 
		#	Slave w/ targetMAC changes, this thread is to be replaced and will end 
		#	automatically.
		#
		# NOTE: This current version is expected to run as daemon.

		try:

			self.printS(targetMAC, "Slave thread started", "G")
			indexReset = False

			# Slave loop: ---------------------------------------------------------
			while(True):

				# Acquire Slave-specific lock:
				if self.slaves[targetMAC].lock.acquire(False):
					# NOTE: This call is non-blocking, which means this thread will
					# not wait for the lock to become available if it isn't. Ins-
					# tead, this thread will check the Slave's recorded status and,
					# if it is no longer connected, this thread will terminate.

					# Increase exchange index:
				 	self.slaves[targetMAC].exchange += 1
				 	if indexReset:
				 		self.slaves[targetMAC].exchange = 1
				 		indexReset = False

					try:
						
						# Check connection status: . . . . . . . . . . . . . . . . .

						if(self.slaves[targetMAC].status == Slave.DISCONNECTED or 
							type(self.slaves[targetMAC].mosi)\
														!= socket._socketobject or
							self.slaves[targetMAC].mosi.getsockname()[1] \
							!= mosiMasterPort):

							# If this Slave has been marked as DISCONECTED or is in
							# a new connection, this thread should shut down.

							self.printS(targetMAC,"[{}] Connection change \
								detected. Ending thread".format( 
									self.slaves[targetMAC].exchange))

							break

						# Get message to be sent: . . . . . . . . . . . . . . . . . 

						try:

							# Check for index limit:
							if self.slaves[targetMAC].exchange >= 99999998: 
								# If indices need resetting, use this exchange:
								message = "{0:08d}|MRES".\
								format(self.slaves[targetMAC].exchange)
								command = "MRES"
								indexReset = True

								self.printS(targetMAC, "[{}] Resetting indices."\
									.format(self.slaves[targetMAC].exchange))


								# Otherwise...
							else:
								# If there is a message waiting to be sent, 
								# retrieve it:
								command = self.slaves[targetMAC].mosiQueue.\
									get_nowait()
								message = "{0:08d}|MSTD|{}".\
									format(self.slaves[targetMAC].exchange, command)

								# Mark task as done:
								self.slaves[targetMAC].mosiQueue.task_done()

						except Queue.Empty:
							# If there is no message to be sent, send verification 
							# message to maintain the connection:
							message  = "{0:08d}|MVER".format(
								self.slaves[targetMAC].exchange)
							command  = None

						# Send message . . . . . . . . . . . . . . . . . . . . . . .

						# Send message:
						self.slaves[targetMAC].mosi.send(message)
							# By now, after the verification steps above, it is as-
							# sumed that the "mosi" attribute is a working socket.
						
						self.printS(targetMAC, "[{}] Sent: {}".format(
							self.slaves[targetMAC].exchange,
							message))

						# Check if connection was terminated by Master:
						if command == "MRIP":

							self.printS(targetMAC, "[{}] MRIP found in MOSI. Terminating.".format(
							self.slaves[targetMAC].exchange))

							# Terminate connection:
							self.disconnect(targetMAC, False)
								# NOTE: Second argument indicates Slave's thread
								# (this thread) should not be terminated within
								# the method.

							# Exit loop to end thread:
							break

						# Reply loop: . . . . . . . . . . . . . . . . . . . . . . . 

						# For each exchange, two messages should be received from 
						# this Slave -- an acknowledgement message, and a reply.

						# Set up sentinel variables for reply loop:
						tries = 3
							# Try to receive messages a limited amount of times.

						remainConnected = False
							# Check this variable after the loop to know whether to
							# remain connected to this Slave.

						mAcknowledged = False
							# Keep track of whether an acknowledgement message was
							# received for this exchange.

						while(tries > 0):

							tries -= 1

							try:

								# Receive a message. Ignore any messages with outda-
								# ted indices:

								receivedIndex = 0

								# Receive loop: .  .  .  .  .  .  .  .  .  .  .  . 

								""" ------------------------------------------------
								NOTE: The messages received here are expected to ha-
								ve the following general form:

										INDEX|KEYWORD|ARGUMENT|RPMS|DUTYCYCLES
											0		1		2	  3			4

								Where INDEX is expected to match the local variable
								index and every '|' is a separator. The shortest va-
								lid form is 

										INDEX|KEYWORD
											0		1

								------------------------------------------------ """

								# NOTE: This loop will be exited in one of two ways:
								#
								# (1) A correctly indexed, correctly splittable mes-
								#	  sage is received.
								#
								# (2) A socket timeout exception.

								while(receivedIndex != 
									self.slaves[targetMAC].exchange):

									received = self.slaves[targetMAC].\
										miso.recv(512)

									self.printS(targetMAC, "[{}] Received: {}".\
										format( 
										self.slaves[targetMAC].exchange, received))

									# Split message:
									receivedSplitted = received.split("|")
									self.printS(targetMAC, "[{}] Splitted: \n\t\t\tIndex: {}\n\t\t\tKeyword: {}".\
										format( 
										self.slaves[targetMAC].exchange, receivedSplitted[0], receivedSplitted[1]))


									# Check index:
									try:
										receivedIndex = int(receivedSplitted[0])

										if receivedIndex != \
											self.slaves[targetMAC].exchange:
											self.printS(targetMAC, "[{}] Index mismatch ({}). Discarded.".\
											format(self.slaves[targetMAC].exchange, receivedIndex))

											# Discard this message and get another:
											continue

										else:

											# Check length:
											if len(receivedSplitted) < 2:
												# By this convention, 
												# receivedSplitted should never ha-
												# ve length smaller than 2.

												self.printS(targetMAC, "[{}] WARNING: Invalid message size. Discarded".\
													format(
													self.slaves[targetMAC].exchange
													))

												# Discard this message, get another:
												continue

											else:
												# At this point, it is reasonable to
												# assume this message corresponds to
												# this exchange. 

												# Break out of receive loop to pro-
												# cess this message:
												self.printS(targetMAC, "[{}] Message size and index validated".\
													format(
													self.slaves[targetMAC].exchange
													), "G")

												break

									except ValueError:
										self.printS(targetMAC, "[{}] WARNING: Invalid \
											message contents (expected index). \
											Discarded.".\
											format(self.slaves[targetMAC].exchange),
											"W")

										# Discard this message and get another:
										continue

									except IndexError:
										self.printS(targetMAC, "[{}] WARNING: Invalid \
											message contents (IndexError). \
											Discarded.".\
											format(self.slaves[targetMAC].exchange),
											"W")

										# Discard this message and get another:
										continue

									# End receive loop .  .  .  .  .  .  .  .  .  . 

								# Check keywords:
								keyword = receivedSplitted[1]

								self.printS(targetMAC, "[{}] Parsed keyword: \"{}\"".\
									format(self.slaves[targetMAC].exchange, keyword))

								# Check for acknowledgement message .  .  .  .  
								if keyword == "SACK":
									# Acknowledgement received as expected.
									self.printS(targetMAC, "[{}] Message acknowledged"\
										.format(self.slaves[targetMAC].exchange))

									mAcknowledged = True

									# Add one more "try" to this loop:
									tries += 1

									# Loop again:
									continue

								else:
									# If the reply received is not an acknow-
									# ledgement message from Slave, then it is a 
									# message and should be acknowledged.

									# Acknowledge command:
									self.slaves[targetMAC].mosi.\
										send("{0:08d}|MACK".format(
											self.slaves[targetMAC].exchange))								


								# Check for disconnect message: .  .  .  .  .  .

								if keyword == "SRIP":
									# "Connection terminated."

									# Check for optional error message:
									try:

										self.printS(targetMAC, "[{}] WARNING. \
											SLAVE DISCONNECTED:\n\t \"{}\""\
											.format(self.slaves[targetMAC].exchange,
												receivedSplitted[2]), "W")

									except IndexError:
										# If there is no message to be printed,
										# proceed:
										self.printS(targetMAC, "[{}] WARNING. \
											SLAVE DISCONNECTED."\
											.format(self.slaves[targetMAC].exchange
												), "W")

										pass


									# Break out of reply loop with 
									# remainConnected as False:

									remainConnected = False
									break
 
								# Check for standard messages and error codes:
								# .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .

								elif keyword == "SRDY":
									# "Command completed."

									# Set status to CONNECTED to accept new com-
									# mands:
									self.slaves[targetMAC].status = \
										Slave.CONNECTED

									remainConnected = True

								elif keyword == "BUSY":
									# "Busy executing command."

									# Set status to BUSY to block new commands
									# until completion.

									self.slaves[targetMAC].status = \
										Slave.BUSY

									remainConnected = True

								elif keyword == "CERR":
									# "Command error."

									# Print error message and proceed w/ loop.
									# Do not disconnect:

									self.printS(targetMAC, "[{}] WARNING. \
										COMMAND ERROR:\n\t \"{}\""\
										.format(self.slaves[targetMAC].exchange, 
											receivedSplitted[2]), "W")

									# Since no command is being executed, list
									# Slave as CONNECTED (not BUSY):
									self.slaves[targetMAC].status = \
										Slave.CONNECTED

								if keyword == "SERR":
									# "Slave error."

									# Print error message and proceed w/ loop.
									# Do not disconnect:

									self.printS(targetMAC, "[{}] WARNING. SLAVE ERROR:\
										\n\t \"{}\""\
										.format(self.slaves[targetMAC].exchange, 
											receivedSplitted[2]), "W")

									# Do not extract DC's nor RPM's in this 
									# case, but do not terminate connection,
									# either:
									remainConnected = True
									break

								# Done processing keyword and optional argument.
								# Proceed w/ data feedback (DC & RPM):

								# Extract updated DC's and RPM's:
								rpms = receivedSplitted[2].split("~")
								dcs = receivedSplitted[3].split("~")

								# Validate:
								self.printS(targetMAC, "[{}] Parsed lists:\
										\n\tRPM: {}\
										\n\tDC:  {}"
										.format(self.slaves[targetMAC].exchange, 
											rpms,dcs))

								# The following statements will raise an 
								# indexError if this reply contains less RPM's
								# and/or duty cycles than the Slave's number of
								# active fans.
								rpms[self.slaves[targetMAC].activeFans]
								dcs[self.slaves[targetMAC].activeFans]
								
								# Send data to dataLog:
								self.dataLog(targetMAC, rpms, dcs)

								# Set sentinel value to maintain connection 
								# after this loop:

								remainConnected = True

								# Finish loop:
								break # Out of reply loop


							except socket.timeout:

								# Check if the message was acknowledged:
								if not mAcknowledged:
									# Resend message:
									self.slaves[targetMAC].mosi.send(message)
							
									self.printS(targetMAC, "[{}] WARNING: Missed acknowledgement message. Message resent".\
										format(self.slaves[targetMAC].exchange), "W")

									continue

								else:
									# If the message was acknowledged, continue w/
									# loop, which will automatically terminate w/
									# "too many" timeouts.

									self.printS(targetMAC, "[{}] WARNING: Time out reached ({} Attempt(s) left)".\
										format(self.slaves[targetMAC].exchange, tries), "W")

									continue

							except IndexError:

								# An IndexError is raised if the received message
								# is missing expected components.

								self.printS(targetMAC, "[{}] WARNING: IndexError. Invalid message ({})".\
									format(self.slaves[targetMAC].exchange, received)\
									,"W")

								# Discard message, but do not end connection:
								remainConnected = True
								break # Out of reply loop

						# End reply loop .  .  .  .  .  .  .  .  .  .  .  .  .  . 

						# Check sentinel variable: .  .  .  .  .  .  .  .  .  .  .  
						
						if remainConnected:

							# Resume loop (next exchange):
							continue

						else:

							self.printS(targetMAC, "\"remainConnected\" flag set to False", "W")

							# Terminate connection:
							self.disconnect(targetMAC, False)
								# NOTE: Second argument indicates Slave's thread
								# (this thread) should not be terminated within
								# the method.

							# Terminate loop:
							break

					finally:

						# Guarantee release of Slave-specific lock:
						self.slaves[targetMAC].lock.acquire(False)
							#								 ^ Non-blocking
							#
							# Note: if the lock was released within the "try" clause
							# then this statement will prevent a threading exception
							# when an attempt to release an unlocked lock is made.
						self.slaves[targetMAC].lock.release()

				elif self.slaves[targetMAC].status <= 0:
					# If this Slave is no longer registered as connected, then
					# the connection handled by this thread has ended, and this
					# thread should therefore end.

					# WARNING: The above read operation (to check Slave's status)
					# is done w/o acquiring lock, and thus relies on the atomici-
					# ty of said operation (See Python's Global Interpreter Lock).
					# Beware of portability issues when using nonstandard versions
					# of Python.

					self.printS(targetMAC, "[{}] Connection change detected."\
					.format(self.slaves[targetMAC].exchange), "W")

					break

				else:
					# If the Slave is still connected, try to acquire lock again.
					pass

			# End Slave loop -------------------------------------------------------

			self.printS(targetMAC,"[{}] Slave thread ended."\
					.format(self.slaves[targetMAC].exchange), "W")

		except Exception as e: # Print uncaught exceptions
			self.printM("UNCAUGHT EXCEPTION: \"{}\"".\
				format(traceback.format_exc()), "E")

		# End _slaveRoutine ====================================================
	

	# # AUXILIARY METHODS # # # # # # # # # # # # # # # # # # # # # # # # # # #
		# ABOUT: These methods are to be used within this class. For methods to
		# be accessed by the user of a Communicator instance, see INTERFACE ME-
		# THODS below.


	def connect(self, targetMAC): # ============================================M
		# ABOUT: Given the MAC address of a known Slave, try to secure a
		# connection. Read usage notes below.
		#
		# PARAMETERS:
		# - targetMAC: MAC address of Slave to which to connect.
		#
		# NOTE: This Slave is expected to be already recorded in self.slaves.
		# FURTHERMORE this method assumes the given Slave has port numbers as
		# its "miso" and "mosi" attributes, which will be replaced by sockets
		# w/ corresponding functionality. Calling this method on a Slave that
		# is CONNECTED, DISCONNECTED, or in any other state that has a socket
		# or None in said attributes will result in a socket.error exception
		# being raised. Modify these self.slaves entries before calling this
		# method. (LIKEWISE, AN IP ADDRESS ATTRIBUTE IS ALSO EXPECTED.)
		#
		# If the constraints outlined above are not met, ValueError is raised.
		# (If a non-listed Slave is requested, KeyError is raised)

		# WARNING: THIS METHOD ACCESSES SHARED RESOURCES WITHOUT ACQUIRING THEIR
		# RESPECTIVE LOCKS. THIS IS BECAUSE IT IS ONLY MEANT TO BE USED WITHIN
		# COMMUNICATOR THREADS THAT WILL ONLY CALL IT AFTER ACQUIRING SAID LOCKS
		# AND BEFORE RELEASING THEM.

		"""	"HANDSHAKE" PROCESS: . . . . . . . . . . . . . . . . . . . . . . . .
			
			FIRST EXCHANGE:
			-M: Send MMISO and MMOSI port numbers and communication "period" to 
				S's SMOSI
			-S: Receive. Stop listening for broadcasts
			-S: Reply w/ confirmation
				(By now all four sockets are verified (MOSI pair and MISO pair))
			-M: Receive
			
			SECOND EXCHANGE:
			-M: Send profile data level 2
			-S: Receive profile data. Assign profile data accordingly
			-S: Send confirmation
			-M: Receive confirmation

		. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 
		"""

		# VALIDATE INPUT AND TARGET SLAVE --------------------------------------

		self.printS(targetMAC, "Initiating connection.", "G")


		# Check if given Slave meets this method's constraints:
		if not self.slaves[targetMAC].status in \
			[Slave.KNOWN, Slave.AVAILABLE]:

			# If this Slave does not have the right status, raise an excep-
			# tion:

			raise ValueError("Current Slave status does not allow \
				connection")

		elif type(self.slaves[targetMAC].mosi) is not int or\
			type(self.slaves[targetMAC].miso) is not int:

			# If either of the Slave's miso or mosi attributes is not an in-
			# teger, raise an exception:

			raise ValueError("Bad MISO and/or MOSI types (need int)")

		elif self.slaves[targetMAC].ip is None:

			# If there is no IP address, raise an exception:

			raise ValueError("Given Slave has no IP address")

		self.printS(targetMAC, "Verified. Setting up sockets")

		# Done verifying. By this point, this Slave is registered w/ an ac-
		# ceptable status, has integer miso and mosi attributes, and an IP
		# address.

		# HANDSHAKE EXCHANGES ----------------------------------------------

		# Set up Slave sockets: - - - - - - - - - - - - - - - - - - - - - - 

		# MISO:
		miso = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		miso.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		miso.settimeout(self.profiler.get_periodMS()/2000.0)
			# The communications period is defined in milliseconds. The 
			# socket timeout should be one-fifth of said period, and this
			# method expects a value in seconds.
		miso.bind(('', 0))
		miso.connect((self.slaves[targetMAC].ip, 
			self.slaves[targetMAC].miso))

		# MOSI:
		mosi = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		mosi.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		mosi.settimeout(self.profiler.get_periodMS()/2000.0)
			# The communications period is defined in milliseconds. The 
			# socket timeout should be one-fifth of said period, and this
			# method expects a value in seconds.
		mosi.bind(('', 0))
		mosi.connect((self.slaves[targetMAC].ip, 
			self.slaves[targetMAC].mosi))

		self.printS(targetMAC, "Sockets set up:\
			\n\t\tSMISO: {}\
			\n\t\tSMOSI: {}".format(
				miso.getsockname(), mosi.getsockname()))
		
		# Set up Queue of things to send: - - - - - - - - - - - - - - - - - 
		handshakeQueue = Queue.Queue()


		# First message is of the form:
		#		INDEX|MHS1|MMISO|MMOSI|PERIOD_MS
		#	e.g 00000001|MHS1|52011|61102|1000
		handshakeQueue.put("MHS1|{},{},{}".\
			format(
				miso.getsockname()[1], 
				mosi.getsockname()[1], 
				self.profiler.get_periodMS()
				))

		# Second message is of the form:
		#		INDEX|MHS2|FAN_MODE|DOUBLE_PARAM1|DOUBLE_PARAM2|...
		#	...FAN_AMOUNT|COUNTER_COUNTS|PULSES_PER_ROTATION|...
		#   ...MAXRPM|MINRPM|MINDC

		handshakeQueue.put("MHS2|{},{},{},{},{},{},{},{},{}".\
			format(
			self.profiler.get_fanMode(),
			self.profiler.get_targetRelation()[0],
			self.profiler.get_targetRelation()[1],
			self.slaves[targetMAC].activeFans,
			self.profiler.get_counterCounts(),
			self.profiler.get_pulsesPerRotation(),
			self.profiler.get_maxRPM(),
			self.profiler.get_minRPM(),
			self.profiler.get_minDC()
			))




		self.printS(targetMAC, "Handshake initiated.")
		# Handshake loop - - - - - - - - - - - - - - - - - - - - - - - - - -

		totalSteps = handshakeQueue.qsize()
		successfulSteps = 0
		failed = True
		self.slaves[targetMAC].exchange = 0


		while(not successfulSteps >= totalSteps):
			# NOTE: Besides by uncaught exceptions, this loop will only 
			# terminate either by "failed" being set to True, or by ac-
			# cumulating enough successfulSteps

			# Increase exchange index:
		 	self.slaves[targetMAC].exchange += 1



			# Get message to be sent: . . . . . . . . . . . . . . . 
			try:

				message = "{:08d}|{:s}".\
					format(self.slaves[targetMAC].exchange, 
						handshakeQueue.get_nowait())

				# Mark task as done:
				handshakeQueue.task_done()

			except Queue.Empty:
				# Terminate handshake loop if there is nothing left
				# to send:
				self.printS(targetMAC, "({})({}/{}) HS Queue emptied.".\
				format(self.slaves[targetMAC].exchange
					, successfulSteps, totalSteps))
				break

			# Send message . . . . . . . . . . . . . . . . . . . . .

			# Send message:
			mosi.send(message)
			
			self.printS(targetMAC,"({})({}/{}) Sent: {}".format(
				self.slaves[targetMAC].exchange,
				 successfulSteps, totalSteps, message))

			# Reply loop: . . . . . . . . . . . . . . . . . . . . . 

			# For each exchange, two messages should be received 
			# from this Slave -- an acknowledgement message, and a 
			# reply.

			# Set up sentinel variables for reply loop:

			tries = 2
				# Try to receive messages a limited amount of times.

			mAcknowledged = False
				# Keep track of whether an acknowledgement message 
				# was received for this exchange.

			while(tries > 0): #(Reply loop)

				tries -= 1

				try:

					# Receive a message. Ignore any messages with 
					# outdated indices:

					receivedIndex = 0

					# Receive loop: .  .  .  .  .  .  .  .  .  .  .

					""" --------------------------------------------
					NOTE: The messages received here are expected to 
					have the following form:

							INDEX|KEYWORD|
								0		1

					-------------------------------------------- """

					# NOTE: This loop will be exited in one of two ways:
					#
					# (1) A correctly indexed, correctly splittable mes-
					#	  sage is received.
					#
					# (2) A socket timeout exception.

					while(receivedIndex != 
						self.slaves[targetMAC].exchange): # (Receive loop)

						received = miso.recv(512)

						self.printS(targetMAC, "({})({}/{}) Received: {}".\
							format(self.slaves[targetMAC].exchange, 
							successfulSteps, totalSteps, received))

						# Split message:
						receivedSplitted = received.split("|")



						# Check index:
						try:
							receivedIndex = int(receivedSplitted[0])

							if receivedIndex != \
								self.slaves[targetMAC].exchange:
								self.printS(targetMAC, "({})({}/{}) Index mismatch ({}). Discarded.".\
									format(self.slaves[targetMAC].exchange, 
									successfulSteps, totalSteps,
									receivedIndex))

								# Discard this message and get ano-
								# ther:
								continue

							else:
								# Check length:
								if len(receivedSplitted) < 2:
									# By this convention, 
									# receivedSplitted sho-
									# uld never have length 
									# smaller than 2.


									self.printS(targetMAC, "({})({}/{}) WARNING: Invalid message size. Discarded.".\
									format(self.slaves[targetMAC].exchange, 
									successfulSteps, totalSteps
									), "W")

									# Discard this message and get 
									# another:
									continue

								else:

									# If there are still no errors,
									# Proceed to analyze this mes-
									# sage.

									# Exit receive loop:
									self.printS(targetMAC, "({})({}/{}) Valid message and size: \n\t\t\tIndex: {}\n\t\t\tKeyword: \"{}\"".\
										format(self.slaves[targetMAC].exchange, 
										successfulSteps, totalSteps, receivedIndex,receivedSplitted[1]))


									self.printS(targetMAC, "({})({}/{}) receivedIndex != exchange: {}".\
										format(self.slaves[targetMAC].exchange, 
										successfulSteps, totalSteps, receivedIndex != self.slaves[targetMAC].exchange))

									pass


						except ValueError:
							self.printS(targetMAC, "({})({}/{}) WARNING: Invalid message content (ValueError). Discarded.".\
									format(self.slaves[targetMAC].exchange, 
									successfulSteps, totalSteps
									), "W")

							# Discard this message and get another:
							continue

						except IndexError:
							self.printS(targetMAC, "({})({}/{}) WARNING: Invalid message (IndexError). Discarded.".\
									format(self.slaves[targetMAC].exchange, 
									successfulSteps, totalSteps
									),"W")

							# Discard this message and get another:
							continue

						# End receive loop .  .  .  .  .  .  .  .  .  . 

						# Check keywords:
						keyword = receivedSplitted[1]
						self.printS(targetMAC, "({})({}/{}) Parsed keyword: \"{}\"".\
									format(self.slaves[targetMAC].exchange, 
									successfulSteps, totalSteps, keyword))


						# Check for acknowledgement message .  .  .  .  
						if keyword == "SACK":
							# Acknowledgement received as expected.
							self.printS(targetMAC, "({})({}/{}) Message acknowledged.".\
									format(self.slaves[targetMAC].exchange, 
									successfulSteps, totalSteps
									),"G")

							mAcknowledged = True

							# Add one more "try" to this loop:
							tries += 1

							# Loop again:
							continue

						else:
							# If the reply received is not an acknow-
							# ledgement message from Slave, then it is a 
							# message and should be acknowledged.

							# Acknowledge command:
							mosi.send("{0:08d}|MACK".format(
								self.slaves[targetMAC].exchange))						


						# Check for disconnect message: .  .  .  .  .  .

						if keyword == "SRIP":
							# "Connection terminated."

							# Check for optional error message:
							try:

								self.printS(targetMAC, "({})({}/{}) WARNING: Slave terminated handshake: {}".\
									format(self.slaves[targetMAC].exchange, 
									successfulSteps, totalSteps,
									receivedSplitted[2]
									),"W")

							except IndexError:
								# If there is no message to be printed,
								# proceed:

								self.printS(targetMAC, "({})({}/{}) WARNING: Slave terminated handshake.".\
									format(self.slaves[targetMAC].exchange, 
									successfulSteps, totalSteps
									),"W")

								pass


							# Break out of reply loop w/ failure flag:
							failed = True
							break

						elif keyword == "SHS1" or keyword == "SHS2":
							# If the message received is a handshake
							# confirmation that matches the exchange
							# index, then this step has been comple-
							# ted successfully.
							self.printS(targetMAC, "Handshake keyword confirmed", "G")
							# Increase success counter:
							successfulSteps += 1
							failed = False

							# Resume loop:
							continue
						

				except socket.timeout:

					# Check if the message was acknowledged:
					if not mAcknowledged:
						# Resend message:
						mosi.send(message)

						self.printS(targetMAC, "({})({}/{}) WARNING: Missed acknowledgement message. Message resent".\
							format(self.slaves[targetMAC].exchange, 
							successfulSteps, totalSteps
							),"W")

						continue

					else:
						# If the message was acknowledged, continue w/
						# loop, which will automatically terminate w/
						# "too many" timeouts.

						self.printS(targetMAC, "({})({}/{}) WARNING: Timed out.".\
							format(self.slaves[targetMAC].exchange, 
							successfulSteps, totalSteps
							),"W")

						continue

				except IndexError:

					# An IndexError is raised if the received message
					# is missing expected components. In this context,
					# this implies the simple handshake message is mis-
					# sing something fundamental.

					self.printS(targetMAC, "({})({}/{}) WARNING: Invalid message after initial verification. Terminating.".\
							format( self.slaves[targetMAC].exchange, 
							successfulSteps, totalSteps
							), "W")

					# Break out of loop and end connection attempt:
					failed = True
					break # Out of reply loop

			# End reply loop .  .  .  .  .  .  .  .  .  .  .  .  .  .  .

			self.printS(targetMAC, "Ended reply loop with failure flag as: {}".format(failed))

			# Check sentinel variable(s): .  .  .  .  .  .  .  .  .  .  .
			if failed:
				# If the failure flag is raised, break out of handshake to
				# terminate the connection attempt.
				break


		# End handshake loop - - - - - - - - - - - - - - - - - - - - - - - -

		# CHECK HANDSHAKE RESULTS ------------------------------------------

		if failed or not successfulSteps >= totalSteps:
			# If either the condition required for success failed, or the 
			# failure flag was raised, terminate this connection attempt:

			self.printS(targetMAC, "Handshake unsuccessful. Disconnecting.", "W")

			# Send termination message:
			mosi.send("{0:08d}|MRIP".\
				format(self.slaves[targetMAC].exchange))

			self.slaves[targetMAC].exchange = 0

			# Deactivate sockets
			miso.shutdown(2)
			mosi.shutdown(2)

			miso.close()
			mosi.close()

			# Modify parameters in accordance:

			self.slaves[targetMAC].status = Slave.DISCONNECTED
			self.slaves[targetMAC].mosi = None
			self.slaves[targetMAC].miso = None
			self.slaves[targetMAC].ip = None

			self.printS(targetMAC, "Handshake terminated unsuccessfully.", "W")

		else:
			# If the connection was successful, allocate Slave accordingly:

			self.printS(targetMAC, "Handshake successful.", "G")

			# Allocate sockets:
			self.slaves[targetMAC].miso = miso
			self.slaves[targetMAC].mosi = mosi

			# Change status:
			self.slaves[targetMAC].status = Slave.CONNECTED

			del self.slaves[targetMAC].mosiQueue
			self.slaves[targetMAC].mosiQueue = Queue.Queue(1)

			self.slaves[targetMAC].thread = threading.Thread( 
				target = self._slaveRoutine,
				args = [targetMAC, mosi.getsockname()[1]])

			self.slaves[targetMAC].thread.start()

			self.printS(targetMAC, "Handshake terminated successfully.", "G")
		# End connect() ========================================================



	def disconnect(self, targetMAC, joinThread = True, remove = False): # ======
		# ABOUT: Terminate connection of a connected Slave.
		# PARAMETERS:
		# - targetMAC: String, MAC address of connected Slave from which to dis-
		#	connect. If this method is used to REMOVE a Slave, it may be used on
		#	a Slave that is not connected.
		# - joinThread: Boolean, whether to join and terminate Slave's thread.
		#	If set to False, the Slave thread will be removed from the Slave
		#	without stopping, and be allowed to stop automatically. Defaults to
		#	True.
		# - remove: Boolean whether to mark a Slave to not connect automatically. 
		#   This removes the Slave from the profile, if applicable.
		#

		# WARNING: THIS METHOD ACCESSES SHARED RESOURCES WITHOUT ACQUIRING THEIR
		# RESPECTIVE LOCKS. THIS IS BECAUSE IT IS ONLY MEANT TO BE USED WITHIN
		# COMMUNICATOR THREADS THAT WILL ONLY CALL IT AFTER ACQUIRING SAID LOCKS
		# AND BEFORE RELEASING THEM.


		# Check status:
		if self.slaves[targetMAC].status > 0:
			# If the Slave is connected, proceed with disconnection.

			self.printS(targetMAC,"Disconnecting from Slave", "W")

			# Send termination message:
			self.slaves[targetMAC].miso.send("{0:08d}|MRIP".\
				format(self.slaves[targetMAC].exchange))

			self.slaves[targetMAC].exchange = 0

			# Deactivate sockets
			self.slaves[targetMAC].miso.shutdown(2)
			self.slaves[targetMAC].mosi.shutdown(2)

			self.slaves[targetMAC].miso.close()
			self.slaves[targetMAC].mosi.close()

			# Modify parameters in accordance:

			self.slaves[targetMAC].status = Slave.DISCONNECTED
			self.slaves[targetMAC].mosi = None
			self.slaves[targetMAC].miso = None
			self.slaves[targetMAC].ip = None

			del self.slaves[targetMAC].mosiQueue
			self.slaves[targetMAC].mosiQueue = Queue.Queue(1)

			if joinThread:
				# The thread will detect the changes above and terminate 
				# automatically. 

				self.printS(targetMAC, "Joining thread")
				self.slaves[targetMAC].thread.join()

			self.printS(targetMAC, "Disconnected from Slave", "W")

			if remove:
				self.printS(targetMAC, "Slave removed from list")
				del self.slaves[targetMAC]



		elif remove:
			self.printS(targetMAC, "Slave removed from list")
			del self.slaves[targetMAC]

		else:

			# Otherwise, raise exception:

			self.printS(targetMAC, "ERROR: Tried to disconnect from disconnected\
				Slave", "E")

		# End disconnect ======================================================= 


	# # INTERFACE METHODS # # # # # # # # # # # # # # # # # # # # # # # # # # #

	def add(self, targetMAC): # ================================================M
		# ABOUT: Mark a Slave on the network for connection. The given Slave 
		# must be already listed and marked AVAILABLE. This method will mark it 
		# as KNOWN, and the Listener Thread will add it automatically when it
		# responds to the next broadcast.
		# PARAMETERS:
		# - targetMAC: String, MAC address of Slave to "add."

		# Acquire lock:
		self.slaves[targetMAC].lock.acquire()
		try:

			# Check status:
			if self.slaves[targetMAC].status != Slave.AVAILABLE:
				self.printM("ERROR: Tried to add a Slave w/ status other than \
					AVAILABLE", "E")

			else:
				# If the board is AVAILABLE, set is as KNOWN:
				self.slaves[targetMAC].status = Slave.KNOWN

		finally:
			self.slaves[targetMAC].lock.acquire(False)
				#								 ^ Non-blocking
				#
				# Note: if the lock was released within the "try" clause
				# then this statement will prevent a threading exception
				# when an attempt to release an unlocked lock is made.
			self.slaves[targetMAC].lock.release()


		# End add ==============================================================

	def send(self, command, targetMAC): # ======================================
		# ABOUT: Send a command to a given, connected Slave by adding to its MO-
		# SI Queue. Notice 

		# [NOT IMPLEMENTED]

		pass
		# End send =============================================================


		# End shutdown =========================================================

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


	print "NO TEST SUITE IMPLEMENTED. TERMINATING."