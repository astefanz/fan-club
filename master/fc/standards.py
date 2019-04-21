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

## COMMUNICATIONS ##############################################################

# Communicator commands --------------------------------------------------------
# Message codes:
MSG_ADD = 3031
MSG_DISCONNECT = 3032
MSG_REBOOT = 3033
MSG_REMOVE = 3034
MSG_SHUTDOWN = 3035

# Target codes:
TGT_ALL = 4041
TGT_SELECTED = 4042

MESSAGE_CODES = (
    MSG_ADD,
    MSG_DISCONNECT,
    MSG_REBOOT,
    MSG_REMOVE,
    MSG_SHUTDOWN
)

# Control codes:
CTL_DC = 5051
# NOTE: From the old communicator, commands have been simplified by using only
# "SET_DC_MULTI" Also, SET_RPM has been omitted until feedback control is to be
# implemented.
CONTROL_CODES = (
    CTL_DC
)

# Bootloader codes:
BTL_START = 6061
BTL_STOP = 6062

BOOTLOADER_CODES = (
    BTL_START,
    BTL_STOP
)

# Aggregates:

MESSAGES = {"Add":MSG_ADD, "Disconnect":MSG_DISCONNECT, "Reboot":MSG_REBOOT,
    "Remove": MSG_REMOVE, "Shutdown":MSG_SHUTDOWN}
TARGETS = {"All":TGT_ALL, "Selected":TGT_SELECTED}

CONTROLS = {"DC":CTL_DC}

# Network status vectors -------------------------------------------------------
# Form:
#        Process a new network state vector N of the following form:
#            [ CONN, IP, BIP, BPORT, LPORT ]
#              |     |   |    |       |
#              |     |   |    |       Listener port (int)
#              |     |   |    Broadcast port (int)
#              |     |   Broadcast IP (String)
#              |     Communications IP (String)
#              Connection status (Bool -- connected or not)

# Status codes:
CONNECTED = 0
KNOWN = 1
DISCONNECTED = 2
AVAILABLE = 3
UPDATING = 4
TAGS = (CONNECTED, KNOWN, DISCONNECTED, AVAILABLE, UPDATING)

# Status 'long' names:
STATUSES = {
    CONNECTED : 'Connected',
    KNOWN : 'Known',
    DISCONNECTED : 'Disconnected',
    AVAILABLE : 'Available',
    UPDATING : 'Updating'
}

# Status foreground colors:
FOREGROUNDS = {
    CONNECTED : '#0e4707',
    KNOWN : '#44370b',
    DISCONNECTED : '#560e0e',
    AVAILABLE : '#666666',
    UPDATING : '#192560'
}

# Status background colors:
BACKGROUNDS = {
    CONNECTED : '#d1ffcc',
    KNOWN : '#fffaba',
    DISCONNECTED : '#ffd3d3',
    AVAILABLE : '#ededed',
    UPDATING : '#a6c1fc'
}

# Slave data vectors -----------------------------------------------------------
# Form:
#        Process new slave vector S of the following form:
#
#            S = [INDEX_0, NAME_0, MAC_0, STATUS_0, FANS_0, VERSION_0...]
#            |    |        |       |      |         |       |
#            |    |        |       |      |         |       Slave 0's version
#            |    |        |       |      |         Slave 0's active fans
#            |    |        |       |      Slave 0's status
#            |    |        |       Slave 0's MAC
#            |    |        Slave 0's name
#            |    Slave 0's index (should be 0)
#            This slave vector

# Slave data:
SD_SIZE = 6

# Offsets of data per slave in the slave data vector:
SD_INDEX, SD_NAME, SD_MAC, SD_STATUS, SD_FANS, SD_VERSION = range(SD_SIZE)

