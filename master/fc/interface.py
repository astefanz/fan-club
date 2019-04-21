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
import fc.communicator as cm

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
    SYMBOL = "[FE]"

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
        us.PrintServer.__init__(self, pqueue, period)
        self.archive = archive
        self.communicator = communicator
        self.version = self.archive[ac.version]
        self.platform = self.archive[ac.platform]

        self.__buildPipes()
        self.__buildLists()

        # Build backend abstraction:
        def startNetwork():
            communicator.start(archive.profile(), self.feedbackPipeSend,
                self.controlPipeRecv, self.networkPipeSend,
                self.slavesPipeSend, self.messagePipeBackEnd)

        self.network = cm.NetworkAbstraction(communicator,
            self.messagePipeFrontEnd, self.controlPipeSend, startNetwork)

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

    def feedbackClient(self, client):
        """
        Add CLIENT to the list of objects who's feedbackIn method is to be
        called to distribute incoming feedback vectors.
        """
        self.feedbackClients.append(client.feedbackIn)

    def networkClient(self, client):
        """
        Add CLIENT to the list of objects who's networkIn method is to be
        called to distribute incoming network vectors.
        """
        self.networkClients.append(client.networkIn)

    def slavesClient(self, client):
        """
        Add CLIENT to the list of objects who's slavesIn method is to be
        called to distribute incoming slaves vectors.
        """
        self.slavesClients.append(client.slavesIn)

    # FOR INHERITANCE ----------------------------------------------------------
    def _mainloop():
        """
        To be overriden upon inheritance. This method builds the actual
        interface and blocks for the entirety of its existence. When this
        method returns, the interface terminates.
        """
        raise AttributeError("Interface missing _mainloop implementation.")

    def _cycle(self):
        """
        Execute one iteration of the inter-process and print sentinels.

        NOTE: You may want to call this method within a try/catch block to keep
        exceptions from breaking the sentinel loop.
        """
        us.PrintServer._cycle(self)
        if self.feedbackPipeRecv.poll():
            feedback = self.feedbackPipeRecv.recv()
            for client in self.feedbackClients:
                client.feedbackIn(feedback)
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
        self.feedbackPipeRecv, self.feedbackPipeSend = mp.Pipe(False)
        self.controlPipeRecv, self.controlPipeSend = mp.Pipe(False)
        self.networkPipeRecv, self.networkPipeSend = mp.Pipe(False)
        self.slavesPipeRecv, self.slavesPipeSend = mp.Pipe(False)
        self.messagePipeFrontEnd, self.messagePipeBackEnd = mp.Pipe(True)

    def __buildLists(self):
        """
        Create the containers to hold the clients of each inter-process message
        type.
        """
        self.feedbackClients = []
        self.networkClients = []
        self.slavesClients = []
