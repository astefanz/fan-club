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
Safety checking and array health monitoring behavior.

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## DEPENDENCIES ################################################################
from fc import archive as ac, standards as std, printer as pt


## MAIN ########################################################################
class FCWatchdog(pt.PrintClient):
    """
    This backend class scans all incoming and outgoing vectors to check for
    user-chosen conditions.
    """
    SYMBOL = "[WD]"

    I_NAME, I_ARGS, I_METHOD = range(3)

    def __init__(self, mapper, pqueue):
        """
        - archive := FCArchive with current profile.
        - pqueue := Queue for PrintClient.
        """
        pt.PrintClient.__init__(self, pqueue)
        self.mapper = mapper
        # TODO
        # - last C
        # - checkers
        # - processors
        # - custom callbacks

        # Control processors:
        self.controlProcessor = self._identityProcessor()
        self.control_processors = (
            ("None (Identity)", (,), self._identityProcessor),
            ("Scale DC", ("s ([0, 1])",), self._scaleProcessor),
            ("Saturate DC", ("low", "high"), self._saturateProcessor))


    # API ----------------------------------------------------------------------
    # TODO
    def processControl(self, C):
        """
        Check the outgoing control vector C. Returns the new control vector to
        be used, which may be the last "accepted" control vector if there is
        one stored and the current vector meets the requirements to be
        discarded.
        """
        return self.controlProcessor(C)

    def checkFeedback(self, F):
        """
        Check the incoming feedback vector F. Returns None.
        """
        # TODO
        pass

    def checkNetwork(self, N):
        """
        Check the incoming network state vector N. Returns None.
        """
        # TODO
        pass

    def checkSlaves(self, S):
        """
        Check the incoming slave state vector S. Returns None.
        """
        # TODO
        pass

    def profileChanged(self):
        """
        Account for a change in the loaded profile.
        """
        pass

    # TODO get possible processors and checkers
    # TODO activate and deactivate checkers
    # TODO activate and deactivate processors
    # TODO set callbacks for errors

    # Auxiliary ----------------------------------------------------------------
    # TODO

    # TODO S check for disconnected slaves
    # TODO N check for network errors
    # TODO C check for fans around a value (relative and absolute)
    # TODO C check for fans outside of a value (relative and absolute)

    # "Processor" methods for control vectors:
    def _identityProcessor(self, *_):
        """
        Return a processor that returns the vector given without modifying it.
        """
        self.prints(f"Setting identity processor.")
        return lambda C: C

    def _scaleProcessor(self, s = 1.0):
        """
        Return a processor that multiplies all the entries in the given vector
        by the given scalar, which is expected to be in (0, 1].

        Raises a ValueError if the scalar is outside the valid range.
        """
        if s <= 0 or s > 1:
            raise ValueError(f"Given scalar {s} is outside (0, 1]")

        self.prints(f"Setting scale processor with s = {s}")

        return lambda C: [s*c for c in C]

    def _saturateProcessor(self, low = 0.0, high = 1.0):
        """
        Return a processor method that saturates all values at the given upper
        and lower bounds, which must be in [0, 1] and low < high. Raises a
        ValueError if the given bounds are invalid.
        """
        if low < 0 or low > 1 or high < 0 or high > 1:
            raise ValueError(
                f"Bounds [{low}, {high}] out of range ([0, 1] each)")
        elif low >= high:
            raise ValueError(f"Low bound {low} >= High bound {high}")

        self.prints(f"Setting saturation processor in [{low}, {high}]")

        return lambda C: [min(high, max(low, c)) for c in C]
