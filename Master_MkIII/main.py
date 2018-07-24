################################################################################
## Project: Fanclub Mark II "Master" ## File: main.py  - Main file            ##
##----------------------------------------------------------------------------##
## CALIFORNIA INSTITUTE OF TECHNOLOGY ## GRADUATE AEROSPACE LABORATORY ##     ##
## CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES                             ##
##----------------------------------------------------------------------------##
##      ____      __      __  __      _____      __      __    __    ____     ##
##     / __/|   _/ /|    / / / /|  _- __ __\    / /|    / /|  / /|  / _  \    ##
##    / /_ |/  / /  /|  /  // /|/ / /|__| _|   / /|    / /|  / /|/ /   --||   ##
##   / __/|/ _/    /|/ /   / /|/ / /|    __   / /|    / /|  / /|/ / _  \|/    ##
##  / /|_|/ /  /  /|/ / // //|/ / /|__- / /  / /___  / -|_ - /|/ /     /|     ##
## /_/|/   /_/ /_/|/ /_/ /_/|/ |\ ___--|_|  /_____/| |-___-_|/  /____-/|/     ##
## |_|/    |_|/|_|/  |_|/|_|/   \|___|-    |_____|/   |___|     |____|/       ##
##                   _ _    _    ___   _  _      __   __                      ##
##                  | | |  | |  | T_| | || |    |  | |  |                     ##
##                  | _ |  |T|  |  |  |  _|      ||   ||                      ##
##                  || || |_ _| |_|_| |_| _|    |__| |__|                     ##
##                                                                            ##
##----------------------------------------------------------------------------##
## Alejandro A. Stefan Zavala ## <alestefanz@hotmail.com> ##                  ##
################################################################################

VERSION = "\"MP2\"" # Reference for consecutive versions

#### IMPORTS ###################################################################
# System:
import multiprocessing as mp
import time

# FCMkII:
import FCMainWindow as mw
import FCSpawner as sw
import FCPRCommunicator as cr
import auxiliary.errorPopup as ep
#### MAIN ######################################################################       

print((">>> FCMkII Started on {}".format(time.strftime(
	"%a %d %b %Y %H:%M:%S", time.localtime()))))
"""
# Backup original AutoProxy function
backup_autoproxy = mp.managers.AutoProxy

# Defining a new AutoProxy that handles unwanted key argument 'manager_owned'
def redefined_autoproxy(token, serializer, manager=None, authkey=None,
          exposed=None, incref=True, manager_owned=True):
    # Calling original AutoProxy without the unwanted key argument
    return backup_autoproxy(token, serializer, manager, authkey,
                     exposed, incref)

# Updating AutoProxy definition in mp.managers package
mp.managers.AutoProxy = redefined_autoproxy
"""
try:

	manager = mp.Manager()
	
	commandQueue = manager.Queue()
	misoMatrixQueue  = manager.Queue()
	printQueue = manager.Queue()
	spawnQueue = manager.Queue()	

	spawner = sw.FCSpawner(commandQueue, misoMatrixQueue, spawnQueue, printQueue)
	interface = mw.FCMainWindow(VERSION, commandQueue, misoMatrixQueue, spawnQueue, printQueue) 
	interface.mainloop()
	spawner.end()
except:
	ep.errorPopup("UNHANDLED EXCEPTION AT FCMAIN: ")	

print((">>> FCMkII Ended on {}\n".format(time.strftime(
	"%a %d %b %Y %H:%M:%S", time.localtime()))))
