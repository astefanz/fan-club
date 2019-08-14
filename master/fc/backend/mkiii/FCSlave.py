################################################################################
## Project: Fan Club Mark II "Master" ## File: FCSlave.py                     ##
##----------------------------------------------------------------------------##
## CALIFORNIA INSTITUTE OF TECHNOLOGY ## GRADUATE AEROSPACE LABORATORY ##     ##
## CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES                             ##
##----------------------------------------------------------------------------##
##      ____      __      __  __      _____      __      __    __    ____     ##
##     / __/|   _/ /|    / / / /|  _- __ __\    / /|    / /|  / /|  / _  \    ##
##    / /_ |/  / /  /|  /  // /|/ / /|__| _|   / /|    / /|  / /|/ /   --||   ##
##   / __/|/ _/    /|/ /   / /|/ / /|    __   / /|    / /|  / /|/ / _  \|/    ##
##  / /|_|/ /  /  /|/ / // //|/ / /|__- / /  / /___  / -|_ - /|/ /     /|     ##
## /_/|/   /_/ /_/|/ /_/ /_/|/ |\ ___--|_|  /_____/| |-___-_|/  /____-/|/     ##
## |_|/    |_|/|_|/  |_|/|_|/   \|___|-    |_____|/   |___|     |____|/       ##
##                   _ _    _    ___   _  _      __   __                      ##
##                  | | |  | |  | T_| | || |    |  | |  |                     ##
##                  | _ |  |T|  |  |  |  _|      ||   ||                      ##
##                  || || |_ _| |_|_| |_| _|    |__| |__|                     ##
##                                                                            ##
##----------------------------------------------------------------------------##
## Alejandro A. Stefan Zavala ## <alestefanz@hotmail.com> ##                  ##
################################################################################

## ABOUT #######################################################################
"""
OOP representation of Slave units.

"""
################################################################################

## DEPENDENCIES ################################################################

import random # FIXME

# Network:
import socket

# Data:
import queue      # Communication between threads
import threading   # Thread-safe access

# MkIV:
import fc.standards as s

## CONSTANT VALUES #############################################################

# SLAVE STATUS CODES:
    # ABOUT: Positive status codes are for connected Slaves, negative codes for
    # disconnected ones.

AVAILABLE = s.SS_AVAILABLE
KNOWN = s.SS_KNOWN
DISCONNECTED = s.SS_DISCONNECTED
BOOTLOADER = s.SS_UPDATING
CONNECTED = s.SS_CONNECTED

# SLAVE UPDATE CODES:

STATUS_CHANGE = 1
VALUE_UPDATE = 0

# MISO MATRIX UPDATE CODES:
MISO_UPDATED = 11
MISO_NO_UPDATE = 10

# AUXILIARY DEFINITIONS ########################################################

def translate(statusCode, short = False): # ====================================
    # ABOUT: Translate an integer status code to a String.
    # PARAMETERS:
    # - statusCode: int, status code to translate.
    # - short: bool, whether to give corresponding single-char version.
    # RAISES:
    # - ValueError if given argument is not a valid status code

    result = ""

    if statusCode == DISCONNECTED:
        result = "DISCONNECTED"
    elif statusCode == AVAILABLE:
        result = "AVAILABLE"
    elif statusCode == KNOWN:
        result = "KNOWN"
    elif statusCode == CONNECTED:
        result = "CONNECTED"
    elif statusCode == BOOTLOADER:
        result = "BOOTLOADER"
    else:
        raise ValueError("Slave.translate got nonexistent statusCode! ({})".\
            format(statusCode))

    if short:
        return result[0]
    else:
        return result

    # End translate # ==========================================================

## CLASS DEFINITION ############################################################

class FCSlave:
    # ABOUT: Representation of connected Slave model, primarily a container with
    # no behavior besides that of its components, such as Locks.

    def __init__(self, name, mac, fans, maxFans, status, routine,
        routineArgs, misoQueueSize, index, version = "MkII(?)",
        ip = None, misoP = None, mosiP = None, misoS = None, mosiS = None):
        # ABOUT: Constructor for class Slave.

        # ATTRIBUTE HANDLER TABLE ----------------------------------------------
        #   ABOUT: This table describes each attribute of this class and how
        #   these are meant to be used and accessed.
        #   NOTE: It is implied that these attributes will be accessed through
        #   the corresponding get/set methods.
        #
        #   ATTRIBUTE           KIND        MODIFIER        THREADING
        #   --------------------------------------------------------------------
        #   Name                constant    None            Free (R.O)
        #   MAC Address         constant    None (R.O)      Free (R.O)
        #   Status              variable    LT & ST         Full lock on set
        #   Fans                constant    None            Free (R.O)
        #   ....................................................................
        #   MOSI index          volatile    ST              Locked get/set
        #   MISO index          volatile    ST (_receive)   Locked get/set
        #   Data index          volatile    ST (_receive)   Locked get/set
        #   IP Address          variable    LT              Set w/ status (F.L)
        #   MISO/MOSI Ports     variables   LT              Set w/ status (F.L)
        #   MISO/MOSI Sockets   variables   ST              Full lock on set
        #
        #   --------------------------------------------------------------------
        #   LEGEND:
        #   Here "constant" means an attribute will not change during execution
        #   and is therefore thread-safe to access (at least in Python!);
        #   "variable" means it will change during execution and must use locks
        #   for thread-safety; "volatile" means it is expected to change very
        #   frequently and therefore deserves special measures for efficiency.
        # ----------------------------------------------------------------------

        # Validate parameters ..................................................
            # Because Lord knows something will go wrong.

        if type(name) is not str:
            raise TypeError(
                "Attribute 'name' must be str, not {}".format(type(name)))
        if type(mac) is not str:
            raise TypeError(
                "Attribute 'mac' must be str, not {}".format(type(mac)))
        elif type(fans) is not int:
            raise TypeError(
                "Attribute 'fans' must be int, not {}".format(type(fans)))
        elif type(maxFans) is not int:
            raise TypeError(
                "Attribute 'maxFans' must be int, not {}".format(type(maxFans)))
        elif type(status) is not int:
            raise TypeError(
                "Attribute 'status' must be int, not {}".format(type(status)))
        elif status not in (CONNECTED, KNOWN, DISCONNECTED, AVAILABLE):
            raise ValueError("Argument 'status' must be valid status code "\
                "(not {})".format(status))
        elif type(routine) is not type(self.getMAC):
            raise TypeError(
                "Attribute 'routine' must be function, not {}".\
                format(type(routine)))
        elif type(misoQueueSize) is not int:
            raise TypeError(
                "Attribute 'misoQueueSize' must be int, not {}".\
                format(type(misoQueueSize)))
        elif type(index) is not int:
            raise TypeError(
                "Attribute 'index' must be int, not {}".\
                format(type(index)))
        elif type(version) is not str:
            raise TypeError(
                "Attribute 'version' must be int, not {}".\
                format(type(version)))
        elif type(ip) not in (str, type(None)):
            raise TypeError(
                "Attribute 'ip' must be str or None, not {}".\
                format(type(ip)))
        elif type(misoP) not in (int, type(None)):
            raise TypeError(
                "Attribute 'misoP' must be int or None, not {}".\
                format(type(misoP)))
        elif type(mosiP) not in (int, type(None)):
            raise TypeError(
                "Attribute 'mosiP' must be int or None, not {}".\
                format(type(mosiP)))
        elif type(misoS) not in (socket.socket, type(None)):
            raise TypeError(
                "Attribute 'misoS' must be socket.socket or None, "\
                "not {}".\
                format(type(misoS)))
        elif type(mosiS) not in (socket.socket, type(None)):
            raise TypeError(
                "Attribute 'mosiS' must be socket.socket or None, "\
                "not {}".\
                format(type(mosiS)))

        # Initialize constant attributes .......................................

        # Name:
        self.name = name

        # MAC:
        self.mac = mac

        # Fans:
        self.fans = fans
        self.maxFans = maxFans
        self.padding_rpm_connected = [s.PAD]*maxFans
        self.padding_rpm_disconnected = [s.RIP]*maxFans
        self.padding_dc_connected = [s.PAD]*maxFans
        self.padding_dc_disconnected = [s.RIP]*maxFans

        # Index:
        self.index = index

        # Initialize variable attributes .......................................
        self.status = status
        self.statusLock = threading.Lock()

        self.version = version
        self.versionLock = threading.Lock()

        # Communications-specific ..............................................

        # IP address:
        self.ip = ip
        self.ipLock = threading.Lock()

        # Port numbers:
        self.misoP = misoP
        self.mosiP = mosiP
        self.portLock = threading.Lock()

        # Sockets:
        self.misoS = misoS
        self.mosiS = mosiS
        self.socketLock = threading.Lock()

        # MOSI index:
        self.mosiIndex = 0
        self.mosiIndexLock = threading.Lock()

        # MISO index:
        self.misoIndex = 0
        self.misoIndexLock = threading.Lock()

        # Data index:
        self.dataIndex = 0
        self.dataIndexLock = threading.Lock()

        # Drop index:
        self.dropIndex = 0
        self.dropIndexLock = threading.Lock()

        # Initialize multithreading attributes .................................

        # Threading lock:
        self.lock = threading.Lock()

        # Queues:
        self.mosiQueue = queue.Queue(2)
        self.misoQueue = queue.Queue(misoQueueSize)

        # Buffers: FIXME
        self.misoBuffer = None
        self.mosiBuffer = None

        # Handler thread:
        self.thread = threading.Thread(
            target = routine,
            args = routineArgs + (self,)
            )
        self.thread.setDaemon(True)

        # End __init__ =========================================================

    def start(self): # =========================================================
        # ABOUT: Start Slave thread.

        self.thread.start()

        # End start ============================================================

    # GETTERS FOR CONSTANT ATTRIBUTES ##########################################
    def getName(self): #========================================================
        # ABOUT: Getter for this Slave's name.
        # NOTE: read-only. No need for locks.
        return self.name

    def getMAC(self): # ========================================================
        # ABOUT: Getter for this Slave's MAC address.
        # NOTE: Since this attribute is "read only," lock usage is neglected.
        return self.mac

        # End getMAC ===========================================================

    def getIndex(self): # ======================================================
        # ABOUT: Get this Slave's index.

        return self.index

        # End getIndex =========================================================

    def getFans(self): # =======================================================
        # ABOUT: Get this Slave's fans.

        return self.fans

        # End getFans ==========================================================

    def getStatus(self): # =====================================================
        # ABOUT: Getter for status. (Uses locks for thread-safety.)

        try:
            self.statusLock.acquire()

            # Use placeholder to return value after releasing lock:
            placeholder = self.status

            # Notice lock will be released by finally clause
            return placeholder

        finally:
            self.statusLock.release()

        # End getStatus ========================================================

    def setStatus(self, # ======================================================
        newStatus,
        newIP = None,
        newMISOP = None,
        newMOSIP = None,
        newVersion = None,
        lock = True):
        # ABOUT: Setter for status. (Uses full lock for thread-safety.)
        # NOTE: This method will modify all attributes that correspond to the
        # status change in question. Furthermore, this method is the only
        # external mean by which to change the IP address, and port numbers:
        # this is to say that the only way to change these parameters is to
        # reset a connection.
        # PARAMETERS:
        # - newStatus: int, must represent valid status code.
        # - newIP: str, new IP address. Required to set to AVAILABLE and KNOWN
        #   only (will be ignored otherwise). Defaults to None.
        # - newMISOP and newMOSIP: ints, new MISO and MOSI port numbers, res-
        #   pectively. Required to set to AVAILABLE and KNOWN. (will be igno-
        #   red otherwise). Default to None.
        # - newVersion: str, code of the MkII-S version running in the MCU
        # - lock: bool, whether to acquire Slave lock (set to False if caller
        #   already has lock. OTHERWISE DEADLOCK WILL ENSUE!
        # RAISES:
        # - TypeError, ValueError, if newStatus is not int status code or argu-
        #   ments are invalid.
        # - Queue.Full if update queue is full.

        # Validate input -------------------------------------------------------
        if newStatus not in \
            (CONNECTED, KNOWN, DISCONNECTED, AVAILABLE, BOOTLOADER):
            raise ValueError("Argument 'newStatus' must be valid status code "\
                "(not {})".format(newStatus))

        try:
            # Acquire locks:
            if lock:
                self.acquire()

            # Check for redundancy ---------------------------------------------
            if self.status == newStatus:
                # Skip if status change is redundant.
                return

            # NOTE: At this point, whatever newStatus is, we know self.status is
            # not.
            elif newStatus == DISCONNECTED:
                # When DISCONNECTED, remove connection-specific attributes.
                #self._setPorts(None, None)
                #self._setIP(None)
                self.resetIndices()
                self._emptyMISOBuffer()

            elif newStatus in (AVAILABLE, KNOWN):
                # Reset indices and update IP address and port numbers:

                # Check for missing arguments:
                if newIP == None and self.ip == None:
                    raise ValueError("Missing 'newIP' argument")
                elif newMISOP == None and self.misoP == None:
                    raise ValueError("Missing 'newMISOP' argument")
                elif newMOSIP == None and self.mosiP == None:
                    raise ValueError("Missing 'newMOSIP' argument")

                if newIP != None:
                    self._setIP(newIP)
                if newMISOP != None:
                    self._setPorts(newMISOP, newMOSIP)
                    # NOTE: Argument validation will be performed here

                if newVersion != None:
                    if type(newVersion) is not str:
                        raise TypeError("Argument 'newVersion' must be of type"\
                            "str, not {}".format(type(newVersion)))
                    else:
                        self.version = newVersion

                # Reset indices:
                self.resetIndices()

            elif newStatus == CONNECTED:
                # When CONNECTED, do not reset indices:
                pass

            elif newStatus == BOOTLOADER:
                pass

            else:
                raise ValueError("SUPPOSEDLY IMPOSSIBLE ERROR: COULD NOT "\
                    "CLASSIFY newStatus! (Value: {})".format(newStatus))

            # Update status ----------------------------------------------------
            self.status = newStatus

        finally:
            if lock:
                self.release()

        # End setStatus ========================================================

    def getVersion(self): # ====================================================
        # ABOUT: Get version of this Slave.
        # RETURNS:
        # - str, may be empty("").
        # NOTE: Thread-safe (blocks)

        try:
            self.versionLock.acquire()

            # Use placeholder to return value after releasing lock:
            placeholder = self.version

            # Lock will be released by finally clause
            return placeholder

        finally:
            self.versionLock.release()

        # End getVersion =======================================================

    def setVersion(self, newVersion): # ========================================
        # ABOUT: Set version.
        # PARAMETERS:
        # - newVersion: str.
        # NOTE: Thread-safe (blocks)

        # Validate input:
        if type(newVersion) is not str:
            raise TypeError("Argument 'newVersion' must be str, "\
                "not {}".\
                format(type(newVersion)))
        try:
            self.versionLock.acquire()

            self.version = newVersion

        finally:
            self.versionLock.release()

        # End setVersion =======================================================

    # METHODS FOR NETWORKING ATTRIBUTES ########################################

    def acquireSocketLock(self, block = True): # ===============================
        # ABOUT: Acquire socket lock to use misoSocket() or mosiSocket().
        # Imitates threading.Lock.acquire.
        # PARAMETERS:
        # - block: bool, whether to block caller to acquire lock.
        #   Defaults to True.
        # RETURN:
        #   bool, whether lock was successfully acquired.

        if block:
            return self.socketLock.acquire()
        else:
            return self.socketLock.acquire(False)

        # End aquireSocketLock =================================================

    def releaseSocketLock(self): # =============================================
        # ABOUT: Release socket lock. Imitates threading.Lock.release.
        # RAISES:
        # - ThreadError if lock is already released.

        self.socketLock.release()

        # End releaseSocketLock ================================================

    def _misoSocket(self): # ===================================================
        # ABOUT: Access MISO socket.
        # NOTE: ACQUIRE SOCKET LOCK BEFORE USING.
        # NOTE: RETURNS DIRECT REFERENCE TO SOCKET OBJECT. ONLY ONE SOCKET MAY
        # BE ACCESSED AT A TIME.

        return self.misoS

        # End _misoSocket ======================================================

    def _mosiSocket(self): # ===================================================
        # ABOUT: Access MOSI socket.
        # NOTE: ACQUIRE SOCKET LOCK BEFORE USING.
        # NOTE: RETURNS DIRECT REFERENCE TO SOCKET OBJECT. ONLY ONE SOCKET MAY
        # BE ACCESSED AT A TIME.

        return self.mosiS

        # end _mosiSocket ======================================================

    def setSockets(self, newMISOS, newMOSIS): # ================================
        # ABOUT: Set socket objects.
        # NOTE: THIS METHOD ACQUIRES THE SOCKET LOCK.
        # WARNING: THIS METHOD ASSUMES THE CALLER HAS ALREADY PROPERLY SHUTDOWN
        # THE PAST SOCKETS, IF ANY.
        # RAISES:
        # - TypeError if arguments are not of type socket.socket .

        try:
            self.socketLock.acquire()

            # Validate arguments:
            if type(newMISOS) is not socket.socket:
                raise TypeError("Argument 'newMISOS' must be of type "\
                    "socket.socket, not {}".\
                    format(type(newMISOS)))
            elif type(newMOSIS) is not socket.socket:
                raise TypeError("Argument 'newMOSIS' must be of type"\
                    "socket.socket, not {}".\
                    format(type(newMOSIS)))

            # Assign new values:
            self.misoS = newMISOS
            self.mosiS = newMOSIS

            # Done
            return

        finally:
            self.socketLock.release()

        # End setSockets =======================================================

    def getMISOIndex(self): # ==================================================
        # ABOUT: Get current MISO index value.
        # RETURNS: int, current MISO index value.
        # NOTE: Thread-safe (blocks)

        try:
            self.misoIndexLock.acquire()

            # Use placeholder to return value after releasing lock:
            placeholder = self.misoIndex

            # Notice finally clause will release lock
            return placeholder

        finally:
            self.misoIndexLock.release()

        # End getMISOIndex =====================================================

    def incrementMISOIndex(self): # ============================================
        # ABOUT: Increment MISO index value (by 1).
        # NOTE: Blocks for thread-safety.

        try:
            self.misoIndexLock.acquire()

            self.misoIndex += 1

        finally:
            self.misoIndexLock.release()

        # End incrementMISOIndex ===============================================

    def setMISOIndex(self, newIndex): # ========================================
        # ABOUT: Set MISO index to a given value.
        # PARAMETERS:
        # - newIndex: int, nonnegative new index value that may be zero.
        # NOTE: Thread-safe (blocks)

        # Validate input:
        if type(newIndex) is not int:
            raise TypeError("Argument 'newIndex' must be of type int, not {}".\
                format(type(newIndex)))

        try:
            self.misoIndexLock.acquire()

            self.misoIndex = newIndex

        finally:
            self.misoIndexLock.release()

        # End setMISOIndex =====================================================

    def getDropIndex(self): # ==================================================
        # ABOUT: Get current Drop index value.
        # RETURNS: int, current Drop index value.
        # NOTE: Thread-safe (blocks)

        try:
            self.dropIndexLock.acquire()

            # Use placeholder to return value after releasing lock:
            placeholder = self.dropIndex

            # Notice finally clause will release lock
            return placeholder

        finally:
            self.dropIndexLock.release()

        # End getDropIndex =====================================================

    def incrementDropIndex(self): # ============================================
        # ABOUT: Increment Drop index value (by 1).
        # NOTE: Blocks for thread-safety.

        try:
            self.dropIndexLock.acquire()

            self.dropIndex += 1

        finally:
            self.dropIndexLock.release()

        # End incrementDropIndex ===============================================

    def setDropIndex(self, newIndex): # ========================================
        # ABOUT: Set Drop index to a given value.
        # PARAMETERS:
        # - newIndex: int, nonnegative new index value that may be zero.
        # NOTE: Thread-safe (blocks)

        # Validate input:
        if type(newIndex) is not int:
            raise TypeError("Argument 'newIndex' must be of type int, not {}".\
                format(type(newIndex)))

        try:
            self.dropIndexLock.acquire()

            self.dropIndex = newIndex

        finally:
            self.dropIndexLock.release()

        # End setDropIndex =====================================================


    def getDataIndex(self): # ==================================================
        # ABOUT: Get current data index value.
        # RETURNS: int, current data index value.
        # NOTE: Thread-safe (blocks)

        try:
            self.dataIndexLock.acquire()

            # Use placeholder to return value after releasing lock:
            placeholder = self.dataIndex

            # Notice finally clause will release lock
            return placeholder

        finally:
            self.dataIndexLock.release()

        # End getDataIndex =====================================================

    def incrementDataIndex(self): # ============================================
        # ABOUT: Increment data index value (by 1).
        # NOTE: Blocks for thread-safety.

        try:
            self.misoDataLock.acquire()

            self.dataIndex += 1

        finally:
            self.dataIndexLock.release()

        # End incrementDataIndex ===============================================

    def setDataIndex(self, newIndex): # ========================================
        # ABOUT: Set data index to a given value.
        # PARAMETERS:
        # - newIndex: int, nonnegative new index value that may be zero.
        # NOTE: Thread-safe (blocks)

        # Validate input:
        if type(newIndex) is not int:
            raise TypeError("Argument 'newIndex' must be of type int, not {}"\
                " ({})".format(type(newIndex), newIndex))

        try:
            self.dataIndexLock.acquire()

            self.dataIndex = newIndex

        finally:
            self.dataIndexLock.release()

        # End setDataIndex =====================================================
    def getMOSIIndex(self): # ==================================================
        # ABOUT: Get current MOSI index value.
        # RETURNS: int, current MOSI index value.
        # NOTE: Thread-safe (blocks)

        try:
            self.mosiIndexLock.acquire()

            # Use placeholder to return value after releasing lock:
            placeholder = self.mosiIndex

            # Notice finally clause will release lock
            return placeholder

        finally:
            self.mosiIndexLock.release()

        # End getMOSIIndex =====================================================

    def setMOSIIndex(self, newIndex): # ========================================
        # ABOUT: Set MOSI index to a given value.
        # PARAMETERS:
        # - newIndex: int, nonnegative new index value that may be zero.
        # NOTE: Thread-safe (blocks)

        # Validate input:
        if type(newIndex) is not int:
            raise TypeError("Argument 'newIndex' must be of type int, not {}".\
                format(type(newIndex)))

        try:
            self.mosiIndexLock.acquire()

            self.mosiIndex = newIndex

        finally:
            self.mosiIndexLock.release()

        # End setMOSIIndex =====================================================

    def incrementMOSIIndex(self): # ============================================
        # ABOUT: Increment MOSI index value (by 1).
        # NOTE: Blocks for thread-safety.

        try:
            self.mosiIndexLock.acquire()

            self.mosiIndex += 1

        finally:
            self.mosiIndexLock.release()

        # End incrementMOSIIndex ===============================================

    def resetIndices(self): # ==================================================
        # ABOUT: Reset both MOSIIndex and MISOIndex to 0.
        # NOTE: Blocks for thread-safety.

        try:
            self.misoIndexLock.acquire()
            self.mosiIndexLock.acquire()
            self.dataIndexLock.acquire()
            self.dropIndexLock.acquire()

            self.misoIndex = 0
            self.mosiIndex = 0
            self.dataIndex = 0
            self.dropIndex = 0

        finally:
            self.misoIndexLock.release()
            self.mosiIndexLock.release()
            self.dataIndexLock.release()
            self.dropIndexLock.release()

        # End resetIndices =====================================================

    def getMOSIPort(self): # ===================================================
        # ABOUT: Get this Slave's MOSI port number.
        # NOTE: Thread-safe (blocks)

        try:
            self.portLock.acquire()

            # Use placeholder to return value after releasing lock:
            placeholder = self.mosiP

            # Notice lock will be released in finally clause
            return placeholder

        finally:
            self.portLock.release()

        # End getMOSIPort ======================================================

    def getMISOPort(self): # ===================================================
        # ABOUT: Get this Slave's MISO port number.
        # NOTE: Thread-safe (blocks)

        try:
            self.portLock.acquire()

            # Use placeholder to return value after releasing lock:
            placeholder = self.misoP

            # Notice lock will be released in finally clause
            return placeholder

        finally:
            self.portLock.release()

        # End getMISOPort ======================================================

    # PUBLIC INTERFACE #########################################################

    def acquire(self, block = True): # =========================================
        # ABOUT: Try to acquire Slave's lock.
        # Imitates threading.Thread.acquire()
        # PARAMETER:
        #  block: bool, whether to block calling thread while waiting.
        # RETURNS:


        if block:
            return self.lock.acquire()
        else:
            return self.lock.acquire(False)

        # End lock =============================================================

    def release(self): # =======================================================
        # ABOUT: Try to release Slave's lock.
        # Imitates threading.Thread.release()
        # RAISES:
        # - ThreadError if lock is already released.

        self.lock.release()

        # End release ==========================================================

    def setMOSI(self, command, block = True): # ================================
        # ABOUT: Add a command (str) to this Slave's MOSI Queue.
        if self.mosiBuffer is not None:
            # TODO: count drop
            pass
        self.mosiBuffer = command
        # End setMOSI ==========================================================

    def getMOSI(self, block = False): # ========================================
        # ABOUT: Try to get a command (as a string) from the Slave's MOSI Queue,
        # if any is available.
        # PARAMETERS:
        # - block: bool, whether to block while waiting for queue.
        # RETURNS:
        # - str representing command to be sent or None if the Queue is empty
        #   and parameter block is set to False.
        value = self.mosiBuffer
        self.mosiBuffer = None
        return value

        # End getMOSI ==========================================================

    def getIP(self): # =========================================================
        # ABOUT: Get Slave's IP address, if any.
        # RETURNS:
        # - str if IP address currently exists, None otherwise.
        # NOTE: Blocks for thread-safety.

        try:
            self.ipLock.acquire()

            # Use placeholder to return value after releasing lock:
            placeholder = self.ip

            # Notice lock will be released by finally clause
            return placeholder

        finally:
            self.ipLock.release()

        # End getIP ============================================================

    def setMISO(self, update, block = True): # ================================
        # Add an update to the Slave's misoQueue
        if self.misoBuffer is not None:
            # TODO: count drop
            pass
        self.misoBuffer = update

        # End setMISO ==========================================================


    def getMISO(self, block = False): # ========================================
        # ABOUT: Try to get an update from this Slave's misoQueue.
        if self.misoBuffer is not None:
            value = self.misoBuffer
            misoBuffer = None
            return value
        else:
            return (self.padding_rpm_connected, self.padding_dc_connected) if \
                self.status is CONNECTED else \
                    (self.padding_rpm_disconnected,
                self.padding_dc_disconnected)
        # End getUpdate ========================================================

    # PRIVATE AUXILIARY METHODS ################################################

    def _emptyMISOBuffer(self): # ==============================================
        # ABOUT: Empty the buffer of the MISO socket, if any, to prevent
        # obsolete messages. The MISO data buffer is also reset.

        if self.misoS is not None:
            timeout = self.misoS.gettimeout()
            self.misoS.settimeout(0.0)

            try:
                while(True):
                    self.misoS.recv(1024)
            except socket.error:
                pass

            self.misoS.settimeout(timeout)
            self.misoBuffer = None

        return

        # End _emptyMISOBuffer =================================================

    def _setIP(self, newIP): # ==================================================
        # ABOUT: Set new IP address.
        # PARAMETER:
        # - newIP: str or None, new IP address to set.
        # NOTE: THIS METHOD IS MEANT AS AN AUXILIARY PRIVATE METHOD AND AS SUCH
        # IS NOT INHERENTLY THREAD-SAFE (BESIDES W/ getIP()).
        try:
            self.ipLock.acquire()
            # Validate input:
            if type(newIP) in (str, type(None)):

                self.ip = newIP

                # Done
                return

            else:
                raise TypeError("Argument 'newIP' must be str or None, "\
                    "not {}".\
                    format(type(newIP)))

        finally:
            self.ipLock.release()

        # End _setIP ===========================================================

    def _setPorts(self, newMISOP, newMOSIP): # =================================
        # ABOUT: Set new MISO and MOSI port numbers.
        # PARAMETERS:
        # - newMISOP, newMOSIP: ints or None (both), port numbers to set.
        # NOTE: THIS METHOD IS MEANT AS AN AUXILIARY PRIVATE METHOD AND AS SUCH
        # IS NOT INHERENTLY THREAD-SAFE.

        try:
            self.portLock.acquire()

            # Validate input:
            if type(newMISOP) in (int, type(None)) and \
                type(newMISOP) == type(newMOSIP):
                # Both arguments have valid and equal types. Now check values:

                if newMISOP == None:
                    # Both arguments are None (valid)
                    pass
                # If they are integers, check their values:
                elif newMISOP <= 0:
                    raise TypeError("Argument 'newMISOP' must be > 0 ({})"\
                        "(MOSI: {})".\
                        format(newMISOP, newMOSIP))
                elif newMOSIP <= 0:
                    raise TypeError("Argument 'newMOSIP' must be > 0 ({})"\
                        "(MISO: {})".\
                        format(newMOSIP, newMISOP))
                else:
                    pass

                # Tests passed. Assign values:

                self.misoP = newMISOP
                self.mosiP = newMOSIP

                # Done
                return

            else:
                # Bad types. Report to user:
                raise TypeError("Bad types. Arguments 'newMISOP' and "\
                    "'newMOSIP' "\
                    "must have valid and equal types. "\
                    "(Here MISO: {} and MOSI: {})".\
                    format(type(newMISOP), type(newMOSIP)))

        finally:
            self.portLock.release()
        # End _setPorts ========================================================



