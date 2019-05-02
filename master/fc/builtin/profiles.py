################################################################################
## Project: Fanclub Mark IV "Master" profile GUI  ## File: profile.py         ##
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
 + Repository of built-in profiles.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """
from .. import archive as ac

DEV1 = {
    ac.name : "Development Profile",
    ac.description : "A provisional profile to be used for development.",
    ac.platform : ac.UNKNOWN,

    ac.broadcastIP : "10.42.0.255",
    ac.broadcastPort  : 65000,
    ac.broadcastPeriodMS : 1000,
    ac.periodMS : 100,
    ac.maxLength : 512,
    ac.maxTimeouts : 10,

    ac.mainQueueSize : 10,
    ac.slaveQueueSize: 10,
    ac.broadcastQueueSize : 2,
    ac.listenerQueueSize : 3,
    ac.misoQueueSize : 2,
    ac.printerQueueSize : 3,
    ac.passcode : "CT",
    ac.socketLimit : 1024,

    ac.defaultSlave :
        {
            ac.SV_name : "FAWT Module",
            ac.SV_mac : "None",
            ac.SV_index : -1,
            ac.SV_fanModel : "Unknown",
            ac.SV_fanMode : ac.SINGLE,
            ac.SV_targetRelation :(1.0, 0.0),
            ac.SV_chaserTolerance : 0.02,
            ac.SV_fanFrequencyHZ : 25000,
            ac.SV_counterCounts : 2,
            ac.SV_counterTimeoutMS : 30,
            ac.SV_pulsesPerRotation : 2,
            ac.SV_maxRPM : 16000,
            ac.SV_minRPM : 1200,
            ac.SV_minDC : 0.5,
            ac.SV_maxFans : 21,
            ac.SV_pinout : "BASE",
            ac.MD_assigned : False,
            ac.MD_row : -1,
            ac.MD_column : -1,
            ac.MD_rows : 0,
            ac.MD_columns : 0,
            ac.MD_mapping : ()
        },
    ac.savedSlaves : (
        {
            ac.SV_name : "A1",
            ac.SV_mac : "00:80:e1:38:00:2a",
            ac.SV_index : -1,
            ac.SV_fanModel : "Unknown",
            ac.SV_fanMode : ac.SINGLE,
            ac.SV_targetRelation :(1.0, 0.0),
            ac.SV_chaserTolerance : 0.02,
            ac.SV_fanFrequencyHZ : 25000,
            ac.SV_counterCounts : 2,
            ac.SV_counterTimeoutMS : 30,
            ac.SV_pulsesPerRotation : 2,
            ac.SV_maxRPM : 16000,
            ac.SV_minRPM : 1200,
            ac.SV_minDC : 0.1,
            ac.SV_maxFans : 21,
            ac.SV_pinout : "BASE",
            ac.MD_assigned : True,
            ac.MD_row : 0,
            ac.MD_column : 0,
            ac.MD_rows : 1,
            ac.MD_columns : 21,
            ac.MD_mapping : \
                ("0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20")
        },
        {
            ac.SV_name : "A2",
            ac.SV_mac : "00:80:e1:45:00:46",
            ac.SV_index : -1,
            ac.SV_fanModel : "Unknown",
            ac.SV_fanMode : ac.SINGLE,
            ac.SV_targetRelation :(1.0, 0.0),
            ac.SV_chaserTolerance : 0.02,
            ac.SV_fanFrequencyHZ : 25000,
            ac.SV_counterCounts : 2,
            ac.SV_counterTimeoutMS : 30,
            ac.SV_pulsesPerRotation : 2,
            ac.SV_maxRPM : 16000,
            ac.SV_minRPM : 1200,
            ac.SV_minDC : 0.1,
            ac.SV_maxFans : 21,
            ac.SV_pinout : "BASE",
            ac.MD_assigned : True,
            ac.MD_row : 1,
            ac.MD_column : 0,
            ac.MD_rows : 1,
            ac.MD_columns : 21,
            ac.MD_mapping : \
                ("0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20")
        }),
    ac.pinouts : ac.PINOUTS.copy(),
    ac.maxRPM : 16000,
    ac.maxFans : 21,
    ac.dcDecimals : 2,
    ac.fanArray : {
        ac.FA_rows : 2,
        ac.FA_columns : 21,
        ac.FA_layers : 1,
    },
}

DEV2 = {
    ac.name : "Development Profile 2" ,
    ac.description : "A provisional profile to be used for development. " \
        "Uses double fans.",
    ac.platform : ac.UNKNOWN,

    ac.broadcastIP : "10.42.0.255",
    ac.broadcastPort  : 65000,
    ac.broadcastPeriodMS : 1000,
    ac.periodMS : 100,
    ac.maxLength : 512,
    ac.maxTimeouts : 10,

    ac.mainQueueSize : 10,
    ac.slaveQueueSize: 10,
    ac.broadcastQueueSize : 2,
    ac.listenerQueueSize : 3,
    ac.misoQueueSize : 2,
    ac.printerQueueSize : 3,
    ac.passcode : "CT",
    ac.socketLimit : 1024,

    ac.defaultSlave :
        {
            ac.SV_name : "FAWT Module",
            ac.SV_mac : "None",
            ac.SV_index : -1,
            ac.SV_fanModel : "Unknown",
            ac.SV_fanMode : ac.DOUBLE,
            ac.SV_targetRelation :(1.0, 0.0),
            ac.SV_chaserTolerance : 0.02,
            ac.SV_fanFrequencyHZ : 25000,
            ac.SV_counterCounts : 2,
            ac.SV_counterTimeoutMS : 30,
            ac.SV_pulsesPerRotation : 2,
            ac.SV_maxRPM : 16000,
            ac.SV_minRPM : 1200,
            ac.SV_minDC : 0.5,
            ac.SV_maxFans : 20,
            ac.SV_pinout : "BASE",
            ac.MD_assigned : False,
            ac.MD_row : -1,
            ac.MD_column : -1,
            ac.MD_rows : 0,
            ac.MD_columns : 0,
            ac.MD_mapping : ()
        },
    ac.savedSlaves : (
        {
            ac.SV_name : "A1",
            ac.SV_mac : "00:80:e1:38:00:2a",
            ac.SV_index : -1,
            ac.SV_fanModel : "Unknown",
            ac.SV_fanMode : ac.DOUBLE,
            ac.SV_targetRelation :(1.0, 0.0),
            ac.SV_chaserTolerance : 0.02,
            ac.SV_fanFrequencyHZ : 25000,
            ac.SV_counterCounts : 2,
            ac.SV_counterTimeoutMS : 30,
            ac.SV_pulsesPerRotation : 2,
            ac.SV_maxRPM : 16000,
            ac.SV_minRPM : 1200,
            ac.SV_minDC : 0.1,
            ac.SV_maxFans : 20,
            ac.SV_pinout : "BASE",
            ac.MD_assigned : True,
            ac.MD_row : 0,
            ac.MD_column : 0,
            ac.MD_rows : 1,
            ac.MD_columns : 10,
            ac.MD_mapping : \
                ("0-1,2-3,4-5,6-7,8-9,10-11,12-13,14-15,16-17,18-19")
        },
        {
            ac.SV_name : "A2",
            ac.SV_mac : "00:80:e1:45:00:46",
            ac.SV_index : -1,
            ac.SV_fanModel : "Unknown",
            ac.SV_fanMode : ac.DOUBLE,
            ac.SV_targetRelation :(1.0, 0.0),
            ac.SV_chaserTolerance : 0.02,
            ac.SV_fanFrequencyHZ : 25000,
            ac.SV_counterCounts : 2,
            ac.SV_counterTimeoutMS : 30,
            ac.SV_pulsesPerRotation : 2,
            ac.SV_maxRPM : 16000,
            ac.SV_minRPM : 1200,
            ac.SV_minDC : 0.1,
            ac.SV_maxFans : 20,
            ac.SV_pinout : "BASE",
            ac.MD_assigned : True,
            ac.MD_row : 1,
            ac.MD_column : 0,
            ac.MD_rows : 1,
            ac.MD_columns : 10,
            ac.MD_mapping : \
                ("0-1,2-3,4-5,6-7,8-9,10-11,12-13,14-15,16-17,18-19")
        }),
    ac.pinouts : ac.PINOUTS.copy(),
    ac.maxRPM : 16000,
    ac.maxFans : 20,
    ac.dcDecimals : 2,
    ac.fanArray : {
        ac.FA_rows : 2,
        ac.FA_columns : 10,
        ac.FA_layers : 2,
    },
}

DEV3 = {
    ac.name : "Development Profile 3",
    ac.description : "A provisional profile to be used for development.",
    ac.platform : ac.UNKNOWN,

    ac.broadcastIP : "10.42.0.255",
    ac.broadcastPort  : 65000,
    ac.broadcastPeriodMS : 1000,
    ac.periodMS : 100,
    ac.maxLength : 512,
    ac.maxTimeouts : 10,

    ac.mainQueueSize : 10,
    ac.slaveQueueSize: 10,
    ac.broadcastQueueSize : 2,
    ac.listenerQueueSize : 3,
    ac.misoQueueSize : 2,
    ac.printerQueueSize : 3,
    ac.passcode : "CT",
    ac.socketLimit : 1024,

    ac.defaultSlave :
        {
            ac.SV_name : "FAWT Module",
            ac.SV_mac : "None",
            ac.SV_index : -1,
            ac.SV_fanModel : "Unknown",
            ac.SV_fanMode : ac.SINGLE,
            ac.SV_targetRelation :(1.0, 0.0),
            ac.SV_chaserTolerance : 0.02,
            ac.SV_fanFrequencyHZ : 25000,
            ac.SV_counterCounts : 2,
            ac.SV_counterTimeoutMS : 30,
            ac.SV_pulsesPerRotation : 2,
            ac.SV_maxRPM : 16000,
            ac.SV_minRPM : 1200,
            ac.SV_minDC : 0.5,
            ac.SV_maxFans : 21,
            ac.SV_pinout : "BASE",
            ac.MD_assigned : False,
            ac.MD_row : -1,
            ac.MD_column : -1,
            ac.MD_rows : 0,
            ac.MD_columns : 0,
            ac.MD_mapping : ()
        },
    ac.savedSlaves : (
        {
            ac.SV_name : "A1",
            ac.SV_mac : "00:80:e1:38:00:2a",
            ac.SV_index : -1,
            ac.SV_fanModel : "Unknown",
            ac.SV_fanMode : ac.SINGLE,
            ac.SV_targetRelation :(1.0, 0.0),
            ac.SV_chaserTolerance : 0.02,
            ac.SV_fanFrequencyHZ : 25000,
            ac.SV_counterCounts : 2,
            ac.SV_counterTimeoutMS : 30,
            ac.SV_pulsesPerRotation : 2,
            ac.SV_maxRPM : 16000,
            ac.SV_minRPM : 1200,
            ac.SV_minDC : 0.1,
            ac.SV_maxFans : 21,
            ac.SV_pinout : "BASE",
            ac.MD_assigned : True,
            ac.MD_row : 0,
            ac.MD_column : 0,
            ac.MD_rows : 5,
            ac.MD_columns : 4,
            ac.MD_mapping : \
                ("0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20")
        },
        {
            ac.SV_name : "A2",
            ac.SV_mac : "00:80:e1:45:00:46",
            ac.SV_index : -1,
            ac.SV_fanModel : "Unknown",
            ac.SV_fanMode : ac.SINGLE,
            ac.SV_targetRelation :(1.0, 0.0),
            ac.SV_chaserTolerance : 0.02,
            ac.SV_fanFrequencyHZ : 25000,
            ac.SV_counterCounts : 2,
            ac.SV_counterTimeoutMS : 30,
            ac.SV_pulsesPerRotation : 2,
            ac.SV_maxRPM : 16000,
            ac.SV_minRPM : 1200,
            ac.SV_minDC : 0.1,
            ac.SV_maxFans : 21,
            ac.SV_pinout : "BASE",
            ac.MD_assigned : True,
            ac.MD_row : 0,
            ac.MD_column : 4,
            ac.MD_rows : 5,
            ac.MD_columns : 4,
            ac.MD_mapping : \
                ("0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20")
        }),
    ac.pinouts : ac.PINOUTS.copy(),
    ac.maxRPM : 16000,
    ac.maxFans : 21,
    ac.dcDecimals : 2,
    ac.fanArray : {
        ac.FA_rows : 5,
        ac.FA_columns : 8,
        ac.FA_layers : 1,
    },
}
BASE = {
    ac.name : "Prov. Basement Tunnel",
    ac.description : "Not the wind tunnel GALCIT wants, but the one it needs.",
    ac.platform : ac.UNKNOWN,

    ac.broadcastIP : "10.42.0.255",
    ac.broadcastPort  : 65000,
    ac.broadcastPeriodMS : 1000,
    ac.periodMS : 100,
    ac.maxLength : 512,
    ac.maxTimeouts : 10,

    ac.mainQueueSize : 10,
    ac.slaveQueueSize: 10,
    ac.broadcastQueueSize : 2,
    ac.listenerQueueSize : 3,
    ac.misoQueueSize : 2,
    ac.printerQueueSize : 3,
    ac.passcode : "CT",
    ac.socketLimit : 1024,

    ac.defaultSlave :
        {
            ac.SV_name : "FAWT Module",
            ac.SV_mac : "None",
            ac.SV_index : -1,
            ac.SV_fanModel : "Unknown",
            ac.SV_fanMode : ac.SINGLE,
            ac.SV_targetRelation :(1.0, 0.0),
            ac.SV_chaserTolerance : 0.02,
            ac.SV_fanFrequencyHZ : 25000,
            ac.SV_counterCounts : 2,
            ac.SV_counterTimeoutMS : 30,
            ac.SV_pulsesPerRotation : 2,
            ac.SV_maxRPM : 16000,
            ac.SV_minRPM : 1200,
            ac.SV_minDC : 0.1,
            ac.SV_maxFans : 21,
            ac.SV_pinout : "BASE",
            ac.MD_assigned : False,
            ac.MD_row : -1,
            ac.MD_column : -1,
            ac.MD_rows : 0,
            ac.MD_columns : 0,
            ac.MD_mapping : ()
        },
    ac.savedSlaves : (
        {
            ac.SV_name : "B1",
            ac.SV_mac : "00:80:e1:4b:00:36",
            ac.SV_index : -1,
            ac.SV_fanModel : "Unknown",
            ac.SV_fanMode : ac.SINGLE,
            ac.SV_targetRelation :(1.0, 0.0),
            ac.SV_chaserTolerance : 0.02,
            ac.SV_fanFrequencyHZ : 25000,
            ac.SV_counterCounts : 2,
            ac.SV_counterTimeoutMS : 30,
            ac.SV_pulsesPerRotation : 2,
            ac.SV_maxRPM : 16000,
            ac.SV_minRPM : 1200,
            ac.SV_minDC : 0.1,
            ac.SV_maxFans : 20,
            ac.SV_pinout : "BASE",
            ac.MD_assigned : True,
            ac.MD_row : 7,
            ac.MD_column : 5,
            ac.MD_rows : 4,
            ac.MD_columns : 6,
            ac.MD_mapping : \
                '19,17,13,9,,,18,16,12,8,5,2,,15,11,7,4,1,,14,10,6,3,0'
        },
        {
            ac.SV_name : "B2",
            ac.SV_mac : "00:80:e1:2f:00:1d",
            ac.SV_index : -1,
            ac.SV_fanModel : "Unknown",
            ac.SV_fanMode : ac.SINGLE,
            ac.SV_targetRelation :(1.0, 0.0),
            ac.SV_chaserTolerance : 0.02,
            ac.SV_fanFrequencyHZ : 25000,
            ac.SV_counterCounts : 2,
            ac.SV_counterTimeoutMS : 30,
            ac.SV_pulsesPerRotation : 2,
            ac.SV_maxRPM : 16000,
            ac.SV_minRPM : 1200,
            ac.SV_minDC : 0.1,
            ac.SV_maxFans : 20,
            ac.SV_pinout : "BASE",
            ac.MD_assigned : True,
            ac.MD_row : 7,
            ac.MD_column : 0,
            ac.MD_rows : 4,
            ac.MD_columns : 6,
            ac.MD_mapping : \
                ',,13,9,5,,19,16,12,8,4,,18,15,11,7,3,1,17,14,10,6,2,0'
        },
        {
            ac.SV_name : "B3",
            ac.SV_mac : "00:80:e1:29:00:2e",
            ac.SV_index : -1,
            ac.SV_fanModel : "Unknown",
            ac.SV_fanMode : ac.SINGLE,
            ac.SV_targetRelation :(1.0, 0.0),
            ac.SV_chaserTolerance : 0.02,
            ac.SV_fanFrequencyHZ : 25000,
            ac.SV_counterCounts : 2,
            ac.SV_counterTimeoutMS : 30,
            ac.SV_pulsesPerRotation : 2,
            ac.SV_maxRPM : 16000,
            ac.SV_minRPM : 1200,
            ac.SV_minDC : 0.1,
            ac.SV_maxFans : 20,
            ac.SV_pinout : "BASE",
            ac.MD_assigned : True,
            ac.MD_row : 3,
            ac.MD_column : 0,
            ac.MD_rows : 5,
            ac.MD_columns : 6,
            ac.MD_mapping : \
                '18,19,,,,,13,14,15,16,17,,7,8,9,10,11,12,2,3,4,5,6,,0,1,,,,'
        },
        {
            ac.SV_name : "B4",
            ac.SV_mac : "00:80:e1:27:00:3e",
            ac.SV_index : -1,
            ac.SV_fanModel : "Unknown",
            ac.SV_fanMode : ac.SINGLE,
            ac.SV_targetRelation :(1.0, 0.0),
            ac.SV_chaserTolerance : 0.02,
            ac.SV_fanFrequencyHZ : 25000,
            ac.SV_counterCounts : 2,
            ac.SV_counterTimeoutMS : 30,
            ac.SV_pulsesPerRotation : 2,
            ac.SV_maxRPM : 16000,
            ac.SV_minRPM : 1200,
            ac.SV_minDC : 0.1,
            ac.SV_maxFans : 20,
            ac.SV_pinout : "BASE",
            ac.MD_assigned : True,
            ac.MD_row : 0,
            ac.MD_column : 0,
            ac.MD_rows : 4,
            ac.MD_columns : 6,
            ac.MD_mapping : \
                '0,1,2,3,4,,5,6,7,8,9,,10,11,12,13,14,15,,,16,17,18,19'
        },
        {
            ac.SV_name : "B5",
            ac.SV_mac : "00:80:e1:4b:00:42",
            ac.SV_index : -1,
            ac.SV_fanModel : "Unknown",
            ac.SV_fanMode : ac.SINGLE,
            ac.SV_targetRelation :(1.0, 0.0),
            ac.SV_chaserTolerance : 0.02,
            ac.SV_fanFrequencyHZ : 25000,
            ac.SV_counterCounts : 2,
            ac.SV_counterTimeoutMS : 30,
            ac.SV_pulsesPerRotation : 2,
            ac.SV_maxRPM : 16000,
            ac.SV_minRPM : 1200,
            ac.SV_minDC : 0.1,
            ac.SV_maxFans : 20,
            ac.SV_pinout : "BASE",
            ac.MD_assigned : True,
            ac.MD_row : 0,
            ac.MD_column : 5,
            ac.MD_rows : 4,
            ac.MD_columns : 6,
            ac.MD_mapping : \
                '19,17,13,9,5,2,18,16,12,8,4,1,,15,11,7,3,0,,14,10,6,,,'
        },
        {
            ac.SV_name : "B6",
            ac.SV_mac : "00:80:e1:47:00:3d",
            ac.SV_index : -1,
            ac.SV_fanModel : "Unknown",
            ac.SV_fanMode : ac.SINGLE,
            ac.SV_targetRelation :(1.0, 0.0),
            ac.SV_chaserTolerance : 0.02,
            ac.SV_fanFrequencyHZ : 25000,
            ac.SV_counterCounts : 2,
            ac.SV_counterTimeoutMS : 30,
            ac.SV_pulsesPerRotation : 2,
            ac.SV_maxRPM : 16000,
            ac.SV_minRPM : 1200,
            ac.SV_minDC : 0.1,
            ac.SV_maxFans : 21,
            ac.SV_pinout : "BASE",
            ac.MD_assigned : True,
            ac.MD_row : 3,
            ac.MD_column : 5,
            ac.MD_rows : 5,
            ac.MD_columns : 6,
            ac.MD_mapping : \
                ',,,,9,4,20,18,15,12,8,3,,17,14,11,7,2,19,16,13,10,6,1,,,,,5,0'

        }
    ),
    ac.pinouts : ac.PINOUTS.copy(),
    ac.maxRPM : 16000,
    ac.maxFans : 21,
    ac.dcDecimals : 2,
    ac.fanArray : {
        ac.FA_rows : 11,
        ac.FA_columns : 11,
        ac.FA_layers : 1,
    },
}


PROFILES = {
    "DEV1" : DEV1,
    "DEV2" : DEV2,
    "DEV3" : DEV3,
    "BASE": BASE
}
