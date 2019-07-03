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
 + Interface between the FCMkIV front and back ends.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import multiprocessing as mp
import threading as mt

from fc import standards as s, printer as pt
from fc.backend.mkiii import FCCommunicator as fcc

## HELPER CLASSES ##############################################################
class FCCommunicator(pt.PrintClient):
    """
    Abstractions to be used by the FC front-end to interface with the
    communications back-end.
    """
    SYMBOL = "[NW]"

    def __init__(self, feedbackPipeSend, slavePipeSend, networkPipeSend,
        archive, pqueue):
        """
        """
        pt.PrintClient.__init__(self, pqueue)

        self.feedbackPipeSend = feedbackPipeSend
        self.slavePipeSend = slavePipeSend
        self.networkPipeSend = networkPipeSend
        self.archive = archive
        self.process = None
        self.watchdog = None

        self.commandPipeRecv, self.commandPipeSend = mp.Pipe(False)
        self.controlPipeRecv, self.controlPipeSend = mp.Pipe(False)

    # API ......................................................................
    def start(self):
        """
        Start the communications back-end process. Does nothing if it already
        active.

        PROFILE := Currently loaded profile. See FCArchive.
        """
        try:
            if not self.active():
                self.printr("Starting CM back-end")
                self.process = mp.Process(
                    name = "FC_Comms_Backend",
                    target = self._b_routine,
                    args = (self.archive.profile(),
                            self.commandPipeRecv,
                            self.controlPipeRecv,
                            self.feedbackPipeSend,
                            self.slavePipeSend,
                            self.networkPipeSend,
                            self.pqueue),
                    daemon = True)
                self.process.start()

                self.watchdog = mt.Thread(
                    name = "FC BE Watchdog",
                    target = self._w_routine,
                    daemon = True)
                self.watchdog.start()
            else:
                self.printw("Tried to start already active back-end")
        except Exception as e:
            self.printx(e, "Exception when starting back-end")

    def stop(self, timeout = s.MP_STOP_TIMEOUT_S):
        """
        Stop this Communicator (shut down the communication daemon). Does
        nothing if this instance is not active.
        """
        try:
            if self.active():
                self.printw("Stopping communications back-end...")
                self.commandIn(s.CMD_STOP)
                self.process.join(timeout)
                if self.process.is_alive():
                    self.process.terminate()
                self.process = None
            else:
                self.printw("Tried to stop already inactive back-end")
        except Exception as e:
            self.printx(e, "Exception when stopping back-end")

    def active(self):
        """
        Return whether this instance is running its communications daemon.
        """
        return self.process is not None and self.process.is_alive()

    def commandIn(self, command, target = s.TGT_ALL, rest = ()):
        """
        Send a general command with command code COMMAND with target code
        TARGET, followed by the values in VALUES (required only
        when applicable; its particular value depends on the command). In
        general. this method should be superseded by the specific send methods.
        """
        # FIXME: performance
        if self.active():
            self.commandPipeSend.send((command, target) + rest)


    def controlIn(self, C):
        """
        Process the control vector C.
        """
        # FIXME: performance
        if self.active():
            self.controlPipeSend.send((s.CTL_DC_VECTOR, s.TGT_ALL) + tuple(C))

    def connect(self):
        """
        Send a message to activate the Communicator backend.
        """
        self.start()

    def disconnect(self):
        """
        Send a message to stop the Communicator backend.
        """
        self.stop()

    def shutdown(self):
        """
        Send a shutdown message to the Communicator backend.
        """
        self.commandIn(s.CMD_SHUTDOWN, s.TGT_ALL)

    def startBootloader(self, filename, version, size):
        """
        Send a command to start the bootloader using the binary file at
        FILENAME with version code VERSION and byte size SIZE.
        """
        self.commandIn(s.CMD_FUPDATE_START, s.TGT_ALL,
            (version, filename, size))

    def stopBootloader(self):
        """
        Send a command to stop the flashing process.
        """
        self.commandIn(s.CMD_FUPDATE_STOP)

    def broadcastIP(self, ip):
        """
        Set the broadcast IP.
        - ip := String, new IP address to use, either a valid IPv4 or the String
            "<broadcast>"
        """
        self.commandIn(s.CMD_BIP, ip)

    # Internal methods .........................................................
    @staticmethod
    def _b_routine(profile, commandPipeRecv, controlPipeRecv, feedbackPipeSend,
        slavePipeSend, networkPipeSend, pqueue):
        """
        Back-end routine. To be executed by the B.E. process.
        """
        P = pt.printers(pqueue, "[CR]")
        P[pt.R]("Comms. backend process started")
        try:
            comms = fcc.FCCommunicator(profile, commandPipeRecv,
                controlPipeRecv, feedbackPipeSend, slavePipeSend,
                networkPipeSend, pqueue)
            comms.join()
        except Exception as e:
            P[pt.X](e, "Fatal error in comms. backend process")
        P[pt.W]("Comms. backend process terminated")

    def _w_routine(self):
        """
        Watchdog routine. Tracks whether the back-end process is active.
        """
        self.printd("Back-end watchdog routine started")
        self.process.join()
        self._stopped()
        self.printd("Back-end watchdog routine ended")

    def _stopped(self):
        """
        To be executed when the network switches to disconnected.
        """
        # Send disconnected status vector
        self.networkPipeSend.send((False, None, None, None, None))


