################################################################################
## Project: Fanclub Mark IV "Master" GUI          ## File: network.py         ##
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
 + Graphical interface for the FC network.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import os
import time as tm
import shutil as sh

import tkinter as tk
import tkinter.filedialog as fdg
import tkinter.ttk as ttk
import tkinter.font as fnt

## GLOBALS #####################################################################

""" Status codes. """
CONNECTED = 'C'
KNOWN = 'K'
DISCONNECTED = 'D'
AVAILABLE = 'A'
UPDATING = 'U'
TAGS = (CONNECTED, KNOWN, DISCONNECTED, AVAILABLE, UPDATING)

""" Status 'long' names. """
STATUSES = {
    CONNECTED : 'Connected',
    KNOWN : 'Known',
    DISCONNECTED : 'Disconnected',
    AVAILABLE : 'Available',
    UPDATING : 'Updating'
}

""" Status foreground colors. """
FOREGROUNDS = {
    CONNECTED : '#0e4707',
    KNOWN : '#44370b',
    DISCONNECTED : '#560e0e',
    AVAILABLE : '#666666',
    UPDATING : '#192560'
}

""" Status background colors. """
BACKGROUNDS = {
    CONNECTED : '#d1ffcc',
    KNOWN : '#fffaba',
    DISCONNECTED : '#ffd3d3',
    AVAILABLE : '#ededed',
    UPDATING : '#a6c1fc'
}

## BASE ########################################################################
class NetworkWidget(tk.Frame):
    """
    Container for all the FC network GUI front-end widgets, except the FC
    status bar.
    """

    DEMO_MESSAGES = {"Add":1,"Disconnect":2,"Reboot":3, "Remove": 4}
    DEMO_TARGETS = {"All":1, "Selected":2}

    def __init__(self, master, network, archive,
        printd = lambda s:None, printx = lambda e:None):
        """
        Create a new NetworkWidget inside MASTER, interfaced with the network
        backend using the NETWORK abstraction.
        (See fc.communicator.NetworkAbstraction.)

        Optionally, methods PRINTD and PRINTX as defined in fc.utils may
        be passed on to be used for print feedback.
        """
        # Core setup -----------------------------------------------------------
        tk.Frame.__init__(self, master)
        self.main = tk.Frame(self)
        self.main.pack(fill = tk.BOTH, expand = True, padx = 10, pady = 5)

        self.main.grid_columnconfigure(0, weight = 1)
        self.main.grid_rowconfigure(2, weight = 1)

        self.network = network

        self.printd, self.printx = printd, printx


        # ----------------------------------------------------------------------
        self.firmwareFrame = tk.LabelFrame(self.main, text = "Firmware Update")
        self.firmwareFrame.grid(row = 1, sticky = "EW")
        self.firmwareUpdate = FirmwareUpdateWidget(self.firmwareFrame, network,
            printd = printd, printx = printx)
        self.firmwareUpdate.pack(fill = tk.BOTH, expand = True)

        self.slaveList = SlaveListWidget(self.main, network)
        self.slaveList.grid(row = 2, sticky = "NEWS")

        self.networkFrame = tk.LabelFrame(self.main, text = "Network Control")
        self.networkFrame.grid(row = 0, sticky = "EW")
        self.networkControl = NetworkControlWidget(self.networkFrame, network,
            self.slaveList)
        self.networkControl.pack(fill = tk.BOTH, expand = True)


    def getNetworkControlWidget(self):
        return self.networkControl

    def getFirmwareUpdateWidget(self):
        return self.firmwareUpdate

    def getSlaveList(self):
        return self.slaveList

## WIDGETS #####################################################################

# Network control ==============================================================
class NetworkControlWidget(tk.Frame):
    """
    GUI front-end for the FC network control tools (such as adding and removing
    Slaves).
    """

    def __init__(self, master, network, slaveList):
        tk.Frame.__init__(self, master)
        self.network = network
        self.slaveList = slaveList

        frameconfig = {"side" : tk.TOP, "fill" : tk.BOTH, "expand" : True,
            "padx" : 10, "pady" : 5}

        # Connection ...........................................................
        self.isConnected = False
        self._connectCallback = network.connect
        self._disconnectCallback = network.disconnect

        self.connectionFrame = tk.Frame(self, relief = tk.RIDGE, bd = 1)
        self.connectionFrame.pack(**frameconfig)

        self.connectButton = tk.Button(self.connectionFrame, text = "Connect",
            command = self._onConnect, padx = 10, pady = 5, width = 12)
        self.connectButton.pack(side = tk.LEFT, padx = 0, fill = tk.Y)

        self.connectionVar = tk.StringVar()
        self.connectionVar.set("TEST")
        self.connectionLabel = tk.Label(self.connectionFrame,
            textvariable = self.connectionVar, width = 15,
            relief = tk.SUNKEN, font = "Courier 10 bold", padx = 10, pady = 5)
        self.connectionLabel.pack(side = tk.RIGHT, fill = tk.Y, pady = 5,
            padx = 10)

        self.activeWidgets = []

        # Target ...............................................................
        self.targetFrame = tk.Frame(self)
        self.targetFrame.pack(**frameconfig)

        self.targetLabel = tk.Label(self.targetFrame, text = "Target: ")
        self.targetLabel.pack(side = tk.LEFT)
        self.target = tk.IntVar()
        self.target.set(0)

        self.targetButtons = []

        # Message ..............................................................
        self.messageFrame = tk.Frame(self)
        self.messageFrame.pack(**frameconfig)

        self.messageLabel = tk.Label(self.messageFrame, text = "Message: ")
        self.messageLabel.pack(side = tk.LEFT)
        self.message = tk.IntVar()
        self.message.set(0)

        self.messageButtons = []

        # Send .................................................................
        self.sendFrame = tk.Frame(self)
        self.sendFrame.pack(**frameconfig)
        self.sendButton = tk.Button(self.sendFrame, text = "Send",
            command = self._send, padx = 10, pady = 5)
        self.sendButton.pack(side = tk.LEFT)
        self._sendCallback = network.sendMessage
        self.activeWidgets.append(self.sendButton)

        for message, code in self.network.messages():
            self._addMessage(message, code)
        for target, code in self.network.targets():
            self._addTarget(target, code)

        # Wrap-up ..............................................................
        self.disconnected()

    # API ......................................................................
    def connecting(self):
        """
        Indicate that a connection is being activated.
        """
        self.connectButton.config(state = tk.DISABLED, text = "Connecting")
        self._setWidgetState(tk.DISABLED)
        self.isConnected = False

    def connected(self):
        """
        Indicate that there is an active network connection.
        """
        self.connectButton.config(state = tk.NORMAL, text = "Disconnect",
            command = self._onDisconnect)
        self.connectionVar.set("Connected")
        self.connectionLabel.config(fg = FOREGROUNDS[CONNECTED])
        self._setWidgetState(tk.NORMAL)
        self.isConnected = True

    def disconnecting(self):
        """
        Indicate that a connection is being terminated.
        """
        self.connectButton.config(state = tk.DISABLED, text = "Disconnecting")
        self._setWidgetState(tk.DISABLED)
        self.isConnected = False

    def disconnected(self):
        """
        Indicate that there is an active network connection.
        """
        self.connectButton.config(state = tk.NORMAL, text = "Connect",
            command = self._onConnect)
        self.connectionVar.set("Disconnected")
        self.connectionLabel.config(fg = FOREGROUNDS[DISCONNECTED])
        self._setWidgetState(tk.DISABLED)
        self.isConnected = False

    # Internal methods .........................................................
    def _onConnect(self, *event):
        self._connectCallback()
        self.connected() # FIXME
        print("[WARNING] Widget connecting behavior not implemented")

    def _onDisconnect(self, *event):
        self._disconnectCallback()
        self.disconnected() # FIXME
        print("[WARNING] Widget disconnecting behavior not implemented")

    def _send(self, *E):
        """
        Send the selected target and
        message codes, as well as the current slave list selection.
        """
        self._sendCallback(self.target.get(), self.message.get(),
            self.slaveList.selected())

    def _setWidgetState(self, state):
        """
        Set the state of all network control 'interactive' widgets, such as
        buttons, to the Tkinter state STATE.
        """
        for button in self.activeWidgets:
            button.config(state = state)

    def _addTarget(self, name, code):
        """
        Allow the user to specify the target named NAME with the code CODE
        passed to the send callback.
        """
        button = tk.Radiobutton(self.targetFrame, text = name, value = code,
            variable = self.target, indicatoron = False, padx = 10, pady = 5)
        button.config(state = tk.NORMAL if self.isConnected else tk.DISABLED)

        button.pack(side = tk.LEFT, anchor = tk.W, padx = 5)
        self.targetButtons.append(button)
        self.activeWidgets.append(button)

        if len(self.targetButtons) is 1:
            self.target.set(code)

    def _addMessage(self, name, code):
        """
        Allow the user to send the message named NAME with the message code CODE
        passed to the send callback.
        """
        button = tk.Radiobutton(self.messageFrame, text = name, value = code,
            variable = self.message, indicatoron = False, padx = 10, pady = 5)
        button.config(state = tk.NORMAL if self.isConnected else tk.DISABLED)

        button.pack(side = tk.LEFT, anchor = tk.W, padx = 5)
        self.messageButtons.append(button)
        self.activeWidgets.append(button)

        if len(self.messageButtons) is 1:
            self.message.set(code)

# Firmware update ==============================================================
class FirmwareUpdateWidget(tk.Frame):
    """
    GUI front-end for the FC firmware update tools, i.e the Mark III
    "Bootloader."
    """
    def __init__(self, master, network,
        printd = lambda s:None, printx = lambda e:None):

        tk.Frame.__init__(self, master)
        # Setup ................................................................
        self.network = network

        self.main = tk.Frame(self)
        self.main.pack(fill = tk.BOTH, expand = True, padx = 10, pady = 5)
        self.setupWidgets = []

        self.printx = printx
        self.printd = printd

        # File .................................................................
        self.fileFrame = tk.Frame(self.main)
        self.fileFrame.pack(fill = tk.X, expand = True)

        self.fileLabel = tk.Label(self.fileFrame, text = "File: ", padx = 10,
            pady = 5)
        self.fileLabel.pack(side = tk.LEFT)

        self.filename = ""
        self.fileSize = 0
        self.fileVar = tk.StringVar()
        self.fileEntry = tk.Entry(self.fileFrame, textvariable = self.fileVar)
        self.fileEntry.pack(side = tk.LEFT, fill = tk.X, expand = True,
            padx = 10)
        self.fileEntry.config(state = tk.DISABLED)

        self.fileButton = tk.Button(self.fileFrame, text = "...",
            command = self._chooseFile)
        self.fileButton.pack(side = tk.LEFT)
        self.setupWidgets.append(self.fileButton)

        # Version ..............................................................
        self.bottomFrame = tk.Frame(self.main)
        self.bottomFrame.pack(fill = tk.X, expand = True)

        self.versionLabel = tk.Label(self.bottomFrame, text = "Version Code: ",
            padx = 10, pady = 5)
        self.versionLabel.pack(side = tk.LEFT)

        self.version = tk.StringVar()
        self.versionEntry = tk.Entry(self.bottomFrame, width = 10,
            textvariable = self.version, font = 'TkFixedFont')
        self.versionEntry.pack(side = tk.LEFT, fill = tk.X, expand = False,
            padx = 10)
        self.setupWidgets.append(self.versionEntry)

        # Start ................................................................
        self.startButton = tk.Button(self.bottomFrame, command = self._start,
            text = "Start", padx = 10, pady = 5)
        self.startButton.pack(side = tk.LEFT, padx = 20)
        self.inactiveLabelConfig = {'text':'(Inactive)', 'fg':'gray',
            'font':'TkDefaultFont'}
        self.readyLabelConfig = {'text':'Ready', 'fg':'black',
            'font':'TkDefaultFont'}
        self.liveLabelConfig = {'text':'LIVE', 'fg':'red',
            'font':'TkBoldFont'}
        self.statusLabel = tk.Label(self.bottomFrame, padx = 10, pady = 5,
            **self.inactiveLabelConfig)
        self.statusLabel.pack(side = tk.LEFT)

        self.start = network.startBootloader
        self.stop = network.stopBootloader

        self.fileVar.trace('w', self._checkReady)
        self.version.trace('w', self._checkReady)
        self._inactive()

    def _start(self, *args):
        """
        Start a firmware update.
        """
        self.startButton.config(text = "Starting", state = tk.DISABLED)
        self._setWidgetState(tk.DISABLED)
        self.start(self.filename, self.version.get(), self.fileSize)
        self._live()

    def _stop(self, *args):
        """
        Stop a firmware update.
        """
        self.startButton.config(text = "Stopping", state = tk.DISABLED)
        self.stop()
        self._ready()

    def _chooseFile(self, *args):
        try:
            self._setWidgetState(tk.DISABLED)
            self.fileVar.set(
                fdg.askopenfilename(
                    initialdir = os.getcwd(), # Get current working directory
                    title = "Choose file",
                    filetypes = (("Binary files","*.bin"),("All files","*.*"))
                )
            )
            self.fileEntry.xview_moveto(1.0)

            if len(self.fileVar.get()) > 0:

                self.fileSize = os.path.getsize(self.fileVar.get())

                # Move file to current directory:
                newFileName = os.getcwd() + \
                        os.sep + \
                        os.path.basename(self.fileVar.get())
                try:
                    sh.copyfile(self.fileVar.get(), newFileName)
                except sh.SameFileError:
                    pass

                self.filename = os.path.basename(newFileName)
                self.printd(
                    "Target binary:\n\tFile: {}"\
                    "\n\tSize: {} bytes"\
                    "\n\tCopied as \"{}\" for flashing".\
                    format(
                        self.fileVar.get(),
                        self.fileSize,
                        self.filename
                    )
                )
                self._checkReady()
            else:
                self._inactive()
        except Exception as e:
            self.printx(e)
            self._inactive()

    def _setWidgetState(self, state):
        """
        Set the state of the interface widgets (entries, file chooser button...)
        to STATE (either tk.NORMAL or tk.DISABLED).
        """
        for widget in self.setupWidgets:
            widget.config(state = state)

    def _inactive(self):
        """
        Set the widget as not ready to launch a firmware update.
        """
        self.startButton.config(text = "Start", command = self._start,
            state = tk.DISABLED)
        self.statusLabel.config(**self.inactiveLabelConfig)
        self._setWidgetState(tk.NORMAL)

    def _ready(self):
        """
        Set the widget as ready to launch an update.
        """
        self.startButton.config(text = "Start", command = self._start,
            state = tk.NORMAL)
        self.statusLabel.config(**self.readyLabelConfig)
        self._setWidgetState(tk.NORMAL)

    def _live(self):
        """
        Set the widget as currently running a firmware update.
        """
        self.startButton.config(text = "Stop", command = self._stop,
            state = tk.NORMAL)
        self.statusLabel.config(**self.liveLabelConfig)
        self._setWidgetState(tk.DISABLED)

    def _checkReady(self, *args):
        """
        Check whether the widget is ready to launch a firmware update and update
        its state accordingly. ARGS is ignored
        """
        if len(self.filename) > 0 and len(self.version.get()) > 0 \
            and self.fileSize > 0:
            self._ready()
        elif self.fileSize is 0 and len(self.filename) > 0:
            self.printx(RuntimeError("Given file \"{}\" is empty".format(
                self.filename)))
        else:
            self._inactive()

# Slave list ===================================================================
class SlaveListWidget(tk.Frame):
    """
    GUI front-end for the FC Slave List display.
    """


    """ Slave tuple indices. """
    I_INDEX = 0
    I_MAC = 1
    I_STATUS = 2
    I_FANS = 3
    I_VERSION = 4


    def __init__(self, master, network):
        tk.Frame.__init__(self, master)

        # Setup ................................................................
        self.network = network

        self.main = tk.LabelFrame(self, text = "Slave List",
            padx = 10, pady = 5)
        self.main.pack(fill = tk.BOTH, expand = True)

        self.main.grid_rowconfigure(1, weight = 1)
        self.main.grid_columnconfigure(0, weight = 1)

        bc = {'font':"TkDefaultFont 7"}

        # Options ..............................................................
        self.optionsFrame = tk.Frame(self.main, pady = 5)
        self.optionsFrame.grid(row = 2, sticky = "EW")

        self.sortButton = tk.Button(self.optionsFrame, text = "Sort",
            padx = 10, pady = 5, command = self.sort, **bc)
        self.sortButton.pack(side = tk.LEFT, padx = 10)

        self.selectAllButton = tk.Button(self.optionsFrame, text = "Select All",
            padx = 10, pady = 5, command = self._selectAll, **bc)
        self.selectAllButton.pack(side = tk.LEFT, padx = 10)

        self.deselectAllButton = tk.Button(self.optionsFrame,
            text = "Deselect All", padx = 10, pady = 5,
            command = self._deselectAll, **bc)
        self.deselectAllButton.pack(side = tk.LEFT, padx = 10)

        self.autoVar = tk.BooleanVar()
        self.autoVar.set(True)
        self.autoButton = tk.Checkbutton(self.optionsFrame,
            text = "Move on Change", variable = self.autoVar,
            indicatoron = False, padx = 10, pady = 5, **bc)
        self.autoButton.pack(side = tk.RIGHT, padx = 10)

        # Slave list ...........................................................
        self.slaveList = ttk.Treeview(self.main, selectmode = "extended")
        self.slaveList["columns"] = ("Index","MAC","Status","Fans", "Version")

        # Configure row height dynamically
        # See: https://stackoverflow.com/questions/26957845/
        #       ttk-treeview-cant-change-row-height
        font = fnt.Font(family = 'TkDefaultFont', size = 12)
        self.style = ttk.Style(self.winfo_toplevel())
        self.style.configure('Treeview',
            rowheight = font.metrics()['linespace'])

        # Create columns:
        self.slaveList.column('#0', width = 20, stretch = False)
        self.slaveList.column("Index", width = 20, anchor = "center")
        self.slaveList.column("MAC", width = 70, anchor = "center")
        self.slaveList.column("Status", width = 70, anchor = "center")
        self.slaveList.column("Fans", width = 50, stretch = True,
            anchor = "center")
        self.slaveList.column("Version", width = 50,
            anchor = "center")

        # Configure column headings:
        self.slaveList.heading("Index", text = "Index")
        self.slaveList.heading("MAC", text = "MAC")
        self.slaveList.heading("Status", text = "Status")
        self.slaveList.heading("Fans", text = "Fans")
        self.slaveList.heading("Version", text = "Version")

        # Configure tags:
        self.slaveList.tag_configure(
            CONNECTED,
            background = BACKGROUNDS[CONNECTED],
            foreground = FOREGROUNDS[CONNECTED],
            font = 'Courier 12 ')

        self.slaveList.tag_configure(
            UPDATING,
            background = BACKGROUNDS[UPDATING],
            foreground = FOREGROUNDS[UPDATING],
            font = 'Courier 12 bold')

        self.slaveList.tag_configure(
            DISCONNECTED,
            background = BACKGROUNDS[DISCONNECTED],
            foreground = FOREGROUNDS[DISCONNECTED],
            font = 'Courier 12 bold')

        self.slaveList.tag_configure(
            KNOWN,
            background = BACKGROUNDS[KNOWN],
            foreground = FOREGROUNDS[KNOWN],
            font = 'Courier 12 bold')

        self.slaveList.tag_configure(
            AVAILABLE,
            background = BACKGROUNDS[AVAILABLE],
            foreground = FOREGROUNDS[AVAILABLE],
            font = 'Courier 12 ')

        # Save previous selection:
        self.oldSelection = None

        # Bind command:
        self.slaveList.bind('<Double-1>', self._onDoubleClick)
        self.slaveList.bind('<Control-a>', self._selectAll)
        self.slaveList.bind('<Control-A>', self._selectAll)
        self.slaveList.bind('<Control-d>', self._deselectAll)
        self.slaveList.bind('<Control-D>', self._deselectAll)

        self.slaveList.grid(row = 1, sticky = "NEWS")

        # DATA -------------------------------------------------------------
        self.slaves = {}
        self.indices = []
        self.numSlaves = 0

        self.callback = lambda i: None

        print("[NOTE] No callback implemented for SlaveList double click")

    # API ......................................................................
    def addSlave(self, slave):
        """
        Add SLAVE to the list. ValueError is raised if a slave with that index
        already exists. SLAVE is expected to be a tuple (or list) of the form
            (INDEX, MAC, STATUS, FANS, VERSION)
        Where INDEX is an integer that is expected to be unique among slaves,
        MAC and VERSION are strings, STATUS is one of the status codes
        defined as class attributes of this class, FANS is an integer.
        """
        if slave[self.I_INDEX] in self.slaves:
            raise ValueError("Repeated Slave index {}".format(slave[self.I_INDEX]))
        elif slave[self.I_STATUS] not in TAGS:
            raise ValueError("Invalid status tag \"{}\"".format(
                slave[self.I_STATUS]))
        else:
            index = slave[self.I_INDEX]
            iid = self.slaveList.insert('', 0,
                values = (index + 1, slave[self.I_MAC],
                    STATUSES[slave[self.I_STATUS]], slave[self.I_FANS],
                    slave[self.I_VERSION]),
                tag = slave[self.I_STATUS])
            self.slaves[index] = slave + (iid,)
            self.indices.append(index)

    def addSlaves(self, slaves):
        """
        Iterate over SLAVES and add each Slave to the list. ValueError is
        raised if two slaves share the same index.
        """
        for slave in slaves:
            self.addSlave(slave)

    def updateSlave(self, slave):
        """
        Modify the entry on SLAVE. KeyError is raised if there is no slave
        with SLAVE's index.
        """
        index = slave[self.I_INDEX]
        iid = self.slaves[index][-1]

        self.slaveList.item(
            iid, values = (index + 1, slave[self.I_MAC],
                STATUSES[slave[self.I_STATUS]], slave[self.I_FANS],
                slave[self.I_VERSION]),
            tag = slave[self.I_STATUS])

        self.slaves[self.I_INDEX] = slave + (iid,)

        if self.autoVar.get():
            self.slaveList.move(iid, '', 0)

    def updateSlaves(self, slaves):
        """
        Iterate over SLAVES and update the existing entry on each one.
        ValueError is raised if one slave's index is not found.
        """
        for slave in slaves:
            self.updateSlave(slave)

    def setStatus(self, index, status):
        """
        Modify only the status of the Slave at index INDEX to STATUS.
        """
        slave = self.slaves[index]
        self.slaves[index] = slave[:self.I_STATUS] + (status,) \
            + slave[self.I_STATUS + 1:]

        self.slaveList.item(slave[-1],
            values = (index + 1, slave[self.I_MAC], STATUSES[status],
                slave[self.I_FANS], slave[self.I_VERSION]),
            tag = status)

        if self.autoVar.get():
            self.slaveList.move(self.slaves[index][-1], '', 0)

    def clear(self):
        """
        Empty the list.
        """
        for index, slave in self.slaves.items():
            self.slaveList.delete(slave[-1])
        self.slaves = {}
        self.indices = []

    def selected(self, status = None):
        """
        Return a list of the indices of slaves selected. STATUS (optional)
        returns a list of only the indices of slaves with such status code, if
        any exist.
        """
        selected = []
        for iid in self.slaveList.selection():
            if status is None \
                or self.slaveList.item(iid)['values'][self.I_STATUS] == status:
                selected.append(
                    self.slaveList.item(iid)['values'][self.I_INDEX] - 1)
        return selected

    def sort(self):
        """
        Sort the Slaves in ascending or descending (toggle) order of index.
        """
        self.indices.reverse()
        for index in self.indices:
            self.slaveList.move(self.slaves[index][-1], '', 0)


    # Internal methods .........................................................
    def _onDoubleClick(self, *A):
        if len(self.slaves) > 0:
            selected = self.selected()
            if len(selected) > 0:
                self.callback(selected[0])

    def _selectAll(self, *A):
        for index, slave in self.slaves.items():
            self.slaveList.selection_add(slave[-1])

    def _deselectAll(self, *A):
        self.slaveList.selection_set(())

# Network status bar ===========================================================
class StatusBarWidget(tk.Frame):
    """
    GUI front-end for the FC "status bar."
    """

    TOTAL = 'T'

    def __init__(self, master, network):
        tk.Frame.__init__(self, master)

        # Setup ................................................................
        self.network = network
        self.config(relief = tk.RIDGE, borderwidth = 2)

        # Status counters ......................................................
        self.statusFrame = tk.Frame(self, relief = tk.SUNKEN, borderwidth = 0)
        self.statusFrame.pack(side = tk.LEFT)

        self.statusFrames = {}
        self.statusVars, self.statusLabels, self.statusDisplays  = {}, {}, {}

        for code, name in ((self.TOTAL, "Total"),) + tuple(STATUSES.items()):
            self.statusFrames[code] = tk.Frame(self.statusFrame,
                relief = tk.SUNKEN, bd = 1)
            self.statusFrames[code].pack(side = tk.LEFT, padx = 5, pady = 3)

            self.statusVars[code] = tk.IntVar()
            self.statusVars[code].set(0)

            self.statusLabels[code] = tk.Label(self.statusFrames[code],
                text = name + ": ", font = "Courier 7", padx = 10, pady = 5,
                fg = FOREGROUNDS[code] if code in FOREGROUNDS else 'black')
            self.statusLabels[code].pack(side = tk.LEFT, pady = 5)

            self.statusDisplays[code] = tk.Label(self.statusFrames[code],
                textvariable = self.statusVars[code], font = "Courier 7",
                padx = 10, pady = 5,
                fg = FOREGROUNDS[code] if code in FOREGROUNDS else 'black')
            self.statusDisplays[code].pack(side = tk.LEFT)

        # Buttons ..............................................................
        self._shutdownCallback = network.shutdown

        self.buttonFrame = tk.Frame(self)
        self.buttonFrame.pack(side = tk.RIGHT, fill = tk.Y)

        self.shutdownButton = tk.Button(self.buttonFrame, text = "SHUTDOWN",
            command = self._onShutdown, padx = 10,
            font = "Calibri 9 bold",
            highlightbackground= 'black',
            activebackground = "#560e0e", activeforeground = "#ffd3d3",
            foreground ='#560e0e')
        self.shutdownButton.pack(side = tk.RIGHT, fill = tk.Y)


    # API ......................................................................
    def setCount(self, status, count):
        """
        Set the status counter that corresponds to status code STATUS to COUNT.
        """
        self.statusVars[status].set(count)

    def addCount(self, status, count = 1):
        """
        Add COUNT (defaults to 1) to the current value in the status counter
        that corresponds to status code STATUS.
        """
        self.statusVars[status].set(count + self.statusVars[status].get())

    def getCount(self, status):
        """
        Return the current count corresponding to status code STATUS.
        """
        return self.statusVars[status].get()

    def setTotal(self, count):
        """
        Set the total counter to COUNT.
        """
        self.statusVars[self.TOTAL].set(count)

    def addTotal(self, count = 1):
        """
        Add COUNT (defaults to 1) to the total counter.
        """
        self.statusVars[self.TOTAL].set(count + self.statusVars[self.TOTAL])

    def getTotal(self):
        """
        Return the current total.
        """
        return self.statusVars[self.TOTAL].get()

    def clear(self):
        """
        Set all counters to 0
        """
        for count in self.statusVars.values():
            count.set(0)

    # Internal methods .........................................................
    def _onShutdown(self, *event):
        self._shutdownCallback()

## DEMO ########################################################################
if __name__ == "__main__":
    # NOTE: outdated (since NetworkAbstraction implementation)
    print("FCMkIV Network GUI demo started")

    # Base
    mw = tk.Tk()
    NW = NetworkWidget(mw, printd = print, printx = print)
    N = NW.getNetworkControlWidget()

    for i in range(1, 4):
        N.addTarget("Target {}".format(i), i)
        N.addMessage("Message {}".format(i), i)

    def callback(t, m):
        print("Sending message [{}] to target [{}]".format(m, t))

    N.setCallback(callback)

    S = NW.getSlaveList()

    S.addSlaves((
        (0, "XX:XX", 'D', 69, 'FAKE'),
        (1, "XX:XX", 'D', 69, 'FAKE'),
        (2, "XX:XX", 'D', 69, 'FAKE'),
        (3, "XX:XX", 'D', 69, 'FAKE'),
    ))

    S.updateSlave((0, "XX:XX", 'C', 69, 'FAKE'))
    S.setStatus(1, 'A')

    mw.grid_columnconfigure(0, weight = 1)
    mw.grid_rowconfigure(0, weight = 1)
    NW.grid(row = 0, sticky = "NEWS")

    SB = StatusBarWidget(mw)
    SB.grid(row = 1, sticky = "EW")

    SB.setCount(CONNECTED, 10)
    for i in range(3):
        SB.addCount(DISCONNECTED)

    SB.addCount(CONNECTED, -1)
    SB.setTotal(SB.getCount(CONNECTED))

    mw.mainloop()

    print("FCMkIV Network GUI demo finished")
