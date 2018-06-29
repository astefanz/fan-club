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
SPEC_CAST_MODULE_ASSIGNMENT_CH = SPEC_CAST_MODULE_ASSIGNMENT_FRONT

SPEC_CAST_MODULE_DIMENSIONS = (3,3) # (rows, columns) 
SPEC_CAST_PINOUT = "ETRGMLWXPQJKUVBADC edcb_^ng`w\\]porqfs"
SPEC_CAST_DIMENSIONS = (36, 36)
SPEC_CAST_MAX_FANS = 18
SPEC_CAST_DEF_ACTIVE_FANS = 18

SPEC_CAST_DIMS_12 = (36,36) # (9, 12)


# .............................................................................. 

# Values to be used in provisional FCArchiver: 
DEF_MODULE_DIMENSIONS = SPEC_CAST_MODULE_DIMENSIONS
DEF_MODULE_ASSIGNMENT = SPEC_CAST_MODULE_ASSIGNMENT_FRONT
DEF_PINOUT =  SPEC_CAST_PINOUT
DEF_DIMENSIONS = SPEC_CAST_DIMS_12

# PREDEFINED SLAVE LISTS =======================================================

SLAVELIST_CAST_ALL = [\
	[
		"Module 1",
		"00:80:e1:48:00:38",
		18,
		(0,0),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 2",
		"00:80:e1:48:00:3e",
		18,
		(0,3),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 3",
		"00:80:e1:43:00:1f",
		18,
		(0,6),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 4",
		"00:80:e1:43:00:36",
		18,
		(0,9),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 5",
		"00:80:e1:47:00:3a",
		18,
		(0,12),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 6",
		"00:80:e1:41:00:36",
		18,
		(0,15),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 7",
		"00:80:e1:47:00:25",
		18,
		(0,18),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 8",
		"00:80:e1:40:00:3d",
		18,
		(0,21),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 9",
		"00:80:e1:47:00:44",
		18,
		(0,24),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 10",
		"00:80:e1:36:00:21",
		18,
		(0,27),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 11",
		"00:80:e1:37:00:21",
		18,
		(0,30),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 12",
		"00:80:e1:38:00:21",
		18,
		(0,33),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 13",
		"00:80:e1:28:00:3f",
		18,
		(3,0),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 14",
		"00:80:e1:1f:00:35",
		18,
		(3,3),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 15",
		"00:80:e1:40:00:37",
		18,
		(3,6),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 16",
		"00:80:e1:4b:00:2a",
		18,
		(3,9),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 17",
		"00:80:e1:46:00:3a",
		18,
		(3,12),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 18",
		"00:80:e1:2b:00:3b",
		18,
		(3,15),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 19",
		"00:80:e1:37:00:37",
		18,
		(3,18),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 20",
		"00:80:e1:4a:00:25",
		18,
		(3,21),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 21",
		"00:80:e1:40:00:3f",
		18,
		(3,24),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 22",
		"00:80:e1:53:00:3a",
		18,
		(3,27),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 23",
		"00:80:e1:47:00:38",
		18,
		(3,30),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 24",
		"00:80:e1:1e:00:24",
		18,
		(3,33),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 25",
		"00:80:e1:36:00:1c",
		18,
		(6,0),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 26",
		"00:80:e1:2f:00:2f",
		18,
		(6,3),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 27",
		"00:80:e1:32:00:35",
		18,
		(6,6),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 28",
		"00:80:e1:2b:00:28",
		18,
		(6,9),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 29",
		"00:80:e1:1b:00:35",
		18,
		(6,12),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 30",
		"00:80:e1:33:00:18",
		18,
		(6,15),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 31",
		"00:80:e1:4b:00:22",
		18,
		(6,18),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 32",
		"00:80:e1:50:00:2d",
		18,
		(6,21),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 33",
		"00:80:e1:45:00:1f",
		18,
		(6,24),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 34",
		"00:80:e1:35:00:37",
		18,
		(6,27),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 35",
		"00:80:e1:32:00:21",
		18,
		(6,30),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 36",
		"00:80:e1:2b:00:36",
		18,
		(6,33),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 37",
		"00:80:e1:2e:00:46",
		18,
		(9,0),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 38",
		"00:80:e1:31:00:47",
		18,
		(9,3),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 39",
		"00:80:e1:45:00:3a",
		18,
		(9,6),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 40",
		"00:80:e1:46:00:2c",
		18,
		(9,9),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 41",
		"00:80:e1:40:00:1c",
		18,
		(9,12),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 42",
		"00:80:e1:38:00:36",
		18,
		(9,15),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 43",
		"00:80:e1:50:00:1f",
		18,
		(9,18),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 44",
		"00:80:e1:39:00:24",
		18,
		(9,21),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 45",
		"00:80:e1:41:00:37",
		18,
		(9,24),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 46",
		"00:80:e1:35:00:3e",
		18,
		(9,27),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 47",
		"00:80:e1:1e:00:3c",
		18,
		(9,30),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 48",
		"00:80:e1:3b:00:25",
		18,
		(9,33),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 49",
		"00:80:e1:32:00:47",
		18,
		(12,0),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 50",
		"00:80:e1:45:00:45",
		18,
		(12,3),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 51",
		"00:80:e1:4f:00:35",
		18,
		(12,6),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 52",
		"00:80:e1:3a:00:1a",
		18,
		(12,9),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 53",
		"00:80:e1:24:00:35",
		18,
		(12,12),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 54",
		"00:80:e1:3d:00:33",
		18,
		(12,15),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 55",
		"00:80:e1:49:00:3a",
		18,
		(12,18),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 56",
		"00:80:e1:35:00:3b",
		18,
		(12,21),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 57",
		"00:80:e1:23:00:30",
		18,
		(12,24),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 58",
		"00:80:e1:31:00:2a",
		18,
		(12,27),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 59",
		"00:80:e1:47:00:45",
		18,
		(12,30),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 60",
		"00:80:e1:46:00:37",
		18,
		(12,33),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 61",
		"00:80:e1:1b:00:31",
		18,
		(15,0),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 62",
		"00:80:e1:33:00:36",
		18,
		(15,3),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 63",
		"00:80:e1:2e:00:2d",
		18,
		(15,6),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 64",
		"00:80:e1:20:00:3b",
		18,
		(15,9),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 65",
		"00:80:e1:3f:00:37",
		18,
		(15,12),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 66",
		"00:80:e1:1d:00:35",
		18,
		(15,15),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 67",
		"00:80:e1:1f:00:25",
		18,
		(15,18),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 68",
		"00:80:e1:40:00:35",
		18,
		(15,21),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 69",
		"00:80:e1:45:00:25",
		18,
		(15,24),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 70",
		"00:80:e1:2d:00:19",
		18,
		(15,27),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 71",
		"00:80:e1:29:00:1c",
		18,
		(15,30),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 72",
		"00:80:e1:3d:00:32",
		18,
		(15,33),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 73",
		"00:80:e1:44:00:43",
		18,
		(18,0),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 74",
		"00:80:e1:26:00:35",
		18,
		(18,3),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 75",
		"00:80:e1:22:00:32",
		18,
		(18,6),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 76",
		"00:80:e1:34:00:37",
		18,
		(18,9),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 77",
		"00:80:e1:2a:00:28",
		18,
		(18,12),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 78",
		"00:80:e1:40:00:21",
		18,
		(18,15),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 79",
		"00:80:e1:31:00:31",
		18,
		(18,18),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 80",
		"00:80:e1:44:00:32",
		18,
		(18,21),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 81",
		"00:80:e1:4a:00:30",
		18,
		(18,24),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 82",
		"00:80:e1:4f:00:3b",
		18,
		(18,27),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 83",
		"00:80:e1:44:00:45",
		18,
		(18,30),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 84",
		"00:80:e1:25:00:35",
		18,
		(18,33),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 85",
		"00:80:e1:1f:00:3c",
		18,
		(21,0),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 86",
		"00:80:e1:48:00:27",
		18,
		(21,3),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 87",
		"00:80:e1:1c:00:30",
		18,
		(21,6),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 88",
		"00:80:e1:38:00:39",
		18,
		(21,9),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 89",
		"00:80:e1:36:00:28",
		18,
		(21,12),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 90",
		"00:80:e1:4a:00:1b",
		18,
		(21,15),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 91",
		"00:80:e1:27:00:29",
		18,
		(21,18),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 92",
		"00:80:e1:2b:00:1e",
		18,
		(21,21),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 93",
		"00:80:e1:1b:00:30",
		18,
		(21,24),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 94",
		"00:80:e1:51:00:22",
		18,
		(21,27),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 95",
		"00:80:e1:4a:00:35",
		18,
		(21,30),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 96",
		"00:80:e1:39:00:35",
		18,
		(21,33),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 97",
		"00:80:e1:4f:00:1f",
		18,
		(24,0),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 98",
		"00:80:e1:45:00:36",
		18,
		(24,3),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 99",
		"00:80:e1:2b:00:3f",
		18,
		(24,6),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 100",
		"00:80:e1:3e:00:1c",
		18,
		(24,9),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 101",
		"00:80:e1:3e:00:28",
		18,
		(24,12),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 102",
		"00:80:e1:2c:00:30",
		18,
		(24,15),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 103",
		"00:80:e1:2e:00:47",
		18,
		(24,18),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 104",
		"00:80:e1:45:00:32",
		18,
		(24,21),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 105",
		"00:80:e1:1d:00:32",
		18,
		(24,24),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 106",
		"00:80:e1:2e:00:1c",
		18,
		(24,27),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 107",
		"00:80:e1:30:00:3e",
		18,
		(24,30),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 108",
		"00:80:e1:33:00:28",
		18,
		(24,33),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 109",
		"00:80:e1:31:00:1c",
		18,
		(27,0),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 110",
		"00:80:e1:4f:00:2f",
		18,
		(27,3),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 111",
		"00:80:e1:4f:00:2d",
		18,
		(27,6),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 112",
		"00:80:e1:2c:00:35",
		18,
		(27,9),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 113",
		"00:80:e1:30:00:28",
		18,
		(27,12),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 114",
		"00:80:e1:46:00:46",
		18,
		(27,15),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 115",
		"00:80:e1:35:00:32",
		18,
		(27,18),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 116",
		"00:80:e1:42:00:3f",
		18,
		(27,21),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 117",
		"00:80:e1:4b:00:25",
		18,
		(27,24),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 118",
		"00:80:e1:40:00:36",
		18,
		(27,27),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 119",
		"00:80:e1:30:00:3b",
		18,
		(27,30),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 120",
		"00:80:e1:49:00:1d",
		18,
		(27,33),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 121",
		"00:80:e1:22:00:30",
		18,
		(30,0),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 122",
		"00:80:e1:41:00:28",
		18,
		(30,3),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 123",
		"00:80:e1:51:00:2d",
		18,
		(30,6),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 124",
		"00:80:e1:4a:00:36",
		18,
		(30,9),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 125",
		"00:80:e1:44:00:3f",
		18,
		(30,12),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 126",
		"00:80:e1:2a:00:1e",
		18,
		(30,15),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 127",
		"00:80:e1:3c:00:31",
		18,
		(30,18),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 128",
		"00:80:e1:44:00:3a",
		18,
		(30,21),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 129",
		"00:80:e1:45:00:46",
		18,
		(30,24),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 130",
		"00:80:e1:35:00:21",
		18,
		(30,27),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 131",
		"00:80:e1:3c:00:47",
		18,
		(30,30),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 132",
		"00:80:e1:47:00:1f",
		18,
		(30,33),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 133",
		"00:80:e1:2d:00:2d",
		18,
		(33,0),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 134",
		"00:80:e1:43:00:28",
		18,
		(33,3),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 135",
		"00:80:e1:39:00:36",
		18,
		(33,6),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 136",
		"00:80:e1:21:00:35",
		18,
		(33,9),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 137",
		"00:80:e1:2d:00:46",
		18,
		(33,12),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 138",
		"00:80:e1:4d:00:1f",
		18,
		(33,15),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 139",
		"00:80:e1:4c:00:2a",
		18,
		(33,18),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 140",
		"00:80:e1:46:00:21",
		18,
		(33,21),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 141",
		"00:80:e1:46:00:43",
		18,
		(33,24),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 142",
		"00:80:e1:4e:00:3b",
		18,
		(33,27),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 143",
		"00:80:e1:33:00:3e",
		18,
		(33,30),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	],
	[
		"Module 144",
		"00:80:e1:49:00:22",	
		#"00:80:e1:3c:00:1b",
		18,
		(33,33),
		SPEC_CAST_MODULE_DIMENSIONS,
		SPEC_CAST_MODULE_ASSIGNMENT_CH
	]
]

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
DEF_SLAVELIST = SLAVELIST_CAST_ALL

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

