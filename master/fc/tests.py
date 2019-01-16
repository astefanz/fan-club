################################################################################
## Project: Fanclub Mark IV "Master" unit tests ## File:                      ##
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
 + Unit tests.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import unittest as ut
import time as tm
import threading as mt

import fc.utils as us
import fc.process as process
import tkinter as tk

## TEST CASES ##################################################################
class FCProcessTest(ut.TestCase):

    class DummyProcess(process.FCProcess):
        """
        Provisional FCProcess for testing.
        """

        @staticmethod
        def dummyRoutine(data):
            """
            To be run by this FCProcess' child process.
            """
            profile = data['profile']
            symbol = data['symbol']
            pipes = data['pipes']

            us.dprint("[DP] DummyProcess routine started")
            gui = tk.Tk()


            def mainloop():
                done = False

                while not done:
                    for key in pipes:
                        if key is not process.COMMAND and pipes[key].poll():
                            pipe = pipes[key]
                            message = pipe.recv()
                            #print("[DP] '{}' received from pipe with code {}".\
                            #    format(message, key))
                            for channel in (process.MESSAGE, process.COMMAND):
                                pipes[channel].send(
                                    process.message(message[process.RECEIVER],
                                        message[process.SENDER],
                                        key))
                            if message[process.SUBJECT] == process.STOP:
                               # print("[DP] STOP received")
                                done = True

                us.dprint("[DP] Ending GUI")
                gui.quit()
                us.dprint("[DP] Auxiliary thread done")

            try:
                thread = mt.Thread(target = mainloop, daemon = True)
                thread.start()
                gui.mainloop()
                us.dprint("[DP] GUI done")
                thread.join(1)
                if thread.is_alive():
                    raise RuntimeError("DT Auxiliary thread stuck")
            except Exception as e:
                us.printexc(e)
                pipes[process.MESSAGE].send(
                    process.message(0, 0, process.ERROR, (str(e),)))

        def __init__(self):
            process.FCProcess.__init__(self,
                routine = FCProcessTest.DummyProcess.dummyRoutine,
                args = {'a' : '1a', 'b' : '1b' }, name = "Dummy Process")

        def usesMatrix(self):
            return True

        def usesNetwork(self):
            return True

        def usesSlaveList(self):
            return True

        def isRunnable(self):
            return True

    class StuckProcess(process.FCProcess):
        """
        FCProcess who's child process will not end on its own, to test forced
        termination.
        """
        @staticmethod
        def snorlax(data):
            """
            I don't feel like doing anything today.
            """
            us.dprint("[SS] Stuck process started")
            while True:
                tm.sleep(1)

        def __init__(self):
            process.FCProcess.__init__(self,
                routine = FCProcessTest.StuckProcess.snorlax,
                args = {'a' : '1a', 'b' : '1b' },
                name = "Test Process (ignore this)")

        def isRunnable(self):
            return True

    def test(self):
        dummy = self.DummyProcess()
        print("[TS] FCProcess test suite started")
        fcpstart = tm.time()

        self.assertFalse(dummy.isActive())
        dummy.start(profile = {})
        self.assertTrue(dummy.isActive())

        sender = -1
        receiver = -2

        channels = {
            process.MESSAGE : dummy.messageIn,
            process.MATRIX  : dummy.matrixIn,
            process.NETWORK : dummy.networkIn,
            process.SLAVES  : dummy.slaveListIn
        }

        timeout = 1 # Seconds
        for key in channels:

            us.dprint("[TS] Sending message over key ", key)
            channels[key](process.message(
                sender, receiver, key))
            start = tm.time()
            self.assertTrue(dummy.hasMessage(timeout),
                "hasMessage timed out after {} seconds".format(timeout))
            self.assertTrue(dummy.hasCommand(timeout),
                "hasCommand timed out after {} seconds".format(timeout))
            stop = tm.time()

            message = dummy.getMessage()
            command = dummy.getCommand()

            us.dprint("[TS] Messages circled back over key {} in {:.3f}s".\
                format(key, stop - start))

            if message[process.SUBJECT] is process.ERROR:
                ut.fail("[TS] Error in DummyProcess: \"{}\"".\
                    format(message[process.ARGUMENTS]))

            self.assertEqual(message, command)
            self.assertEqual(message, process.message(receiver, sender, key))

        dummy.messageIn(process.message(sender, receiver, process.STOP))
        self.assertFalse(dummy.isActive())

        us.dprint("[TS] Testing FCProcess' forced termination")
        stuck = self.StuckProcess()
        stuck.start(profile = {})
        stuck.stop()
        tm.sleep(.5)
        self.assertFalse(stuck.isActive(),
            "Unable to forcibly stop stuck process")

        print("[TS] FCProcess test suite complete ({:.3f}s)".format(
            tm.time() - fcpstart))
