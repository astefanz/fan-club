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
 + Auxiliary functions and definitions for testing and debugging.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################

import inspect
    # Print line numbers. See:
    #   http://code.activestate.com/recipes/
    #       145297-grabbing-the-current-line-number-easily/
import sys
import traceback
import platform as plt

## GLOBAL CONSTANTS ############################################################
WINDOWS = 'WIN'
MAC = 'MAC'
LINUX = 'LNX'
UNKNOWN = 'UNK'

## AUXILIARY FUNCTIONS #########################################################

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

def l(message = "", prefix = '', postfix = '\n'):
    """
    Print the number of the line in which the function is called.
    - MESSAGE specifies an optional text to include when printing.
      Defaults to an empty string.
    - PREFIX defaults an empty string.
    - POSTFIX defaults to newline.
    """
    print(prefix, "L:", ln(), message, end = postfix)
