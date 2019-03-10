################################################################################
## Project: Fanclub Mark IV "Master"  ## File: interface.py                   ##
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
 + Base class for any Fan Club front end (i.e user interface).
 +
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import multiprocessing as mp
import threading as mt
import time as tm

import fc.archive as ac
import fc.utils as us

## GLOBALS #####################################################################

################################################################################
class FCInterface(us.PrintServer):
    """
    This class abstracts the common behavior of any Fan Club user interface. In
    particular, it handles the general API and the inter-process communication
    facilities: any Fan Club front-end holds a "sentinel thread" that
    listens for data sent by either the interface-specific objects or the
    back-end communications process and distributes it to the corresponding
    "client" processes. See "inheritance notes" below.

    Note that, by the current implementation, an FCInterface instance is meant
    to be "run" (read: used) once.

    -- ON PERFORMANCE AND INHERITANCE ------------------------------------------
    By inheriting from fc.utils.PrintServer, this class has a similar behavior:
    a sentinel thread runs in the background and checks for messages between
    processes to forward (as well as messages to display, by PrintServer).

    This behavior has been encapsulated within the same methods and attributes
    as PrintServer --that is, they now refer to both inter-process
    communications and terminal output. See fc.utils.PrintServer.
    """
    symbol = "[FE]"

    def __init__(self, pqueue, archive, communicator,
        period = us.PrintServer.default_period):
        """
        Initialize a new FC interface. PQUEUE is a Queue
        instance to be used for printing, ARCHIVE is an FCArchive instance and
        COMMUNICATOR is an inactive FCCommunicator instance. PERIOD optionally
        specifies the time between sentinel cycles, in seconds, and defaults to
        PrintServer.default_period.

        Note that an FCInstance instance is meant to be used once per execution.
        Calling run twice will result in a RuntimeError.
        """
        us.PrintServer.__init__(self, pqueue, self.symbol, period)
        self.archive = archive
        self.communicator = communicator
        self.version = self.archive[ac.version]
        self.platform = self.archive[ac.platform]

        self.__buildPipes()
        self.__buildLists()

    # "PUBLIC" INTERFACE -------------------------------------------------------
    def run(self):
        """
        Run the main loop of the interface. Expected to block during the entire
        execution of the interface. (Returning means the interface has been
        closed.)
        """
        # Check for redundant usage:
        self._checkStarted()

        # Start sentinels:
        self.start()

        # Run interface:
        self._mainloop()

        # Clean up:
        self.stop()

    # FOR INHERITANCE ----------------------------------------------------------
    def _mainloop():
        """
        To be overriden upon inheritance. This method builds the actual
        interface and blocks for the entirety of its existence. When this
        method returns, the interface terminates.
        """
        raise AttributeError("Interface missing _mainloop implementation.")

    def _addClient(self, client):
        """
        To be passed to any 'widgets' in order to
        streamline the addition of widgets to the lists of "clients" of the
        Communicator's data. For an use-case, see the FCWidget class defition.
        """
        if client.usesMatrix():
            self.matrixClients.append(client.matrixIn)
        if client.usesNetwork():
            self.networkClients.append(client.networkIn)
        if client.usesSlaves():
            self.slavesClients.append(client.slavesIn)

    def _sendCommand(self, command, value = None):
        """
        Sends command with code COMMAND (as defined in FCCommunicator's file)
        with value VALUE when appropriate. Does nothing if the Communicator is
        not active
        """
        if self.communicator.active():
            self.commandPipeFrontEnd.send((command, value))
        else:
            self.printw("Tried to send command offline ({})".format(command))

    def _cycle(self):
        """
        Execute one iteration of the inter-process and print sentinels.

        NOTE: You may want to call this method within a try/catch block to keep
        exceptions from breaking the sentinel loop.
        """
        us.PrintServer._cycle(self)
        if self.matrixPipeRecv.poll():
            matrix = self.matrixPipeRecv.recv()
            for client in self.matrixClients:
                client.matrixIn(matrix)
        if self.networkPipeRecv.poll():
            network = self.networkPipeRecv.recv()
            for client in self.networkClients:
                client.networkIn(network)
        if self.slavesPipeRecv.poll():
            slaves = self.slavesPipeRecv.recv()
            for client in self.slavesClients:
                client.slavesIn(slaves)

    # "PRIVATE" AUXILIARY METHODS ----------------------------------------------
    def __buildPipes(self):
        """
        Create the multiprocessing Pipe instances used by this FCInterface and
        assign them to the corresponding member attributes.
        """
        self.matrixPipeRecv, self.matrixPipeSend = mp.Pipe(False)
        self.networkPipeRecv, self.networkPipeSend = mp.Pipe(False)
        self.slavesPipeRecv, self.slavesPipeSend = mp.Pipe(False)
        self.commandPipeFrontEnd, self.commandPipeBackEnd = mp.Pipe(True)

    def __buildLists(self):
        """
        Create the containers to hold the clients of each inter-process message
        type.
        """
        self.matrixClients = []
        self.networkClients = []
        self.slavesClients = []
