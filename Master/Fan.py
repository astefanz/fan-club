################################################################################
## Project: Fan Club Mark II "Master" ## File: Fan.py                         ##
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
OOP representation of Fans.

"""

## CONSTANT VALUES #############################################################

# FAN STATUS CODES:

ON = 1
OFF = 0
INACTIVE = -1
MISBEHAVING = -2


## CLASS DEFINITION ############################################################

class Fan:
	# ABOUT: Container for fan-specific data

	def __init__(self, index, status, coordinates = (0,0),
		mapping = [0,0,0,0,0,0,0,0,0,0]):
		# ABOUT: Constructor for class Fan.
		# PARAMETERS:
		# - index: integer representing position of fan in array that is expec-
		#	ted to be 21-fans-long (indexed from 0 to 20)
		# - status: integer representing status of this fan (constants defined)
		#	in Fan.py) can be ON, OFF, INACTIVE, or MISBEHAVING. Initially used
		#	to tell whether a Fan is being used (i.e can be OFF or INACTIVE)
		# - coordinates: tuple of two POSITIVE integers representing the posi-
		# 	tion of fan in wind tunnel, if any. Can be left empty, in which ca-
		#	se it defaults to (0,0) to indicate it has not been positioned. If
		#	given a position, it must be within wind tunnel dimensions.
		# - mapping: list of ten RPM's corresponding to duty cycles of 10%, 20%
		#	30%, 40%, 50%, 60%, 70%, 80%, 90% and 100%, used for RPM chasing. It
		#	may be left empty, in which case it defaults to a list of ten 0's to
		#	indicate no mapping has been made.
		#
		# WARNING: THIS CLASS IS NOT MEANT TO BE USED ON ITS OWN BUT AS AN AUXI-
		# LIARY CONTAINER FOR CLASSES SUCH AS Slave AND Profile. AS SUCH, FOR
		# PURPOSES OF EFFICIENCY, IT OPERATES UNDER THE ASSUMPTION THAT ALL PA-
		# RAMETERS HAVE BEEN VERIFIED BY THE GREATER CONTAINER CLASS.

		# Initialize attributes ------------------------------------------------

		# Initialize given attributes:
		self.index = index
		self.coordinates = coordinates
		self.mapping = mapping

		# Initialize member attributes:
			# The following member attributes are modified in accordance to the
			# values received from a connected Slave unit. As such, they have no
			# meaning upon class initialization.

		self.dutyCycle = 0
		self.rpm = 0
		self.status = status
		



