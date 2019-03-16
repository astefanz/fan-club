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

import fc.utils as us

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

# Supported I-P Comms. Messages:
# Message -------- | Arguments
DEFAULT = 5001  #  | N/A
LOAD = 5002     #  | file to load as str (e.g "prof.fc")
SAVE = 5003     #  | file name as str (e.g "prof.fc")
UPDATE = 5004   #  | dict. to use for update

# PARAMETER NAMES ==============================================================

# TODO: General profile encoding with recursive structure. Include precedence
# and way in which to modify, as well as "range."


# Core -------------------------------------------------------------------------
name = 1
description = 2

# Runtime ----------------------------------------------------------------------
platform = 3
printQueue = 4
version = 5

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
# METADATA:
NAME, PRECEDENCE, TYPE = 0, 1, 2
TYPE_PRIMITIVE, TYPE_LIST, TYPE_SUB, TYPE_MAP = 96000, 96001, 96002, 96003

META = {
    name : ("name", 1, TYPE_PRIMITIVE),
    description : ("description", 1, TYPE_PRIMITIVE),
    platform : ("platform", 2, TYPE_PRIMITIVE),
    version : ("version", 3, TYPE_PRIMITIVE),

    broadcastPort  : ("broadcastPort", 4, TYPE_PRIMITIVE),
    broadcastPeriodMS : ("broadcastPeriodMS", 4, TYPE_PRIMITIVE),
    broadcastPeriodS : ("broadcastPeriodS", 4, TYPE_PRIMITIVE),
    periodMS : ("periodMS", 4, TYPE_PRIMITIVE),
    periodS : ("periodS", 4, TYPE_PRIMITIVE),
    maxLength : ("maxLength", 4, TYPE_PRIMITIVE),
    maxTimeouts : ("maxTimeouts", 4, TYPE_PRIMITIVE),
    mainQueueSize : ("mainQueueSize", 4, TYPE_PRIMITIVE),
    slaveQueueSize : ("slaveQueueSize", 4, TYPE_PRIMITIVE),
    broadcastQueueSize : ("broadcastQueueSize", 4, TYPE_PRIMITIVE),
    listenerQueueSize : ("listenerQueueSize", 4, TYPE_PRIMITIVE),
    misoQueueSize : ("misoQueueSize", 4, TYPE_PRIMITIVE),
    printerQueueSize : ("printerQueueSize", 4, TYPE_PRIMITIVE),
    passcode : ("passcode", 4, TYPE_PRIMITIVE),

    defaultSlave : ("defaultSlave", 5, TYPE_SUB),
    SV_name : ("SV_name", 0, TYPE_PRIMITIVE),
    SV_mac : ("SV_mac", 1, TYPE_PRIMITIVE),
    SV_index : ("SV_index", 2, TYPE_PRIMITIVE),
    SV_fanModel : ("SV_fanModel", 3, TYPE_PRIMITIVE),
    SV_fanMode : ("SV_fanMode", 4, TYPE_PRIMITIVE),
    SV_targetRelation : ("SV_targetRelation", 5, TYPE_PRIMITIVE),
    SV_chaserTolerance : ("SV_chaserTolerance", 6, TYPE_PRIMITIVE),
    SV_fanFrequencyHZ : ("SV_fanFrequencyHZ", 7, TYPE_PRIMITIVE),
    SV_counterCounts : ("SV_counterCounts", 8, TYPE_PRIMITIVE),
    SV_counterTimeoutMS : ("SV_counterTimeoutMS", 9, TYPE_PRIMITIVE),
    SV_pulsesPerRotation : ("SV_pulsesPerRotation", 10, TYPE_PRIMITIVE),
    SV_maxRPMs : ("SV_maxRPMs", 11, TYPE_PRIMITIVE),
    SV_minRPMs : ("SV_minRPMs", 12, TYPE_PRIMITIVE),
    SV_minDCs : ("SV_minDCs", 13, TYPE_PRIMITIVE),
    SV_maxFans : ("SV_maxFans", 14, TYPE_PRIMITIVE),
    SV_pinout : ("SV_pinout", 15, TYPE_PRIMITIVE),

    savedSlaves : ("savedSlaves", 6, TYPE_LIST),

    pinouts : ("pinouts", 7, TYPE_MAP),

    defaultModule : ("defaultModule", 8, TYPE_SUB),

    MD_slaveIndex : ("MD_slaveIndex", 0, TYPE_PRIMITIVE),
    MD_row : ("MD_row", 1, TYPE_PRIMITIVE),
    MD_column : ("MD_column", 2, TYPE_PRIMITIVE),
    MD_rows : ("MD_rows", 3, TYPE_PRIMITIVE),
    MD_columns : ("MD_columns", 4, TYPE_PRIMITIVE),
    MD_fans : ("MD_fans", 5, TYPE_PRIMITIVE),
    MD_fanAssignment : ("MD_fanAssignment", 6, TYPE_PRIMITIVE),

    defaultFanArray : ("defaultFanArray", 9, TYPE_SUB),

    FA_name : ("FA_name", 0, TYPE_PRIMITIVE),
    FA_description : ("FA_description", 1, TYPE_PRIMITIVE),
    FA_rows : ("FA_rows", 2, TYPE_PRIMITIVE),
    FA_columns : ("FA_columns", 3, TYPE_PRIMITIVE),
    FA_layers : ("FA_layers", 4, TYPE_PRIMITIVE),
    FA_modules : ("FA_modules", 5, TYPE_PRIMITIVE),

    fanArrays : ("fanArrays", 10, TYPE_LIST)
}


## MAIN ########################################################################

class FCArchive(us.PrintClient):
    """
    Handles the data that distinguishes FC configurations, such as fan array
    details, network settings and known slaves, as well as its storage and
    retrieval to and from files.
    """

    symbol = "[AC]"
    meta = META

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
                SV_name : "FAWT Module",
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

    def __init__(self, pqueue, ver):
        """
        Create a new FCProfile with no profile. PQUEUE is a Queue object in
        which to place standardized (by fc.utils) console output messages.

        VER is a string representing the current FC version.

        Note that a profile must be loaded (may be the default) before this
        instance is used.
        """
        us.PrintClient.__init__(self, pqueue, self.symbol)
        self.runtime = {platform : us.platform(), version : ver}
        self.P = {}
        self.P.update(self.runtime)
        self.modified = False

    def modified(self):
        """
        Return whether the current profile has been modified without saving.
        """
        return self.modified

    def default(self):
        """
        Load the default profile.
        """
        self.P = cp.deepcopy(FCArchive.DEFAULT)
        self.P.update(self.runtime)
        self.modified = False

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
        try:
            # TODO: Validate?
            # Check if runtime is being modified (should we allow this?)
            # Check if type is valid
            # Check if value is valid
            self.P[attribute] = value
            self.modified = True
        except KeyError as e:
            self.printe("Invalid FC Archive key \"{}\"".format(attribute))

    def load(self, name):
        """
        Load profile data from a file named NAME with extension.

        Any IOError raised will be passed to the caller, in which case the
        current profile won't be changed.
        """
        try:
            old = self.P
            new = pk.load(open(name, 'rb'))
            # TODO: Validate?
            self.P = new
            self.P.update(self.runtime)
            self.modified = False
        except IOError as e:
            self.printx(e, "Could not load profile")
            self.P = old

    def save(self, name):
        """
        Save current profile to file named NAME.
        Note that if a file with this name and extension exists it will be
        overwritten.

        IOErrors will cancel the operation and cause an error message to be
        sent to the print queue.
        """
        try:
            pk.dump(self.profile(), open(name, 'wb'))
            self.modified = False
        except IOError as e:
            self.printx(e, "Could not save profile")

    def update(self, update):
        """
        Update the current profile by replacing matching entries with
        those in UPDATE (expected to be a Python dictionary whose keys are
        all preexisting FCArchive keys whose values are valid).
        """
        for key in update:
            self.set(key, update[key])

    def keys(self):
        """
        Return an iterable containing the keys of the loaded profile.
        """
        return self.P.keys()

    def __getitem__(self, key):
        """
        Fetch a value from the current profile, indexed by KEY. Here KEY must
        be a valid key value defined in fc.archive.
        """
        return self.P[key]
