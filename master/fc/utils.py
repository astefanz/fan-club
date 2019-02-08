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
import time as tm

import platform as plt

## GLOBAL CONSTANTS ############################################################
DEBUGP = False

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

# Inter-process printing constants ---------------------------------------------

# Message codes:
D = 100000 # Debug
R = 100001 # Regular
W = 100002 # Warning
E = 100003 # Error
S = 100004 # Success
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
            (R, (symbol if prefix else '') + message))
    funcs[R] = printr

    def printe(message, prefix = True):
        queue.put_nowait(
            (E, (symbol if prefix else '') + message))
    funcs[E] = printe

    def printw(message, prefix = True):
        queue.put_nowait(
            (W, (symbol if prefix else '') + message))
    funcs[W] = printw

    def printd(message, prefix = True):
        if DEBUGP:
            queue.put_nowait(
                (D, (symbol if prefix else '') + message))
    funcs[D] = printd

    def prints(message, prefix = True):
        queue.put_nowait(
            (S, (symbol if prefix else '') + message))
    funcs[S] = prints

    def printx(exception, message = ''):
        queue.put_nowait(
            (E, symbol + traceback.format_exc()))
    funcs[X] = printx

    return funcs

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
