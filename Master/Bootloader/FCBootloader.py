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
import tkMessageBox

import socket as s
import SimpleHTTPServer
import SocketServer
import threading
import traceback

import FCBTSlaveTable as st
import FCBTFileChooser as fr
import FCBTCommunicator as cm

## AUXILIARY FUNCTIONS #########################################################

def printEx(m = None): # =======================================================
	# Print error messages

	if m is not None:
		tkMessageBox.showerror(title = "FCMkII Bootloader Error", 
			message = "Error: {}".format(traceback.format_exc()))

	else:
		tkMessageBox.showerror(title = "FCMkII Bootloader Error", 
			message = "Error message: \n".format( m))
		
	# End printEx ==============================================================
 
## CLASS DEFINITION ############################################################


class FCBootloader:

	def __init__(self, standalone = False): # ==================================
		try:

			# GUI Setup ========================================================

			# Window setup -----------------------------------------------------
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
			self.container.config(bg = self.background)

			# File chooser -----------------------------------------------------
			self.fileChooserFrame = Tk.Frame(
				self.container, bg = self.background)
			self.fileChooser = 	fr.FCBTFileChooser(self.fileChooserFrame)
			self.fileChooser.pack(
				side = Tk.LEFT, fill = Tk.X, expand = True)
			self.fileChooserFrame.pack(side = Tk.TOP, fill = Tk.X, expand = True)
			
			# Communications control --------------------------------------------
			self.communicatorFrame = Tk.Frame(self.container, 
				bg = "red")

			self.communicator = cm.FCBTCommunicator(self.communicatorFrame)			
			self.communicator.pack(
				fill = Tk.BOTH, expand = True)


			self.communicatorFrame.pack( fill = Tk.BOTH,
				expand = True)
		
			# List -------------------------------------------------------------
			self.listFrame = Tk.Frame(self.container, bg= "black")

			# Widget:
			self.slaveTable = st.FCBTSlaveTable(self.listFrame)
			self.slaveTable.pack(fill = Tk.BOTH, expand = True)
			
			self.listFrame.pack(fill = Tk.BOTH, expand = True)

			# Status -----------------------------------------------------------
			self.statusFrame = Tk.Frame(self.container, bg = self.background)


			#self.root.pack()		
			self.root.update()
			self.root.geometry("400x300")
			self.root.minsize(self.root.winfo_width(), self.root.winfo_height())

			self.container.pack(fill = Tk.BOTH, expand = True)
			
			if standalone:
				self.root.mainloop()

		except Exception as e:
			printEx(e)

		# End __init__ =========================================================

if __name__ == "__main__":
	
	fcb = FCBootloader(standalone = True)
