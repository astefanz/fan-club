################################################################################
## Project: Fanclub Mark IV "Master"  ## File: process.py                     ##
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
 + Common functionality for inter-process communication.
 +
 + INTER-PROCESS COMMUNICATION STANDARD ----------------------------------------
 +
 + GENERAL MESSAGES ............................................................
 + FCProcesses may share "messages" created by fc.process.message and indexable
 + as follows (given a message M):
 +
 + M[fc.process.SENDER] := integer that identifies the sender
 + M[fc.process.TARGET] := integer that identifies the receiver
 + M[fc.process.SUBJECT] := object that identifies the message (usually int)
 + M[fc.process.ARGUMENTS] := tuple containing extra data, may be empty
 +
 + Centralized distribution of these messages is expected to be done by
 + fc.core.FCCore and requires that each FCProcess have an unique SENDER ID.
 +
 + STREAMLINED MESSAGES ........................................................
 + Fan array state matrices, network states, fan array commands, and slave list
 + state updates all have their sender and receiver defined by convention, as
 + well as their own dedicated 'channels' (pipes and methods). As such, there is
 + no need to specify descriptive fields like with general messages.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import multiprocessing as mp
import threading as mt

## CONSTANTS ###################################################################
# Pipe dictionary constants:
MESSAGE = 0
MATRIX = 1
NETWORK = 2
SLAVES = 3
COMMAND = 4

PARENT = 0
CHILD = 1

# Inter-process communication --------------------------------------------------
def message(sender, target, subject, arguments = ()):
    """
    Generate an inter-process message with SENDER, TARGET, SUBJECT and
    ARGUMENTS, where ARGUMENTS may be omitted depending on the message.
    """
    return (sender, target, subject, arguments)

# Significant indices:
SENDER = 0
TARGET = 1
SUBJECT = 2
ARGUMENTS = 3

# Basic messages:
STOP = 0

# Sender ID that represents the lack of a sender ID:
SYMBOL = 0

## MAIN ########################################################################
class FCProcess:
    """
    Base class for an FC master-side object that forms part of the process
    network (centralized around the FCCore). Note that a class may be an
    FCProcess without actually running an independent python process, as is the
    case with FCArchive version IV-1.
    """

    """ To be placed at the SENDER position in inter-process messages. """
    symbol = SYMBOL

    def __init__(self, routine = None, args = {}, name = "FC process"):
        """
        Initialize an FCProcess whose process executes ROUTINE, which may be
        omitted and defaults to None if this FCProcess is not runnable. (If it
        is, ommiting ROUTINE will case a multiprocessing.ProcessError to be
        raised.)

        ARGS is a dictionary containing serializable (pickleable) data that
        should be forwarded to the process. Though not necessary, it is by
        convention expected to use str keys --keys 'profile', 'pipes', and
        'symbol' are reserved.
        NAME is an optional string to represent this process.
        """

        self.routine = routine
        self.name = name
        self.process = None
        self.pipes = None
        self.data = args
        self.stopper = None

        if self.isRunnable() and self.routine is None:
            raise mp.ProcessError(
                "Tried to initialize runnable FCProcess without routine")

    def usesMatrix(self):
        """
        Return whether this process expects to receive fan array state matrices.
        """
        return False

    def usesNetwork(self):
        """
        Return whether this process expects to receive network state updates.
        """
        return False

    def usesSlaveList(self):
        """
        Return whether this process expects to receive slave list updates.
        """
        return False

    def isRunnable(self):
        """
        Return whether this FCProcess is actually capable of spawning an
        independent Python process.
        """
        return False

    def isActive(self):
        """
        Return whether the independent Python process spawned by this FCProcess
        is active.
        """
        return self.isRunnable() and self.stopper is None \
            and self.process is not None and self.process.is_alive()

    def matrixIn(self, matrix):
        """
        Receive and process a fan array state matrix (MATRIX).
        """
        if self.usesMatrix() and self.isActive():
            self.pipes[PARENT][MATRIX].send(matrix)

    def networkIn(self, update):
        """
        Receive and process a network state update (UPDATE).
        """
        if self.usesNetwork() and self.isActive():
            self.pipes[PARENT][NETWORK].send(update)

    def slaveListIn(self, update):
        """
        Receive and process a slave list update (UPDATE).
        """
        if self.usesSlaveList() and self.isActive():
            self.pipes[PARENT][SLAVES].send(update)

    def start(self, profile, args = {}):
        """
        Start this instance's independent process, which inherits PROFILE, an
        updated copy of the loaded FC profile, assuming this FCProcess is
        currently inactive. ARGS is used as optional means by which to update
        the arguments passed to this instance's constructor.

        Raises a multiprocessing.ProcessError if this instance is already
        active or is not runnable.
        """
        if self.isRunnable() and not self.isActive():
            if self.stopper is not None and self.stopper.is_alive():
                raise RuntimeError(
                    "Stopper thread active when starting process '{}'".\
                        format(self.name))
            self.stopper = None
            self.pipes = self._pipes()
            self.data.update({'profile':self.profile, 'pipes':self.pipes,
                'symbol':self.symbol})
            self.data.update(args)
            self.process = mp.Process(
                target = self.routine,
                name = self.name,
                args = (self.data,),
                daemon = True
            )
            self.process.start()

        elif not self.isRunnable():
            raise mp.ProcessError("Tried to start non-runnable FCProcess")
        else:
            raise mp.ProcessError("Tried to start already active FCProcess")

    def stop(self, timeout = 2, callback = lambda s: None):
        """
        Stop this instance's active process, assuming there is one.
        TIMEOUT is the number of seconds to wait for the process to end on its
        own (before killing it) and CALLBACK is a function to call
        when the stop operation is complete, to which True or False is passed
        depending on whether the call to join() was successful (True) or
        timed out (False) --the default callback does nothing on either case.

        Raises a multiprocessing.ProcessError if this instance is not active or
        is not runnable.
        """
        if self.isActive():
            self.stopper = mt.Thread(target = self._stopper,
                args = (timeout, callback), daemon = True)
            self.stopper.start()

        if not self.isRunnable():
            raise mp.ProcessError("Tried to stop non-runnable FCProcess")
        elif not self.isActive():
            raise mp.ProcessError("Tried to stop already inactive FCProcess")

    def hasMessage(self):
        """
        Return whether this instance's running process, if any, has a message
        to send to another FCProcess.
        """
        return self.isActive() and self.pipes[PARENT][MESSAGE].poll()

    def getMessage(self):
        """
        Return the buffered message to be sent to another FCProcess, assuming
        there is one. Otherwise, an exception (such as EOFError or
        AttributeError) is raised.
        """
        return self.pipes[PARENT][MESSAGE].recv()

    def messageIn(self, message):
        """
        Give MESSAGE to this FCProcess, forwarding it to the running process
        if appropriate.
        """
        if self.isActive():
            if message[SUBJECT] == STOP:
                self.stop()
            else:
                self.pipes[PARENT][MESSAGE].send(message)

    def hasCommand(self):
        """
        Return whether this FCProcess has a fan array command buffered for
        sending.
        """
        return self.isActive() and self.pipes[PARENT][COMMAND].poll()

    def getCommand(self):
        """
        Return the buffered fan array command, assuming there is one.

        Use hasCommand to check. (An exception such as EOFError or
        AttributeError will be raised if this operation is impossible.)
        """
        return self.pipes[PARENT][COMMAND].recv()

    def _pipes(self):
        """
        For internal use only. Returns a tuple with two dictionaries of
        newly instantiated Pipes, in accordance with the inter-process
        data expected by this instance (matrices, network state...).

        The tuple's process.CHILD dictionary is for the child process; while
        process.PARENT is for the parent-side.
        """
        pipes = ({}, {})

        pipes[PARENT][MESSAGE], pipes[CHILD][MESSAGE] = mp.Pipe(True)
        pipes[PARENT][COMMAND], pipes[CHILD][COMMAND] = mp.Pipe(False)

        if self.usesMatrix():
            pipes[CHILD][MATRIX], pipes[PARENT][MATRIX] = mp.Pipe(False)
        if self.usesNetwork():
            pipes[CHILD][NETWORK], pipes[PARENT][NETWORK] = mp.Pipe(False)
        if self.usesSlaveList():
            pipes[CHILD][SLAVES], pipes[PARENT][SLAVES] = mp.Pipe(False)

    def _stopper(self, timeout, callback):
        """
        For internal use only. To be executed by an auxiliary thread dedicated
        to stopping the running process. Calls CALLBACK(True) upon successful
        completion and CALLBACK(False) otherwise (if join times out after
        TIMEOUT seconds).
        """
        try:
            self.pipes[PARENT][MESSAGE].send(
                message(self.symbol, self.symbol, STOP))
            self.process.join(timeout)

            self.process = None
            for pipe in self.pipes[PARENT].values():
                pipe.close()
            self.pipes = None

            if self.process.exitcode is None:
                print("Process '{}' timed out after {} seconds (terminating)",
                    self.name, timeout)
                while self.process.exitcode is None or self.process.is_alive():
                    self.process.terminate()
                print("Process '{}' terminated",
                    self.name, timeout)
                callback(False)
            else:
                print("Process '{}' stopped successfully", self.name)
                callback(True)
