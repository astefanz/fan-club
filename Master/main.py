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

VERSION = "MASTR_DAWN_0" # Reference for consecutive versions during testing

# BE ADVISED: THIS VERSION IS NOT YET FUNCTIONAL                               #

# This version will test the system's UDP broadcast

#### IMPORTS ###################################################################

import socket

#### CONSTANTS #################################################################

BROADCAST_PORT = 65000
COMMUNICATIONS_PORT = 50007


#### MAIN ######################################################################

print "\n\nFC MKII (" + VERSION + ") INITIATED"

# UDP SOCKET SETUP -------------------------------------------------------------

# Instantiate socket:
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#                          ^               ^
#      Address type (IPv4) |               | Socket type (UDP; i.e "datagram")

# Configure socket for broadcasting:
udp.bind(('', BROADCAST_PORT))
#	Bind to no address (interpreted as any interface available) and set port
#	to BROADCAST_PORT, previously defined

udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
# See:
# https://erlerobotics.gitbooks.io/erle-robotics-python-gitbook-free/udp_and_tcp/socket_options.html

# BROADCAST LOOP ---------------------------------------------------------------

while(True):
	inp = raw_input("Ready to broadcast. (2: tcp| 1:bcast | 0:end): ")

	if(inp == '2'):
		udp.sendto(str(COMMUNICATIONS_PORT), ("<broadcast>", BROADCAST_PORT))
		print "Broadcast sent. Initializing TCP..."
		tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		tcp.bind(('', COMMUNICATIONS_PORT))
		print "Socket initialized. Listening..."
		tcp.listen(1)
		connection, address = tcp.accept()
		print "CONNECTION SUCESSFUL"
		print "\tCONNECTION: ", connection
		print "\tADDRESS: ", address
		

		while(True):

			tcp.send(raw_input("SEND: "))
			print "SENT"

			received = tcp.receive()
			print "RECEIVED: " + str(received)


	elif(inp == '1'):
		udp.sendto(str(COMMUNICATIONS_PORT), ("<broadcast>", BROADCAST_PORT))
		print "Broadcast sent"
	elif(inp == '0'):
		print "RIP"
		break
	else:
		print "Unrecognized input. Try again"
