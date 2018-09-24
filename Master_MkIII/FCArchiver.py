################################################################################
## Project: Fan Club Mark II "Master" ## File: FCArchiver.py                  ##
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

VERSION = "Dynamic 0"

# ** WARNING ** * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
# THIS MODULE IS IN AN EARLY PROTYTPE "STUB" STAGE. IT HAS NO FILE HANDLING CA-
# PABILITIES YET AND WILL ONLY YIELD PREDEFINED VALUES FOR THE DEVELOPMENT OF
# THE REST OF THE CODE
#  * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

## DEPENDENCIES ################################################################

# Data:
import threading
import copy

# Provisional:
from auxiliary import hardcoded as hc
from auxiliary.debug import d

## CONSTANT VALUES #############################################################

# PARAMETER NAMES ==============================================================
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


## CLASS DEFINITION ############################################################

class FCArchiver:
    # ABOUT: This module holds all "variable" data that should be kept in nonvo-
    # latile storage.

    def __init__(self, filename = None): # =====================================
        # ABOUT: Constructor for class FCArchiver.

        self.filename = 'tmp.fanarray'

        # ASSEMBLE DATA STRUCTURE ==============================================
        self.profile = {}

        # Administrative data --------------------------------------------------
        self.profile[name] = [hc.DEF_PROFILE_NAME, str, 
            threading.Lock()]
        self.profile[description] = ["This is a test Profile", str, 
            threading.Lock()]

        # Communications -------------------------------------------------------
        self.profile[broadcastPort] = \
            [hc.DEF_BROADCAST_PORT, int, threading.Lock()]
        self.profile[periodMS] = \
            [hc.DEF_PERIOD_MS, int, threading.Lock()]
        self.profile[broadcastPeriodMS] = \
            [hc.DEF_BROADCAST_PERIOD_MS, int, threading.Lock()]
        self.profile[broadcastPeriodS] = [\
            self.profile[broadcastPeriodMS][0]/1000.0,
            float, threading.Lock()]
        self.profile[periodS] = \
            [hc.DEF_PERIOD_MS/1000.0, float, threading.Lock()]
        self.profile[passcode] = \
            ["CT", str, threading.Lock()]
        self.profile[maxLength] = \
            [hc.DEF_MAX_LENGTH, int, threading.Lock()]
        self.profile[maxTimeouts] = \
            [hc.DEF_MAX_TIMEOUTS, int, threading.Lock()]
        self.profile[mainQueueSize] = \
            [hc.DEF_MAIN_QUEUE_SIZE, int, threading.Lock()]
        self.profile[misoQueueSize] = \
            [hc.DEF_MISO_QUEUE_SIZE, int, threading.Lock()]
        self.profile[printerQueueSize] =\
            [hc.DEF_PRINTER_QUEUE_SIZE, int, threading.Lock()]

        # Wind tunnel ----------------------------------------------------------
        
        # Slave list ...........................................................
        self.profile[savedSlaves] = \
            [hc.DEF_SLAVELIST, list, threading.Lock()]

        # End Slave list ....................................................... 
        self.profile[rows] = [hc.DEF_GRID_ROWS, int, threading.Lock()]
        self.profile[columns] = [hc.DEF_GRID_COLUMNS, int, threading.Lock()]
        self.profile[layers] = [hc.DEF_GRID_LAYERS, int, threading.Lock()]
        self.profile[modules] = [hc.DEF_GRID_MODULES, tuple, threading.Lock()]

        self.profile[maxFans] =  [hc.DEF_MAX_FANS, int, threading.Lock()]

        # Fan array ------------------------------------------------------------
        self.profile[fanModel] = [hc.DEF_FAN_MODEL, str, threading.Lock()]
        self.profile[fanMode]  = [SINGLE, int, threading.Lock()]
        self.profile[targetRelation] = \
            [hc.DEF_TARGET_RELATION, tuple, threading.Lock()]
        self.profile[chaserTolerance]  = \
            [hc.DEF_CHASER_TOLERANCE, float, threading.Lock()]
        self.profile[fanFrequencyHZ] = \
            [hc.DEF_FAN_FREQUENCY_HZ, int, threading.Lock()]
        self.profile[counterCounts] = \
            [hc.DEF_COUNTER_COUNTS, int, threading.Lock()]
        self.profile[counterTimeoutMS]  = \
            [hc.DEF_COUNTER_TIMEOUT_MS, int, threading.Lock()]
        self.profile[pulsesPerRotation]  = \
            [hc.DEF_PULSES_PER_ROTATION, int, threading.Lock()]
        self.profile[maxRPM]  = \
            [hc.DEF_MAX_RPM, int, threading.Lock()]
        self.profile[minRPM]  = \
            [hc.DEF_MIN_RPM, int, threading.Lock()]
        self.profile[minDC]  = \
            [hc.DEF_MIN_DC, int, threading.Lock()]
        self.profile[maxFanTimeouts] = \
            [hc.DEF_MAX_FAN_TIMEOUTS, int, threading.Lock()]
        self.profile[defaultModuleDimensions] = \
            [hc.DEF_MODULE_DIMENSIONS, tuple, threading.Lock()]
        self.profile[defaultModuleAssignment] = \
            [hc.DEF_MODULE_ASSIGNMENT, str, threading.Lock()]
        self.profile[defaultPinout] = \
            [hc.DEF_PINOUT, str, threading.Lock()]

    # End FCArchiver constructor ===============================================

    def get(self, param): # ====================================================
        # ABOUT: Get the value of the specified parameter, given as a constant
        # as defined in FCArchiver.py.
        # NOTE: Used locks for thread-safety.
        # NOTE: If the requested parameter is not immutable (int, tuple...)
        #    this method will perform and return a deep copy.
        # NOTE: Raises KeyError if the requested parameter does not exist.

        try:
            self.profile[param][LOCK].acquire()
            
            # Check parameter type to choose how to return it:
            if self.profile[param][TYPE] in (int, str, float, tuple):
                # Immutable value, no need for fancy copying
                value = self.profile[param][VALUE]
            
            else:
                # Probably a mutable type, such a list. Return a copy.
                value = copy.deepcopy(self.profile[param][VALUE])

            return value

        finally:
            self.profile[param][LOCK].release()

        # End get ==============================================================

    def set(self, param, value): # =============================================
        # ABOUT: Set the value of the specified parameter, given as a constant
        # as defined in FCArchiver.py.
        # NOTE: Uses locks for thread-safety.
        # NOTE: Raises TypeError if the given value is not of the right type.
        # NOTE: Raises KeyError if the requested parameter does not exist.

        try:
            self.profile[param][LOCK].acquire()

            # Check type:
            if type(value) is not self.profile[param][TYPE]:
                raise TypeError("New value ({}) for requested parameter ({}) \
                must be    of type {}, not {}".\
                format(value, param, self.profile[param][TYPE], type(param)))

            # Assign new value:
            self.profile[param][VALUE] = value

            return

        finally:
            self.profile[param][LOCK].release()

        # End set ==============================================================

    def save(self, name = None): # =============================================
        # ABOUT: Save current profile to a file with the given name. If no
        # name is given, the loaded file will be overwritten. If there is
        # no current profile, a provisional name will be made instead.

        raise IOError("FCArchiver save functionality not yet implemented!")

        # End save =============================================================

    def getProfile(self): # ====================================================
        # Get a copy of the current profile as a dictionary of the form:
        #        ACCODE -> VALUE
        # NOTE: Be advised, this process is bulky and should be used only during
        # initialization

        profile = {}
        for itemKey in self.profile:
            try:
                self.profile[itemKey][LOCK].acquire()
                profile[itemKey] = self.profile[itemKey][VALUE]
            finally:
                self.profile[itemKey][LOCK].release()

        return profile
        
        # End getProfile =======================================================

    # NOTE: How to load files? How to deal with multiple profiles? 
    # L-> IDEA: If there is one profile, load it; if there are no profile or 
    #        more than one, throw an exception during construction and let FCI
    #        handle it by notifying the user, and then calling FCArchiver's
    #        constructor again using a specific argument on __init__() to either
    #        specify the filename (give a list with the original exception) or
    #        that it is okay to start w/ null values.

    # NOTE: Another idea... Use some sort of "getAll" function to procedurally
    #        get all parameters and their values. This way, we can generate
    #        settings" displays easily!


## INDEPENDENT TEST SUITE ######################################################

if __name__ == "__main__":
    print(("#### FCMkII: FCArchiver version \"{}\" test suite started ".\
        format(VERSION)))
    
    print("No singly-testable code here...")

    print("#### FCMkII: FCArchiver test suite terminated")
