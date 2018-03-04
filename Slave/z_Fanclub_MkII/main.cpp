////////////////////////////////////////////////////////////////////////////////
// Project: Fanclub Mark II "Slave" // File: main.cpp - Main file             //
//----------------------------------------------------------------------------//
// CALIFORNIA INSTITUTE OF TECHNOLOGY // GRADUATE AEROSPACE LABORATORY //     //
// CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES                             //
//----------------------------------------------------------------------------//
//      ____      __      __  __      _____      __      __    __    ____     //
//     / __/|   _/ /|    / / / /|  _- __ __\    / /|    / /|  / /|  / _  \    //
//    / /_ |/  / /  /|  /  // /|/ / /|__| _|   / /|    / /|  / /|/ /   --||   //
//   / __/|/ _/    /|/ /   / /|/ / /|    __   / /|    / /|  / /|/ / _  \|/    //
//  / /|_|/ /  /  /|/ / // //|/ / /|__- / /  / /___  / -|_ - /|/ /     /|     //
// /_/|/   /_/ /_/|/ /_/ /_/|/ |\ ___--|_|  /_____/| |-___-_|/  /____-/|/     //
// |_|/    |_|/|_|/  |_|/|_|/   \|___|-    |_____|/   |___|     |____|/       //
//                   _ _    _    ___   _  _      __   __                      //
//                  | | |  | |  | T_| | || |    |  | |  |                     //
//                  | _ |  |T|  |  |  |  _|      ||   ||                      //
//                  || || |_ _| |_|_| |_| _|    |__| |__|                     //
//                                                                            //
//----------------------------------------------------------------------------//
// Alejandro A. Stefan Zavala // <alestefanz@hotmail.com> //                  //
////////////////////////////////////////////////////////////////////////////////

#define FCII_VERSION "VERSION: \"Assym. 10\"" // Finishing network tests

// ** W A R N I N G ** BE ADVISED: THIS EARLY VERSION IS NOT YET FUNCTIONAL.  // 

////////////////////////////////////////////////////////////////////////////////
/* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
 * ABOUT: This is the main file of the second major  release  of  the  Fanclub *
 * distributed control system for fan array wind tunnels. This is the  "Slave" *
 * side of the system (the other being the "Master" side, which  controls  the *
 * different available Slaves in the network.                                  *
 *                                                                             *
  * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */
////////////////////////////////////////////////////////////////////////////////

//// DEPENDENCIES //////////////////////////////////////////////////////////////

#include "mbed.h" // STD Mbed functions

#include "settings.h" // Global settings for FCMKII
#include "print.h" // Thread-saf printing
#include "Communicator.h" // Network handler




//// MAIN //////////////////////////////////////////////////////////////////////

int main(){ ////////////////////////////////////////////////////////////////////
    
// INITIALIZATION ==============================================================

    // Print information = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    printf(INIT); // (size: 1560)
    printf(FCII_VERSION);  
    
    printf("\n\r+--SETTINGS-------"
    "-------------------------------------------------------------+"
        // General:
        "\n\r|\t - BAUD RATE: %d"
        "\n\r|\t - FANS: %d"
        "\n\r|\t - BLINK PERIOD (SLOW): %0.2fs"
        "\n\r|\t - BLINK PERIOD (FAST): %0.2fs"
        "\n\r+ - - - - - - - - - - - - - - - - - - - - - - - - - - "
        "- - - - - - - - - - - - - "
        // Networking:
        "\n\r|\t - BROADCAST PORT: %d"
        "\n\r|\t - INIT. TIMEOUT: %dms"
        "\n\r|\t - PASSWORD: \"%s\""
        "\n\r|\t - SLAVE MISO PORT: %d"
        "\n\r|\t - SLAVE MOSI PORT: %d"
        "\n\r|\t - SLAVE LISTENER PORT: %d"
        "\n\r|\t - MAX. MESSAGE LENGTH : %d characters"
        "\n\r|\t - MAX. NETW. TIMEOUTS BEFORE REBOOT: %d"
        "\n\r|\t - MAX. MASTER TIMEOUTS: %d"
        "\n\r+ - - - - - - - - - - - - - - - - - - - - - - - - - - "
        "- - - - - - - - - - - - - "
        // Fan array:
        "\n\r|\t - DEF. FAN MODE: %s"
        "\n\r|\t - DEF. TARGET RELATION[0]: %.1f"
        "\n\r|\t - DEF. TARGET RELATION[1]: %.1f"
        "\n\r|\t - DEF. FAN AMOUNT: %d"
        "\n\r|\t - DEF. COUNTER COUNTS: %d"
        "\n\r|\t - DEF. PULSES PER ROTATION: %d"
        "\n\r|\t - DEF. MAX RPM: %d"
        "\n\r|\t - DEF. MIN RPM: %d"
        "\n\r|\t - DEF. MIN DUTY CYCLE: %0.2f%%"
        ,BAUD, NUMFANS, BLINK_SLOW, BLINK_FAST, BROADCAST_PORT, TIMEOUT_MS, 
        PASSWORD, SMISO, SMOSI, SLISTENER, MAX_MESSAGE_LENGTH, 
        MAX_NETWORK_TIMEOUTS, 
        MAX_MASTER_TIMEOUTS,
        FAN_MODE == SINGLE? "SINGLE":"DOUBLE",
        TARGET_RELATION_0,
        TARGET_RELATION_1,
        MAX_FANS,
        COUNTER_COUNTS,
        PULSES_PER_ROTATION,
        MAX_RPM,
        MIN_RPM,
        MIN_DC*100.0);
    
    printf("\n\r+-------------------------------------------------------------"
        "-----------------+\n\r");
        
    
    // Initialize modules = = = = = = = = = = = = = = = = = = = = = = = = = = = 
    
    T.start();
    
    Communicator communicator; // (Processor is initialized inside)
    
    pl
    printf("\n\r[%08dms][M] Done w/ initialization",tm);
    pu
    
// MAIN LOOP ===================================================================

    //osThreadSetPriority(osThreadGetId(), osPriorityIdle);
        // Set the main thread's priority to be the lowest.
// (See https://os.mbed.com/users/mzta/notebook/how-to-change-the-priority-of-the-mainmain-thread-/)

    while(true){
        Thread::wait(osWaitForever);
    }


// =============================================================================

    return 0; 
    
}// (end main) /////////////////////////////////////////////////////////////////