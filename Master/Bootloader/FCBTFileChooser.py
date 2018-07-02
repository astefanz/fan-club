################################################################################
## Project: Fan Club Mark II "Master" # File: FCBTFileChooser.py              ##
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
Custom Tkinter widget for a graphical file-choosing utiliy.

"""
################################################################################



## DEPENDENCIES ################################################################
from mttkinter import mtTkinter as Tk
import tkFileDialog
import tkMessageBox

## CONSTANT DEFINITIONS ########################################################i

EMPTY = 0

## CLASS DEFINITION ############################################################

class FCBTFileChooser(Tk.Frame): 
	
	def __init__(self, master, background = "#e2e2e2"): # ======================

		Tk.Frame.__init__(self, master)
		
		self.background = background

		# File Chooser label:
		self.fileChooserLabel = Tk.Label(self, 
			bg = self.background, 
			text = "File to upload: ")
		self.fileChooserLabel.pack(
			expand = False, side = Tk.LEFT, anchor = Tk.W)

		# File Chooser Text Field:
		self.entryRedBG = "#ffc1c1"
		self.entryOrangeBG = "#ffd8b2"
		self.entryWhiteBG = "white"

		self.fileVar = Tk.StringVar()
		
		# TODO:
		"""
		self.fileVar.trace('w', self._fileNameEntryCheck)
		"""
	
		self.fileEntry = Tk.Entry(self, 
			highlightbackground = self.background,
			width = 17, bg = self.entryRedBG,
			textvariable = self.fileVar)
		self.fileEntry.pack(side = Tk.LEFT)
 
		self.fileStatus = EMPTY

		# file button:
		self.fileButton = Tk.Button(self, 
			highlightbackground = self.background, text = "...", 
			) # TODO command = self._fileButtonRoutine)

		self.fileButton.pack(side = Tk.LEFT)
		
		# Print padding:
		self.printPadding2 = Tk.Frame(self,
			bg = self.background,
			width = 5
			)
		self.printPadding2.pack(side = Tk.LEFT)
		
		# printTarget feedback:
		self.printTargetFeedbackLabel = Tk.Label(
			self,
			bg = self.background,
			text = '(No filename)',
			fg = 'darkgray',
			anchor = 'w',
			width = 12
			)
		self.printTargetFeedbackLabel.pack(side = Tk.LEFT)
	
		# Print padding:
		self.printPadding1 = Tk.Frame(self,
			bg = self.background,
			width = 20
			)
		self.printPadding1.pack(side = Tk.LEFT)

		
		
