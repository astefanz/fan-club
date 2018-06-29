################################################################################
## Project: Fan Club Mark II "Master" ## File: hardcoded.py                   ##
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
Auxiliary file for provisional, pre-defined profile values.

"""
################################################################################
import random # Random names, boy
import names


# SPECIAL VALUES ===============================================================

# Basement:
SPEC_BASEMENT_MODULE_ASSIGNMENT = \
    "1,2,3,4,5,6,7,8,9,10,,11,12,13,14,15,16,17,18,19,20"

SPEC_BASEMENT_MODULE_DIMENSIONS = (2,11) # (rows, columns)

# CAST:
SPEC_CAST_MODULE_ASSIGNMENT_BACK = \
	"1,3,5,7,9,11,13,15,17"
	# NOTE (UPSTREAM)

SPEC_CAST_MODULE_ASSIGNMENT_FRONT = \
	"0,2,4,6,8,10,12,14,16"
	# NOTE (DOWNSTREAM)

SPEC_CAST_MODULE_DIMENSIONS = (3,3) # (rows, columns) 
SPEC_CAST_PINOUT = "ETRGMLWXPQJKUVBADC edcb_^ng`w\\]porqfs"
SPEC_CAST_DIMENSIONS = (36, 36)
SPEC_CAST_MAX_FANS = 18
SPEC_CAST_DEF_ACTIVE_FANS = 18

SPEC_CAST_DIMS_12 = (9, 12)

# .............................................................................. 

# Values to be used in provisional FCArchiver: 
DEF_MODULE_DIMENSIONS = SPEC_CAST_MODULE_DIMENSIONS
DEF_MODULE_ASSIGNMENT = SPEC_CAST_MODULE_ASSIGNMENT_FRONT
DEF_PINOUT =  SPEC_CAST_PINOUT
DEF_DIMENSIONS = SPEC_CAST_DIMS_12

# PREDEFINED SLAVE LISTS =======================================================

SLAVELIST_CAST_12 = [\
	[	
		"R3-C4",
		"00:80:e1:21:00:35",
		18,
		(6, 9),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_FRONT
	],
	[	
		"R2-C4",
		"00:80:e1:4a:00:36",
		18,
		(3, 9),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_FRONT
	],
	[	
		"42-C3",
		"00:80:e1:51:00:2d",
		18,
		(3, 6),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_FRONT
	],
	[	
		"R3-C1",
		"00:80:e1:2d:00:2d",
		18,
		(6, 0),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_FRONT
	],
	[	
		"R1-C2",
		"00:80:e1:4f:00:2f",
		18,
		(3, 0),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_FRONT
	],

	[	
		"T-L",
		"00:80:e1:31:00:1c",
		18,
		(0, 0),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_FRONT
	],
	[	
		"R1-C3",
		"00:80:e1:4f:00:2d",
		18,
		(0, 6),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_FRONT
	],

	[	
		"R3-C3",
		"00:80:e1:39:00:36",
		18,
		(6, 6),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_FRONT
	],


	[	
		"R3-C2",
		"00:80:e1:43:00:28",
		18,
		(6, 3),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_FRONT
	],

	[	
		"R2-C1",
		"00:80:e1:22:00:30",
		18,
		(3, 0),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_FRONT
	],
	[	
		"R2-C2",
		"00:80:e1:41:00:28",
		18,
		(3, 3),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_FRONT
	],
	[	
		"R1-C4",
		"00:80:e1:41:00:28",
		18,
		(0, 9),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_FRONT
	]
]

SLAVELIST_BASEMENT = [\
			[
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
			]
] # END SLAVELIST_BASEMENT	
		
SLAVELIST_ALEX = [\
			[
				random.choice(names.coolNames),		# Name
				"00:80:e1:38:00:2a",				# MAC
				21,									# Active fans
				(4,7),								# Grid placement
				(0,0),								# Module dimensions
				"1,2,3,4,5,6,7,8,9"					# Module assignment
			],
			
			[
				"Ghost1",							# Name
				"00000000000000:XX",				# MAC
				21,									# Active fans
				(0,0),								# Grid placement
				(3,3),								# Module dimensions
				"1,2,3,4,5,6,7,8,9"					# Module assignment
			],
		
			[
				random.choice(names.coolNames),		# Name
				"00:80:e1:45:00:46",				# MAC 
				21,									# Active fans
				None,								# Grid placement
				(1,1),								# Module dimensions
				''									# Module assignment
			]\
] # End SLAVELIST_ALEX

# Slavelist to be used:
DEF_SLAVELIST = []

# DEFAULT VALUES ===============================================================

DEF_PROFILE_NAME = "[ALPHA]"
	
# COMMUNICATIONS:
DEF_BROADCAST_PORT  = 65000
DEF_PERIOD_MS = 100 # (millisecond(s))
DEF_BROADCAST_PERIOD_MS = 1000
DEF_MAX_LENGTH = 512
DEF_MAX_TIMEOUTS = 10

DEF_MAIN_QUEUE_SIZE = 20
DEF_SLAVE_QUEUE_SIZE= 100
DEF_BROADCAST_QUEUE_SIZE = 2
DEF_LISTENER_QUEUE_SIZE = 3
DEF_MISO_QUEUE_SIZE = 2
DEF_PRINTER_QUEUE_SIZE = 3

# FAN ARRAY:
# NOTE: That of GALCIT's "basement wind tunnel," using DELTA PFR0912XHE-SP00
# fans.

DEF_FAN_MODEL = "DELTA PFR0912XHE-SP00"
DEF_FAN_MODE = -1
DEF_TARGET_RELATION = (1.0,0.0) # (For double fans, irrelevant if on SINGLE)
DEF_CHASER_TOLERANCE = 0.02 # (2% of target RPM)
DEF_FAN_FREQUENCY_HZ = 25000 # 25 KHz PWM signal
DEF_COUNTER_COUNTS = 2 # (Measure time between pulses once)
DEF_COUNTER_TIMEOUT_MS = 30 # (Assume fan is not spinning after 30ms)
DEF_PULSES_PER_ROTATION = 2 # (Fan generates 2 pulses per rotation)
DEF_MAX_RPM = 11500 # (Maximum nominal RPM)
DEF_MIN_RPM = 0  # (Minimum nominal RPM)
DEF_MIN_DC = 0.0 # NOTE (10% duty cycle corresponds to ~1185 RPM)
DEF_MAX_FANS = SPEC_CAST_MAX_FANS
DEF_MAX_FAN_TIMEOUTS = 1 

