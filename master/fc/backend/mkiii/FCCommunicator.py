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
 + Fan Club networking back-end -- provisional version adapted from MkIII.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## DEPENDENCIES ################################################################

# Network:
import socket       # Networking
import http.server  # For bootloader
import socketserver # For bootloader

# System:
import sys          # Exception handling
import traceback    # More exception handling
import threading as mt  # Multitasking
import _thread      # thread.error
import multiprocessing as mp # The big guns

import platform # Check OS and Python version

# Data:
import time         # Timing
import queue
import numpy as np  # Fast arrays and matrices
import random as rd # For random names

# FCMkIII:
import fc.backend.mkiii.FCSlave as sv
import fc.backend.mkiii.hardcoded as hc
import fc.backend.mkiii.names as nm

# FCMkIV:
import fc.archive as ac
import fc.standards as s
import fc.printer as pt

## CONSTANT DEFINITIONS ########################################################

# TODO: Erase all these obsolete codes
""" OBSOLETE XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# Communicator status codes:
CONNECTED = 31
CONNECTING = 32
DISCONNECTED = 33
DISCONNECTING = 34


# Slave data tuple indices:
# Expected form: (INDEX, MAC, STATUS, FANS, VERSION) + IID
#                   0       1   2       3       4       5
INDEX = 0
MAC = 1
STATUS = 2
FANS = 3
VERSION = 4
IID = 5

# Commands: ------------------------------------

ADD = 51
DISCONNECT = 52
REBOOT = 53

# NOTE: Array command e.g.:
#       (COMMUNICATOR, SET_DC, DC, FANS, ALL)
#       (COMMUNICATOR, SET_DC, DC, FANS, 1,2,3,4)
#       (COMMUNICATOR, SET_DC_MANY, DC, SELECTIONS)
#                           |
#                   (INDEX, FANS)

SET_DC = 54
SET_DC_GROUP = 55
SET_DC_MULTI = 56
SET_RPM = 57

# Bootloader commands:

BOOTLOADER_START = 66
BOOTLOADER_STOP = 67

# End commands -----------------------------------

# Special values:
NONE = -1
ALL = -2

FCPRCONSTS = (ADD, DISCONNECT, REBOOT)

# Outputs:
NEW = 11
UPDATE = 12


# Change codes:
NO_CHANGE = 0
CHANGE = 1

# MISO Matrix special columns:
# FIXME: function undocumented; need to define new MISO standard
MISO_COLUMN_STATUS = 0
MISO_COLUMN_TYPE = 1
MISO_SPECIALCOLUMNS = 2

XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX """

# MOSI commands:
# TODO: Replace these
MOSI_NO_COMMAND = 20
MOSI_DC = 21
MOSI_DC_ALL = 22
MOSI_RPM = 23
MOSI_RPM_ALL = 24
MOSI_DISCONNECT = 25
MOSI_REBOOT = 26
MOSI_DC_MULTI = 27

## CLASS DEFINITION ############################################################

# DONE:
# - change profile usage (DONE)

# TODO:
# - change FCSlave constants for s.standards constants
# - change command queue for pipe
# - change pipes
# - change output formatting
# - change input parsing
# - change printing
# - broadcast modes (both here and in interface)
# - stopped behavior

class FCCommunicator(pt.PrintClient):
    VERSION = "Adapted 1"
    SYMBOL = "[CM]"
    SYMBOL_IR = "[IR]"

    # TODO: parameterize these
    DEFAULT_IP_ADDRESS = "0.0.0.0"
        #"0.0.0.0"
    DEFAULT_BROADCAST_IP = "<broadcast>"

    def __init__(self,
            profile,
            commandPipeRecv,
            controlPipeRecv,
            feedbackPipeSend,
            slavePipeSend,
            networkPipeSend,
            pqueue
        ): # ===================================================================
        """
        Constructor for FCCommunicator. This class encompasses the back-end
        network handling and number-crunching half of the software. It is
        expected to be executed in an independent process. (See Python's
        multiprocessing module.)

            profile := profile as loaded from FCArchive
            commandPipeRecv := receive command vectors from FE (mp Pipe())
            controlPipeRecv := receive control vectors from FE (mp Pipe())
            feedbackPipeSend := send feedback vectors to FE (mp Pipe())
            slavePipeSend := send slave vectors to FE (mp Pipe())
            networkPipeSend := send network vectors to FE (mp Pipe())
            pqueue := mp Queue() instance for I-P printing  (see fc.utils)

        """
        pt.PrintClient.__init__(self, pqueue)
        try:
            # INITIALIZE DATA MEMBERS ==========================================

            # Store parameters -------------------------------------------------
            self.profile = profile

            # Network:
            self.broadcastPeriodS = profile[ac.broadcastPeriodMS]/1000
            self.periodMS = profile[ac.periodMS]
            self.periodS = self.periodMS/1000
            self.broadcastPort = profile[ac.broadcastPort]
            self.passcode = profile[ac.passcode]
            self.misoQueueSize = profile[ac.misoQueueSize]
            self.maxTimeouts = profile[ac.maxTimeouts]
            self.maxLength = profile[ac.maxLength]
            self.flashFlag = False
            self.targetVersion = None
            self.flashMessage = None
            self.broadcastMode = s.BMODE_BROADCAST

            # Fan array:
            # FIXME usage of default slave data is a provisional choice
            self.defaultSlave = profile[ac.defaultSlave]

            self.maxFans = profile[ac.maxFans]
            self.fanRange = range(self.maxFans)
            self.dcTemplate = "{},"*self.maxFans
            self.fanMode = profile[ac.defaultSlave][ac.SV_fanMode]
            self.targetRelation = self.defaultSlave[ac.SV_targetRelation]
            self.fanFrequencyHZ = self.defaultSlave[ac.SV_fanFrequencyHZ]
            self.counterCounts = self.defaultSlave[ac.SV_counterCounts]
            self.pulsesPerRotation = self.defaultSlave[ac.SV_pulsesPerRotation]
            self.maxRPM = self.defaultSlave[ac.SV_maxRPM]
            self.minRPM = self.defaultSlave[ac.SV_minRPM]
            self.minDC = self.defaultSlave[ac.SV_minDC]
            self.chaserTolerance = self.defaultSlave[ac.SV_chaserTolerance]
            self.maxFanTimeouts = hc.DEF_MAX_FAN_TIMEOUTS
            self.pinout = profile[ac.pinouts][self.defaultSlave[ac.SV_pinout]]
            self.decimals = profile[ac.dcDecimals]

            self.fullSelection = ''
            for fan in range(self.maxFans):
                self.fullSelection += '1'

            # Multiprocessing and printing:
            self.commandPipeRecv = commandPipeRecv
            self.controlPipeRecv = controlPipeRecv
            self.feedbackPipeSend = feedbackPipeSend
            self.slavePipeSend = slavePipeSend
            self.networkPipeSend = networkPipeSend
            self.stopped = mt.Event()

            # Output queues:
            self.newSlaveQueue = queue.Queue()
            self.slaveUpdateQueue = queue.Queue()

            # Initialize Slave-list-related data:
            self.slavesLock = mt.Lock()

            # Command handling:
            self.commandHandlers = {
                s.CMD_ADD : self.__handle_input_CMD_ADD,
                s.CMD_DISCONNECT : self.__handle_input_CMD_DISCONNECT,
                s.CMD_REBOOT : self.__handle_input_CMD_REBOOT,
                s.CMD_SHUTDOWN : self.__handle_input_CMD_SHUTDOWN,
                s.CMD_FUPDATE_START : self.__handle_input_CMD_FUPDATE_START,
                s.CMD_FUPDATE_STOP : self.__handle_input_CMD_FUPDATE_STOP,
                s.CMD_STOP : self.__handle_input_CMD_STOP,
                s.CMD_BMODE : self.__handle_input_CMD_BMODE,
                s.CMD_BIP : self.__handle_input_CMD_BIP,
                s.CMD_N : self.__handle_input_CMD_N,
                s.CMD_S : self.__handle_input_CMD_S,
            }

            self.controlHandlers = {
                s.CTL_DC_SINGLE : self.__handle_input_CTL_DC_SINGLE,
                s.CTL_DC_VECTOR : self.__handle_input_CTL_DC_VECTOR,
            }

            if self.profile[ac.platform] != ac.WINDOWS:
                self.printd("\tNOTE: Increasing socket limit w/ \"resource\"")
                # Use resource library to get OS to give extra sockets:
                import resource
                resource.setrlimit(resource.RLIMIT_NOFILE,
                    (1024, resource.getrlimit(resource.RLIMIT_NOFILE)[1]))

            # INITIALIZE MASTER SOCKETS ========================================

            # INITIALIZE LISTENER SOCKET ---------------------------------------

            # Create listener socket:
            self.listenerSocket = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM)


            # Configure socket as "reusable" (in case of improper closure):
            self.listenerSocket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind socket to "nothing" (Broadcast on all interfaces and let OS
            # assign port number):
            self.listenerSocket.bind(("", 0))

            self.printr("\tlistenerSocket initialized on " + \
                str(self.listenerSocket.getsockname()))

            self.listenerPort = self.listenerSocket.getsockname()[1]

            # INITIALIZE BROADCAST SOCKET --------------------------------------

            # Create broadcast socket:
            self.broadcastSocket = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM)

            # Configure socket as "reusable" (in case of improper closure):
            self.broadcastSocket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Configure socket for broadcasting:
            self.broadcastSocket.setsockopt(
                socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            # Bind socket to "nothing" (Broadcast on all interfaces and let OS
            # assign port number):
            self.broadcastSocket.bind((self.DEFAULT_IP_ADDRESS, 0))
            self.broadcastIP = self.profile[ac.broadcastIP]

            self.broadcastSocketPort = self.broadcastSocket.getsockname()[1]

            self.broadcastLock = mt.Lock()

            self.printr("\tbroadcastSocket initialized on " + \
                str(self.broadcastSocket.getsockname()))

            # Create reboot socket:
            self.rebootSocket = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM)

            # Configure socket as "reusable" (in case of improper closure):
            self.rebootSocket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Configure socket for rebooting:
            self.rebootSocket.setsockopt(
                socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            # Bind socket to "nothing" (Broadcast on all interfaces and let OS
            # assign port number):
            self.rebootSocket.bind((self.DEFAULT_IP_ADDRESS, 0))

            self.rebootSocketPort = self.rebootSocket.getsockname()[1]

            self.rebootLock = mt.Lock()

            self.printr("\trebootSocket initialized on " + \
                str(self.rebootSocket.getsockname()))

            # Create disconnect socket:
            self.disconnectSocket = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM)

            # Configure socket as "reusable" (in case of improper closure):
            self.disconnectSocket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Configure socket for disconnecting:
            self.disconnectSocket.setsockopt(
                socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            # Bind socket to "nothing" (Broadcast on all interfaces and let OS
            # assign port number):
            self.disconnectSocket.bind((self.DEFAULT_IP_ADDRESS, 0))

            self.disconnectSocketPort = self.disconnectSocket.getsockname()[1]

            self.disconnectLock = mt.Lock()

            self.printr("\tdisconnectSocket initialized on " + \
                str(self.disconnectSocket.getsockname()))

            # Reset any lingering connections:
            self.sendDisconnect()

            # SET UP FLASHING HTTP SERVER --------------------------------------
            self.flashHTTPHandler = http.server.SimpleHTTPRequestHandler
            if self.profile[ac.platform] != ac.WINDOWS:
                TCPServerType = socketserver.ForkingTCPServer
            else:
                TCPServerType = socketserver.ThreadingTCPServer
            self.httpd = TCPServerType(
                ("", 0),
                self.flashHTTPHandler
            )

            self.httpd.socket.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1
            )
            self.httpd.timeout = 5

            self.flashServerThread = mt.Thread(
                target = self.httpd.serve_forever
            )
            self.flashServerThread.setDaemon(True)
            self.flashServerThread.start()
            self.httpPort = self.httpd.socket.getsockname()[1]
            self.printr("\tHTTP Server initialized on {}".format(
                self.httpd.socket.getsockname()))

            # SET UP MASTER THREADS ============================================

            # INITIALIZE BROADCAST THREAD --------------------------------------
            # Configure sentinel value for broadcasts:
            self.broadcastSwitch = True
                # ABOUT: UDP broadcasts will be sent only when this is True
            self.broadcastSwitchLock = mt.Lock() # thread-safe access

            self.broadcastThread = mt.Thread(
                name = "FCMkII_broadcast",
                target = self._broadcastRoutine,
                args = [bytearray("N|{}|{}".format(
                            self.passcode,
                            self.listenerPort),'ascii'),
                        self.broadcastPeriodS]
                )


            # Set thread as daemon (background task for automatic closure):
            self.broadcastThread.setDaemon(True)

            # INITIALIZE LISTENER THREAD ---------------------------------------
            self.listenerThread = mt.Thread(
                name = "FCMkII_listener",
                target = self._listenerRoutine)

            # Set thread as daemon (background task for automatic closure):
            self.listenerThread.setDaemon(True)

            # INITIALIZE INPUT AND OUTPUT THREADS ------------------------------
            self.outputThread  = mt.Thread(
                name = "FCMkII_output",
                target = self._outputRoutine)
            self.outputThread.setDaemon(True)

            self.inputThread = mt.Thread(
                name = "FCMkII_input",
                target = self._inputRoutine)
            self.inputThread.setDaemon(True)

            # SET UP LIST OF KNOWN SLAVES  =====================================

            # instantiate any saved Slaves:
            saved = self.profile[ac.savedSlaves]
            self.slaves = [None]*len(saved)
            # TODO: get rid of FCSlaves

            update = False
            for index, slave in enumerate(saved):
                self.slaves[index] = \
                    sv.FCSlave(
                    name = slave[ac.SV_name],
                    mac = slave[ac.SV_mac],
                    fans = slave[ac.SV_maxFans],
                    maxFans = self.maxFans,
                    status = sv.DISCONNECTED,
                    routine = self._slaveRoutine,
                    routineArgs = (index,),
                    misoQueueSize = self.misoQueueSize,
                    index = index,
                    )

                update = True

            if update:
                self._sendSlaves()

            # START THREADS:

            # Start inter-process threads:
            self.outputThread.start()
            self.inputThread.start()

            # Start Master threads:
            self.listenerThread.start()
            self.broadcastThread.start()

            # Start Slave threads:
            for slave in self.slaves:
                slave.start()

            self.printw("NOTE: Reporting back-end listener IP as whole IP")
            self._sendNetwork()

            # DONE
            self.prints("Communicator ready")

        except Exception as e:
            self.printx(e, "Exception in Communicator __init__: ")

        # End __init__ =========================================================

    # # THREAD ROUTINES # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    # Input handling ...........................................................
    def _inputRoutine(self): # =================================================
        """
        Receive command and control vectors from the front-end.
        """
        SYM = self.SYMBOL_IR
        try:
            self.prints(SYM + " Prototype input routine started")
            while True:
                try:
                    if self.commandPipeRecv.poll():
                        D = self.commandPipeRecv.recv()
                        self.commandHandlers[D[s.CMD_I_CODE]](D)
                    if self.controlPipeRecv.poll():
                        C = self.controlPipeRecv.recv()
                        self.controlHandlers[C[s.CTL_I_CODE]](C)

                except Exception as e: # Print uncaught exceptions
                    self.printx(e, SYM + " Exception in back-end input thread:")

        except Exception as e: # Print uncaught exceptions
            self.printx(e, SYM + " Exception in back-end input thread "\
                + "(LOOP BROKEN):")
        # End _inputRoutine ====================================================

    def __handle_input_CMD_ADD(self, D):
        """
        Process the command vector D with the corresponding command.
        See fc.standards for the expected form of D.
        """
        target = D[s.CMD_I_TGT_CODE]
        if target == s.TGT_ALL:
            # REMARK: Unapplicable Slaves will be automatically ignored
            for index in range(len(self.slaves)):
                self.add(index)
        elif target == s.TGT_SELECTED:
            for index in D[s.CMD_I_TGT_OFFSET:]:
                self.add(index)
        else:
            raise ValueError("Invalid {} target code {}".format(
                s.COMMAND_CODES[D[s.CMD_I_CODE]], target))

    def __handle_input_CMD_DISCONNECT(self, D):
        """
        Process the command vector D with the corresponding command.
        See fc.standards for the expected form of D.
        """
        target = D[s.CMD_I_TGT_CODE]
        if target == s.TGT_ALL:
            self.sendDisconnect()
        elif target == s.TGT_SELECTED:
            for index in D[s.CMD_I_TGT_OFFSET:]:
                self.slaves[index].setMOSI((MOSI_DISCONNECT,),False)
        else:
            raise ValueError("Invalid {} target code {}".format(
                s.COMMAND_CODES[D[s.CMD_I_CODE]], target))

    def __handle_input_CMD_REBOOT(self, D):
        """
        Process the command vector D with the corresponding command.
        See fc.standards for the expected form of D.
        """
        target = D[s.CMD_I_TGT_CODE]
        if target == s.TGT_ALL:
            self.sendReboot()
        elif target == s.TGT_SELECTED:
            for index in D[s.CMD_I_TGT_OFFSET:]:
                self.sendReboot(self.slaves[index])
        else:
            raise ValueError("Invalid {} target code {}".format(
                s.COMMAND_CODES[D[s.CMD_I_CODE]], target))

    def __handle_input_CMD_SHUTDOWN(self, D):
        """
        Process the command vector D with the corresponding command.
        See fc.standards for the expected form of D.
        """
        self.printw("SHUTDOWN COMMAND BEHAVIOR NOT YET IMPLEMENTED") # FIXME

    def __handle_input_CMD_FUPDATE_START(self, D):
        """
        Process the command vector D with the corresponding command.
        See fc.standards for the expected form of D.
        """
        try:
            self.targetVersion = D[s.CMD_I_FU_VERSION]
            filename = D[s.CMD_I_FU_FILENAME]
            filesize = D[s.CMD_I_FU_FILESIZE]
            self.printr("Firmware update command received:"\
                "\n\tVersion: {} \n\tFile: \"{}\"\n\tSize: {} bytes)".format(
                self.targetVersion, filename, filesize))

            self.flashFlag = True

            # FIXME: Why is the passcode "CT" hard-coded? Is it because it is
            # also hard-coded in the bootloader?
            self.flashMessage = "U|CT|{}|{}|{}|{}".format(
                self.listenerPort, self.httpPort, filename, filesize)

            self.prints("Firmware update setup complete.")

        except Exception as e:
            self.printe("Exception raised in setup. Firmware update canceled.")
            self.commandHandlers[s.CMD_FUPDATE_STOP]([s.CMD_FUPDATE_STOP])
            raise e

    def __handle_input_CMD_FUPDATE_STOP(self, D):
        """
        Process the command vector D with the corresponding command.
        See fc.standards for the expected form of D.
        """
        self.printr("Received command to stop firmware update.")
        self.flashFlag = False

    def __handle_input_CMD_STOP(self, D):
        """
        Process the command vector D with the corresponding command.
        See fc.standards for the expected form of D.
        """
        self.printw("Received command to stop communications.")
        self.stop()

    def __handle_input_CMD_BMODE(self, D):
        """
        Process the command vector D with the corresponding command.
        See fc.standards for the expected form of D.
        """
        self.broadcastMode = D[s.CMD_I_BM_BMODE]
        self.printw("BMODE BEHAVIOR NOT YET IMPLEMENTED") # FIXME

    def __handle_input_CMD_BIP(self, D):
        """
        Process the command vector D with the corresponding command.
        See fc.standards for the expected form of D.
        """
        ip = D[s.CMD_I_BIP_IP]
        if self._validBIP(ip):
            self.broadcastIP = ip
            self.prints("Broadcast IP set to {}".format(ip))
            self._sendNetwork()
        else:
            self.printe("Invalid broadcast IP received: {}".format(ip))

    def __handle_input_CMD_N(self, *_):
        """
        Process a request for an updated network state vector.
        """
        self._sendNetwork()

    def __handle_input_CMD_S(self, *_):
        """
        Process a request for an updated slave state vector.
        """
        self._sendSlaves()

    def _validBIP(self, ip):
        """
        Return whether the given ip address is a valid broadcast IP.
            - ip := String, IP address to use.
        """
        if ip == "<broadcast>":
            return True
        else:
            try:
                numbers = tuple(map(int, ip.split(".")))
                if len(numbers) != 4:
                    return False
                else:
                    for number in numbers:
                        if number < 0 or number > 255:
                            return False
                    return True
            except:
                return False

    def __handle_input_CTL_DC_SINGLE(self, C):
        """
        Process the control vector C with the corresponding command.
        See fc.standards for the expected form of C.
        """
        target = C[s.CTL_I_TGT_CODE]
        dc = C[s.CTL_I_SINGLE_DC]
        # FIXME MkIV constants (RIP MOSI...)
        # L--> NOTE Apply this to others, too
        if target is s.TGT_ALL:
            fans = C[s.CTL_I_SINGLE_ALL_SELECTION]
            for slave in self.slaves: # FIXME performance w/ getIndex?
                if slave.getStatus() == sv.CONNECTED:
                    slave.setMOSI((MOSI_DC, dc,  fans), False)
        elif target is s.TGT_SELECTED:
            # FIXME performance
            i = s.CTL_I_SINGLE_TGT_OFFSET
            L = len(C)
            while i < L:
                slave = self.slaves[C[i]]
                fans = C[i + 1]
                if slave.getStatus() == sv.CONNECTED:
                    slave.setMOSI((MOSI_DC, dc,  fans), False)
                i += 2
        else:
            raise ValueError("Invalid {} target code {}".format(
                s.CONTROL_CODES[C[s.CTL_I_CODE]], target))

    def __handle_input_CTL_DC_VECTOR(self, C):
        """
        Process the control vector C with the corresponding command.
        See fc.standards for the expected form of C.
        """
        # TODO: Revise DC standard with maxFans padding

        index = 0
        i = s.CTL_I_VECTOR_DC_OFFSET
        L = len(C)

        while i < L:
            if self.slaves[index].getStatus() == sv.CONNECTED:
                self.slaves[index].setMOSI((
                    MOSI_DC_MULTI,
                    self.dcTemplate.format(*(C[i:i+self.maxFans]))))
            index += 1
            i += self.maxFans


    def _outputRoutine(self): # ================================================
        """
        Send network, slave, and fan array state vectors to the front-end.
        """
        SYM = "[OT]"
        try:
            self.prints(SYM + " Prototype output routine started")
            while True:
                time.sleep(self.periodS)
                try:

                    # Network status:
                    self._sendNetwork()

                    # Slave status:
                    self._sendSlaves()

                    # Feedback vector:
                    # FIXME performance with this format
                    F_r = []
                    F_d = []
                    for slave in self.slaves:
                        rpms, dcs = slave.getMISO()
                        F_r += rpms
                        F_d += dcs
                    self.feedbackPipeSend.send(F_r + F_d)

                except Exception as e: # Print uncaught exceptions
                    self.printx(e, SYM + "Exception in back-end output thread:")

        except Exception as e: # Print uncaught exceptions
            self.printx(e, SYM + "Exception in back-end output thread "\
                + "(LOOP BROKEN): ")
        # End _outputRoutine ===================================================

    def _broadcastRoutine(self, broadcastMessage, broadcastPeriod): # ==========
        """ ABOUT: This method is meant to run inside a Communicator instance's
            broadcastThread.
        """
        try:
            self.prints("[BT] Broadcast thread started w/ period of {}s "\
                "on port {}".format(broadcastPeriod, self.broadcastPort))

            count = 0
            while(True):
                # Increment counter:
                count += 1
                # Wait designated period:
                time.sleep(broadcastPeriod)
                if self.broadcastSwitch:
                    # Broadcast message:
                    self.broadcastSocket.sendto(broadcastMessage,
                        (self.broadcastIP, self.broadcastPort))
        except Exception as e:
            self.printx(e, "[BT] Fatal error in broadcast thread:")
            self.stop()
        # End _broadcastRoutine ================================================

    def _listenerRoutine(self): # ==============================================
        """ ABOUT: This method is meant to run within an instance's listener-
            Thread. It will wait indefinitely for messages to be received by
            the listenerSocket and respond accordingly.
        """

        self.prints("[LR] Listener thread started. Waiting.")

        # Get standard replies:
        launchMessage = "L|{}".format(self.passcode)

        while(True):
            try:
                # Wait for a message to arrive:
                messageReceived, senderAddress = \
                    self.listenerSocket.recvfrom(256)

                # DEBUG: print("Message received")

                """ NOTE: The message received from Slave, at this point,
                    should have one of the following forms:

                    - STD from MkII:
                        A|PCODE|SV:MA:CA:DD:RE:SS|N|SMISO|SMOSI|VERSION
                        0     1         2 3 4     5 6
                    - STD from Bootloader:
                        B|PCODE|SV:MA:CA:DD:RE:SS|N|[BOOTLOADER_VERSION]
                        0     1                 2 3                 4

                    - Error from MkII:
                        A|PCODE|SV:MA:CA:DD:RE:SS|E|ERRMESSAGE

                    - Error from Bootloader:
                        B|PCODE|SV:MA:CA:DD:RE:SS|E|ERRMESSAGE

                    Where SMISO and SMOSI are the Slave's MISO and MOSI
                    port numbers, respectively. Notice separators.
                """
                messageSplitted = messageReceived.decode('ascii').split("|")
                    # NOTE: messageSplitted is a list of strings, each of which
                    # is expected to contain a string as defined in the comment
                    # above.

                # Verify passcode:
                if messageSplitted[1] != self.passcode:
                    self.printw("Wrong passcode received (\"{}\") "\
                        "from {}".format(messageSplitted[1],
                        senderAddress[0]))

                    #print "Wrong passcode"

                    continue

                # Check who's is sending the message
                if messageSplitted[0][0] == 'A':
                    # This message comes from the MkII

                    try:
                        mac = messageSplitted[2]

                        # Check message type:
                        if messageSplitted[3] == 'N':
                            # Standard broadcast reply

                            misoPort = int(messageSplitted[4])
                            mosiPort = int(messageSplitted[5])
                            version = messageSplitted[6]

                            # Verify converted values:
                            if (misoPort <= 0 or misoPort > 65535):
                                # Raise a ValueError if a port number is invalid:
                                self.printw(
                                    "Bad SMISO ({}). Need [1, 65535]".format(
                                        miso))

                            if (mosiPort <= 0 or mosiPort > 65535):
                                # Raise a ValueError if a port number is invalid:
                                raise ValueError(
                                    "Bad SMOSI ({}). Need [1, 65535]".\
                                    format(mosi))

                            if (len(mac) != 17):
                                # Raise a ValueError if the given MAC address is
                                # not 17 characters long.
                                raise ValueError("MAC ({}) not 17 chars".\
                                    format(mac))

                            # Search for Slave in self.slaves
                            index = None
                            for slave in self.slaves:
                                if slave.getMAC() == mac:
                                    index = slave.getIndex()
                                    break

                            # Check if the Slave is known:
                            if index is not None :
                                # Slave already recorded

                                # Check flashing case:
                                if self.flashFlag and version != \
                                    self.targetVersion:
                                    # Version mismatch. Send reboot message

                                    # Send reboot message
                                    self.listenerSocket.sendto(
                                        bytearray("R|{}".\
                                            format(self.passcode),'ascii'),
                                        senderAddress
                                    )

                                # If the index is in the Slave dictionary,
                                # check its status and proceed accordingly:

                                elif self.slaves[index].getStatus() in \
                                    (sv.DISCONNECTED, sv.BOOTLOADER):
                                    # If the Slave is DISCONNECTED but just res-
                                    # ponded to a broadcast, update its status
                                    # for automatic reconnection. (handled by
                                    # their already existing Slave thread)

                                    # Update status and networking information:
                                    self.setSlaveStatus(
                                        self.slaves[index],
                                        sv.KNOWN,
                                        lock = False,
                                        netargs = (
                                            senderAddress[0],
                                            misoPort,
                                            mosiPort,
                                            version
                                            )
                                    )
                                else:
                                    # All other statuses should be ignored for
                                    # now.
                                    pass

                            else:
                                # Newly met Slave
                                index = len(self.slaves)
                                # If the MAC address is not recorded, list it
                                # AVAILABLE and move on. The user may choose
                                # to add it later.
                                name = rd.choice(nm.coolNames)
                                fans = self.defaultSlave[ac.SV_maxFans]

                                self.slaves.append(
                                    sv.FCSlave(
                                        name = name,
                                        mac = mac,
                                        fans = fans,
                                        maxFans = self.maxFans,
                                        status = sv.AVAILABLE,
                                        routine = self._slaveRoutine,
                                        routineArgs = (index, ),
                                        version = version,
                                        misoQueueSize = self.misoQueueSize,
                                        ip = senderAddress[0],
                                        misoP = misoPort,
                                        mosiP = mosiPort,
                                        index = index)
                                )

                                # Add new Slave's information to newSlaveQueue:
                                self._sendSlaves()

                                # Start Slave thread:
                                self.slaves[index].start()

                        elif messageSplitted[3] == 'E':
                            # Error message

                            self.printe("Error message from Slave {}: "\
                                "\"{}\"".format(
                                    messageSplitted[2], messageSplitted[3]))
                        else:
                            # Invalid code
                            raise IndexError

                    except IndexError:
                        self.printw("Invalid message \"{}\" discarded; "\
                            "sent by {}".format(
                                messageReceived,senderAddress))

                elif messageSplitted[0][0] == 'B':
                    # This message comes from the Bootloader

                    try:
                        # Check message type:
                        if messageSplitted[3] == 'N':
                            # Standard broadcast

                            if not self.flashFlag:
                                # No need to flash. Launch MkII:
                                self.listenerSocket.sendto(
                                    bytearray(launchMessage,'ascii'),
                                    senderAddress)

                            else:
                                # Flashing in progress. Send flash message:

                                self.listenerSocket.sendto(
                                    bytearray(self.flashMessage,'ascii'),
                                    senderAddress)

                            # Update Slave status:

                            # Search for Slave in self.slaves
                            index = None
                            mac = messageSplitted[2]

                            for slave in self.slaves:
                                if slave.getMAC() == mac:
                                    index = slave.getIndex()
                                    break

                            if index is not None:
                                # Known Slave. Update status:

                                # Try to get bootloader version:
                                try:
                                    version = messageSplitted[4]
                                except IndexError:
                                    version = "Bootloader(?)"

                                self.slaves[index].setVersion(version)
                                self.setSlaveStatus(
                                    self.slaves[index],
                                    sv.BOOTLOADER
                                )

                            else:

                                # Send launch message:
                                self.listenerSocket.sendto(
                                    bytearray(launchMessage,'ascii'),
                                    senderAddress)


                        elif messageSplitted[3] == 'E':
                            # Error message

                            self.printe("Error message from {} "\
                                "on Bootloader: \"{}\"".format(
                                    messageSplitted[2],
                                    messageSplitted[4]))

                    except IndexError:
                        self.printw("Invalid message \"{}\" discarded; "\
                            "sent by {}".format(
                                senderAddress[0], messageReceived))
                else:
                    # Invalid first character (discard message)
                    self.printw("Warning: Message from {} w/ invalid first "\
                        "character '{}' discarded".format(
                            senderAddress[0], messageSplitted[0]))

            except Exception as e: # Print uncaught exceptions
                self.printx(e, "Exception in listener thread")
        # End _listenerRoutine =================================================

    def _slaveRoutine(self, targetIndex, target): # # # # # # # # # # # # # # # #
        # ABOUT: This method is meant to run on a Slave's communication-handling
        # thread. It handles sending and receiving messages through its MISO and
        # MOSI sockets, at a pace dictated by the Communicator instance's given
        # period.
        # PARAMETERS:
        # - targetIndex: int, index of the Slave handled
        # - target: Slave controlled by this thread
        # NOTE: This version is expected to run as daemon.

        try:

            # Setup ============================================================

            # Get reference to Slave: ------------------------------------------
            slave = target

            # Set up sockets ---------------------------------------------------
            # MISO:
            misoS = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            misoS.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            misoS.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            misoS.settimeout(self.periodS*2)
            misoS.bind(('', 0))

            # MOSI:
            mosiS = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            mosiS.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            mosiS.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            mosiS.settimeout(self.periodS)
            mosiS.bind(('', 0))

            # Assign sockets:
            slave.setSockets(newMISOS = misoS, newMOSIS = mosiS)

            self.printr("[SV] ({:3d}) Slave sockets connected: "\
             " MMISO: {} MMOSI:{} (IP: {})".\
                format(targetIndex + 1,
                    slave._misoSocket().getsockname()[1],
                    slave._mosiSocket().getsockname()[1],
                    slave.getIP()))

            # HSK message ------------------------------------------------------
            def _makeHSK():
                return  "H|{},{},{},{},{}|"\
                    "{} {} {} {} {} {} {} {} {} {} {}".format(
                        slave._misoSocket().getsockname()[1],
                        slave._mosiSocket().getsockname()[1],
                        self.periodMS,
                        self.broadcastPeriodS*1000,
                        self.maxTimeouts,
                        # FIXME: Set values per slave, not globals
                        self.fanMode,
                        self.maxFans,
                        self.fanFrequencyHZ,
                        self.counterCounts,
                        self.pulsesPerRotation,
                        self.maxRPM,
                        self.minRPM,
                        self.minDC,
                        self.chaserTolerance,
                        self.maxFanTimeouts,
                        self.pinout)

            MHSK = _makeHSK()

            # Set up placeholders and sentinels --------------------------------
            slave.resetIndices()
            periodS = self.periodS
            timeouts = 0
            totalTimeouts = 0
            message = "P"
            tryBuffer = True

            failedHSKs = 0


            # Slave loop =======================================================
            while(True):

                try:
                #slave.acquire()

                    status = slave.getStatus()

                    # Act according to Slave's state:
                    if status == sv.KNOWN: # = = = = = = = = = = = = = = = =

                        # If the Slave is known, try to secure a connection:
                        # print "Attempting handshake"

                        # Check for signs of life w/ HSK message:
                        self._send(MHSK, slave, 2, True)

                        # Give time to process:
                        #time.sleep(periodS)

                        tries = 2
                        while True:

                            # Try to receive reply:
                            reply = self._receive(slave)

                            # Check reply:
                            if reply is not None and reply[1] == "H":
                                # print "Processed reply: {}".format(reply), "G"
                                # print "Handshake confirmed"

                                # Mark as CONNECTED and get to work:
                                #slave.setStatus(sv.CONNECTED, lock = False)
                                self.setSlaveStatus(slave,sv.CONNECTED,False)
                                tryBuffer = True
                                break

                                """
                                self._saveTimeStamp(slave.getIndex(), "Connected")
                                """

                            elif reply is not None and reply[1] == "K":
                                # HSK acknowledged, give Slave time
                                continue

                            elif tries > 0:
                                # Try again:
                                self._send(MHSK, slave, 1, True)
                                tries -= 1

                            elif failedHSKs is 0:
                                # Disconnect Slave:
                                self._send("X", slave, 2)
                                #slave.setStatus(sv.DISCONNECTED, lock = False)

                                self.setSlaveStatus(
                                    slave,sv.DISCONNECTED,False)
                                    # NOTE: This call also resets exchange
                                    # index.
                                break

                            else:
                                # Something's wrong. Reset sockets.
                                self.printw("Resetting sockets for {} ({})".\
                                    format(slave.getMAC(), targetIndex + 1))

                            # MISO:
                            slave._misoSocket().close()

                            misoS = socket.socket(
                                socket.AF_INET, socket.SOCK_DGRAM)
                            misoS.setsockopt(
                                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                            misoS.setsockopt(
                                socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                            misoS.settimeout(self.periodS*2)
                            misoS.bind(('', 0))

                            # MOSI:
                            slave._misoSocket().close()

                            mosiS = socket.socket(
                                socket.AF_INET, socket.SOCK_DGRAM)
                            mosiS.setsockopt(
                                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                            mosiS.setsockopt(
                                socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                            mosiS.settimeout(self.periodS)
                            mosiS.bind(('', 0))

                            # Assign sockets:
                            slave.setSockets(newMISOS = misoS, newMOSIS = mosiS)

                            self.printr("[SV] {:3d} Slave sockets "\
                                "re-connected: MMISO: {} MMOSI:{}".format(
                                    targetIndex + 1,
                                    slave._misoSocket().getsockname()[1],
                                    slave._mosiSocket().getsockname()[1]))

                            # HSK message --------------------------------------
                            MHSK = _makeHSK()

                            # Reset counter:
                            failedHSKs = 0

                            continue

                    elif status == sv.CONNECTED: # = = = = = = = = = = = = = = =
                        # If the Slave's state is positive, it is online and
                        # there is a connection to maintain.

                        # A positive state indicates this Slave is online and
                        # its connection need be maintained.

                        #DEBUG DEACTV
                        ## print "[On positive state]"

                        # Check flashing flag:
                        if self.flashFlag and slave.getVersion() != \
                            self.targetVersion:

                            # If the flashing flag is set and this Slave has
                            # the wrong version, reboot it

                            self._send("R", slave, 1)
                            self.setSlaveStatus(slave, sv.DISCONNECTED, False)

                            continue

                        # Check queue for message:
                        fetchedMessage = slave.getMOSI()

                        if fetchedMessage is None:
                            # Nothing to fetch. Send previous command

                            # Send message:
                            self._send(message, slave, 2)

                        elif fetchedMessage[0] == MOSI_DC:
                            # NOTE MkIV format:
                            # (MOSI_DC, DC, SELECTION)
                            # -> DC is already normalized
                            # -> SELECTION is string of 1's and 0's

                            message = "S|D:{}:{}".format(
                                fetchedMessage[1], fetchedMessage[2])
                            #   \---------------/  \---------------/
                            #      Duty cycle         Selection

                            self._send(message, slave, 2)

                        elif fetchedMessage[0] == MOSI_DC_MULTI:
                            # NOTE MkIV format:
                            # (MOSI_DC_MULTI, "dc_0,dc_1,dc_2...dc_maxFans")
                            # Here each dc is already normalized
                            # NOTE: Notice here maxFans is assumed (should be
                            # ignored by slave)
                            message = "S|F:" + fetchedMessage[1]
                            self._send(message, slave, 2)

                        elif fetchedMessage[0] == MOSI_DISCONNECT:
                            self._sendToListener("X", slave, 2)

                        elif fetchedMessage[0] == MOSI_REBOOT:
                            self._sendToListener("R", slave, 2)

                        # DEBUG:
                        # print "Sent: {}".format(message)

                        # Get reply:
                        reply = self._receive(slave)

                        # Check reply: -----------------------------------------
                        if reply is not None:
                            # print "Processed reply: {}".format(reply)

                            # Restore timeout counter after success:
                            timeouts = 0

                            # Check message type:
                            if reply[1] == 'T':
                                # Standard update

                                # Get data index:
                                receivedDataIndex = int(reply[2])

                                # Check for redundant data:
                                if receivedDataIndex > slave.getDataIndex():
                                    # If this data index is greater than the
                                    # currently stored one, this data is new and
                                    # should be updated:

                                    # Update data index:
                                    slave.setDataIndex(receivedDataIndex)

                                    # Update RPMs and DCs:
                                    try:
                                        # Set up data placeholder as a tuple:
                                        # FIXME performance

                                        rpms =  list(map(
                                            int,reply[-2].split(',')))
                                        dcs = list(map(
                                            float,reply[-1].split(',')))

                                        rpms += [0]*(self.maxFans - len(rpms))
                                        dcs += [0]*(self.maxFans - len(dcs))

                                        # FIXME performance pls
                                        # FIXME rem. fix on slave.getMISO()
                                        # when this format is changed
                                        slave.setMISO((rpms, dcs), False)
                                            # FORM: (RPMs, DCs)
                                    except queue.Full:
                                        # If there is no room for this message,
                                        # drop the packet and alert the user:
                                        slave.incrementDropIndex()

                            elif reply[1] == 'I':
                                # Reset MISO index

                                slave.setMISOIndex(0)
                                self.printr("[SV] {} MISO Index reset".format(
                                    slave.getMAC()))

                            elif reply[1] == 'P':
                                # Ping request

                                self._send("P", slave)

                            elif reply[1] == 'Y':
                                # Reconnect reply

                                pass

                            elif reply[1] == 'M':
                                # Maintain connection. Pass
                                pass

                            elif reply[1] == 'H':
                                # Old HSK message. Pass
                                pass

                            elif reply[1] == 'E':
                                # Error report

                                self.printe("[SV] {:3d} ERROR: \"{}\"".format(
                                    targetIndex + 1, reply[2]))

                            elif reply[1] == 'Q':
                                # Ping reply. Pass
                                pass

                            else:
                                # Unrecognized command

                                self.printw("[SV] {:3d} Warning, unrecognized "\
                                    "message: \"{}\"".format(
                                        targetIndex + 1, reply))

                        else:
                            timeouts += 1
                            totalTimeouts += 1

                            """
                            if message is not None:
                                # If a message was sent and no reply was
                                # received, resend it:
                                # print "Timed out. Resending"
                                # Resend message:
                                self._send(message, slave, 1)
                                # Increment timeout counter:

                            """

                            # Check timeout counter: - - - - - - - - - - - - - -
                            if timeouts == self.maxTimeouts -1:
                                # If this Slave is about to time out, send a
                                # ping request

                                self._send("Q", slave, 2)

                            elif timeouts < self.maxTimeouts:
                                # If there have not been enough timeouts to con-
                                # sider the connection compromised, continue.
                                # print "Reply missed ({}/{})".
                                #   format(timeouts,
                                #   self.maxTimeouts)

                                # Restart loop:
                                pass

                            elif tryBuffer:
                                self._send("Y", slave, 2)
                                tryBuffer = False

                            else:
                                self.printw("[SV] {} Slave timed out".\
                                    format(targetIndex + 1))

                                # Terminate connection: ........................

                                # Send termination message:
                                self._sendToListener("X", slave)

                                # Reset timeout counter:
                                timeouts = 0
                                totalTimeouts = 0

                                # Update Slave status:
                                """
                                slave.setStatus(
                                    sv.DISCONNECTED, lock = False)
                                """
                                self.setSlaveStatus(
                                    slave, sv.DISCONNECTED, False)
                                # Restart loop:
                                pass

                                # End check timeout counter - - - - - - - - - -

                            # End check reply ---------------------------------

                    elif status == sv.BOOTLOADER:
                        time.sleep(self.periodS)

                    else: # = = = = = = = = = = = = = = = = = = = = = = = = = =
                        time.sleep(self.periodS)
                        """
                        # If this Slave is neither online nor waiting to be
                        # contacted, wait for its state to change.

                        command = "P"
                        message = "P"

                        # Check if the Slave is mistakenly connected:
                        reply = self._receive(slave)

                        if reply is not None:
                            # Slave stuck! Send reconnect message:
                            if slave.getIP() is not None and \
                                slave.getMOSIPort() is not None:
                                self._send("Y", slave)

                                reply = self._receive(slave)

                                if reply is not None and reply[1] == "Y":
                                    # Slave reconnected!
                                    #slave.setStatus(sv.CONNECTED)
                                    self.setSlaveStatus(
                                        slave,sv.CONNECTED, False)

                            else:
                                self._sendToListener("X", slave)
                        """
                except Exception as e: # Print uncaught exceptions
                    self.printx(e, "[{}] Exception: ".format(targetIndex + 1))

                finally:
                    # DEBUG DEACTV
                    ## print "Slave lock released", "D"
                    # Guarantee release of Slave-specific lock:
                    """
                    try:
                        slave.release()
                    except _thread.error:
                        pass
                    """
                # End Slave loop (while(True)) =================================


        except Exception as e: # Print uncaught exceptions
            self.printx(e, "[{}] Exception: (BROKEN LOOP)".format(
                targetIndex + 1))
        # End _slaveRoutine  # # # # # # # # # # # # # # # # # # # # # # # # #

    # # AUXILIARY METHODS # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # ABOUT: These methods are to be used within this class. For methods to
        # be accessed by the user of a Communicator instance, see INTERFACE ME-
        # THODS below.

    def _send(self, message, slave, repeat = 1, hsk = False): # # # # # # # # #
        # ABOUT: Send message to a KNOWN or CONNECTED sv. Automatically add
        # index.
        # PARAMETERS:
        # - message: str, message to send (w/o "INDEX|")
        # - slave: Slave to contact (must be KNOWN or CONNECTED or behavior is
        #   undefined)
        # - repeat: How many times to send message.
        # - hsk: Bool, whether this message is a handshake message.
        # - broadcast: Bool, whether to send this message as a broad
        # WARNING: THIS METHOD ASSUMES THE SLAVE'S LOCK IS HELD BY ITS CALLER.

        if not hsk:
            # Increment exchange index:
            slave.incrementMOSIIndex()
        else:
            # Set index to zero:
            slave.setMOSIIndex(0)

        # Prepare message:
        outgoing = "{}|{}".format(slave.getMOSIIndex(), message)

        # Send message:
        for i in range(repeat):
            slave._mosiSocket().sendto(bytearray(outgoing,'ascii'),
                (slave.ip, slave.getMOSIPort()))

        # Notify user:
        # print "Sent \"{}\" to {} {} time(s)".
        #   format(outgoing, (slave.ip, slave.mosiP), repeat))

        # End _send # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def _sendToListener(self, message, slave, repeat = 1, targetted = True): # #
        # ABOUT: Send a message to a given Slave's listener socket.


        if targetted and slave.ip is not None:
            # Send to listener socket:
            # Prepare message:
            outgoing = "{}|{}".format(message, self.passcode)
            for i in range(repeat):
                slave._mosiSocket().sendto(bytearray(outgoing,'ascii'),
                (slave.ip, self.broadcastPort))
        else:
            # Send through broadcast:
            # Prepare message:
            outgoing = "J|{}|{}|{}".format(
                self.passcode, slave.getMAC(), message)
            for i in range(repeat):
                slave._mosiSocket().sendto(bytearray(outgoing,'ascii'),
                (self.DEFAULT_BROADCAST_IP, self.broadcastPort))

        # End _sendToListener # # # # # # # # # # # # # # # # # # # # # # # # # #

    def _receive(self, slave): # # # # # # # # # # # # # # # # # # # # # # # # #
        # ABOUT: Receive a message on the given Slave's sockets (assumed to be
        # CONNECTED, BUSY or KNOWN.
        # PARAMETERS:
        # - slave: Slave unit for which to listen.
        # RETURNS:
        # - three-tuple:
        #   (exchange index (int), keyword (str), command (str) or None)
        #   or None upon failure (socket timeout or invalid message)
        # RAISES:
        # - What exceptions may arise from passing an invalid argument.
        # WARNING: THIS METHOD ASSUMES THE SLAVE'S LOCK IS HELD BY ITS CALLER.

        try:
            # Keep searching for messages until a message with a matching index
            # is found or the socket times out (no more messages to retrieve)
            index = -1
            indexMatch = False
            count = 0
            while(True): # Receive loop = = = = = = = = = = = = = = = = = = = =

                # Increment counter: -------------------------------------------
                count += 1
                # DEBUG DEACTV
                ## print "Receiving...({})".format(count), "D"

                # Receive message: ---------------------------------------------
                message, sender = slave._misoSocket().recvfrom(
                    self.maxLength)

                # DEBUG DEACTV
                """
                print "Received: \"{}\" from {}".\
                    format(message, sender)
                """

                try:
                    # Split message: -------------------------------------------
                    splitted = message.decode('ascii').split("|")

                    # Verify index:
                    index = int(splitted[0])

                    if index <= slave.getMISOIndex():
                        # Bad index. Discard message:
                        # print "Bad index: ({})".
                        #   format(index), "D"

                        # Discard message:
                        continue

                    # Check for possible third element:
                    # DEBUG PRINT:
                    #print \
                    #    "Got {} part(s) from split: {}".\
                    #    format(len(splitted), str(splitted)), "D"

                    output = None

                    if len(splitted) == 2:
                        output = (index, splitted[1])

                    elif len(splitted) == 3:
                        output = (index, splitted[1], splitted[2])

                    elif len(splitted) == 4:
                        output = (index, splitted[1], splitted[2], splitted[3])

                    elif len(splitted) == 5:
                        output = (index, splitted[1], int(splitted[2]), splitted[3],
                            splitted[4])

                    else:
                        # print
                        #"ERROR: Unrecognized split amount ({}) on: {}".\
                        #format(len(splitted), str(splitted)), "E")
                        return None

                    # Update MISO index:
                    slave.setMISOIndex(index)

                    # Return splitted message: ---------------------------------
                    # DEBUG DEACTV
                    ## print "Returning {}".format(output), "D"
                    return output

                except (ValueError, IndexError, TypeError) as e:
                    # Handle potential Exceptions from format mismatches:

                    # print "Bad message: \"{}\"".
                    #   format(e), "W")

                    if not indexMatch:
                        # If the correct index has not yet been found, keep lo-
                        # oking:

                        # DEBUG DEACTV
                        ## print "Retrying receive", "D"

                        continue;
                    else:
                        # If the matching message is broken, exit w/ error code
                        # (None)
                        # print
                        #   "WARNING: Broken message with matching index: " +\
                        #   "\n\t Raw: \"{}\"" +\
                        #   "\n\t Splitted: {}" +\
                        #   "\n\t Error: \"{}\"".\
                        #   format(message, splitted, e), "E")

                        return None

                # End receive loop = = = = = = = = = = = = = = = = = = = = = = =

        # Handle exceptions: ---------------------------------------------------
        except socket.timeout:
            # print "Timed out.", "D"
            return None

        # End _receive # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def getNewSlaves(self): # ==================================================
        # Get new Slaves, if any. Will return either a tuple of MAC addresses
        # or None.

        # FIXME: Obsolete? Delete?

        try:
            return self.newSlaveQueue.get_nowait()
        except queue.Empty:
            return None

        # End getNewSlaves =====================================================

    # # INTERFACE METHODS # # # # # # # # # # # # # # # # # # # # # # # # #

    def add(self, targetIndex): # ==============================================
        # ABOUT: Mark a Slave on the network for connection. The given Slave
        # must be already listed and marked AVAILABLE. This method will mark it
        # as KNOWN, and its corresponding handler thread will connect automati-
        # cally.
        # PARAMETERS:
        # - targetIndex: int, index of Slave to "add."
        # RAISES:
        # - Exception if targeted Slave is not AVAILABLE.
        # - KeyError if targetIndex is not listed.

        # Check status:
        status = self.slaves[targetIndex].getStatus()

        if status == sv.AVAILABLE:
            self.setSlaveStatus(self.slaves[targetIndex], sv.KNOWN)
        else:
            pass

        # End add ==============================================================

    def sendReboot(self, target = None): # =====================================
        # ABOUT: Use broadcast socket to send a general "disconnect" message
        # that terminates any existing connection.

        try:
            #self.broadcastLock.acquire()
            if target is None:
                # General broadcast
                self.rebootSocket.sendto(
                    bytearray("R|{}".format(self.passcode),'ascii'),
                    (self.DEFAULT_BROADCAST_IP, self.broadcastPort))

            elif target.getIP() is not None:
                # Targetted broadcast w/ valid IP:
                self.rebootSocket.sendto(
                    bytearray("R|{}".format(self.passcode),'ascii'),
                    (target.getIP(), self.broadcastPort))

            else:
                # Targetted broadcast w/o IP (use MAC):
                self.rebootSocket.sendto(
                    bytearray("r|{}|{}".format(self.passcode, target.getMAC()),
                        'ascii'),
                        (self.DEFAULT_BROADCAST_IP, self.broadcastPort))

        except Exception as e:
            self.printx(e, "[sR] Exception in reboot routine:")

        #finally:
            #self.broadcastLock.release()

        # End sendReboot =======================================================

    def sendDisconnect(self): # ================================================
        # ABOUT: Use disconenct socket to send a general "disconnect" message
        # that terminates any existing connection.

        try:
            #self.broadcastLock.acquire()
            self.disconnectSocket.sendto(
                bytearray("X|{}".format(self.passcode),'ascii'),
                (self.DEFAULT_BROADCAST_IP, self.broadcastPort))

        except Exception as e:
            self.printx(e, "[sD] Exception in disconnect routine")

        # End sendDisconnect ===================================================

    def setSlaveStatus(self, slave, newStatus, lock = True, netargs = None): # =
        # FIXME: No locking?
        # FIXME: Upon simplification of SV data structure...

        # Update status:
        if netargs is None:
            slave.setStatus(newStatus, lock = lock)
        else:
            slave.setStatus(newStatus, netargs[0], netargs[1], netargs[2],
                netargs[3], lock = lock)

        # Send update to handlers:
        self.slaveUpdateQueue.put_nowait(self.getSlaveStateVector(slave))
        # End setSlaveStatus ===================================================

    def getSlaveStateVector(self, slave):
        """
        Generate and return a list to be appended to a slave state vector.
        - slave: slave object from which to generate the list.
        """
        return [slave.index, slave.name, slave.mac, slave.getStatus(),
            slave.fans, slave.version]

    def stop(self): # ==========================================================
        """
        Clean up to terminate.
        """
        # NOTE: All threads are set as Daemon and all sockets as reusable.

        self.printw("Terminating back-end")
        # Send disconnect signal:
        self.sendDisconnect()
        self.stopped.set()
        self.printw("Terminated back-end")
        return
        # End shutdown =========================================================

    def join(self, timeout = None):
        """
        Block until the communicator terminates.
            timeout := seconds to wait (float)
        """
        self.stopped.wait(timeout)

    def _sendNetwork(self):
        """
        Send a network state vector to the front end.
        """
        self.networkPipeSend.send(
            (s.NS_CONNECTED,
            self.listenerSocket.getsockname()[0], # FIXME (?)
            self.broadcastIP,
            self.broadcastPort,
            self.listenerPort))

    def _sendSlaves(self):
        S = []
        for slave in self.slaves:
            S += self.getSlaveStateVector(slave)
        self.slavePipeSend.send(S)

## MODULE'S TEST SUITE #########################################################

if __name__ == "__main__":
    pass
