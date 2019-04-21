################################################################################
## Project: Fanclub Mark IV "Master"              ## File: guiutils.py        ##
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
 + Auxiliary tools for GUI.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import sys
import os
import traceback

import tkinter as tk
from tkinter import messagebox

from .. import utils as us

## DEFINITIONS #################################################################
# Pre-defined configurations:
efont = {"font":"Courier 7"}
fontc = {"font":"TkDefaultFont 7"}
padc = {"padx":5, "pady":5}
lfconf = {**fontc, **padc}
lfpack = {"side":tk.TOP, "anchor":tk.N, "fill":tk.X, "expand":True}
rbconf = {"indicatoron":False, **fontc, **padc}

def silent(message):
    """
    Provisional replacement for inter-process prints.
    """
    print("[SILENCED]", message)

def default_printr(message):
    """
    Provisional replacement for inter-process printr. (See fc.utils)
    """
    print("[GP]", message)

def default_printx(e, message):
    """
    Provisional replacement for inter-process printx. (See fc.utils)
    """
    print("[GP]", message, e)

def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    e.g.
            Logo = resource_path("Logo.png")
    Source:
        https://stackoverflow.com/questions/31836104/
        pyinstaller-and-onefile-how-to-include-an-image-in-the-exe-file
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def popup_exception(title, message, exception):
    """
    Build a popup with TITLE, displaying MESSAGE and the traceback on EXCEPTION.
    """
    messagebox.showerror(title = title,
        message = message + "\n\nException:\"{}\"".format(
            traceback.format_exc()))
