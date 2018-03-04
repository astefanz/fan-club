################################################################################
## Project: Fan Club Mark II "Master" ## File: Slave.py                       ##
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
OOP representation of Slave units.

"""
################################################################################

## DEPENDENCIES ################################################################
import Fan       			 # Fan representation
import Queue      # Communication between threads
import threading   # Thread-safe access
import FCInterface as FCI

## CONSTANT VALUES #############################################################

# SLAVE STATUS CODES:
	# ABOUT: Positive status codes are for connected Slaves, negative codes for
	# disconnected ones.

DISCONNECTED = -3
AVAILABLE = -2
KNOWN = -1
CONNECTED = 1
BUSY = 2

# AUXILIARY DEFINITIONS ########################################################

def translate(statusCode): # ===================================================
	# ABOUT: Translate an integer status code to a String.
	# PARAMETERS:
	# - statusCode: int, status code to translate.
	# RAISES:
	# - ValueError if given argument is not a valid status code

	if statusCode == DISCONNECTED:
		return "DISCONNECTED"
	elif statusCode == AVAILABLE:
		return "AVAILABLE"
	elif statusCode == KNOWN:
		return "KNOWN"
	elif statusCode == CONNECTED:
		return "CONNECTED"
	elif statusCode == BUSY:
		return "BUSY"
	else:
		raise ValueError("Slave.translate got nonexistent statusCode! ({})".\
			format(statusCode))

	# End translate # ==========================================================

## CLASS DEFINITION ############################################################

class Slave:
	# ABOUT: Representation of connected Slave model, primarily a container with
	# no behavior besides that of its components, such as Locks.

	def __init__(self, name, mac, status, interface, maxFans, activeFans,
		ip = None, misoP = None, mosiP = None, misoS = None, mosiS = None,
		thread = None):
		# ABOUT: Constructor for class Slave.
		# WARNING: Method documentation outdated.
		# PARAMETERS:
		# - name: String representing this Slave unit's name (arbitrary)
		# - mac: String representing this Slave unit's MAC address
		# - status: Integer value describing the connection of this Slave, or
		#	lack thereof; its possible values are defined in Slave.py 
		# - fans: List of exactly 21 Fan objects (see Fan.py) that represents
		#	this Slave's set of physical fans.
		# - activeFans: Int, number of fans in the array to be used.
		# - ip: String describing this Slave's IP address, if any. May be left
		#	blank, in which case it defaults to None.
		# - miso: Either an integer representing the Slave's MISO port number or
		#	a Python UDP socket object if this Slave unit is connected.
		# - mosi: Either an integer representing the Slave's MOSI port number or
		#	a Python UDP socket object if this Slave unit is connected.
		#
		# ATTRIBUTES:
		# Besides the Constructor parameters, the following data members are in-
		# trinsic of every Slave instance:
		# - lock: Python Lock object for thread-safe access.
		# - mosiQueue: Python Queue object for inter-thread communication of 
		#	outgoing messages.
		# - thread: Python thread object (or None) that executes Slave's handler
		#	routine.
		# - exchange: int, to coordinate UDP communications.
		#
		# WARNING: THIS CLASS IS NOT MEANT TO BE USED ON ITS OWN BUT AS AN AUXI-
		# LIARY CONTAINER FOR CLASSES SUCH AS Slave AND Profile. AS SUCH, FOR
		# PURPOSES OF EFFICIENCY, IT OPERATES UNDER THE ASSUMPTION THAT ALL PA-
		# RAMETERS HAVE BEEN VERIFIED BY THE GREATER CONTAINER CLASS.

		self.name = name + mac[-3:]
		self.mac = mac
		self.status = status

		self.ip  = ip
		self.misoP = misoP
		self.mosiP = mosiP
		self.misoS = misoS
		self.mosiS = mosiS
		self.thread = thread
		self.exchange = 0
		self.misoIndex = 0

		self.lock = threading.Lock()
		self.mosiQueue = Queue.Queue(1)

		self.slaveDisplay = FCI.SlaveDisplay(
			interface, self.name, mac, status, maxFans, activeFans)

		# Set active fans:
		self.setActiveFans(activeFans)

		self.setRPM = self.slaveDisplay.setRPM
		self.setDC = self.slaveDisplay.setDC


	def setName(self, newName): # ==========================================
		# ABOUT: Update name.
		# PARAMETERS: 
		# - newName: new name.

		self.name = newName
		self.slaveDisplay.setName(newName)

	def setStatus(self, newStatus): # ==========================================
		# ABOUT: Update status.
		# PARAMETERS: 
		# - newStatus: code of the new status.

		self.status = newStatus
		
		if newStatus == DISCONNECTED:
			self.setExchange(0)
			self.setMISOIndex(0)

		self.slaveDisplay.setStatus(newStatus)

		# End setStatus ========================================================

	def setMAC(self, newMAC): # ================================================
		# ABOUT: Update MAC.
		# PARAMETERS: 
		# - MAC: new MAC address.

		self.mac = newMAC
		self.slaveDisplay.setMAC(newMAC)

	def setExchange(self, newExchange): # ======================================
		# ABOUT: Update exchange index.
		# PARAMETERS: 
		# - newExchange: new exchange index.

		self.exchange = newExchange
		self.slaveDisplay.setExchange("E: " + str(newExchange))

	def setIP(self, newIP): # ==================================================
		# ABOUT: Update IP address.
		# PARAMETERS: 
		# - newExchange: new IP address

		self.ip = newIP
		self.slaveDisplay.setIP(newIP)

	def setActiveFans(self, newActiveFans): # ==================================
		# ABOUT: Update activeFans value
		# PARAMETERS:
		# - newActiveFans: new value for activeFans
		self.activeFans = newActiveFans
		self.slaveDisplay.setActiveFans(newActiveFans)

	def incrementExchange(self):
		# ABOUT: Increment exchange index by 1.
		self.exchange += 1
		self.slaveDisplay.setExchange("E: " + str(self.exchange))

	def incrementMISOIndex(self):
		# ABOUT: Increment misoIndex index by 1.
		self.misoIndex += 1
		self.slaveDisplay.setMISOIndex("I: " + str(self.misoIndex))

	def setMISOIndex(self, newMISOIndex): # ======================================
		# ABOUT: Update misoIndex index.
		# PARAMETERS: 
		# - newmisoIndex: new misoIndex index.

		self.misoIndex = newMISOIndex
		self.slaveDisplay.setMISOIndex("I: " + str(newMISOIndex))


