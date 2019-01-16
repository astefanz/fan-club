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

## GLOBAL CONSTANTS ############################################################
DPREFIX = "[DBG]"
EPREFIX = "[ERR]"
WPREFIX = "[WRN]"

OUT = sys.stdout
WRN = sys.stdout
ERR = sys.stderr

DEBUGP = False

## AUXILIARY FUNCTIONS #########################################################

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
