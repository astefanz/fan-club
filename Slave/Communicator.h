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
     NO_MASTER = -2,
     CONNECTED = 1
	};

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

	void reboot(void);
		/* ABOUT: Shut down the Processor module and reboot the MCU.
		 */
   
    // PRIVATE DATA ------------------------------------------------------------
    Processor processor;      // Command-processing module
    int periodMS;             // MISO period
	uint32_t misoIndex;
	uint32_t mosiIndex;
	char version[16];

	bool
		mosiConnectedFlag,		// For MOSI to keep track of connection
		listenerConnectedFlag,	// For MOSI to tell listener if connected
		misoConnectedFlag,		// For MOSI to tell MISO if connected
		mosiDisconnectFlag;		// For listener to tell MOSI to disconnect

    EthernetInterface ethernet;
    UDPSocket slaveMISO, slaveMOSI, slaveListener; // Use UDP
    
    SocketAddress masterMISO, masterMOSI;
        // Store information of all relevant Master sockets
    
    Thread listenerThread, misoThread, mosiThread;
        // Use threads for communications

    Mutex
		sendLock, 	// Send only from one thread at a time
		misoLock,	// Block MISO thread when configuring in handshake
		listenerConnectedFlagLock,	// Set/Get connection flag for listener
		mosiDisconnectFlagLock;		// Set/Get disconnect flag for MOSI thread

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
