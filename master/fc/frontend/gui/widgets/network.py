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
 + REMARKS:
 + - For simplicity's sake, initial archive data is ignored, (e.g saved Slaves
 +   are not initialized into the Slave list during construction). Instead,
 +   such data is expected to be received from Communicator status updates.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import os
import time as tm
import shutil as sh

import tkinter as tk
import tkinter.filedialog as fdg
import tkinter.ttk as ttk
import tkinter.font as fnt

from fc.frontend.gui import guiutils as gus
from fc import standards as s, printer as pt

## GLOBALS #####################################################################
TEST_VECTORS = [
    [],
    [
        0, "T1", "MAC_ADDR", s.SS_CONNECTED, 21, "vx.x.x"
    ],
    [
        0, "T1", "MAC_ADDR", s.SS_CONNECTED, 21, "vx.x.x",
        1, "T2", "MAC_ADDR", s.SS_DISCONNECTED, 21, "vx.x.x",
        2, "T3", "MAC_ADDR", s.SS_AVAILABLE, 21, "vx.x.x"
    ],
    [
        1, "T2", "MAC_ADDR", s.SS_CONNECTED, 21, "vx.x.x",
        2, "T3", "MAC_ADDR", s.SS_CONNECTED, 21, "vx.x.x"
    ]
]

## BASE ########################################################################
class NetworkWidget(tk.Frame, pt.PrintClient):
    """
    Container for all the FC network GUI front-end widgets, except the FC
    status bar.
    """
    SYMBOL = "[NW]"

    def __init__(self, master, network, archive, networkAdd, slavesAdd, pqueue):
        """
        Create a new NetworkWidget inside MASTER, interfaced with the network
        backend using the NETWORK abstraction.
        (See fc.communicator.NetworkAbstraction.)

        NETWORKADD and SLAVESADD are methods to be called on widgets that
        expect to receive incoming network and slaves vectors, respectively.

        PQUEUE is the Queue object to be used for I-P printing.
        """
        # Core setup -----------------------------------------------------------
        tk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

        self.main = tk.Frame(self)
        self.main.pack(fill = tk.BOTH, expand = True, padx = 10, pady = 5)

        self.main.grid_columnconfigure(0, weight = 1)
        self.main.grid_rowconfigure(2, weight = 1)

        self.networkAdd, self.slavesAdd = networkAdd, slavesAdd
        self.network = network

        # ----------------------------------------------------------------------
        self.firmwareFrame = tk.LabelFrame(self.main, text = "Firmware Update")
        self.firmwareFrame.grid(row = 1, sticky = "EW")
        self.firmwareUpdate = FirmwareUpdateWidget(self.firmwareFrame, network,
            pqueue)
        self.firmwareUpdate.pack(fill = tk.BOTH, expand = True)

        self.slaveList = SlaveListWidget(self.main, network, pqueue)
        self.slaveList.grid(row = 2, sticky = "NEWS")

        self.networkFrame = tk.LabelFrame(self.main, text = "Network Control")
        self.networkFrame.grid(row = 0, sticky = "EW")
        self.networkControl = NetworkControlWidget(self.networkFrame, network,
            self.slaveList, pqueue)
        self.networkControl.pack(fill = tk.BOTH, expand = True)
        self.networkControl.addClient(self.firmwareUpdate)

        self.networkAdd(self.networkControl)
        self.slavesAdd(self.slaveList)

    def profileChange(self):
        self.slaveList.clear()

## WIDGETS #####################################################################

# Network control ==============================================================
class NetworkControlWidget(tk.Frame, pt.PrintClient):
    """
    GUI front-end for the FC network control tools (such as adding and removing
    Slaves).
    """
    NO_IP = "[NO IP]"
    NO_PORT = "[NO PORT]"

    def __init__(self, master, network, slaveList, pqueue):
        """
        Create a new NetworkControlWidget.

        MASTER := Tkinter parent widget
        NETWORK := NetworkAbstraction for this system
        SLAVELIST := SlaveList instance from which to fetch selections for
            control messages
        PQUEUE := Queue instance to use for I-P printing
        """

        tk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

        self.network = network
        self.slaveList = slaveList

        frameconfig = {"side" : tk.TOP, "fill" : tk.BOTH, "expand" : True,
            "padx" : 10, "pady" : 5}

        self.clients = [slaveList]
        # Connection ...........................................................

        # Information to display:
        # - IP Address
        # - Broadcast port
        # - Broadcast IP
        # - Listener port

        self.isConnected = False
        self._connectCallback = network.connect
        self._disconnectCallback = network.disconnect

        self.connectionFrame = tk.Frame(self, relief = tk.RIDGE, bd = 1)
        self.connectionFrame.pack(**frameconfig)

        # Connect button:
        self.connectButton = tk.Button(self.connectionFrame, text = "Connect",
            command = self._onConnect, padx = 10, pady = 5, width = 12)
        self.connectButton.pack(side = tk.LEFT, padx = 0, fill = tk.Y)

        # Displays:
        self.ips = []
        self.ports = []

        # IP Address:
        self.ipVar = tk.StringVar()
        self.ipVar.set(self.NO_IP)
        self.ips.append(self.ipVar)
        self.__addDisplay("IP Address", self.ipVar)

        # Broadcast IP:
        self.bcipVar = tk.StringVar()
        self.bcipVar.set(self.NO_IP)
        self.ips.append(self.bcipVar)
        name = "Broadcast IP"
        self.bcipFrame = tk.Frame(self.connectionFrame, relief = tk.RIDGE,
            bd = 1)
        self.bcipFrame.pack(side = tk.RIGHT, fill = tk.Y, pady = 5, padx = 10)

        self.bcipLabel = tk.Label(self.bcipFrame, text = name + ":",
            font = "TkDefaultFont 7")
        self.bcipLabel.pack(side = tk.TOP, fill = tk.X, padx = 10)

        self.bcipDisplay = gus.PromptLabel(self.bcipFrame,
            title = "Edit broadcast IP",
            prompt = "Enter a valid IP address (IPv4) to which to send "
            "broadcast messages. \n"
            "To send to all addresses on the default "\
            "interface, leave the field empty.",
            callback = self._setBroadcastIP,
            starter = self.bcipVar.get,
            background = "white",
            textvariable = self.bcipVar, width = 15,
            relief = tk.SUNKEN, font = "Courier 7", padx = 10, pady = 5)
        self.bcipDisplay.pack(side = tk.TOP, fill = tk.X, pady = 5, padx = 10)

        # Broadcast port:
        self.bcVar = tk.StringVar()
        self.bcVar.set(self.NO_PORT)
        self.ports.append(self.bcVar)
        self.__addDisplay("Broadcast Port", self.bcVar)

        # Listener port:
        self.ltVar = tk.StringVar()
        self.ltVar.set(self.NO_PORT)
        self.ports.append(self.ltVar)
        self.__addDisplay("Listener Port", self.ltVar)

        # Connection display:
        self.connectionVar = tk.StringVar()
        self.connectionVar.set("[NO CONNECTION]")
        self.connectionLabel = tk.Label(self.connectionFrame,
            textvariable = self.connectionVar, width = 15,
            relief = tk.SUNKEN, font = "Courier 7 bold", padx = 10, pady = 5)
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
        self._sendCallback = network.commandIn
        self.activeWidgets.append(self.sendButton)

        for message, code in s.MESSAGES.items():
            self._addMessage(message, code)
        for target, code in s.TARGETS.items():
            self._addTarget(target, code)

        # Wrap-up ..............................................................
        self.disconnected()

    # API ......................................................................
    def networkIn(self, N):
        """
        Process a new network state vector N. See standards.py for form.
        """
        connected = N[0]
        if connected:
            if not self.isConnected:
                self.connected()
            self.ipVar.set(N[1])
            self.bcipVar.set(N[2])
            self.bcVar.set(N[3])
            self.ltVar.set(N[4])
        else:
            self.disconnected()

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
        self.connectionLabel.config(fg = s.FOREGROUNDS[s.SS_CONNECTED],
            bg = s.BACKGROUNDS[s.SS_CONNECTED])
        self._setWidgetState(tk.NORMAL)
        for client in self.clients:
            client.connected()
        self.bcipDisplay.enable()
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
        for ip in self.ips:
            ip.set(self.NO_IP)
        for port in self.ports:
            port.set(self.NO_PORT)
        for client in self.clients:
            client.disconnected()
        self.connectionLabel.config(fg = s.FOREGROUNDS[s.SS_DISCONNECTED],
            bg = s.BACKGROUNDS[s.SS_DISCONNECTED])
        self._setWidgetState(tk.DISABLED)
        self.bcipDisplay.disable()
        self.isConnected = False

    def addClient(self, client):
        """
        Add CLIENT to the list of widgets to update by calling
        client.connected or client.disconnected upon the corresponding changes
        of status.
        """
        self.clients.append(client)

    def connect(self):
        """
        API to trigger connection. Equivalent to pressing the connect button.
        NOTE: Should be called only when disconnected.
        """
        self._onConnect()


    def disconnect(self):
        """
        API to trigger disconnection. Equivalent to pressing the disconnect
        button.

        NOTE: Should be called only when connected.
        """
        self._onDisconnect()

    # Internal methods .........................................................
    def _onConnect(self, *event):
        self._connectCallback()

    def _onDisconnect(self, *event):
        self._disconnectCallback()

    def _send(self, *E):
        """
        Send the selected target and
        message codes, as well as the current slave list selection.
        """
        self._sendCallback(self.message.get(), self.target.get(),
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

    def __addDisplay(self, name, variable):
        """
        Private method to add labels to display connection status variables.
        """

        frame = tk.Frame(self.connectionFrame, relief = tk.RIDGE, bd = 1)
        frame.pack(side = tk.RIGHT, fill = tk.Y, pady = 5, padx = 10)

        label = tk.Label(frame, text = name + ":", font = "TkDefaultFont 7")
        label.pack(side = tk.TOP, fill = tk.X, padx = 10)

        display = tk.Label(frame, textvariable = variable, width = 15,
            relief = tk.SUNKEN, font = "Courier 7", padx = 10, pady = 5)
        display.pack(side = tk.TOP, fill = tk.X, pady = 5, padx = 10)

    def _setBroadcastIP(self, ip):
        """
        Send a command to the Communicator to change the broadcast IP, if
        connected.

        - ip := String, the new IP address to set.
        """
        if ip == "":
            ip = "<broadcast>"
        if self.isConnected and ip is not None:
            self.network.broadcastIP(ip)
            self.printr("Sent broadcast IP change request (\"{}\")".format(ip))

# Firmware update ==============================================================
class FirmwareUpdateWidget(tk.Frame, pt.PrintClient):
    """
    GUI front-end for the FC firmware update tools, i.e the Mark III
    "Bootloader."
    """
    SYMBOL = "[FU]"
    READY, LIVE, INACTIVE = range(3)

    def __init__(self, master, network, pqueue):
        """
        Create a new FirmwareUpdateWidget.

        MASTER := Tkinter parent widget
        NETWORK := NetworkAbstraction being used
        PQUEUE := Queue instance for I-P printing
        """
        tk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

        # Setup ................................................................
        self.network = network

        self.main = tk.Frame(self)
        self.main.pack(fill = tk.BOTH, expand = True, padx = 10, pady = 5)
        self.setupWidgets = []

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
        self.status = self.INACTIVE
        self._inactive()

        print("[NOTE] Confirm firmware update status consistency?")

    # API ......................................................................
    def connected(self):
        """
        Called when the network switches from disconnected to connected.
        """
        pass

    def disconnected(self):
        """
        Called when the network switches from connected to disconnected.
        """
        self._stop()

    # Internal methods .........................................................
    def _start(self, *args):
        """
        Start a firmware update.
        """
        if self.status is self.READY:
            self.startButton.config(text = "Starting", state = tk.DISABLED)
            self._setWidgetState(tk.DISABLED)
            self.start(self.filename, self.version.get(), self.fileSize)
            self._live()

    def _stop(self, *args):
        """
        Stop an ongoing firmware update if there is one.
        """
        if self.status is self.LIVE:
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
        self.status = self.INACTIVE

    def _ready(self):
        """
        Set the widget as ready to launch an update.
        """
        self.startButton.config(text = "Start", command = self._start,
            state = tk.NORMAL)
        self.statusLabel.config(**self.readyLabelConfig)
        self._setWidgetState(tk.NORMAL)
        self.status = self.READY

    def _live(self):
        """
        Set the widget as currently running a firmware update.
        """
        self.startButton.config(text = "Stop", command = self._stop,
            state = tk.NORMAL)
        self.statusLabel.config(**self.liveLabelConfig)
        self._setWidgetState(tk.DISABLED)
        self.status = self.LIVE

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
class SlaveListWidget(tk.Frame, pt.PrintClient):
    """
    GUI front-end for the FC Slave List display.
    """
    SYMBOL = "[SL]"

    def __init__(self, master, network, pqueue):
        """
        Create a new SlaveList widget.

        MASTER := Tkinter parent widget
        NETWORK := NetworkAbstraction being used
        PQUEUE := Queue object for I-P printing
        """

        tk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

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
        self.slaveList["columns"] = \
            ("Index","Name","MAC","Status","Fans", "Version")

        # Configure row height dynamically
        # See: https://stackoverflow.com/questions/26957845/
        #       ttk-treeview-cant-change-row-height
        self.listFontSize = 8
        font = fnt.Font(family = 'TkDefaultFont', size = self.listFontSize)
        self.style = ttk.Style(self.winfo_toplevel())
        self.style.configure('Treeview',
            rowheight = font.metrics()['linespace'] + 2)

        # Create columns:
        self.slaveList.column('#0', width = 20, stretch = False)
        self.slaveList.column("Index", width = 20, anchor = "center")
        self.slaveList.column("Name", width = 20, anchor = "center")
        self.slaveList.column("MAC", width = 80, anchor = "center")
        self.slaveList.column("Status", width = 70, anchor = "center")
        self.slaveList.column("Fans", width = 50, stretch = True,
            anchor = "center")
        self.slaveList.column("Version", width = 50, anchor = "center")

        # Configure column headings:
        self.slaveList.heading("Index", text = "Index")
        self.slaveList.heading("Name", text = "Name")
        self.slaveList.heading("MAC", text = "MAC")
        self.slaveList.heading("Status", text = "Status")
        self.slaveList.heading("Fans", text = "Fans")
        self.slaveList.heading("Version", text = "Version")

        # Configure tags:
        self.slaveList.tag_configure(
            s.SS_CONNECTED,
            background = s.BACKGROUNDS[s.SS_CONNECTED],
            foreground = s.FOREGROUNDS[s.SS_CONNECTED],
            font = 'Courier {} '.format(self.listFontSize))

        self.slaveList.tag_configure(
            s.SS_UPDATING,
            background = s.BACKGROUNDS[s.SS_UPDATING],
            foreground = s.FOREGROUNDS[s.SS_UPDATING],
            font = 'Courier {} bold'.format(self.listFontSize))

        self.slaveList.tag_configure(
            s.SS_DISCONNECTED,
            background = s.BACKGROUNDS[s.SS_DISCONNECTED],
            foreground = s.FOREGROUNDS[s.SS_DISCONNECTED],
            font = 'Courier {} bold'.format(self.listFontSize))

        self.slaveList.tag_configure(
            s.SS_KNOWN,
            background = s.BACKGROUNDS[s.SS_KNOWN],
            foreground = s.FOREGROUNDS[s.SS_KNOWN],
            font = 'Courier {} bold'.format(self.listFontSize))

        self.slaveList.tag_configure(
            s.SS_AVAILABLE,
            background = s.BACKGROUNDS[s.SS_AVAILABLE],
            foreground = s.FOREGROUNDS[s.SS_AVAILABLE],
            font = 'Courier {} '.format(self.listFontSize))

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
        self.testi = 0

        print("[NOTE] No callback implemented for SlaveList double click")

    # API ......................................................................
    def slavesIn(self, S):
        """
        Process new slave vector S. See standards.py for form.
        """
        size = len(S)
        if size%s.SD_LEN != 0:
            raise ValueError("Slave vector size is not a multiple of {}".format(
                s.SD_LEN))

        for i in range(0, size, s.SD_LEN):
            # FIXME too redundant (getting two copies. What the hell, m8)
            index, name, mac, status, fans, version = S[i:i+s.SD_LEN]
            slave = (index, name, mac, status, fans, version)
            if index not in self.slaves:
                self.addSlave(slave)
            else:
                self.updateSlave(slave)

    def addSlave(self, slave):
        """
        Add SLAVE to the list. ValueError is raised if a slave with that index
        already exists. SLAVE is expected to be a tuple (or list) of the form
            (INDEX, NAME, MAC, STATUS, FANS, VERSION)
        Where INDEX is an integer that is expected to be unique among slaves,
        MAC and VERSION are strings, STATUS is one of the status codes
        defined as class attributes of this class, FANS is an integer.
        """
        if slave[s.SD_INDEX] in self.slaves:
            raise ValueError("Repeated Slave index {}".format(slave[s.SD_INDEX]))
        elif slave[s.SD_STATUS] not in s.SLAVE_STATUSES:
            raise ValueError("Invalid status tag \"{}\"".format(
                slave[s.SD_STATUS]))
        else:
            index = slave[s.SD_INDEX]
            iid = self.slaveList.insert('', 0,
                values = (index + 1, slave[s.SD_NAME], slave[s.SD_MAC],
                    s.SLAVE_STATUSES[slave[s.SD_STATUS]], slave[s.SD_FANS],
                    slave[s.SD_VERSION]),
                tag = slave[s.SD_STATUS])
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
        index = slave[s.SD_INDEX]
        iid = self.slaves[index][-1]

        self.slaveList.item(
            iid, values = (index + 1, slave[s.SD_NAME], slave[s.SD_MAC],
                s.SLAVE_STATUSES[slave[s.SD_STATUS]], slave[s.SD_FANS],
                slave[s.SD_VERSION]),
            tag = slave[s.SD_STATUS])

        self.slaves[index] = slave + (iid,)

        if self.autoVar.get() \
                and slave[s.SD_STATUS] != self.slaves[index][s.SD_STATUS]:
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
        self.slaves[index] = slave[:s.SD_STATUS] + (status,) \
            + slave[s.SD_STATUS + 1:]

        self.slaveList.item(slave[-1],
            values = (index + 1, slave[s.SD_MAC], s.SLAVE_STATUSES[status],
                slave[s.SD_FANS], slave[s.SD_VERSION]),
            tag = status)

        if self.autoVar.get():
            self.slaveList.move(self.slaves[index][-1], '', 0)

    def connected(self):
        """
        To be called when the network changes from disconnected to connected.
        """
        pass

    def disconnected(self):
        """
        To be called when the network changes from connected to disconnected.
        """
        self.clear()

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
        Return a tuple of the indices of slaves selected. STATUS (optional)
        returns a list of only the indices of slaves with such status code, if
        any exist.
        """
        selected = ()
        for iid in self.slaveList.selection():
            if status is None \
                or self.slaveList.item(iid)['values'][s.SD_STATUS] == status:
                selected += (self.slaveList.item(iid)['values'][s.SD_INDEX]-1, )
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

    def __testF1(self):
        """ Provisional testing method for development """
        self.slavesIn(TEST_VECTORS[self.testi%len(TEST_VECTORS)])
        self.testi += 1

# Network status bar ===========================================================
class StatusBarWidget(tk.Frame, pt.PrintClient):
    """
    GUI front-end for the FC "status bar."
    """
    SYMBOL = "[SB]"

    TOTAL = 100
    CONNECTED_STR = "Connected"
    DISCONNECTED_STR = "Disconnected"

    def __init__(self, master, shutdown, pqueue):
        """
        Horizontal bar that contains a breakdown of all slave statuses in
        the network, plus a connect/disconnect button.

        MASTER := Tkinter parent widget
        SHUTDOWN := Method to call when the shutdown button is pressed
        PQUEUE := Queue object to be used for I-P printing
        """
        tk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

        # Setup ................................................................

        # Status counters ......................................................
        self.statusFrame = tk.Frame(self, relief = tk.SUNKEN, borderwidth = 0)
        self.statusFrame.pack(side = tk.LEFT)

        self.statusFrames = {}
        self.statusVars, self.statusLabels, self.statusDisplays  = {}, {}, {}

        for code, name in ((self.TOTAL, "Total"),) \
            + tuple(s.SLAVE_STATUSES.items()):
            self.statusFrames[code] = tk.Frame(self.statusFrame,
                relief = tk.RIDGE, bd = 1)
            self.statusFrames[code].pack(side = tk.LEFT, padx = 5, pady = 1)

            self.statusVars[code] = tk.IntVar()
            self.statusVars[code].set(0)

            self.statusLabels[code] = tk.Label(self.statusFrames[code],
                text = name, font = "Courier 6 bold", padx = 6, pady = 1,
                width = 14,
                fg = s.FOREGROUNDS[code] if code in s.FOREGROUNDS else 'black')
            self.statusLabels[code].pack(side = tk.TOP)

            self.statusDisplays[code] = tk.Label(self.statusFrames[code],
                textvariable = self.statusVars[code], font = "Courier 6 bold",
                padx = 6, pady = 1, relief = tk.SUNKEN, bd = 1,
                fg = s.FOREGROUNDS[code] if code in s.FOREGROUNDS else 'black')
            self.statusDisplays[code].pack(side = tk.TOP, fill = tk.X, padx = 2)

        self.connectionVar = tk.StringVar()
        self.connectionVar.set("[NO CONNECTION]")

        self.connectionLabel = tk.Label(self.statusFrame,
            textvariable = self.connectionVar, width = 11,
            relief = tk.SUNKEN, font = "Courier 7 bold", padx = 6, pady = 5)
        self.connectionLabel.pack(side = tk.RIGHT, fill = tk.Y, pady = 3,
            padx = 6)
        self.status = s.SS_DISCONNECTED

        # Buttons ..............................................................
        self._shutdownCallback = shutdown

        self.buttonFrame = tk.Frame(self)
        self.buttonFrame.pack(side = tk.RIGHT, fill = tk.Y)

        self.shutdownButton = tk.Button(self.buttonFrame, text = "SHUTDOWN",
            command = self._onShutdown, padx = 10,
            font = "Calibri 9 bold",
            highlightbackground= 'black',
            activebackground = "#560e0e", activeforeground = "#ffd3d3",
            foreground ='#560e0e', pady = 0)
        self.shutdownButton.pack(side = tk.RIGHT, fill = tk.Y)

        # Slave data:
        self.slaves = {}

        # Initialize:
        self.disconnected()

    # API ......................................................................
    def networkIn(self, N):
        """
        Process a new network status vector.
        """
        connected = N[0]
        if not connected and self.status == s.SS_CONNECTED:
            self.disconnected()
        if connected and self.status == s.SS_DISCONNECTED:
            self.connected()

    def slavesIn(self, S):
        """
        Process a new slaves status vector.
        """
        size = len(S)
        for offset in range(0, size, s.SD_LEN):
            index = S[offset + s.SD_INDEX]
            status = S[offset + s.SD_STATUS]
            if index in self.slaves:
                if self.slaves[index] != status:
                    self.addCount(self.slaves[index], -1)
                    self.addCount(status, 1)
                    self.slaves[index] = status
            else:
                self.addTotal(1)
                self.addCount(status, 1)
                self.slaves[index] = status

    def connected(self):
        """
        Handle network switching to connected.
        """
        self.connectionVar.set(self.CONNECTED_STR)
        self.connectionLabel.config(fg = s.FOREGROUNDS[s.SS_CONNECTED],
            bg = s.BACKGROUNDS[s.SS_CONNECTED])
        self.status = s.SS_CONNECTED

    def disconnected(self):
        """
        Handle network switching to disconnected.
        """
        self.clear()
        self.connectionVar.set(self.DISCONNECTED_STR)
        self.connectionLabel.config(fg = s.FOREGROUNDS[s.SS_DISCONNECTED],
            bg = s.BACKGROUNDS[s.SS_DISCONNECTED])
        self.status = s.SS_DISCONNECTED

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
        self.statusVars[self.TOTAL].set(count \
            + self.statusVars[self.TOTAL].get())

    def getTotal(self):
        """
        Return the current total.
        """
        return self.statusVars[self.TOTAL].get()

    def clear(self):
        """
        Reset data
        """
        for count in self.statusVars.values():
            count.set(0)
            self.slaves = {}

    def profileChange(self):
        self.clear()

    # Internal methods .........................................................
    def _onShutdown(self, *event):
        self._shutdownCallback()

## DEMO ########################################################################
if __name__ == "__main__":
    print("FCMkIV Network GUI demo started")
    print("[No Network GUI demo implemented]")
    print("FCMkIV Network GUI demo finished")
