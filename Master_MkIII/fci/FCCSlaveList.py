################################################################################
## Project: Fan Club Mark II "Master" # File: FCCSlaveList.py                 ##
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
Custom Tkinter widget to display Slave statuses.

"""
################################################################################


## DEPENDENCIES ################################################################

# GUI:
#from mttkinter import mtTkinter as Tk
import tkinter as Tk
import tkinter.filedialog 
import tkinter.messagebox
import tkinter.font
import tkinter.ttk # "Notebooks"

# System:
import os # Get current working directory & check file names
import sys # Exception handling
import inspect # get line number for debugging
import traceback

# FCMkII:
import FCSlave as sv
import FCCommunicator as cm

## CONSTANTS ###################################################################


## CLASS DEFINITION ############################################################

class FCCSlaveList(Tk.Frame): # ================================================

	# NOTE: Slaves are stored as: 
	# [Index + 1, cm.MAC, status, fans, version, iid]
	#          0    1       2     3    4      5

	def __init__(self, master): # ==============================================
		try:
			# Parameters displayed:
			# - Index 
			# - cm.MAC
			# - Status
			# - Fans
			# - Version

			# CONFIGURE --------------------------------------------------------
			Tk.Frame.__init__(self, master)
			self.background = "#d3d3d3"
			self.foreground = "black"
			self.config(
				bg = self.background, 
				relief = Tk.SUNKEN,
				borderwidth = 2
			)
		
			# BUILD ------------------------------------------------------------
			
			# Create list:
			self.slaveList = tkinter.ttk.Treeview(
				self, 
				selectmode="extended"
			)
			self.slaveList["columns"] = \
				("Index","MAC","Status","Fans", "Version")

			# Create columns:
			self.slaveList.column('#0', width = 20, stretch = False)
			self.slaveList.column("Index", width = 20, anchor = "center")
			self.slaveList.column("MAC", width = 70, anchor = "center")
			self.slaveList.column("Status", width = 70, anchor = "center")
			self.slaveList.column("Fans", width = 50, stretch = False, 
				anchor = "center")
			self.slaveList.column("Version", width = 50, 
				anchor = "center")

			# Configure column headings:
			self.slaveList.heading("Index", text = "Index")
			self.slaveList.heading("MAC", text = "MAC")
			self.slaveList.heading("Status", text = "Status")
			self.slaveList.heading("Fans", text = "Fans")
			self.slaveList.heading("Version", text = "Version")

			# Configure tags:
			self.slaveList.tag_configure(
				"C", 
				background= '#d1ffcc', 
				foreground = '#0e4707', 
				font = 'TkFixedFont 12 ') # Connected
			
			self.slaveList.tag_configure(
				"B", 
				background ='#a6c1fc', 
				foreground= '#192560', 
				font = 'TkFixedFont 12 bold') # Bootloader

			self.slaveList.tag_configure(
			"D", 
			background= '#ffd3d3', 
			foreground ='#560e0e', 
			font = 'TkFixedFont 12 bold')# Disconnected

			self.slaveList.tag_configure(
			"K",
			background= '#fffaba',
			foreground ='#44370b',
			font = 'TkFixedFont 12 bold') # Known

			self.slaveList.tag_configure(
			"A", 
			background= '#ededed', 
			foreground ='#666666',
			font = 'TkFixedFont 12 ') # Available

			# Save previous selection:
			self.oldSelection = None

			# Bind command:
			#self.slaveList.bind('<Double-1>', self._onDoubleClick)
			self.slaveList.bind('<Control-a>', self.selectAll)
			self.slaveList.bind('<Control-A>', self.selectAll)
			self.slaveList.bind('<Double-1>', self.selectAll)
			self.slaveList.bind('<Escape>', self.deselectAll)

			self.slaveList.pack(fill = Tk.BOTH, expand = True, anchor = 'n')

			# DATA -------------------------------------------------------------
			self.slaves = {}
			self.numSlaves = 0
			
			#self.pack(fill = Tk.BOTH, expand = True, side = Tk.TOP)

		
		except Exception as e: # Print uncaught exceptions
			tkinter.messagebox.showerror(title = "FCMkII Fatal Error",
				message = "Warning: Uncaught exception in "\
				"SList constructor: \"{}\"".\
				format(traceback.format_exc()))
		
		# End __init__ =========================================================

	def addSlaves(self, newSlaves): # ==========================================
		# Expected format:
		# (Index, cm.MAC, Status, Fans, Version)
	
		for newSlave in newSlaves:

			if newSlave[cm.INDEX] in self.slaves:
				raise ValueError("Tried to 'add' existing Slave index ({})".\
					format(newSlave[cm.INDEX]))

			else:
				index = newSlave[cm.INDEX]
				iid = self.slaveList.insert(
					'', 
					0,
					values = (
						index + 1,
						newSlave[cm.MAC],
						sv.translate(newSlave[cm.STATUS]),
						newSlave[cm.FANS],
						newSlave[cm.VERSION]
						),
					tag = sv.translate(newSlave[cm.STATUS], True)
				)
				self.slaves[index] = newSlave + (iid,)
		
		# End add ==============================================================

	def updateSlaves(self, slaves): # ==========================================
		# Expected format:
		# (Index, cm.MAC, Status, Fans, Version)
	
		for newValues in slaves:
			index = newValues[cm.INDEX]
			iid = self.slaves[index][cm.IID]

			self.slaves[index] = newValues + (iid,)

			self.slaveList.item(
				iid,	
				values = (
						index + 1,
						newValues[cm.MAC],
						sv.translate(newValues[cm.STATUS]),
						newValues[cm.FANS],
						newValues[cm.VERSION]
						),
				tag = sv.translate(newValues[cm.STATUS], True)
			)	

			if newValues[cm.STATUS] is not sv.CONNECTED:
				self.slaveList.move(
					iid,
					'',
					0,
				)


		# End update ===========================================================

	def setSlaveStatus(self, index, newStatus): # ==============================

		slave =	self.slaves[index]
		self.slaves[index] = slave[:cm.STATUS] + (newStatus,) + slave[cm.STATUS+1:]

		self.slaveList.item(
			self.slaves[index][cm.IID],
			values = (
				index + 1,
				slave[cm.MAC],
				slave[cm.STATUS],
				slave[cm.FANS],
				slave[cm.VERSION]
				),
			tag = sv.translate(newStatus, True)
		)

		if newStatus is not sv.CONNECTED:
			self.slaveList.move(
				self.slaves[index][cm.IID],
				'',
				0,
			)

		# End setStatus ========================================================

	def clear(self): # =========================================================
		# Empty slave list.

		for index in self.slaves:
			self.slaveList.delete(self.slaves[index][cm.IID])

		del self.slaves
		self.slaves = {}

		# End clear ============================================================

	def remove(self, index): # =================================================
		# Remove one Slave from list and data structure

		self.slaveList.delete(self.slaves[index][cm.IID])
		del self.slaves[index]

		# End remove ===========================================================
	
	def getSelection(self, statusFilter = None): # =============================
	
		selection = ()
		for iid in self.slaveList.selection():
			if statusFilter is None or \
				selfslaveList.item(iid)['values'][cm.STATUS] == statusFilter:
				
				selection += (
					self.slaveList.item(iid)['values'][cm.INDEX] - 1,
				)

		return selection

		# End getSelection =====================================================

	def setSelection(self, selection = None, status = None): # =================
		# Set which Slaves are selected. Takes an iterable of integers (indices)
		# and selects such Slaves in the SlaveList... If the list is omitted,
		# all Slaves will be selected. Optional argument "status" will cause
		# this function to only select Slaves with the given status code.
		
		#iids = []

		if selection is None:
			iterable = self.slaves
		else:
			iterable = selection
		
		for index in iterable:
			if status is None or self.slaves[index][cm.STATUS] == status:
				#iids.append(self.slaves[index][cm.IID])
				self.slaveList.selection_add(self.slaves[index][cm.IID])
				#print "Selected {}: {}".format(index, self.slaves[index][cm.IID])
		
		#self.slaveList.selection_add(tuple(iids))

		# End setSelection =====================================================

	def selectAll(self, event): # ==============================================
		for index in self.slaves:
			#iids.append(self.slaves[index][cm.IID])
			self.slaveList.selection_add(self.slaves[index][cm.IID])

		# End selectAll ========================================================
	
	def toggleAll(self, event): # ==============================================
		for index in self.slaves:
			#iids.append(self.slaves[index][cm.IID])
			self.slaveList.selection_toggle(self.slaves[index][cm.IID])

		# End toggleAll ========================================================
	
	def deselectAll(self, event): # ============================================
		#iids.append(self.slaves[index][cm.IID])
		self.slaveList.selection_set(())

		# End deselectAll ======================================================

	"""
	def setStatus(self, index, newStatus): # ===================================

		self.slaves[index][2] = sv.translate(newStatus)
		self.slaveList.item(self.slaves[index][-1], # <- cm.IID 
			values = self.slaves[index],
			tag = sv.translate(newStatus, True))

		# Move:
		if newStatus is not sv.CONNECTED:
			self.slaveList.move(self.slaves[index][-1], '', 0)
			
		# End setStatus ========================================================
	
	def setVersion(self, index, newVersion): # =================================

		self.slaves[index][4] = sv.translate(newVersion)
		self.slaveList.item(self.slaves[index][-1], # <- cm.IID 
			values = self.slaves[index],
			
		# End setVersion ========================================================
	"""

	"""
	def setSelection(self, selected): # ========================================
		pass
	"""

## TEST SUITE ##################################################################

if __name__ is '__main__':
	
	import threading as tr
	import time as tm

	def _routine(sl): # --------------------------------------------------------
		
		sl.add((1,'COUNTRY:ROAD', sv.KNOWN, 47, 'Freedom'))
		tm.sleep(.2)
		sl.add((2,'PI:V', sv.CONNECTED, 75, 'Freedom'))
		tm.sleep(.2)
		
		sl.update((1,'PI:V', sv.DISCONNECTED, 75, 'Freedom'))
		tm.sleep(.2)
		
		sl.clear()
		tm.sleep(.2)
		
		sl.add((0, 'Doodle', sv.DISCONNECTED, 22, 'Doods'))
		tm.sleep(.2)
		sl.remove(0)
		tm.sleep(.2)
		sl.add((1, 'Doodle', sv.DISCONNECTED, 22, 'Doods'))
		tm.sleep(.2)
		sl.add((2, 'Doodle', sv.DISCONNECTED, 22, 'Doods'))
		tm.sleep(.2)
		sl.add((3, 'Doodle', sv.DISCONNECTED, 22, 'Doods'))
		tm.sleep(.2)
		sl.setSlaveStatus(3, sv.KNOWN)
		tm.sleep(.2)
		sl.setSelection(selection = None, status = sv.DISCONNECTED)

		while True:
			sl.getSelection()
			tm.sleep(0.5)

		# End routine ----------------------------------------------------------

	frame = Tk.Frame(None)
	frame.master.minsize(width = 666, height = 333)
	frame.master.title("FCMkII Slave List Unit Test")

	sl = SlaveList(frame)
	sl.pack(fill = Tk.BOTH, expand = True)
	
	thread = tr.Thread(target = _routine, args = (sl,))
	thread.setDaemon(True)
	thread.start()


	frame.pack(fill = Tk.BOTH, expand = True)

	frame.mainloop()

	## End test suite ##########################################################



