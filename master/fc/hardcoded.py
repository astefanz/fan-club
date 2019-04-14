################################################################################
## Project: Fanclub Mark IV "Master"  ## File: hardcoded.py                   ##
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
 + Provisional hardcoded profiles.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

PROFILES = {
    "DEV" : DEV
}

PINOUTS = {
    "BASE" : "FGHMALXWKJUVNISOBQTDC qsrnabdtfhvuepckmljoi",
    "CAST" : "ETRGMLWXPQJKUVBADC edcb_^ng`w\\]porqfs",
    "JPL"  : "FGCDABNOLMHITUQSJK efcdabnolmhirspqjk"
}
""" Provisional, hard-coded profiles. """
DEV = {
    name : "Development Profile",
    description : "A provisional profile to be used for development.",
    platform : UNKNOWN,

    broadcastPort  : 65000,
    broadcastPeriodMS : 1000,
    broadcastPeriodS : 1,
    periodMS : 100,
    maxLength : 512,
    maxTimeouts : 10,

    mainQueueSize : 10,
    slaveQueueSize: 10,
    broadcastQueueSize : 2,
    listenerQueueSize : 3,
    misoQueueSize : 2,
    printerQueueSize : 3,
    passcode : "CT",

    defaultSlave :
        {
            SV_name : "FAWT Module",
            SV_mac : "None",
            SV_index : -1,
            SV_fanModel : "Unknown",
            SV_fanMode : SINGLE,
            SV_targetRelation :(1.0, 0.0),
            SV_chaserTolerance : 0.02,
            SV_fanFrequencyHZ : 25000,
            SV_counterCounts : 2,
            SV_counterTimeoutMS : 30,
            SV_pulsesPerRotation : 2,
            SV_maxRPMs : 16000,
            SV_minRPMs : 1200,
            SV_minDCs : 0.5,
            SV_maxFans : 21,
            SV_pinout : "BASE",
            MD_row : -1,
            MD_column : -1,
            MD_rows : 0,
            MD_columns : 0,
            MD_mapping : ()
        },
savedSlaves : (
        {
            SV_name : "A1",
            SV_mac : "00:80:e1:38:00:2a",
            SV_index : 0,
            SV_fanModel : "Unknown",
            SV_fanMode : SINGLE,
            SV_targetRelation :(1.0, 0.0),
            SV_chaserTolerance : 0.02,
            SV_fanFrequencyHZ : 25000,
            SV_counterCounts : 2,
            SV_counterTimeoutMS : 30,
            SV_pulsesPerRotation : 2,
            SV_maxRPMs : 16000,
            SV_minRPMs : 1200,
            SV_minDCs : 0.5,
            SV_maxFans : 21,
            SV_pinout : "BASE",
            MD_row : 0,
            MD_column : 0,
            MD_rows : 21,
            MD_columns : 1,
            MD_mapping : \
                ("0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20")
        },
        {
            SV_name : "A1",
            SV_mac : "00:80:e1:45:00:46",
            SV_index : 0,
            SV_fanModel : "Unknown",
            SV_fanMode : SINGLE,
            SV_targetRelation :(1.0, 0.0),
            SV_chaserTolerance : 0.02,
            SV_fanFrequencyHZ : 25000,
            SV_counterCounts : 2,
            SV_counterTimeoutMS : 30,
            SV_pulsesPerRotation : 2,
            SV_maxRPMs : 16000,
            SV_minRPMs : 1200,
            SV_minDCs : 0.5,
            SV_maxFans : 21,
            SV_pinout : "BASE",
            MD_row : 0,
            MD_column : 1,
            MD_rows : 21,
            MD_columns : 1,
            MD_mapping : \
                ("0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20")
        }),
    pinouts : PINOUTS.copy(),
    fanArray : {
        FA_rows : 21,
        FA_columns : 2,
        FA_layers : 1,
    },
}

