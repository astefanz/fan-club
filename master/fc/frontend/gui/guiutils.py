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
from tkinter import simpledialog

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

class PromptLabel(tk.Label):
    """
    A Tkinter Label that creates a popup window requesting a value when
    it is clicked. Besides its required arguments upon construction, it may
    be handled like a regular Tkinter Label.

    NOTE: Do not bind callbacks to this widget upon left click (<Button-1>),
    for this will interfere with the prompt behavior. Instead, incorporate
    the desired behavior into the "callback" method to be passed upon
    construction.
    """

    DIALOGMETHOD = simpledialog.askstring
    N = lambda: ""

    ACTIVE_BG = "white"
    INACTIVE_BG = "gray"

    def __init__(self, master, title, prompt, callback, starter = "", **kwargs):
        """
        Create a new PromptLabel.
        - master := Tkinter parent widget
        - title := String, title to display in popup window
        - prompt := String, text to write in popup window to request input
        - callback := Function to be called when a new input is given; such
            new input will be passed to it
        - starter := method that returns a String when called without arguments;
            the String is to be used as a starting value for the text entry.
            Defaults to a method that returns an empty String.
        Additionally, all optional keyword arguments accepted by Tkinter
        Labels may be used.
        """
        tk.Label.__init__(self, master, **kwargs)

        self.title = title
        self.prompt = prompt
        self.starter = starter

        self.callback = callback
        self.bind("<Button-1>", self._onClick)

        self.enable()

    def _onClick(self, event = None):
        """
        Handle left click event. Generates prompt and passed its result to the
        given callback.
        """
        if self.enabled:
            self.callback(PromptLabel.DIALOGMETHOD(self.title, self.prompt,
                initialvalue = self.starter(), parent = self.winfo_toplevel()))

    def enable(self):
        """
        Enable the widget's interactive behavior. This is the default state.
        """
        self.enabled = True
        self.config(bg = self.ACTIVE_BG)

    def disable(self):
        """
        Disable the widget's interactive behavior.
        """
        self.enabled = False
        self.config(bg = self.INACTIVE_BG)


def _validateN(newCharacter, textBeforeCall, action):
    try:
        return action == '0' or  newCharacter in '0123456789' or \
            int(newCharacter) > 0
    except:
        return False

def _validateF(newCharacter, textBeforeCall, action):
    try:
        return action == '0' or  newCharacter in '.0123456789' or \
            float(newCharacter) > 0 and float(newCharacter) <= 100
    except:
        return False

