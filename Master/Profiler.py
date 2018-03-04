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
import names

import random # Random names, boy

## CONSTANT VALUES #############################################################

# FAN MODES:
SINGLE = 1
DOUBLE = 2

# DEFAULT CONFIGURATION ========================================================
	
# COMMUNICATIONS:
STD_BROADCAST_PORT  = 65000
STD_BROADCAST_PERIOD_S = 1
STD_PERIOD_MS = 500 # (millisecond(s))
STD_MASTER_TIMEOUT_MS= 1000
STD_INTERIM_MS = 200
STD_MAX_LENGTH = 512
STD_MAX_TIMEOUTS = 4

STD_MAIN_QUEUE_SIZE = 20
STD_SLAVE_QUEUE_SIZE= 100
STD_BROADCAST_QUEUE_SIZE = 2
STD_LISTENER_QUEUE_SIZE = 3


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
DEFAULT_MAX_FANS = 21


## CLASS DEFINITION ############################################################

class Profiler:
	# ABOUT: This module holds all "variable" data that should be kept in nonvo-
	# latile storage.

	def __init__(self, interface):
		# ABOUT: Constructor for class Profiler.

		# Administrative data --------------------------------------------------
		self.name = "Alphatunnel"
		self.description = "This is a test Profile"

		# Communications -------------------------------------------------------
		self.broadcastPort = STD_BROADCAST_PORT
		self.broadcastPeriodS = STD_BROADCAST_PERIOD_S
		self.periodMS = STD_PERIOD_MS
		self.passcode = "good_luck"
		self.maxLength = STD_MAX_LENGTH
		self.maxTimeouts = STD_MAX_TIMEOUTS
		self.masterTimeout = STD_MASTER_TIMEOUT_MS
		self.masterTimeoutS = self.masterTimeout/1000.0
		self.interim = STD_INTERIM_MS
		self.interimS = self.interim/1000.0

		self.mainQueueSize = STD_MAIN_QUEUE_SIZE
		self.slaveQueueSize = STD_SLAVE_QUEUE_SIZE
		self.broadcastQueueSize = STD_BROADCAST_QUEUE_SIZE
		self.listenerQueueSize = STD_LISTENER_QUEUE_SIZE

		# Wind tunnel ----------------------------------------------------------
		self.slaves = {}

		self.slaves["00:80:e1:38:00:2a"] = Slave.Slave(name = random.choice(names.coolNames), 
			mac = "00:80:e1:38:00:2a", status = Slave.KNOWN, 
			interface = interface, maxFans = 21,  activeFans = 21)

		self.slaves["00:80:e1:45:00:46"] = Slave.Slave(name = random.choice(names.coolNames), 
			mac = "00:80:e1:45:00:46", status = Slave.KNOWN, 
			interface = interface, maxFans = 21,  activeFans = 21)

		

		self.slaves["00:80:e1:2f:00:1d"] = Slave.Slave(name = random.choice(names.coolNames), 
			mac = "00:80:e1:2f:00:1d", status = Slave.KNOWN, 
			interface = interface, maxFans = 21,  activeFans = 21)


		"""PROVISIONAL ZOMBIE SLAVES
		self.slaves["z:01"] = Slave.Slave(name = random.choice(names.coolNames), mac = "z:01", status = Slave.KNOWN, interface = interface, maxFans = 21,  activeFans = 21)
		self.slaves["z:02"] = Slave.Slave(name = random.choice(names.coolNames), mac = "z:02", status = Slave.KNOWN, interface = interface, maxFans = 21,  activeFans = 21)
		self.slaves["z:03"] = Slave.Slave(name = random.choice(names.coolNames), mac = "z:03", status = Slave.KNOWN, interface = interface, maxFans = 21,  activeFans = 21)
		self.slaves["z:04"] = Slave.Slave(name = random.choice(names.coolNames), mac = "z:04", status = Slave.KNOWN, interface = interface, maxFans = 21,  activeFans = 21)
		self.slaves["z:05"] = Slave.Slave(name = random.choice(names.coolNames), mac = "z:05", status = Slave.KNOWN, interface = interface, maxFans = 21,  activeFans = 21)

		self.slaves["z:06"] = Slave.Slave(name = random.choice(names.coolNames), mac = "z:06", status = Slave.KNOWN, interface = interface, maxFans = 21,  activeFans = 21)
		self.slaves["z:07"] = Slave.Slave(name = random.choice(names.coolNames), mac = "z:07", status = Slave.KNOWN, interface = interface, maxFans = 21,  activeFans = 21)
		self.slaves["z:08"] = Slave.Slave(name = random.choice(names.coolNames), mac = "z:08", status = Slave.KNOWN, interface = interface, maxFans = 21,  activeFans = 21)
		self.slaves["z:09"] = Slave.Slave(name = random.choice(names.coolNames), mac = "z:09", status = Slave.KNOWN, interface = interface, maxFans = 21,  activeFans = 21)
		self.slaves["z:10"] = Slave.Slave(name = random.choice(names.coolNames), mac = "z:10", status = Slave.KNOWN, interface = interface, maxFans = 21,  activeFans = 21)

		self.slaves["z:11"] = Slave.Slave(name = random.choice(names.coolNames), mac = "z:11", status = Slave.KNOWN, interface = interface, maxFans = 21,  activeFans = 21)
		self.slaves["z:12"] = Slave.Slave(name = random.choice(names.coolNames), mac = "z:12", status = Slave.KNOWN, interface = interface, maxFans = 21,  activeFans = 21)
		self.slaves["z:13"] = Slave.Slave(name = random.choice(names.coolNames), mac = "z:13", status = Slave.KNOWN, interface = interface, maxFans = 21,  activeFans = 21)
		self.slaves["z:14"] = Slave.Slave(name = random.choice(names.coolNames), mac = "z:14", status = Slave.KNOWN, interface = interface, maxFans = 21,  activeFans = 21)
		self.slaves["z:15"] = Slave.Slave(name = random.choice(names.coolNames), mac = "z:15", status = Slave.KNOWN, interface = interface, maxFans = 21,  activeFans = 21)

		self.slaves["z:16"] = Slave.Slave(name = random.choice(names.coolNames), mac = "z:16", status = Slave.KNOWN, interface = interface, maxFans = 21,  activeFans = 21)
		self.slaves["z:17"] = Slave.Slave(name = random.choice(names.coolNames), mac = "z:17", status = Slave.KNOWN, interface = interface, maxFans = 21,  activeFans = 21)
		self.slaves["z:18"] = Slave.Slave(name = random.choice(names.coolNames), mac = "z:18", status = Slave.KNOWN, interface = interface, maxFans = 21,  activeFans = 21)
		self.slaves["z:19"] = Slave.Slave(name = random.choice(names.coolNames), mac = "z:19", status = Slave.KNOWN, interface = interface, maxFans = 21,  activeFans = 21)
		self.slaves["z:20"] = Slave.Slave(name = random.choice(names.coolNames), mac = "z:20", status = Slave.KNOWN, interface = interface, maxFans = 21,  activeFans = 21)
		"""

		self.slavesLock = threading.Lock()
		self.dimensions = (0,0)
		self.maxFans = DEFAULT_MAX_FANS

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
