################################################################################
## Project: Fan Club Mark II "Master" # File: FCSpawner.py                    ##
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
Process manager for FCMkII

"""
################################################################################


## DEPENDENCIES ################################################################

# Systen:
import multiprocessing as mp
import threading as tr

# FCMkII:	
import auxiliary.errorPopup as ep
import traceback

## AUXILIARY DEFINITIONS #######################################################

def _spawnerRoutine(stopPipeOut, spawnQueue, printQueue): # ====================

	# SETUP --------------------------------------------------------------------

	canPrint = True

	def _printM(message, tag = 'S'): # =========================================
		printQueue.put_nowait(("[SR] " + message, tag))

		# End _printM ==========================================================

	def _printE(message = "SPAWNER-R ERROR"): # ================================
		try:
			exception = traceback.format_exc() 
			if canPrint and exception != 'None\n':
				_printM("{}: {}".format(message, exception), 'E')

			elif exception == 'None\n':
				_printM(message, 'E')

			else:
				ep.errorPopup(Exception(), 
					"SPAWNER ERROR: " + exception)

		except:
			ep.errorPopup("Exception is base FCWidget print-E:")	

		# End _printE ==========================================================
		
	_printM("Spawner ready", 'G')

	processTuples = []

	# MAIN LOOP ----------------------------------------------------------------
	while True:
		try:
		
			# Check input on each loop

			# Check stop pipe:
			if stopPipeOut.poll():
				spMessage = stopPipeOut.recv()
				if spMessage is 1:
					# End process

					_printM("Ending Spawner")
					for processTuple in processTuples:
						if processTuple[PROCESS].is_alive():
							_printM(
								"WARNING: Ending Spawner w/ live processes",'E')

					_printM("Spawner ended")
					break

				else:
					_printM("WARNING: Invalid stopPipe message \"{}\"".\
						format(spMessage),'E')
					# Bad stopPipe message
			
			# Check Queue:
			if not spawnQueue.empty():
				spawnTuple = spawnQueue.get_nowait()
				# NOTE: See auxiliary definitions at FCSpawner source for the 
				# expected form of a spawnTuple

				# Add new process:
				try:
					print "Something was received: {}".format(spawnTuple)
					
					newProcess = mp.Process(
						name = "FCMkII_Widget",
						target = spawnQueue[TARGET],
						args = spawnQueue[ARGS]
					)
					newProcess.daemon = True
					
					newProcess.start()

					# Notify widget:
					spawnTuple[PIPE].send(STARTED)

					processTuples.append(spawnTuple + (newProcess,)) 
					_printM("New process spawned", 'G')

				except:
					_printE("Error when spawning new process:")
					
					try:
						newProcess.terminate()
					except:
						pass

					try:
						spawnTuple[PIPE].send(ERROR)
					except:
						_printE()
						_printM("WARNING: Could not send error message for "\
							"spawn request")

			# Check running processes:
			for i in range(len(processTuples)-1, -1, -1):
				# NOTE: This loop will traverse processTuples backwards to allow
				# deletion of elements w/o index errors

				if not processTuples[i][PROCESS].is_alive():
					# Process ended, send notification to handler and delete it
					# from the process list

					processTuple[i][PIPE].send(STOPPED)
					
					# Delete from list:
					del processTuple[i]		

		except:
			_printE()
	

	# End _spawnerRoutine ======================================================

# Command codes:
STARTED = 11
STOPPED = 12
ERROR = 13

def translate(code): # ---------------------------------------------------------
	# Get string representing Spawner integer code

	if code is START:
		return "START"
	
	elif code is STOP:
		return "STOP"

	elif code is ERROR:
		return "ERROR"

	else:
		return "[UNKNOWN CODE ({})]"
	
	# End translate ------------------------------------------------------------

# Spawn tuple:
# Expected form: 			(target_method)
#								0
# NOTE: Here args is expected to be a tuple of arguments to be passed to
# target_method

# Resource dictionary:
PIPE = -1
PROCESS = -2
MP_ARGS = -3

# EXPECTED PROCESS ARGUMENT ORDER:
# shutdownPipe
# commandQueue
# MOSI Queue
# printQueue
# INTERPROCESS_ARGS
# SERIALIZABLE_ARGS

SPAWNER_SIDE = 0
CALLER_SIDE = 1

## CLASS DEFINITION ############################################################

class FCSpawner:

	def __init__(self, spawnQueue, printQueue): # ==============================
		self.canPrint = False
		self.symbol = "[SW] "
		try:
			
			self.printQueue = printQueue
			self.canPrint = True
			self.active = False

			# Inter-process communication:
			self.spawnQueue = spawnQueue
			self.stopPipeOut, self.stopPipeIn = mp.Pipe(False)

			# Process:
			self.spawnerProcess = mp.Process(
				name = "FCMkII_Spawner",
				target = _spawnerRoutine,
				args = (self.stopPipeOut, self.spawnQueue, printQueue)
			)

			self.spawnerProcess.start()
			self.active = True

		except:
			self._printE("SPAWNER INIT. ERROR")
			# NOTE: traceback.format_exc() will automatically fetch the latest
			# Exception data
	
		# End __init__ =========================================================

	def getSpawnQueue(self): # =================================================
		return self.spawnQueue
		# End getSpawnQueue ====================================================

	def end(self): # ===========================================================
		self.stopPipeIn.send(1)
		self.spawnerProcess.join(2)
		if self.spawnerProcess.is_alive():
			self.terminate()

		self.active = False

		# End end ==============================================================

	def terminate(self): # =====================================================
		self.spawnerProcess.terminate()
		self._printE("WARNING: Spawner process terminated")
		self.active = False

		# End terminate ========================================================

	def _printM(self, message, tag = 'S'): # ===================================
		try:
			if self.canPrint:
				self.printQueue.put_nowait((self.symbol + message, tag))
			elif tag is 'E':
				self._printE(message)

		except:
			self._printE("Exception is base FCWidget print:")

		# End _printM ==========================================================

	def _printE(self, message = "SPAWNER ERROR"): # ============================
		try:
			exception = traceback.format_exc() 
			if self.canPrint and exception is not 'None\n':
				self._printM("{}: {}".format(message, exception), 'E')

			elif exception is 'None\n':
				self._printM(message, 'E')

			else:
				ep.errorPopup(Exception(), 
					"SPAWNER ERROR: " + exception)

		except:
			ep.errorPopup(e, "Exception is base FCWidget print-E:")	

		# End _printE ==========================================================
