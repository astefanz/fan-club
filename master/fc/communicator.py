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
MSG_SHUTDOWN = 3035

# Target codes:
TGT_ALL = 4041
TGT_SELECTED = 4042

# Control codes:
CTL_DC = 5051
# NOTE: From the old communicator, commands have been simplified by using only
# "SET_DC_MULTI" Also, SET_RPM has been omitted until feedback control is to be
# implemented.

# Bootloader codes:
BTL_START = 6061
BTL_STOP = 6062

## HELPER CLASSES ##############################################################
class NetworkAbstraction(us.PrintClient):
    """
    Abstractions to be used by the FC front-end to interface with
    communications.
    """

    MESSAGES = {"Add":MSG_ADD, "Disconnect":MSG_DISCONNECT, "Reboot":MSG_REBOOT,
        "Remove": MSG_REMOVE, "Shutdown":MSG_SHUTDOWN}
    TARGETS = {"All":TGT_ALL, "Selected":TGT_SELECTED}

    CONTROLS = {"DC":CTL_DC}

    def __init__(self, communicator, messagePipe, inputPipe, startMethod):
        """
        Create a new NetworkAbstraction that sends messages to the given
        Communicator instance (COMMUNICATOR) through MESSAGE_PIPE and input
        vectors through INPUT_PIPE (both send-enabled Connection instances
        returned by multiprocessing.Pipe).

        STARTMETHOD is a method (with no arguments) to be called when the
        Communicator is to be started.
        """
        self.communicator = communicator
        self.messagePipe = messagePipe
        self.inputPipe = inputPipe
        self.startMethod = startMethod

    def send(self, command, value = ()):
        """
        Send a general command with command code COMMAND and value tuple VALUE
        (when applicable, its particular value depends on the command). In
        general. this method should be superseded by the specific send methods.

        Raises a RuntimeError if this method is called while the Communicator
        is inactive.
        """
        if self.communicator.active():
            self.messagePipe.send((command) + value)
        else:
            raise RuntimeError("Tried to send command offline ({})".format(
                command))

    def connect(self):
        """
        Send a message to activate the Communicator backend.
        """
        self.startMethod()

    def disconnect(self):
        """
        Send a message to stop the Communicator backend.
        """
        self.communicator.stop()

    def shutdown(self):
        """
        Send a shutdown message to the Communicator backend.
        """
        self.send(MSG_SHUTDOWN, TGT_ALL)

    def sendMessage(self, message, target, selection = ()):
        """
        Send a message with message code MESSAGE, target code TARGET and, if
        applicable, SELECTION (may be omitted otherwise).
        """
        self.send(message, (target, selection))

    def sendMatrix(self, matrix):
        """
        Send the control matrix MATRIX.

        For performance, this method does not check if the communicator is
        inactive.
        """
        # FIXME implement matrix behavior
        raise RuntimeError("Control matrix behavior not yet implemented")

    def startBootloader(self, filename, version, size):
        """
        Send a command to start the bootloader using the binary file at
        FILENAME with version code VERSION and byte size SIZE.
        """
        self.send(BTL_START, (filename, version, size))

    def stopBootloader(self):
        """
        Send a command to stop the flashing process.
        """
        seld.send(BTL_STOP)

    def messages(self):
        """
        Return an iterable of (NAME, CODE) pairs representing the messages that
        can be sent to the Communicator backend.
        """
        return self.MESSAGES.items()

    def targets(self):
        """
        Return an iterable of (NAME, CODE) pairs representing the target options
        that can be sent to the Communicator backend (in reference to messages).
        """
        return self.TARGETS.items()

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

    def start(self, profile, feedbackPipe, inputPipe, networkPipe, slavesPipe,
        messagePipe, timeout = MP_STOP_TIMEOUT_S):
        """
        Start this Communicator (launch the communication daemon). Stops and
        restarts this instance if it is already active.

        Arguments:
        - PROFILE: See FC Archive.
        - PIPES (multiprocessing Pipe Connections):
            - FEEDBACK will be use to send array state vectors to
              the front end.
            - INPUT pipe will be used to receive input vectors from the front
              end.
            - NETWORK and SLAVES will be used to send network and slave list
              state vectors.
            - MESSAGE is a bidirectional pipe used to RECEIVE commands
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
