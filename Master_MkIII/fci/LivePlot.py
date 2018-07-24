################################################################################
## Project: Fan Club Mark II "Master" ## File: LiveTable.py                   ##
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
Display RPM matrix live.

"""
################################################################################

## DEPENDENCIES ################################################################

#from mttkinter import mtTkinter as Tk
import tkinter as Tk
import tkinter.ttk

# System:
import sys			# Exception handling
import traceback	# More exception handling
import random		# Random names, boy
import resource		# Socket limit
import threading	# Multitasking
import _thread		# thread.error
import multiprocessing as pr # The big guns

# Data:
import time			# Timing
import queue
import numpy as np	# Fast arrays and matrices
import random

# FCMkII:
import FCCommunicator as cm
import FCSlave as sv
import FCWidget as wg
import FCArchiver as ac

## AUXILIARY DEFINITIONS #######################################################

class LiveTableWidget(Tk.Frame):

	def __init__(self, 
		profile,
		numSlaves, 
		maxFans, 
		stopPipeOut,
		misoMatrixPipeOut,
		commandQueue,
		printQueue
		): # ===================================================================

		Tk.Frame.__init__(self)

		self.normalTitle = "FCMkII Live Table"
		self.printingTitle = "FCMkII Live Table [PRINTING]"
		self.master.title(self.normalTitle)
		self.commandQueue = commandQueue
		self.printQueue = printQueue

		self._printM("Building Live Table")

		self.profile = profile
		self.numSlaves = numSlaves
		self.maxFans = maxFans
		
		self.misoMatrixPipeOut = misoMatrixPipeOut
		self.stopPipeOut = stopPipeOut

		self.latestMatrix = []
		self.lastPrintedMatrix = 0

		# Build top bar --------------------------------------------------------
		# Set background:
		self.bg = "#e2e2e2"
		self.fg = "black"
		self.config(bg = self.bg)

		self.topBar = Tk.Frame(
			self,
			bg = self.bg,
		)
		
		self.playPauseFlag = True
		self.playPauseButton = Tk.Button(
			self.topBar,
			bg = self.bg,
			highlightbackground = self.bg,
			fg = self.fg,
			text = "Pause",
			width = 10,
			command = self._playPause
		)
		self.bind("<space>", self._playPause)
		self.master.bind("<space>",self._playPause)

		self.playPauseButton.pack(side = Tk.LEFT)
	
		self.printThread = None
		self.donePrinting = False
		self.printMatrixButton = Tk.Button(
			self.topBar,
			bg = self.bg,
			highlightbackground = self.bg,
			fg = self.fg,
			text = "Print",
			width = 10,
			command = self._printMatrix,
		)
		self.master.bind("<Control-P>",self._printMatrix)
		self.master.bind("<Control-p>",self._printMatrix)

		self.wasPaused = False
		self.printMatrixButton.pack(side = Tk.LEFT)	

		self.counterVarLabel = Tk.Label(
			self.topBar,
			text = "    Matrix: ",
			fg = self.fg,
			bg = self.bg
		)
		self.counterVarLabel.pack(side = Tk.LEFT)
		
		self.matrixCount = 0
		self.counterVar = Tk.IntVar()
		self.counterVar.set(0)
		self.counterLabel = Tk.Label(
			self.topBar,
			textvariable = self.counterVar,
			relief = Tk.SUNKEN,
			bd = 1,
			bg = self.bg,
			fg = self.fg,
			width = 10
		)
		self.counterLabel.pack(side = Tk.LEFT)

		self.timerSeconds = 0
		self.timerMinutes = 0
		self.timerHours = 0

		self.timeStampSeconds = 0
		self.timeStampMinutes = 0
		self.timeStampHours = 0

		self.timerVarLabel = Tk.Label(
			self.topBar,
			text = "    Time stamp: ",
			fg = self.fg,
			bg = self.bg
		)
		self.timerVarLabel.pack(side = Tk.LEFT)

		self.timerVar = Tk.StringVar()
		self.timerVar.set("00:00:00")
		self.timerLabel = Tk.Label(
			self.topBar,
			textvariable = self.timerVar,
			relief = Tk.SUNKEN,
			bd = 1,
			bg = self.bg,
			fg = self.fg,
			font = ('TkFixedFont',12),
			width = 10
		)
		self.timerLabel.pack(side = Tk.LEFT)
	
		# Sentinel .............................................................
		self.sentinelWidgets = []
		self._sentinelCheck = lambda x: False

		self.sentinelFrame = Tk.Frame(
			self.topBar,
			bg = self.bg,
		)
		
		self.sentinelLabel = Tk.Label(
			self.sentinelFrame,
			bg = self.bg,
			fg = self.fg,
			text = "    Watchdog: ",
			font = ("TkStandardFont", 14)
		)
		self.sentinelLabel.pack(side = Tk.LEFT)

		self.sentinelSecondaryLabel = Tk.Label(
			self.sentinelFrame,
			bg = self.bg,
			fg = self.fg,
			text = " When an RPM is "
		)
		self.sentinelSecondaryLabel.pack(side = Tk.LEFT)
		
		self.sentinelMenuVar = Tk.StringVar()
		self.sentinelMenuVar.set("Above")
		self.sentinelMenu = Tk.OptionMenu(
			self.sentinelFrame,
			self.sentinelMenuVar,
			"Above",
			"Below",
			"Outside 10% of",
			"Within 10% of",
			"Not"
		)
		self.sentinelMenu.configure(
			highlightbackground = self.bg,
			bg = self.bg,
			width = 10
		)
		self.sentinelMenu.pack(side = Tk.LEFT)
		self.sentinelWidgets.append(self.sentinelMenu)

		validateC = self.register(self._validateN)
		self.sentinelEntry = Tk.Entry(self.sentinelFrame, 
			highlightbackground = self.bg,
			bg = 'white',
			fg = self.fg,
			width = 7, validate = 'key', validatecommand = \
				(validateC, '%S', '%s', '%d'))
		self.sentinelEntry.insert(0,'0')
		self.sentinelEntry.pack(side = Tk.LEFT)
		self.sentinelWidgets.append(self.sentinelEntry)
		
		self.sentinelTerciaryLabel = Tk.Label(
			self.sentinelFrame,
			bg = self.bg,
			fg = self.fg,
			text = " RPM   "
		)
		self.sentinelTerciaryLabel.pack(side = Tk.LEFT)
		
		self.sentinelActionMenuVar = Tk.StringVar()
		self.sentinelActionMenuVar.set("Highlight")
		self.sentinelActionMenu = Tk.OptionMenu(
			self.sentinelFrame,
			self.sentinelActionMenuVar,
			"Warn me",
			"Highlight",
			"Shut down",
		)
		self.sentinelActionMenu.configure(
			highlightbackground = self.bg,
			bg = self.bg,
			width = 13
		)
		self.sentinelActionMenu.pack(side = Tk.LEFT)
		self.sentinelWidgets.append(self.sentinelActionMenu)
		
		self.sentinelPauseVar = Tk.BooleanVar()
		self.sentinelPauseVar.set(True)
		self.sentinelPauseButton = Tk.Checkbutton(
			self.sentinelFrame, 
			text ="Freeze table", 
			variable = self.sentinelPauseVar, 
			bg = self.bg, 
			fg = self.fg)
		self.sentinelPauseButton.pack(side = Tk.LEFT)
		self.sentinelWidgets.append(self.sentinelPauseButton)

		self.sentinelPrintVar = Tk.IntVar()
		self.sentinelPrintButton = Tk.Checkbutton(
			self.sentinelFrame, 
			text ="Print table", 
			variable = self.sentinelPrintVar, 
			bg = self.bg, 
			fg = self.fg)
		self.sentinelPrintButton.pack(side = Tk.LEFT)
		self.sentinelWidgets.append(self.sentinelPrintButton)

		self.sentinelApplyButton = Tk.Button(
			self.sentinelFrame,
			bg = self.bg,
			highlightbackground = self.bg,
			fg = self.fg,
			text = "Apply",
			width = 6,
			command = self._applySentinel,
			state = Tk.NORMAL
		)
		self.sentinelApplyButton.pack(side = Tk.LEFT)
 
		self.sentinelClearButton = Tk.Button(
			self.sentinelFrame,
			bg = self.bg,
			highlightbackground = self.bg,
			fg = self.fg,
			text = "Clear",
			width = 6,
			command = self._clearSentinel,
			state = Tk.DISABLED
		)
		self.sentinelClearButton.pack(side = Tk.LEFT)

		self.sentinelFrame.pack(side = Tk.RIGHT)
		self.sentinelFlag = False

		self.topBar.pack(side = Tk.TOP, fill = Tk.X, expand = True)
		# Build table ----------------------------------------------------------

		# Add columns:

		self.table = tkinter.ttk.Treeview(
			self,
			selectmode = 'none',
			height = 32
		)
		self.columns = ("Index", "Max", "Min")
		self.specialColumns = len(self.columns)

		self.zeroes = ()
		for fanNumber in range(maxFans):
			self.columns += ("Fan {}".format(fanNumber+1),)
			self.zeroes += (0,)

		self.table['columns'] = self.columns

		self.table.column("#0", width = 20, stretch = False)

		for column in self.columns:	
			self.table.column(column, width = 70, anchor = "center")
			self.table.heading(column, text = column)

		# Configure tags:
		self.table.tag_configure(
			"H", # Highlight
			background= '#fffaba',
			foreground ='#44370b',
			font = 'TkFixedFont 12 bold'
		)
		
		self.table.tag_configure(
			"D", # Disconnected
			background= '#fffaba',
			foreground ='#44370b',
			font = 'TkFixedFont 12 bold'
		)
		
		self.table.tag_configure(
			"N", # Normal
			background= 'white',
			foreground ='black',
			font = 'TkFixedFont 12'
		)

		# Add rows and build slave list:
		self.slaves = {}
		for index in range(numSlaves):
			self.slaves[index] = self.table.insert(
					'', 
					'end',
					values = (
						index + 1,
						) + self.zeroes,
					tag = "N"
			)

		self.table.pack(fill = Tk.BOTH, expand = True)

		# Pack -----------------------------------------------------------------
		self.pack(fill = Tk.BOTH, expand = True)

		self._updateChecker()
		self._timer()

		self._printM("Live Table online", "G")

		# End __init__ =========================================================


	def matrixIn(self, matrix): # ==============================================
		
		if self.playPauseFlag:
			# Check matrix size (number of slaves):
			if len(matrix) > self.numSlaves:
				for newIndex in range(self.numSlaves, len(matrix)):
					print("Adding index ", newIndex)
					self.slaves[newIndex] = self.table.insert(
							'', 
							'end',
							values = (
								newIndex + 1,
								) + self.zeroes,
							tag = "N"
					)

				self.numSlaves += 1

			# Now update RPMS:
			for index, matrixRow in enumerate(matrix):
				tag = "N"
				if matrixRow[0] is not sv.CONNECTED:
					newValues = self.zeroes
					tag = "D"
				else:
					newValues = tuple(matrixRow[1:self.maxFans+1])
					maxValue = max(matrixRow[1:self.maxFans+1])
					minValue = min(matrixRow[1:self.maxFans+1])
					if self.sentinelFlag:
						for fan, value in enumerate(newValues):
							if self._sentinelCheck(value):
								tag = "H"
								self._executeSentinel(index,fan,value)
								

				self.table.item(
					self.slaves[index], # <-- IID
					values = (index+1,maxValue,minValue) + newValues,
					tag = tag	
				)
		
			# Increment counter and store matrix:
			self.counterVar.set(self.matrixCount)
			self.latestMatrix = matrix

		else:
			# Paused. Discard matrix
			del matrix
			pass
		self.matrixCount += 1

		# End matrixIn =========================================================

	def _applySentinel(self, event = False): # =================================
		try:
			if self.sentinelEntry.get() != '':
				self.sentinelFlag = True	
				self.sentinelApplyButton.config(state = Tk.DISABLED)
				
				self._sentinelCheck = self._assembleSentinel()
				
				for widget in self.sentinelWidgets:
					widget.config(state = Tk.DISABLED)
				self.sentinelClearButton.config(state = Tk.NORMAL)
		except:
			self._printM("ERROR In A.S.: {}".format(traceback.format_exc()),'E')

		# End _applySentinel ===================================================

	def _executeSentinel(self, targetSlave, targetFan, RPM): # =================

		# Action:
		action = self.sentinelActionMenuVar.get()
		
		if action == "Highlight row(s)":
			pass

		elif action == "Warn me":
			self._printM("WARNING: Module {}, Fan {} at "\
				"{} RPM".format(targetSlave + 1, targetFan, RPM),'E')

		elif action == "Shut down":
			self.commandQueue.put_nowait((cm.ALL,cm.REBOOT))
			if self.playPauseFlag:
				self._playPause()

			self._printM("WARNING: Shutdown triggered by Module {}, Fan {} "\
				"({} RPM)".format(targetSlave + 1, targetFan, RPM), 'E')

		# Print (and avoid printing the same matrix twice):
		if self.sentinelPrintVar.get() and \
			self.lastPrintedMatrix < self.matrixCount:
			self._printMatrix(sentinelValues = (targetFan,targetSlave,RPM))	
			print("{} != {}".format(self.lastPrintedMatrix, self.matrixCount))
			self.lastPrintedMatrix = self.matrixCount

		# Pause:
		if self.sentinelPauseVar.get() and self.playPauseFlag:
			self._playPause()

		# End _executeSentinel =================================================

	def _assembleSentinel(self): # =============================================

		check = self.sentinelMenuVar.get()
		value = int(self.sentinelEntry.get())
		
		if check == "Above":
			
			return lambda rpm : rpm > value

		elif check == "Below":

			return lambda rpm : rpm < value

		elif check == "Outside 10% of":

			return lambda rpm : rpm > value*1.1 or rpm < value*.9

		elif check == "Within 10% of":
			
			return lambda rpm : rpm < value*1.1 and rpm > value*.9

		elif check == "Not":

			return lambda rpm : rpm != value

		# End _assembleSentinel ================================================

	def _clearSentinel(self, event = False): # =================================
		self.sentinelFlag = False
		self.sentinelClearButton.config(state = Tk.DISABLED)
		for widget in self.sentinelWidgets:
			widget.config(state = Tk.NORMAL)
		self.sentinelApplyButton.config(state = Tk.NORMAL)

		# End _clearSentinel ===================================================

	def _updateChecker(self): # ================================================

		try:

			if self.misoMatrixPipeOut.poll():
				self.matrixIn(self.misoMatrixPipeOut.recv())

		except:
			self._printM(
				"ERROR in Live Table updater: " + traceback.format_exc(),'E')

		finally:	
			self.after(100, self._updateChecker)

		# End updateChecker ====================================================

	def _timer(self): # ========================================================
		
		try:
			
			self.timerSeconds += 1

			if self.timerSeconds >= 60:
				self.timerSeconds = 0
				self.timerMinutes += 1
				
			if self.timerMinutes >= 60:
				self.timerMinutes = 0
				self.timerHours += 1

			if self.playPauseFlag:
				self.timeStampSeconds = self.timerSeconds
				self.timeStampMinutes = self.timerMinutes
				self.timeStampHours = self.timeStampHours

			self.timerVar.set("{:02d}:{:02d}:{:02d}".\
				format(
					self.timeStampHours,
					self.timeStampMinutes,
					self.timeStampSeconds))

		except:
			self._printM("ERROR in timer: " + traceback.format_exc(), 'E')

		finally:
			self.after(1000, self._timer)

		# End _timer ===========================================================
	
	def _validateN(self, newCharacter, textBeforeCall, action): # ==============
		# ABOUT: To be used by TkInter to validate text in "Send" Entry.
		if action == '0':
			return True

		elif newCharacter in '0123456789':
			return True

		else:
			return False


	def _printMatrix(self, event = None, sentinelValues = None): # =============

		if self.playPauseFlag:
			self.wasPaused = False
			self._playPause()

		else:
			self.wasPaused = True

		# Lock table ...........................................................
		self.playPauseButton.config(state = Tk.DISABLED)
		self.printMatrixButton.config(state = Tk.DISABLED)

		if not self.sentinelFlag:
			for widget in self.sentinelWidgets:
				widget.config(state = Tk.DISABLED)
			self.sentinelApplyButton.config(state = Tk.DISABLED)

		else:
			self.sentinelClearButton.config(state = Tk.DISABLED)
		
		self.master.title(self.printingTitle)

		# Print ................................................................
		self.donePrinting = False

		self.printThread = threading.Thread(
			name = "FCMkII_LT_Printer",
			target = self._printRoutine,
			args = (sentinelValues,)
		)
		self.printThread.setDaemon(True)
		self.printThread.start()

		self._printChecker()
		
	
		# End _printMatrix =====================================================

	def _printChecker(self): # =================================================
		
		if not self.donePrinting: 
			self.after(100, self._printChecker)

		else:
			# Unlock table .....................................................
			self.playPauseButton.config(state = Tk.NORMAL)
			self.printMatrixButton.config(state = Tk.NORMAL)

			if not self.sentinelFlag:
				for widget in self.sentinelWidgets:
					widget.config(state = Tk.NORMAL)
				self.sentinelApplyButton.config(state = Tk.NORMAL)
				if not self.wasPaused:
					self._playPause()

			else:
				self.sentinelClearButton.config(state = Tk.NORMAL)
				if not self.sentinelPauseVar.get():
					self._playPause()
			
			self.master.title(self.normalTitle)	
			
		# End _printChecker ====================================================

	def _printRoutine(self, sentinel = None): # ================================
		
		try:	
			fileName = "FCMkII_table_print_on_{}.csv".format(
				time.strftime("%a_%d_%b_%Y_%H:%M:%S", time.localtime())) 

			self._printM("Printing to file")

			with open(fileName, 'w') as f:
				# File setup ...................................................
				
				f.write("Fan Club MkII data launched on {}  using "\
					"profile \"{}\" with a maximum of {} fans.\n"\
					"Timestamp (since live table was launched): {}"\
					"Matrix number (since live table was launched): {}\n\n".\
					format(
						time.strftime(
							"%a %d %b %Y %H:%M:%S", time.localtime()), 
						self.profile[ac.name],
						self.profile[ac.maxFans],
						self.timerVar.get(),
						self.matrixCount
						)
					)

				if sentinel is not None:
					f.write("NOTE: This data log was activated by a watchdog "\
						"trigger caused by fan {} of module {} being "\
						"measured at {} RPM "\
						"(Condition: \"{}\" if \"{}\" {} RPM)\n".\
						format(
							sentinel[0]+1,	# Fan
							sentinel[1]+1,	# Slave
							sentinel[2],	# RPM value
							self.sentinelActionMenuVar.get(),
							self.sentinelMenuVar.get(),
							self.sentinelEntry.get()
							)
					)
			
				# Headers (fifth line):

				# Write headers:
				f.write("Module,")
				
				for column in self.columns[self.specialColumns:]:
					f.write("{} RPM,".format(column))

				# Move to next line:
				f.write('\n')

				# Write matrix:
				for index, row in enumerate(self.latestMatrix):
					f.write("{},".format(index+1))
					for value in row[1:]:
						f.write("{},".format(value))

					f.write('\n')

			self.donePrinting = True
			self._printM("Done printing",'G')

		except:
			self._printM("ERROR When printing matrix: {}".\
				format(traceback.print_exc()),'E')
			self.donePrinting = True

		# End _printRoutine ====================================================

	def _playPause(self, event = None, force = None): # ========================

		if self.playPauseFlag or force is False:
			self.playPauseFlag = False
			self.playPauseButton.config(
				text = "Play"
			)
		elif not self.playPauseFlag or force is True:
			self.playPauseFlag = True
			self.playPauseButton.config(
				text = "Pause"
			)
			self.timerVar.set("{:02d}:{:02d}:{:02d}".\
				format(
					self.timerHours,
					self.timerMinutes,
					self.timerSeconds))

		# End _playPause =======================================================

	def _printM(self, message, tag = 'S'): # ===================================

		self.printQueue.put_nowait(("[TR] " + message, tag))

		# End _printM ==========================================================

	# End LiveTableWidget ------------------------------------------------------


def _liveTableRoutine(
	stopPipeOut,
	commandQueue,
	mosiMatrixQueue,
	printQueue,
	profile,
	misoMatrixPipeOut
): # ===========================================================================

	try:

		lt = LiveTableWidget(
			profile,
			len(profile[ac.savedSlaves]),
			profile[ac.maxFans],
			stopPipeOut,
			misoMatrixPipeOut,
			commandQueue,
			printQueue
		)


		lt.mainloop()

		printQueue.put_nowait(("[TR] Live Table Terminated", 'W'))

	except Exception as e: # Print uncaught exceptions
		printQueue.put(("[TR] UNHANDLED EXCEPTION terminated Network Process: "\
			"\"{}\"".format(traceback.format_exc()), "E")
			)

	# End _liveTableRoutine ====================================================

## CLASS DEFINITION ############################################################
class LiveTable(wg.FCWidget):

	def __init__(
		self,
		master,
		profile,
		spawnQueue,
		printQueue
	): # =======================================================================

		try:
			
			self.profile = profile
			self.spawnQueue = spawnQueue
			self.printQueue = printQueue

			self.misoMatrixPipeOut, self.misoMatrixPipeIn = pr.Pipe(False)

			try:

				super(LiveTable, self).__init__(
					master,
					_liveTableRoutine,
					spawnQueue,
					printQueue,
					(
						profile,
						self.misoMatrixPipeOut
						
					),
					"TB"
				)

			except:
				ep.errorPopup()

			self.statusToSTR = {
				wg.ACTIVE : "Deactivate Live Table",	
				wg.INACTIVE : "Activate Live Table",
				wg.STARTING : "Activating Live Table",
				wg.STOPPING : "Deactivating Live Table"
			}

			self.bg = "#e2e2e2"
			self.fg = "black"

			self.button = Tk.Button(
				self,
				bg = self.bg,
				fg = self.fg,
				text = self.statusToSTR[wg.INACTIVE],
				command = self.start
			)
			self.button.pack()
			def mainloop():
				numSlaves = len(profile[ac.savedSlaves])+1
				possibleRPMs = range(0, 11500)
				while True:
				
					time.sleep(0.05)

					newMatrix = []
					for index in range(numSlaves):
						newMatrix.append([sv.CONNECTED] + random.sample(possibleRPMs,18))

					#numSlaves += 1

					self.misoMatrixPipeIn.send(newMatrix)

					"""
					# Check shutdown flag ----------------------------------------------
					if stopPipeOut.poll():
						message = stopPipeOut.recv()
						if message == 1:
							printQueue.put_nowait(("[TR] Shutting down network","W"))

							# TODO:

							break

						else:
							printQueue.put_nowait(
								("[TR] WARNING: Unrecognized message in LT-Routine "\
								"shutdown pipe (ignored): \"{}\"".\
								format(message),"E"))
							continue
					"""
			thread = threading.Thread(
				target = mainloop
				)
			thread.setDaemon(True)
			thread.start()

		except:
			self._printE("Error in Live Table Initialization:")

		# End __init__ =========================================================

	def _setStatus(self, newStatus): # =========================================

		super(LiveTable, self)._setStatus(newStatus)

		if newStatus not in (wg.ACTIVE, wg.INACTIVE):
			buttonState = Tk.DISABLED
		else:
			buttonState = Tk.NORMAL

		if newStatus is wg.INACTIVE:
			buttonCommand = self.start
		else:
			buttonCommand = self.stop

		self.button.config(
			text = self.statusToSTR[newStatus],
			command = buttonCommand,
			state = buttonState
		)
		# End _setStatus =======================================================
