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
    LISTENER_PORT|INDEX|NROWS|NCOLS|RPMS
    - Listener reply:
    INDEX|REPLY_CODE|REPLY_VALUE
    - Command to listener:
    INDEX|COMMAND_CODE|COMMAND_VALUE

+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

# IMPORTS ######################################################################
import socket as sk

from . import utils as us, standards as s

# CLASS DEFINITIONS ############################################################
class ExternalControl(us.PrintClient):
    """
    Back end for "external control" functionality.
    """
    SYMBOL = "[EX]"

    def __init__(self, archive, pqueue): # FIXME control
        """
        - archive := MkIV FCArchive instance.
        - pqueue := Queue instance for I.P. printing.
        """
        us.PrintClient.__init__(self, pqueue)

        self.archive = archive
        self.pqueue = pqueue

        self.sockets = {}
        self.statuses = {}
        for key in s.EX_KEYS:
            self.sockets[key] = None
            self.statuses[key] = s.EX_INACTIVE

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

    def activateBroadcast(self, target):
        """
        Activate the broadcast module.
        """
        self.activate(s.EX_BROADCAST, target = target)

    def activateListener(self, port):
        """
        Activate the listener module.
        """
        self.activate(s.EX_LISTENER, port = port)

    def deactivateBroadcast(self):
        """
        Deactivate the broadcast module.
        """
        self.deactivate(s.EX_BROADCAST)

    def deactivateListener(self):
        """
        Deactivate the listener module.
        """
        self.deactivate(s.EX_LISTENER)

    def activate(self, key, port = 0, target = ("", 0)):
        """
        Activate the module referred to by the given key. If the requested
        module is already active, it will be deactivated first.
        - key := standard constant referring to either the broadcast or listener
            module.
        - port := int, (optional) port to assign to the corresponding socket.
            Defaults to 0 to let the operating system assign any port.
        - target := int, (optional) address tuple to which to bind the
            corresponding socket. Defaults to ("", 0) to bind to nothing.
        """
        try:
            if self.isActive(key):
                self.deactivate(key)
            self.sockets[key] = self._socket(port,target,key == s.EX_BROADCAST)
            self.statuses[key] = s.EX_ACTIVE
            self.prints("{} Activated".format(s.EX_NAMES[key]))
        except Exception as e:
            self.printx(e,"Error while activating {}".format(s.EX_NAMES[key]))
            self.deactivate(key)

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
            self.prints("{} Deactivated".format(s.EX_NAMES[key]))

    def feedbackIn(self, F):
        """
        Process the feedback vector F.
        """
        # TODO
        pass

    def networkIn(self, N):
        """
        Process the network state vector N.
        """
        # TODO
        pass

    def slavesIn(self, S):
        """
        Process the slave status vector S.
        """
        # TODO
        pass

    # Internal methods ---------------------------------------------------------
    def _socket(self, port: int, target: tuple, broadcast: bool):
        """
        Create an UDP socket on the given port and bound to the given address
        tuple, which must be of the form (TARGET_IP, TARGET_PORT).
        - port := int, port to assign to the socket.
        - target := tuple, of the form (TARGET_IP, TARGET_PORT).
        - broadcast := bool, whether to set the socket as a broadcast socket.
        """
        sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
        sock.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
        if broadcast:
            sock.setsockopt(sk.SOL_SOCKET, sk.SO_BROADCAST, 1)
        sock.bind(target)
        return sock
