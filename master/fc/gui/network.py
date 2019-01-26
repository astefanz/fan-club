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
import tkinter as tk
import tkinter.ttk as ttk

## WIDGETS #####################################################################

# Network control ==============================================================
class NetworkControlWidget(tk.Frame):
    """
    GUI front-end for the FC network control tools (such as adding and removing
    Slaves).
    """

    def __init__(self, master):
        tk.Frame.__init__(self, master)

        frameconfig = {"side" : tk.TOP, "fill" : tk.BOTH, "expand" : True,
            "padx" : 10, "pady" : 5}

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
        self.callback = lambda t, m: None

    def setCallback(self, callback):
        """
        Set the method to be called when the "Send" button is pressed. CALLBACK
        must receie two integer codes, the first of which refers to the selected
        target and the second to the selected message. (See addTarget and
        addMessage)
        """
        self.callback = callback

    def addTarget(self, name, code):
        """
        Allow the user to specify the target named NAME with the code CODE
        passed to the send callback.
        """
        button = tk.Radiobutton(self.targetFrame, text = name, value = code,
            variable = self.target, indicatoron = False, padx = 10, pady = 5)

        button.pack(side = tk.LEFT, anchor = tk.W)
        self.targetButtons.append(button)

        if len(self.targetButtons) is 1:
            self.target.set(code)

    def addMessage(self, name, code):
        """
        Allow the user to send the message named NAME with the message code CODE
        passed to the send callback.
        """
        button = tk.Radiobutton(self.messageFrame, text = name, value = code,
            variable = self.message, indicatoron = False, padx = 10, pady = 5)

        button.pack(side = tk.LEFT, anchor = tk.W)
        self.messageButtons.append(button)

        if len(self.messageButtons) is 1:
            self.message.set(code)

    def _send(self, *E):
        """
        Call the given callback and pass it the currently selected target and
        message codes. Nonexistent codes are set to 0.
        """
        self.callback(self.target.get(), self.message.get())

# Firmware update ==============================================================
class FirmwareUpdateWidget(tk.Frame):
    """
    GUI front-end for the FC firmware update tools, i.e the Mark III
    "Bootloader."
    """
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        # TODO finish init
        l = tk.Label(self, text = "Firmware Update", bg = "gray", fg = "green")
        l.pack(fill = tk.BOTH, expand = True)

    # TODO methods

# Slave list ===================================================================
class SlaveListWidget(tk.Frame):
    """
    GUI front-end for the FC Slave List display.
    """
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        # TODO finish init
        l = tk.Label(self, text = "Slave List", bg = "blue", fg = "red")
        l.pack(fill = tk.BOTH, expand = True)

    # TODO methods

# Network status bar ===========================================================
class StatusBarWidget(tk.Frame):
    """
    GUI front-end for the FC "status bar."
    """
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        # TODO finish init

    # TODO methods

## BASE ########################################################################
class NetworkWidget(tk.Frame):
    """
    Container for all the FC network GUI front-end widgets, except the FC
    status bar.
    """
    def __init__(self, master):
        # Core setup -----------------------------------------------------------
        tk.Frame.__init__(self, master)
        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure(1, weight = 1)

        # ----------------------------------------------------------------------
        self.notebook = ttk.Notebook(self)

        self.networkControl = NetworkControlWidget(self.notebook)
        self.firmwareUpdate = FirmwareUpdateWidget(self.notebook)
        self.slaveList = SlaveListWidget(self)

        self.notebook.add(self.networkControl, text = "Network Control")
        self.notebook.add(self.firmwareUpdate, text = "Firmware Update")

        self.notebook.grid(row = 0, sticky = "EW")
        self.slaveList.grid(row = 1, sticky = "NEWS")

    def getNetworkControlWidget(self):
        return self.networkControl

    def getFirmwareUpdateWidget(self):
        return self.firmwareUpdate

## DEMO ########################################################################
if __name__ == "__main__":
    print("FCMkIV Network GUI demo started")

    # Base
    mw = tk.Tk()
    NW = NetworkWidget(mw)
    N = NW.getNetworkControlWidget()

    for i in range(1, 4):
        N.addTarget("Target {}".format(i), i)
        N.addMessage("Message {}".format(i), i)

    def callback(t, m):
        print("Sending message [{}] to target [{}]".format(m, t))

    N.setCallback(callback)

    NW.pack(fill = tk.BOTH, expand = True)
    mw.mainloop()

    # Status bar

    print("FCMkIV Network GUI demo finished")
