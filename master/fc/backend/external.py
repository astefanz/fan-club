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
        - One for a duty cycle matrix
        - One for uniform flow
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
    INDEX|B|LISTENER_PORT|TIME_STAMP|NROWS|NCOLS|NLAYERS|RPMS
    - Listener reply:
    INDEX|REPLY_CODE|REPLY_VALUE
    - Command to listener:
    INDEX|COMMAND_CODE|COMMAND_VALUE

Given a new index to be compared with the currently-stored one, the new index
is considered valid if the following condition is met:
    new_index > last_index or new_index < last_index - delta
Where "delta" may be chosen arbitrarily.

ON INDICES:
Output indices should be initialized to 1. Input indices should be initialized
to 0.

+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

# IMPORTS ######################################################################
import socket as sk
import threading as mt
from fc import printer as pt, standards as s, archive as ac

# CONSTANT DEFINITIONS #########################################################
RECV_SIZE = 32768
MAIN_SPLITTER = '|'
END_CODE = "END"

# CLASS DEFINITIONS ############################################################
class NoController:
    def set(self, dc):
        self._rip()

    def map(self, *_):
        self._rip()

    def _rip(self):
        raise RuntimeError("No controller set up for external control")

class ExternalControl(pt.PrintClient):
    """
    Back end for "external control" functionality.
    """
    SYMBOL = "[EX]"
    NOTHING = lambda n: None
    BROADCAST_TEMPLATE = "{}|B|{}|{}|{}|{}|{}|{}"

    # TODO: Listener behavior

    # FIXME: redundant work on old F vectors

    def __init__(self, mapper, archive, pqueue,
        controller = NoController(),
        setFEBroadcastStatus = NOTHING,
        setFEBroadcastOut = NOTHING,
        setFEListenerStatus = NOTHING,
        setFEListenerIn = NOTHING,
        setFEListenerOut = NOTHING): # FIXME control
        """
        - mapper := FC Mapper instance (grid mapping).
        - archive := MkIV FCArchive instance.
        - pqueue := Queue instance for I.P. printing.
        """
        pt.PrintClient.__init__(self, pqueue)

        self.mapper = mapper
        self.archive = archive
        self.pqueue = pqueue
        self.controller = controller

        self.profileChange()

        self.broadcastTarget = None
        self.broadcastRepeat = 0

        self.listenerPort = 0
        self.listenerRepeat = 0

        self.setFEBroadcastStatus = setFEBroadcastStatus
        self.setFEBroadcastOut = setFEBroadcastOut
        self.setFEListenerStatus = setFEListenerStatus
        self.setFEListenerIn = setFEListenerIn
        self.setFEListenerOut = setFEListenerOut

        self.ip = '0.0.0.0'
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

        if self.archive[ac.externalListenerAutoStart]:
            self.activateListener(self.defaultListenerPort, self.defaultRepeat)
        if self.archive[ac.externalBroadcastAutoStart]:
            self.activateBroadcast(
                (self.defaultBroadcastIP, self.defaultBroadcastPort),
                self.defaultRepeat)

        self.commandHandlers = {
            s.EX_CMD_F : self._handleF,
            s.EX_CMD_N : self._handleN,
            s.EX_CMD_S : self._handleS,
            s.EX_CMD_DC_VECTOR : self._handleDCVector,
            s.EX_CMD_UNIFORM : self._handleUniform,
            s.EX_CMD_PROFILE : self._handleProfile,
            s.EX_CMD_EVALUATE : self._handleEvaluate,
        }

    # API ----------------------------------------------------------------------
    def isActive(self, key):
        """
        Return whether the requested module (broadcast or listener) is active.
        - key := standard constant referring to either broadcast or listener,
        """
        return self.statuses[key] == s.EX_ACTIVE

    def getBroadcastStatus(self):
        return self.statuses[s.EX_BROADCAST]

    def getListenerStatus(self):
        return self.statuses[s.EX_LISTENER]

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
            self.setFEBroadcastStatus(s.EX_ACTIVE)

    def activateListener(self, port, repeat):
        """
        Activate the listener module.
        """
        if self._activate(s.EX_LISTENER, port = port):
            self.listenerPort = port
            self.listenerRepeat = repeat

            # FIXME
            self.listenerThread = mt.Thread(
                target = self._listenerRoutine,
                args = (self.sockets[s.EX_LISTENER], self._processCommand,
                    self.deactivateListener,
                    self._setListenerIn, self._setListenerOut,
                    self.listenerRepeat, self.pqueue),
                daemon = True)
            # FIXME count?
            self.listenerThread.start()
            self.setFEListenerStatus(s.EX_ACTIVE)


    def deactivateBroadcast(self):
        """
        Deactivate the broadcast module.
        """
        self.deactivate(s.EX_BROADCAST)
        self.setFEBroadcastOut(self.indices[s.EX_BROADCAST][s.EX_I_OUT])
        self.setFEBroadcastStatus(s.EX_INACTIVE)

    def deactivateListener(self, redundant = True):
        """
        Deactivate the listener module.
        - redundant := whether to execute even if the listener appears to be
            deactivated.
        """
        if not self.isListenerActive() or redundant:
            try:
                temp = self._socket('Listener Deactivator', 0, False)
                temp.sendto(bytearray('', 'ascii'),
                    self.sockets[s.EX_LISTENER].getsockname())
                temp.close()
            except AttributeError:
                pass
            self.deactivate(s.EX_LISTENER)
            self.setFEListenerIn(self.indices[s.EX_LISTENER][s.EX_I_IN])
            self.setFEListenerOut(self.indices[s.EX_LISTENER][s.EX_I_OUT])
            self.listenerPort = 0
            self.listenerThread = None
            self.setFEListenerStatus(s.EX_INACTIVE)
            self.warnedDimensions = False

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
            self.sockets[key] = self._socket(s.EX_NAMES[key], port,
                key == s.EX_BROADCAST)
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
            self.indices[key][s.EX_I_IN] = 0
            self.indices[key][s.EX_I_OUT] = 1
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

    def setCallbacks(self, setFEBroadcastStatus = NOTHING,
        setFEBroadcastOut = NOTHING, setFEListenerStatus = NOTHING,
        setFEListenerIn = NOTHING, setFEListenerOut = NOTHING):
        """
        Set the methods to be called to update the front end. The methods will
        be called immediately to match the current state of the back end.
        """
        self.setFEBroadcastStatus = setFEBroadcastStatus
        self.setFEBroadcastOut = setFEBroadcastOut
        self.setFEListenerStatus = setFEListenerStatus
        self.setFEListenerIn = setFEListenerIn
        self.setFEListenerOut = setFEListenerOut

        self.setFEBroadcastStatus(self.getBroadcastStatus())
        self.setFEBroadcastOut(self.indices[s.EX_BROADCAST][s.EX_I_OUT])
        self.setFEListenerStatus(self.getListenerStatus())
        self.setFEListenerIn(self.indices[s.EX_LISTENER][s.EX_I_IN])
        self.setFEListenerOut(self.indices[s.EX_LISTENER][s.EX_I_OUT])

    def setController(self, controller):
        self.controller = controller

    def profileChange(self):
        self.dimensions = (
            self.archive[ac.fanArray][ac.FA_rows],
            self.archive[ac.fanArray][ac.FA_columns],
            self.archive[ac.fanArray][ac.FA_layers],
        )
        self.R, self.C, self.L = self.dimensions
        self.RC = self.R*self.C
        self.RCL = self.RC*self.L

        self.delta = self.archive[ac.externalIndexDelta]

        self.defaultListenerPort = self.archive[ac.externalDefaultListenerPort]
        self.defaultBroadcastPort =self.archive[ac.externalDefaultBroadcastPort]
        self.defaultBroadcastIP = self.archive[ac.externalDefaultBroadcastIP]
        self.defaultRepeat = self.archive[ac.externalDefaultRepeat]

    # Internal methods ---------------------------------------------------------
    def _socket(self, name: str, port: int, broadcast: bool):
        """
        Create an UDP socket on the given port and bound to the given address
        tuple, which must be of the form (TARGET_IP, TARGET_PORT).
        - port := int, port to assign to the socket.
        - broadcast := bool, whether to set the socket as a broadcast socket.
        """
        sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
        sock.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
        sock.settimeout(None)
        if broadcast:
            sock.setsockopt(sk.SOL_SOCKET, sk.SO_BROADCAST, 1)
        sock.bind(("", port))
        self.prints("Opened {} socket on {}".format(name, sock.getsockname()))
        return sock

    def _broadcast(self):
        """
        Send a broadcast.
        """
        try:
            # FIXME performance
            index = self.indices[s.EX_BROADCAST][s.EX_I_OUT]
            message = self.BROADCAST_TEMPLATE.format(
                index, self.listenerPort, 0,  *self.dimensions,
                str(self._G())[1:-1])
            for _ in range(self.broadcastRepeat):
                self.sockets[s.EX_BROADCAST].sendto(
                    bytearray(message, 'ascii'), self.broadcastTarget)
            self.setFEBroadcastOut(index)
            self.indices[s.EX_BROADCAST][s.EX_I_OUT] = index + 1
        except Exception as e:
            self.printx(e, "Error in State Broadcast")
            self.deactivateBroadcast()

    def _G(self):
        """
        Return a grid vector corresponding to the latest feedback vector.
        """
        G = [s.PAD]*(self.mapper.getSize_G()*2)
        for k in range(self.mapper.getSize_K()):
            G[self.mapper.index_KG(k)] = self.F[k]
        return G

    def _processCommand(self, command: str, index_in: int, index_out: int):
        """
        Process a listener command and return the reply to be sent back as well
        as the new input index. Returns None if the given index indicates
        redundancy.
        - command := str, command to process.
        - index_in := int, current listener input index.
        - index_out := int, current listener output index, for replies.
        Returns a tuple of the form
            (reply_bytearray, new_input_index)
        If the command is not redundant according to the current input index, or
            (None, old_input_index)
        If the command is redundant and the message should be ignored.
        """
        splitted = command.split(s.EX_CMD_SPLITTER)
        index_new = int(splitted[s.EX_CMD_I_INDEX])
        code = splitted[s.EX_CMD_I_CODE]
        if code == s.EX_CMD_RESET:
            return (None, 0)
        if index_new == 0:
            self.printw("NOTE: Input index 0 is always ignored")
        if splitted[-1] == '':
            splitted = splitted[:-1]
        if index_new >= index_in - self.delta and index_new <= index_in:
            # new not in [old - delta, old]
            return (None, index_in)
        reply_content = ""
        if code not in s.EX_CMD_CODES:
            raise KeyError("Unrecognized command code \"{}\"".format(code))
        reply_content = self.commandHandlers[code](*splitted)
        reply = "{}|{}|{}".format(index_out, code, reply_content)
        return (bytearray(reply, 'ascii'), index_new)

    def _setListenerIn(self, index):
        self.indices[s.EX_LISTENER][s.EX_I_IN] = index
        self.setFEListenerIn(index)

    def _setListenerOut(self, index):
        self.indices[s.EX_LISTENER][s.EX_I_OUT] = index
        self.setFEListenerOut(index)

    def _handleF(self, index_new, code):
        return str(self.F)[1:-1]

    def _handleN(self, index_new, code):
        return str(self.N)[1:-1]

    def _handleS(self, index_new, code):
        return str(self.S)[1:-1]

    def _handleDCVector(self, index_new, code, R_raw, C_raw, L_raw, vector_raw):
        dcs = tuple(map(float, vector_raw.split(s.EX_LIST_SPLITTER)[:self.RCL]))
        R, C, L = int(R_raw), int(C_raw), int(L_raw)
        if len(dcs) != R*C*L:
            raise ValueError(
                "DC vector length () does not match given ".format(len(dcs))
                + "dimensions ({}x{}x{} = {})".format(L, R, C, L*R*C))
        if (R, C, L) != self.dimensions:
            raise ValueError("DC matrix dimension mismatch. Expected "\
                + "{}x{}x{}".format(R, C, L)\
                + " and got {}x{}x{}".format(*self.dimensions))
        self.controller.map(self._oneToOne(dcs), 0)
        return str(R*C*L)

    def _oneToOne(self, vector):
        """
        Return an FC function that maps fans 1:1 to a given DC vector.
        """
        def f(r, c, l, *_):
            # FIXME lack of robustness w/ assignment position
            return vector[l*self.RC + r*self.C + c]
        return f

    def _handleUniform(self, index_new, code, dc_raw):
        dc = float(dc_raw)
        if dc < 0.0 or dc > 1.0:
            raise ValueError(f"Duty cycle {dc:} outside of range [0.0, 1.0]")
        self.controller.set(dc)
        return str(dc)

    def _handleProfile(self, index_new, code, attribute):
        return self.archive[ac.INVERSE[attribute]]

    def _handleEvaluate(self, index_new, code, expression):
        self.printr("Executing externally received expression: \n\t"+expression)
        return eval(expression)

    @staticmethod
    def _listenerRoutine(socket, method, stop, set_in, set_out, repeat, pqueue):
        P = pt.printers(pqueue, "[XL]")
        pr, pe, px = P[pt.R], P[pt.E], P[pt.X]
        pr("External control listener routine started")

        index_in, index_out = 0, 1
        repeater = range(repeat)
        while True:
            try:
                message, sender = socket.recvfrom(RECV_SIZE)
                decoded = message.decode('ascii')
                if decoded == "":
                    break
                try:
                    reply, index_in = method(decoded, index_in, index_out)
                except Exception as e:
                    px(e,"Exception while processing external command")
                    reply = bytearray(
                        "{}|{}|{}".format(index_out, s.EX_REP_ERROR, e),'ascii')
                if reply is not None:
                    for _ in repeater:
                        socket.sendto(reply, sender)
                    index_out += 1
                set_in(index_in)
                set_out(index_out)
            except Exception as e:
                px(e, "Exception in external control listener routine")
        pr("External control listener routine ended")
        stop(redundant = False)



