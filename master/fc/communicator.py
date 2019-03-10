##############################################################################
## Project: Fanclub Mark IV "Master"  ## File: communicator.py                ##
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
 + Fan Club networking back-end.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import fc.utils as us

## CONSTANT DEFINITIONS ########################################################
MP_STOP_TIMEOUT_S = 0.5

# Message codes:
MSG_ADD = 3031
MSG_DISCONNECT = 3032
MSG_REBOOT = 3033
MSG_REMOVE = 3034
MESSAGES = {"Add":MSG_ADD, "Disconnect":MSG_DISCONNECT, "Reboot":MSG_REBOOT,
    "Remove": MSG_REMOVE}

# Target codes:
TGT_ALL = 4041
TGT_SELECTED = 4042
TARGETS = {"All":TGT_ALL, "Selected":TGT_SELECTED}

## CLASS DEFINITION ############################################################
class FCCommunicator(us.PrintClient):
    """
    Handles the "master" side of the fan array control network. In summary, an
    instance of this class outputs arrays indicating the state of the tunnel
    and the network and receives as input arrays representing commands to be
    executed by the tunnel.

    This version receives input and output from a series of multiprocessing
    pipe ends (See Python's multiprocessing) which are passed when the
    communications daemon is started (See start method).
    """
    symbol = "[CM]"

    def __init__(self, pqueue):
        """
        Initialize a new FC Communicator (inactive). PQUEUE is the multiprocess
        Queue to be used for printing.

        NOTE: At most one FCCommunicator instance is meant to exist at a given
        time.
        """
        us.PrintClient.__init__(self, pqueue, self.symbol)
        self.pqueue = pqueue

        self.printw("Initialized FCCommunicator skeleton") # FIXME

    def start(self, profile, matrixPipe, networkPipe, slavePipe, commandPipe,
        timeout = MP_STOP_TIMEOUT_S):
        """
        Start this Communicator (launch the communication daemon). Stops and
        restarts this instance if it is already active.

        Arguments:
        - PROFILE: See FC Archive.
        - PIPES (multiprocessing pipes, or multiprocessing-pipe-like):
            - The MATRIX pipe end will be used bidirectionally: to SEND array
              state vectors and to RECEIVE array input vectors.
            - The NETWORK and SLAVE pipe ends will be used to SEND network and
              slave list state vectors.
            - The COMMAND pipe is a bidirectional pipe used to RECEIVE commands
              (such as a command to launch ethernet flashing) and may be used
              to SEND special messages if necessary, though this functionality
              remains undefined.
        - TIMEOUT: Optional, seconds to wait when stopping the current daemon if
          this method is used while it is already alive.
        """

        if self.active():
            self.stop(timeout)

        self.printw("Started FCCommunicator skeleton") # FIXME


    def stop(self, timeout = MP_STOP_TIMEOUT_S):
        """
        Stop this Communicator (shut down the communication daemon). Does
        nothing if this instance is not active.
        """
        self.printw("Stopped FCCommunicator skeleton") # FIXME
        pass

    def active(self):
        """
        Return whether this instance is running its communications daemon.
        """
        self.printw("Checked activity of FCCommunicator skeleton") # FIXME
        return False
