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
import pickle as pk
import copy as cp
    # For deep copies. See:
    # https://stackoverflow.com/questions/3975376/\
    #   understanding-dict-copy-shallow-or-deep/3975388

import fc.process as pr

## GLOBALS #####################################################################
VERSION = "IV-1"
CODE = 1

# Platforms:
UNKNOWN = -1
WINDOWS = 0
MACOS = 1
LINUX = 2

# Fan modes:
SINGLE = 1
DOUBLE = 2

# Built-in pinouts:
PINOUTS = {
    "BASE" : "FGHMALXWKJUVNISOBQTDC qsrnabdtfhvuepckmljoi",
    "CAST" : "ETRGMLWXPQJKUVBADC edcb_^ng`w\\]porqfs",
    "JPL"  : "FGCDABNOLMHITUQSJK efcdabnolmhirspqjk"
}

# Parameter categories:
UNCLASSIFIED = 0
ARRAY = 1
NETWORK = 2

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
defaultFanArray = 201

fanArrays = 204

# For each fan array .....
FA_name = 205
FA_description = 206
FA_rows = 208
FA_columns = 209
FA_layers = 210
FA_modules = 211

# For each module . . . .
MD_slaveIndex = 300
MD_row = 301
MD_column = 302
MD_rows = 303
MD_columns = 304
MD_fans = 305
MD_fanAssignment = 306
# . . . . . . . . . . . .
# ........................

## MAIN ########################################################################

class FCArchive(pr.FCProcess):
    """
    Handles the data that distinguishes FC configurations, such as fan array
    details, network settings and known slaves, as well as its storage and
    retrieval to and from files.
    """

    """ Default profile. """
    DEFAULT = {
        name : "Unnamed FC Profile",
        description : "",
        platform : UNKNOWN,

        broadcastPort  : 65000,
        broadcastPeriodMS : 1000,
        broadcastPeriodS : 1,
        periodMS : 100,
        periodS : 0.1,
        maxLength : 512,
        maxTimeouts : 10,

        mainQueueSize : 10,
        slaveQueueSize: 10,
        broadcastQueueSize : 2,
        listenerQueueSize : 3,
        misoQueueSize : 2,
        printerQueueSize : 3,
        passcode : "CT",

        defaultSlave :
            {
                SV_name : "Module",
                SV_mac : "None",
                SV_index : -1,
                SV_fanModel : "Unknown",
                SV_fanMode : SINGLE,
                SV_targetRelation :(1.0, 0.0),
                SV_chaserTolerance : 0.02,
                SV_fanFrequencyHZ : 25000,
                SV_counterCounts : 2,
                SV_counterTimeoutMS : 30,
                SV_pulsesPerRotation : 2,
                SV_maxRPMs : 16000,
                SV_minRPMs : 1200,
                SV_minDCs : 0.5,
                SV_maxFans : 21,
                SV_pinout : "BASE"
            },
        savedSlaves : (),
        pinouts : PINOUTS.copy(),

        defaultModule : {
            MD_slaveIndex : -1,
            MD_row : -1,
            MD_column : -1,
            MD_rows : 0,
            MD_columns : 0,
            MD_fans : 0,
            MD_fanAssignment : ()
        },
        defaultFanArray : {
            FA_name : "Fan Array",
            FA_description : "",
            FA_rows : 0,
            FA_columns : 0,
            FA_layers : 0,
            FA_modules : ()
        },
        fanArrays : ()
    }

    """ Profile attributes that support the FCArchive add method. """
    ADDABLE = {savedSlaves, fanArrays}

    """ Profile attributes categories. """
    CATEGORIES = {
        ARRAY : {defaultModule, defaultFanArray, fanArrays},
        NETWORK : {broadcastPort, broadcastPeriodMS, broadcastPeriodS,
            periodMS, periodS, maxLength, maxTimeouts, mainQueueSize,
            slaveQueueSize, broadcastQueueSize, listenerQueueSize,
            misoQueueSize, printerQueueSize, passcode, defaultSlave, pinouts
        }
    }

    def __init__(self, currentPlatform):
        """
        Create a new FCProfile with no profile.
        CURRENTPLATFORM must be one of the constants defined in this module
        that represents a supported platform --WINDOWS, MACOS, LINUX or UNKNOWN.

        Note that a profile must be loaded (may be the default) before this
        instance is used.
        """
        pr.FCProcess.__init__(self, name = "FC Archive")

        self.currentPlatform = currentPlatform
        self.P = None

    def default(self):
        """
        Load the default profile.
        """
        self.P = cp.deepcopy(FCArchive.DEFAULT)
        self.P[platform] = self.currentPlatform

    def profile(self):
        """
        Return a copy of the current profile, represented as a dictionary who's
        keys are constants defined in this module.

        Raises an AttributeError if this instance has no profile loaded.
        """
        if self.P is not None:
            return cp.deepcopy(self.P)
        else:
            raise AttributeError("No profile loaded")

    def set(self, attribute, value):
        """
        Replace the current value of ATTRIBUTE (an attribute constant defined in
        this module) in the current profile for the given VALUE, which must be
        valid and of the correct type. Returns the category that was modified.

        Note that nothing is saved to persistent storage unless the save method
        is called.
        """
        # TODO: Validate?
        self.P[attribute] = value
        for category in FCArchive.CATEGORIES:
            if attribute in FCArchive.CATEGORIES[category]:
                return category
        return UNCLASSIFIED

    def add(self, attribute, value):
        """
        Append the value VALUE to ATTRIBUTE (same as in the set method) in the
        current profile.

        Raises a ValueError if the given ATTRIBUTE does not support adding
        (such as periodMS or passcode; attributes like savedSlaves do support
        appending).
        """
        if attribute in FCArchive.ADDABLE:
            # TODO: Validate? (Or validate just at set?)
            self.set(attribute, self.P[attribute] + (value,))
        else:
            raise ValueError(
                "Can't add to non-addable attribute ({})".format(attribute))

    def load(self, name):
        """
        Load profile data from a file named NAME with extension.

        Any IOError raised will be passed to the caller, in which case the
        current profile won't be changed.
        """
        new = pk.load(open(name, 'rb'))
        # TODO: Validate?
        self.P = new
        self.P[platform] = self.currentPlatform

    def save(self, name):
        """
        Save current profile to file named NAME.
        Note that if a file with this name and extension exists it will be
        overwritten.

        Any IOError raised will be passed to the caller.
        """
        pk.dump(self.profile(), open(name, 'wb'))

    def messageIn(self, message):
        """
        Process inter-process message MESSAGE.
        """
        # FIXME

        # TODO:
        # - load
        # - default
        # - save
        # - update
        # - add
        # ~ query
        # ~ validate

        pass
