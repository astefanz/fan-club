################################################################################
##----------------------------------------------------------------------------##
## CALIFORNIA INSTITUTE OF TECHNOLOGY ## GRADUATE AEROSPACE LABORATORY ##     ##
## CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES                      ##     ##
##----------------------------------------------------------------------------##
##      ____      __      __  __      _____      __      __    __    ____     ##
##     / __/|   _/ /|    / / / /|  _- __ __\    / /|    / /|  / /|  / _  \    ##
##    / /_ |/  / /  /|  /  // /|/ / /|__| _|   / /|    / /|  / /|/ /   --||   ##
##   / __/|/ _/    /|/ /   / /|/ / /|    __   / /|    / /|  / /|/ / _  \|/    ##
##  / /|_|/ /  /  /|/ / // //|/ / /|__- / /  / /___  / -|_ - /|/ /     /|     ##
## /_/|/   /_/ /_/|/ /_/ /_/|/ |\ ___--|_|  /_____/| |-___-_|/  /____-/|/     ##
## |_|/    |_|/|_|/  |_|/|_|/   \|___|-    |_____|/   |___|     |____|/       ##
##                   _ _    _    ___   _  _      __  __   __                  ##
##                  | | |  | |  | T_| | || |    |  ||_ | | _|                 ##
##                  | _ |  |T|  |  |  |  _|      ||   \\_//                   ##
##                  || || |_ _| |_|_| |_| _|    |__|  |___|                   ##
##                                                                            ##
##----------------------------------------------------------------------------##
## Alejandro A. Stefan Zavala ## <astefanz@berkeley.edu>   ##                 ##
## Chris J. Dougherty         ## <cdougher@caltech.edu>    ##                 ##
## Marcel Veismann            ## <mveisman@caltech.edu>    ##                 ##
################################################################################
""" ABOUT ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
API with which to externally control the FC MkIV master-side.
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """
import socket as sk
import threading as mt

DEFAULT_LPORT = 60169
DEFAULT_BPORT = 60069
DEFAULT_DELTA = 10

class FCClient:
    """
    Interface for external control. Contains all necessary behavior to control
    the MkIV over a network.
    """
    def __init__(self, R, C, L, lport = DEFAULT_LPORT, bport = DEFAULT_BPORT,
        delta = DEFAULT_DELTA):
        """
        Build and initialize an FCClient instance.

        - R := int, number of rows of the fan array being controlled.
        - C := int, number of columns of the fan array being controlled.
        - L := int, number of layers of the fan array being controlled.
        - lport := int, port number for the command listener. Defaults to the
            default listener port. Can be obtained from state broadcasts.
        - bport := int, port number for the state broadcast. Defaults to the
            default broadcast port.
        - delta := int, size of the "discard index" range. Defaults to the
            default index delta.
        """
        self.R, self.C, self.L = R, C, L
        self.lport, self.bport = lport, bport
        self.delta = delta

        # Build sockets TODO

    def startBroadcastThread(self):
        # TODO
        pass

    def stopBroadcastThread(self):

    def setListenerPort(self):

    def setBroadcastPort(self):

    def isBroadcastActive(self):

    def

    # Internal methods ..........................
