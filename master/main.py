#!/usr/bin/python3 #############################################################
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
 + FC execution starts here. Launches Core.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

if __name__ == '__main__':
    #if us.platform() == us.WINDOWS:
    # Windows-specific requirement around processes. See:
    # https://stackoverflow.com/questions/18204782

    ## IMPORTS #################################################################
    import multiprocessing as mp
    import fc.frontend.gui.tkgui as tkg
    import fc.archive as ac
    import fc.backend.communicator as cm
    import fc.utils as us
    import fc.printer as pt
    import fc.builtin.profiles as btp

    ## GLOBALS #################################################################
    VERSION = "0.14"
    INIT_PROFILE = "CAST" # FIXME

    # NOTE on writing servers like the ext. ctl. API:
    # - have stop methods handle redundance
    # - call stop method from end of routine
    # - have start methods restart if applicable
    # - have listener threads block at socket and deactivate them by sending
    #   to that socket

    ## MAIN ####################################################################
    # Prints ...................................................................
    print(pt.HEADER)

    # FIXME: reminders
    print("[REM] Look into 'memory leak' in profile switches and data path")
    print("[REM] Look into control after profile switching ('return 1')")
    print("[REM] Pass profiles, not archive, " \
          +  "when profile changes will cause reset")
    print("[REM] Change all watchdog threads to Tkinter 'after' scheduling")
    print("[REM] Indexing by 1 in functional input")
    print("[REM] Standardize notation (also: function argument consistency)")
    print("[REM] period_ms abstraction barrier in FCInterface")
    print("[REM] LiveTable and manual control")
    print("[REM] Enforce consistent slave indices")
    print("[REM] External control on profile changes")
    print("[REM] Comms. reset on profile changes")
    print("[REM] Direct control w/ live table")
    print("[REM] Auto-update displays to latest data when switching")
    print("[REM] Change core and print server to use blocked threads")
    print("[REM] Terminal arguments")
    print("[REM] Daemon threads")
    print("[REM] Grid position indicators")
    print("[REM] Switching from preview")
    print("[REM] FC Function constants")

    # Execution ................................................................
    pqueue = mp.Queue()
    archive = ac.FCArchive(pqueue, VERSION, btp.PROFILES[INIT_PROFILE])
    interface = tkg.FCGUI(archive, pqueue)
    interface.run()
