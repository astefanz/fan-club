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

from . import network as ntw, control as ctr, profile as pro, console as csl


if __name__ == '__main__':
    import embedded.caltech_white as cte
else:
    from .embedded import caltech_white as cte

## AUXILIARY GLOBALS ###########################################################
BG_CT = "#ff6e1f"
BG_ERROR = "#510000"
FG_ERROR = "red"

## MAIN ########################################################################
class Base(tk.Frame):

    ERROR_MESSAGE = \
        "[NOTE: There are error messages in the console. Click here.]"

    def __init__(self, master, network, title, version):
        """
        Create a new GUI base on the Tkinter root MASTER, with title TITLE and
        showing the version VERSION.
        """
        tk.Frame.__init__(self, master = master)

        # Core setup -----------------------------------------------------------
        self.network = network

        self.screenWidth = self.master.winfo_screenwidth()
        self.screenHeight = self.master.winfo_screenheight()

        self.winfo_toplevel().title(title)
        self.winfo_toplevel().geometry("{}x{}".format(
            self.screenWidth//2, self.screenHeight//2))

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
        self.profileWidget = pro.ProfileDisplay(self.profileTab)
        self.profileWidget.pack(fill = tk.BOTH, expand = True, padx = 20,
            pady = 20)

        # Network tab:
        self.networkWidget = ntw.NetworkWidget(self.networkTab, network)
        self.networkWidget.pack(fill = tk.BOTH, expand = True, padx = 20,
            pady = 20)

        # Control tab:
        self.controlWidget = ctr.ControlWidget(self.controlTab, network)
        self.controlWidget.pack(fill = tk.BOTH, expand = True, padx = 20,
            pady = 20)

        # Console tab:
        self.consoleWidget = csl.ConsoleWidget(self.consoleTab,
            self._consoleWarning)
        self.consoleWidget.pack(fill = tk.BOTH, expand = True, padx = 20,
            pady = 20)
        self.consoleTab.bind("<Visibility>", self._consoleCalm)
        # FIXME

        self.notebook.add(self.profileTab, text = "Profile")
        self.notebook.add(self.networkTab, text = "Network")
        self.notebook.add(self.controlTab, text = "Control")
        self.notebook.add(self.consoleTab, text = "Console")

        self.notebook.grid(row = 1, sticky = 'NWES')

        # Bottom bar ...........................................................
        self.bottomBar = tk.Frame(self)
        self.bottomBar.grid(row = 2, sticky = 'EW')
        self.bottomWidget = ntw.StatusBarWidget(self.bottomBar, network)
        self.bottomWidget.pack(side = tk.LEFT, fill = tk.X, expand = True)

        # FIXME:
        print("[WARNING] Missing Ext. Control")
        print("[WARNING] Missing Console")

    def focusProfile(self, *_):
        self.notebook.select(0)

    def focusNetwork(self, *_):
        self.notebook.select(1)

    def focusControl(self, *_):
        self.notebook.select(2)
        #self.controlWidget.redrawGrid()

    def focusConsole(self, *_):
        self.notebook.select(3)

    def getConsoleMethods(self):
        c = self.consoleWidget
        return (c.printr, c.printw, c.printe, c.prints, c.printd, c.printx)

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

    # Splash screen:
    S = spl.SplashHandler(spl.FCSplashWidget, 'Demo', width = 750, height = 500,
        useFactor = False)

    S.start()
    tm.sleep(.69)
    S.stop()

    # GUI:
    root = tk.Tk()

    base = Base(root, title = "FC MkIV Base GUI Demo", version = "Demo")

    top = tk.Label(base.getTopBar(), text = "Top Bar")
    base.addToTop(top)

    profile = pro.ProfileDisplay(base.getProfileTab())
    base.setProfileWidget(profile)

    network = tk.Label(base.getNetworkTab(), text = "Network Tab")
    base.setNetworkWidget(network)

    control = tk.Label(base.getControlTab(), text = "Control Tab")
    base.setControlWidget(control)

    bot = tk.Label(base.getBottomBar(), text = "Bottom Bar")
    base.addToBottom(bot)

    base.pack(fill = tk.BOTH, expand = True)
    root.mainloop()
    print("FC GUI Base demo finished")
