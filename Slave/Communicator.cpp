////////////////////////////////////////////////////////////////////////////////
// Project: Fanclub Mark II "Slave" // File: Communicator.cpp - Implementation//
//----------------------------------------------------------------------------//
// CALIFORNIA INSTITUTE OF TECHNOLOGY // GRADUATE AEROSPACE LABORATORY //	  //
// CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES							  //
//----------------------------------------------------------------------------//
//		____	  __	  __  __	  _____		 __		 __    __	 ____	  //
//	   / __/|	_/ /|	 / / / /|  _- __ __\	/ /|	/ /|  / /|	/ _  \	  //
//	  / /_ |/  / /	/|	/  // /|/ / /|__| _|   / /|    / /|  / /|/ /   --||   //
//	 / __/|/ _/    /|/ /   / /|/ / /|	 __   / /|	  / /|	/ /|/ / _  \|/	  //
//	/ /|_|/ /  /  /|/ / // //|/ / /|__- / /  / /___  / -|_ - /|/ /	   /|	  //
// /_/|/   /_/ /_/|/ /_/ /_/|/ |\ ___--|_|	/_____/| |-___-_|/	/____-/|/	  //
// |_|/    |_|/|_|/  |_|/|_|/	\|___|-    |_____|/   |___|		|____|/		  //
//					 _ _	_	 ___   _  _		 __   __					  //
//					| | |  | |	| T_| | || |	|  | |	|					  //
//					| _ |  |T|	|  |  |  _|		 ||   ||					  //
//					|| || |_ _| |_|_| |_| _|	|__| |__|					  //
//																			  //
//----------------------------------------------------------------------------//
// Alejandro A. Stefan Zavala // <alestefanz@hotmail.com> //				  //
////////////////////////////////////////////////////////////////////////////////

//// ABOUT /////////////////////////////////////////////////////////////////////
// This module handles communications to Master throug ethernet.			  //
////////////////////////////////////////////////////////////////////////////////

/* -----------------------------------------------------------------------------
 * SUMMARY OF CHARACTER CODES
 * -----------------------------------------------------------------------------
	N “NORMAL” i.e. Standard broadcast
	U “UPDATE” i.e. Update broadcast
	R “REBOOT” i.e. Reboot MCU
	L “LAUNCH” i.e. Launch MkII
 * -----------------------------------------------------------------------------
	S “STANDARD” i.e. Standard command for Processor
	D “DUTY CYCLE” i.e. Set Duty Cycle
	C “CHASE” i.e. Chase RPM
	H “HANDSHAKE” i.e. Handshake to start connection
	X “DISCONNECT” i.e. Assume disconnection (ShutdownProcessor)
	Z “REBOOT” i.e. Reboot MCU
	I “INDEX” i.e. Reset MISO Index
	W “POWER” i.e. Power PSU
 * -----------------------------------------------------------------------------
	A “APPLICATION” i.e. Message from MkII
	B “BOOTLOADER” i.e. Message from Bootloader
	M “MAINTAIN” i.e. Maintain connection
	T “STANDARD” i.e. Standard update message
	E “ERROR” i.e. Error message
	P “PING” i.e. Ping request
	I “INDEX” i.e. MISO index reset
 * -------------------------------------------------------------------------- */

/* -----------------------------------------------------------------------------
 * NOTES ON THREAD SAFETY
 * -----------------------------------------------------------------------------
 * CRITICAL SECTIONS ...........................................................
 * 
 * -The Processor shall not be shut down in the middle of its RPM update 
 *	routine. Processor update retrieval is thread-safe (checks isolated buffer)
 *
 * -The MISO thread shall be blocked for and during handshake
 *
 * -The only blocking operations dependent on other threads done by the 
 *	listener thread are checking a connection flag and setting a disconnection
 *	flag (shared with MOSI). For all other matters, the listener thread is to 
 *	be isolated.
 *
 * 
 * -------------------------------------------------------------------------- */

//// DEPENDENCIES //////////////////////////////////////////////////////////////
#include "Communicator.h"
#include "mbed_stats.h"
#include "FastPWM.h"
//// CLASS INTERFACE ///////////////////////////////////////////////////////////

// CONSTRUCTORS AND DESTRUCTORS ------------------------------------------------

Communicator::Communicator(const char version[]):
	processor(),
	periodMS(TIMEOUT_MS),
	
	mosiConnectedFlag(false),
	listenerConnectedFlag(false),
	misoConnectedFlag(false),
	mosiDisconnectFlag(false),

	listenerThread(
		osPriorityNormal,
		STACK_SIZE * 1024,
		NULL, /* Stack memory */
		"LSTN" // Name
	),
	misoThread(
		osPriorityNormal, // Priority
		STACK_SIZE * 1024,
		NULL, // Stack memory
		"MISO" // Name
	),
	mosiThread(
		osPriorityNormal, 
		STACK_SIZE * 1024,
		NULL, // Stack memory
		"MOSI" // Name
	),
	
	red(LED3), 
	green(LED1),

	xred(D3), 
	#ifndef JPL
	xgreen(D5)
	#endif 
	{ // // // // // // // // // // // // // // // // // // // // // // // // //
	/* ABOUT: Constructor for class Communicator. Starts networking threads.
	 * PARAMETERS:
	 * -Processor &processor: Reference to Processor instance. (See Proces-
	 *	sor.h)
	 */
	pl;printf("\n\r[%08dms][c] Initializing Communicator threads", tm);pu;
	
	strcpy(this->version, version);

	// Initialize ethernet interface - - - - - - - - - - - - - - - - - - - - - -
	int result = -1;
	unsigned int count = 1;
	
	// Set LED
	this->_setRed(L_ON);

	while(result < 0){ // Ethernet loop ........................................
		pl;printf(
		"\n\r[%08dms][C] Initializing ethernet interface...(%d)",
		tm, count++);pu;
		
		result = this->ethernet.connect();
		
		if(result < 0){
			// If there was an error at this stage, there is a pro-
			// blem with the network.
			pl; printf("\n\r[%08dms][C] "
				"ERROR initializing ethernet: \"%s\"",
				tm, this->_interpret(result));pu;
			this->reboot();	
		} // End if result < 0
		
	} // End ethernet loop .....................................................
	pl; printf("\n\r[%08dms][C] Ethernet initialized \n\r\tMAC: %s\n\r\tIP: %s",tm,
		ethernet.get_mac_address(), ethernet.get_ip_address());pu;
	
	// Initialize sockets - - - - - - - - - - - - - - - - - - - - - - - - - - - 
	
	pl;
	printf("\n\r[%08dms][C] Initializing sockets", tm);
	pu;

	this->slaveMISO.open(&this->ethernet);
	this->slaveMISO.bind(SMISO);
	
	this->slaveMOSI.open(&this->ethernet);
	this->slaveMOSI.bind(SMOSI);
	this->slaveMOSI.set_timeout(TIMEOUT_MS);
	
	this->slaveListener.open(&this->ethernet);
	this->slaveListener.bind(SLISTENER);
	this->slaveListener.set_timeout(-1); // Listen for broadcasts w/o timeout
	
	pl;
	printf("\n\r[%08dms][C] Sockets initialized",tm);
	pu;

	this->processor.start();
	
	pl;printf("\n\r[%08dms][C] Ready for messages",tm);pu;	
	
	// Start communications thread - - - - - - - - - - - - - - - - - - - - - - -
	// Set LED
	this->_setRed(L_OFF);

	this->misoThread.start(callback(this,
		&Communicator::_misoRoutine));

	this->mosiThread.start(callback(this,
		&Communicator::_mosiRoutine));

	// Start listener thread - - - - - - - - - - - - - - - - - - - - - - - - - -
	this->listenerThread.start(callback(this, &Communicator::_listenerRoutine));
	
	pl;printf("\n\r[%08dms][c] Communicator constructor done", tm);pu;

	} // End Communicator::Communicator // // // // // // // // // // // // // /
	 
void Communicator::_listenerRoutine(void){ // // // // // // // // // // // // /
	/* ABOUT: Code to be executed by the broadcast listener thread.
	 */ 
	 
	// Thread setup ============================================================
	pl;printf("\n\r[%08dms][L] \"Listener\" thread started: %lX", tm, 
		uint32_t(Thread::gettid()) 
	);pu;

	listenerID = uint32_t(Thread::gettid());
	
	// Declare placeholders: - - - - - - - - - - - - - - - - - - - - - - - -
	int bytesReceived = 0, lastListenerPort = 0;
	char dataReceived[MAX_MESSAGE_LENGTH];
	
	SocketAddress masterBroadcast, masterListener;

	while(true){ // Listener routine loop ======================================
		
		Thread::wait(TIMEOUT_MS);
		this->_setGreen(L_ON);
		
		// Receive data: - - - - - - - - - - - - - - - - - - - - - - - - - - - -
		bytesReceived = this->slaveListener.recvfrom(
			&masterBroadcast,
			dataReceived,
			MAX_MESSAGE_LENGTH
			);

		this->_setGreen(L_OFF);
		
		// Validate reception of data = = = = = = = = = = = = = = = = = = = = = 
		if (bytesReceived <= 0){
			pl;printf(
				"\n\r[%08dms][C] UNRECOGNIZED NETWORK ERROR. WILL REBOOT: "
				"\n\r\t\"%s\""
				,tm, this->_interpret(bytesReceived));pu;

			// Reboot:
			this->reboot();

		} else{
			// Positive code. A message was received.
			// A positive value indicates a message was received.
			
			// Format data:
			dataReceived[bytesReceived] = '\0';

			// Validate data received: - - - - - - - - - - - - - - - - - - - - -
			char* splitPointer = NULL; // Save splitting position in strtok_r
			char* splitPositionTracker = NULL;
			char specifier = '\0';
				// NOTE: Use strtok_r instead of strtok for thread safety.

			/* -----------------------------------------------------------------
			 * EXPECTED POSSIBLE BROADCAST FORMATS:
			 * -----------------------------------------------------------------
			 * - STD BCAST: N|PASSCODE|M L PORT
			 * - UPDT BCAST: U|PASSCODE|M L PORT|FILE NAME|FILE SIZE BYTES
			 * - SHUTD BCAST: R|PASSCODE
			 * - LAUNCH MkII (For Bootloader): L|PASSCODE
			 * ---------------------------------------------------------------*/
			
			// Specifier .......................................................
			// Get what should be a character specifying the nature of this
			// broadcast:
			splitPointer = strtok_r(dataReceived, "|", &splitPositionTracker);
				
			// Verify:
			if (splitPointer == NULL){
				pl;printf("\n\r[%08dms][L] NULL Splitter on char. Discarded",tm);pu;
				continue;
			}

			// Save specifier:
			specifier = splitPointer[0];

			// Passcode ........................................................
			// Point to passcode:
			splitPointer = strtok_r(NULL, "|", &splitPositionTracker);
			
			// Check passcode:
			if(splitPointer == NULL){
				pl;printf("\n\r[%08dms][L] NULL Splitter on P.Code. Discarded",tm);pu;
				continue;
			} else if (strcmp(splitPointer, PASSCODE) != 0){
				pl;printf("\n\r[%08dms][L] Passcode mismatch (%s != %s)", tm,
					splitPointer, PASSCODE);pu;
				continue;	
			} 				
			// Now assume correct passcode and proceed to check specifier ......

			switch(specifier){
				
				case 'N': { // STD BCAST. Send reply
					
					// Update Master Listener port
					
					splitPointer = strtok_r(NULL, "|", &splitPositionTracker);
					if(splitPointer == NULL){
						pl;printf("\n\r[%08dms][L] NULL Splitter on M.L.Port "\
							"discarded",tm);pu;
						continue;
					}

					int port = atoi(splitPointer);
					if(port <= 0){
						pl;printf("\n\r[%08dms][L] Bad M.L.Port \"%d\" "\
							"discarded",tm, port);pu;
						continue;
					} else if (port != lastListenerPort){

						//this->errorLock.lock();
						masterListener.set_ip_address(
							masterBroadcast.get_ip_address()
						);
						masterListener.set_port(port);
						lastListenerPort = port;
						//this->errorLock.unlock();

					}
					
					// If disconnected, send standard reply

					this->listenerConnectedFlagLock.lock();
					if(not this->listenerConnectedFlag){
						char reply[MAX_MESSAGE_LENGTH];

						int n = snprintf(reply, 256, "A|%s|%s|N|%d|%d|%s", 
							PASSCODE,
							this->ethernet.get_mac_address(),
							SMISO, 
							SMOSI,
							this->version);

						this->slaveListener.sendto(masterListener, reply, n);
						
						pl;printf("\n\r[%08dms][L] Broadcast validated. "\
							"Reply sent to %s, %d", tm,
							masterListener.get_ip_address(),
							masterListener.get_port()
						);pu;

					} // End reply if disconnected
					this->listenerConnectedFlagLock.unlock();

					break;
				} // End STD BCAST

				case 'U': { // UPDATE BCAST. Reboot
					pl;printf("\n\r[%08dms][L] Update command received. "\
						"Rebooting", tm);pu;
					
					this->reboot();
					break;
				} // End UPDATE BCAST

				case 'R': { // SHUTDOWN BCAST. Reboot
					pl;printf("\n\r[%08dms][L] Shutdown command received. "\
						"Rebooting", tm);pu;
					
					this->reboot();
					break;
				} // End SHUTDOWN BCAST
				
				case 'r':{ // TARGETTED SHUTDOWN BCAST. Check MAC
					pl;printf("\n\r[%08dms][L] Targetted shutdown received", 
						tm);pu;
					
					splitPointer = strtok_r(NULL, "|", &splitPositionTracker);
					if(splitPointer == NULL){
						pl;printf("\n\r[%08dms][L] NULL Splitter on target MAC"\
							" (discarded)",tm);pu;
						continue;
					} else if (strcmp(splitPointer, 
						this->ethernet.get_mac_address()) == 0){
				
						pl;printf("\n\r[%08dms][L] Target MAC match. rebooting.", 
							tm);pu;
						
						this->reboot();

					} else {
						
						pl;printf("\n\r[%08dms][L] Target MAC mismatch (%s). "\
							"Ignoring", tm, this->ethernet.get_mac_address());pu;
					}
				
					break;

				}
				case 'X': { // DISCONNECT BCAST. Change status to DISCONNECTED
					pl;printf("\n\r[%08dms][L] Disconnect command received.",
						tm);pu;
					
					// Set disconnect flag:
					this->mosiDisconnectFlagLock.lock();
					this->mosiDisconnectFlag = true;
					this->mosiDisconnectFlagLock.unlock();

					break;
				} // End DISCONNECT BCAST

				case 'L': { // LAUNCH BCAST. Ignore
					pl;printf("\n\r[%08dms][L] \"Launch\" command ignored",
						tm);pu;	
					break;
				} // End LAUNCH BCAST

				default: { // Unrecognized broadcast specifier
					pl;printf("\n\r[%08dms][L] Unrecognized BC code \"%c\""\
						" ignored",tm, specifier);pu;	
				}

			} // End switch specifier
			
		} // End reception validation = = = = = = = = = = = = = = = = = = = = = 
	}// End listener routine loop ==============================================
} // End Communicator::_listenerRoutine // // // // // // // // // // // // // /
   
void Communicator::_misoRoutine(void){ // // // // // // // // // // // // // //
	// ABOUT: Send periodic updates to Master once connected.

	// Thread setup ============================================================
	pl;printf("\n\r[%08dms][O] \"MISO\" thread started: %lX", tm, 
		uint32_t(Thread::gettid())
	);pu;

	misoID = uint32_t(Thread::gettid());

	// Initialize placeholders -------------------------------------------------
	char processed[MAX_MESSAGE_LENGTH] = {0}; // Feedback to be sent to Master 

	processed[0] = 'M';
	processed[1] = '\0';
	// Thread loop =============================================================
	while(true){
		
		// DEBUG: PRINT STACKS OF COMMS. THREADS -------------------------------
		#ifdef STACK_PRINTS
		pl;printf(
			"\n\r\tMISO (%10X): Used: %6lu Size: %6lu Max: %6lu"\
			"\n\r\tMOSI (%10X): Used: %6lu Size: %6lu Max: %6lu"\
			"\n\r\tLIST (%10X): Used: %6lu Size: %6lu Max: %6lu",
			
			this->mosiID,
			this->mosiThread.used_stack(),
			this->mosiThread.stack_size(),
			this->mosiThread.max_stack(),
			
			this->misoID,
			this->misoThread.used_stack(),
			this->misoThread.stack_size(),
			this->misoThread.max_stack(),
			
			this->listenerID,
			this->listenerThread.used_stack(),
			this->listenerThread.stack_size(),
			this->listenerThread.max_stack()
		);pu;
		#endif // STACK_PRINTS -------------------------------------------------
		
		// Check status = = = = = = = = = = = = = = = = = = = = = = = = = = = = 
		this->misoLock.lock();
		if(this->misoConnectedFlag){
			// Connected. Send update to Master.

			// Fetch message to send -------------------------------------------
			this->processor.get(processed);
			
			// Send message ----------------------------------------------------
			this->_send(processed, 1, false); // false -> do not print to stdout
			Thread::wait(this->periodMS);
		} 
		this->misoLock.unlock();
		
		Thread::yield();
	} // End MISO loop =========================================================
} // End Communicator::_misoRoutine // // // // // // // // // // // // // // //

void Communicator::_mosiRoutine(void){ // // // // // // // // // // // // // //
	// ABOUT: Listen for commands from Master.

	// Thread setup ============================================================
	pl;printf("\n\r[%08dms][I] \"MOSI\" thread started: %lX", tm, 
		uint32_t(Thread::gettid())
	);pu;

	mosiID = uint32_t(Thread::gettid());

	// Communications variables:
	int masterTimeouts = 0;
	int maxMasterTimeouts = 0;

	// Communications placeholders:
	char buffer[MAX_MESSAGE_LENGTH] = {0};
	char specifier = '\0';
	char *splitPointer = NULL;
	char *savePointer = NULL;
	bool disconnect = false;

	// Handshake placeholders:
	int parsedMISOPort = 0;
	int parsedMOSIPort = 0;
	int parsedPeriodMS = 0;
	int parsedBPeriodMS = 0;
	int parsedMaxMasterTimeouts = 0;

	// Thread loop =============================================================
	while(true){
		
		
		this->_blinkRed();
		// Wait for message ----------------------------------------------------
		int result = this->_receive(&specifier, buffer);
		this->_blinkRed();

		// Check disconnect flag:
		if(not disconnect){
			// NOTE: Do not perform this check if the disconnect flag is 
			// already set to true

			this->mosiDisconnectFlagLock.lock();
			disconnect = this->mosiDisconnectFlag;
			this->mosiDisconnectFlagLock.unlock();
		} // End check disconnect flag

		// Verify reception = = = = = = = = = = = = = = = = = = = = = = = = = = 
		if (result <= 0) {		

			// Check network status:
			// NOTE: CANNOT TEST NETWORK STATUS W/ MBED 5.4.9
			nsapi_connection_status_t netStatus = 
				this->ethernet.get_connection_status();

			if(netStatus == NSAPI_STATUS_DISCONNECTED or
				netStatus == NSAPI_STATUS_ERROR_UNSUPPORTED){
				pl;printf("\n\r[%08dms][L] NETWORK ERROR. REBOOTING",tm);pu;
				
				// Reboot:
				this->reboot();

			} else if( (result == NSAPI_ERROR_WOULD_BLOCK and \
				this->mosiConnectedFlag) or 
				disconnect){

				// Timeout while disconnected. Count it.
				pl;printf(
					"\n\r[%08dms][I][N] NOTE: MOSI timeout", tm);pu;
				
				masterTimeouts++;

				if(masterTimeouts >= maxMasterTimeouts or disconnect){
					// Master timed out. Disconnect.
					pl;printf(
						"\n\r[%08dms][I][N] NOTE: Master timed out or "\
						"disconnect flag raised", tm);pu;

					// NOTE: Block MISO while reconfiguring
					this->misoLock.lock();
					pl;printf(
						"\n\r[%08dms][I][N] Locked MISO", tm);pu;
					
					// Shut down Processor:
					this->processor.setStatus(OFF);
					
					pl;printf(
						"\n\r[%08dms][I][N] Turned off Processor", tm);pu;
					
					// Reset exchange indices:
					this->misoIndex = 0;
					this->mosiIndex = 0;

					// Reset timeout counters:
					masterTimeouts = 0;

					// Set connection flags:
					this->mosiConnectedFlag = false;

					this->listenerConnectedFlagLock.lock();
					this->listenerConnectedFlag = false;
					this->listenerConnectedFlagLock.unlock();

					this->mosiDisconnectFlag = false;
					disconnect = false;

					this->misoConnectedFlag = false;

					// Release MISO:
					this->misoLock.unlock();	
					this->_setRed(L_OFF); // NOTE: The opposite state will be 
										  // visible (See start of this loop)
					
					pl;printf(
						"\n\r[%08dms][I][N] Disconnected", tm);pu;
					
				} // End timeout routine
		
			} // End if socket timed out

		} else if(this->mosiConnectedFlag) {
			// Message received while connected 

			// Reset timeout counter:
			masterTimeouts = 0;

			// A message was received. Validate its content.
			switch(specifier){
				
				case 'S':{ // STANDARD
			
					// Verify nonempty message:
					if(buffer[0] == '\0'){
						pl;printf(
							"\n\r[%08dms][I][E] WARNING: EMPTY MESSAGE ON 'S'",
							tm);pu;
					} else {
					
						// Pass message to Processor:
						this->processor.process(buffer);
					
					} // End check buffer

					break;
				}
					
				case 'H':{ // HANDSHAKE
					pl;printf(
						"\n\r[%08dms][I][N] NOTE: HSK while connected", tm);pu;
					this->_send("H", 2);
					break;
				}

				case 'X':{ // DISCONNECT
					
					pl;printf(
						"\n\r[%08dms][I] Disconnect message received.", tm);pu;
					
					disconnect = true;
					break;
				}
					
				case 'R': case 'Z': { // REBOOT
					pl;printf(
						"\n\r[%08dms][I] Reboot message received."\
							" Rebooting", tm);pu;

					this->reboot();
					break;
				}
					
				case 'I':{ // INDEX
					pl;printf(
						"\n\r[%08dms][I] Resetting MOSI index" , tm);pu;
					this->mosiIndex = 0;
					
					break;
				}
					
				case 'P':{ // PING
					pl;printf(
						"\n\r[%08dms][I] Ping message received" , tm);pu;
					masterTimeouts = 0;

					break;
				}

				case 'Q':{ // PING REQUEST
					pl;printf(
						"\n\r[%08dms][I] Ping req. received" , tm);pu;
					
					this->_send("Q", 2);

					break;
				
				}
				
				default:{
					pl;printf(
						"\n\r[%08dms][I][E] WARNING: UNRECOGNIZED CODE \'%c\'",
						tm, specifier);pu;
				
					break;
				}
			
			} // End switch specifier
		
		} else if (specifier == 'H'){
			// If there is no connection, accept only HSK messages
		
			// Verify nonempty message:
				if(buffer[0] == '\0'){
					pl;printf(
						"\n\r[%08dms][I][E] WARNING: EMPTY HSK MESSAGE",
						tm);pu;
					continue;
				}
			 
				this->_send("K", 2);

				// Get network-related configuration
				// Here the buffer is expected to be formatted as 
				//
				//		 MISOP,MOSIP,PERIODMS,MAXT|ARRAY_CONFIG
				//					
				//
				
				// MISO Port
				
				splitPointer = strtok_r(buffer, ",", &savePointer);
				if(splitPointer == NULL){
					pl;printf(
						"\n\r[%08dms][I][E] NULL MISO P. IN HSK",
						tm);pu;
					continue; // Discard HSK
				}
				parsedMISOPort = atoi(splitPointer);

				if (parsedMISOPort  ==0){
					pl;printf(
						"\n\r[%08dms][I][E] ZERO MISO P. IN HSK",
						tm);pu;
					continue; // Discard HSK
				}
				
				// MOSI Port
				splitPointer = strtok_r(NULL, ",", &savePointer);
				
				if(splitPointer == NULL){
					pl;printf(
						"\n\r[%08dms][I][E] NULL MOSI P. IN HSK",
						tm);pu;
					continue; // Discard HSK
				}
				parsedMOSIPort = atoi(splitPointer);
				if (parsedMOSIPort == 0){
					pl;printf(
						"\n\r[%08dms][I][E] ZERO MOSI P. IN HSK",
						tm);pu;
					continue; // Discard HSK
				}
				
				// Comms. Period
				splitPointer = strtok_r(NULL, ",", &savePointer);
				
				if(splitPointer == NULL){
					pl;printf(
						"\n\r[%08dms][I][E] NULL PERIOD IN HSK",
						tm);pu;
					continue; // Discard HSK
				}
				
				parsedPeriodMS = atoi(splitPointer);
				
				if (parsedPeriodMS ==0){
					pl;printf(
						"\n\r[%08dms][I][E] ZERO PERIOD IN HSK",
						tm);pu;
					continue; // Discard HSK
				}
				
				// Broadcast period:
				splitPointer = strtok_r(NULL, ",", &savePointer);
				
				if(splitPointer == NULL){
					pl;printf(
						"\n\r[%08dms][I][E] NULL B.PERIOD IN HSK",
						tm);pu;
					continue; // Discard HSK
				}
				
				parsedBPeriodMS = atoi(splitPointer);
				
				if (parsedBPeriodMS ==0){
					pl;printf(
						"\n\r[%08dms][I][E] ZERO B.PERIOD IN HSK",
						tm);pu;
					continue; // Discard HSK
				}
				
				// Max. Master timeouts
				splitPointer = strtok_r(NULL, ",|", &savePointer);
				if(splitPointer == NULL){
					pl;printf(
						"\n\r[%08dms][I][E] NULL M.TIMEOUTS IN HSK",
						tm);pu;
					continue; // Discard HSK
				}

				parsedMaxMasterTimeouts = atoi(splitPointer);

				if (parsedMaxMasterTimeouts == 0 ){
					pl;printf(
						"\n\r[%08dms][I][E] ZERO M.TIMEOUTS IN HSK",
						tm);pu;
					continue; // Discard HSK
				}
				
				// Processor
				
				// Send Processor-related configuration
				// 	NOTE: COPY IN PROCESSOR
				
				splitPointer = strtok_r(NULL, "|", &savePointer);
				
				if(splitPointer == NULL){
					pl;printf(
						"\n\r[%08dms][I][E] NULL PERIOD IN HSK",
						tm);pu;
					continue; // Discard HSK
				}
				bool processorSuccess = this->processor.process(
					splitPointer, true);
				
				/* DEBUG
				pl;printf(
					"\n\r[%08dms][I] Parsed: "\
						"\n\r\tMISOP: %d"\
						"\n\r\tMOSIP: %d"\
						"\n\r\tPERIOD: %dms"\
						"\n\r\tTIMEOUTS: %d"\
						"\n\r\tProcessor: %s",
						tm,
						parsedMISOPort,
						parsedMOSIPort,
						parsedPeriodMS,
						parsedMaxMasterTimeouts,
						splitPointer
						);pu;
				*/
				
				// Check success:
				if(processorSuccess){
					
					this->misoLock.lock();

					// Apply configuration
					this->masterMISO.set_port(parsedMISOPort);
					this->masterMISO.set_ip_address(
						this->masterMOSI.get_ip_address());
					
					this->periodMS = parsedPeriodMS;
					this->slaveMOSI.set_timeout(parsedPeriodMS);

					maxMasterTimeouts = parsedMaxMasterTimeouts;
				
					// Send handshake acknowledgement
					this->_send("H", 2, true);

					// Reset timeout counters:
					masterTimeouts = 0;

					// Set connection flags:
					this->mosiConnectedFlag = true;

					this->listenerConnectedFlagLock.lock();
					this->listenerConnectedFlag = true;
					this->listenerConnectedFlagLock.unlock();

					this->mosiDisconnectFlag = false;
					disconnect = false;

					this->misoConnectedFlag = true;
					
					// Activate processor:
					this->processor.setStatus(ACTIVE);

					this->misoLock.unlock();

					pl;printf(
						"\n\r[%08dms][I][D] Handshake complete",
					tm);pu;
					
					this->_setRed(L_OFF); // NOTE: The opposite state will be 
										  // visible (See start of this loop)
				
				} else {
					pl;printf(
						"\n\r[%08dms][I][D] Handshake error at processor",
					tm);pu;

				} // End check processor success
		
		} else if (specifier == 'X'){
			// Redundant disconnect message. Ignore
			pl;printf(
				"\n\r[%08dms][I][D] Redundant disconnect message ignored",
			tm);pu;
			
		} else {
			pl;printf(
				"\n\r[%08dms][I][E] WARNING: Could not classify code \"%c\"",
				tm, specifier);pu;

		} // End verify reception

	} // End MOSI loop =========================================================
} // End Communicator::_mosiRoutine // // // // // // // // // // // // // // //

int Communicator::_send(const char* message, int times, bool print){ // // // //
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

	// Cannot send messages if there is no established connection:
	this->sendLock.lock();

	char outgoing[MAX_MESSAGE_LENGTH];
	int length = 0;
	int resultCode = 0;

	// Increment MISO index:
	this->misoIndex++;
	
	// Format message: - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	length = sprintf(outgoing, "%lu|%s", this->misoIndex, message); 
	
	// Send  message: - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
	for(int i = 0; i < times; i++){
		resultCode = this->slaveMISO.sendto(
			this->masterMISO, outgoing, length);
		if(resultCode <= 0){
			break;
		}
	}
	if (resultCode <= 0){
		pl;printf("\n\r[%08dms][C][E] SEND ERROR: %d",tm, resultCode);

	} else if(print){

		// Notify terminal: - - - - - - - - - - - - - - - - - - - - - - - - - - 
		pl;printf("\n\r[%08dms][C] Sent: \"%s\" "
				  "\n\r\t\tTo MMISO (%s, %d) (%d time(s))", 
			tm, length > 0? outgoing : "[SEND ERR]", 
			this->masterMISO.get_ip_address(), this->masterMISO.get_port(), 
			times);pu;
	}
	
	this->sendLock.unlock();

	// Return result code: - - - - - - - - - - - - - - - - - - - - - - - - - - -
	return resultCode;
	 	 
} // End Communicator::_send // // // // // // // // // // // // // // // // // 

int Communicator::_receive(char* specifier, char message[]){ // // // // // // 
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

	// Placeholders ============================================================
	char 	buffer[MAX_MESSAGE_LENGTH] = {0},
			*splitPointer = NULL,
			*splitPosition = NULL;

	int result = -1; 
	uint32_t index = 0;
	
	// NOTE: The following loop will either terminate successfully by reaching 
	// the return statement at the end of this loop or by an eventual timeout
	// or other network error (first case of if/else statement below)

	// Receive message =========================================================
	while(true){
		result = 
			this->slaveMOSI.recvfrom(
				&this->masterMOSI, buffer, MAX_MESSAGE_LENGTH);
		
		// Verify reception ====================================================
		if(result <= 0){
			// Timeout or connection error (leave connection error detection to
			// listener thread)
			*specifier = '\0';
			message[0] = '\0';
			return result;
		 
		} else { // Validate message ===========================================
			
			
			// Add NULL-termination character:
			buffer[result] = '\0';

			// Check index -----------------------------------------------------
			// Get index:
			splitPointer = strtok_r(buffer, "|", &splitPosition);
			if(splitPointer == NULL){
				// NULL index. Ignore message
				pl;printf("\n\r[%08dms][R] WARNING: NULL Index received", 
					tm);pu;
				continue;
	
			} else if ((index = uint32_t(atoi(splitPointer))) != 0 
				and index < this->mosiIndex){
				// Outdated message
				pl;printf("\n\r[%08dms][R] Old MSG Ignored (%lu)", 
					tm, index);pu;
				continue;

			} // End check index
			
			// NOTE: Index 0 is a special case (HSK)

			// Get specifier ---------------------------------------------------
			splitPointer = strtok_r(NULL, "|", &splitPosition);
			if(splitPointer == NULL){
				// NULL specifier. Ignore message
				pl;printf("\n\r[%08dms][R] WARNING: NULL Spec. received:"\
					"\n\r\t\t\"%s\"", tm, buffer);pu;
				continue;

			} else {
				// Non-NULL specifier. Store in placeholder:
				*specifier = splitPointer[0];

				// Check for zero index w/o HSK (not allowed)
				if(index == 0 and *specifier != 'H'){
					pl;printf("\n\r[%08dms][R] WARNING: Non-HSK 0 Index"\
					" received:\n\r\t\t%s", tm, buffer);pu;
					continue;	
				}
			}

			// Get message -----------------------------------------------------
			
			// NOTE: Use splitPosition instead in order to keep all separators
			// (Using strtok_r would get only one segment, while we want to
			// return the entirety of the message that is after the specifier.)

			if(strlen(splitPosition) == 0){
				// No message (acceptable for some specifiers)
				message[0] = '\0';
				

			} else {
				// Valid message to be stored:
				strcpy(message, splitPosition);
			}

			// Message approved. Modify MOSI index:
			this->mosiIndex = index;
			
			return result;

		} // End verify result
	} // End receive loop

} // End Communicator::_receive // // // // // // // // // // // // // // // // 

const char* Communicator::_interpret(int errorCode){
	/* Interpret a network error code and return its description.
	 * - PARAM int errorCode: negative error code received by some network'n
	 *	 instance, such as a TCPSocket.
	 * - RETURN: pointer to constant, NULL-terminated string of chars that
	 *	 describes the error, if a description is found.
	 */
	 
	switch(errorCode){
		

		case NSAPI_ERROR_OK:
			return "No error";
		
		case NSAPI_ERROR_WOULD_BLOCK:
			return "No data is available but call is non-blocking";
			
		case NSAPI_ERROR_UNSUPPORTED:
			return "Unsupported functionality";
		
		case NSAPI_ERROR_PARAMETER:
			return "Invalid configuration";
			
		case NSAPI_ERROR_NO_CONNECTION:
			return "Not connected to a network";
		
		case NSAPI_ERROR_NO_SOCKET:
			return "Socket not available for use";
		
		case NSAPI_ERROR_NO_ADDRESS:
			return "IP address is not known";
		
		case NSAPI_ERROR_NO_MEMORY:   
			return "Memory resource not available";
		
		case NSAPI_ERROR_NO_SSID:	  
			return "SSID not found";
		
		case NSAPI_ERROR_DNS_FAILURE:	  
			return "DNS failed to complete successfully";
		
		case NSAPI_ERROR_DHCP_FAILURE:	  
			return "DHCP failed to complete successfully";
		
		case NSAPI_ERROR_AUTH_FAILURE:	  
			return "Connection to access point failed";
		
		case NSAPI_ERROR_DEVICE_ERROR:	  
			return "Failure interfacing with the network processor";
		
		case NSAPI_ERROR_IN_PROGRESS:	  
			return "Operation (e.g. connect) in progress";
		
		case NSAPI_ERROR_ALREADY:	  
			return "Operation (e.g. connect) already in progress";
		
		case NSAPI_ERROR_IS_CONNECTED:	  
			return "Socket is already connected";
		
		default:
			return "Unknown error";
			
	} // End switch
			
	} // End Communicator::_interpret // // // // // // // // // // // // / // /

void Communicator::_setRed(int state){ // // // // // // // // // // // // // //
	/* ABOUT: Set state of red USR LED. To be used by _setStatus.
	 */

	switch(state){
		
		case L_TOGGLE:
			this->red = !this->red;
			this->xred = this->red;
			break;

		case L_ON:
			this->red = true;
			this->xred = true;
			break;

		case L_OFF:
			this->red = false;
			this->xred = false;
			break;
	}

} // End Communicator::_setRed // // // // // // // // // // // // // // // // /
	 
void Communicator::_setGreen(int state){ // // // // // // // // // // // // // 
	/* ABOUT: Set state of green USR LED. To be used by _setStatus.
	 */
	
	switch(state){
		
		case L_TOGGLE:
			this->green = !this->green;
			#ifndef JPL
			this->xgreen = this->green;
			#endif
			break;

		case L_ON:
			this->green = true;
			#ifndef JPL
			this->xgreen = true;
			#endif
			break;

		case L_OFF:
			this->green = false;
			#ifndef JPL
			this->xgreen = false;
			#endif
			break;

	}
} // End Communicator::_setGreen // // // // // // // // // // // // // // // //

void Communicator::_blinkRed(void){ // // // // // // // // // // // // // // //
	/* ABOUT: Blink red LED (alternate).
	 */

	this->red = !this->red;
	this->xred = !this->xred;

} // End Communicator::_blinkRed // // // // // // // // // // // // // // // //

void Communicator::_blinkGreen(void){ // // // // // // // // // // // // // //
	/* ABOUT: Blink green LED (alternate).
	 */

	this->green = !this->green;
	#ifndef JPL
	this->xgreen = !this->xgreen;
	#endif

} // End Communicator::_blinkGreen // // // // // // // // // // // // // // //

void Communicator::reboot(void){ // // // // // // // // // // // // // // // //
	/* ABOUT: Shut down the Processor module and reboot the MCU.
	 */
		
	// Set green:
	this->_setGreen(L_OFF);
	
	Ticker ledTicker, shutdownTicker;

	// Set red:
	ledTicker.attach(callback(this, &Communicator::_blinkRed),
		BLINK_FAST);

	// Set ticker to shutdown unconditionally in case of Processor crash:
	shutdownTicker.attach(&NVIC_SystemReset, 2);

	// Shut down Processor:
	this->processor.setStatus(OFF);

	// Reboot:
	NVIC_SystemReset();

} // End Communicator::reboot // // // // // // // // // // // // // // // // //
