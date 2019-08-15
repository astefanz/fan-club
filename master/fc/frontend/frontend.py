################################################################################
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
 + Base class for the FC Frontend. Handles inter-process communication.
 +
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import multiprocessing as mp
import threading as mt
import time as tm

import fc.archive as ac
import fc.utils as us
import fc.printer as pt
import fc.backend.communicator as cm
import fc.backend.external as ex
import fc.backend.mapper as mr
import fc.standards as std

################################################################################
class FCFrontend(pt.PrintServer):
    """
    This class abstracts the common behavior of any Fan Club user interface. In
    particular, it handles the general API and the inter-process communication
    facilities: any Fan Club front-end holds a "sentinel thread" that
    listens for data sent by either the interface-specific objects or the
    back-end communications process and distributes it to the corresponding
    "client" processes. See "inheritance notes" below.

    Note that, by the current implementation, an FCCore instance is meant
    to be "run" (read: used) once.

    -- ON PERFORMANCE AND INHERITANCE ------------------------------------------
    By inheriting from fc.utils.PrintServer, this class has a similar behavior:
    a sentinel thread runs in the background and checks for messages between
    processes to forward (as well as messages to display as a PrintServer).

    This behavior has been encapsulated within the same methods and attributes
    as PrintServer --that is, they now refer to both inter-process
    communications and terminal output. See fc.utils.PrintServer.
    """
    SYMBOL = "[FE]"

    def __init__(self, archive, pqueue):
        """
        Initialize a new FC interface. PQUEUE is a Queue
        instance to be used for printing, ARCHIVE is an FCArchive instance.

        Note that an instance is meant to be used once per execution.
        Calling run twice will result in a RuntimeError.
        """
        pt.PrintServer.__init__(self, pqueue)
        self.archive = archive
        self.live = True
        self.version = self.archive[ac.version]
        self.platform = self.archive[ac.platform]
        self.__buildLists()
        self.__buildPipes()
        self.__buildLocks()
        self.__buildThreads()
        self.__flushAltBuffers()

        # TODO backend abstraction
        self.mapper = mr.Mapper(self.archive)

        self.network = cm.FCCommunicator(self.feedback_send, self.slave_send,
            self.network_send, archive, pqueue)
        self.external = ex.ExternalControl(self.mapper, archive, pqueue)
        self.addFeedbackClient(self.external)
        self.addNetworkClient(self.external)
        self.addSlaveClient(self.external)
        self.archiveClient(self.mapper)
        self.archiveClient(self.external)


    # "PUBLIC" INTERFACE -------------------------------------------------------
    def run(self):
        """
        Run the main loop of the program. Expected to block during execution
        Returning means the program has been closed.
        """
        # Start sentinels:
        pt.PrintServer.start(self)
        self._startThreads()

        # Execute front end:
        self._mainloop()

        # Clean up:
        self._stopThreads()
        pt.PrintServer.stop(self)

    def addFeedbackClient(self, client):
        """
        Add CLIENT to the list of objects who's feedbackIn method is to be
        called to distribute incoming feedback vectors.
        """
        self.feedback_clients.append(client.feedbackIn)

    def addNetworkClient(self, client):
        """
        Add CLIENT to the list of objects who's networkIn method is to be
        called to distribute incoming network vectors.
        """
        self.network_clients.append(client.networkIn)

    def addSlaveClient(self, client):
        """
        Add CLIENT to the list of objects who's slavesIn method is to be
        called to distribute incoming slaves vectors.
        """
        self.slave_clients.append(client.slavesIn)

    def archiveClient(self, client):
        """
        Add CLIENT to the list of objects to be notified when the loaded
        profile is modified by calling their profileChange method.
        """
        self.archive_clients.append(client)

    # FOR INHERITANCE ----------------------------------------------------------
    def _mainloop():
        """
        To be overriden upon inheritance. This method builds the actual
        interface and blocks for the entirety of its existence. When this
        method returns, the interface terminates.
        """
        raise AttributeError("Interface missing _mainloop implementation.")

    def setLive(self, live):
        """
        Set whether feedback, network and slave vectors should be fetched from
        the network backend (live == True) or from the alternate buffers
        (live == False)
        """
        self.live = live
        self.__flushAltBuffers()

    def altFeedbackIn(self, F):
        """
        Set the alternative feedback vector F. Ignored if "live."
        """
        if not self.live:
            self.F_alt = F

    def altNetworkIn(self, N):
        """
        Set the alternative network vector N. Ignored if "live."
        """
        if not self.live:
            self.N_alt = N

    def altSlaveIn(self, S):
        """
        Set the alternative slave status vector S. Ignored if "live."
        """
        if not self.live:
            self.S_alt = S

    # "PRIVATE" AUXILIARY METHODS ----------------------------------------------
    def _onProfileChange(self):
        """
        Handle a change in the loaded FC Profile.
        """
        self.network.stop()
        self._pauseThreads()
        self.__flushPipes()
        self._resumeThreads()

        for client in self.archive_clients:
            client.profileChange()

    def _pauseThreads(self):
        """
        Freeze the sentinel threads. Acquires each thread's corresponding lock.
        NOTE: Stop the network backend before using.
        """
        while not self.feedback_lock.acquire(False):
            self.feedback_send.send(std.PAD)
        while not self.network_lock.acquire(False):
            self.network_send.send(std.PAD)
        while not self.slave_lock.acquire(False):
            self.slave_send.send(std.PAD)

    def _resumeThreads(self):
        """
        Unfreeze the sentinel threads. Releases their corresponding locks.
        NOTE: _pauseThreads should have been called.
        """
        self.feedback_lock.release()
        self.network_lock.release()
        self.slave_lock.release()

    def _getAltF(self):
        temp = self.F_alt
        self.F_alt = None
        return temp

    def _getAltN(self):
        temp = self.N_alt
        self.N_alt = None
        return temp

    def _getAltS(self):
        temp = self.S_alt
        self.S_alt = None
        return temp

    def __flushAltBuffers(self):
        self.F_alt, self.N_alt, self.S_alt = None, None, None

    def __flushPipes(self):
        for pipe in self.recv_pipes:
            while pipe.poll():
                _ = pipe.recv()

    def __buildPipes(self):
        """
        Create the multiprocessing Pipe instances used by this FCCore and
        assign them to the corresponding member attributes.
        """
        self.feedback_recv, self.feedback_send = mp.Pipe(False)
        self.network_recv, self.network_send = mp.Pipe(False)
        self.slave_recv, self.slave_send = mp.Pipe(False)
        self.send_pipes = (
            self.feedback_send, self.network_send, self.slave_send)
        self.recv_pipes = (
            self.feedback_recv, self.network_recv, self.slave_recv)

    def __buildLocks(self):
        """
        Create the sentinel synchronization locks within construction.
        """
        self.feedback_lock = mt.Lock()
        self.network_lock = mt.Lock()
        self.slave_lock = mt.Lock()

    def __buildLists(self):
        """
        Create the containers to hold the clients of each inter-process message
        type.
        """
        self.feedback_clients = []
        self.network_clients = []
        self.slave_clients = []
        self.archive_clients = []

    def __buildThreads(self):
        """
        Build the I.P. watchdogs that listen for communicator messages.
        Meant to be called only during construction.
        """
        self.threads = (
            mt.Thread(target = self._feedbackRoutine, daemon = True),
            mt.Thread(target = self._slaveRoutine, daemon = True),
            mt.Thread(target = self._networkRoutine, daemon = True))

    def _startThreads(self):
        """
        Start I.P. watchdogs. Meant to be called only once.
        """
        for thread in self.threads:
            thread.start()

    def _stopThreads(self):
        """
        Stop I.P. watchdogs. Meant to be called only once. Stops the watchdogs
        by closing their multiprocessing pipes to generate an IO exception.
        """
        for pipe in self.send_pipes:
            pipe.close()

    def _feedbackRoutine(self):
        """
        Watchdog for I.P. feedback vectors.
        """
        self.printr("Feedback watchdog started.")
        F = None
        while True:
            try:
                self.feedback_lock.acquire()
                self.feedback_lock.release()
                F = self.feedback_recv.recv()
                if F == std.END:
                    break
                if not self.live:
                    F = self._getAltF()
                if F != None and F != std.PAD:
                    for client_method in self.feedback_clients:
                        client_method(F)
            except Exception as e:
                self.printx(e, "Exception in FE feedback routine")
        self.printr("Feedback watchdog terminated.")
        print("Feedback watchdog terminated.")

    def _slaveRoutine(self):
        self.printr("Slave state watchdog started.")
        S = None
        while True:
            try:
                self.slave_lock.acquire()
                self.slave_lock.release()
                S = self.slave_recv.recv()
                if S == std.END:
                    break
                if S != None and S != std.PAD:
                    for client_method in self.slave_clients:
                        client_method(S)
            except Exception as e:
                self.printx(e, "Exception in FE slave routine")
        self.printr("Slave state watchdog terminated.")
        print("Slave state watchdog terminated.")

    def _networkRoutine(self):
        self.printr("Network state watchdog started.")
        while True:
            try:
                self.network_lock.acquire()
                self.network_lock.release()
                N = self.network_recv.recv()
                if N == std.END:
                    break
                if N != None and N != std.PAD:
                    for client_method in self.network_clients:
                        client_method(N)
            except Exception as e:
                self.printx(e, "Exception in FE network routine")
        self.printr("Network state watchdog terminated.")
        print("Network state watchdog terminated.")

