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
#include "print.h" // Thread-safe printing
#include "Communicator.h" // Network handler

#define FCMKII_VERSION "B06271"
// BMMDD: Restored basement + seven sq. FAWT's
// BASE1: Switch to basement configuration
// CAST17.0DB: Added "MULTI" command to Processor
// Changed on CAST150.0DB: Removed default fan array values and refactored main
// Changed on CAST14.2DB: Locked RPM and DC R/W... Fixed crashes
// Changed on CAST13.0DB: Reduced thread stacks to 4KB each and
// deactivated stack debug prints


void mainLoop(void){
	// ABOUT: Workaround to control main thread stack size:
	pl;printf("\n\r[%08dms][M] \"Main\" thread started: %lX", tm,
		(uint32_t)Thread::gettid());pu;
	Communicator communicator(FCMKII_VERSION);

	Thread::wait(osWaitForever);
} // End mainLoop


//// MAIN //////////////////////////////////////////////////////////////////////


int main(){ ////////////////////////////////////////////////////////////////////

// INITIALIZATION ==============================================================

    // Print information = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    printf(INIT); // (size: 1560)
    printf("\n\r VERSION: %s", FCMKII_VERSION);

    printf("\n\r+--SETTINGS-------"
    "-------------------------------------------------------------+"
        // General:
        "\n\r|\t - STACK SIZE: %d KB"
        "\n\r|\t - BAUD RATE: %d"
        "\n\r|\t - FANS: %d"
        "\n\r|\t - BLINK PERIOD (SLOW): %0.2fs"
        "\n\r|\t - BLINK PERIOD (FAST): %0.2fs"
        "\n\r+ - - - - - - - - - - - - - - - - - - - - - - - - - - "
        "- - - - - - - - - - - - - "
        // Networking:
        "\n\r|\t - BROADCAST PORT: %d"
        "\n\r|\t - INIT. TIMEOUT: %dms"
        "\n\r|\t - PASSCODE: \"%s\""
        "\n\r|\t - SLAVE MISO PORT: %d"
        "\n\r|\t - SLAVE MOSI PORT: %d"
        "\n\r|\t - SLAVE LISTENER PORT: %d"
        "\n\r|\t - MAX. MESSAGE LENGTH : %d characters"
        "\n\r|\t - MAX. NETW. TIMEOUTS BEFORE REBOOT: %d"
        "\n\r|\t - MAX. MASTER TIMEOUTS: %d"
        "\n\r|\t - MAX. FANS: %d"
        "\n\r|\t - DEF. FAN RPM TIMEOUT: %d us"
        "\n\r+ - - - - - - - - - - - - - - - - - - - - - - - - - - "
        "- - - - - - - - - - - - - ",
        STACK_SIZE,
		BAUD, NUMFANS, BLINK_SLOW, BLINK_FAST,

		BROADCAST_PORT, TIMEOUT_MS,
        PASSCODE, SMISO, SMOSI, SLISTENER, MAX_MESSAGE_LENGTH,
        MAX_NETWORK_TIMEOUTS,
        MAX_MASTER_TIMEOUTS,

		MAX_FANS,
		DEFAULT_FAN_TIMEOUT_US

	);
    printf("\n\r+-------------------------------------------------------------"
        "-----------------+\n\r");


    // Initialize modules = = = = = = = = = = = = = = = = = = = = = = = = = = =
    T.start();

    pl
    printf("\n\r[%08dms][M] Done w/ initialization",tm);
    pu


// MAIN LOOP ===================================================================

	Thread mainThread(osPriorityNormal, 8*1024);
	mainThread.start(&mainLoop);

	#if defined(HEAP_PRINTS) || defined(STACK_PRINTS)
	while(true){
	#endif

		#ifdef HEAP_PRINTS
		// See
		// https://os.mbed.com/docs/latest/tutorials/
		//		optimizing.html#runtime-memory-tracing

		mbed_stats_heap_t heap_stats;

			mbed_stats_heap_get(&heap_stats);
			pl;printf("\n\rHEAP SIZE: %10lu MAX HEAP: %10lu",
				heap_stats.current_size, heap_stats.max_size);pu;


		#endif // HEAP_PRINTS

		#ifdef STACK_PRINTS
		pl;printf(
			"\n\r\tFMAIN (%10X): Used: %6lu Size: %6lu Max: %6lu",
			0,
			mainThread.used_stack(),
			mainThread.stack_size(),
			mainThread.max_stack()
		);pu;
		#endif // STACK_PRINTS

		#if defined(HEAP_PRINTS) || defined(STACK_PRINTS)
		Thread::wait(1000);
	} // End heap or stack print loop
	#endif

	Thread::wait(osWaitForever);

// =============================================================================

    return 0;

}// (end main) /////////////////////////////////////////////////////////////////
