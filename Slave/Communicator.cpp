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

//// DEPENDENCIES //////////////////////////////////////////////////////////////
#include "Communicator.h"
#include "mbed_stats.h"
//// CLASS INTERFACE ///////////////////////////////////////////////////////////

// CONSTRUCTORS AND DESTRUCTORS ------------------------------------------------

Communicator::Communicator(const char version[]):processor(),periodMS(TIMEOUT_MS),
	mosiIndex(0),misoIndex(0), masterTimeouts(0),
	listenerThread(osPriorityNormal,16 * 1024 /*16K stack size*/),
	misoThread(osPriorityNormal, 16 * 1024 /*32K stack size*/),
	mosiThread(osPriorityNormal, 16 * 1024 /*32K stack size*/),
	red(LED3), xred(D3), green(LED1), xgreen(D5)
	{ // // // // // // // // // // // // // // // // // // // // // // // // //
	/* ABOUT: Constructor for class Communicator. Starts networking threads.
	 * PARAMETERS:
	 * -Processor &processor: Reference to Processor instance. (See Proces-
	 *	sor.h)
	 */
	pl;printf("\n\r[%08dms][c] Initializing Communicator threads", tm);pu;
	this->_setStatus(INITIALIZING);

	strcpy(this->version, version);

	// Initialize ethernet interface - - - - - - - - - - - - - - - - - - - - - -
	int result = -1;
	unsigned int count = 1;

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
			this->_setStatus(NO_NETWORK);
			
		} // End if result < 0
		
	} // End ethernet loop .....................................................
	pl; printf("\n\r[%08dms][C] Ethernet initialized (%s) ",tm,
		ethernet.get_ip_address());pu;
	
	// Initialize sockets - - - - - - - - - - - - - - - - - - - - - - - - - - - 
	
	pl;
	printf("\n\r[%08dms][C] Initializing sockets", tm);
	pu;
	
	this->slaveMISO.open(&ethernet);
	this->slaveMISO.bind(SMISO);
	this->slaveMISO.set_timeout(TIMEOUT_MS);
	
	this->slaveMOSI.open(&ethernet);
	this->slaveMOSI.bind(SMOSI);
	this->slaveMOSI.set_timeout(-1); // Listen for commands w/o timeout
	
	this->slaveListener.open(&ethernet);
	this->slaveListener.bind(SLISTENER);
	this->slaveListener.set_timeout(TIMEOUT_MS);
	
	pl;
	printf("\n\r[%08dms][C] Sockets initialized",tm);
	pu;

	this->processor.start();
	
	this->_setStatus(NO_MASTER);
	pl;printf("\n\r[%08dms][C] Ready for messages",tm);pu;	
	
	// Start communications thread - - - - - - - - - - - - - - - - - - - - - - -
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
	pl;printf("\n\r[%08dms][L] Listener thread started", tm);pu;
	
	// Declare placeholders: - - - - - - - - - - - - - - - - - - - - - - - -
	char dataReceived[MAX_MESSAGE_LENGTH];

	while(true){ // Listener routine loop ======================================
		
		// Wait a certain time in accordance to current comm status: - - - - - -
		/*
		this->configurationLock.lock();
		Thread::wait(this->getStatus() == CONNECTED? 
			this->periodMS:
			TIMEOUT_MS);
	   
		this->configurationLock.unlock();
		*/
		Thread::wait(TIMEOUT_MS);
		// Receive data: - - - - - - - - - - - - - - - - - - - - - - - - - - - -
		int bytesReceived = this->slaveListener.recvfrom(
			&masterBroadcast,
			dataReceived,
			MAX_MESSAGE_LENGTH
			);
		
		// Validate reception of data = = = = = = = = = = = = = = = = = = = = = 
		if(bytesReceived == NSAPI_ERROR_WOULD_BLOCK){
			// Socket timed out. Increment and check timeout counters.

			// Increment corresponding timeout: - - - - - - - - - - - - - - - - 
			if(this->getStatus() == CONNECTED){
				// Connected to Master. Increment Master timeouts:
				this->_incrementTimeouts();
				// Check network status:
				nsapi_connection_status_t netStatus = 
					this->ethernet.get_connection_status();

				if(netStatus == NSAPI_STATUS_DISCONNECTED or
					netStatus == NSAPI_STATUS_ERROR_UNSUPPORTED){
					pl;printf("\n\r[%08dms][L] NETWORK ERROR. REBOOTING",tm);pu;
					
					// Set status to NO_NETWORK:
					this->_setStatus(NO_NETWORK);
				}
				// Check threshold:
				if(this->_getTimeouts() < MAX_MASTER_TIMEOUTS){
					// Still within threshold
					pl;printf("\n\r[%08dms][L] MT incremented (%d/%d)",
						tm, this->_getTimeouts(), MAX_MASTER_TIMEOUTS);pu;
				
				}else if (this->_getTimeouts() == MAX_MASTER_TIMEOUTS - 1){
					// Ping Master before timing out
					this->_send("|P");

				}else{
					// Past threshold:
					pl;printf("\n\r[%08dms][L] MT THRESHOLD (%d/%d)",
						tm, this->_getTimeouts(), MAX_MASTER_TIMEOUTS);pu;

					// Assume disconnection:
					this->_setStatus(NO_MASTER);

				} // End check threshold.
			}else{
				// Not connected to Master.
				
				// Check network status:
				nsapi_connection_status_t netStatus = 
					this->ethernet.get_connection_status();

				if(netStatus == NSAPI_STATUS_DISCONNECTED or
					netStatus == NSAPI_STATUS_ERROR_UNSUPPORTED){
					pl;printf("\n\r[%08dms][L] NETWORK ERROR. REBOOTING",tm);pu;
					
					// Set status to NO_NETWORK:
					this->_setStatus(NO_NETWORK);
				} else {
					pl;printf("\n\r[%08dms][L] Standing by...",tm);pu;
				
				}

			} // End if socket timeout

			// Restart loop:
			continue;

			// Done handling socket timeout - - - - - - - - - - - - - - - - - -		
		} else if (bytesReceived <= 0){
			// Unrecognized error code. Reboot.
			pl;printf(
				"\n\r[%08dms][C] UNRECOGNIZED NETWORK ERROR. WILL REBOOT: "
				"\n\r\t\"%s\""
				,tm, this->_interpret(bytesReceived));pu;

			// Reboot:
			this->_setStatus(NO_NETWORK);
		} else{
			// Positive code. A message was received.
			// A positive value indicates a message was received.
			
			// Format data:
			dataReceived[bytesReceived] = '\0';

			if(this->getStatus() != CONNECTED){
				// Print out this feedback only if there is no ongoing 
				// connection w/ Master

				pl;printf("\n\r[%08dms][L] Received: \"%s\""
						"\n\r				 From: (%s,%d)",tm,
					dataReceived, masterBroadcast.get_ip_address(), 
					masterBroadcast.get_port());pu;
			}

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
			} else {
				this->passcodeLock.lock();
				strcpy(this->passcode, splitPointer);
				this->passcodeLock.unlock();
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
					} else {
						this->masterListener.set_ip_address(
							this->masterBroadcast.get_ip_address()
						);
						this->masterListener.set_port(port);
					}
					
					// If disconnected, send standard reply
					if(this->getStatus() != CONNECTED){
						char reply[MAX_MESSAGE_LENGTH];

						this->passcodeLock.lock();
						int n = snprintf(reply, 256, "A|%s|%s|N|%d|%d|%s", 
							this->passcode,
							this->ethernet.get_mac_address(),
							SMISO, 
							SMOSI,
							this->version);
						this->passcodeLock.unlock();

						this->listenerSocketLock.lock();
						this->slaveListener.sendto(
							masterListener, reply, n);
						pl;printf("\n\r[%08dms][L] Broadcast validated. "\
							"Reply sent to %s, %d", tm,
							masterListener.get_ip_address(),
							masterListener.get_port());pu;
						this->listenerSocketLock.unlock();

					} // End reply if disconnected
					
					// Store IP addres

					break;
				} // End STD BCAST

				case 'U': { // UPDATE BCAST. Reboot
					pl;printf("\n\r[%08dms][L] Update command received. "\
						"Rebooting", tm);pu;
				
					this->_setStatus(NO_NETWORK);
					break;
				} // End UPDATE BCAST

				case 'R': { // SHUTDOWN BCAST. Reboot
					pl;printf("\n\r[%08dms][L] Shutdown command received. "\
						"Rebooting", tm);pu;
				
					this->_setStatus(NO_NETWORK);
					break;
				} // End SHUTDOWN BCAST

				case 'L': { // LAUNCH BCAST. Ignore
					if(this->getStatus() != CONNECTED){
						pl;printf("\n\r[%08dms][L] \"Launch\" command ignored",
							tm);pu;	
					}
					break;
				} // End LAUNCH BCAST

				default: { // Unrecognized broadcast specifier
					pl;printf("\n\r[%08dms][L] Unrecognized BC code \"%c\""\
						" ignored",
						tm, specifier);pu;	
				}

			} // End switch specifier
			
		} // End reception validation = = = = = = = = = = = = = = = = = = = = = 
	}// End listener routine loop ==============================================
} // End Communicator::_listenerRoutine // // // // // // // // // // // // // /
   
void Communicator::_misoRoutine(void){ // // // // // // // // // // // // // //
	// ABOUT: Send periodic updates to Master once connected.

	// Thread setup ============================================================
	pl;printf("\n\r[%08dms][O] MISO thread started",tm);pu;

	// Initialize placeholders -------------------------------------------------
	unsigned int misoPeriodMS = 1; // Time between cycles
	char processed[MAX_MESSAGE_LENGTH] = {0}; // Feedback to be sent to Master 

	processed[0] = 'M';
	// Thread loop =============================================================
	while(true){
		
		// Check status = = = = = = = = = = = = = = = = = = = = = = = = = = = = 
		if(this->getStatus() == CONNECTED){
			// Connected. Send update to Master.

			// Fetch message to send -------------------------------------------
			this->processor.get(processed);
			
			// Send message ----------------------------------------------------
			this->_send(processed, 1);

		} else { // = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = 
			// Not connected. Nothing to send.

		} // End check status = = = = = = = = = = = = = = = = = = = = = = = = = 

		// Wait period ---------------------------------------------------------

		// Fetch latest value:
		this->periodLock.lock();
		misoPeriodMS = this->periodMS;
		this->periodLock.unlock();

		// Wait:
		Thread::wait(misoPeriodMS);
		


		// (Restart loop)

	} // End MISO loop =========================================================
} // End Communicator::_misoRoutine // // // // // // // // // // // // // // //

void Communicator::_mosiRoutine(void){ // // // // // // // // // // // // // //
	// ABOUT: Listen for commands from Master.

	// Thread setup ============================================================
	pl;printf("\n\r[%08dms][I] MOSI thread started",tm);pu;

	// Prepare placeholders ----------------------------------------------------

	// Communications:
	char buffer[MAX_MESSAGE_LENGTH] = {0};
	char errorBuffer[MAX_MESSAGE_LENGTH] = {0};
	char specifier = '\0';
	char *splitPointer = NULL;
	char *savePointer = NULL;

	// Handshake:
	int parsedMISOPort = 0;
	int parsedMOSIPort = 0;
	int parsedPeriodMS = 0;
	int parsedMaxMasterTimeouts = 0;

	// Thread loop =============================================================
	while(true){

		// Wait for message ----------------------------------------------------
		int result = this->_receive(&specifier, buffer);

		// Verify reception = = = = = = = = = = = = = = = = = = = = = = = = = = 
		if(result <= 0){
			// Error. Discard message. (Error will be printed by _receive)
			continue;
		
		} else if(this->getStatus() == CONNECTED) {
			
			// A message was received. Validate its content.
			switch(specifier){
				
				case 'S':{ // STANDARD
			
					// Verify nonempty message:
					if(buffer[0] == '\0'){
						pl;printf(
							"\n\r[%08dms][I][E] WARNING: EMPTY MESSAGE ON 'S'",
							tm);pu;
						this->_sendError("E|Empty 'S' message received");
					}
					
					// Pass message to Processor:
					this->processor.process(buffer);
					break;
				}
					
				case 'H':{ // HANDSHAKE
					pl;printf(
						"\n\r[%08dms][I][E] WARNING: HSK while connected", tm);pu;
					this->_sendError("E|HSK while connected");

					break;
				}
				case 'X':{ // DISCONNECT
					
					pl;printf(
						"\n\r[%08dms][I] Disconnect message received.", tm);pu;
					
					this->_setStatus(NO_MASTER);
					break;
				}
					
				case 'Z':{ // REBOOT
					pl;printf(
						"\n\r[%08dms][I] Reboot message received."\
							" Rebooting", tm);pu;

					this->_setStatus(NO_NETWORK);
					break;
				}
					
				case 'I':{ // INDEX
					pl;printf(
						"\n\r[%08dms][I] Resetting MOSI index" , tm);pu;
					this->_resetMOSIIndex();
					
					break;
				}
					
				case 'P':{ // PING
					pl;printf(
						"\n\r[%08dms][I] Ping message received" , tm);pu;
					this->_resetTimeouts();

					break;
				}
					
				default:{
					pl;printf(
						"\n\r[%08dms][I][E] WARNING: UNRECOGNIZED CODE \'%c\'",
						tm, specifier);pu;
					snprintf(errorBuffer, MAX_MESSAGE_LENGTH,
						"E|Unrecognized code '%c'", specifier);
					this->_sendError(errorBuffer);
				
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
				}
			 
				// Get network-related configuration
				// Here the buffer is expected to be formatted as 
				//
				//		 MISOP,MOSIP,PERIODMS,MAXT|ARRAY_CONFIG
				//					
				//
				
				// MISO Port
				
				/* DEBUG
				pl;printf(
					"\n\r[%08dms][I] HSK: %s",
					tm, buffer);pu;

				splitPointer = strtok_r(buffer, ",", &savePointer);
				pl;printf(
					"\n\r[%08dms][I] split: %s\n\r\tsave:%s",
					tm, splitPointer, savePointer);pu;

				*/

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
				
				/* DEBUG
				pl;printf(
					"\n\r[%08dms][I] parsedMISOPort: %d",
					tm, parsedMISOPort);pu;
				*/

				// MOSI Port
				splitPointer = strtok_r(NULL, ",", &savePointer);
				
				/* DEBUG
				pl;printf(
					"\n\r[%08dms][I] split: %s\n\r\tsave:%s",
					tm, splitPointer, savePointer);pu;
				*/
				
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
				
				/* DEBUG
				pl;printf(
					"\n\r[%08dms][I] parsedMOSIPort: %d",
					tm, parsedMOSIPort);pu;
				pl;printf(
					"\n\r[%08dms][I] split: %s\n\r\tsave:%s",
					tm, splitPointer, savePointer);pu;

				*/

				// Period
				splitPointer = strtok_r(NULL, ",", &savePointer);
				
				/* DEBUG
				pl;printf(
					"\n\r[%08dms][I] split: %s\n\r\tsave:%s",
					tm, splitPointer, savePointer);pu;
				*/

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
				
				/* DEBUG
				pl;printf(
					"\n\r[%08dms][I] parsedPeriodMS: %d",
					tm, parsedPeriodMS);pu;
				*/

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
				
				/* DEBUG
				pl;printf(
					"\n\r[%08dms][I] parsedMaxMasterTimeouts: %d",
					tm, parsedMaxMasterTimeouts);pu;

				*/

				// Processor
				
				// Send Processor-related configuration
				// 	NOTE: COPY IN PROCESSOR
				
				splitPointer = strtok_r(NULL, "|", &savePointer);
				
				/* DEBUG
				pl;printf(
					"\n\r[%08dms][I] parsedMOSIPort: %d",
					tm, parsedMOSIPort);pu;
				pl;printf(
					"\n\r[%08dms][I] split: %s\n\r\tsave:%s",
					tm, splitPointer, savePointer);pu;
				*/

				if(splitPointer == NULL){
					pl;printf(
						"\n\r[%08dms][I][E] NULL PERIOD IN HSK",
						tm);pu;
					continue; // Discard HSK
				}
				bool processorSuccess = this->processor.process(splitPointer);
				
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
					
					// Apply configuration
					this->sendLock.lock();
					this->receiveLock.lock();
					this->masterMISO.set_port(parsedMISOPort);
					this->masterMISO.set_ip_address(
						this->masterMOSI.get_ip_address());

					this->receiveLock.unlock();
					this->sendLock.unlock();
					
					this->periodLock.lock();
					this->periodMS = parsedPeriodMS;
					this->periodLock.unlock();

					this->maxMasterTimeoutsLock.lock();
					this->maxMasterTimeouts = parsedMaxMasterTimeouts;
					this->maxMasterTimeoutsLock.unlock();
				
					// Send handshake acknowledgement
					this->_send("H", 1, true);

					// Update status:
					this->_setStatus(CONNECTED);
				
				} else {

					// HSK error at processor
					this->_sendError("E|Bad HSK at Processor");
					this->_setStatus(NO_MASTER);
				} // End check processor success
		
		} else {
			
			pl;printf(
				"\n\r[%08dms][I][E] WARNING: Could not classify message",
				tm);pu;
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
	this->_incrementMISOIndex();
	
	// Format message: - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	length = sprintf(outgoing, "%lu|%s", this->_getMISOIndex(), message); 
	
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
				  "\n\r				   To MMISO (%s, %d) (%d times)", 
			tm, length > 0? outgoing : "[SEND ERR]", 
			this->masterMISO.get_ip_address(), this->masterMISO.get_port(), 
			times);pu;
	}
	
	this->sendLock.unlock();

	// Return result code: - - - - - - - - - - - - - - - - - - - - - - - - - - -
	return resultCode;
	 	 
} // End Communicator::_send // // // // // // // // // // // // // // // // // 

int Communicator::_sendError(const char* message){ // // // // // // // // // // /
	/* ABOUT: Send an error message to Master, if possible. This function will
	 * try to use either the MISO-side _send function 
	 * (if there is a connection) or the listener thread's socket.
	 * PARAMETERS:
	 * - const char* message: NULL-terminated message to send.
	 * RETURN: int; number of bytes received upon success, negative error code
	 * on failure.
	 * NOTE: Blocks for thread-safety.
	 */

	// Check connection status
	if (this->getStatus() == CONNECTED){
		// Use standard _send function
		return this->_send(message);
	
	} else {
		// Use listenerSocket 
		int result = 0;
		char buffer[MAX_MESSAGE_LENGTH] = {0};
		this->passcodeLock.lock();
		snprintf(buffer, MAX_MESSAGE_LENGTH, "A|%s|%s|E|%s",
			this->passcode, this->ethernet.get_mac_address(),
			message);
		this->passcodeLock.unlock();

		this->listenerSocketLock.lock();
		result = this->slaveListener.sendto(
			this->masterListener, message, strlen(message));
		this->listenerSocketLock.unlock();

		return result;
	}

} // End Communicator::_sendError // // // // // // // // // // // // // // // /

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
				and index < this->_getMOSIIndex()){
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
			this->_setMOSIIndex(index);
			return result;

		} // End verify result
	} // End receive loop

} // End Communicator::_receive // // // // // // // // // // // // // // // // 
	
void Communicator::_setStatus(const int newStatus){ // // // // // // // // // /
	// ABOUT: Set the current connection status, which will be displayed to
	// The user using the MCU's LED's and used for multithread coordination.
	
	static	Ticker statusTicker; // For LED blinking
  
	// Acquire lock: 
	this->statusLock.lock();
 
	// Check current status for redundance: ------------------------------------
	if(this->status == newStatus){
		// Do nothing if the status modification is redundant:
		return;
	}else{ // Otherwise, update the status accordingly:
		// Reset timeout counters when changing status:
		this->_resetTimeouts();
	
		switch(newStatus){ // - - - - - - - - - - - - - - - - - - - - - - - - - 
			
			case NO_MASTER: // ..................................................
				// Reset exchange index:
				this->_resetMOSIIndex();
				this->_resetMISOIndex();
			
				// Set green:
				statusTicker.attach(callback(this, &Communicator::_blinkGreen),
					BLINK_SLOW);
				// Set red:
				this->_setRed(L_ON);
		
				// Shut down Processor:
				this->processor.setStatus(OFF);
		
				// Notify user:
				pl;printf("\n\r[%08dms][S] Status: NO_MASTER",tm);pu;
			
				
				// Exit switch:
				break;
			
			case CONNECTING: // ................................................
				// Do not reset exchange index
			
				// Set green:
				statusTicker.attach(callback(this, &Communicator::_blinkGreen),
					BLINK_SLOW);
				// Set red:
				this->_setRed(L_ON);
				
				
				// Notify user:
				pl;printf("\n\r[%08dms][S] Status: CONNECTING",tm);pu;
				
				// Exit switch:
				break;
			
			case CONNECTED: // .................................................
				
				// No blinking:
				statusTicker.detach();
				
				// Set green:
				this->_setGreen(L_ON);
				this->_setRed(L_OFF);
				
				
				// Notify user:
				pl;printf("\n\r[%08dms][S] Status: CONNECTED", tm);pu;
				
				// Activate processor:
				this->processor.setStatus(ACTIVE);
				
				// Exit switch:
				break;
							 
			case NO_NETWORK: // ................................................
				// Reset exchange index:
				this->_resetMOSIIndex();
				this->_resetMISOIndex();
			
				// Set green:
				this->_setGreen(L_OFF);
				
				// Set red:
				statusTicker.attach(callback(this, &Communicator::_blinkRed),
					BLINK_FAST);
		
				// Shut down Processor:
				this->processor.setStatus(L_OFF);	
					
				// Notify user:
				pl;printf("\n\r[%08dms][S] Status: NO_NETWORK", tm);pu;    
			   
				pl;printf("\n\r[%08dms][S][REDN] Status: NO_NETWORK", tm);pu;	 
				// Give system time to print:
				wait_ms(1);

				// Reboot:
				NVIC_SystemReset();

				// Exit switch
				break;
				
			case INITIALIZING: // ..............................................
				// Reset exchange index:
				this->_resetMOSIIndex();
				this->_resetMISOIndex();
			
				// No blinking:
				statusTicker.detach();
				
				// Set green:
				this->_setGreen(L_OFF);
				this->_setRed(L_ON);
			
				   
				// Notify user:
				pl;printf("\n\r[%08dms][S] Status: INITIALIZING", tm);pu;	
				
				// Exit switch: 
				break;
			
			default: // ........................................................
				// Input not recognized. Issue error message:
				pl;printf("\n\r[%08dms][S] WARNING:"
					" Invalid status code given (%d)", tm, newStatus);pu;
					
				// Return control without changing status:
				return;
				
			
		} // End switch newStatus  - - - - - - - - - - - - - - - - - - - - - - -
		
	// Update status variable: - - - - - - - - - - - - - - - - - - - - - - - - -
	this->status = newStatus;
	
	} // End check status ------------------------------------------------------
	
	// Release status lock:
	this->statusLock.unlock();

	// Return control: ---------------------------------------------------------
	return;
	  
	} // End Communicator::_setStatus // // // // // // // // // // // // // // // /

int Communicator::getStatus(void){

		// Acquire lock:
		this->statusLock.lock();

		// Store value in placeholder to release lock before returning:
		int8_t status = this->status;

		// Release lock:
		this->statusLock.unlock();

		// Return fetched value
		return status;

		// NOTE: "Look-then-leap" risk of status changing between unlock and 
		// return?
		
	} // End Communicator::getStatus // // // // // // // // // // // // // // /

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

void Communicator::_resetTimeouts(void){ // // // // // // // // // // // // // 
	/* ABOUT: Reset Master timeout counter to 0.
	 * NOTE: Blocks for thread safety.
	 */

	this->timeoutLock.lock();
	this->masterTimeouts = 0;
	this->timeoutLock.unlock();

} // Communicator::_resetTimeouts // // // // // // // // // // // // // // // /

void Communicator::_incrementTimeouts(void){ // // // // // // // // // // // //
	/* ABOUT: Increase Master timeout counter by 1.
	 * NOTE: Blocks for thread safety.
	 */

	this->timeoutLock.lock();
	this->masterTimeouts++;
	this->timeoutLock.unlock();

} // Communicator::_increaseTimeouts // // // // // // // // // // // // // // /

int Communicator::_getTimeouts(void){ // // // // // // // // // // // // // // 
	/* ABOUT: Get value of Master timeout counter.
	 * NOTE: Blocks for thread safety.
	 */

	int value = 0;
	this->timeoutLock.lock();
	value =	this->masterTimeouts;
	this->timeoutLock.unlock();
	
	return value;

} // Communicator::_getTimeouts // // // // // // // // // // // // // // // // 

void Communicator::_resetMISOIndex(void){ // // // // // // // // // // // // // 
	/* ABOUT: Reset  MISO index to 1.
	 * NOTE: Blocks for thread safety.
	 */

	this->misoIndexLock.lock();
	this->misoIndex = 1;
	this->misoIndexLock.unlock();

} // Communicator::_resetMISOIndex // // // // // // // // // // // // // // // 

void Communicator::_incrementMISOIndex(void){ // // // // // // // // // // // /
	/* ABOUT: Increase  MISO index by 1.
	 * NOTE: Blocks for thread safety.
	 */

	this->misoIndexLock.lock();
	this->misoIndex++;
	this->misoIndexLock.unlock();

} // Communicator::_increaseMISOIndex // // // // // // // // // // // // // // 

uint32_t Communicator::_getMISOIndex(void){ // // // // // // // // // // // // 
	/* ABOUT: Get value of  MISO index.
	 * NOTE: Blocks for thread safety.
	 */

	uint32_t value = 0;
	this->misoIndexLock.lock();
	value =	this->misoIndex;
	this->misoIndexLock.unlock();
	
	return value;

} // Communicator::_getMISOIndex // // // // // // // // // // // // // // // // 

void Communicator::_resetMOSIIndex(void){ // // // // // // // // // // // // // 
	/* ABOUT: Reset  MOSI index to 1.
	 * NOTE: Blocks for thread safety.
	 */

	this->mosiIndexLock.lock();
	this->mosiIndex = 1;
	this->mosiIndexLock.unlock();

} // Communicator::_resetMOSIIndex // // // // // // // // // // // // // // // 

void Communicator::_incrementMOSIIndex(void){ // // // // // // // // // // // /
	/* ABOUT: Increase  MOSI index by 1.
	 * NOTE: Blocks for thread safety.
	 */

	this->mosiIndexLock.lock();
	this->mosiIndex++;
	this->mosiIndexLock.unlock();

} // Communicator::_increaseMOSIIndex // // // // // // // // // // // // // // 

uint32_t Communicator::_getMOSIIndex(void){ // // // // // // // // // // // // 
	/* ABOUT: Get value of  MOSI index.
	 * NOTE: Blocks for thread safety.
	 */

	uint32_t value = 0;
	this->mosiIndexLock.lock();
	value =	this->mosiIndex;
	this->mosiIndexLock.unlock();
	
	return value;

} // Communicator::_getMOSIIndex // // // // // // // // // // // // // // // // 

void Communicator::_setMOSIIndex(uint32_t newIndex){ // // // // // // // // // 
	/* ABOUT: Set value of  MOSI index.
	 * NOTE: Blocks for thread safety.
	 */

	this->mosiIndexLock.lock();
	this->mosiIndex = newIndex;
	this->mosiIndexLock.unlock();

} // Communicator::_increaseMOSIIndex // // // // // // // // // // // // // // 

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
			this->xgreen = this->green;
			break;

		case L_ON:
			this->green = true;
			this->xgreen = true;
			break;

		case L_OFF:
			this->green = false;
			this->xgreen = false;
			break;

	}
} // End Communicator::_setGreen // // // // // // // // // // // // // // // //

void Communicator::_blinkRed(void){ // // // // // // // // // // // // // // //
	/* ABOUT: Blink red LED (alternate).
	 */

	this->red = !this->red;
	this->xred = !this->xred;

} // End Communicator::_blinkRed // // // // // // // // // // // // // // // //

void Communicator::_blinkGreen(void){ // // // // // // // // // // // // // // //
	/* ABOUT: Blink green LED (alternate).
	 */

	this->green = !this->green;
	this->xgreen = !this->xgreen;

} // End Communicator::_blinkGreen // // // // // // // // // // // // // // // //
