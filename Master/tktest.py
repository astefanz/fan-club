# GUI:
from mttkinter import mtTkinter as Tk
#import Tkinter as Tk
import tkFileDialog 
import tkMessageBox
import tkFont
import ttk # "Notebooks"

# System:
import threading
import time
import traceback
import os # Get current working directory & check file names
import sys # Exception handling
import inspect # get line number for debugging
import multiprocessing as mp

# Data:
import numpy as np
import Queue

# FCMkII:
import FCCommunicator as cm
import FCPRCommunicator as pc
import FCArchiver as ac
import FCPrinter as pt
import FCSlave as sv

import fci.FCPRGrid as gd
import fci.SlaveList as sl
import fci.Terminal as tm

import FCInterface

from auxiliary.debug import d

SPAWN = 1
TERMINATE = -1

def f(a):
	tl = Tk.Toplevel()
	tl.mainloop()


def spawn(prs):
	prs.append(mp.Process(target = f, args = (1,)))
	prs[-1].daemon = True
	prs[-1].start()

def spawner(pipeOut):
	pl = []
	while True:
		if pipeOut.poll():
			msg = pipeOut.recv()
			if msg is SPAWN:
				spawn(pl)
			elif msg is TERMINATE:
				break

pipeOut, pipeIn = mp.Pipe(False)

def sendSpawn():
	pipeIn.send(SPAWN)

def sendTerminate():
	pipeIn.send(TERMINATE)

def spawnFCI():
	fci = FCInterface.FCInterface("Test")
	fci.mainloop()

spawnProcess = mp.Process(target = spawner, args = (pipeOut,))
spawnProcess.start()

spawnFCIProcess = mp.Process(target = spawnFCI)
spawnFCIProcess.start()

root = Tk.Tk()
button = Tk.Button(root, text = "Spawn Process", command = sendSpawn)
button.pack()
button2 = Tk.Button(root, text = "End", command = sendTerminate)
button2.pack()
root.mainloop()

