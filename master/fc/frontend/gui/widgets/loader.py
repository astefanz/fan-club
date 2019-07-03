################################################################################
## Project: Fanclub Mark IV "Master" GUI          ## File: loader.py          ##
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
 + General file I/O facilities for FCGUI widgets.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import os
import time as tm

import tkinter as tk
import tkinter.filedialog as fdg
import tkinter.ttk as ttk
import tkinter.font as fnt

from fc.frontend.gui import guiutils as gus
from fc.frontend.gui.widgets import grid as gd
from fc.frontend.gui.embedded import colormaps as cms

## GLOBALS #####################################################################
NOTHING = lambda: None

## WIDGETS #####################################################################
class Loader(tk.Frame):
    """
    Base class to handle file I/O for a given file extension (both read and
    write).
    """

    TITLE = "Choose file"

    def __init__(self, master, filetypes):
        """
        Create a new Loader that expects to load and save files with the given
        FILETYPES --expected to be a nonempty list or tuple of (name, ext)
        pairs where each "ext" (extension) starts with a dot and has at least
        length 2.
        """
        tk.Frame.__init__(self, master)

        # Validate input:
        self.filetypes = []
        if not filetypes:
            raise ValueError("Tried to construct Loader without filetypes.")
        for i, filetype in enumerate(filetypes):
            error = None
            if len(filetype[1]) <= 0:
                error = "Extension too short (length {}) ".format(
                    len(filetype[1]))
            elif filetype[1][0] != '.':
                error = "Badly formatted filetype (missing dot) "
            if error:
                raise ValueError(error + "({})".format(i))
            else:
                self.filetypes.append((filetype[0], '*' + filetype[1]))

        self.filetypes.append(("All files", "*.*"))

        # Build member attributes:
        self.filetypes = tuple(filetypes)
        self.directory = os.getcwd()

    def loadDialog(self):
        """
        Launch a Tkinter file dialog for the user to choose a filename. Returns
        the path to the chosen file.
        """

        filename = fdg.askopenfilename(initialdir = self.directory,
            title = self.TITLE, filetypes = self.filetypes)
        if not filename:
            return None
        splitted = filename.split('/')[:-1]
        self.directory = ("{}/"*len(splitted)).format(*splitted)
        return filename

    def saveDialog(self, default = None):
        """
        Launch a Tkinter file dialog to choose a file to which to write and
        return the chosen filename as a string, or None if the user cancelled
        the operation.

        DEFAULT (optional) allows the caller to specify an initial filename.
        """
        args = {} if not default else {'initialfile' : default}

        filename = fdg.asksaveasfilename(
            initialdir = self.directory,
            title = self.TITLE, filetypes = self.filetypes, **args)
        splitted = filename.split('/')[:-1]
        self.directory = ("{}/"*len(splitted)).format(*splitted)
        if not filename:
            return None
        return filename

    def load(self, filename = None):
        """
        Load the file given by FILENAME and return its contents (as a string) in
        a tuple, of the form:
            (CONTENTS, FILENAME)
        If the argument FILENAME is omitted, loadDialog will be called to
        request a file name from the user. Returns None if a dialog is used and
        the user does not choose a file.
        """
        if not filename:
            filename = self.loadDialog()
        if not filename:
            return None
        with open(filename, 'r') as f:
            contents = f.read()
        return (contents, filename)

    def save(self, contents, filename = None, default = None):
        """
        Write CONTENTS into a FILENAME. If FILENAME is None, asks the user
        by calling saveDialog. If the result is None again, the operation is
        cancelled. Likewise if CONTENTS is None, the function will return
        immediately without prompting the user.

        DEFAULT may be optionally used to specify a default filename for the
        dialog that may be displayed.

        Returns the number of bytes written, nor None if the operation was
        cancelled
        """
        if not contents:
            return None
        if not filename:
            filename = self.saveDialog(default)
        if not filename:
            return None

        with open(filename, 'w') as f:
            return f.write(contents)


class LoaderWidget(Loader):
    """
    Loader with a minimal Tkinter GUI (just buttons).
    """

    def __init__(self, master, filetypes, onSave, onLoad, default = NOTHING):
        """
        Create a new Loader widget in MASTER that reads and writes files of
        types FILETYPES. (See Loader.) When the user clicks on the Save or
        Load buttons, the result of executing the corresponding methods (
        either the contents of a file, if loading, or a request for contents
        to save, if saving) will cause the methods ONSAVE and ONLOAD to be
        called as appropriate.

        DEFAULT (optional) is a method to be called to specify a default
        filename when saving.
        """
        Loader.__init__(self, master, filetypes)
        self.default = default
        self.onSave = onSave
        self.onLoad = onLoad
        self.interactive = []

        self._buildLoadButton()
        self._buildSaveButton()

    def config(self, state):
        """
        Allow widget to be disabled by Tkinter config method.
        """
        if state == tk.NORMAL:
            self.enable()
        else:
            self.disable()

    def enable(self):
        """
        Enable interactive components.
        """
        for widget in self.interactive:
            widget.config(state = tk.NORMAL)

    def disable(self):
        """
        Disable interactive components.
        """
        for widget in self.interactive:
            widget.config(state = tk.DISABLED)

    def _load(self, *E):
        """
        Load button callback.
        """
        self.onLoad(self.load())

    def _save(self, *E):
        """
        Save button callback.
        """
        self.save(self.onSave(), default = self.default())

    def _addInteractive(self, widget):
        """
        Add an interactive widget for systematic enabling and disabling.
        """
        self.interactive.append(widget)

    def _buildLoadButton(self, text = "Load"):
        self.loadButton = tk.Button(self, text = text,
            **gus.padc, **gus.fontc, command = self._load)
        self.loadButton.pack(side = tk.LEFT, **gus.padc)
        self.interactive.append(self.loadButton)

    def _buildSaveButton(self, text = "Save"):
        self.saveButton = tk.Button(self, text = text,
            **gus.padc, **gus.fontc, command = self._save)
        self.saveButton.pack(side = tk.LEFT, **gus.padc)
        self.interactive.append(self.saveButton)

class FlowLoaderWidget(LoaderWidget):
    """
    Shorthand for a LoaderWidget that loads flows from CSV files.
    Does not allow saving.
    """
    EXTENSION = ".csv"
    FILETYPES = (("CSV", EXTENSION),)

    def __init__(self, master, onLoad):
        """
        See LoaderWidget.
        """
        LoaderWidget.__init__(self, master, self.FILETYPES, lambda: None, onLoad)
        self.default = lambda: "FCMkIV_flow_{}{}".format(tm.strftime(
            "%a_%d_%b_%Y_%H-%M-%S", tm.localtime()), self.EXTENSION)

    def _save(self, *_):
        """
        No saving implemented.
        """
        pass

    def _buildSaveButton(self):
        """
        No saving here.
        """
        pass

    def _buildLoadButton(self):
        LoaderWidget._buildLoadButton(self, "Choose File")

