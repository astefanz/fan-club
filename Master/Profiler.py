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
import numpy as np

import random # Random names, boy

## CONSTANT VALUES #############################################################

# FAN MODES:
SINGLE = 1
DOUBLE = 2

# DEFAULT CONFIGURATION ========================================================

PROFILE_NAME = "[ALPHA]"
	
# COMMUNICATIONS:
STD_BROADCAST_PORT  = 65000
STD_PERIOD_MS = 100 # (millisecond(s))
STD_BROADCAST_PERIOD_MS = 1000
STD_MAX_LENGTH = 512
STD_MAX_TIMEOUTS = 4

STD_MAIN_QUEUE_SIZE = 20
STD_SLAVE_QUEUE_SIZE= 100
STD_BROADCAST_QUEUE_SIZE = 2
STD_LISTENER_QUEUE_SIZE = 3
STD_MISO_QUEUE_SIZE = 4
STD_PRINTER_QUEUE_SIZE = 3

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

DEFAULT_MODULE_DIMENSIONS = (2, 11) # (rows, columns)
DEFAULT_MODULE_ASSIGNMENT = \
    "1,2,3,4,5,6,7,8,9,10,,11,12,13,14,15,16,17,18,19,20"

## CLASS DEFINITION ############################################################

class Profiler:
	# ABOUT: This module holds all "variable" data that should be kept in nonvo-
	# latile storage.

	def __init__(self):
		# ABOUT: Constructor for class Profiler.
		
		# Store profile information in dictionary:
		self.profile = {}

		# Administrative data --------------------------------------------------
		self.profile["name"] = PROFILE_NAME
		self.profile["description"] = "This is a test Profile"

		# Communications -------------------------------------------------------
		self.profile["broadcastPort"] = STD_BROADCAST_PORT
		self.profile["periodMS"] = STD_PERIOD_MS
		self.profile["broadcastPeriodMS"] = STD_BROADCAST_PERIOD_MS
		self.profile["broadcastPeriodS"] = \
			self.profile["broadcastPeriodMS"]/1000.0
		self.profile["periodS"] = STD_PERIOD_MS/1000.0
		self.profile["passcode"] = "good_luck"
		self.profile["maxLength"] = STD_MAX_LENGTH
		self.profile["maxTimeouts"] = STD_MAX_TIMEOUTS

		self.profile["mainQueueSize"] = STD_MAIN_QUEUE_SIZE
		self.profile["misoQueueSize"] = STD_MISO_QUEUE_SIZE
		self.profile["printerQueueSize"] = STD_PRINTER_QUEUE_SIZE

		# Wind tunnel ----------------------------------------------------------
		
		# Slave list ...........................................................
		self.slaveList = [	
		
		# ALEX'S
			(
				random.choice(names.coolNames),		# Name
				"00:80:e1:38:00:2a",				# MAC
				21,									# Active fans
				(4,7),								# Grid placement
				(0,0),								# Module dimensions
				"1,2,3,4,5,6,7,8,9"					# Module assignment
			),
			
			(
				"Ghost1",							# Name
				"00000000000000:XX",				# MAC
				21,									# Active fans
				(0,0),								# Grid placement
				(3,3),								# Module dimensions
				"1,2,3,4,5,6,7,8,9"					# Module assignment
			)
		]	
		"""		
			[
				random.choice(names.coolNames),		# Name
				"00:80:e1:45:00:46",				# MAC 
				 21									# Active fans
				 None,								# Grid placement
				(1,1),								# Module dimensions
				''									# Module assignment
			]
		"""
		#]
		""" BASEMENT WIND TUNNEL:

			[
				random.choice(names.coolNames),		# Name
				"00:80:e1:2f:00:1d",				# MAC 
				 21									# Active fans
				(1,1),								# Module dimensions
				''									# Module assignment
			]
		"""
		
		# End Slave list ........................................................ 

		self.profile["dimensions"] = (11,11)
		self.profile["maxFans"] =  DEFAULT_MAX_FANS

		# Fan array ------------------------------------------------------------
		self.profile["fanModel"] = DEFAULT_FAN_MODEL
		self.profile["fanMode"]  = SINGLE
	 	self.profile["targetRelation"]  = DEFAULT_TARGET_RELATION
		self.profile["chaserTolerance"]  = DEFAULT_CHASER_TOLERANCE
		self.profile["counterCounts"] = DEFAULT_COUNTER_COUNTS
		self.profile["counterTimeoutMS"]  = DEFAULT_COUNTER_TIMEOUT_MS
		self.profile["pulsesPerRotation"]  = DEFAULT_PULSES_PER_ROTATION
		self.profile["maxRPM"]  = DEFAULT_MAX_RPM
		self.profile["minRPM"]  = DEFAULT_MIN_RPM
		self.profile["minDC"]  = DEFAULT_MIN_DC
		
		self.profile["defaultModuleDimensions"] = DEFAULT_MODULE_DIMENSIONS
		self.profile["defaultModuleAssignment"] = \
                    DEFAULT_MODULE_ASSIGNMENT
