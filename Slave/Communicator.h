////////////////////////////////////////////////////////////////////////////////
// Project: Fanclub Mark II "Slave" // File: Communicator.h - Interface       //
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

#ifndef COMMUNICATOR_H
#define COMMUNICATOR_H

//// ABOUT /////////////////////////////////////////////////////////////////////
// This module handles communications to Master throughout ethernet.          //
////////////////////////////////////////////////////////////////////////////////

//// DEPENDENCIES //////////////////////////////////////////////////////////////

#include "EthernetInterface.h"
#include "SocketAddress.h"
#include "UDPSocket.h"
#include "Mutex.h"
#include "Thread.h"

#include "Processor.h"
#include "print.h"
#include "settings.h"
#include "feedback.h"

//// CONSTANT DECLARATIONS /////////////////////////////////////////////////////

enum {
     NO_NETWORK = -4, 
     INITIALIZING = -3, 
     NO_MASTER = -2,
     CONNECTING = 0,  
     CONNECTED = 1};

enum {
	L_ON = 1,
	L_OFF = 0,
	L_TOGGLE = 2};

//// CLASS INTERFACE ///////////////////////////////////////////////////////////

class Communicator {
public:

    // CONSTRUCTORS AND DESTRUCTORS --------------------------------------------

    Communicator(const char version[]);
        /* ABOUT: Constructor for class Communicator. Starts networking threads.
         * PARAMETERS:
         * -Processor &processor: Reference to Processor instance. (See Proces-
         *  sor.h)
         */


private:
    // PRIVATE FUNCTIONS -------------------------------------------------------
         
    void _listenerRoutine(void);
        /* ABOUT: Code to be executed by the broadcast listener thread.
         */ 
         
    void _misoRoutine(void);
        /* ABOUT: Code to be executed by the miso thread.
         */

    void _mosiRoutine(void);
        /* ABOUT: Code to be executed by the mosi thread.
         */
         
    int _send(const char* message, int times = 1, bool print = false);
		/* ABOUT: Send a message to the known Master MISO socket using the Slave
		*	MISO socket. The currently stored exchange index will be added automati-
		*	cally, along with its following delimiter ("INDEX|" e.g "00000001|").
		* PARAMETERS:
		* -const char* message: NULL-terminated char-array containing message 
		*	to be sent.
		* -int times: number of times to send a message, (for good measure)
		*	defaults to 1.
		* -bool print: whether to print to terminal the message sent. Defaults to
		*	false.
		* RETURN: Int; number of bytes sent upon success, negative socket error
		*	code on failure. If repetition is requested, the result of the last mes-
		*	sage is returned.
		* WARNING: This private member function assumes (1) the Slave's MISO 
		*	socket is ready to send messages and (2) the message given ends in
		*	'\0'.
	 	* NOTE: Blocks for thread-safety.
		*/

	int _sendError(const char* message);
		/* ABOUT: Send an error message to Master, if possible. This function will
		 * try to use either the MISO-side _send function 
		 * (if there is a connection) or the listener thread's socket.
		 * PARAMETERS:
		 * - const char* message: NULL-terminated message to send.
		 * RETURN: int; number of bytes received upon success, negative error code
		 * on failure.
		 * NOTE: Blocks for thread-safety.
		 */

	int _receive(char* specifier, char message[]);
		/* ABOUT: Receive a message in MOSI socket and place it in the given
		 * placeholder arguments.
		 * RETURNS: Int; number of bytes received upon success, negative error
		 * code upon failure.
		 *
		 * Expected message format:
		 *
		 * 		MOSI_INDEX | C | MESSAGE
		 *
		 */ 
         
    void _setStatus(const int newStatus);
        /* ABOUT: Set the current connection status, which will be displayed to
         *  The user using the MCU's LED's.
         */

	int getStatus(void);
		/* ABOUT: Get current connection status in a thread-safe manner.
		 */
        
    void _setRed(int state = L_TOGGLE);
        /* ABOUT: Set state of red USR LED. To be used by _setStatus.
         */
         
    void _setGreen(int state = L_TOGGLE);
        /* ABOUT: Set state of green USR LED. To be used by _setStatus.
         */

	void _blinkRed(void);
		/* ABOUT: Blink red LED (alternate).
		 */

	void _blinkGreen(void);
		/* ABOUT: Blink green LED (alternate).
		 */

    const char* _interpret(int errorCode);
        /* ABOUT: Interpret a network error code and return its description.
         * PARAMETERS:
         * -int errorCode: negative error code received by some network'n
         *  instance, such as a TCPSocket.
         * RETURN: pointer to constant, NULL-terminated string of chars that
         *  describes the error, if a description is found.
         */
   
   	void _resetTimeouts(void);
		/* ABOUT: Reset Master timeout counter to 0.
		 * NOTE: Blocks for thread safety.
		 */
         
   	void _incrementTimeouts(void);
		/* ABOUT: Increase Master timeout counter by 1.
		 * NOTE: Blocks for thread safety.
		 */
         
   	int _getTimeouts(void);
		/* ABOUT: Get value of Master timeout counter.
		 * NOTE: Blocks for thread safety.
		 */
         
   	void _resetMISOIndex(void);
		/* ABOUT: Reset  MISO index to 1.
		 * NOTE: Blocks for thread safety.
		 */
         
   	void _incrementMISOIndex(void);
		/* ABOUT: Increase  MISO index by 1.
		 * NOTE: Blocks for thread safety.
		 */
         
   	uint32_t _getMISOIndex(void);
		/* ABOUT: Get value of  MISO index.
		 * NOTE: Blocks for thread safety.
		 */
         
   	void _resetMOSIIndex(void);
		/* ABOUT: Reset  MOSI index to 1.
		 * NOTE: Blocks for thread safety.
		 */
         
   	void _incrementMOSIIndex(void);
		/* ABOUT: Increase  MOSI index by 1.
		 * NOTE: Blocks for thread safety.
		 */
         
   	uint32_t _getMOSIIndex(void);
		/* ABOUT: Get value of  MOSI index.
		 * NOTE: Blocks for thread safety.
		 */

   	void _setMOSIIndex(uint32_t newIndex);
		/* ABOUT: Set value of  MOSI index.
		 * NOTE: Blocks for thread safety.
		 */

         
    // PRIVATE DATA ------------------------------------------------------------
    Processor processor;      // Command-processing module
    int status;               // Connection status
    int periodMS;             // MISO period
	int bPeriodMS;
	char version[16];
	char passcode[16];

    uint32_t mosiIndex;   // Index messages
    uint32_t misoIndex;       // Index outgoing messages
    int masterTimeouts;  // Keep track of timeouts for connection check
	int maxMasterTimeouts;

    EthernetInterface ethernet;
    
    UDPSocket slaveMISO, slaveMOSI, slaveListener; // Use UDP
    
    SocketAddress masterMISO, masterMOSI, masterListener, masterBroadcast;
        // Store information of all relevant Master sockets
    
    Thread listenerThread, misoThread, mosiThread;
        // Use threads for communications

    Mutex	periodLock, // Lock relevant threads when modifying values
			bPeriodLock,
			statusLock,
			timeoutLock,
			misoIndexLock,
			mosiIndexLock,
			sendLock,
			receiveLock,
			maxMasterTimeoutsLock,
			listenerSocketLock,
			passcodeLock;

    DigitalOut 
		red, 
	 	green
		,xred
		#ifndef JPL 
		,xgreen
		#endif
		;
        // Use red and green LED's to convey connection status
    
};


#endif // COMMUNICATOR_H
