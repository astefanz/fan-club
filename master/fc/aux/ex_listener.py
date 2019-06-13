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
Provisional script to test the external control command listener.

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """
import socket as sk
import threading as mt

DEFAULT_LPORT = 60169

class ExternalControlClient:
    def __init__(self, port = DEFAULT_LPORT, R = 11, C = 11, L = 1):
        self.socket = openSocket(0)
        self.index_in, self.index_out = 0, 1
        self.target = ("0.0.0.0", port)
        self.R, self.C, self.L = R, C, L
        self.RC = self.R*self.C
        self.RCL = self.RC*self.L


    def send(self, message, timeout = 5):
        command = "{}|{}".format(self.index_out, message)
        self.socket.sendto(bytearray(command, 'ascii'), self.target)
        self.index_out += 1
        print("Command sent. Waiting for reply...")
        try:
            self.socket.settimeout(timeout)
            message, sender = self.socket.recvfrom(1024)
            print("Received: \n\t", message.decode('ascii'))
            print("From: ", str(sender))
        except sk.error:
            print("Timed out")

    def mapRCL(self, f):
        dcs = [0]*self.RCL
        for r in range(self.R):
            for c in range(self.C):
                for l in range(self.L):
                    k = l*self.RC + r*self.C + c
                    dcs[k] = f(r, c, l)
        self.send("D|{}|{}|{}|{}".format(self.L, self.R, self.C,str(dcs)[1:-1]))

    def close(self):
        self.socket.close()
        print("Closed socket")

def openSocket(port):
    sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
    sock.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
    sock.bind(("", port))
    print(f"Opened socket on port {sock.getsockname()[1]}")
    return sock

