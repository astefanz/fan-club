################################################################################
## Project: Fanclub Mark IV "Master" profile GUI  ## File: profile.py         ##
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
 + GUI Component in charge of displaying and manipulating FC profiles.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import tkinter as tk
import tkinter.ttk as ttk

from . import loader as ldr
from .. import archive as ac
## AUXILIARY GLOBALS ###########################################################

## MAIN ########################################################################
class ProfileDisplay(tk.Frame):

    def __init__(self, master, archive):
        """
        Build an empty FC profile display in container MASTER.
        """
        tk.Frame.__init__(self, master = master)

        # TODO:
        # - means by which to automatically update values here if the archive
        #   is modified elsewhere (should this be allowed?)

        # Core setup ...........................................................
        self.archive = archive

        # Grid:
        self.grid_rowconfigure(0, weight = 0)
        self.grid_rowconfigure(1, weight = 0)
        self.grid_rowconfigure(2, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        self.grid_columnconfigure(1, weight = 1)

        # Callbacks:
        # FIXME
        self.applyCallback = self._nothing

        self.addCallback = self._nothing
        self.editCallback = self._nothing
        self.deleteCallback = self._nothing

        # File I/O:
        self.loader = ldr.Loader(self, (("Fan Club Profile",".fcp"),))

        # Build top bar ........................................................
        self.topBar = tk.Frame(self)
        self.topBar.grid(row = 0, sticky = "EW")

        self.topLabel = tk.Label(self.topBar, text = "Profile:   ",
            justify = tk.LEFT)
        self.topLabel.pack(side = tk.LEFT)

        self.defaultButton = tk.Button(self.topBar, text = "Default",
            command = self._default)
        self.defaultButton.pack(side = tk.LEFT)

        self.loadButton = tk.Button(self.topBar, text = "Load",
            command = self._load)
        self.loadButton.pack(side = tk.LEFT)

        self.saveButton = tk.Button(self.topBar, text = "Save",
            command = self._save)
        self.saveButton.pack(side = tk.LEFT)

        self.applyButton = tk.Button(self.topBar, text = "Apply",
            command = self.applyCallback)
        self.applyButton.pack(side = tk.LEFT)

        # Build editor bar .....................................................
        self.editorBar = tk.Frame(self)
        self.editorBar.grid(row = 0, column = 1, sticky = "EW")

        self.editorLabel = tk.Label(self.editorBar, text = "Attribute:   ",
            justify = tk.LEFT)
        self.editorLabel.pack(side = tk.LEFT)

        self.addButton = tk.Button(self.editorBar, text = "Add to",
            command = self.addCallback)
        self.addButton.pack(side = tk.LEFT)

        self.editButton = tk.Button(self.editorBar, text = "Edit",
            command = self.addCallback)
        self.editButton.pack(side = tk.LEFT)

        self.deleteButton = tk.Button(self.editorBar, text = "Delete",
            command = self.addCallback)
        self.deleteButton.pack(side = tk.LEFT)

        # Build display ........................................................
        self.displayFrame = tk.Frame(self)
        self.displayFrame.grid(row = 2, columnspan = 2, sticky = "NEWS",
            pady = 10)

        self.display = ttk.Treeview(self.displayFrame)
        self.display.configure(columns = ("Attribute", "Value"))
        self.display.column("#0", width = 20, stretch = False)
        self.display.column("Attribute", width = 20)
        self.display.column("Value")
        self.display.heading("Attribute", text = "Attribute")
        self.display.heading("Value", text = "Value")
        self.display.pack(fill = tk.BOTH, expand = True)

    # API ----------------------------------------------------------------------
    def update(self):
        """
        Rebuild the displayed values based on the current profile attributes in
        the loaded archive.
        """
        for key in self.archive.keys():
            iid = self.display.insert('', 0,
                values = (self.archive.names[key], self.archive[key])
            )


    # Callbacks ----------------------------------------------------------------
    def _default(self, event = None):
        """
        Switch to the default profile and display it.
        """
        self.archive.default()
        self.update()

    def _save(self, event = None):
        """
        Save the current profile.
        """
        self.archive.save(self.loader.saveDialog("fan_array_profile"))

    def _load(self, event = None):
        """
        Load a new profile.
        """
        self.archive.load(self.loader.loadDialog())

    def _nothing(*args):
        """
        Placeholder for unnasigned callbacks.
        """
        pass

## DEMO ########################################################################

