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

## CONSTANT VALUES #############################################################

# SLAVE STATUS CODES:
	# ABOUT: Positive status codes are for connected Slaves, negative codes for
	# disconnected ones.

DISCONNECTED = -3
AVAILABLE = -2
KNOWN = -1
CONNECTED = 1
BUSY = 2

## CLASS DEFINITION ############################################################

class Slave:
	# ABOUT: Representation of connected Slave model, primarily a container with
	# no behavior besides that of its components, such as Locks.

	def __init__(self, name, mac, status, fans, activeFans, ip = None, 
		misoP = None, mosiP = None, misoS = None, mosiS = None, thread = None):
		# ABOUT: Constructor for class Slave.
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
		# - thread: Python thread object (from Python threading package) that
		#	executes FC MkII's Communicator's Slave routine.
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

		self.name = name
		self.mac = mac
		self.status = status
		self.lock = threading.Lock()
		self.fans = fans
		self.activeFans = activeFans
		self.ip  = ip
		self.misoP = misoP
		self.mosiP = mosiP
		self.misoS = misoS
		self.mosiS = mosiS
		self.mosiQueue = Queue.Queue(1)
		self.thread = thread
		self.exchange = 0

