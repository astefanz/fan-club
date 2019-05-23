#!/usr/bin/python3 #############################################################
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
import multiprocessing as mp

import fc.tkgui as tkg
import fc.archive as ac
import fc.communicator as cm
import fc.utils as us
import fc.builtin.profiles as btp

## GLOBALS #####################################################################
VERSION = "0.9"
INIT_PROFILE = "BASE" # FIXME

## MAIN ########################################################################
print(us.HEADER)

# FIXME: reminders
print("[REM] Look into 'memory leak' in profile switches and data path")
print("[REM] Look into control after profile switching ('return 1')")
print("[REM] Pass profiles, not archive, when profile changes will cause reset")
print("[REM] Change all watchdog threads to Tkinter 'after' scheduling")
print("[REM] Indexing by 1 in functional input")
print("[REM] Standardize notation (also: function argument consistency)")
print("[REM][control] display time counter in dynamic flow")
print("[REM] period_ms abstraction barrier in FCInterface")

pqueue = mp.Queue()
archive = ac.FCArchive(pqueue, VERSION)
archive.profile(btp.PROFILES[INIT_PROFILE])
interface = tkg.FCGUI(archive, pqueue)
interface.run()

print("[--] FC MkIV GUI demo finished") # FIXME
