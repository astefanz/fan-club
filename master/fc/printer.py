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
 + Streamlined inter-process text output.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import sys
import traceback
import io as io
    # StringIO to redirect stdout. See:
    # https://stackoverflow.com/questions/1218933/
    #   can-i-redirect-the-stdout-in-python-into-some-sort-of-string-buffer
import multiprocessing as mp
import threading as mt
import time as tm

import platform as plt

import fc.standards as std

## GLOBAL CONSTANTS ############################################################
DEBUGP = False

DPREFIX = "[DBG]"
EPREFIX = "[ERR]"
WPREFIX = "[WRN]"

WRN = sys.stdout
ERR = sys.stderr
OUT = sys.stdout

HEADER = \
"""
--------------------------------------------------------------------------------
-- CALIFORNIA INSTITUTE OF TECHNOLOGY -- GRADUATE AEROSPACE LABORATORY        --
-- CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES                             --
--------------------------------------------------------------------------------
--      ____      __      __  __      _____      __      __    __    ____     --
--     / __/|   _/ /|    / / / /|  _- __ __\    / /|    / /|  / /|  / _  \    --
--    / /_ |/  / /  /|  /  // /|/ / /|__| _|   / /|    / /|  / /|/ /   --||   --
--   / __/|/ _/    /|/ /   / /|/ / /|    __   / /|    / /|  / /|/ / _  \|/    --
--  / /|_|/ /  /  /|/ / // //|/ / /|__- / /  / /___  / -|_ - /|/ /     /|     --
-- /_/|/   /_/ /_/|/ /_/ /_/|/ |\ ___--|_|  /_____/| |-___-_|/  /____-/|/     --
-- |_|/    |_|/|_|/  |_|/|_|/   \|___|-    |_____|/   |___|     |____|/       --
--                   _ _    _    ___   _  _      __  __   __                  --
--                  | | |  | |  | T_| | || |    |  ||_ | | _|                 --
--                  | _ |  |T|  |  |  |  _|      ||   ||_//                   --
--                  || || |_ _| |_|_| |_| _|    |__|  |___|                   --
--                                                                            --
--------------------------------------------------------------------------------
--   <astefanz@berkeley.edu> <cdougher@caltech.edu> <mveisman@caltech.edu>    --
--------------------------------------------------------------------------------
"""

# Inter-process printing constants ---------------------------------------------

# Message codes:
R = 100001 # Regular
W = 100002 # Warning
E = 100003 # Error
S = 100004 # Success
D = 100000 # Debug
X = 100005 # Exception

# Message code to string marks:
CODE_TO_STR = {
    R : "",
    W : "[WARNING]",
    E : "[*ERROR*]",
    S : "",
    D : "[_DEBUG_]",
}

# Message content indices:
MI_CODE = 0
MI_CONT = 1

## AUXILIARY FUNCTIONS #########################################################

## Printing utilities ----------------------------------------------------------
def printers(queue, symbol = "[--]"):
    """
    Generate and return standard FC print functions that redirect their output
    to the multiprocess queue QUEUE after prefixing SYMBOL. The functions are
    returned inside a dictionary in which the constants R, W, E, S, D and X,
    defined in fc.utils correspond as keys to 'regular,' 'warning,' 'error,'
    'success' and 'exception' print functions.

    The exception print function expects an Exception instance whose traceback
    to print and an optional string to include as an error message; all other
    functions expect a string to print as output and an optional boolean that
    specifies whether to append SYMBOL as a prefix.

    NOTE: Debug prints can be turned on (True) or off (False) by modifying the
    global variable fc.utils.DEBUGP.

    NOTE: the given queue will be used through its put_nowait method, and no
    Exception checking is done within the print functions.
    """
    symbol += ' '
    funcs = {}
    def printr(message, prefix = True):
        queue.put_nowait(
            (R, tm.strftime("[%H:%M:%S]") + (symbol if prefix else '') \
                + message))
    funcs[R] = printr

    def printe(message, prefix = True):
        queue.put_nowait(
            (E,  tm.strftime("[%H:%M:%S]") + (symbol if prefix else '') \
                + message))
    funcs[E] = printe

    def printw(message, prefix = True):
        queue.put_nowait(
            (W,  tm.strftime("[%H:%M:%S]") + (symbol if prefix else '') \
                + message))
    funcs[W] = printw

    def printd(message, prefix = True):
        if DEBUGP:
            queue.put_nowait(
                (D,  tm.strftime("[%H:%M:%S]") + (symbol if prefix else '') \
                    + message))
    funcs[D] = printd

    def prints(message, prefix = True):
        queue.put_nowait(
            (S, ( tm.strftime("[%H:%M:%S]") + symbol if prefix else '') \
                + message))
    funcs[S] = prints

    def printx(exception, message = ''):
        queue.put_nowait(
            (E, tm.strftime("[%H:%M:%S]") + symbol + message \
                + ' "{}"'.format(exception) \
                + '\nTraceback:\n' + traceback.format_exc()))
    funcs[X] = printx

    return funcs

class PrintClient:
    """
    Simple class to be inherited from by classes that use the queued-printing
    facilities given by printers. Serves as a shortcut for common member
    function creation.
    """
    SYMBOL = "[--]"

    def __init__(self, pqueue, symbol = "[--]"):
        """
        Create the following member functions for streamlined queued printing
        in this instance:

        - printr: regular print
        - printe: error print
        - printw: warning print
        - printd: debug print
        - prints: success print
        - printx: exception print

        """
        P = printers(pqueue, self.SYMBOL)
        self.printr = P[R]
        self.printe = P[E]
        self.printw = P[W]
        self.printd = P[D]
        self.prints = P[S]
        self.printx = P[X]
        self.pqueue = pqueue

class PrintServer(PrintClient):
    """
    Watch a print queue for messages and print them to some form of text
    output. The specific printing process is to be implemented by the children
    of this class by overriding the "print" method.

    NOTE that an instance of this class is meant to be started and stopped once
    in its life time. Unless overriden, trying to start a PrintServer twice will
    raise a RuntimeError.
    """
    SYMBOL = "[PS]"

    def __init__(self, pqueue):
        """
        Build and start a PrintServer that tracks PQUEUE. A daemonic "print
        thread" will be started.
        """
        PrintClient.__init__(self, pqueue)

        self.started = False
        self.done = mt.Event()

    def print(self, code, text):
        """
        To be overriden by child classes to implement specific printing
        behavior. CODE is a constant as defined in utils.py; it determines
        what kind of message this is (i.e a warning, an error, etc.). TEXT is
        the actual message to display.
        """
        raise RuntimeError("PrintServer process method not implemented")

    def start(self):
        """
        Start the print thread. RuntimeError if this PrintServer is or has ever
        been started.
        """
        self._checkStarted()
        self.thread = mt.Thread(name = "FC Print Thread",
            target = self._routine, daemon = True)
        self.thread.start()
        self._setStarted()

    def stop(self):
        """
        Set the flag to end the print thread. Cannot be undone.
        """
        self.pqueue.put_nowait(std.END)

    def _routine(self):
        """
        Procedure to be executed by the sentinel thread. Contains its main loop
        and checks for the appropriate threading.Event to terminate.
        """
        print(self.SYMBOL, "Print thread started.")
        self.printr("Print thread started.")
        while True:
            try:
                message = self.pqueue.get()
                if message == std.END:
                    break
                self.print(*message)
            except Exception as e:
                print("[ERROR] Exception in print thread:",
                    traceback.format_exc())
                self.printx(e, "Exception in print thread:")
        print(self.SYMBOL, "Print thread terminated.")
        self.printr("Print thread started.")

    def _checkStarted(self):
        """
        Verify that this instance has not been started before. If so, raise a
        RuntimeError.
        """
        if self.started:
            raise RuntimeError("Tried to start the same sentinel twice.")

    def _setStarted(self):
        """
        Record that this instance has been started once.
        """
        self.started = True
