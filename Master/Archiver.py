################################################################################
## Project: Fan Club Mark II "Master" ## File: Archiver.py                    ##
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
DEFAULT_TARGET_RELATION = (1.0,0.0) # (For double fans, irrelevant if on SINGLE)
DEFAULT_CHASER_TOLERANCE = 0.02 # (2% of target RPM)
DEFAULT_FAN_FREQUENCY_HZ = 25000 # 25 KHz PWM signal
DEFAULT_COUNTER_COUNTS = 1 # (Measure time between pulses once)
DEFAULT_COUNTER_TIMEOUT_MS = 30 # (Assume fan is not spinning after 30ms)
DEFAULT_PULSES_PER_ROTATION = 2 # (Fan generates 2 pulses per rotation)
DEFAULT_MAX_RPM = 11500 # (Maximum nominal RPM)
DEFAULT_MIN_RPM = 1185  # (Minimum nominal RPM)
DEFAULT_MIN_DC = 0.1 # (10% duty cycle corresponds to ~1185 RPM)
DEFAULT_MAX_FANS = 21
DEFAULT_MAX_FAN_TIMEOUTS = 1 

DEFAULT_MODULE_DIMENSIONS = (2, 11) # (rows, columns)
DEFAULT_MODULE_ASSIGNMENT = \
    "1,2,3,4,5,6,7,8,9,10,,11,12,13,14,15,16,17,18,19,20"

## CLASS DEFINITION ############################################################

class Archiver:
	# ABOUT: This module holds all "variable" data that should be kept in nonvo-
	# latile storage.

	def __init__(self):
		# ABOUT: Constructor for class Archiver.
		
		# ASSEMBLE DATA STRUCTURE ==============================================
		self.profile = {}

		# Administrative data --------------------------------------------------
		self.profile["name"] = [PROFILE_NAME
		self.profile["description"] = ["This is a test Profile"

		# Communications -------------------------------------------------------
		self.profile["broadcastPort"] = [STD_BROADCAST_PORT, int, threading.Lock()]
		self.profile["periodMS"] = [STD_PERIOD_MS, int, threading.Lock()]
		self.profile["broadcastPeriodMS"] = [STD_BROADCAST_PERIOD_MS, int, threading.Lock()]
		self.profile["broadcastPeriodS"] = [\,
			self.profile["broadcastPeriodMS"]/1000.0, float, threading.Lock()]
		self.profile["periodS"] = [STD_PERIOD_MS/1000.0, float, threading.Lock()]
		self.profile["passcode"] = ["good_luck", str, threading.Lock()]
		self.profile["maxLength"] = [STD_MAX_LENGTH, int, threading.Lock()]
		self.profile["maxTimeouts"] = [STD_MAX_TIMEOUTS, int, threading.Lock()]
		self.profile["mainQueueSize"] = [STD_MAIN_QUEUE_SIZE, int, threading.Lock()]
		self.profile["misoQueueSize"] = [STD_MISO_QUEUE_SIZE, int, threading.Lock()]
		self.profile["printerQueueSize"] = [STD_PRINTER_QUEUE_SIZE, int, threading.Lock()]

		# Wind tunnel ----------------------------------------------------------
		
		# Slave list ...........................................................
		self.slaveList = \
                        [[
				random.choice(names.coolNames),		# Name
				"00:80:e1:4b:00:36",				# MAC 
				 20,									# Active fans
                                (7,5),
				(4,6),								# Module dimensions
				'20,18,14,10,,,19,17,13,9,6,3,,16,12,8,5,2,,15,11,7,4,1'									# Module assignment
			],
                        [
				random.choice(names.coolNames),		# Name
				"00:80:e1:2f:00:1d",				# MAC 
				 20,									# Active fans
                                (7,0),
				(4,6),								# Module dimensions
				',,14,10,6,,20,17,13,9,5,,19,16,12,8,4,2,18,15,11,7,3,1'									# Module assignment
			],
                        [
				random.choice(names.coolNames),		# Name
				"00:80:e1:29:00:2e",				# MAC 
				 20,									# Active fans
                                (3,0),
				(5,6),								# Module dimensions
				'19,20,,,,,14,15,16,17,18,,8,9,10,11,12,13,3,4,5,6,7,,1,2,,,,'									# Module assignment
			],
                        [
				random.choice(names.coolNames),		# Name
				"00:80:e1:27:00:3e",				# MAC 
				 20,									# Active fans
                                (0,0),
				(4,6),								# Module dimensions
				'1,2,3,4,5,,6,7,8,9,10,,11,12,13,14,15,16,,,17,18,19,20'									# Module assignment
			],
                        [
				random.choice(names.coolNames),		# Name
				"00:80:e1:4b:00:42",				# MAC 
				 20,									# Active fans
                                (0,5),
				(4,6),								# Module dimensions
				'20,18,14,10,6,3,19,17,13,9,5,2,,16,12,8,4,1,,15,11,7,,,'									# Module assignment
			],
                        [
				random.choice(names.coolNames),		# Name
				"00:80:e1:47:00:3d",				# MAC 
				 21,									# Active fans
                                (3,5),
				(5,6),								# Module dimensions
				',,,,10,5,21,19,16,13,9,4,,18,15,12,8,3,20,17,14,11,7,2,,,,,6,1'									# Module assignment
			]]	
		
		# ALEX'S
                """
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
		"""
		
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
		
		# BASEMENT WIND TUNNEL:

			
                """
                                ,
                        [
				random.choice(names.coolNames),		# Name
				"00:80:e1:2f:00:1d",				# MAC 
				 21									# Active fans
				(1,1),								# Module dimensions
				''									# Module assignment
			],
                        [
				random.choice(names.coolNames),		# Name
				"00:80:e1:2f:00:1d",				# MAC 
				 21									# Active fans
				(1,1),								# Module dimensions
				''									# Module assignment
			],
                        [
				random.choice(names.coolNames),		# Name
				"00:80:e1:2f:00:1d",				# MAC 
				 21									# Active fans
				(1,1),								# Module dimensions
				''									# Module assignment
			],
                        [
				random.choice(names.coolNames),		# Name
				"00:80:e1:2f:00:1d",				# MAC 
				 21									# Active fans
				(1,1),								# Module dimensions
				''									# Module assignment
			],
                        [
				random.choice(names.coolNames),		# Name
				"00:80:e1:2f:00:1d",				# MAC 
				 21									# Active fans
				(1,1),								# Module dimensions
				''									# Module assignment
			]
		"""
		
		
		# End Slave list ........................................................ 

		self.profile["dimensions"] = (11,11), int, threading.Lock()] 
		self.profile["maxFans"] =  DEFAULT_MAX_FANS, int, threading.Lock()] 
, int, threading.Lock()] 
		# Fan array ------------------------------------------------------------, int, threading.Lock()] 
		self.profile["fanModel"] = DEFAULT_FAN_MODEL, int, threading.Lock()] 
		self.profile["fanMode"]  = SINGLE, int, threading.Lock()] 
	 	self.profile["targetRelation"]  = DEFAULT_TARGET_RELATION, int, threading.Lock()] 
		self.profile["chaserTolerance"]  = DEFAULT_CHASER_TOLERANCE, int, threading.Lock()] 
		self.profile["fanFrequencyHZ"] = DEFAULT_FAN_FREQUENCY_HZ, int, threading.Lock()] 
		self.profile["counterCounts"] = DEFAULT_COUNTER_COUNTS, int, threading.Lock()] 
		self.profile["counterTimeoutMS"]  = DEFAULT_COUNTER_TIMEOUT_MS, int, threading.Lock()] 
		self.profile["pulsesPerRotation"]  = DEFAULT_PULSES_PER_ROTATION, int, threading.Lock()] 
		self.profile["maxRPM"]  = DEFAULT_MAX_RPM, int, threading.Lock()] 
		self.profile["minRPM"]  = DEFAULT_MIN_RPM, int, threading.Lock()] 
		self.profile["minDC"]  = DEFAULT_MIN_DC, int, threading.Lock()] 
		self.profile["maxFanTimeouts"] = DEFAULT_MAX_FAN_TIMEOUTS, int, threading.Lock()] 
		, int, threading.Lock()] 
		self.profile["defaultModuleDimensions"] = DEFAULT_MODULE_DIMENSIONS, int, threading.Lock()] 
		self.profile["defaultModuleAssignment"] = \, int, threading.Lock()] 
                    DEFAULT_MODULE_ASSIGNMENT, int, threading.Lock()] 

