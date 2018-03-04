////////////////////////////////////////////////////////////////////////////////
// Project: Fanclub Mark II "Slave" // File: Communicator.cpp - Implementation//
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

//// ABOUT /////////////////////////////////////////////////////////////////////
// This module handles communications to Master throug ethernet.              //
////////////////////////////////////////////////////////////////////////////////

//// DEPENDENCIES //////////////////////////////////////////////////////////////
#include "Communicator.h"

//// CLASS INTERFACE ///////////////////////////////////////////////////////////

// CONSTRUCTORS AND DESTRUCTORS ------------------------------------------------

Communicator::Communicator():processor(),periodMS(TIMEOUT_MS),
    exchangeIndex(0),networkTimeouts(0),masterTimeouts(0),
    listenerThread(osPriorityNormal, 16 * 1024 /*16K stack size*/),
    misoThread(osPriorityNormal, 32 * 1024 /*32K stack size*/),
    mosiThread(osPriorityNormal, 32 * 1024 /*32K stack size*/),
    red(LED3), green(LED1)
    { // // // // // // // // // // // // // // // // // // // // // // // // //
    /* ABOUT: Constructor for class Communicator. Starts networking threads.
     * PARAMETERS:
     * -Processor &processor: Reference to Processor instance. (See Proces-
     *  sor.h)
     */
    pl;printf("\n\r[%08dms][c] Initializing Communicator threads", tm);pu;
    this->_setStatus(INITIALIZING);

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
    char dataReceived[256], password[16] = {'\0'};
    int masterListenerPort = -1;

    while(true){ // Listener routine loop ======================================
        
        // Wait standard timeout time to allow other threads to act: - - - - - -
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
            if(this->status == CONNECTED){
                // Connected to Master. Increment Master timeouts:
                this->masterTimeouts++;

                // Check threshold:
                if(this->masterTimeouts < MAX_MASTER_TIMEOUTS){
                    // Still within threshold
                    pl;printf("\n\r[%08dms][L] MT incremented (%d/%d)",
                        tm, this->masterTimeouts, MAX_MASTER_TIMEOUTS);pu;

                }else{
                    // Past threshold:
                    pl;printf("\n\r[%08dms][L] MT THRESHOLD (%d/%d)",
                        tm, this->masterTimeouts, MAX_MASTER_TIMEOUTS);pu;

                    // Assume disconnection:
                    this->_setStatus(NO_MASTER);

                } // End check threshold.
            }else{
                // Not connected to Master. Increment network timeouts:
                this->networkTimeouts++;

                // Check threshold:
                if(this->networkTimeouts < MAX_NETWORK_TIMEOUTS){
                    // Still within threshold
                    pl;printf("\n\r[%08dms][L] NT incremented (%d/%d)",
                        tm, this->networkTimeouts, MAX_NETWORK_TIMEOUTS);pu;

                }else{
                    // Past network timeout threshold:
                    pl;printf("\n\r[%08dms][L] NT THRESHOLD (%d/%d) REBOOTING",
                        tm, this->networkTimeouts, MAX_NETWORK_TIMEOUTS);pu;
                    
                    // Arbitrary wait for printing to finish:
                    wait_ms(1);

                    // Reboot:
                    NVIC_SystemReset();
                    
                } // End check threshold.
            } 

            // Restart loop:
            continue;

            // Done handling socket timeout - - - - - - - - - - - - - - - - - -     
        } else if (bytesReceived <= 0){
            // Unrecognized error code. Reboot.
            pl;printf(
                "\n\r[%08dms][C] UNRECOGNIZED NETWORK ERROR. WILL REBOOT: "
                "\n\r\t\"%s\""
                ,tm, this->_interpret(bytesReceived));pu;

            // Arbitrary wait for printing to finish:
            wait_ms(1);

            // Reboot:
            NVIC_SystemReset();
        } else{
            // Positive code. A message was received.
            // A positive value indicates a message was received.
            
            // Format data:
            dataReceived[bytesReceived] = '\0';
            pl;printf("\n\r[%08dms][L] Received: \"%s\""
                      "\n\r                From: (%s,%d)",tm,
                dataReceived, masterBroadcast.get_ip_address(), 
                masterBroadcast.get_port());pu;

            // Validate data received: - - - - - - - - - - - - - - - - - - - - -
            sl;
            strtok(dataReceived, "|");
            strcpy(password, strtok(NULL, "|"));
            masterListenerPort = atoi(strtok(NULL, "|"));
            su;
            pl;printf("\n\r[%08dms][L] Parsing:"
                      "\n\r                Master LPort: %d"
                      "\n\r                Password: \"%s\"", 
                      tm, masterListenerPort, password);pu;
            
            if(masterListenerPort > 0 and strcmp(password, PASSWORD) == 0){
                // If the message received represents a general broadcast,
                // send corresponding reply: - - - - - - - - - - - - - - - - - -
                
                pl;printf("\n\r[%08dms][L] General broadcast validated. "
                            "Sending reply",tm);pu;
                
                // Configure listener address:..................................
                this->masterListener.set_ip_address(
                    masterBroadcast.get_ip_address());
                
                this->masterListener.set_port(masterListenerPort);
                
                // Send reply:..................................................
                char reply[256];
                sprintf(reply, "00000000|%s|%s|%d|%d", 
                    password,this->ethernet.get_mac_address(),SMISO, SMOSI);
                    
                this->slaveListener.sendto(
                    masterListener, reply, strlen(reply));
            
                pl; printf("\n\r[%08dms][L] Sent: %s"
                           "\n\r                To (%s, %d)",tm,
                    reply, masterListener.get_ip_address(), 
                    masterListenerPort);pu;
                    
                // Blink green LED: - - - - - - - - - - - - - - - - - - - - - - 
                for(int i = 0; i < (this->status == CONNECTED? 0:1); i++){
                    this->green = !this->green;
                    Thread::wait(0.050);
                    this->green = !this->green;
                } // End blink green LED - - - - - - - - - - - - - - - - - - - -
                
            }else{
                // If the message received represents neither a general bcast
                // nor a specific broadcast, discard it and restart:
                
                pl; printf("\n\r[%08dms][L] Message invalid. Discarded", tm);pu;
                continue;
                
            }// end data validation - - - - - - - - - - - - - - - - - - - - - - 
        } // End reception validation = = = = = = = = = = = = = = = = = = = = = 
    }// End listener routine loop ==============================================
    } // End Communicator::_listenerRoutine // // // // // // // // // // // // 
   
void Communicator::_misoRoutine(void){ // // // // // // // // // // // // // //
    // ABOUT: Send periodic updates to Master once connected.

    // Thread setup ============================================================
    pl;printf("\n\r[%08dms][O] MISO thread started",tm);pu;

    // Initialize placeholders -------------------------------------------------
    unsigned int misoPeriodMS = 1; // Time between cycles
    char processed[MAX_MESSAGE_LENGTH]; // Feedback to be sent back to Master 

    // Thread loop =============================================================
    while(true){
        // Check status = = = = = = = = = = = = = = = = = = = = = = = = = = = = 
        if(this->status == CONNECTED){
            // Connected. Send update to Master.

            // [TODO: Error-checking queue]

            // Fetch message to send -------------------------------------------
            this->processor.get(processed);
            
            // Send message ----------------------------------------------------
            this->_send(processed, 2);

        } else { // = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = 
            // Not connected. Nothing to send.

        } // End check status = = = = = = = = = = = = = = = = = = = = = = = = = 

        // Wait period ---------------------------------------------------------

        // Fetch latest value:
        this->configurationLock.lock();
        misoPeriodMS = this->periodMS;
        this->configurationLock.unlock();

        // Wait:
        Thread::wait(misoPeriodMS);

        // (Restart loop)

    } // End MISO loop =========================================================
    } // End Communicator::_misoRoutine // // // // // // // // // // // // // /

void Communicator::_mosiRoutine(void){ // // // // // // // // // // // // // //
    // ABOUT: Listen for commands from Master.

    // Thread setup ============================================================
    pl;printf("\n\r[%08dms][I] MOSI thread started",tm);pu;

    // Prepare placeholders ----------------------------------------------------
    int receivedExchange = 0;  // Exchange index of a received message
    char receivedKeyword[64];  // Keyword of a received message
    char receivedCommand[MAX_MESSAGE_LENGTH]; // Possible command in a message

    this->exchangeIndex = 0;
    // Thread loop =============================================================
    while(true){

        // Wait for message ----------------------------------------------------
        int result = this->_receive(&(this->exchangeIndex), 
            &receivedExchange, receivedKeyword, receivedCommand);

        // Verify reception = = = = = = = = = = = = = = = = = = = = = = = = = = 
        if(result <= 0){
            // Error. Discard message. (Error will be reported by _receive)
            continue;

        }else{
            // A message was received. Validate its content.

            // Check message contents -----------------------------------------
            if(!strcmp(receivedKeyword, "MHSK")){
                // Handshake message w/ configuration parameters.
                pl;printf("\n\r[%08dms][C] HSK received. Updating sockets",tm);pu;

                // Update status to stop broadcast:
                this->_setStatus(CONNECTING);

                // Update sockets: .................................................

                // Get configuration lock:
                this->configurationLock.lock();

                // Get values: . . . . . . . . . . . . . . . . . . . . . . . . . . .
                char *ptr = NULL;
                int port, periodms;
                sl;
                ptr = strtok(receivedCommand, ",");
                pl;printf("\n\r[%08dms][C] First item: %s",tm, ptr);pu;

                // Get Master MISO port:
                if(ptr != NULL and (port = atoi(ptr)) > 0){
                    this->masterMISO.set_port(port);

                    // Set Master IP on MISO (from MOSI):
                    this->masterMISO.set_ip_address(
                        this->masterMOSI.get_ip_address());
                        
                    pl;printf("\n\r[%08dms][C] Master MISO set to: %s on %d",
                    tm, masterMISO.get_ip_address(), port);pu;
                }else{
                    // Bad Master MISO:
                    pl;printf(
                        "\n\r[%08dms][C] HS1 ERROR. Bad master MISO: %d(-1 if NULL)"
                        ,tm, ptr == NULL? -1:port);pu;

                    // Discard progress and restart:
                    this->_setStatus(NO_MASTER);

                    // Release configuration lock:
                    this->configurationLock.unlock();

                    // Restart loop:
                    su;continue;
                }

                // Skip Master MOSI port:
                ptr = strtok(NULL, ",");
                pl;printf("\n\r[%08dms][C] Second item: %s",tm, ptr);pu;
                
                ptr = strtok(NULL, ",");
                pl;printf("\n\r[%08dms][C] Third item: %s",tm, ptr);pu;

                // Get period:
                if(ptr != NULL and (periodms = atoi(ptr)) > 0){
                    
                    pl;printf("\n\r[%08dms][C] Timeout set to: %dms",
                        tm, periodms);pu;

                }else{
                    // Bad timeout:
                    pl;printf(
                        "\n\r[%08dms][C] HS1 ERROR. Bad period: %d(-1 if NULL)"
                        ,tm, ptr == NULL? -1:periodms);pu;

                    // Discard progress and restart:
                    this->_setStatus(NO_MASTER);

                    // Release configuration lock:
                    this->configurationLock.unlock();

                    // Restart loop:
                    su;continue;
                }

                // Get fan array configuration for Processor:
                ptr = strtok(NULL, ",");
                pl;printf("\n\r[%08dms][C] Fourth item: %s",tm, ptr);pu;

                // Verify:
                if(ptr == NULL){
                    // Error while splitting.
                    pl;printf(
                        "\n\r[%08dms][C] HS2 ERROR. NULL configuration."
                        ,tm);pu;

                    // Discard progress and restart:
                    this->_setStatus(NO_MASTER);

                    // Release configuration lock:
                    this->configurationLock.unlock();

                    // Restart loop:
                    su;continue;

                }
                su;
                // Send command to processor: ..................................
                bool success = this->processor.process(ptr);

                // Check success: ..............................................
                if(not success){
                    // If there was a failure in the configuration, terminate 
                    // the attempt:
                    pl;printf(
                        "\n\r[%08dms][C] HS2 error at processor. "
                        "Handshake aborted",tm);pu;

                }else{
                    // Success. 

                    // Send reply to master:
                    this->_send("SHSK", 5); // Send reply

                    pl;printf(
                        "\n\r[%08dms][C] HSK Success",tm);pu;

                    // Update status and move on:
                    this->_setStatus(CONNECTED);

                    // Release configuration lock:
                    this->configurationLock.unlock();

                    // Restart loop:
                    continue;

                    } // End check success .....................................

            }else if(this->status == CONNECTED and // - - - - - - - - - - - - - 
                !strcmp(receivedKeyword, "MVER")){

                // Verification message. Not compatible w/ this version.
                pl;printf(
                    "\n\r[%08dms][C] WARNING: MVER obsolete",tm);pu;

            }else if(this->status == CONNECTED and // - - - - - - - - - - - - - 
                !strcmp(receivedKeyword, "MSTD")){
                // Standard command message. Send command to Processor.

                pl;printf(
                    "\n\r[%08dms][C] MSTD. Command: %s",tm, receivedCommand);pu;

                // Send command to Processor:
                this->processor.process(receivedCommand);

            }else if(this->status == CONNECTED and // - - - - - - - - - - - - - 
                !strcmp(receivedKeyword, "MRIP")){

                pl;printf(
                    "\n\r[%08dms][C] Connection terminated by Master",tm);pu;

                // Terminate connection:
                this->_setStatus(NO_MASTER);

            }else{ // - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
                // Unrecognized message (or command received while disconnected)
                pl;printf(
                    "\n\r[%08dms][C] WARNING: Keyword unrecognized or non-HSK"
                    " before setup",tm);pu;

                // Reset index if waiting for HSK:
                if(this->status == NO_MASTER){
                    this->exchangeIndex = 0;
                } // End reset index

            }// End check message ----------------------------------------------

        } // End verify reception = = = = = = = = = = = = = = = = = = = = = = = 

        // (Restart loop)

    } // End MOSI loop =========================================================
    } // End Communicator::_mosiRoutine // // // // // // // // // // // // // /

int Communicator::_send(const char* message, int times){ // // // // // // // //
    /* ABOUT: Send a message to the known Master MISO socket using the Slave
     *  MISO socket. The currently stored exchange index will be added automati-
     *  cally, along with its following delimiter ("INDEX|" e.g "00000001|").
     * PARAMETERS:
     * -const char* message: NULL-terminated char-array containing message 
     *  to be sent.
     * -int times: number of times to send a message, (for good measure)
     *  defaults to 1.
     * RETURN: Int; number of bytes sent upon success, negative socket error
     *  code on failure. If repetition is requested, the result of the last mes-
     *  sage is returned.
     * WARNING: This private member function assumes (1) the Slave's MISO 
     *  socket is ready to send messages and (2) the message given ends in
     *  '\0'.
     */
    
    static char outgoing[MAX_MESSAGE_LENGTH];
    static int length;
    static int resultCode;

    // Increment MISO index:
    this->misoIndex++;
    
    // Format message: - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    length = sprintf(outgoing, "%d|%s", this->misoIndex, message); 
    
    // Send  message: - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    
    for(int i = 0; i < times; i++)
        resultCode = this->slaveMISO.sendto(masterMISO, outgoing, length);
    
    // Notify terminal: - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    pl;printf("\n\r[%08dms][C] Sent: \"%s\" "
              "\n\r                To MMISO (%s, %d) (%d times)", 
        tm, length > 0? outgoing : "[SEND ERR]", 
        this->masterMISO.get_ip_address(), this->masterMISO.get_port(), times);
        pu;
    
    // Set acknowledgement flag to false: - - - - - - - - - - - - - - - - - - - 
    this->messageResent = false;    
    
    // Return result code: - - - - - - - - - - - - - - - - - - - - - - - - - - -
    return resultCode;
     
         
    } // End Communicator::_send // // // // // // // // // // // // // // // //

int Communicator::_receive( // // // // // // // // // // // // // // // // // /
    int *currentIndex, int *receivedIndex, char* keyword, char* command){
        /* ABOUT: Receive a message in MOSI socket and place it in the given
         * placeholder arguments.
         * RETURNS: Int; number of bytes received upon success, negative error
         * code upon failure.
         */ 
    
    // Placeholders: ===========================================================
    char received[MAX_MESSAGE_LENGTH];
    int result = -1;
    char *ptr;

    // Default values: =========================================================
    *receivedIndex = 0;
    keyword[0] = '\0';
    command[0] = '\0';
    result = -1;
    
    
    // Loop until a correct message is received or the socket times out:
    while(true){ // Receive loop ===============================================
        // Get messages and evaluate them. Either return w/ success after find-
        // ing an appropriate message or w/ failure after timing out.

        // Get a message: = = = = = = = = = = = = = = = = = = = = = = = = = = = 
        pl;printf("\n\r[%08dms][R] Waiting on message",tm);pu;
        
        result = 
            this->slaveMOSI.recvfrom(&this->masterMOSI, received, MAX_MESSAGE_LENGTH);

        // Validate message = = = = = = = = = = = = = = = = = = = = = = = = = = 

        // Check result integer: ----------------------------------------------
        if(result <= 0){
            // Timeout or other error code. Exit function w/ error code.
            pl;printf(
                "\n\r[%08dms][R] Receive timeout or network error: \n\r\t\"%s\""
                ,tm, this->_interpret(result));pu;
                
            return result;
            
        } // Done checking result integer: -------------------------------------
        // Split message: ------------------------------------------------------
        received[result] = '\0';
        
        pl;printf("\n\r[%08dms][R] Received: %s (%d)", tm,received, result);pu;

        sl;
        ptr = strtok(received,"|");
        
        // Get index: - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        if(ptr != NULL){
            *receivedIndex = atoi(ptr);
        }
        
        // Check index: - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        if((*receivedIndex <= *currentIndex) or (ptr == NULL)){
            // Bad index:
            pl;printf("\n\r[%08dms][R] Bad recv'd index (%d): expected %d",tm,
                ptr == NULL? 0 : *receivedIndex, *currentIndex);pu;

            // Restart loop:
            su;continue;
        }
        // Check keyword: - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        ptr = strtok(NULL, "|");

        if(ptr != NULL and strlen(ptr) == 4){
            strcpy(keyword, ptr);
        }
        else{
            // Bad keyword: 
            pl;printf("\n\r[%08dms][R] Bad recv'd keyword (%s)",tm,
                ptr == NULL? "[NULL]" : keyword);pu;

            // Restart loop:
            su;continue;
        }
        

        // Check command: - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        ptr = strtok(NULL, "|");

        if(ptr != NULL){

            strcpy(command, ptr);
            
        }else{
            command[0] = '\0';
        }

        su;

        // Reset corresponding timeout: - - - - - - - - - - - - - - - - - - - - 
        if(this->status == CONNECTED){

            // Increment Master timeouts:
            this->masterTimeouts = 0;

        }else{

            // Increment networkTimeouts:
            this->networkTimeouts = 0;

            } // End increment timeout - - - - - - - - - - - - - - - - - - - - 

        // Update index upon success: - - - - - - - - - - - - - - - - - - - - - 
        *currentIndex = *receivedIndex;

        // Break from loop:
        break;
        } // End receive loop /=================================================
    return result;        

    } // End Communicator::_receive // // // // // // // // // // // // // // //

void Communicator::_setStatus(const int newStatus){ // // // // // // // // // /
    // ABOUT: Set the current connection status, which will be displayed to
    // The user using the MCU's LED's and used for multithread coordination.
    
    static  Ticker statusTicker; // For LED blinking
    
    // Check current status for redundance: ------------------------------------
    if(this->status == newStatus){
        // Do nothing if the status modification is redundant:
        return;
    }else{ // Otherwise, update the status accordingly:
        // Reset timeout counters when changing status:
        this->networkTimeouts = 0;
        this->masterTimeouts = 0;
    
        switch(newStatus){ // - - - - - - - - - - - - - - - - - - - - - - - - - 
            
            case NO_MASTER: // ..................................................
                // Reset exchange index:
                this->exchangeIndex = 0;
                this->misoIndex = 0;
            
                // Set green:
                statusTicker.attach(callback(this, &Communicator::_blinkGreen),
                    BLINK_SLOW);
                // Set red:
                this->red = true;
                
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
                this->red = true;
                
                
                // Notify user:
                pl;printf("\n\r[%08dms][S] Status: CONNECTING",tm);pu;
                
                // Exit switch:
                break;
            
            case CONNECTED: // .................................................
                
                // No blinking:
                statusTicker.detach();
                
                // Set green:
                this->green = true;
                this->red = false;
                
                
                // Notify user:
                pl;printf("\n\r[%08dms][S] Status: CONNECTED", tm);pu;
                
                // Exit switch:
                break;
                             
            case NO_NETWORK: // ................................................
                // Reset exchange index:
                this->exchangeIndex = 0;
                this->misoIndex = 0;
            
                // Set green:
                this->green = false;
                
                // Set red:
                statusTicker.attach(callback(this, &Communicator::_blinkRed),
                    BLINK_FAST);
                    
                // Notify user:
                pl;printf("\n\r[%08dms][S] Status: NO_NETWORK", tm);pu;    
                
                // Exit switch
                break;
                
            case INITIALIZING: // ..............................................
                // Reset exchange index:
                this->exchangeIndex = 0;
                this->misoIndex = 0;
            
                // No blinking:
                statusTicker.detach();
                
                // Set green:
                this->green = false;
                this->red = true;
            
                   
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
    
    // Return control: ---------------------------------------------------------
    return;
      
    } // End Communicator::_setStatus // // // // // // // // // // // // // // // /

void Communicator::_blinkRed(){ // // // // // // // // // // // // // // // // 
    // About: Alternate status of red USR LED. To be used by _setStatus.
    
    // When called, alternate status:
    this->red = !red;
    
    } // End Communicator::_blinkRed // // // // // // // // // // // // // // /

void Communicator::_blinkGreen(){ // // // // // // // // // // // // // // // /
    // About: Alternate status of green USR LED. To be used by _setStatus.
    
    // When called, alternate status:
    this->green = !green;
    
    } // End Communicator::_blinkGreen // // // // // // // // // // // // // //

const char* Communicator::_interpret(int errorCode){
    /* Interpret a network error code and return its description.
     * - PARAM int errorCode: negative error code received by some network'n
     *   instance, such as a TCPSocket.
     * - RETURN: pointer to constant, NULL-terminated string of chars that
     *   describes the error, if a description is found.
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