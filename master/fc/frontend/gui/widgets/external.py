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
 + External control widget.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

 ## IMPORTS ####################################################################
import os
import time as tm
import random as rd
import multiprocessing as mp
import copy as cp

import tkinter as tk
import tkinter.filedialog as fdg
import tkinter.ttk as ttk
import tkinter.font as fnt

from fc.frontend.gui import guiutils as gus
from fc import archive as ac, printer as pt, standards as s

## CLASSES #####################################################################
class ExternalControlWidget(pt.PrintClient, tk.Frame):
    """
    Front end for external control.
    """
    SYMBOL = "[FX]"

    MODULE_BROADCAST, MODULE_LISTENER = 0, 1

    def __init__(self, master, archive, backend, pqueue):
        """
        - master := tkiner parent widget.
        - archive := FCMkIV Archive instance.
        - backend := ExternalControl back end.
        - vertical := bool, whether the widget will be taller than it is wide.
        - pqueue := Queue instance for printing (see fc.utils).
        """
        tk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

        self.archive = archive
        self.backend = backend
        self.modules = {}

        self.setters = {
            s.EX_BROADCAST: {
                s.EX_ACTIVE: self._startBroadcastBackEnd,
                s.EX_INACTIVE: self._stopBroadcastBackEnd
            },
            s.EX_LISTENER: {
                s.EX_ACTIVE: self._startListenerBackEnd,
                s.EX_INACTIVE: self._stopListenerBackEnd
            }
        }

        # Build GUI ............................................................
        self.grid_columnconfigure(0, weight = 1)
        row = 0

        self.allFrame = tk.Frame(self)
        self.allFrame.grid(row = row, column = 0, sticky = "EW")
        self.startAllButton = tk.Button(self.allFrame, text = "Start All",
            command = self._onStartAll, **gus.fontc)
        self.startAllButton.pack(side = tk.LEFT, fill = tk.X, expand = True)
        self.stopAllButton = tk.Button(self.allFrame, text = "Stop All",
            command = self._onStopAll, **gus.fontc)
        self.stopAllButton.pack(side = tk.LEFT, fill = tk.X, expand = True)
        row += 1

        self.broadcast = ECSetupWidget(self, "State Broadcast",
            self._startBroadcastBackEnd, self._stopBroadcastBackEnd,
            defaultIP = self.archive[ac.externalDefaultBroadcastIP],
            defaultPort = self.archive[ac.externalDefaultBroadcastPort],
            defaultRepeat = self.archive[ac.externalDefaultRepeat],
            editIP = True,
            )

        self.broadcast.grid(row = row, column = 0, sticky = "EW")
        row += 1
        self.modules[s.EX_BROADCAST] = self.broadcast

        self.listener = ECSetupWidget(self, "Command Listener",
            self._startListenerBackEnd, self._stopListenerBackEnd,
            defaultIP = self.archive[ac.externalDefaultListenerIP],
            defaultPort = self.archive[ac.externalDefaultListenerPort],
            defaultRepeat = self.archive[ac.externalDefaultRepeat],
            editIP = False)
        self.listener.grid(row = row, column = 0, sticky = "EW")
        row += 1
        self.modules[s.EX_LISTENER] = self.listener

        # Wrap-up ..............................................................
        self.backend.setCallbacks(
            setFEBroadcastStatus = self.setBroadcast,
            setFEBroadcastOut = self.broadcast.setOutputIndex,
            setFEListenerStatus = self.setListener,
            setFEListenerIn = self.listener.setInputIndex,
            setFEListenerOut = self.listener.setOutputIndex)

    # API ----------------------------------------------------------------------
    def set(self, key, value, backend = True):
        try:
            self.modules[key].setActive(value)
        except Exception as e:
            self.printx(e, "Exception while {}activating {}".format(
                "de" if value == s.EX_INACTIVE else "", s.EX_NAMES[key]))
            if value == s.EX_ACTIVE:
                self.set(key, s.EX_INACTIVE)

    def setBroadcast(self, value):
        self.set(s.EX_BROADCAST, value)

    def startBroadcast(self):
        self.set(s.EX_BROADCAST, s.EX_ACTIVE)

    def stopBroadcast(self):
        self.set(s.EX_BROADCAST, s.EX_INACTIVE)

    def setListener(self, value):
        self.set(s.EX_LISTENER, value)

    def startListener(self):
        self.set(s.EX_LISTENER, s.EX_ACTIVE)

    def stopListener(self):
        self.set(s.EX_LISTENER, s.EX_INACTIVE)

    def startAll(self):
        self._startBroadcastBackEnd()
        self._startListenerBackEnd()

    def stopAll(self):
        self._stopBroadcastBackEnd()
        self._stopListenerBackEnd()

    # Internal methods ---------------------------------------------------------
    def _startBroadcastBackEnd(self):
        self.backend.activateBroadcast(
            target = (self.broadcast.getIP(), self.broadcast.getPort()),
            repeat = self.broadcast.getRepeat())

    def _stopBroadcastBackEnd(self):
        self.backend.deactivateBroadcast()

    def _startListenerBackEnd(self):
        self.backend.activateListener(port = self.listener.getPort(),
            repeat = self.listener.getRepeat())

    def _stopListenerBackEnd(self):
        self.backend.deactivateListener()

    def _onStartAll(self, *_):
        self.startAll()

    def _onStopAll(self, *_):
        self.stopAll()

class ECSetupWidget(tk.Frame):
    """
    General front end for either the external control listener server or the
    external control broadcast server.
    """

    DISP_CONFIG_GENERAL = {'font':'TkFixedFont 7 bold', 'relief':tk.SUNKEN,
        'bd':2}
    DISP_CONFIG_ACTIVE = {'text' : 'Active',
        'fg' : s.FOREGROUNDS[s.SS_CONNECTED],
        'bg' : s.BACKGROUNDS[s.SS_CONNECTED]}
    DISP_CONFIG_INACTIVE = {'text' : 'Inactive',
        'fg' : s.FOREGROUNDS[s.SS_DISCONNECTED],
        'bg' : s.BACKGROUNDS[s.SS_DISCONNECTED]}
    DISP_CONFIGS = {s.EX_ACTIVE : DISP_CONFIG_ACTIVE,
        s.EX_INACTIVE : DISP_CONFIG_INACTIVE}

    PARAM_IP, PARAM_PORT, PARAM_REPEAT = 0, 1, 2
    PARAMETERS = (PARAM_IP, PARAM_PORT, PARAM_REPEAT)
    TYPES = {
        PARAM_IP : str,
        PARAM_PORT : int,
        PARAM_REPEAT : int,
    }

    def __init__(self, master, title, startf, stopf,
        defaultIP, defaultPort, defaultRepeat, editIP):
        """
        - title := str, text to put on top label.
        - master := tkinter master widget.
        - startf := function to be called with no arguments upon start.
        - stopf := function to be called with no arguments upon stop.
        - default* := default value for the corresponding parameter.
        - editIP := bool, whether the IP address is user-editable.
        """
        tk.Frame.__init__(self, master)
        self.startf, self.stopf = startf, stopf
        self.title = title
        self.defaultIP = defaultIP
        self.defaultPort = defaultPort
        self.defaultRepeat = defaultRepeat
        self.editIP = editIP
        self.defaults = {
            self.PARAM_IP : self.defaultIP,
            self.PARAM_PORT : self.defaultPort,
            self.PARAM_REPEAT : self.defaultRepeat,
        }
        self.setters =  {
            self.PARAM_IP : self.setIP,
            self.PARAM_PORT : self.setPort,
            self.PARAM_REPEAT : self.setRepeat,
        }
        self.disabled =  {
            self.PARAM_IP : not self.editIP,
            self.PARAM_PORT : False,
            self.PARAM_REPEAT : False,
        }
        self.entries = {}
        self.active = None
        self.activeWidgets = []
        validateN = self.register(gus._validateN)
        def anything(*_):
            return True
        validateA = self.register(anything)

        # GUI ..................................................................
        # Main Layout:
        self.main = tk.LabelFrame(self, text = title, **gus.fontc)
        self.main.pack(fill = tk.BOTH, expand = True)
        rows, columns = (0, 1, 2, 3), (0, 1)

        top, mid, low, bottom = rows
        left, right = columns

        for column in columns:
            self.main.grid_columnconfigure(column, weight = 1)

        # Active display:
        self.activeDisplay = tk.Label(self.main, **self.DISP_CONFIG_GENERAL)
        self.activeDisplay.grid(row = top, column = left, sticky = "EW")

        # Indices:

        self.inputIndexFrame = self._gridFrame(self.main, mid, left)
        _, self.inputIndexEntry = self._entryPair(self.inputIndexFrame,
            self.PARAM_REPEAT, "In: ", validateN, active = False)
        self.inputIndexVar = tk.IntVar()
        self.inputIndexEntry.config(state = tk.DISABLED,
            textvariable = self.inputIndexVar)
        self.outputIndexFrame = self._gridFrame(self.main, low, left)
        _, self.outputIndexEntry = self._entryPair(self.outputIndexFrame,
            self.PARAM_REPEAT, "Out: ", validateN, active = False)
        self.outputIndexVar = tk.IntVar()
        self.outputIndexEntry.config(state = tk.DISABLED,
            textvariable = self.outputIndexVar)

        # IP and Port:
        self.ipFrame = self._gridFrame(self.main, top, right)
        _, self.ipEntry = self._entryPair(self.ipFrame, self.PARAM_IP, "IP: ",
            validateA, self.editIP, 15)
        if not self.editIP:
            self.ipEntry.config(state = tk.DISABLED)
        self.portFrame = self._gridFrame(self.main, mid, right)
        _, self.portEntry = self._entryPair(self.portFrame, self.PARAM_PORT,
            "Port: ", validateN)

        # Index and Repeat:
        self.repeatFrame = self._gridFrame(self.main, low, right)
        _, self.repeatEntry = self._entryPair(self.repeatFrame,
            self.PARAM_REPEAT, "Repeat: ", validateN)

        # Start and stop button:
        self.startStopFrame = self._gridFrame(self.main, bottom, left)
        self.startStopButton = tk.Button(self.startStopFrame, text = "Start",
            command = self._onStart, **gus.fontc)
        self.startStopButton.pack(fill = tk.X, expand = True)

        self.ssb_configs = {
            s.EX_ACTIVE:    {'text':'Stop', 'command':self._onStop},
            s.EX_INACTIVE: {'text':'Start', 'command':self._onStart}
            }

        # Default button:
        self.defaultFrame = self._gridFrame(self.main, bottom, right)
        self.defaultButton = tk.Button(self.defaultFrame, text = "Defaults",
            command = self._onDefault, **gus.fontc)
        self.defaultButton.pack(fill = tk.X, expand = True)
        self.activeWidgets.append(self.defaultButton)

        # Wrap up ..............................................................
        self.setDefaults()
        self.setActive(False)

    # API ----------------------------------------------------------------------
    def setActive(self, active):
        """
        Configure the widget to the corresponding status (either active or
        inactive as defined in the corresponding class attributes)
        """
        self.config(tk.DISABLED if active == s.EX_ACTIVE else tk.NORMAL)
        self.startStopButton.config(**self.ssb_configs[active])
        self.activeDisplay.config(**self.DISP_CONFIGS[active])
        self.active = active

    def isActive(self):
        return self.active

    def getRepeat(self):
        return self._get(self.PARAM_REPEAT)

    def getIP(self):
        return self._get(self.PARAM_IP)

    def getPort(self):
        return self._get(self.PARAM_PORT)

    def setInputIndex(self, index):
        self.inputIndexVar.set(index)

    def setOutputIndex(self, index):
        self.outputIndexVar.set(index)

    def setIP(self, ip):
        self._set(self.PARAM_IP, ip)

    def setPort(self, port):
        self._set(self.PARAM_PORT, port)

    def setRepeat(self, repeat):
        self._set(self.PARAM_REPEAT, repeat)

    def setDefaults(self):
        for parameter in self.PARAMETERS:
            self._set(parameter, self.defaults[parameter])

    def config(self, state):
        """
        Set the state of all active widgets.
        - state: either tkinter.NORMAL or tkinter.DISABLED.
            """
        for widget in self.activeWidgets:
            widget.config(state = state)

    # Internal methods ---------------------------------------------------------
    def _set(self, parameter, value):
        disabled = self.disabled[parameter] or self.active
        entry = self.entries[parameter]
        entry.config(state = tk.NORMAL)
        entry.delete(0, tk.END)
        entry.insert(0, value)
        if disabled:
            entry.config(state = tk.DISABLED)

    def _get(self, parameter):
        return self.TYPES[parameter](self.entries[parameter].get())

    def _onStart(self, *_):
        self.startf()

    def _onStop(self, *_):
        self.stopf()

    def _onDefault(self, *_):
        self.setDefaults()

    def _gridFrame(self, master, row, column, columnspan = 1):
        """
        Repetitive behavior to build a frame in one of the grid containers. The
        frame is constructed and "gridded" before being returned.
        """
        frame =  tk.Frame(master)
        frame.grid(row = row, column = column, sticky = "NEWS",
            columnspan = columnspan)
        return frame

    def _entryPair(self, master, key, text, validator, active = True,width = 7):
        """
        Repetitive behavior to build a label-entry pair in the given container.
        Packs the two widgets and returns them as a tuple of the form
        (label, entry).
        - master := Tkinter parent widget. Must use "Pack" layout manager.
        - key := "PARAM_" key to add to the entry dictionary.
        - text := str, text to display in label.
        - validator := Tkinter-compatible "validator" function. Must be
            already registered.
        - active := bool, whether to add the entry to the list of "active"
            widgets.
        """


        label = tk.Label(master, text = text, **gus.fontc, width = 7,
            anchor = 'e')
        label.pack(side = tk.LEFT)

        entry = tk.Entry(master, **gus.efont, validate = "key",
            validatecommand = (validator, '%S', '%s', '%d'),
            disabledforeground = 'black')
        entry.pack(side = tk.LEFT, fill = tk.X, expand = True)
        if active:
            self.activeWidgets.append(entry)
        self.entries[key] = entry

        return label, entry

