################################################################################
## Project: Fanclub Mark IV "Master" base window  ## File: base.py            ##
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
 + Basic container for all other FC GUI widgets.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import time as tm
import tkinter as tk
import tkinter.ttk as ttk

from fc.frontend.gui import guiutils as gus
from fc.frontend.gui.widgets import network as ntw, control as ctr, \
    profile as pro, console as csl
from fc.frontend.gui.embedded import caltech_white as cte
from fc import printer as pt, utils as us

## AUXILIARY GLOBALS ###########################################################
BG_CT = "#ff6e1f"
BG_ERROR = "#510000"
FG_ERROR = "red"

NOPE = lambda m: print("[SILENCED]: ", m)

## MAIN ########################################################################
class Base(tk.Frame, pt.PrintClient):

    ERROR_MESSAGE = \
        "[There are error messages in the console. Click here.]"

    SYMBOL = "[BS]"

    def __init__(self, master, network, external, mapper, archive, title,
        version, feedbackAdd, networkAdd, slavesAdd, profileCallback,
        setLive, setF, pqueue):
        """
        Create a new GUI base on the Tkinter root MASTER, with title TITLE and
        showing the version VERSION.

        FEEDBACKADD, NETWORKADD and SLAVESADD are methods to which widgets that
        are "clients" of the feedback, network and slaves vectors should be
        passed to assign them as such to the inter-process communications
        framework.

        PROFILECALLBACK is a method to be called without arguments when a
        profile is changed.

        PQUEUE is the Queue object to be used for inter-process printing.
        """
        # FIXME outdated description
        tk.Frame.__init__(self, master = master)
        pt.PrintClient.__init__(self, pqueue, self.SYMBOL)

        print("[NOTE] Streamline GUI printing?") # TODO

        # Core setup -----------------------------------------------------------
        self.network = network
        self.external = external
        self.mapper = mapper
        self.archive = archive
        self.feedbackAdd = feedbackAdd
        self.networkAdd = networkAdd
        self.slavesAdd = slavesAdd

        self.setLive, self.setF = setLive, setF

        self.screenWidth = self.master.winfo_screenwidth()
        self.screenHeight = self.master.winfo_screenheight()

        self.winfo_toplevel().title(title)

        """
        self.winfo_toplevel().geometry("{}x{}".format(
            self.screenWidth//2, self.screenHeight//2))
        """

        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure(1, weight = 1)

        self.version = version
        # Containers -----------------------------------------------------------

        # Top bar ..............................................................
        self.topBar = tk.Frame(self, relief = 'ridge', borderwidth = 2,
            bg = BG_CT)
        self.topBar.grid(row = 0, sticky = 'EW')

        self.caltechImage = tk.PhotoImage(data = cte.CALTECH)
        self.caltechImage = self.caltechImage.subsample(15)
        self.caltechLabel = tk.Label(self.topBar, image = self.caltechImage,
            bg = self.topBar['bg'])

        self.caltechLabel.pack(side = tk.LEFT, ipady = 4, padx = 6)

        self.errorLabel = tk.Label(self.topBar, text = self.ERROR_MESSAGE,
            bg = BG_ERROR, fg = FG_ERROR, padx = 10)
        self.errorLabel.bind("<Button-1>", self.focusConsole)
        self.warning = False

        self.topWidgets = []

        # Help:
        self.helpButton = tk.Button(self.topBar, text = "Help",
            command = self._helpCallback)
        self.helpButton.pack(side = tk.RIGHT)
        self.topWidgets.append(self.helpButton)

        # Notebook .............................................................
        self.notebook = ttk.Notebook(self)
        self.profileTab = tk.Frame(self.notebook)
        self.networkTab = tk.Frame(self.notebook)
        self.controlTab = tk.Frame(self.notebook)
        self.consoleTab = tk.Frame(self.notebook)

        # Profile tab:
        self.profileWidget = pro.ProfileDisplay(self.profileTab, archive,
            profileCallback, pqueue)
        self.profileWidget.pack(fill = tk.BOTH, expand = True, padx = 20,
            pady = 20)

        # Network tab:
        self.networkWidget = ntw.NetworkWidget(self.networkTab,
            network = network, archive = archive, networkAdd = self.networkAdd,
            slavesAdd = self.slavesAdd, pqueue = pqueue)
        self.networkWidget.pack(fill = tk.BOTH, expand = True, padx = 20,
            pady = 20)

        # Control tab:
        self.controlWidget = ctr.ControlWidget(self.controlTab,
            network = network,
            external = external,
            mapper = mapper,
            archive = archive,
            setLiveBE = self.setLive,
            setFBE = self.setF,
            pqueue = pqueue)

        self.controlWidget.pack(fill = tk.BOTH, expand = True, padx = 20,
            pady = 20)
        self.feedbackAdd(self.controlWidget)
        self.slavesAdd(self.controlWidget)
        self.networkAdd(self.controlWidget)

        # Console tab:
        self.consoleWidget = csl.ConsoleWidget(self.consoleTab,
            self._consoleWarning)
        self.consoleWidget.pack(fill = tk.BOTH, expand = True, padx = 20,
            pady = 20)
        self.consoleTab.bind("<Visibility>", self._consoleCalm)

        self.notebook.add(self.profileTab, text = "Profile")
        self.notebook.add(self.networkTab, text = "Network")
        self.notebook.add(self.controlTab, text = "Control")
        self.notebook.add(self.consoleTab, text = "Console")

        self.notebook.grid(row = 1, sticky = 'NWES')

        # Bottom bar ...........................................................
        self.bottomBar = tk.Frame(self)
        self.bottomBar.grid(row = 2, sticky = 'EW')
        self.bottomWidget = ntw.StatusBarWidget(self.bottomBar,
            network.shutdown, pqueue)
        self.bottomWidget.pack(side = tk.LEFT, fill = tk.X, expand = True,
            pady = 3, padx = 3)
        self.networkAdd(self.bottomWidget)
        self.slavesAdd(self.bottomWidget)

    def focusProfile(self, *_):
        self.notebook.select(0)

    def focusNetwork(self, *_):
        self.notebook.select(1)

    def focusControl(self, *_):
        self.controlWidget.blockAdjust()
        self.notebook.select(2)
        self.controlWidget.redraw()
        self.after(50, self.controlWidget.unblockAdjust)

    def focusConsole(self, *_):
        self.notebook.select(3)

    def getConsoleMethods(self):
        c = self.consoleWidget
        return (c.printr, c.printw, c.printe, c.prints, c.printd, c.printx)

    def profileChange(self):
        self.networkWidget.profileChange()
        self.controlWidget.profileChange()
        self.bottomWidget.profileChange()

    # Internal methods ---------------------------------------------------------
    def _helpCallback(self):
        """
        To be called when the Help button is pressed.
        """
        print("[WARNING] Help button not yet built") # FIXME

    def _consoleWarning(self):
        """
        To be used by the console to warn the user of errors.
        """
        self.errorLabel.pack(side = tk.LEFT, padx = 100, fill = tk.Y)
        self.warning = True

    def _consoleCalm(self, *E):
        """
        To be called after the console is  warnings have been checked.
        """
        if self.warning:
            self.errorLabel.pack_forget()


## DEMO ########################################################################
if __name__ == '__main__':
    import splash as spl
    import profile as pro

    print("FC GUI Base demo started")

    print("FC GUI Base demo not implemented")

    print("FC GUI Base demo finished")
