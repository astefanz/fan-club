################################################################################
## Project: Fan Club Mark II "Master" # File: Terminal.py                     ##
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
Custom Tkinter widget to print text output

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
import threading
import queue
import os # Get current working directory & check file names
import sys # Exception handling
import inspect # get line number for debugging
import traceback
import time

# FC:
from auxiliary import errorPopup as ep

class Terminal(Tk.Frame): # ====================================================

	def __init__(self, master, queue): # =======================================
		try:
			# - Version

			# CONFIGURE --------------------------------------------------------
			Tk.Frame.__init__(self, master)
			self.background = "#d3d3d3"
			self.foreground = "black"
		
			# Set debug foreground:
			self.debugColor = "#ff007f"

			self.mainQueue = queue

			self.packed = True

			# BUILD ------------------------------------------------------------	
			self.mainTerminalContainer = Tk.Frame(
				self,
				bg = self.background,
				relief = Tk.SUNKEN,
				bd = 3
			)
			self.mainTerminalContainer.pack(fill = Tk.BOTH, expand = True)
			
			self.mainTerminal = Tk.Frame(
				self.mainTerminalContainer,
				bg = self.background
			)
			
			self.mainTerminal.pack(side = Tk.TOP, fill = Tk.BOTH, expand = True)

			self.mainTLock = threading.Lock()
			self.mainTText = Tk.Text(self.mainTerminal, 
				fg = "#424242", bg=self.background, font = ('TkFixedFont'),
				selectbackground = "#cecece",
				state = Tk.DISABLED)
			self.mainTScrollbar = Tk.Scrollbar(self.mainTerminal)
			self.mainTScrollbar.pack(side = Tk.RIGHT, fill=Tk.Y)
			self.mainTScrollbar.config(command=self.mainTText.yview)
			self.mainTText.config(yscrollcommand = self.mainTScrollbar.set)
			self.mainTText.bind("<1>", 
				lambda event: self.mainTText.focus_set())
			self.mainTText.pack(fill =Tk.BOTH, expand = True)
			# Configure tags:
			self.mainTText.tag_config("S")
			self.mainTText.tag_config("G", foreground = "#168e07")
			self.mainTText.tag_config(\
				"W", underline = 1, foreground = "orange")
			self.mainTText.tag_config(\
				"E", underline = 1, foreground = "red", background = "#510000")
			self.mainTText.tag_config(\
				"D", foreground = self.debugColor)
			
			# TERMINAL CONTROL FRAME ...............................................

			self.terminalControlFrame = Tk.Frame(self.mainTerminal,	
				bg = self.background)

			# Autoscroll checkbox:
			self.autoscrollVar = Tk.IntVar()

			self.autoscrollButton = Tk.Checkbutton(self.terminalControlFrame, 
				text ="Auto-scroll", variable = self.autoscrollVar, 
				bg = self.background, fg = self.foreground)

			self.terminalControlFrame.pack(fill = Tk.X)

			# Debug checkbox:
			self.debugVar = Tk.IntVar()

			self.debugButton = Tk.Checkbutton(self.terminalControlFrame, 
				text ="Debug prints", variable = self.debugVar, 
				bg = self.background, fg = self.foreground)

			# Terminal print:
			self.terminalVar = Tk.IntVar()
			self.terminalVar.set(1)

			self.terminalButton = Tk.Checkbutton(self.terminalControlFrame, 
				text ="Terminal output", variable = self.terminalVar, 
				bg = self.background, fg = self.foreground)

			# Clear terminal:
			self.clearTerminalButton = Tk.Button(
				self.terminalControlFrame,
				text = "Clear",
				bg = self.background,
				highlightbackground = self.background,
				fg = self.foreground,
				command = self._clearTerminal
			)

			# Print terminal:
			self.printTerminalButton = Tk.Button(
				self.terminalControlFrame,
				text = "Print to File",
				bg = self.background,
				highlightbackground = self.background,
				fg = self.foreground,
				command = self._printTerminal
			)

			# BUILD:
			self.autoscrollButton.pack(side = Tk.LEFT)
			self.debugButton.pack(side = Tk.LEFT)
			self.terminalButton.pack(side = Tk.LEFT)
			self.autoscrollButton.select()

			self.clearTerminalButton.pack(side = Tk.LEFT)
			self.printTerminalButton.pack(side = Tk.LEFT)

			# RUN --------------------------------------------------------------
			"""
			self.terminalThread = threading.Thread(target = 
				self._terminalRoutine)
		
			self.terminalThread.setDaemon(True)
			"""
			self.terminalUpdater()

		except Exception as e: # Print uncaught exceptions
			tkinter.messagebox.showerror(title = "FCMkII Fatal Error",
				message = "Warning: Uncaught exception in "\
				"GUI Terminal constructor: \"{}\"".\
				format(traceback.format_exc()))

		# End __init__ =========================================================


	def terminalUpdater(self): # ===============================================
		# ABOUT: Keep main terminal window updated w/ Communicator output. 
		# Uses Tkinter scheduler instead of thread.
	
		try:
			if self.terminalVar.get() == 0 or self.mainQueue.empty():
				return

			else: 
				for i in range(self.mainQueue.qsize()):
					# Fetch message to print:
					message = self.mainQueue.get(True)
					if type(message) is not tuple and len(message) is not 2:
						
						self.mainTText.config(state = Tk.NORMAL)
							# Must change state to add text.
						self.mainTText.insert(
							Tk.END, "Bad message format: \"{}\:\n".\
							format(message), "E")
						self.mainTText.config(state = Tk.DISABLED)
							
					# If there is an item, print it (otherwise, Empty exception is
					# raised and handled)

					# NOTE: The current setting should remain blocked until a 
					# message arrives
					
					# Check for debug tag:
					if message[1] is "D" and self.debugVar.get() == 0:
						# Do not print if the debug variable is set to 0
						pass

					else:

						# Switch focus to this tab in case of errors of warnings:
						if message[1] is "E" and not self.packed:
							self._toggle(force = True)

						self.mainTText.config(state = Tk.NORMAL)
							# Must change state to add text.
						self.mainTText.insert(
							Tk.END, message[0] + "\n", message[1])
						self.mainTText.config(state = Tk.DISABLED)

						# Check for auto scroll:
						if self.autoscrollVar.get() == 1:
							self.mainTText.see("end")

		except Exception as e: # Print uncaught exceptions
			tkinter.messagebox.showerror(
				title = "FCMkII Error",
				message = "Warning: Uncaught exception in Terminal "\
				"printer routine: \"{}\"".\
				format(traceback.format_exc()))

		finally:
			self.after(100, self.terminalUpdater)

		# End terminalUpdater ==================================================

	
	def _terminalRoutine(self): # ==============================================
		# ABOUT: Keep main terminal window updated w/ Communicator output...
	
		while True:
			try:
				if self.terminalVar.get() == 0:
					continue

				else: 
					try:
						# Fetch message to print:
						message = self.mainQueue.get(True)
						if type(message) is not tuple or len(message) is not 2:
							
							if not self.packed:
								self._toggle(force = True)

							self.mainTText.config(state = Tk.NORMAL)
								# Must change state to add text.
							self.mainTText.insert(
								Tk.END, "Bad message format: \"{}\:\n".\
								format(message), "E")
							self.mainTText.config(state = Tk.DISABLED)
							

					except queue.Empty:
						# If there is nothing to print, try again.
						continue
					else:
						# If there is an item, print it (otherwise, Empty exception is
						# raised and handled)

						# NOTE: The current setting should remain blocked until a 
						# message arrives
						
						# Check for debug tag:
						if message[1] is "D" and self.debugVar.get() == 0:
							# Do not print if the debug variable is set to 0
							pass

						else:

							# Switch focus to this tab in case of errors of warnings:
							if message[1] is "E" and not self.packed:
								self._toggle(force = True)

							self.mainTText.config(state = Tk.NORMAL)
								# Must change state to add text.
							self.mainTText.insert(
								Tk.END, message[0] + "\n", message[1])
							self.mainTText.config(state = Tk.DISABLED)

							# Check for auto scroll:
							if self.autoscrollVar.get() == 1:
								self.mainTText.see("end")

			except Exception as e: # Print uncaught exceptions
				tkinter.messagebox.showerror(
					title = "FCMkII Error",
					message = "Warning: Uncaught exception in Terminal "\
					"printer routine: \"{}\"".\
					format(traceback.format_exc()))

		# End _terminalRoutine =================================================
	
	def toggle(self, force = None): # ==========================================

		if force is True or not self.packed:
			# Show terminal
			self.mainTerminalContainer.pack(fill = Tk.BOTH, expand = True)
			self.mainTerminalContainer.pack_configure(expand = True)
			self.mainTerminal.pack(side = Tk.TOP, fill = Tk.BOTH, expand = True)
			self.packed = True

		else:
			# Hide terminal
			self.mainTerminal.pack_forget()
			self.mainTerminalContainer.config(height = 1)
			self.packed = False

		# End toggle ===========================================================

	def getMinSize(self): # ====================================================

		self.update_idletasks()
		return (0 , 0)

		# End getMinSize =======================================================

	def _printTerminal(self, event = None): # ==================================
		
		try:
			# Get file
			filename = tkinter.filedialog.asksaveasfilename(
						initialdir = os.getcwd(), # Get current working directory
						initialfile = "FCMkII_terminal_{}.txt".format(
								time.strftime(
									"%a_%d_%b_%Y_%H-%M-%S", 
									time.localtime()
								)
						),
						title = "Choose file",
						filetypes = (("Text files","*.txt"),
							("All files","*.*"))
			)
			
			if filename == '':
				self._printM(
					"Terminal print-to-file canceled (no filename)", 'W')

			else:
				with open(filename, 'w') as f:
					
					f.write("Fan Club MkII Terminal log printed on {}\n\n".\
						format(time.strftime(
								"%a %d %b %Y %H:%M:%S", 
								time.localtime()
							)
						)
					)

					f.write(self.mainTText.get(1.0, Tk.END))
		
		except:
			self._printE("Exception in Terminal print-to-file:")
		
		# End _printTerminal ===================================================

	def _clearTerminal(self, event = None): # ==================================
		
		self.mainTText.config(state = Tk.NORMAL)
		self.mainTText.delete(1.0, Tk.END)
		self.mainTText.config(state = Tk.DISABLED)

		# End _clearTerminal ===================================================

	def _printM(self, message, tag = 'S'): # ===================================
		
		try:
			self.printQueue.put_nowait(("[TM] " + message, tag))
		except:
			ep.errorPopup("Exception in Terminal print:")	
	
	def _printE(self, prelude = "Exception in Terminal:"): # ===================
		
		self._printM(prelude + ' ' + traceback.format_exc(), 'E')

		# End _printE ==========================================================
