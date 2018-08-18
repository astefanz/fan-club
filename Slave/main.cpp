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

#define FCMKII_VERSION "CAST14.2DB" // Letter for bootloader testing
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
        "\n\r+ - - - - - - - - - - - - - - - - - - - - - - - - - - "
        "- - - - - - - - - - - - - "
        // Fan array:
        "\n\r|\t - DEF. FAN MODE: %s"
        "\n\r|\t - DEF. TARGET RELATION[0]: %.1f"
        "\n\r|\t - DEF. TARGET RELATION[1]: %.1f"
        "\n\r|\t - DEF. FAN AMOUNT: %d"
        "\n\r|\t - DEF. COUNTER COUNTS: %d"
        "\n\r|\t - DEF. PULSES PER ROTATION: %d"
        "\n\r|\t - DEF. PWM FREQUENCY: %d Hz"
        "\n\r|\t - DEF. MAX RPM: %d"
        "\n\r|\t - DEF. MIN RPM: %d"
        "\n\r|\t - DEF. MIN DUTY CYCLE: %0.2f%%"
        "\n\r|\t - DEF. CHASER TOLERANCE: %0.2f%%"
        "\n\r|\t - DEF. MAX FAN TIMEOUTS: %d"
        ,BAUD, NUMFANS, BLINK_SLOW, BLINK_FAST, BROADCAST_PORT, TIMEOUT_MS, 
        PASSCODE, SMISO, SMOSI, SLISTENER, MAX_MESSAGE_LENGTH, 
        MAX_NETWORK_TIMEOUTS, 
        MAX_MASTER_TIMEOUTS,
        FAN_MODE == SINGLE? "SINGLE":"DOUBLE",
        TARGET_RELATION_0,
        TARGET_RELATION_1,
        MAX_FANS,
        COUNTER_COUNTS,
        PULSES_PER_ROTATION,
        PWM_FREQUENCY,
        MAX_RPM,
        MIN_RPM,
        MIN_DC*100.0,
		CHASER_TOLERANCE*100.0,
		MAX_FAN_TIMEOUTS);
    
    printf("\n\r+-------------------------------------------------------------"
        "-----------------+\n\r");
        
    
    // Initialize modules = = = = = = = = = = = = = = = = = = = = = = = = = = = 
    T.start();
    
    pl
    printf("\n\r[%08dms][M] Done w/ initialization",tm);
    pu
   

// MAIN LOOP ===================================================================

    //osThreadSetPriority(osThreadGetId(), osPriorityIdle);
        // Set the main thread's priority to be the lowest.
// (See https://os.mbed.com/users/mzta/notebook/how-to-change-the-priority-of-the-mainmain-thread-/)

	Thread mainThread(osPriorityNormal, 8*1024);
	mainThread.start(&mainLoop);
	
	#ifdef HEAP_PRINTS
	mbed_stats_heap_t heap_stats;

	while(true){
		mbed_stats_heap_get(&heap_stats);
		pl;printf("\n\rHEAP SIZE: %10lu MAX HEAP: %10lu",
			heap_stats.current_size, heap_stats.max_size);pu;

		Thread::wait(500);
	}
	#endif // HEAP_PRINTS
	
	/*
	while(true){
		pl;printf(
			"\n\r\tFMAIN (%10X): Used: %6lu Size: %6lu Max: %6lu",
			0,
			mainThread.used_stack(),
			mainThread.stack_size(),
			mainThread.max_stack()
		);pu;
		Thread::wait(1000);
	}
	*/
	
	// DEBUG: MEMORY ANALYTICS -------------------------------------------------
	// See https://os.mbed.com/docs/latest/tutorials/optimizing.html#runtime-memory-tracing
	/*
	int cnt = osThreadGetCount();
    mbed_stats_stack_t *stats = (mbed_stats_stack_t*) malloc(cnt * sizeof(mbed_stats_stack_t));

	while(true) {
    	cnt = mbed_stats_stack_get_each(stats, cnt);
		for (int i = 0; i < cnt; i++) {
			pl;printf("\n\rThread: 0x%X, Stack size: %u, Max stack: %u\r\n", 
				stats[i].thread_id, 
				stats[i].reserved_size, 
				stats[i].max_size);pu;
		}

		Thread::wait(1000);

	}
	*/
	// -------------------------------------------------------------------------	

	Thread::wait(osWaitForever);

// =============================================================================

    return 0; 
    
}// (end main) /////////////////////////////////////////////////////////////////
