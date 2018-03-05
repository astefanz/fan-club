################################################################################
## Project: Fan Club Mark II "Master" ## File: Communicator.py                ##
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
This module handles low-level socket communications w/ Slave units.

"""
################################################################################

## DEPENDENCIES ################################################################

import socket     # Networking
import threading  # Multitasking
import thread     # thread.error
import time       # Timing
import Queue
import sys        # Exception handling
import traceback  # More exception handling
import random # Random names, boy

import FCInterface
import Profiler    # Custom representation of wind tunnel
import Slave
import Fan
import names


VERSION = "Asymmetrical 1"

## CLASS DEFINITION ############################################################

class Communicator:

    def __init__(self, profiler, interface, bcupdate, ltupdate):
        #   \-----------------------------------------------------------/
        #   Interface methods
        # ABOUT: Constructor for class Communicator.

        try:


            # INITIALIZE DATA MEMBERS ==============================================

            # Output queues:
            self.mainQueue = Queue.Queue(profiler.mainQueueSize)

            self.printM("Initializing Communicator instance")

            # Interface:
            self.interface = interface
            self.bcupdate = bcupdate
            self.ltupdate = ltupdate

            # Profiler:
            self.profiler = profiler

            # Wind tunnel:
            self.slaves = profiler.slaves
            self.slavesLock = profiler.slavesLock

            # Communications:
            self.broadcastPeriodS = profiler.broadcastPeriodS
            self.periodMS = profiler.periodMS
            self.broadcastPort = profiler.broadcastPort
            self.password = profiler.passcode

            # Create a temporary socket to obtain Master's IP address for reference:
            temp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            temp.connect(('192.0.0.8', 1027))
            self.hostIP = temp.getsockname()[0]
            temp.close()

            self.printM("\tHost IP: {}".format(self.hostIP))

            # INITIALIZE MASTER SOCKETS ============================================

            # INITIALIZE LISTENER SOCKET -------------------------------------------

            # Create listener socket:
            self.listenerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


            # Configure socket as "reusable" (in case of improper closure): 
            self.listenerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind socket to "nothing" (Broadcast on all interfaces and let system 
            # assign port number):
            self.listenerSocket.bind(("", 0))

            self.printM("\tlistenerSocket initialized on " + \
                str(self.listenerSocket.getsockname()))

            self.listenerPort = self.listenerSocket.getsockname()[1]

            # INITIALIZE BROADCAST SOCKET ------------------------------------------

            # Create broadcast socket:
            self.broadcastSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Configure socket as "reusable" (in case of improper closure): 
            self.broadcastSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Configure socket for broadcasting:
            self.broadcastSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            # Bind socket to "nothing" (Broadcast on all interfaces and let system 
            # assign port number):
            self.broadcastSocket.bind(("192.168.1.129", 0))

            self.broadcastSocketPort = self.broadcastSocket.getsockname()[1]

            self.printM("\tbroadcastSocket initialized on " + \
                str(self.broadcastSocket.getsockname()))


            # INITIALIZE SPECIFIC SOCKET ------------------------------------------
                # ABOUT: The sniper socket is to be used to contact known Slaves to
                # secure a connection. See self._specificBroadcast() Method.

            # Create socket:
            self.specificSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Configure socket for broadcasting:
            self.specificSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            # Configure socket as "reusable" (in case of improper closure): 
            self.specificSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind socket to "nothing":
            self.specificSocket.bind(("", 0))

            self.printM("\tspecificSocket initialized on " + \
                str(self.specificSocket.getsockname()))


            # SET UP MASTER THREADS ================================================

            # INITIALIZE BROADCAST THREAD ------------------------------------------

            # Configure sentinel value for broadcasts:
            self.broadcastSwitch = True
                # ABOUT: UDP broadcasts will be sent only when this switch is True
            self.broadcastSwitchLock = threading.Lock() # for thread-safe access

            self.broadcastThread = threading.Thread(
                name = "FCMkII_broadcast",
                target = self._broadcastRoutine,
                args = ["00000000|{}|{}".format(self.password, 
                            self.listenerPort), 
                        self.broadcastPeriodS]
                )

            # Set thread as daemon (background task for automatic closure):
                # NOTE: A better approach, to be taken in future versions, is to use
                # events and/or signals to trigger cleanup measures.
            self.broadcastThread.setDaemon(True)

            # INITIALIZE LISTENER THREAD -------------------------------------------

            self.listenerThread =threading.Thread(
                name = "FCMkII_listener",
                target = self._listenerRoutine)

            # Set thread as daemon (background task for automatic closure):
                # NOTE: A better approach, to be taken in future versions, is to use
                # events and/or signals to trigger cleanup measures.
            self.listenerThread.setDaemon(True)

            # START MASTER THREADS =================================================

            self.listenerThread.start()
            self.broadcastThread.start()

            # START KNOWN SLAVE THREADS ============================================

            for mac in self.slaves:
                #self.printM("\tInitializing {}".format(mac), "G")

                self.slaves[mac].setStatus(Slave.DISCONNECTED)
                self.slaves[mac].thread = threading.Thread( 
                    target = self._slaveRoutine,
                    args = [mac])
                self.slaves[mac].thread.setDaemon(True)
                self.slaves[mac].thread.start()

            self.printM("Communicator ready", "G")

        except Exception as e: # Print uncaught exceptions
            self.printM("UNCAUGHT EXCEPTION: \"{}\"".\
                format(traceback.format_exc()), "E")

        # # END __init__() # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    # # THREAD ROUTINES # # # # # # # # # # # # # # # # # # # # # # # # # # # #  

    def _broadcastRoutine(self, broadcastMessage, broadcastPeriod): # ==========
        """ ABOUT: This method is meant to run inside a Communicator instance's
            broadcastThread. 
        """
        try: # Catch any exception for printing (have no stdout w/ GUI!)

            broadcastSocketPortCopy = self.broadcastSocketPort # Thread safety

            self.printM("[BT] Broadcast thread started w/ period of {} "\
                "second(s)"\
                .format(broadcastPeriod), "G")

            count = 0

            while(True):

                # Increment counter:
                count += 1

                # Wait designated period:
                time.sleep(broadcastPeriod)

                self.broadcastSwitchLock.acquire()
                try:
                    # Send broadcast only if self.broadcastSwitch is True:
                    if self.broadcastSwitch:
                        # Broadcast message:
                        self.broadcastSocket.sendto(broadcastMessage, 
                            ("<broadcast>", 65000))

                    # Blink broadcast display:
                    self.bcupdate()

                finally:
                    # Guarantee lock release:
                    self.broadcastSwitchLock.release()

        except Exception as e:
            self.printM("[BT] UNCAUGHT EXCEPTION: \"{}\"".\
                format(traceback.format_exc()), "E")

        self.bcupdate("R")

        # End _broadcastRoutine ================================================

    def _listenerRoutine(self): # ==============================================
        """ ABOUT: This method is meant to run within an instance's listener-
            Thread. It will wait indefinitely for messages to be received by
            the listenerSocket and respond accordingly.
        """

        try:    

            self.printM("[LT] Listener thread started. Waiting.", "G")

            while(True):
                self.ltupdate()

                # Wait for a message to arrive:
                messageReceived, senderAddress = self.listenerSocket.recvfrom(256)

                self.ltupdate("B")
                """ NOTE: The message received from Slave, at this point, should ha-
                    ve the following form:

                        000000000|PASSWORD|SV:MA:CA:DD:RE:SS|SMISO|SMOSI| 

                    Where SMISO and SMOSI are the Slave's MISO and MOSI port numb-
                    ers, respectively. Notice separator.
                """

                messageSplitted = messageReceived.split("|")
                    # NOTE: messageSplitted is a list of strings, each of which is
                    # expected to contain a string as defined in the comment above.

                # Validate message -------------------------------------------------

                try:

                    # Verify password:
                    if messageSplitted[1] != self.password:
                        raise ValueError("Wrong password received ({})".\
                            format(messageSplitted[1]))

                    # Attempt conversion into corresponding containers:
                    misoPort = int(messageSplitted[3])
                    mosiPort = int(messageSplitted[4])
                    mac = messageSplitted[2]
                    # A ValueError will be raised if invalid port numbers are given
                    # and an IndexError will be raised if the given message yields 
                    # less than three strings when splitted.

                    # DEBUG DEACTV:
                    """
                    self.printL("Parsed:\
                                \n\t\t Password: {}\
                                \n\t\t MAC: {}\
                                \n\t\t MMISO: {}\
                                \n\t\t MMOSI: {}\n".\
                                format(
                                messageSplitted[1],
                                messageSplitted[2],
                                messageSplitted[3],
                                messageSplitted[4]))
                    """

                    # Verify converted values:
                    if (misoPort <= 0 or misoPort > 65535):
                        # Raise a ValueError if a port number is invalid:
                        raise ValueError("Bad SMISO ({}). Need [1, 65535]".\
                            format(miso))

                    if (mosiPort <= 0 or mosiPort > 65535):
                        # Raise a ValueError if a port number is invalid:
                        raise ValueError("Bad SMOSI ({}). Need [1, 65535]".\
                            format(mosi))

                    if (len(mac) != 17):
                        # Raise a ValueError if the given MAC address is not 17
                        # characters long.
                        raise ValueError("MAC ({}) not 17 chars ({})")


                except (ValueError, IndexError) as e:

                    # If the given message is invalid, discard it and move on:

                    self.printM("[LT ]Error: \"{}\"\n\tObtained when parsing \"\
                        {}\" from {}. (Message discarded)"\
                    .format(e, messageReceived, senderAddress), "W")

                    # Move on:
                    continue

                # Check Slave against self.slaves and respond accordingly ----------
                    # (Message validation completed successfully by this point)
                try:
                    # (NOTE: try/finally clause guarantees lock release)

                    # Acquire lock:
                    self.slavesLock.acquire(False)

                    # Check if the Slave is known:
                    if(mac in self.slaves):

                        # If the MAC address is in the Slave dictionary, check its re-
                        # corded status and proceed accordingly:
                        self.slaves[mac].lock.acquire()
                        try:
                            # Retrieve status for consecutive uses:
                            status = self.slaves[mac].status 

                            if (status == Slave.KNOWN or
                                status == Slave.DISCONNECTED):

                                # ABOUT: 
                                #
                                # - KNOWN Slaves have been approved by the user and
                                #   should be connected to automatically.
                                #
                                # - DISCONNECTED Slaves were previously connected to
                                #   and later anomalously disconnected. Since have
                                #   been chosen by the user, they should be recon-
                                #   nected to automatically.

                                # Update status and networking information:
                                self.slaves[mac].setIP(senderAddress[0])
                                self.slaves[mac].misoP = misoPort
                                self.slaves[mac].mosiP = mosiPort
                                self.slaves[mac].setStatus(Slave.KNOWN)

                        finally:

                            # Guarantee release of Slave-specific lock:
                            try:
                                self.slaves[mac].lock.release()
                            except thread.error:
                                pass



                    else:

                        # If the MAC address is not recorded, list this board as A-
                        # VAILABLE and move on. The user may choose to add it later:

                        # NOTE: Slaves that are not connected will have either port
                        # numbers or None as their "miso" and "mosi" attributes.
                        # When a connection is secured, these port numbers will be
                        # replaced by UDP sockets CONNECTED to said port numbers --
                        # notice: CONNECTED, not BINDED.

                        # Create a new Slave instance and store it:

                        self.slaves[mac] = Slave.Slave(
                            name = random.choice(names.coolNames),
                            mac = mac,              # MAC address
                            status = Slave.AVAILABLE,   # Status
                            interface = self.interface,
                            activeFans = 21,
                            maxFans = 21,
                            ip = senderAddress[0],  # IP address
                            misoP = misoPort,   # Master in/Slave out port number
                            mosiP = mosiPort        # Slave in/Master out port number
                            )

                        # Add slave thread:
                        self.slaves[mac].thread = threading.Thread( 
                            target = self._slaveRoutine,
                            args = [mac])
                        self.slaves[mac].thread.setDaemon(True)
                        self.slaves[mac].thread.start()


                finally:

                    # Guarantee release of general Slave lock:
                    self.slavesLock.acquire(False)
                        #                     ^ Non-blocking
                        #
                        # Note: if the lock was released within the "try" clause
                        # then this statement will prevent a threading exception
                        # when an attempt to release an unlocked lock is made.
                    
                    self.slavesLock.release()

        except Exception as e: # Print uncaught exceptions
            self.printM("[LT] UNCAUGHT EXCEPTION: \"{}\"".\
                format(traceback.format_exc()), "E")

        self.ltupdate("R")
                
        # End _listenerRoutine =================================================

    def _slaveRoutine(self, targetMAC): # # # # # # # # # # # # # # # # # # # # 
        # ABOUT: This method is meant to run on a Slave's communication-handling
        # thread. It handles sending and receiving messages through its MISO and
        # MOSI sockets, at a pace dictated by the Communicator instance's given
        # period. 
        # PARAMETERS:
        # - targetMAC: String, MAC address of the Slave handled by
        #   this thread.
        # - mosiMasterPort: Int, port number of the MOSI socket in the particular 
        #   connection handled by this thread. If the MOSI socket used by the 
        #   Slave w/ targetMAC changes, this thread is to be replaced and will end 
        #   automatically.
        #
        # NOTE: This current version is expected to run as daemon.

        try:

            # Setup: ===========================================================
            self.printM("[{}] Slave thread started".\
                format(self.slaves[targetMAC].mac), "G")

            # Get reference to Slave: ------------------------------------------
            slave = self.slaves[targetMAC]

            # Set up sockets: --------------------------------------------------
            # MISO:
            slave.misoS = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            slave.misoS.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            slave.misoS.settimeout(self.profiler.masterTimeoutS)
                # The communications period is defined in milliseconds. The 
                # socket timeout should be one-fifth of said period, and this
                # method expects a value in seconds.
            slave.misoS.bind(('', 0))

            # MOSI:
            slave.mosiS = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            slave.mosiS.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            slave.mosiS.settimeout(self.profiler.masterTimeoutS)
                # The communications period is defined in milliseconds. The 
                # socket timeout should be one-fifth of said period, and this
                # method expects a value in seconds.
            slave.mosiS.bind(('', 0))

            self.printM("[{}] Sockets set up successfully: \
             \n\t\tMMISO: {}\n\t\tMMOSI:{}".\
                format(slave.mac,
                    slave.misoS.getsockname(), slave.mosiS.getsockname()))

            # HSK message: -----------------------------------------------------

            MHSK = "MHSK|{},{},{},S~{},{},{},{},{},{},{},{},{}".format(
                        slave.misoS.getsockname()[1], 
                        slave.mosiS.getsockname()[1], 
                        self.profiler.periodMS,
                        self.profiler.fanMode,
                        self.profiler.targetRelation[0],
                        self.profiler.targetRelation[1],
                        self.slaves[targetMAC].activeFans,
                        self.profiler.counterCounts,
                        self.profiler.pulsesPerRotation,
                        self.profiler.maxRPM,
                        self.profiler.minRPM,
                        self.profiler.minDC)

            # Set up placeholders and sentinels: -------------------------------
            slave.setExchange(0)
            timeouts = 0
            message = None

            # Slave loop: ======================================================
            while(True):

                time.sleep(self.profiler.interimS)

                # Acquire:
                slave.lock.acquire()
                # DEBUG DEACTV
                ## print "Slave lock acquired"

                try:

                    # Act according to Slave's state: 
                    if slave.status == Slave.KNOWN: # = = = = = = = = = = = = = 

                        # If the Slave is known, try to secure a connection:
                        # print "Attempting handshake"

                        # Check for signs of life w/ HSK message:
                        self._send(MHSK, slave, 1, True)

                        # Try to receive reply:
                        reply = self._receive(slave)

                        # Check reply:
                        if reply != None and reply[1] == "SHSK":
                            # print "Processed reply: {}".format(reply), "G"
                            # print "Handshake confirmed"

                            # Mark as CONNECTED and get to work:
                            slave.setStatus(Slave.CONNECTED)

                        else:
                            # If there was an error, restart attempt:
                            # print
                            #   "Missed handshake. Retrying."
                            # Set Slave to disconnected:
                            slave.setStatus(Slave.DISCONNECTED) 
                                # NOTE: This call also resets exchange index.


                    elif slave.status > 0: # = = = = = = = = = = = = = = = = = = 
                        # If the Slave's state is positive, it is online and 
                        # there is a connection to maintain.

                        # A positive state indicates this Slave is online and 
                        # its connection need be maintained.

                        #DEBUG DEACTV
                        ## print "[On positive state]"

                        # Check queue for message:
                        try:  
                            command = slave.mosiQueue.get_nowait()
                            slave.mosiQueue.task_done()
                            message = "MSTD|" + command

                        except Queue.Empty:
                            # Nothing to send:
                            message = None
                            pass

                        # Send message, if any:
                        if message != None:
                            self._send(message, slave, 4)

                            # DEBUG: 
                            # print "Sent: {}".format(message)

                        # Get reply:
                        reply = self._receive(slave)

                        # Check reply: -----------------------------------------
                        if reply != None:
                            # print "Processed reply: {}".format(reply)

                            # Restore timeout counter after success:
                            timeouts = 0

                            # Check if there are DCs and RPMs:
                            if len(reply) > 2:
                                # Update RPMs and DCs:
                                dcs = reply[-1].split(',')
                                rpms = reply[-2].split(',')

                                for index in range(slave.activeFans):
                                    slave.setDC(float(dcs[index])*100, index)
                                    slave.setRPM(rpms[index], index)

                        else:
                            timeouts += 1

                            if message != None:
                                # If a message was sent and no reply was 
                                # received, resend it:
                                # print "Timed out. Resending"
                                # Resend message:
                                self._send(message, slave, 4)
                                # Increment timeout counter:

                            # Check timeout counter: - - - - - - - - - - - - - -
                            if timeouts < self.profiler.maxTimeouts:
                                # If there have not been enough timeouts to con-
                                # sider the connection compromised, continue.
                                # print "Reply missed ({}/{})".
                                #   format(timeouts, 
                                #       self.profiler.maxTimeouts)

                                # Restart loop:
                                continue;

                            else:
                                self.printM("[{}] Slave timed out".\
                                    format(slave.mac), "W")

                                # Terminate connection: ........................

                                # Send termination message:
                                self._send("MRIP", slave)

                                # Reset timeout counter:
                                timeouts = 0

                                # Update Slave status:
                                slave.setStatus(Slave.DISCONNECTED)

                                # Restart loop:
                                continue

                                # End check timeout counter - - - - - - - - - - 

                            # End check reply ---------------------------------

                    else: # = = = = = = = = = = = = = = = = = = = = = = = = = = 
                        
                        # If this Slave is neither online nor waiting to be 
                        # contacted, wait for its state to change.

                        # Reset index:
                        slave.setExchange(0)

                        # DEBUG DEACTIV
                        ## print "[Inactive status: {}]".
                        #   format(slave.status)

                        # Wait arbitrary amount (say, comms period):
                        try:
                            slave.lock.release()
                        except thread.error:
                            pass

                        # Restart loop to check again:
                        continue


                finally:
                    # DEBUG DEACTV
                    ## print "Slave lock released", "D"
                    # Guarantee release of Slave-specific lock:

                    try:
                        slave.lock.release()
                    except thread.error:
                        pass

                # End Slave loop (while(True)) =================================


        except Exception as e: # Print uncaught exceptions
            self.printM("[{}] UNCAUGHT EXCEPTION: \"{}\"".
               format(slave.mac, traceback.format_exc()), "E")

        finally:

            try:
                slave.lock.release()
            except thread.error:
                pass

        
        self.printM("[{}] UNCAUGHT EXCEPTION: \"{}\"".
            format(slave.mac, traceback.format_exc()), "E")
        # End _slaveRoutine  # # # # # # # # # # # #  # # # # # # # # # # # # # 

    # # AUXILIARY METHODS # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # ABOUT: These methods are to be used within this class. For methods to
        # be accessed by the user of a Communicator instance, see INTERFACE ME-
        # THODS below.

    def _send(self, message, slave ,repeat = 1, hsk = False): # # # # # # # # # 
        # ABOUT: Send message to a KNOWN or CONNECTED Slave. Automatically add
        # index.
        # PARAMETERS:
        # - message: str, message to send (w/o "INDEX|")
        # - slave: Slave to contact (must be KNOWN or CONNECTED or behavior is
        #   undefined)
        # - repeat: How many times to send message.
        # - hsk: Bool, whether this message is a handshake message.
        # WARNING: THIS METHOD ASSUMES THE SLAVE'S LOCK IS HELD BY ITS CALLER.

        if not hsk:
            # Increment exchange index:
            slave.incrementExchange()
        else:
            # Set index to zero:
            slave.setExchange(0)

        # Send message:
        for i in range(repeat):
            outgoing = "{}|{}".format(slave.exchange, message)
            slave.mosiS.sendto(outgoing,
                (slave.ip, slave.mosiP))

        # Notify user:
        # print "Sent \"{}\" to {} {} time(s)".
        #   format(outgoing, (slave.ip, slave.mosiP), repeat))

        # End _send # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

    def _receive(self, slave): # # # # # # # # # # # # # # # # # # # # # # # # # 
        # ABOUT: Receive a message on the given Slave's sockets (assumed to be
        # CONNECTED, BUSY or KNOWN.
        # PARAMETERS:
        # - slave: Slave unit for which to listen.
        # RETURNS:
        # - three-tuple: 
        #       (exchange index (int), keyword (str), command (str) or None)
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
                message, sender = slave.misoS.recvfrom(
                    self.profiler.maxLength)

                # DEBUG DEACTV
                ## print "Received: \"{}\" from {}".
                 #   format(message, sender), "D")

                try:
                    # Split message: -------------------------------------------
                    splitted = message.split("|")

                    # Verify index:
                    index = int(splitted[0])

                    if index <= slave.misoIndex:
                        # Bad index. Discard message:
                        # print "Bad index: ({})".
                        #   format(index), "D"

                        # Discard message:
                        continue

                    # Check for possible third element:
                    # DEBUG PRINT:
                    #print \
                    #    "Got {} part(s) from split: {}".\
                    #        format(len(splitted), str(splitted)), "D"

                    output = None

                    if len(splitted) == 2:
                        output = (index, splitted[1])
                        
                    elif len(splitted) == 3:
                        output = (index, splitted[1], splitted[2])

                    elif len(splitted) == 4:
                        output = (index, splitted[1], splitted[2], splitted[3])

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
                    #       format(e), "W")

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

    def printM(self, output, tag = 'S'): # =====================================
        # ABOUT: Print on corresponding GUI terminal screen by adding a message to
        # this Communicator's corresponding output Queue.
        # PARAMETERS:
        # - output: str, string to be printed.
        # - tag: str, single character for string formatting.
        # RETURNS: bool, whether the placement of the message was successful.
        # The given message will be added to the corresponding output Queue or
        # will block until it is possible.

        # Place item in corresponding output Queue:
        return self.mainQueue.put((output, tag))

    def printS(self, mac, output, tag = 'S'): # ================================
        # ABOUT: Print on corresponding GUI terminal screen by adding a message to
        # this Communicator's corresponding output Queue.
        # PARAMETERS:
        # - mac: str, MAC address of Slave unit in question
        # - output: str, string to be printed.
        # - tag: str, single character for string formatting.
        # RETURNS: bool, whether the placement of the message was successful.
        # The given message will be added to the corresponding output Queue ONLY
        # IF THERE IS AVAILABLE SPACE. Otherwise, the message will be discarded.
        # Output Queue sizes are set in Profiler.

        # Place item in corresponding output Queue:
        try:
            self.slaveQueue.put_nowait((mac, output, tag))
            return True
        except Queue.Full:
            return False

    # # INTERFACE METHODS # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def add(self, targetMAC): # ================================================
        # ABOUT: Mark a Slave on the network for connection. The given Slave 
        # must be already listed and marked AVAILABLE. This method will mark it 
        # as KNOWN, and the Listener Thread will add it automatically when it
        # responds to the next broadcast.
        # PARAMETERS:
        # - targetMAC: String, MAC address of Slave to "add."

        # Acquire lock:
        self.slaves[targetMAC].lock.acquire()
        try:

            # Check status:
            if self.slaves[targetMAC].status != Slave.AVAILABLE:
                self.printM("ERROR: Tried to add a Slave w/ status other than \
                    AVAILABLE", "E")

            else:
                # If the board is AVAILABLE, set is as KNOWN:
                self.slaves[targetMAC].setStatus(Slave.KNOWN)

        finally:
            self.slaves[targetMAC].lock.acquire(False)
                #                                ^ Non-blocking
                #
                # Note: if the lock was released within the "try" clause
                # then this statement will prevent a threading exception
                # when an attempt to release an unlocked lock is made.
            try:
                self.slaves[targetMAC].lock.release()
            except thread.error:
                    pass


        # End add ==============================================================

    def send(self, command, targetMAC): # ======================================
        # ABOUT: Send a command to a given, connected Slave by adding to its MO-
        # SI Queue. Notice 

        # [NOT IMPLEMENTED]

        pass
        # End send =============================================================


        # End shutdown =========================================================

    def setBroadcastSwitch(self, newState): # ==================================
        """ ABOUT: Set whether to send UDP broadcast. Parameter Switch is
            expected to be True or False. Otherwise, a ValueError is raised.
        """

        # Validate argument:
        if (type(newState) == bool):
            # If input is valid, modify broadcast switch:
            self.broadcastSwitchLock.acquire()
            try:

                self.broadcastSwitch = newState

            finally:

                # Lock will always be released:
                self.broadcastSwitchLock.release()

            if newState:
                self.printB("Broadcast activated", "G")
            else:
                self.printB("Broadcast deactivated")

        else:
            # Raise exception upon invalid input:
            raise ValueError("setBroadcastSwitch expects bool, not {}".\
                format(type(newState)))

        # End setBroadcastSwitch() =========================================

    def getBroadcastSwitch(self): # ============================================
        """ ABOUT: Get the current value of broadcastSwitch.
        """
        return self.broadcastSwitch

        # End getBroadcastSwitch() =============================================





## MODULE'S TEST SUITE #########################################################

if __name__ == "__main__":

    print "FANCLUB MARK II COMMUNICATOR MODULE TEST SUITE INITIATED."
    print "VERSION = " + VERSION


    print "NO TEST SUITE IMPLEMENTED. TERMINATING."