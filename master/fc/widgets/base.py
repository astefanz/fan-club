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
import tkinter as tk
import tkinter.ttk as ttk

import widget as wg

## AUXILIARY GLOBALS ###########################################################

## MAIN ########################################################################
class Base(wg.FCWidget):

    def __init__(self, master, title = "FC MkIV", version = "N/A"):

        # Core setup -----------------------------------------------------------
        wg.FCWidget.__init__(self, master = master)


        self.screenWidth = self.master.winfo_screenwidth()
        self.screenHeight = self.master.winfo_screenheight()

        self.winfo_toplevel().title(title)
        self.winfo_toplevel().geometry("{}x{}".format(
            self.screenWidth//2, self.screenHeight//2))

        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure(1, weight = 1)

        self.version = version
        # Containers -----------------------------------------------------------
        K = self.kwargs

        # Top bar ..............................................................
        self.topBar = tk.Frame(self, relief = 'ridge', borderwidth = 2)
        self.topBar.grid(row = 0, sticky = 'EW')

        self.caltechImage = tk.PhotoImage(file = "caltech.png")
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
        self.bottomBar = tk.Frame(self, relief = 'ridge', borderwidth = 2)
        self.bottomBar.grid(row = 2, sticky = 'EW')
        self.versionLabel = tk.Label(self.bottomBar,
            text = "Version: \"{}\"".format(self.version))
        self.versionLabel.pack(side = tk.RIGHT, padx = 6)
        self.bottomWidgets = []

    def getTopBar(self):
        return self.topBar

    def addToTop(self, widget):
        self.topWidgets.append(widget)
        widget.pack(side = tk.RIGHT)

    def getBottomBar(self):
        return self.bottomBar

    def addToBottom(self, widget):
        self.bottomWidgets.append(widget)
        widget.pack(side = tk.LEFT)

    def getProfileTab(self):
        return self.profileTab

    def setProfileWidget(self, widget):
        if self.profileWidget is not None:
            self.profileWidget.destroy()
        self.profileWidget = widget
        widget.pack(fill = tk.BOTH, expand = True)

    def getNetworkTab(self):
        return self.networkTab

    def setNetworkWidget(self, widget):
        if self.networkWidget is not None:
            self.networkWidget.destroy()
        self.networkWidget = widget
        widget.pack(fill = tk.BOTH, expand = True)

    def getControlTab(self):
        return self.controlTab

    def setControlWidget(self, widget):
        if self.controlWidget is not None:
            self.controlWidget.destroy()
        self.controlWidget = widget
        widget.pack(fill = tk.BOTH, expand = True)

    def setTitle(self, title):
        self.winfo_toplevel().title(title)

## DEMO ########################################################################
if __name__ == '__main__':

    print("FC GUI Base demo started")
    root = tk.Tk()
    base = Base(root, title = "FC MkIV Base GUI Demo", version = "Demo")

    top = tk.Label(base.getTopBar(), text = "Top Bar")
    base.addToTop(top)

    profile = tk.Label(base.getProfileTab(), text = "Profile Tab")
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
