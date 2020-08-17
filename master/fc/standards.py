################################################################################
## Project: Fanclub Mark IV "Master" base window  ## File: standards.py       ##
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
 + Repository of shared constant values to be used for communication across
 + processes and objects.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

""" INTER PROCESS COMMUNICATIONS STANDARD ++++++++++++++++++++++++++++++++++++++

                 ------ CONTROL PIPE ------------------------
            +----> [control vector (DC assignments) ] ----------->+
            ^    --------------------------------------------     |
            |                                                     |
            |    ------ COMMAND PIPE ------------------------     |
            | +--> [command vector (ADD, REBOOT, FIRMW...)] --->+ |
            ^ ^  --------------------------------------------   V V
        -----------                                         ------------
       |           |                                       |            |
       | FRONT-END |                                       |  BACK-END  |
       |           |                                       |            |
        -----------                                         ------------
         ^ ^ ^ ^                                               V V V V
         | | | |  ---- FEEDBACK PIPE ------------------------  | | | |
         | | | +<- [feedback vector F (DC's and RPM's)] <------+ | | |
         | | |    -------------------------------------------    | | |
         | | |                                                   | | |
         | | |    ---- SLAVE PIPE ---------------------------      | |
         | | +<--- [slave vector S (slave i's, statuses...)] <-----+ |
         | |      -------------------------------------------        |
         | |                                                         |
         | |      ---- NETWORK PIPE -------------------------        |
         | +<----- [network vector N (global IP's and ports)] <------+
         |        -------------------------------------------        |
         |                                                           |
         |        ==== PRINT QUEUE ==========================        |
         +<------- [print messages] <--------------------------------+
                  ===========================================

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

# TODO: Network diagnostics data, such as MISO and MOSI indices and packet
# loss counts, etc.

# TODO: Confirm DC normalization and formats

# TODO: Check performance w/ DC fan selections being Strings
# Timing for multiprocessing back-ends:
MP_STOP_TIMEOUT_S = 0.5

# Number of decimals to have for duty cyle. Indicates by which power of 10 to
# normalize
DC_DECIMALS = 2 # FIXME make this part of the profile
DC_NORMALIZER = 10.0**(DC_DECIMALS + 2) # .... Divide by this to normalize


# Target codes:
TGT_ALL = 4041
TGT_SELECTED = 4042

# NOTE: The purpose of these dictionaries is twofold --first, they allow for
# near constant-time lookup to check whether an integer is a valid code of a
# certain category; second, they allow translation of codes to strings for
# auxiliary printing.
TARGET_CODES = {
    TGT_ALL : "TGT_ALL",
    TGT_SELECTED : "TGR_SELECTED"
}

# Command vectors ##############################################################
# NOTE: Sent through the same channel as control vectors.
# Form:
#
#        D =  [CODE, TARGET_CODE, TARGET_0, TARGET_1,... ]
#              |     |            |---------------------/
#              |     |            |
#              |     |            |
#              |     |            Indices of selected slaves, if applicable
#              |     Whether to apply to all or to a subset of the slaves
#              Command code: ADD, DISCONNECT, REBOOT, etc. (below)
#
#                         either broadcast or targetted "heart beat"
#                         |
#        D =  [CMD_BMODE, BMODE]
#              |          |
#              |          New broadcast mode
#              Set new broadcast mode
#
#        D =  [CMD_FUPDATE_START, TGT_ALL VERSION_NAME, FILE_NAME, SIZE]
#              |                          |             |          |
#              |                          |             |          |
#              |                          |             |          File size (b)
#              |                          |             File name (String)
#              |                          Version name (String)
#              Start firmware update
#
#                       IP address to target
#                       |
#        D =  [CMD_BIP, IP]
#              |
#              |
#              Set new broadcast IP

# Command codes:
CMD_ADD = 3031
CMD_DISCONNECT = 3032
CMD_REBOOT = 3033
CMD_SHUTDOWN = 3035
CMD_FUPDATE_START = 3036 # .............................. Start firmware update
CMD_FUPDATE_STOP = 3037
CMD_STOP = 3038 # ............................................... Stop back-end
CMD_BMODE = 3039  # .............................................. Set broadcast
CMD_BIP = 3040

CMD_N = 3041 # .............................................. Get Network Vector
CMD_S = 3042 # .............................................. Get Slave Vector

# Broadcast modes:
BMODE_BROADCAST = 8391
BMODE_TARGETTED = 8392

# INDICES:
CMD_I_CODE = 0
CMD_I_TGT_CODE = 1
CMD_I_TGT_OFFSET = 2

CMD_I_FU_VERSION = 2
CMD_I_FU_FILENAME = 3
CMD_I_FU_FILESIZE = 4

CMD_I_BM_BMODE = 1

CMD_I_BIP_IP = 1

COMMAND_CODES = {
    CMD_ADD : "CMD_ADD",
    CMD_DISCONNECT : "CMD_DISCONNECT",
    CMD_REBOOT : "CMD_REBOOT",
    CMD_SHUTDOWN : "CMD_SHUTDOWN",
    CMD_FUPDATE_START : "CMD_FUPDATE_START",
    CMD_FUPDATE_STOP : "CMD_FUPDATE_STOP",
    CMD_STOP : "CMD_STOP",
    CMD_BMODE : "CMD_BMODE",
    CMD_BIP : "CMD_BIP",
    CMD_N : "CMD_N",
    CMD_S : "CMD_S"
}

# Control vectors ##############################################################
# NOTE: Sent through the same channel as command vectors
# NOTE: Here each duty cycle is a float between 0.0 and 1.0, inclusive.
# Form:
#                                                           1st fan selected
#                                                           |2nd fan selected
#                                                           ||
#                                       String of the form "01001..."
#                                       |
# [CTL_DC_SINGLE, TGT_SELECTED, DC, TARGET_0, SEL_0, TARGET_1, SEL_1...]
#  |              |             |   |-------------/ |----------------/
#  |              |             |   |               |
#  |              |             |   |               Data for second target...
#  |              |             |   Index of first target slave, then selection
#  |              |             Target duty cycle (int) (must be normalized)
#  |              Apply command to selected Slaves
#  Control code
#                                                  1st fan selected
#                                                  |2nd fan selected
#                                                  ||
#                              String of the form "01001..."
#                              |
# [CTL_DC_SINGLE, TGT_ALL, DC, SELECTION]
#  |              |        |   |
#  |              |        |   Selected fans
#  |              |        Target duty cycle, as integer (must be normalized)
#  |              Apply to all Slaves
#  Control code
#
# [CTL_DC_VECTOR, TGT_SELECTED, DC_0_0, DC_0_1, DC_0_MF,...DC_N-1_0,...DC_N-1_MF]
#  |                 |         |----------------------/ |----------------/
#  |                 |         |                        |
#  |                 |         |                        DC's for last slave
#  |                 |         Fans of slave 0
#  |                 Whether to apply to all or to a subset of the slaves
#  Control code
#  NOTE: TGT_SELECTED is ignored, as CTL_DC_VECTOR is meant to only use this
#  NOTE: Here all slaves are assumed to have maxFans fans. Inactive fans are
#  expected to be padded with zeros.

# Control codes:
CTL_DC_SINGLE = 5051
CTL_DC_VECTOR = 5052

# Control indices:
CTL_I_CODE = 0
CTL_I_TGT_CODE = 1

CTL_I_SINGLE_DC = 2
CTL_I_SINGLE_ALL_SELECTION = 3

CTL_I_SINGLE_TGT_OFFSET = 3
CTL_I_VECTOR_TGT_OFFSET = 1
CTL_I_VECTOR_DC_OFFSET = 2

CONTROL_CODES = {
    CTL_DC_SINGLE : "CTL_DC_SINGLE",
    CTL_DC_VECTOR : "CTL_DC_VECTOR"
}


# Aggregates:
MESSAGES = {"Add":CMD_ADD, "Disconnect":CMD_DISCONNECT, "Reboot":CMD_REBOOT,
    "Shutdown":CMD_SHUTDOWN}
TARGETS = {"All":TGT_ALL, "Selected":TGT_SELECTED}

CONTROLS = {"Ohno" : 1}#{"DC":CTL_DC}

# Network status vectors #######################################################
# Form:
#      N =    [CONN, IP, BIP, BPORT, LPORT]
#              |     |   |    |       |
#              |     |   |    |       Listener port (int)
#              |     |   |    Broadcast port (int)
#              |     |   Broadcast IP (String)
#              |     Communications IP (String)
#              Connection status (Bool -- connected or not)

# Indices:
NS_LEN = 5
NS_I_CONN, NS_I_IP, NS_I_BIP, NS_I_BPORT, NS_I_LPORT = range(NS_LEN)

# Network Status codes:
NS_CONNECTED = 20001
NS_CONNECTING = 20002
NS_DISCONNECTED = 20003
NS_DISCONNECTING = 20004

NETWORK_STATUSES = {
    NS_CONNECTED : "Connected",
    NS_CONNECTING : "Connecting",
    NS_DISCONNECTED : "Disconnected",
    NS_DISCONNECTING : "Disconnecting",
}

# Slave status codes:
SS_CONNECTED = 30001
SS_KNOWN = 30002
SS_DISCONNECTED = 30003
SS_AVAILABLE = 30004
SS_UPDATING = 30005

SLAVE_STATUSES = {
    SS_CONNECTED : 'Connected',
    SS_KNOWN : 'Known',
    SS_DISCONNECTED : 'Disconnected',
    SS_AVAILABLE : 'Available',
    SS_UPDATING : 'Bootloader'
}

SLAVE_STATUSES_SHORT = {
    SS_CONNECTED : 'CONND',
    SS_KNOWN : 'KNOWN',
    SS_DISCONNECTED : 'DISCN',
    SS_AVAILABLE : 'AVAIL',
    SS_UPDATING : 'BOOTN'
}


# Status foreground colors:
FOREGROUNDS = {
    SS_CONNECTED : '#0e4707',
    SS_KNOWN : '#44370b',
    SS_DISCONNECTED : '#560e0e',
    SS_AVAILABLE : '#666666',
    SS_UPDATING : '#192560'
}
FOREGROUNDS.update({
    NS_CONNECTED : FOREGROUNDS[SS_CONNECTED],
    NS_CONNECTING : FOREGROUNDS[SS_DISCONNECTED],
    NS_DISCONNECTED : FOREGROUNDS[SS_DISCONNECTED],
    NS_DISCONNECTING : FOREGROUNDS[SS_CONNECTED],
})

# Status background colors:
BACKGROUNDS = {
    SS_CONNECTED : '#d1ffcc',
    SS_KNOWN : '#fffaba',
    SS_DISCONNECTED : '#ffd3d3',
    SS_AVAILABLE : '#ededed',
    SS_UPDATING : '#a6c1fc'
}
BACKGROUNDS.update({
    NS_CONNECTED : BACKGROUNDS[SS_CONNECTED],
    NS_CONNECTING : BACKGROUNDS[SS_DISCONNECTED],
    NS_DISCONNECTED : BACKGROUNDS[SS_DISCONNECTED],
    NS_DISCONNECTING : BACKGROUNDS[SS_CONNECTED],
})

# Slave data vectors ###########################################################
# Form:
#
#            S = [INDEX_0, NAME_0, MAC_0, STATUS_0, FANS_0, VERSION_0...]
#                 |        |       |      |         |       |
#                 |        |       |      |         |       Slave 0's version
#                 |        |       |      |         Slave 0's active fans
#                 |        |       |      Slave 0's status
#                 |        |       Slave 0's MAC
#                 |        Slave 0's name
#                 Slave 0's index (should be 0)

# Slave data:
SD_LEN = 6

# Offsets of data per slave in the slave data vector:
SD_INDEX, SD_NAME, SD_MAC, SD_STATUS, SD_FANS, SD_VERSION = range(SD_LEN)

# Feedback vectors #############################################################
# Form:
#
#     F = [RPM_0_1, RPM_0_1, RPM_0_F0, RPM_1_1,... RPM_N-1_FN-1,  DC_0_1,...]
#          |-------------------------/ |------..   |              |-----...
#          |                           |           |     Same pattern, for DC's
#          |                           |           /
#          |                           |   RPM of fan FN-1 of slave N-1
#          |                           RPM's of slave 1
#          RPM's of slave 0
#
# NOTE: Controllers with mappings (i.e grid) need not care about new slaves, for
# they are always unmapped. To get the DC offset they need only get half of the
# feedback vector, and mapped (i.e saved) slaves are guaranteed to be the first
# by the communicator's index assignment.
# Controllers who need to always show all Slaves (i.e live table) may track the
# size of the feedback vector, the default slave values (applied to new slaves),
# and the slave vectors.
# NOTE: Values corresponding to non-connected slaves will be set to a negative
# code.
#
# TODO: Need means by which to handle disconnected slaves and diff. fan sizes
RIP = -666
PAD = -69
END = -354

# EXTERNAL CONTROL #############################################################
EX_BROADCAST, EX_LISTENER = 40001, 40002
EX_KEYS = (EX_BROADCAST, EX_LISTENER)
EX_ACTIVE, EX_INACTIVE = True, False
EX_NAME_BROADCAST, EX_NAME_LISTENER = "State Broadcast", "Command Listener"
EX_NAMES = {EX_BROADCAST: EX_NAME_BROADCAST, EX_LISTENER: EX_NAME_LISTENER}

EX_I_IN, EX_I_OUT = 40010, 40011
EX_INDICES = (EX_I_IN, EX_I_OUT)
EX_RIP = "[RIP]"

EX_CMD_SPLITTER = '|'
EX_LIST_SPLITTER = ','
EX_CMD_I_INDEX, EX_CMD_I_CODE = 0, 1
EX_CMD_F, EX_CMD_N, EX_CMD_S = 'F', 'N', 'S' # Get state vectors
EX_CMD_DC_VECTOR = 'D' # Process DC matrix
EX_CMD_UNIFORM = 'U' # Apply DC to al
EX_CMD_PROFILE = 'P' # Profile attribute
EX_CMD_EVALUATE = 'V' # Evaluate Python expression and get result
EX_CMD_RESET = 'R' # Reset input index

EX_CMD_CODES = (EX_CMD_F, EX_CMD_N, EX_CMD_S, EX_CMD_DC_VECTOR, EX_CMD_UNIFORM,
    EX_CMD_PROFILE, EX_CMD_EVALUATE)

EX_REP_ERROR = 'E'

