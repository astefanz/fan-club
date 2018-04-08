################################################################################
## Project: Fan Club Mark II "Master" ## File: Slave.py                       ##
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
OOP representation of Slave units.

"""
################################################################################

## DEPENDENCIES ################################################################
import Fan       			 # Fan representation
import Queue      # Communication between threads
import threading   # Thread-safe access
import FCInterface as FCI

## CONSTANT VALUES #############################################################

# SLAVE STATUS CODES:
	# ABOUT: Positive status codes are for connected Slaves, negative codes for
	# disconnected ones.

DISCONNECTED = -3
AVAILABLE = -2
KNOWN = -1
CONNECTED = 1
BUSY = 2

# AUXILIARY DEFINITIONS ########################################################

def translate(statusCode, short = False): # ====================================
	# ABOUT: Translate an integer status code to a String.
	# PARAMETERS:
	# - statusCode: int, status code to translate.
	# - short: bool, whether to give corresponding single-char version.
	# RAISES:
	# - ValueError if given argument is not a valid status code

	result = ""

	if statusCode == DISCONNECTED:
		result = "DISCONNECTED"
	elif statusCode == AVAILABLE:
		result = "AVAILABLE"
	elif statusCode == KNOWN:
		result = "KNOWN"
	elif statusCode == CONNECTED:
		result = "CONNECTED"
	elif statusCode == BUSY:
		result = "BUSY"
	else:
		raise ValueError("Slave.translate got nonexistent statusCode! ({})".\
			format(statusCode))

	if short:
		return result[0]
	else:
		return result

	# End translate # ==========================================================

## CLASS DEFINITION ############################################################

class Slave:
	# ABOUT: Representation of connected Slave model, primarily a container with
	# no behavior besides that of its components, such as Locks.

	def __init__(self, name, mac, status, master, display, maxFans, activeFans,
		ip = None, misoP = None, mosiP = None, misoS = None, mosiS = None,
		thread = None):
		# ABOUT: Constructor for class Slave.
		# WARNING: Method documentation outdated.
		# PARAMETERS:
		# - name: String representing this Slave unit's name (arbitrary)
		# - mac: String representing this Slave unit's MAC address
		# - status: Integer value describing the connection of this Slave, or
		#	lack thereof; its possible values are defined in Slave.py 
		# - fans: List of exactly 21 Fan objects (see Fan.py) that represents
		#	this Slave's set of physical fans.
		# - activeFans: Int, number of fans in the array to be used.
		# - ip: String describing this Slave's IP address, if any. May be left
		#	blank, in which case it defaults to None.
		# - miso: Either an integer representing the Slave's MISO port number or
		#	a Python UDP socket object if this Slave unit is connected.
		# - mosi: Either an integer representing the Slave's MOSI port number or
		#	a Python UDP socket object if this Slave unit is connected.
		#
		# ATTRIBUTES:
		# Besides the Constructor parameters, the following data members are in-
		# trinsic of every Slave instance:
		# - lock: Python Lock object for thread-safe access.
		# - mosiQueue: Python Queue object for inter-thread communication of 
		#	outgoing messages.
		# - thread: Python thread object (or None) that executes Slave's handler
		#	routine.
		# - exchange: int, to coordinate UDP communications.
		#
		# WARNING: THIS CLASS IS NOT MEANT TO BE USED ON ITS OWN BUT AS AN AUXI-
		# LIARY CONTAINER FOR CLASSES SUCH AS Slave AND Profile. AS SUCH, FOR
		# PURPOSES OF EFFICIENCY, IT OPERATES UNDER THE ASSUMPTION THAT ALL PA-
		# RAMETERS HAVE BEEN VERIFIED BY THE GREATER CONTAINER CLASS.

		self.name = name + mac[-3:]
		self.mac = mac
		self.status = status
		self.statusLock = threading.Lock()

		self.maxFans = maxFans
		self.activeFans = activeFans
		self.activeFansLock = threading.Lock()

		self.ip  = ip
		self.ipLock = threading.Lock()

		self.misoP = misoP
		self.mosiP = mosiP
		self.misoS = misoS
		self.mosiS = mosiS
		self.thread = thread
		self.exchange = 0
		self.exchangeLock = threading.Lock()

		self.misoIndex = 0

		self.lock = threading.Lock()
		self.mosiQueue = Queue.Queue(1)

		self.slaveDisplay = FCI.SlaveDisplay(master, self)

		self.setRPM = self.slaveDisplay.setRPM
		self.setDC = self.slaveDisplay.setDC

		# Add self to display (ttk Treeview)
		# NOTE: If time allows, add layer of abstraction. (You wish.)
		self.display = display
		self.iid = self.display.insert('', 'end', 
			values = (self.name, self.mac, translate(self.status),
			 self.ip, self.activeFans), tag = translate(self.status, True))
	
		# End __init__ =================================================

	def setRPMs(self, rpms): # =============================================
		# ABOUT: Update RPM list.
		
		# NOTE: Provisional debug mode

		print "Updated RPMs: {}".format(rpms)
		
		indx = 0
		for rpm in rpms:
			self.setRPM(rpm, indx)
			indx += 1

		# End setRPMs ==================================================

	def setDCs(self, dcs): # ===============================================
		# ABOUT: Update DC list.

		# NOTE: Provisional debug mode

		print "Updated DCs: {}".format(dcs)
		
		i = 0
		for dc in dcs:
			self.setDC(dc*100, i)
			i += 1
		
		# End setDCs ===================================================

	def setName(self, newName): # ==========================================
		# ABOUT: Update name.
		# PARAMETERS: 
		# - newName: new name.
		self.name = newName

	def setStatus(self, newStatus): # ==========================================
		# ABOUT: Update status.
		# PARAMETERS: 
		# - newStatus: code of the new status.
		
		try:
			self.statusLock.acquire()

			if self.status == newStatus:
				return
			else: 
				self.status = newStatus
				
				if newStatus == DISCONNECTED:
					self.setExchange(0)
					self.setMISOIndex(0)
					self.setActiveFans(0, True)

				self.slaveDisplay.setStatus(newStatus)

		finally:
			# Guarantee lock release:
			self.statusLock.release()

		# End setStatus ========================================================

	def setMAC(self, newMAC): # ================================================
		# ABOUT: Update MAC.
		# PARAMETERS: 
		# - MAC: new MAC address.

		self.mac = newMAC

		self.updateList()

	def setExchange(self, newExchange): # ======================================
		# ABOUT: Update exchange index.
		# PARAMETERS: 
		# - newExchange: new exchange index.

		self.exchange = newExchange
		self.slaveDisplay.setExchange(newExchange)

		self.updateList()

	def setIP(self, newIP): # ==================================================
		# ABOUT: Update IP address.
		# PARAMETERS: 
		# - newExchange: new IP address

		self.ip = newIP

		self.updateList()

	def updateList(self, newStatus = None): # ==================================
		# ABOUT: Update items in Slave list
		if newStatus == None:
			self.display.item(self.iid, 
				values = [self.name, self.mac, translate(self.status),
				 self.ip, self.activeFans])
		else:
			self.display.item(self.iid, 
				values = [self.name, self.mac, translate(self.status),
				 self.ip, self.activeFans], tag = translate(self.status ,True))


	def setActiveFans(self, newActiveFans, displayOnly = False): # =============
		# ABOUT: Update activeFans value
		# PARAMETERS:
		# - newActiveFans: new value for activeFans
		# - displayOnly: bool, whether to modify stored active fans variable or
		#	to only deactivate fan displays.
		if not displayOnly:
			self.activeFans = newActiveFans
		self.slaveDisplay.setActiveFans(newActiveFans)
		self.updateList()

	def incrementExchange(self):
		# ABOUT: Increment exchange index by 1.
		self.exchange += 1
		self.slaveDisplay.setExchange(self.exchange)

	def incrementMISOIndex(self):
		# ABOUT: Increment misoIndex index by 1.
		self.misoIndex += 1
		self.slaveDisplay.setMISOIndex(self.misoIndex)

	def setMISOIndex(self, newMISOIndex): # ======================================
		# ABOUT: Update misoIndex index.
		# PARAMETERS: 
		# - newmisoIndex: new misoIndex index.

		self.misoIndex = newMISOIndex
		self.slaveDisplay.setMISOIndex(newMISOIndex)


