################################################################################
## Project: Fanclub Mark IV "Master" main file ## File: main.py               ##
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
 + FC execution starts here. Launches Core.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import time as tm
import tkinter as tk

from fc.gui import splash as spl, base as bas, profile as pro, network as ntw

## MAIN ########################################################################
# NOTE: Currently a GUI demo 'empty shell'
print("FC MkIV GUI demo started")

# Splash screen:
S = spl.SplashHandler(spl.FCSplashWidget, 'Demo', width = 750, height = 500,
    useFactor = False)

S.start()
tm.sleep(1)
S.stop()

# GUI:
root = tk.Tk()

base = bas.Base(root, title = "FC MkIV Base GUI Demo", version = "Demo")

top = tk.Label(base.getTopBar(), text = "Top Bar")
base.addToTop(top)

profile = pro.ProfileDisplay(base.getProfileTab())
base.setProfileWidget(profile)

network = ntw.NetworkWidget(base.getNetworkTab())
base.setNetworkWidget(network)

netWidget = network.getNetworkControlWidget()
netWidget.addTarget("All", 1)
netWidget.addTarget("Selected", 2)

for message, code in {"Add":1,"Disconnect":2,"Reboot":3, "Remove": 4}.items():
    netWidget.addMessage(message, code)

control = tk.Label(base.getControlTab(), text = "Control Tab")
base.setControlWidget(control)

bot = ntw.StatusBarWidget(base.getBottomFrame())
base.setBottom(bot)

base.pack(fill = tk.BOTH, expand = True)
base.tab(bas.Base.T_CONTROL)

root.mainloop()
print("FC MkIV GUI demo finished")
