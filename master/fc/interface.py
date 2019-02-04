################################################################################
## Project: Fanclub Mark IV "Master"  ## File: interface.py                   ##
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
 + Base class for all FC Interfaces.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import threading as mt

import fc.process as pr
import fc.utils as us

################################################################################
class FCInterface(pr.FCProcess):
    """
    Base class for all FC front-ends. Behaves like an FCProcess in terms of
    inter-process communication through the FC Core. It is meant to be
    subclassed by different types of FC front ends, each of which handles the
    interface-specific details.

    It also runs a "sentinel" thread in charge of monitoring inter-process
    messages to and from the interface. The sentinel "target" (function) must be
    passed to the constructor, and it will receive the standard child-end set
    of pipes as its first argument. (It is started when mainloop() is called.)
    The sentinel may also "listen" to the "stop lock" to check whether it should
    stop execution.

    NOTE: An FCInterface is meant to be executed once throughout its lifetime.
    """
    def __init__(self, pqueue, routine, sid, name = "FC Interface",
        symbol = "[IT]", data = {}):
        pr.FCProcess.__init__(self, pqueue = pqueue, name = name,
            symbol = symbol)

        self.sid = sid
        self.routine = routine
        self.data = data

    def mainloop(self):
        """
        Run the main loop of the interface. Expected to block during the entire
        execution of the interface. (Returning means the interface has been
        closed.)

        Note: override the parent class' _mainloop method to specify its
        behavior. Otherwise, it will simply start and stop the sentinel and
        return immediately.
        """
        lock = mt.Lock()
        pipes = self._pipes()

        self.data.update({'pipes': pipes[pr.CHILD]})
        self.data.update({'pqueue': self.pqueue})
        self.data.update({'lock': lock})

        sentinel = mt.Thread(name = "FCI Sentinel", target = self.routine,
            args = (self.data,), daemon = True)
        lock.acquire()

        sentinel.start()
        self._mainloop()

        if not lock.acquire(False):
            lock.release()

    def _mainloop(self):
        """
        Override to specify the behavior of the interface's main loop.
        """
        return

    def isRunnable(self):
        return False

    def usesMatrix(self):
        return True

    def usesNetwork(self):
        return True

    def usesSlaveList(self):
        return True
