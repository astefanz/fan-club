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

if __name__ == '__main__':
    import embedded.caltech as cte
else:
    from .embedded import caltech as cte

## AUXILIARY GLOBALS ###########################################################

## MAIN ########################################################################
class Base(tk.Frame):

    """ Tab codes """
    T_PROFILE = 0
    T_NETWORK = 1
    T_CONTROL = 2

    def __init__(self, master, title = "FC MkIV", version = "N/A"):

        # Core setup -----------------------------------------------------------
        tk.Frame.__init__(self, master = master)


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
        self.topBar = tk.Frame(self, relief = 'ridge', borderwidth = 2)
        self.topBar.grid(row = 0, sticky = 'EW')

        self.caltechImage = tk.PhotoImage(data = cte.CALTECH)
        self.caltechImage = self.caltechImage.subsample(25)
        self.caltechLabel = tk.Label(self.topBar, image = self.caltechImage)

        self.caltechLabel.pack(side = tk.LEFT, ipady = 4, padx = 6)

        self.topWidgets = []

        # Notebook .............................................................
        self.notebook = ttk.Notebook(self)
        self.profileTab = tk.Frame(self.notebook)
        self.networkTab = tk.Frame(self.notebook)
        self.controlTab = tk.Frame(self.notebook)

        self.profileWidget = None
        self.networkWidget = None
        self.controlWidget = None

        self.notebook.add(self.profileTab, text = "Profile")
        self.notebook.add(self.networkTab, text = "Network")
        self.notebook.add(self.controlTab, text = "Control")

        self.notebook.grid(row = 1, sticky = 'NWES')

        # Bottom bar ...........................................................
        self.bottomBar = tk.Frame(self)
        self.bottomBar.grid(row = 2, sticky = 'EW')
        self.bottomWidget = None

    def getTopBar(self):
        return self.topBar

    def addToTop(self, widget):
        self.topWidgets.append(widget)
        widget.pack(side = tk.RIGHT)

    def getBottomFrame(self):
        return self.bottomBar

    def setBottom(self, widget):
        self.bottomWidget = widget
        widget.pack(side = tk.LEFT, fill = tk.X, expand = True)

    def getProfileTab(self):
        return self.profileTab

    def setProfileWidget(self, widget):
        if self.profileWidget is not None:
            self.profileWidget.destroy()
        self.profileWidget = widget
        widget.pack(fill = tk.BOTH, expand = True, padx = 20, pady = 20)

    def getNetworkTab(self):
        return self.networkTab

    def setNetworkWidget(self, widget):
        if self.networkWidget is not None:
            self.networkWidget.destroy()
        self.networkWidget = widget
        widget.pack(fill = tk.BOTH, expand = True, padx = 20, pady = 20)

    def getControlTab(self):
        return self.controlTab

    def setControlWidget(self, widget):
        if self.controlWidget is not None:
            self.controlWidget.destroy()
        self.controlWidget = widget
        widget.pack(fill = tk.BOTH, expand = True, padx = 20, pady = 20)

    def setTitle(self, title):
        self.winfo_toplevel().title(title)

    def tab(self, code):
        """
        Swap to tab with tab code CODE (predefined constant class attribute).
        """
        self.notebook.select(code)

## DEMO ########################################################################
if __name__ == '__main__':
    import splash as spl
    import profile as pro

    print("FC GUI Base demo started")

    # Splash screen:
    S = spl.SplashHandler(spl.FCSplashWidget, 'Demo', width = 750, height = 500,
        useFactor = False)

    S.start()
    tm.sleep(1)
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
