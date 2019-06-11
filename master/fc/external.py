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
External control back end.

DESIGN NOTES:

Build separate from "master" network (Communicator). Focus on simplicity.

- Do not use a custom rate. Use the rate already set by controls.
- Set as a state vector client. Save most recent of each vector. Broadcast
    feedback vector when received and send state vectors when requested.
- Have states be simply flags. Set up sockets upon activation, tear them down
    upon deactivation.
- Have a short and simple set of commands:
    - Request a state vector
    - Request profile information
    - Fit a duty cycle matrix
- From above, have the following message types:
    - Only one broadcast (send RPM's)
    - Listener commands:
        - One for each state vector, so F, N and S
        - One to fit a duty cycle matrix
        - One to request profile data (send the attribute name)
        - One to evaluate a Python expression
    - Listener replies:
        - One for each requested state vector, so F, N and S. Include vector and
            its timestamps
        - One for requested profile attributes (P?)
        - One for errors (E?)
        - One for Python expression results
- Have a simple message format:
    - Broadcast:
    LISTENER_PORT|INDEX|NROWS|NCOLS|NLAYERS|RPMS
    - Listener reply:
    INDEX|REPLY_CODE|REPLY_VALUE
    - Command to listener:
    INDEX|COMMAND_CODE|COMMAND_VALUE

+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

# IMPORTS ######################################################################
import socket as sk

from . import utils as us, standards as s, archive as ac

# CLASS DEFINITIONS ############################################################
class ExternalControl(us.PrintClient):
    """
    Back end for "external control" functionality.
    """
    SYMBOL = "[EX]"
    NOTHING = lambda n: None
    BROADCAST_TEMPLATE = "{}|{}|{}|{}|{}|{}"

    # TODO: Listener behavior

    # FIXME: redundant work on old F vectors

    def __init__(self, mapper, archive, pqueue,
        setBroadcastStatus = NOTHING,
        setBroadcastOut = NOTHING,
        setListenerStatus = NOTHING,
        setListenerIn = NOTHING,
        setListenerOut = NOTHING): # FIXME control
        """
        - mapper := FC Mapper instance (grid mapping).
        - archive := MkIV FCArchive instance.
        - pqueue := Queue instance for I.P. printing.
        """
        us.PrintClient.__init__(self, pqueue)

        self.mapper = mapper
        self.archive = archive
        self.pqueue = pqueue

        self.dimensions = (
            self.archive[ac.fanArray][ac.FA_layers],
            self.archive[ac.fanArray][ac.FA_rows],
            self.archive[ac.fanArray][ac.FA_columns],
        )
        self.L, self.R, self.C = self.dimensions

        self.broadcastTarget = None
        self.broadcastRepeat = 0

        self.listenerPort = 0
        self.listenerRepeat = 0


        self.setBroadcastStatus = setBroadcastStatus
        self.setBroadcastOut = setBroadcastOut
        self.setListenerStatus = setListenerStatus
        self.setListenerIn = setListenerIn
        self.setListenerOut = setListenerOut

        self.sockets = {}
        self.statuses = {}
        self.indices = {}
        for key in s.EX_KEYS:
            self.sockets[key] = None
            self.statuses[key] = s.EX_INACTIVE
            self.indices[key] = {}
            for index in s.EX_INDICES:
                self.indices[key][index] = 0

        self.F, self.N, self.S = [], [], []

    # API ----------------------------------------------------------------------
    def isActive(self, key):
        """
        Return whether the requested module (broadcast or listener) is active.
        - key := standard constant referring to either broadcast or listener,
        """
        return self.statuses[key] == s.EX_ACTIVE

    def isBroadcastActive(self):
        """
        Return whether the broadcast is active.
        """
        return self.statuses[s.EX_BROADCAST] == s.EX_ACTIVE

    def isListenerActive(self):
        """
        Return whether the listener is active.
        """
        return self.statuses[s.EX_LISTENER] == s.EX_ACTIVE

    def activateBroadcast(self, target, repeat):
        """
        Activate the broadcast module.
        """
        if self._activate(s.EX_BROADCAST):
            self.broadcastTarget = target
            self.broadcastRepeat = repeat
            self.setBroadcastStatus(s.EX_ACTIVE)

    def activateListener(self, port, repeat):
        """
        Activate the listener module.
        """
        if self._activate(s.EX_LISTENER, port = port):
            self.listenerPort = port
            self.listenerRepeat = repeat
            self.setListenerStatus(s.EX_ACTIVE)

    def deactivateBroadcast(self):
        """
        Deactivate the broadcast module.
        """
        self.deactivate(s.EX_BROADCAST)
        self.setBroadcastOut(self.indices[s.EX_BROADCAST][s.EX_I_OUT])
        self.setBroadcastStatus(s.EX_INACTIVE)

    def deactivateListener(self):
        """
        Deactivate the listener module.
        """
        self.deactivate(s.EX_LISTENER)
        self.setListenerIn(self.indices[s.EX_LISTENER][s.EX_I_IN])
        self.setListenerOut(self.indices[s.EX_LISTENER][s.EX_I_OUT])
        self.listenerPort = 0
        self.setListenerStatus(s.EX_INACTIVE)

    def _activate(self, key, port = 0):
        """
        Activate the module referred to by the given key. If the requested
        module is already active, it will be deactivated first. Returns whether
        the operation was successful
        - key := standard constant referring to either the broadcast or listener
            module.
        - port := int, (optional) port to assign to the corresponding socket.
            Defaults to 0 to let the operating system assign any port.
        """
        try:
            if self.isActive(key):
                self.deactivate(key)
            self.sockets[key] = self._socket(port, key == s.EX_BROADCAST)
            self.statuses[key] = s.EX_ACTIVE
            self.prints("{} Activated".format(s.EX_NAMES[key]))
            return True
        except Exception as e:
            self.printx(e,"Error while activating {}".format(s.EX_NAMES[key]))
            self.deactivate(key)
            return False

    def deactivate(self, key):
        """
        Deactivate the module referred to by the given key. Can be called
        redundantly.
        - key := standard constant referring to either the broadcast or listener
            module.
        """
        try:
            self.statuses[key] = s.EX_INACTIVE
            sock = self.sockets[key]
            if sock is not None:
                sock.close()
        except Exception as e:
            self.printx(e,"Error while deactivating {}".format(s.EX_NAMES[key]))
        finally:
            self.sockets[key] = None
            for index in s.EX_INDICES:
                self.indices[key][index] = 0
            self.prints("{} Deactivated".format(s.EX_NAMES[key]))

    def feedbackIn(self, F):
        """
        Process the feedback vector F.
        """
        self.F = F
        if self.isBroadcastActive():
            self._broadcast()

    def networkIn(self, N):
        """
        Process the network state vector N.
        """
        self.N = N

    def slavesIn(self, S):
        """
        Process the slave status vector S.
        """
        self.S = S

    def setCallbacks(self, setBroadcastStatus = NOTHING,
        setBroadcastOut = NOTHING, setListenerStatus = NOTHING,
        setListenerIn = NOTHING, setListenerOut = NOTHING):
        """
        Set the methods to be called to update the front end.
        """
        self.setBroadcastStatus = setBroadcastStatus
        self.setBroadcastOut = setBroadcastOut
        self.setListenerStatus = setListenerStatus
        self.setListenerIn = setListenerIn
        self.setListenerOut = setListenerOut

    def profileChange(self):
        # TODO
        return

    # Internal methods ---------------------------------------------------------
    def _socket(self, port: int, broadcast: bool):
        """
        Create an UDP socket on the given port and bound to the given address
        tuple, which must be of the form (TARGET_IP, TARGET_PORT).
        - port := int, port to assign to the socket.
        - broadcast := bool, whether to set the socket as a broadcast socket.
        """
        sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
        sock.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
        if broadcast:
            sock.setsockopt(sk.SOL_SOCKET, sk.SO_BROADCAST, 1)
        sock.bind(("", port))
        return sock

    def _broadcast(self):
        """
        Send a broadcast.
        """
        try:
            # FIXME performance
            index = self.indices[s.EX_BROADCAST][s.EX_I_OUT]
            message = self.BROADCAST_TEMPLATE.format(
                self.listenerPort, index, *self.dimensions, str(self._G())[1:-1])
            for _ in range(self.broadcastRepeat):
                self.sockets[s.EX_BROADCAST].sendto(
                    bytearray(message, 'ascii'), self.broadcastTarget)
            self.setBroadcastOut(index)
            self.indices[s.EX_BROADCAST][s.EX_I_OUT] = index + 1
        except Exception as e:
            self.printx(e, "Error in State Broadcast")
            self.deactivateBroadcast()

    def _G(self):
        """
        Return a grid vector corresponding to the latest feedback vector.
        """
        G = [s.PAD]*self.mapper.getSize_G()
        for k in range(self.mapper.getSize_K()):
            G[self.mapper.index_KG(k)] = self.F[k]
        return G

