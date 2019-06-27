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
API with which to externally control the FC MkIV master-side.
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """
import socket as sk
import threading as mt

# GLOBAL CONSTANTS #############################################################
DEFAULT_LPORT = 60169
DEFAULT_BPORT = 60069
DEFAULT_DELTA = 10
DEFAULT_PACKET_SIZE = 32768
DEFAULT_TIMEOUT = 3

MAIN_SEPARATOR = '|'
LIST_SEPARATOR = ','

CODE_F = 'F'
CODE_N = 'N'
CODE_S = 'S'
CODE_ERROR = 'E'
CODE_UNIFORM = 'U'
CODE_DC_VECTOR = 'D'
CODE_PROFILE = 'P'
CODE_EVALUATE = 'V'
CODE_RESET = 'R'


# CLASS DEFINITIONS ############################################################
class NoThread:
    def is_alive(self):
        return False

class FCClient:
    """
    Interface for external control. Contains all necessary behavior to control
    the MkIV over a network.
    """
    def __init__(self, R = 11, C = 11, L = 1,
        lport = DEFAULT_LPORT, bport = DEFAULT_BPORT, listener_ip = "0.0.0.0",
        delta = DEFAULT_DELTA, repeat = 0,
        timeout = DEFAULT_TIMEOUT, auto_configure = True,
        packet_size = DEFAULT_PACKET_SIZE, silent = False,
        error_callback = None, broadcast_callback = None):
        """
        Build and initialize an FCClient instance.

        - R := int, number of rows of the fan array being controlled.
            Has an arbitrary default value in case of auto_configure.
        - C := int, number of columns of the fan array being controlled.
            Has an arbitrary default value in case of auto_configure.
        - L := int, number of layers of the fan array being controlled.
            Defaults to the basement tunnel's dimensions
        - lport := int, port number for the command listener. Defaults to the
            default listener port. Can be obtained from state broadcasts.
        - bport := int, port number for the state broadcast. Defaults to the
            default broadcast port.
        - listener_ip := str, IP address to which to send commands. Defaults to
            "0.0.0.0"
        - delta := int, size of the "discard index" range. Defaults to the
            default index delta.
        - repeat := int, number of additional times to send a command. Defaults
            to 0.
        - timeout := how many seconds to wait for a reply. Optional
        - auto_configure := bool, whether to update tunnel parameters and
            listener port based on broadcast data. Optional. Defaults to True.
        - packet_size := int, how many bytes to get (max) per packet. Optional.
        - silent := whether to mute automated prints to terminal.
        - broadcast_callback := method to call when a new broadcast is received.
            The method must accept the following parameters (under any name, but
            in the given order):
                - t := float, the time stamp of the RPM vector
                - R := int, the number of rows
                - C := int, the number of columns
                - L := int, the number of layers
                - rpms := list of ints, the RPM's of the grid in vector form
                    starting from top-left, first layer and moving right.
        - error_callback := method to call when error messages are received.
            The method must accept one string. Defaults to printing to STDOUT.
        """
        self.R, self.C, self.L = R, C, L
        self.RC = self.R*self.C
        self.RCL = self.RC*self.L
        self.listener_port, self.broadcast_port = lport, bport
        self.listener_ip = listener_ip
        self.delta = delta
        self.repeat = repeat
        self.timeout = timeout
        self.auto_configure = auto_configure
        self.packet_size = packet_size
        self.silent = silent
        self._errorCallback = self._printError if error_callback is None else \
            error_callback

        # Broadcast:
        self.broadcast_socket = None
        self._broadcastCallback = self._printGrid if broadcast_callback is None\
            else broadcast_callback
        self.no_thread = NoThread()
        self.broadcast_thread = self.no_thread

        # Listener:
        self.listener_socket = None
        self.resetListenerIndices()
        self._buildListenerSocket()
        if self.listener_port != 0:
            self.requestReset()

    # API ----------------------------------------------------------------------
    # Broadcast ................................................................
    def startBroadcastThread(self):
        if self.isBroadcastThreadActive():
            self.stopBroadcastThread()
        self._buildBroadcastSocket()
        self.broadcast_thread = mt.Thread(target = self._broadcastRoutine,
            daemon = True)
        self.broadcast_thread.start()

    def stopBroadcastThread(self, redundant = False):
        self._verify(redundant, bool)
        if self.isBroadcastThreadActive() or redundant:
            self.listener_socket.sendto(
                bytearray('', 'ascii'), self.broadcast_socket.getsockname())
            self.broadcast_thread = self.no_thread

    def isBroadcastThreadActive(self):
        return self.broadcast_thread.is_alive()

    def setBroadcastCallback(self, callback):
        restart = self.isBroadcastThreadActive()
        self.stopBroadcastThread()
        self.broadcastCallback = callback
        if restart:
            self.startBroadcastThread()

    def setBroadcastPort(self, port):
        self._verify(port, int, minimum = 0, maximum = 65536)
        restart = self.isBroadcastThreadActive()
        self.stopBroadcastThread()
        self.broadcast_port = port
        if restart:
            self.startBroadcastThread()

    def setAutoConfigure(self, auto_configure):
        self.auto_configure = auto_configure

    # Listener .................................................................
    def setListenerPort(self, port):
        """
        Change the port number to which to send commands to the listener.
        - port := int, port to set as target.
        """
        self._verify(port, int, minimum = 0, maximum = 65536)
        self.listener_port = port
        self.print(f"Listener port set to {port}")
        self.requestReset()

    def setListenerIP(self, ip):
        """
        Set the IP address to which to send commands to the listener.
        - ip := str, address to use.
        """
        self._verify(ip, str)
        self.listener_ip = ip
        self.print(f"Listener ip set to {ip}")
        self.requestReset()

    def getListenerIndices(self):
        """
        Return a tuple of the form
            (index_in, index_out)
        With the incoming and outgoing indices used to communicate with the
        command listener.
        """
        return (self.index_in, self.index_out)

    def setListenerIndices(self, index_in = None, index_out = None):
        """
        Modify the listener indices.
        - index_in: int, index for incoming messages (replies)
        - index_out: int, index for outgoing messages (commands)
        """
        if index_in is not None:
            self.index_in = index_in
            self.print(f"Listener incoming index updated to {self.index_in}")
        if index_out is not None:
            self.index_out = index_out
            self.print(f"Listener outgoing index updated to {self.index_out}")

    def resetListenerIndices(self):
        """
        Set the listener indices to their initial values.
        """
        self.index_in, self.index_out = 0, 1

    def sendUniform(self, dc):
        """
        Send a command to set the entire array to the given duty cycle.
        - dc := float, value to assign. Must be in [0.0, 1.0]
        """
        self._verify(dc, int, float, minimum = 0.0, maximum = 1.0)
        return self._sendToListener(CODE_UNIFORM, dc)

    def sendDCVector(self, vector):
        """
        Send the given vector of duty cycles to be mapped 1:1 onto the grid.
        The vector must have length R*C*L and contain only numerical values
        in [0.0, 1.0].
        - vector: list or tuple, vector of duty cycles to apply.
        """
        if len(vector) != self.RCL:
            raise ValueError("Vector size mismatch. Got {}. Expected {}".format(
                len(vector), self.RCL))
        return self._sendToListener(CODE_DC_VECTOR,
            f"{self.R}|{self.C}|{self.L}|" + str(vector)[1:-1])

    def mapRCL(self, f):
        """
        Build a duty cycle vector parameterized by the given function and send
        it as a command to be executed.

        - f := function, must take the following arguments:
            - three integers representing the row, column and layer of the
                fan being evaluated.
            - three integers representing the total number of rows, columns and
                layers of the grid in question.
            It must return a value between 0.0 and 1.0.
        """
        vector = [0]*self.RCL
        for l in range(self.L):
            for r in range(self.R):
                for c in range(self.C):
                    k = l*self.RC + r*self.C + c
                    vector[k] = f(r, c, l, self.R, self.C, self.L)
        return self.sendDCVector(vector)

    def sendExpression(self, expression):
        """
        Send a Python expression to be evaluated. The result is returned.
        - expression := str, expression to evaluate.
        """
        self._verify(expression, str)
        return self._sendToListener(CODE_EVALUATE, expression)

    def queryFeedbackVector(self):
        """
        Request a raw "feedback vector" containing the RPM's and duty cycles
        of the slaves in the network.

        The vector is returned as a list of ints and floats.
        """
        return self._parseGeneric(self._sendToListener(CODE_F))

    def queryNetworkVector(self):
        """
        Request a 'network vector' that summarizes the state of the master-side
        of the network.

        The vector is returned as a list of parsed Python values.
        """
        return self._parseGeneric(self._sendToListener(CODE_N))

    def querySlaveVector(self):
        """
        Request a 'slave vector' that summarizes the state of the slave-side
        of the network.

        The vector is returned as a list of parsed Python values.
        """
        return self._parseGeneric(self._sendToListener(CODE_S))

    def queryProfile(self, attribute):
        """
        Request the value of a 'top level' profile attribute.
        - attribute := str, name of the profile value.
        """
        return eval(self._sendToListener(CODE_PROFILE, attribute))

    def requestReset(self):
        """
        Send a request that this side's outgoing listener index be reset.
        """
        return self._sendToListener(CODE_RESET, get_reply = False)

    # Other ....................................................................
    def setPacketSize(self, size):
        self._verify(size, int, minimum = 1)
        self.packet_size = size
        if self.isBroadcastThreadActive():
            self.startBroadcastThread()

    def setDimensions(self, R, C, L):
        self._verify(R, int, minimum = 0)
        self._verify(C, int, minimum = 0)
        self._verify(L, int, minimum = 0)
        self.R, self.C, self.L = R, C, L
        self.RC = self.R*self.C
        self.RCL = self.RC*self.L
        self.print("Dimensions updated to R: {}, C: {}, L: {}".format(
            self.R, self.C, self.L))

    def setRepeat(self, repeat):
        self._verify(repeat, int, minimum = 0)

    # Internal methods ---------------------------------------------------------
    def _buildSockets(self):
        """
        Create the broadcast and listener sockets and add them as member
        attributes. Can be called repeatedly to rebuild the sockets.
        """
        self._buildListenerSocket()
        self._buildBroadcastSocket()

    def _buildListenerSocket(self):
        """
        Create the listener socket and add it as a member attribute. Can be
        called repeatedly to rebuild the socket.

        The listener socket is bound to an arbitrary port, chosen by the
        operating system.
        """
        if self.listener_socket is not None:
            self.listener_socket.close()
        self.listener_socket = self._socket(name = "Listener")
        self.listener_socket.settimeout(self.timeout)

    def _buildBroadcastSocket(self):
        """
        Create the broadcast socket and add it as a member attribute. Can be
        called repeatedly to rebuild the socket.

        The socket is bound to the given broadcast port and is configured to
        block indefinetly (i.e no timeout).
        """
        if self.broadcast_socket is not None:
            self.broadcast_socket.close()
        self.broadcast_socket = self._socket(
            port = self.broadcast_port, name = "Broadcast")
        self.broadcast_socket.settimeout(None)
        self.broadcast_socket.setsockopt(sk.SOL_SOCKET, sk.SO_BROADCAST, 1)

    def _socket(self, port = 0, name = ""):
        """
        Build and return a new UDP socket bound to the given port. The socket
        is set as "reuseable."

        - port := int, port to which to bind the socket. Defaults to 0 to let
            the operating system choose.

        - name := str, name with which to refer to the socket when printing
            to STDOUT.
        """
        sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
        sock.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
        sock.bind(("", port))
        self.print("{} socket opened on port {}".format(
            name, sock.getsockname()[1]))
        return sock

    def _sendToListener(self, code, content = "", get_reply = True):
        """
        Send a message to the command listener.

        - code := str, code that identifies the type of command.
        - content := str, content of the command, if any.
        - get_reply := bool, whether to wait for a reply and return the result.
            Defaults to True.
        """
        if self.listener_port == 0:
            raise RuntimeError(
            "Listener port set to 0. Is the listener in the other end active?")

        message = bytearray("{}|{}|{}".format(self.index_out, code, content),
                'ascii')
        for _ in range(1 + self.repeat):
            self.listener_socket.sendto(message,
                (self.listener_ip, self.listener_port))
        self.index_out += 1

        if get_reply:
            reply_code, reply_message = self._getReply(code)
            if reply_code == CODE_ERROR:
                self._errorCallback(reply_message)
            return reply_message

    def _getReply(self, code):
        """
        Get and return reply from the listener socket and update the input
        index if necessary.
        Will discard received messages that have an index in the discard range
        or whose code does not correspond to the given one.

        - code: str, expected message code.

        Returns a tuple of the following form:
            (code, contents)
        The returned code is either the given code or the error message code and
        the reply's contents are given as a string.
        Upon timeout, the returned tuple will instead be:
            (None, None)
        """
        index_new, code_new, reply, message, sender \
            = self.index_in, None, "[NONE]", "", None
        try:
            while self._discard(index_new, self.index_in) \
                    or code_new not in (code, CODE_ERROR):
                reply_raw, sender = self.listener_socket.recvfrom(
                    self.packet_size)

                reply = reply_raw.decode('ascii')
                splitted = reply.split(MAIN_SEPARATOR)
                index_new, code_new = int(splitted[0]), splitted[1]
                message = splitted[2]

        except sk.error:
            self.print("Timed out.")
            return (None, None)
        except Exception as e:
            self.print("While parsing the message: \n\t{}\n\n".format(reply)\
                + "The following error occurred: {}".format(e))
            return (None, None)

        self.index_in = index_new
        return (code_new, message)

    def _discard(self, index_new, index_old):
        """
        Return whether the given indices should result in discarding the
        corresponding message.
        """
        return index_new <= index_old and index_new > index_old - self.delta

    def _nothing(self, *_):
        pass

    def _printError(self, message):
        self.print("Error message received ")

    def _broadcastRoutine(self):
        self.print("Broadcast thread started")
        b_index_in = 0
        while True:
            try:
                message, sender = self.broadcast_socket.recvfrom(
                    self.packet_size)
                decoded = message.decode('ascii')
                if decoded == "":
                    break
                parsed = self._parseBroadcast(decoded, b_index_in)
                if parsed is not None:
                    b_index_in = parsed[0]
                    if self.auto_configure:
                        if self.listener_port != parsed[2]:
                            self.setListenerPort(parsed[2])
                        if self.listener_ip != sender[0]:
                            self.setListenerIP(sender[0])
                        R, C, L = parsed[4:7]
                        if self.RCL != R*C*L:
                            self.setDimensions(R, C, L)
                    self._broadcastCallback(*parsed[3:])
            except Exception as e:
                self.print("Exception in broadcast thread: {}".format(e))
        self.stopBroadcastThread()

    def _parseBroadcast(self, message, index_old):
        """
        Parse a broadcast message and return the result.
        - message := str, the decoded broadcast message.
        - index_old := int, the currently-stored broadcast index.
        If the index is not within discard range, a tuple containing all the
        parsed elements of the broadcast is returned. Otherwise, None is
        returned.
        """
        """
        Expected form:
        .........................................................
        INDEX|B|LISTENER_PORT|TIME_STAMP|NROWS|NCOLS|NLAYERS|RPMS
        0.....1.2.............3..........4.....5.....6.......7...
        """
        splitted = message.split(MAIN_SEPARATOR)
        index_new = int(splitted[0])
        if self._discard(index_new, index_old):
            return None
        code = splitted[1]
        listener_port = int(splitted[2])
        time_stamp = int(splitted[3])
        R, C, L = tuple(map(int, splitted[4:7]))
        rpms = tuple(map(int, splitted[7].split(LIST_SEPARATOR)))
        return (index_new, code, listener_port, time_stamp, R, C, L, rpms)

    def _printGrid(self, t, R, C, L, rpms):
        """
        Print a grid using the standard broadcast data.
        """
        grid = ""
        for l in range(L):
            grid += f"L = {l+1:}:"
            for r in range(R):
                grid += "\n| "
                for c in range(C):
                    k = l*self.RC + r*self.C + c
                    rpm = rpms[k]
                    grid += f"{rpm:6d} "
                grid += "|"
        self.print("** {}x{}x{} Grid received at time stamp {}:\n{}".format(
            R, C, L, t, grid))

    def print(self, *args, **kwargs):
        """
        Wrapper around calls to the standard Python print function that respects
        the object's internal "silent" flag.
        """
        if not self.silent:
            print("[FCClient]", *args, **kwargs)

    def _verify(self, value, *types, minimum = None, maximum = None):
        """
        Used to verify arguments and raise exceptions if necessary.
        """
        if type(value) not in types:
            raise TypeError("Bad argument type. Expected {}. Got {}".format(
                types, type(value)))
        if minimum is not None and value < minimum:
            raise ValueError("Under-range argument value {}. Min: {}".format(
                value, minimum))
        if maximum is not None and value > maximum:
            raise ValueError("Over-range value {}. Max: {}".format(
                value, maximum))
        return

    def _parseGeneric(self, vector):
        """
        Parse a "raw vector" as obtained from a listener reply and return the
        result as a list.
        """
        if vector is None:
            return None
        return [eval(raw_value) for raw_value in vector.split(LIST_SEPARATOR)]

# TEST RUN #####################################################################
if __name__ == '__main__':
    c = FCClient()
    c.startBroadcastThread()
    pass


