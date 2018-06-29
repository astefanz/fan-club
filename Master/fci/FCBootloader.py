################################################################################
## Project: Fan Club Mark II "Master" # File: FCBootloader.py                 ##
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
GUI for FC Bootloader

"""
################################################################################


## DEPENDENCIES ################################################################
from mttkinter import mtTkinter as Tk
import tkFileDialog

import socket as s
import SimpleHTTPServer
import SocketServer
import threading

## CLASS DEFINITION ############################################################

class FCBootloader:

	def __init__(self, standalone = False): # ==================================
		
		# Window setup ---------------------------------------------------------
		if standalone:
			self.root = Tk.Tk()
			self.container = Tk.Frame(self.root)

		else:
			self.root = Tk.Toplevel()
			self.container = self.root

		self.root.title("FCMkII Bootloader")
		self.root.lift()
		self.root.focus_force()
		self.root.grab_set()

		self.background = "#e2e2e2"
		self.foreground = "black"
		self.root.config(bg = self.background)
	

		# Sockets --------------------------------------------------------------

		# File chooser ---------------------------------------------------------
		self.fileChooserFrame = Tk.Frame(self.root, bg = self.background)

		self.topLabel = Tk.Label(self.fileChooserFrame, 
			bg = self.background, fg = self.foreground, 
			text = "Choose file pls")
		self.topLabel.pack(expand = False, side = Tk.TOP, anchor = Tk.N)
		self.fileChooserFrame.pack(side = Tk.TOP, expand = False)

		# Slave list -----------------------------------------------------------

		# Start button ---------------------------------------------------------	
		if standalone:
			self.root.mainloop()
		

if __name__ == "__main__":
	
	fcb = FCBootloader(standalone = True)
