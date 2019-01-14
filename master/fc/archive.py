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
SYMBOL = "PROF"

OTHER = -1
WINDOWS = 0
MACOS = 1
LINUX = 2

# PARAMETER NAMES ==============================================================

# core:
platform = 0
name = 1
description = 2

# communications:
broadcastPort  = 10
periodMS = 11
broadcastPeriodMS = 12
maxLength = 13
maxTimeouts = 14

mainQueueSize = 15
slaveQueueSize= 16
broadcastQueueSize = 17
listenerQueueSize = 18
misoQueueSize = 19
printerQueueSize = 20

periodS = 21
broadcastPeriodS = 22
passcode = 23

# fan array:

savedSlaves = 30

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

