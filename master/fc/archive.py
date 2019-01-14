################################################################################
## Project: Fanclub Mark IV "Master"  ## File: archive.py                     ##
##----------------------------------------------------------------------------##
## CALIFORNIA INSTITUTE OF TECHNOLOGY ## GRADUATE AEROSPACE LABORATORY ##     ##
## CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES                      ##     ##
##----------------------------------------------------------------------------##
##      ____      __      __  __      _____      __      __    __    ____     ##
##     / __/|   _/ /|    / / / /|  _- __ __\    / /|    / /|  / /|  / _  \    ##
##    / /_ |/  / /  /|  /  // /|/ / /|__| _|   / /|    / /|  / /|/ /   --||   ##
##   / __/|/ _/    /|/ /   / /|/ / /|    __   / /|    / /|  / /|/ / _  \|/    ##
##  / /|_|/ /  /  /|/ / // //|/ / /|__- / /  / /___  / -|_ - /|/ /     /|     ##
## /_/|/   /_/ /_/|/ /_/ /_/|/ |\ ___--|_|  /_____/| |-___-_|/  /____-/|/     ##
## |_|/    |_|/|_|/  |_|/|_|/   \|___|-    |_____|/   |___|     |____|/       ##
##                   _ _    _    ___   _  _      __  __   __                  ##
##                  | | |  | |  | T_| | || |    |  ||_ | | _|                 ##
##                  | _ |  |T|  |  |  |  _|      ||   \\_//                   ##
##                  || || |_ _| |_|_| |_| _|    |__|  |___|                   ##
##                                                                            ##
##----------------------------------------------------------------------------##
## Alejandro A. Stefan Zavala ## <astefanz@berkeley.edu>   ##                 ##
## Chris J. Dougherty         ## <cdougher@caltech.edu>    ##                 ##
## Marcel Veismann            ## <mveisman@caltech.edu>    ##                 ##
################################################################################

""" ABOUT ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 + The "profile" represents the data that distinguishes a fan array, as well as
 + a specific FC configuration. The class FCArchive manages such profiles.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################

## GLOBALS #####################################################################
VERSION = "IV-1"

CODE = 1
SYMBOL = "AC"

# Platforms:
UNKNOWN = -1
WINDOWS = 0
MACOS = 1
LINUX = 2

# Fan modes:
SINGLE = 1
DOUBLE = 2

# PARAMETER NAMES ==============================================================

# Core -------------------------------------------------------------------------
name = 1
description = 2
platform = 3

# Network ----------------------------------------------------------------------
broadcastPort  = 100
broadcastPeriodMS = 101
broadcastPeriodS = 102
periodMS = 103
periodS = 104
maxLength = 105
maxTimeouts = 106

mainQueueSize = 107
slaveQueueSize= 108
broadcastQueueSize = 109
listenerQueueSize = 110
misoQueueSize = 111
printerQueueSize = 112
passcode = 113

defaultSlave = 114
savedSlaves = 115

# For each Slave .........
SV_name = 116
SV_mac = 117
SV_index = 118
SV_fanModel = 119
SV_fanMode = 120
SV_targetRelation = 121
SV_chaserTolerance = 122
SV_fanFrequencyHZ = 123
SV_counterCounts = 124
SV_counterTimeoutMS = 125
SV_pulsesPerRotation = 126
SV_maxRPMs = 127
SV_minRPMs = 128
SV_minDCs = 129
SV_maxFans = 130
SV_pinout = 131
# ........................

pinouts = 132

# Fan array --------------------------------------------------------------------
defaultModule = 200

fanArrays = 204

# TODO: Finish writing down items (See spec.). Don't forget to add prefixes like
# FA_ and MD_

# For each fan array .....
name = 205
description = 206
rows = 208
columns = 209
layers = 210
modules = 211

# For each module . . . .
slaveIndex = 300
row = 301
column = 302
rows = 303
columns = 304

# . . . . . . . . . . . .
# ........................

"""
fanModel = 31
fanMode =  32
targetRelation = 33
chaserTolerance = 34
fanFrequencyHZ = 35
counterCounts = 36
counterTimeoutMS = 37
pulsesPerRotation = 38
maxRPM = 39
minRPM = 310
minDC = 311
maxFans = 312
maxFanTimeouts = 313
defaultPinout = 314

rows = 41
columns = 42
layers = 43
modules = 44
defaultModuleDimensions = 45
defaultModuleAssignment = 46
"""

# FAN MODES (Not parameters):
SINGLE = -1
DOUBLE = -2

# PARAMETER LIST ITEMS:
VALUE = 0
TYPE = 1
LOCK = 2

# ARRAY MAPPING INDICES:
M_INDEX = 0
M_ROW = 1
M_COLUMN = 2
M_NUMROWS = 3
M_NUMCOLUMNS = 4
M_NUMFANS = 5
M_ASSIGNMENT = 6
## MAIN ########################################################################

class FCArchive:

    """
    Create a new FCProfile.
    - PLATFORM: One of the constants (defined in fc.profile) that represents
      a supported platform --WINDOWS, MACOS, LINUX or OTHER.
    """
    def __init__(self, platform):
        self.profile = {}

