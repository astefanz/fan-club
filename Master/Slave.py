################################################################################
## Project: Fanclub Mark II "Master" ## File: Slave.py  - "Slave" class       ##
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
This module contains OOP representation of Slave devices.

"""
################################################################################

## CONSTANT VALUS ##############################################################

# SLAVE STATUS CODES
	# ABOUT: Positive status codes are for connected Slaves, negative codes for
	# disconnected ones.

BLOCKED = -4
DISCONNECTED = -3
AVAILABLE = -2
KNOWN = -1
CONNECTED = 1

## CLASS DEFINITION ############################################################

class Slave:

	def __init__(self, mac, status,i ip = None, miso = None, mosi = None):
		# NOTE: "miso" and "mosi" stand for, "Master in, Slave out" and
		# "Master out, Slave in," respectively. These are tuples of the
		# form (socket, address) where "socket" is a Python UDP socket
		# object and "address" is itself a tuple of the form (IP, PORt)
		# which are the IP and port number of the corresponding miso 
		# (or mosi) socket of this connected Slave board.

		self.mac = mac
		self.status = status
		self.ip  = ip
		self.miso = miso
		self.mosi = mosi