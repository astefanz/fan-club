################################################################################
## Project: Fan Club Mark II "Master" ## File: Profiler.py                    ##
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
Nonvolatile storage and wind tunnel representation.

"""
################################################################################


# ** WARNING ** * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
# THIS MODULE IS IN AN EARLY PROTYTPE "STUB" STAGE. IT HAS NO FILE HANDLING CA-
# PABILITIES YET AND WILL ONLY YIELD PREDEFINED VALUES FOR THE DEVELOPMENT OF
# THE REST OF THE CODE
#  * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

## DEPENDENCIES ################################################################
import Slave 
import threading
import Fan

## CONSTANT VALUES #############################################################

# FAN MODES:
SINGLE = 1
DOUBLE = 2

# DEFAULT CONFIGURATION ========================================================
	
# COMMUNICATIONS:
STD_BROADCAST_PORT  = 65000
STD_BROADCAST_PERIOD_S = 1
STD_PERIOD_MS = 2000 # (millisecond(s))
STD_MASTER_TIMEOUT_MS= 500
STD_INTERIM_MS = 200
STD_MAX_LENGTH = 512
STD_MAX_TIMEOUTS = 4


# FAN ARRAY:
# NOTE: That of GALCIT's "basement wind tunnel," using DELTA PFR0912XHE-SP00
# fans.

DEFAULT_FAN_MODEL = "DELTA PFR0912XHE-SP00"
DEFAULT_FAN_MODE =  SINGLE
DEFAULT_TARGET_RELATION = (1,0) # (For double fans, irrelevant if on SINGLE)
DEFAULT_CHASER_TOLERANCE = 0.02 # (2% of target RPM)
DEFAULT_COUNTER_COUNTS = 1 # (Measure time between pulses once)
DEFAULT_COUNTER_TIMEOUT_MS = 30 # (Assume fan is not spinning after 30ms)
DEFAULT_PULSES_PER_ROTATION = 2 # (Fan generates 2 pulses per rotation)
DEFAULT_MAX_RPM = 11500 # (Maximum nominal RPM)
DEFAULT_MIN_RPM = 1185  # (Minimum nominal RPM)
DEFAULT_MIN_DC = 0.1 # (10% duty cycle corresponds to ~1185 RPM)

## CLASS DEFINITION ############################################################

class Profiler:
	# ABOUT: This module holds all "variable" data that should be kept in nonvo-
	# latile storage. In particular, it holds the representation of the w.tunnel
	# controlled by an instance of Fan Club. All other classes (Interface, Com-
	# municator) refer to this one to access wind-tunnel-specific data in a co-
	# ordinated and thread-safe manner.

	def __init__(self, printM):
		# ABOUT: Constructor for class Profiler.
		# PARAMETERS:
		# - printM: Python function with which to print terminal output. Must 
		#	take a string to be printed.

		printM("Initializing Profiler \
			(PRELIMINARY MODE. NO FILE HANDLING CAPABILITY)")

		# Administrative data --------------------------------------------------
		self.name = "Alphatunnel"
		self.description = "This is a test Profile"

		# Communications -------------------------------------------------------
		self.broadcastPort = STD_BROADCAST_PORT
		self.broadcastPeriodS = STD_BROADCAST_PERIOD_S
		self.periodMS = STD_PERIOD_MS
		self.password = "good_luck"
		self.maxLength = STD_MAX_LENGTH
		self.maxTimeouts = STD_MAX_TIMEOUTS
		self.masterTimeout = STD_MASTER_TIMEOUT_MS
		self.interim = STD_INTERIM_MS

		# Wind tunnel ----------------------------------------------------------
		self.slaves = {}

		self.slaves["00:80:e1:38:00:2a"] = Slave.Slave(name = "Lad", mac = "00:80:e1:38:00:2a", status = Slave.KNOWN, fans = [Fan.Fan(1,0), Fan.Fan(2,0), Fan.Fan(3,0), Fan.Fan(4,0), Fan.Fan(5,0), Fan.Fan(6,0), Fan.Fan(7,0),\
											Fan.Fan(8,0), Fan.Fan(9,0), Fan.Fan(10,0), Fan.Fan(11,0), Fan.Fan(12,0), Fan.Fan(13,0), Fan.Fan(14,0),\
											Fan.Fan(15,0), Fan.Fan(16,0), Fan.Fan(17,0), Fan.Fan(18,0), Fan.Fan(19,0), Fan.Fan(20,0), Fan.Fan(21,0)], activeFans = 21)

		self.slaves["00:80:e1:45:00:46"] = Slave.Slave(name = "Leed", mac = "00:80:e1:45:00:46", status = Slave.KNOWN, fans = [Fan.Fan(1,0), Fan.Fan(2,0), Fan.Fan(3,0), Fan.Fan(4,0), Fan.Fan(5,0), Fan.Fan(6,0), Fan.Fan(7,0),\
											Fan.Fan(8,0), Fan.Fan(9,0), Fan.Fan(10,0), Fan.Fan(11,0), Fan.Fan(12,0), Fan.Fan(13,0), Fan.Fan(14,0),\
											Fan.Fan(15,0), Fan.Fan(16,0), Fan.Fan(17,0), Fan.Fan(18,0), Fan.Fan(19,0), Fan.Fan(20,0), Fan.Fan(21,0)], activeFans = 21)

		
		self.slavesLock = threading.Lock()
		self.dimensions = (0,0)

		# Fan array ------------------------------------------------------------
		self.fanModel = DEFAULT_FAN_MODEL
		self.fanMode = SINGLE
	 	self.targetRelation = DEFAULT_TARGET_RELATION
		self.chaserTolerance = DEFAULT_CHASER_TOLERANCE
		self.counterCounts = DEFAULT_COUNTER_COUNTS
		self.counterTimeoutMS = DEFAULT_COUNTER_TIMEOUT_MS
		self.pulsesPerRotation = DEFAULT_PULSES_PER_ROTATION
		self.maxRPM = DEFAULT_MAX_RPM
		self.minRPM = DEFAULT_MIN_RPM
		self.minDC = DEFAULT_MIN_DC


		printM("\tProfiler initialized", "G")

	def getSlave(self, mac = None):
		# ABOUT: Access a Slave in the Slave dictionary.
		# PARAMETERS:
		# - mac: MAC address of Slave.
		# EXCEPTIONS: 
		# - Will raise KeyError if there is no such Slave.

		return self.slaves[mac]

	def addSlave(self, newSlave):
		# ABOUT: Add a Slave to the Slave dictionary.
		# PARAMETERS:
		# - newSlave: Initialized Slave instance to add. If there is already a
		#	Slave under its MAC address, such old Slave will be overwritten.

		printM("Adding new Slave...")
		self.slavesLock.acquire()

		try:
			self.slaves[newSlave.mac] = newSlave
		finally:
			self.slavesLock.release()

		printM("Added {}".format(newSlave.mac))

	def overwrite(self, filename):
		# ABOUT: Save current configuration into file.
		# PARAMETERS:
		# - filename: String of filename to use.

		# REM: SAVE ONLY KNOWN, CONNECTED, AND DISCONNECTED SLAVES

		printM("WARNING: SAVE COMMAND CALLED ON PRELIMINARY VERSION")


	# GETTERS # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 


	def get_name(self):
		# ABOUT: Get parameter.

		return self.name

	def get_description(self):
		# ABOUT: Get parameter.

		return self.description

	def get_broadcastPort(self):
		# ABOUT: Get parameter.

		return self.broadcastPort

	def get_broadcastPeriodS(self):
		# ABOUT: Get parameter

		return self.broadcastPeriodS

	def get_periodMS(self):
		# ABOUT: Get parameter.

		return self.periodMS

	def get_password(self):
		# ABOUT: Get parameter.

		return self.password

	def get_maxLength(self):
		# ABOUT: Get parameter.

		return self.maxLength

	def get_maxTimeouts(self):
		# ABOUT: Get parameter.

		return self.maxTimeouts

	def get_masterTimeoutS(self):
		# Pls

		return self.masterTimeout/1000.0

	def get_interimS(self):
		# Pls

		return self.interim/1000.0

	def get_dimensions(self):
		# ABOUT: Get parameter.

		return self.dimensions

	def get_fanModel(self):
		# ABOUT: Get parameter.

		return self.fanModel

	def get_fanMode(self):
		# ABOUT: Get parameter.

		return self.fanMode

	def get_targetRelation(self):
		# ABOUT: Get parameter.

		return self.targetRelation

	def get_chaserTolerance(self):
		# ABOUT: Get parameter.

		return self.chaserTolerance

	def get_counterCounts(self):
		# ABOUT: Get parameter.

		return self.counterCounts

	def get_counterTimeoutMS(self):
		# ABOUT: Get parameter.

		return self.counterTimeoutMS

	def get_pulsesPerRotation(self):
		# ABOUT: Get parameter.

		return self.pulsesPerRotation

	def get_maxRPM(self):
		# ABOUT: Get parameter.

		return self.maxRPM

	def get_minRPM(self):
		# ABOUT: Get parameter.

		return self.minRPM

	def get_minDC(self):
		# ABOUT: Get parameter.

		return self.minDC




	# SETTERS # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

	def set_name(self, value):
		# ABOUT: Set parameter to specified value.
		# PARAMETERS:
		# - value: new value to assign

		printM("WARNING: MODIFICATION OF VALUE CALLED ON PRELIMINARY MODE")

	def set_mac(self, value):
		# ABOUT: Set parameter to specified value.
		# PARAMETERS:
		# - value: new value to assign

		printM("WARNING: MODIFICATION OF VALUE CALLED ON PRELIMINARY MODE")

	def set_broadcastPort(self):
		# ABOUT: Set parameter to specified value.
		# PARAMETERS:
		# - value: new value to assign

		printM("WARNING: MODIFICATION OF VALUE CALLED ON PRELIMINARY MODE")

	def set_broadcastPeriodS(self):
		# ABOUT: Set parameter to specified value.
		# PARAMETERS:
		# - value: new value to assign

		printM("WARNING: MODIFICATION OF VALUE CALLED ON PRELIMINARY MODE")

	def set_periodMS(self):
		# ABOUT: Set parameter to specified value.
		# PARAMETERS:
		# - value: new value to assign

		printM("WARNING: MODIFICATION OF VALUE CALLED ON PRELIMINARY MODE")

	def set_password(self):
		# ABOUT: Set parameter to specified value.
		# PARAMETERS:
		# - value: new value to assign

		printM("WARNING: MODIFICATION OF VALUE CALLED ON PRELIMINARY MODE")

	def set_description(self, value):
		# ABOUT: Set parameter to specified value.
		# PARAMETERS:
		# - value: new value to assign

		printM("WARNING: MODIFICATION OF VALUE CALLED ON PRELIMINARY MODE")

	def set_slaves(self, value):
		# ABOUT: Set parameter to specified value.
		# PARAMETERS:
		# - value: new value to assign

		printM("WARNING: MODIFICATION OF VALUE CALLED ON PRELIMINARY MODE")

	def set_dimensions(self, value):
		# ABOUT: Set parameter to specified value.
		# PARAMETERS:
		# - value: new value to assign

		printM("WARNING: MODIFICATION OF VALUE CALLED ON PRELIMINARY MODE")

	def set_fanModel(self, value):
		# ABOUT: Set parameter to specified value.
		# PARAMETERS:
		# - value: new value to assign

		printM("WARNING: MODIFICATION OF VALUE CALLED ON PRELIMINARY MODE")

	def set_fanMode(self, value):
		# ABOUT: Set parameter to specified value.
		# PARAMETERS:
		# - value: new value to assign

		printM("WARNING: MODIFICATION OF VALUE CALLED ON PRELIMINARY MODE")

	def set_targetRelation(self, value):
		# ABOUT: Set parameter to specified value.
		# PARAMETERS:
		# - value: new value to assign

		printM("WARNING: MODIFICATION OF VALUE CALLED ON PRELIMINARY MODE")

	def set_chaserTolerance(self, value):
		# ABOUT: Set parameter to specified value.
		# PARAMETERS:
		# - value: new value to assign

		printM("WARNING: MODIFICATION OF VALUE CALLED ON PRELIMINARY MODE")

	def set_counterCounts(self, value):
		# ABOUT: Set parameter to specified value.
		# PARAMETERS:
		# - value: new value to assign

		printM("WARNING: MODIFICATION OF VALUE CALLED ON PRELIMINARY MODE")

	def set_counterTimeoutMS(self, value):
		# ABOUT: Set parameter to specified value.
		# PARAMETERS:
		# - value: new value to assign

		printM("WARNING: MODIFICATION OF VALUE CALLED ON PRELIMINARY MODE")

	def set_pulsesPerRotation(self, value):
		# ABOUT: Set parameter to specified value.
		# PARAMETERS:
		# - value: new value to assign

		printM("WARNING: MODIFICATION OF VALUE CALLED ON PRELIMINARY MODE")

	def set_maxRPM(self, value):
		# ABOUT: Set parameter to specified value.
		# PARAMETERS:
		# - value: new value to assign

		printM("WARNING: MODIFICATION OF VALUE CALLED ON PRELIMINARY MODE")

	def set_minRPM(self, value):
		# ABOUT: Set parameter to specified value.
		# PARAMETERS:
		# - value: new value to assign

		printM("WARNING: MODIFICATION OF VALUE CALLED ON PRELIMINARY MODE")

	def set_minDC(self, value):
		# ABOUT: Set parameter to specified value.
		# PARAMETERS:
		# - value: new value to assign

		printM("WARNING: MODIFICATION OF VALUE CALLED ON PRELIMINARY MODE")

		































