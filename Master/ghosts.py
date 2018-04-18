################################################################################
## Project: Fan Club Mark II "Master" ## File: ghosts.py                      ##
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
This is an auxiliary module to simulate "dummy" FCMkII Slaves over a network.

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
import resource

class GhostSlave:
	# NEEDS:
	# - listener thread to answer to broadcasts
	# 	- listener socket
	# - receive thread to receive replies
	#	- receive socket
	# - send thread to send random values
	#	- send socket
	#	- period_ms
	# 

	def __init__(self, number, mbAddress): 
		# Constructor for GhostSlave
		
		# Basic attributes:
		self.mac = "{:014d}:XX".format(number)
		
		self.misoI = 0
		self.mosiI = 0
		
		self.mbAddress = mbAddress
		# Create sockets:

		## LISTENER:
		self.ls = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)				  
		# Configure socket as "reusable" (in case of improper closure):
		self.ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		# Bind socket to "nothing" (Broadcast on all interfaces and let OS
		# assign port number):
		self.ls.bind(("", 0))
		#print self.ls.getsockname()

		## RECEIVER
		self.rs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)				  
		# Configure socket as "reusable" (in case of improper closure):
		self.rs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		# Bind socket to "nothing" (Broadcast on all interfaces and let OS
		# assign port number):
		self.rs.bind(("", 0))
		#print self.rs.getsockname()

		## SENDER
		self.ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)				  
		# Configure socket as "reusable" (in case of improper closure):
		self.ss.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		# Bind socket to "nothing" (Broadcast on all interfaces and let OS
		# assign port number):
		self.ss.bind(("", 0))
		#print self.ss.getsockname()
		
		
		# Synchronization:
		self.commsLock = threading.Lock()
		self.masterIP = ''
		self.masterPort = 0
		self.periodMS = 100
		self.connected = False

		# Fire up them' threads:

		self.st = threading.Thread(
			target = self._senderR
		)
		self.st.setDaemon(True)

		self.rt = threading.Thread(
			target = self._receiverR
		)
		self.rt.setDaemon(True)

		self.rt.start()
		self.st.start()
		
	
		self.ls.sendto('{}|good_luck|{}|{}|{}'.\
			format(self.misoI, 
			self.mac,
			self.ss.getsockname()[1],
			self.rs.getsockname()[1]),
			self.mbAddress)
		
		self.dc = 0.0
		print "[{}] Ghost reporting".format(self.mac)
		# End __init__ ---------------------------------------------------------

	def _receiverR(self):
		# Receiver routine:

		while True:

			# Get message:
			message, sender = self.rs.recvfrom(256)

			print "{} RR: {}".format(self.mac, message)

			# Check message:
			splitted = message.split("|")
			if splitted [0] <= self.mosiI:
				continue

			if splitted[1] == "MHSK":
				# Handshake
				sp2 = splitted[2].split(",")
				self.masterIP = sender[0]
				self.masterPort = int(sp2[0])
				self.periodMS = int(sp2[2])
				self.misoI = 1
				for i in (1,2):
					self.rs.sendto("1|SHSK", (self.masterIP, self.masterPort))
					self.misoI += 1
				
				self.connected = True
			
			elif splitted[1] == "MSTD":
				ss = splitted[2].split("~")
				self.dc = float(ss[1])
				
			else:
				pass
			
		# End _receiveR --------------------------------------------------------
		

	def _senderR(self):
		# Sender routine
		
		while(True):
			if self.connected:
				time.sleep(self.periodMS/1000.0)
				# Fake DCs:

				frpm = ''
				fdc = ''
				for i in range(21):
					
					#frpm += str(random.randint(0,11500)) + ","
					#fdc += str(random.randint(0,100)) + ","

					frpm += str(int(self.dc*11500)) + ","
					fdc += str(self.dc*100) + ","
				for i in range(3):
					m = "{}|SSTD|{}|{}".\
						format(self.mosiI,frpm[:-1],fdc[:-1])
					self.ss.sendto(m,
						(self.masterIP, self.masterPort)
					)
					print m

					self.mosiI += 1
				


# RUN THIS BAD BOY:

resource.setrlimit(
	resource.RLIMIT_NOFILE, 
	(1024, resource.getrlimit(resource.RLIMIT_NOFILE)[1]
	))
numT = int(raw_input("Number of GhostSlaves? "))
gs = []


## LISTENER:
ls = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)				  
# Configure socket as "reusable" (in case of improper closure):
ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# Bind socket to "nothing" (Broadcast on all interfaces and let OS
# assign port number):
ls.bind(("", 65000))
print ls.getsockname()

print "Listening for Master broadcast..."
while(True):

	message, sender = ls.recvfrom(256)
	
	splitted = message.split('|')
	
	if splitted[1] == "good_luck":	
		mba = (sender[0], int(splitted[2]))
		break

print "Found Master as {}".format(str(mba))
ls.close()

for i in range(numT):
	gs.append(GhostSlave(i, mba))
	
while(True):
	pass




