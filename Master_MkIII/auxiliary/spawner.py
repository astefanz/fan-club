################################################################################
## Project: Fan Club Mark II "Master" ## File: spawner.py                     ##
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

## ABOUT #######################################################################
"""
Method for "indirectly" spawning processes, used as a workaround for X 
limitations on Unix

"""
################################################################################

## DEPENDENCIES ################################################################
import multiprocessing as pr

## DEFINITION ##################################################################

def _spawnRoutine(givenTarget, givenArgs = None): # ============================

	print(" in spawn routine")
	if givenArgs is not None:
		newProcess = pr.Process(target = givenTarget, args = givenArgs)

	else:
		newProcess = pr.Process(target = givenTarget)

	print("spawning process")
	newProcess.start()
	print("spawnRoutine done")

	# End _spawnRoutine ========================================================

def spawn(givenTarget, givenArgs = None): # ====================================
	print("in spawn")
	spawnProcess = pr.Process(
		target = _spawnRoutine, args = (givenTarget, givenArgs))
	
	spawnProcess.start()
	print("joining spawnProcess")
	spawnProcess.join()
	print("spawn done")

	# End spawn ================================================================
