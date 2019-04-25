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

# NOTE: When importing the CAST wind tunnel, remember the difference by one
# between MkIII module assignments and MkIV module assignments

## GLOBALS #####################################################################
VERSION = "IV-1"
CODE = 1

# Platforms:
UNKNOWN = -1
WINDOWS = 0
MACOS = 1
LINUX = 2

# Fan modes:
SINGLE = -1 # NOTE: mat change to positive values when slave side is updated
DOUBLE = -2
FAN_MODES = (SINGLE, DOUBLE)

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
periodMS = 103
maxLength = 105
maxTimeouts = 106

mainQueueSize = 107
slaveQueueSize= 108
broadcastQueueSize = 109
listenerQueueSize = 110
misoQueueSize = 111
printerQueueSize = 112
passcode = 113

socketLimit = 114

defaultSlave = 1105
savedSlaves = 1106

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
SV_maxRPM = 127
SV_minRPM = 128
SV_minDC = 129
SV_maxFans = 130
SV_pinout = 131
# For each module . . . .
MD_assigned = 300
MD_row = 301
MD_column = 302
MD_rows = 303
MD_columns = 304
MD_mapping = 306
# ........................

pinouts = 132

# Fan array --------------------------------------------------------------------
maxRPM = 200
maxFans = 201
dcDecimals = 202
fanArray = 203

# For each fan array .....
FA_rows = 208
FA_columns = 209
FA_layers = 210

# . . . . . . . . . . . .
# ........................

# VALIDATORS ===================================================================
# ABOUT: Validators are functions that take in the value of some profile
# attribute and return None if the value is valid for such attribute and raise
# a ValueError otherwise.

def make_lambda_validator(l):
    """
    Create a validator that checks whether, for a given value V, l(V) returns
    a True value.
    """
    def validator(value):
        if not l(value):
            raise ValueError("Invalid attribute value ({})".format(value))
    return validator

def make_range_validator(low, high):
    """
    Create a validator that checks whether a given numerical or string value N
    is in the range LOW <= N <= HIGH.

    Notice inclusivity.
    """
    def validator(value):
        if value < low or value > high:
            raise ValueError("Value ({}) is outside the range [{}, {}]".format(
                value, low, high))
    return validator

def make_eq_validator(required):
    """
    Create a validator that checks whether a given numerical or string value N
    is N == REQUIRED.
    """
    def validator(given):
        if given != required:
            raise ValueError("Value ({}) must be ({})".format(given, required))
    return validator

def make_geq_validator(low):
    """
    Create a validator that checks whether a given numerical or string value N
    is N >= LOW.

    Notice inclusivity.
    """
    def validator(value):
        if value < low:
            raise ValueError("Value ({}) is less than minimum ({})".format(
                value, low))
    return validator

def make_gt_validator(low):
    """
    Create a validator that checks whether a given numerical or string value N
    is N > LOW.

    Notice inclusivity.
    """
    def validator(value):
        if value <= low:
            raise ValueError("Value ({}) is not above minimum ({})".format(
                value, low))
    return validator

def make_leq_validator(high):
    """
    Create a validator that checks whether a given numerical or string value N
    is N <= HIGH.

    Notice inclusivity.
    """
    def validator(value):
        if value > high:
            raise ValueError("Value ({}) is larger than maximum ({})".format(
                value, high))
    return validator

def make_in_validator(*values):
    """
    Create a validator that checks whether the given value is one of the given
    VALUES.
    """
    def validator(value):
        if value not in values:
            raise ValueError(
                "Value ({}) is not among valid values. (!= {})".format(value,
                values))
    return validator

def make_neq_validator(*values):
    """
    Create a validator that checks whether the given value is different from all
    the values in VALUES.
    """
    def validator(value):
        if value in values:
            raise ValueError("Value ({}) is not permitted. (!= {})".format(
                value, values))
    return validator

def validate_true(value):
    """
    Validator that checks whether VALUE is a "True" value (i.e nonzero,
    nonempty, etc.)
    """
    if not value:
        raise ValueError("Value ({}) cannot be a null value.".format(value))

def mix(*validators):
    """
    Return a validator function that runs the given value through all
    VALIDATORS, in the order in which they're passed here.
    """
    def validator(value):
        for V in validators:
            V(value)
    return validator

def v_fail_all(value):
    """
    Validator that fails on all values.
    """
    raise ValueError("No values can be assigned to this attribute.")

def make_type_validator(T):
    """
    Validator that checks whether for some value N, type(N) is T
    """
    def validator(value):
        if type(value) is not T:
            raise ValueError(
                "Value ({}) is not of the right type (i.e {})".format(value, T))
    return validator

def make_length_validator(length):
    """
    Return a validator that checks whether the given value has exactly length
    LENGTH.
    """
    def validator(value):
        if len(value) is not length:
            raise ValueError(
                "Value ({}) does not have the required length {}".format(value,
                    length))
    return validator

v_pass_all = lambda v: print("[WARNING] Pass-all validator called on:", v)
v_int = make_type_validator(int)
v_str = make_type_validator(str)
v_port = make_range_validator(1, 65535)
v_nonnegative = make_geq_validator(0)
v_nonnegative_int = mix(v_int, v_nonnegative)
v_nonzero = make_neq_validator(0)
v_positive_int = mix(make_type_validator(int), make_gt_validator(0))
v_normalized = make_range_validator(0.0, 1.0)
v_nonempty = validate_true
v_nonempty_str = mix(make_type_validator(str), v_nonempty)
v_mac = mix(v_str, make_length_validator(17))
v_dutycycle = make_range_validator(0, 100)
v_bool = make_type_validator(bool)
v_negative_one = make_eq_validator(-1)

# METADATA =====================================================================
NAME, PRECEDENCE, TYPE, EDITABLE, VALIDATOR = tuple(range(5))


TYPE_PRIMITIVE, TYPE_LIST, TYPE_SUB, TYPE_MAP = 96000, 96001, 96002, 96003

META = {
    name : (
        "name",
        1,
        TYPE_PRIMITIVE,
        True,
        v_nonempty_str),
    description : (
        "description",
        1,
        TYPE_PRIMITIVE,
        True,
        v_str),
    platform : (
        "platform",
        2,
        TYPE_PRIMITIVE,
        False,
        v_fail_all),
    version : ("version",
		3,
		TYPE_PRIMITIVE,
		False,
		v_fail_all),

    broadcastPort  : ("broadcastPort",
		4,
		TYPE_PRIMITIVE,
		True,
		v_port),
    broadcastPeriodMS : ("broadcastPeriodMS",
		4,
		TYPE_PRIMITIVE,
		True,
        v_positive_int),
    periodMS : ("periodMS",
		4,
		TYPE_PRIMITIVE,
		TYPE_PRIMITIVE,
		True,
        v_positive_int),
    maxLength : ("maxLength",
		4,
		TYPE_PRIMITIVE,
		True,
		v_positive_int),
    maxTimeouts : ("maxTimeouts",
		4,
		TYPE_PRIMITIVE,
		True,
		v_positive_int),
    mainQueueSize : ("mainQueueSize",
		4,
		TYPE_PRIMITIVE,
		True,
		v_positive_int),
    slaveQueueSize : ("slaveQueueSize",
		4,
		TYPE_PRIMITIVE,
		True,
        v_positive_int),
    broadcastQueueSize : ("broadcastQueueSize",
		4,
		TYPE_PRIMITIVE,
		True,
        v_positive_int),
    listenerQueueSize : ("listenerQueueSize",
		4,
		TYPE_PRIMITIVE,
		True,
        v_positive_int),
    misoQueueSize : ("misoQueueSize",
		4,
		TYPE_PRIMITIVE,
		True,
		v_positive_int),
    printerQueueSize : ("printerQueueSize",
		4,
		TYPE_PRIMITIVE,
		True,
        v_positive_int),
    passcode : ("passcode",
		4,
		TYPE_PRIMITIVE,
		True,
		v_nonempty_str),
    socketLimit : ("socketLimit",
		4,
		TYPE_PRIMITIVE,
		True,
        v_positive_int),
    defaultSlave : ("defaultSlave",
		5,
		TYPE_SUB,
		False,
		v_fail_all),
    SV_name : ("SV_name",
		0,
		TYPE_PRIMITIVE,
		True,
		v_str),
    SV_mac : ("SV_mac",
		1,
		TYPE_PRIMITIVE,
		True,
		v_mac),
    SV_index : ("SV_index",
		2,
		TYPE_PRIMITIVE,
		True,
		v_negative_one),
    SV_fanModel : ("SV_fanModel",
		3,
		TYPE_PRIMITIVE,
		True,
		v_str),
    SV_fanMode : ("SV_fanMode",
		4,
		TYPE_PRIMITIVE,
		True,
        make_in_validator(FAN_MODES)),
    SV_targetRelation : ("SV_targetRelation",
		5,
		TYPE_PRIMITIVE,
		True,
        make_lambda_validator(lambda v: len(v) == 2 and \
            type(v[0] in (float,
		int)) and type(v[i] in (float,
		int)))),
    SV_chaserTolerance : ("SV_chaserTolerance",
		6,
		TYPE_PRIMITIVE,
		True,
        v_normalized),
    SV_fanFrequencyHZ : ("SV_fanFrequencyHZ",
		7,
		TYPE_PRIMITIVE,
		True,
        v_positive_int),
    SV_counterCounts : ("SV_counterCounts",
		8,
		TYPE_PRIMITIVE,
		True,
        v_positive_int),
    SV_counterTimeoutMS : ("SV_counterTimeoutMS",
		9,
		TYPE_PRIMITIVE,
		True,
        v_positive_int),
    SV_pulsesPerRotation : ("SV_pulsesPerRotation",
		10,
		TYPE_PRIMITIVE,
		True,
        v_nonnegative),
    SV_maxRPM : ("SV_maxRPM",
		11,
		TYPE_PRIMITIVE,
		True,
		v_positive_int),
    SV_minRPM : ("SV_minRPM",
		12,
		TYPE_PRIMITIVE,
		True,
		v_nonnegative_int),
    SV_minDC : ("SV_minDC",
		13,
		TYPE_PRIMITIVE,
		True,
		v_dutycycle),
    SV_maxFans : ("SV_maxFans",
		14,
		TYPE_PRIMITIVE,
		True,
		v_positive_int),
    SV_pinout : ("SV_pinout",
		15,
		TYPE_PRIMITIVE,
		True,
        make_in_validator(PINOUTS.keys())),
    MD_assigned: ("MD_assigned",
        16,
        TYPE_PRIMITIVE,
        True,
        v_bool),
    MD_row : ("MD_row",
		16,
		TYPE_PRIMITIVE,
		True,
		v_nonnegative_int),
    MD_column : ("MD_column",
		17,
		TYPE_PRIMITIVE,
		True,
		v_nonnegative_int),
    MD_rows : ("MD_rows",
		18,
		TYPE_PRIMITIVE,
		True,
		v_nonnegative_int),
    MD_columns : ("MD_columns",
		19,
		TYPE_PRIMITIVE,
		True,
		v_nonnegative_int),
    MD_mapping : ("MD_mapping",
		20,
		TYPE_PRIMITIVE,
		True,
		v_pass_all),

    savedSlaves : ("savedSlaves",
		6,
		TYPE_LIST,
		False,
		v_fail_all),

    pinouts : ("pinouts",
		7,
		TYPE_MAP,
		False,
		v_pass_all),

    maxRPM : ("maxRPM",
		8,
		TYPE_PRIMITIVE,
		True,
		v_positive_int),

    maxFans : ("maxFans",
		8,
		TYPE_PRIMITIVE,
		True,
		v_positive_int),

    dcDecimals : ("dcDecimals",
		8,
		TYPE_PRIMITIVE,
		True,
		v_nonnegative_int),

    fanArray : ("fanArray",
		9,
		TYPE_SUB,
		False,
		v_fail_all),

    FA_rows : ("FA_rows",
		2,
		TYPE_PRIMITIVE,
		True,
		v_nonnegative_int),
    FA_columns : ("FA_columns",
		3,
		TYPE_PRIMITIVE,
		True,
		v_nonnegative_int),
    FA_layers : ("FA_layers",
		4,
		TYPE_PRIMITIVE,
		True,
		v_nonnegative_int),
}

INVERSE = {value[NAME] : key for key, value in META.items()}

UNIQUES = {SV_index, SV_mac}

# Default values ---------------------------------------------------------------
def unpack_default_slave(slave):
    result = '{\n\\'
    for key, value in slave.items():
        result += "\t {} : {},\n".format(META[key][NAME], value)
    result += '}'
    return result

def index_slave(slave):
    return slave[SV_index]

KEY, UNPACKER, INDEXER = 0, 1, 2
DEFAULTS = {
    savedSlaves : (defaultSlave, unpack_default_slave, index_slave)
}

## MAIN ########################################################################

class FCArchive(us.PrintClient):
    """
    Handles the data that distinguishes FC configurations, such as fan array
    details, network settings and known slaves, as well as its storage and
    retrieval to and from files.
    """

    SYMBOL = "[AC]"
    meta = META
    defaults = DEFAULTS

    """ Default profile. """
    DEFAULT = {
        name : "Unnamed FC Profile",
        description : "",
        platform : UNKNOWN,

        broadcastPort  : 65000,
        broadcastPeriodMS : 1000,
        periodMS : 100,
        maxLength : 512,
        maxTimeouts : 10,

        mainQueueSize : 10,
        slaveQueueSize: 10,
        broadcastQueueSize : 2,
        listenerQueueSize : 3,
        misoQueueSize : 2,
        printerQueueSize : 3,
        passcode : "CT",
        socketLimit : 1024,

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
                SV_maxRPM : 16000,
                SV_minRPM : 1200,
                SV_minDC : 0.5,
                SV_maxFans : 21,
                SV_pinout : "BASE",
                MD_assigned : False,
                MD_row : -1,
                MD_column : -1,
                MD_rows : 0,
                MD_columns : 0,
                MD_mapping : ()
            },
        savedSlaves : (),
        pinouts : PINOUTS.copy(),
        maxRPM : 16000,
        maxFans : 21,
        dcDecimals : 2,
        fanArray : {
            FA_rows : 0,
            FA_columns : 0,
            FA_layers : 0,
        },
    }

    def __init__(self, pqueue, ver):
        """
        Create a new FCProfile with no profile. PQUEUE is a Queue object in
        which to place standardized (by fc.utils) console output messages.

        VER is a string representing the current FC version.

        Note that a profile must be loaded (may be the default) before this
        instance is used.
        """
        us.PrintClient.__init__(self, pqueue)
        self.runtime = {platform : us.platform(), version : ver}
        self.P = {}
        self.P.update(self.runtime)
        self.modified = False

        # TODO: Startup "auto-load" routine
        self.builtin("DEV2") # FIXME temporary
        self.printw("Provisional profile set")

    def modified(self):
        """
        Return whether the current profile has been modified without saving.
        """
        return self.modified

    def default(self):
        """
        Load the default profile.
        """
        return # FIXME (blocking for builtin call)
        self.P = cp.deepcopy(FCArchive.DEFAULT)
        self.P.update(self.runtime)
        self.modified = False

    def builtin(self, name):
        """
        Provisional method to switch to a "built-in" (hardcoded) profile.
        """
        self.P = cp.deepcopy(PROFILES[name])
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

    def add(self, attribute, value):
        """
        Add VALUE to the TYPE_LIST attribute ATTRIBUTE.
        """
        if self.meta[attribute][TYPE] is not TYPE_LIST:
            raise ValueError("Tried to add to non-list attribute {} ".format(
                self.meta[attribute][NAME]))
        try:
            # TODO: Validate?
            # Check if runtime is being modified (should we allow this?)
            # Check if type is valid
            # Check if value is valid
            self.P[attribute] += (value,)
            self.modified = True
        except KeyError as e:
            self.printe("Invalid FC Archive key \"{}\"".format(attribute))

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

""" Provisional, hard-coded profiles. """ # FIXME
DEV1 = {
    name : "Development Profile",
    description : "A provisional profile to be used for development.",
    platform : UNKNOWN,

    broadcastPort  : 65000,
    broadcastPeriodMS : 1000,
    periodMS : 100,
    maxLength : 512,
    maxTimeouts : 10,

    mainQueueSize : 10,
    slaveQueueSize: 10,
    broadcastQueueSize : 2,
    listenerQueueSize : 3,
    misoQueueSize : 2,
    printerQueueSize : 3,
    passcode : "CT",
    socketLimit : 1024,

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
            SV_maxRPM : 16000,
            SV_minRPM : 1200,
            SV_minDC : 0.5,
            SV_maxFans : 21,
            SV_pinout : "BASE",
            MD_assigned : False,
            MD_row : -1,
            MD_column : -1,
            MD_rows : 0,
            MD_columns : 0,
            MD_mapping : ()
        },
    savedSlaves : (
        {
            SV_name : "A1",
            SV_mac : "00:80:e1:38:00:2a",
            SV_index : -1,
            SV_fanModel : "Unknown",
            SV_fanMode : SINGLE,
            SV_targetRelation :(1.0, 0.0),
            SV_chaserTolerance : 0.02,
            SV_fanFrequencyHZ : 25000,
            SV_counterCounts : 2,
            SV_counterTimeoutMS : 30,
            SV_pulsesPerRotation : 2,
            SV_maxRPM : 16000,
            SV_minRPM : 1200,
            SV_minDC : 0.1,
            SV_maxFans : 21,
            SV_pinout : "BASE",
            MD_assigned : True,
            MD_row : 0,
            MD_column : 0,
            MD_rows : 1,
            MD_columns : 21,
            MD_mapping : \
                ("0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20")
        },
        {
            SV_name : "A2",
            SV_mac : "00:80:e1:45:00:46",
            SV_index : -1,
            SV_fanModel : "Unknown",
            SV_fanMode : SINGLE,
            SV_targetRelation :(1.0, 0.0),
            SV_chaserTolerance : 0.02,
            SV_fanFrequencyHZ : 25000,
            SV_counterCounts : 2,
            SV_counterTimeoutMS : 30,
            SV_pulsesPerRotation : 2,
            SV_maxRPM : 16000,
            SV_minRPM : 1200,
            SV_minDC : 0.1,
            SV_maxFans : 21,
            SV_pinout : "BASE",
            MD_assigned : True,
            MD_row : 1,
            MD_column : 0,
            MD_rows : 1,
            MD_columns : 21,
            MD_mapping : \
                ("0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20")
        }),
    pinouts : PINOUTS.copy(),
    maxRPM : 16000,
    maxFans : 21,
    dcDecimals : 2,
    fanArray : {
        FA_rows : 2,
        FA_columns : 21,
        FA_layers : 1,
    },
}

DEV2 = {
    name : "Development Profile 2" ,
    description : "A provisional profile to be used for development. " \
        "Uses double fans.",
    platform : UNKNOWN,

    broadcastPort  : 65000,
    broadcastPeriodMS : 1000,
    periodMS : 100,
    maxLength : 512,
    maxTimeouts : 10,

    mainQueueSize : 10,
    slaveQueueSize: 10,
    broadcastQueueSize : 2,
    listenerQueueSize : 3,
    misoQueueSize : 2,
    printerQueueSize : 3,
    passcode : "CT",
    socketLimit : 1024,

    defaultSlave :
        {
            SV_name : "FAWT Module",
            SV_mac : "None",
            SV_index : -1,
            SV_fanModel : "Unknown",
            SV_fanMode : DOUBLE,
            SV_targetRelation :(1.0, 0.0),
            SV_chaserTolerance : 0.02,
            SV_fanFrequencyHZ : 25000,
            SV_counterCounts : 2,
            SV_counterTimeoutMS : 30,
            SV_pulsesPerRotation : 2,
            SV_maxRPM : 16000,
            SV_minRPM : 1200,
            SV_minDC : 0.5,
            SV_maxFans : 20,
            SV_pinout : "BASE",
            MD_assigned : False,
            MD_row : -1,
            MD_column : -1,
            MD_rows : 0,
            MD_columns : 0,
            MD_mapping : ()
        },
    savedSlaves : (
        {
            SV_name : "A1",
            SV_mac : "00:80:e1:38:00:2a",
            SV_index : -1,
            SV_fanModel : "Unknown",
            SV_fanMode : DOUBLE,
            SV_targetRelation :(1.0, 0.0),
            SV_chaserTolerance : 0.02,
            SV_fanFrequencyHZ : 25000,
            SV_counterCounts : 2,
            SV_counterTimeoutMS : 30,
            SV_pulsesPerRotation : 2,
            SV_maxRPM : 16000,
            SV_minRPM : 1200,
            SV_minDC : 0.1,
            SV_maxFans : 20,
            SV_pinout : "BASE",
            MD_assigned : True,
            MD_row : 0,
            MD_column : 0,
            MD_rows : 1,
            MD_columns : 10,
            MD_mapping : \
                ("0-1,2-3,4-5,6-7,8-9,10-11,12-13,14-15,16-17,18-19")
        },
        {
            SV_name : "A2",
            SV_mac : "00:80:e1:45:00:46",
            SV_index : -1,
            SV_fanModel : "Unknown",
            SV_fanMode : DOUBLE,
            SV_targetRelation :(1.0, 0.0),
            SV_chaserTolerance : 0.02,
            SV_fanFrequencyHZ : 25000,
            SV_counterCounts : 2,
            SV_counterTimeoutMS : 30,
            SV_pulsesPerRotation : 2,
            SV_maxRPM : 16000,
            SV_minRPM : 1200,
            SV_minDC : 0.1,
            SV_maxFans : 20,
            SV_pinout : "BASE",
            MD_assigned : True,
            MD_row : 1,
            MD_column : 0,
            MD_rows : 1,
            MD_columns : 10,
            MD_mapping : \
                ("0-1,2-3,4-5,6-7,8-9,10-11,12-13,14-15,16-17,18-19")
        }),
    pinouts : PINOUTS.copy(),
    maxRPM : 16000,
    maxFans : 20,
    dcDecimals : 2,
    fanArray : {
        FA_rows : 2,
        FA_columns : 10,
        FA_layers : 2,
    },
}

BASE = {
    name : "Prov. Basement Tunnel",
    description : "Not the wind tunnel GALCIT wants, but the one it needs.",
    platform : UNKNOWN,

    broadcastPort  : 65000,
    broadcastPeriodMS : 1000,
    periodMS : 100,
    maxLength : 512,
    maxTimeouts : 10,

    mainQueueSize : 10,
    slaveQueueSize: 10,
    broadcastQueueSize : 2,
    listenerQueueSize : 3,
    misoQueueSize : 2,
    printerQueueSize : 3,
    passcode : "CT",
    socketLimit : 1024,

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
            SV_maxRPM : 16000,
            SV_minRPM : 1200,
            SV_minDC : 0.1,
            SV_maxFans : 21,
            SV_pinout : "BASE",
            MD_assigned : False,
            MD_row : -1,
            MD_column : -1,
            MD_rows : 0,
            MD_columns : 0,
            MD_mapping : ()
        },
    savedSlaves : (
        {
            SV_name : "B1",
            SV_mac : "00:80:e1:4b:00:36",
            SV_index : -1,
            SV_fanModel : "Unknown",
            SV_fanMode : SINGLE,
            SV_targetRelation :(1.0, 0.0),
            SV_chaserTolerance : 0.02,
            SV_fanFrequencyHZ : 25000,
            SV_counterCounts : 2,
            SV_counterTimeoutMS : 30,
            SV_pulsesPerRotation : 2,
            SV_maxRPM : 16000,
            SV_minRPM : 1200,
            SV_minDC : 0.1,
            SV_maxFans : 20,
            SV_pinout : "BASE",
            MD_assigned : True,
            MD_row : 7,
            MD_column : 5,
            MD_rows : 4,
            MD_columns : 6,
            MD_mapping : \
                '19,17,13,9,,,18,16,12,8,5,2,,15,11,7,4,1,,14,10,6,3,0'
        },
        {
            SV_name : "B2",
            SV_mac : "00:80:e1:2f:00:1d",
            SV_index : -1,
            SV_fanModel : "Unknown",
            SV_fanMode : SINGLE,
            SV_targetRelation :(1.0, 0.0),
            SV_chaserTolerance : 0.02,
            SV_fanFrequencyHZ : 25000,
            SV_counterCounts : 2,
            SV_counterTimeoutMS : 30,
            SV_pulsesPerRotation : 2,
            SV_maxRPM : 16000,
            SV_minRPM : 1200,
            SV_minDC : 0.1,
            SV_maxFans : 20,
            SV_pinout : "BASE",
            MD_assigned : True,
            MD_row : 7,
            MD_column : 0,
            MD_rows : 4,
            MD_columns : 6,
            MD_mapping : \
                ',,13,9,5,,19,16,12,8,4,,18,15,11,7,3,1,17,14,10,6,2,0'
        },
        {
            SV_name : "B3",
            SV_mac : "00:80:e1:29:00:2e",
            SV_index : -1,
            SV_fanModel : "Unknown",
            SV_fanMode : SINGLE,
            SV_targetRelation :(1.0, 0.0),
            SV_chaserTolerance : 0.02,
            SV_fanFrequencyHZ : 25000,
            SV_counterCounts : 2,
            SV_counterTimeoutMS : 30,
            SV_pulsesPerRotation : 2,
            SV_maxRPM : 16000,
            SV_minRPM : 1200,
            SV_minDC : 0.1,
            SV_maxFans : 20,
            SV_pinout : "BASE",
            MD_assigned : True,
            MD_row : 3,
            MD_column : 0,
            MD_rows : 5,
            MD_columns : 6,
            MD_mapping : \
                '18,19,,,,,13,14,15,16,17,,7,8,9,10,11,12,2,3,4,5,6,,0,1,,,,'
        },
        {
            SV_name : "B4",
            SV_mac : "00:80:e1:27:00:3e",
            SV_index : -1,
            SV_fanModel : "Unknown",
            SV_fanMode : SINGLE,
            SV_targetRelation :(1.0, 0.0),
            SV_chaserTolerance : 0.02,
            SV_fanFrequencyHZ : 25000,
            SV_counterCounts : 2,
            SV_counterTimeoutMS : 30,
            SV_pulsesPerRotation : 2,
            SV_maxRPM : 16000,
            SV_minRPM : 1200,
            SV_minDC : 0.1,
            SV_maxFans : 20,
            SV_pinout : "BASE",
            MD_assigned : True,
            MD_row : 0,
            MD_column : 0,
            MD_rows : 4,
            MD_columns : 6,
            MD_mapping : \
                '0,1,2,3,4,,5,6,7,8,9,,10,11,12,13,14,15,,,16,17,18,19'
        },
        {
            SV_name : "B5",
            SV_mac : "00:80:e1:4b:00:42",
            SV_index : -1,
            SV_fanModel : "Unknown",
            SV_fanMode : SINGLE,
            SV_targetRelation :(1.0, 0.0),
            SV_chaserTolerance : 0.02,
            SV_fanFrequencyHZ : 25000,
            SV_counterCounts : 2,
            SV_counterTimeoutMS : 30,
            SV_pulsesPerRotation : 2,
            SV_maxRPM : 16000,
            SV_minRPM : 1200,
            SV_minDC : 0.1,
            SV_maxFans : 20,
            SV_pinout : "BASE",
            MD_assigned : True,
            MD_row : 0,
            MD_column : 5,
            MD_rows : 4,
            MD_columns : 6,
            MD_mapping : \
                '19,17,13,9,5,2,18,16,12,8,4,1,,15,11,7,3,0,,14,10,6,,,'
        },
        {
            SV_name : "B6",
            SV_mac : "00:80:e1:47:00:3d",
            SV_index : -1,
            SV_fanModel : "Unknown",
            SV_fanMode : SINGLE,
            SV_targetRelation :(1.0, 0.0),
            SV_chaserTolerance : 0.02,
            SV_fanFrequencyHZ : 25000,
            SV_counterCounts : 2,
            SV_counterTimeoutMS : 30,
            SV_pulsesPerRotation : 2,
            SV_maxRPM : 16000,
            SV_minRPM : 1200,
            SV_minDC : 0.1,
            SV_maxFans : 21,
            SV_pinout : "BASE",
            MD_assigned : True,
            MD_row : 3,
            MD_column : 5,
            MD_rows : 5,
            MD_columns : 6,
            MD_mapping : \
                ',,,,9,4,20,18,15,12,8,3,,17,14,11,7,2,19,16,13,10,6,1,,,,,5,0'

        }
    ),
    pinouts : PINOUTS.copy(),
    maxRPM : 16000,
    maxFans : 21,
    dcDecimals : 2,
    fanArray : {
        FA_rows : 11,
        FA_columns : 11,
        FA_layers : 1,
    },
}


PROFILES = {
    "DEV1" : DEV1,
    "DEV2" : DEV2,
    "BASE": BASE
}
