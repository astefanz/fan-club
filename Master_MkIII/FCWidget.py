################################################################################
## Project: Fan Club Mark II "Master" # File: FCWidget.py                     ##
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
Base class for FCMkII GUI Widgets

"""
################################################################################


## DEPENDENCIES ################################################################

# GUI:
import tkinter as Tk

# System:
import multiprocessing as mp
import threading as tr

# FCMkII:
import FCSpawner as sw
import auxiliary.errorPopup as ep
import traceback

## AUXILIARY DEFINITIONS #######################################################

# Status codes:
ACTIVE = 1
STARTING = 2
INACTIVE = 3
STOPPING = 4

# Update index codes:
TARGET = 0
COMMAND = 1
VALUE = 2

# Update command-codes:
STOP = 1

def translate(code): # ---------------------------------------------------------
	# Get string representing FCWidget status code

	if code is ACTIVE:
		return "ACTIVE"
	elif code is STARTING:
		return "STARTING"
	elif code is INACTIVE:
		return "INACTIVE"
	elif code is STOPPING:
		return "STOPPING"
	else:
		return "[UNKNOWN CODE ({})]".format(code)

	# End translate ------------------------------------------------------------

## CLASS DEFINITION ############################################################

class FCWidget(Tk.Frame):
	
	def __init__(
		self, 
		master,
		process,	
		profile,

		spawnQueue,
		printQueue,
		specialArguments = (),
		
		symbol = "WG"
		): # ===================================================================
	
		self.canPrint = False

		try:
			Tk.Frame.__init__(self, master)
			self.master = master
			self.symbol =  "[{}] ".format(symbol)
			self.printQueue = printQueue
			self.canPrint = True

			# Store arguments:
			self.process = process
			self.specialArguments = specialArguments
			self.specialArgumentsLock = tr.Lock()
			self.profile = profile
			self.profileLock = tr.Lock()
			self.spawnQueue = spawnQueue

			# Create member attributes:
			self.updatePipeOut, self.updatePipeIn = mp.Pipe(False)
			self.misoMatrixPipeOut, self.misoMatrixPipeIn = mp.Pipe(False)

			# Pipes for inter-process communication:
			self.spawnPipeOut, self.spawnPipeIn = mp.Pipe(False)
		
			# Standard process arguments (pipes):
			self.standardArguments = \
				(self.profile, self.updatePipeOut, self.misoMatrixPipeOut)

			# Status:
			self.status = INACTIVE
			self.statusLock = tr.Lock()

			# Start watchdog thread:
			self.watchdogThread = None
			
			# Launch periodic updates:
			self._periodicUpdate()


		except Exception as e:

			if not self.canPrint:
				ep.errorPopup("Exception in base FCWidget constructor:")

			else:
				self._printM(
					"ERROR: {}".format(traceback.format_exc()), 'E')

		# End __init__ =========================================================


	def start(self): # =========================================================
		# Start process, if possible
		try:

			# Check status
			if self.getStatus() is INACTIVE:
				# Can start process	

				# Set status to starting:
				self._setStatus(STARTING)
				self.specialArgumentsLock.acquire()	
				self.spawnQueue.put_nowait(
					(
						self.process, 
						self.standardArguments + self.specialArguments,
						self.spawnPipeIn
					)
				)
				
				self._startWatchdog()
			else:
				# Cannot start process
				self._printM(
					"WARNING: Tried to start non-inactive widget", 'E')


		except Exception as e:
			self._printE(e, "Error in start:")

		finally:
			try:
				self.specialArgumentsLock.release()
			except:
				pass

		# End start ============================================================

	def stop(self): # ==========================================================
		# Stop process, if possible
		try:
			# Check status
			if self.getStatus() is ACTIVE:
				# Can start process
				
				# Set status to starting:
				self._setStatus(STOPPING)

				# Send stop signal:
				self.updatePipeIn.send((None, STOP,))

				self._startWatchdog()
			else:
				# Cannot start process
				self._printM(
					"WARNING: Tried to stop non-active widget", 'W')

		except Exception as e:
			self._printE(e, "Error in stop:")
		
		# End stop =============================================================

	def updateIn(self, update): # ==============================================
		# Input a new update tuple
		# NOTE: incoming update tuples will be ignored whenever the process is
		# inactive

		if self.getStatus() is ACTIVE:
			self.updatePipeIn.send(update)

		else:
			del update

		# End updateIn =========================================================

	def misoMatrixIn(self, matrix): # ==========================================
		# Input a new MISO matrix
		# NOTE: incoming matrices will be ignored whenever the process is 
		# inactive.


		if self.getStatus() is ACTIVE:
			self.misoMatrixPipeIn.send(matrix)

		else:
			del matrix

		# End misoMatrixIn =====================================================


	def _setStatus(self, newStatus): # =========================================
		try:

			self.statusLock.acquire()
			self.status = newStatus

		except Exception as e:
			self._printE(e, "Error in _setStatus:")
		
		finally:
			self.statusLock.release()

		# End _setStatus =======================================================

	def getStatus(self): # =====================================================
		try:
			self.statusLock.acquire()
			status = self.status
			return status
		
		except Exception as e:
			self._printE(e, "Error in getStatus:")
		
		finally:
			self.statusLock.release()

		# End getStatus ========================================================

	def _setSpecialArguments(self, newSpecialArguments): # =====================
		try:

			self.specialArgumentsLock.acquire()
			self.specialArguments = newSpecialArguments

		except Exception as e:
			self._printE(e, "Error in _setSpecialArguments:")
		
		finally:
			self.specialArgumentsLock.release()

		# End _setSpecialArguments =============================================

	def getSpecialArguments(self): # ===========================================
		try:
			self.specialArgumentsLock.acquire()
			specialArguments = self.specialArguments
			return specialArguments
		
		except Exception as e:
			self._printE(e, "Error in getSpecialArguments:")
		
		finally:
			self.specialArgumentsLock.release()

		# End getSpecialArguments ==============================================
	
	def _setProfile(self, newProfile): # =======================================
		try:

			self.profileLock.acquire()
			self.profile = newProfile

		except Exception as e:
			self._printE(e, "Error in _setProfile:")
		
		finally:
			self.profileLock.release()

		# End _setProfile ======================================================

	def getProfile(self): # ====================================================
		try:
			self.profileLock.acquire()
			profile = self.profile
			return profile
		
		except Exception as e:
			self._printE(e, "Error in getProfile:")
		
		finally:
			self.profileLock.release()

		# End getProfile =======================================================

	def _printM(self, message, tag = 'S'): # ===================================
		try:
			if self.canPrint:
				self.printQueue.put_nowait((self.symbol + message, tag))
			
			else:
				ep.errorPopup("Could not print")

		except Exception as e:
			ep.errorPopup("Exception is base FCWidget print:")

		# End _printM ==========================================================

	def _printE(self, exception, preamble = 'ERROR:'): # =======================
		try:
			self._printM("{} {}".format(preamble, traceback.format_exc()), 'E')
		
		except Exception as e:
			ep.errorPopup("Exception is base FCWidget print-E:")	

		# End _printE ==========================================================

	def _startWatchdog(self): # ================================================

		# Verify status:
		status = self.getStatus()
		if status in (STARTING, STOPPING) and \
			(self.watchdogThread is None or not self.watchdogThread.is_alive()):	
			
			self.watchdogThread = tr.Thread(
				name = "FCMkII_watchdog",
				target = self._watchdogRoutine
			)
			self.watchdogThread.setDaemon(True)
			self.watchdogThread.start()
		
		elif self.watchdogThread is not None:
			raise RuntimeError("Tried to start watchdog atop active thread")	
			
		else:
			raise RuntimeError("Tried to start watchdog w/ invalid status "\
				"({})".format(translate(status)), 'E')

	def _watchdogRoutine(self): # ==============================================
		self._printM("Watchdog started", 'D')

		while True:
			try:
				# Listen for spawner notifications:
				if self.spawnPipeOut.poll():
					message = self.spawnPipeOut.recv()
					status = self.getStatus()

					if message is sw.STARTED and status is STARTING:
						# Widget successfully activated:
						self._setStatus(ACTIVE)
						break

					elif message is sw.STOPPED and status is STOPPING:
						# Widget successfully stopped:
						self._setStatus(INACTIVE)
						break

					elif message is sw.ERROR:
						self._printM("WARNING: Failed to start process", 'E')
						self._setStatus(INACTIVE)
						break

					else:
						# Invalid combination:
						self._printM(
							"WARNING: Invalid spawner message / status "\
							"combination --- got \"{}\" while \"{}\"".\
							format(
								sw.translate(message), translate(status)))
						break
			except Exception as e:
				self._printE(e, "ERROR in watchdog:")

		self._printM("Watchdog ended", 'D')
		# _watchdogRoutine =====================================================

	def _updateMethod(self): # =================================================
		# NOTE: To be overridden by child classes
		pass

		# ======================================================================

	def _periodicUpdate(self): # ===============================================
		# Use Tkinter's "after" to schedule periodic updates and check
		# Process status.	
		try:

			# Check status:
			if self.getStatus() is not ACTIVE:
				return

			elif self.spawnPipeOut.poll():
				message = self.spawnPipeOut.recv()
				if message is sw.STOPPED:
					self._setStatus(INACTIVE)

			else:
				self._updateMethod()

		except:
			self._printE("ERROR in scheduled Comms. Updater:")
	
		finally: 
			self.after(100, self._periodicUpdate)

		# End _periodicUpdate # ================================================



