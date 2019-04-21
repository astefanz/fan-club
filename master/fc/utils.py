################################################################################
## Project: Fanclub Mark IV "Master" utilities ## File: utils.py              ##
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
 + Auxiliary functions and definitions for testing and debugging.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################

import inspect
    # Print line numbers. See:
    #   http://code.activestate.com/recipes/
    #       145297-grabbing-the-current-line-number-easily/
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

## GLOBAL CONSTANTS ############################################################
DEBUGP = False
DEFAULT_PERIOD = 1 # second

DPREFIX = "[DBG]"
EPREFIX = "[ERR]"
WPREFIX = "[WRN]"

WRN = sys.stdout
ERR = sys.stderr
OUT = sys.stdout

WINDOWS = 'WIN'
MAC = 'MAC'
LINUX = 'LNX'
UNKNOWN = 'UNK'

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
    of this class by overriding the "process" method.

    NOTE that an instance of this class is meant to be started and stopped once
    in its life time. Unless overriden, trying to start a PrintServer twice will
    raise a RuntimeError.

    -- ON PERFORMANCE AND INHERITANCE ------------------------------------------
    This class uses a "sentinel" thread to regularly poll the print queue for
    messages to display to the user. If the default behavior (a standard thread)
    interferes with your interface implementation (e.g. Tkinter with
    multithreading horror) such behavior can be customized by overriding or
    calling the following methods (for some instance P):

    ============================================================================
      METHOD            | DESCRIPTION
    ============================================================================
      P.start()         | build and launch the sentinel thread.
    --------------------+-------------------------------------------------------
      P.stop()          | terminate the sentinel thread
    --------------------+-------------------------------------------------------
      P._cycle()        | execute a single iteration of the sentinel main loop
    --------------------+-------------------------------------------------------
      P._setStarted()   | record that this instance has been started. To be
                        | called by start()
    --------------------+-------------------------------------------------------
      P._checkStarted() | verify that this instance has not been started before
                        | and raise the appropriate exception if it has
    ============================================================================

    While overriding these methods, the following attributes may come in handy:

    ============================================================================
      ATTRIBUTE         | DESCRIPTION
    ============================================================================
      P.period_s        | int; wait between sentinel cycles in seconds
    --------------------+-------------------------------------------------------
      P.period_ms       | int; wait between sentinel cycles in milliseconds
    --------------------+-------------------------------------------------------
      P.done            | threading.Event; to tell sentinel thread to end
    --------------------+-------------------------------------------------------
      P.started         | boolean; whether this instance has been started
    --------------------+-------------------------------------------------------
    """
    SYMBOL = "[PS]"

    def __init__(self, pqueue, period = DEFAULT_PERIOD):
        """
        Build and start a PrintServer that tracks PQUEUE. A daemonic "print
        thread" will be started. The print thread will check for messages to
        print every PERIOD seconds (defaults to PrintServer.default_period).
        """
        PrintClient.__init__(self, pqueue)
        self.period_s = period
        self.period_ms = int(period*1000)
        if self.period_ms <= 0:
            raise ValueError(
                "Given period {}s is too small (yiels {}ms)".format(
                    period_s, period_ms))

        self.started = False
        self.done = mt.Event()

    def process(self, code, text):
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
            target = self._routine, args = (self.done,))
        self.thread.start()
        self._setStarted()

    def stop(self):
        """
        Set the flag to end the print thread. Cannot be undone.
        """
        self.done.set()

    def _routine(self):
        """
        Procedure to be executed by the sentinel thread. Contains its main loop
        and checks for the appropriate threading.Event to terminate.
        """
        while not self.done.is_set():
            try:
                tm.sleep(self.period_s)
                self._cycle()
            except Exception as e:
                self.printx(e, "Exception in sentinel:")
                print("[ERROR] Exception in sentinel:",
                    traceback.format_exc())
        print(self.symbol, "Print thread terminated")

    def _cycle(self):
        """
        Execute one iteration of the print sentinel main loop.

        NOTE: You may want to call this method within a try/catch block to keep
        exceptions from breaking the sentinel loop.
        """
        while not self.pqueue.empty():
            self.process(*self.pqueue.get_nowait())

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

class TerminalPrinter:
    """
    Print FC output (using multiprocessing.Queue) to a given file in a
    multiprocessing.Process. The process is made daemonic so it terminates
    automatically if needed.
    """

    @staticmethod
    def routine(queue, file, lock):
        """
        Continuously scan QUEUE to print its contents to TARGET.

        Stop when LOCK is released.
        """
        T = {
            R : "[R]",
            W : "[W]",
            E : "[!]",
            S : "[S]",
        }
        while not lock.acquire(block = False):
            if not queue.empty():
                message = queue.get_nowait()
                print(T[message[MI_CODE]] + message[MI_CONT],
                    file = file)
        lock.release()

    def __init__(self, queue, file = sys.stdout):
        """
        New TerminalPrinter instance that prints messages sent to QUEUE to FILE.
        """
        self.file = file
        self.queue = queue
        self.lock = mp.Lock()
        self.process = mp.Process(
            name = "FC TerminalPrinter",
            target = self.routine,
            args = (self.queue, self.file, self.lock),
            daemon = True)
        self.lock.acquire()

    def start(self):
        """
        Start the printer process.
        """
        self.process.start()

    def stop(self):
        """
        Stop the printer process.
        """
        self.lock.release()

## Multiplatform facilities ----------------------------------------------------
def platform():
    """
    Return a string representing the current platform:
    utils.WINDOWS, utils.MAC, utils.LINUX or utils.UNKNOWN

    """
    S = plt.system()
    if S == 'Windows':
        return WINDOWS
    elif S == 'Linux':
        return LINUX
    elif S == 'Darwin':
        return MAC
    else:
        return UNKNOWN

## Debug utilities -------------------------------------------------------------

def ln():
    """
    Return the number of the line in source code in which this function is
    called.
    """
    return inspect.currentframe().f_back.f_lineno

def l(message = "", prefix = DPREFIX, postfix = '\n'):
    """
    Print the number of the line in which the function is called.
    - MESSAGE specifies an optional text to include when printing.
      Defaults to an empty string.
    - PREFIX defaults fc.utils.DPREFIX.
    - POSTFIX defaults to newline.
    """
    print(prefix, "L:", inspect.currentframe().f_back.f_lineno, message,
        end = postfix, file = OUT)

def printerr(message, preamble = EPREFIX, signature = ''):
    """
    Print error message MESSAGE to fc.utils.ERR, appending PREAMBLE (defaults
    to fc.utils.EPREFIX) and SIGNATURE (defaults to empty string).
    """
    print(preamble + signature, message, file = ERR)

def printwrn(message, preamble = WPREFIX, signature = ''):
    """
    Print warning message MESSAGE to fc.utils.WRN, appending PREAMBLE (defaults
    to fc.utils.WPREFIX) and SIGNATURE (defaults to empty string).
    """
    print(preamble + signature, message, file = WRN)

def printexc(exception, preamble = EPREFIX, signature = ''):
    """
    Print EXCEPTION to fc.utils.ERR, appending PREAMBLE (defaults to
    fc.utils.EPREFIX) and SIGNATURE (defaults to empty string).
    """
    print(preamble + signature, traceback.format_exc(), file = ERR)

def dprint(*args):
    """
    Wrapper around the standard Python print function that works only when the
    global fc.utils.DEBUGP flag is set to True.
    """
    if DEBUGP:
        print(*args)

