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

Communicator::Communicator():processor(),
    exchangeIndex(0),networkTimeouts(0),masterTimeouts(0),
    listenerThread(osPriorityNormal, 16 * 1024 /*16K stack size*/),
    communicationThread(osPriorityNormal, 48 * 1024 /*48K stack size*/),
    red(LED3), green(LED1)
    { // // // // // // // // // // // // // // // // // // // // // // // // //
    /* ABOUT: Constructor for class Communicator. Starts networking threads.
     * PARAMETERS:
     * -Processor &processor: Reference to Processor instance. (See Proces-
     *  sor.h)
     */
    pl;printf("\n\r[%08dms][c] Initializing Communicator threads", tm);pu;
    this->_setStatus(INITIALIZING);
    
    // Start communications thread:
    this->communicationThread.start(callback(this,
        &Communicator::_communicationRoutine));

    
    // Start listener thread:
    this->listenerThread.start(callback(this, &Communicator::_listenerRoutine));
    
    pl;printf("\n\r[%08dms][c] Communicator constructor done", tm);pu;

    } // End Communicator::Communicator // // // // // // // // // // // // // /
     
void Communicator::_listenerRoutine(void){ // // // // // // // // // // // // / 
    /* ABOUT: Code to be executed by the broadcast listener thread.
     */ 
     
    pl;printf("\n\r[%08dms][L] Listener thread started", tm);pu;
    
    while(true){ // Listener routine loop ======================================
        
        // Wait standard timeout time to allow other threads to act: - - - - - -
        Thread::wait(TIMEOUT_MS);
        
        // Check status:
        if(this->status != NO_MASTER){
            // The listener routine should only be active when searching for
            // Master.
            
            // Yield control to other threads:
            Thread::wait(TIMEOUT_MS);
            // Restart loop when back:
            continue;
        }
        
        // Declare placeholders: - - - - - - - - - - - - - - - - - - - - - - - -
        char dataReceived[256], password[16] = {'\0'};
        int masterListenerPort = -1;
        
        // Receive data: - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        int bytesReceived = this->slaveListener.recvfrom(
                &masterBroadcast,
                dataReceived,
                255
            );
        
        // Validate reception of data: - - - - - - - - - - - - - - - - - - - - -
        if(bytesReceived <= 0){
            // A negative error code indicates a socket timeout. (In case of a
            // network error, the communication thread will catch it.)
            // (Also, a zero-length char array is not considered a valid messa-
            // ge and will be ignored.)
            // Restart loop:
            continue;
            
        }
        else{
            // A nonnegative value indicates a message was received.
            
            // Format data:
            dataReceived[bytesReceived] = '\0';
            pl;printf("\n\r[%08dms][L] Received: \"%s\""
                      "\n\r                From: (%s,%d)",tm,
                dataReceived, masterBroadcast.get_ip_address(), 
                masterBroadcast.get_port());pu;
        } 
        
        // If this line is reached, a message has been received.
        
        // Validate data received: - - - - - - - - - - - - - - - - - - - - - - -
        
        strtok(dataReceived, "|");
        strcpy(password, strtok(NULL, "|"));
        masterListenerPort = atoi(strtok(NULL, "|"));

        pl;printf("\n\r[%08dms][L] Parsing:"
                  "\n\r                Master LPort: %d"
                  "\n\r                Password: \"%s\"", 
                  tm, masterListenerPort, password);pu;
        
        if(masterListenerPort > 0 and strcmp(password, PASSWORD) == 0){
            // If the message received represents a general broadcast,
            // send corresponding reply: - - - - - - - - - - - - - - - - - - - -
            
            pl;printf("\n\r[%08dms][L] General broadcast validated. "
                        "Sending reply",tm);pu;
            
            // Configure listener address:......................................
            this->masterListener.set_ip_address(
                masterBroadcast.get_ip_address());
            
            this->masterListener.set_port(masterListenerPort);
            
            // Send reply:......................................................
            char reply[256];
            sprintf(reply, "00000000|%s|%s|%d|%d", 
                password,this->ethernet.get_mac_address(),SMISO, SMOSI);
                
            this->slaveListener.sendto(
                masterListener, reply, strlen(reply));
        
            pl; printf("\n\r[%08dms][L] Sent: %s"
                       "\n\r                To (%s, %d)",tm,
                reply, masterListener.get_ip_address(), masterListenerPort);pu;
                
            // Blink green LED for signaling: - - - - - - - - - - - - - - - - - 
            for(int i = 0; i < (this->status == CONNECTED? 1:2); i++){
                this->green = !this->green;
                Thread::wait(0.050);
                this->green = !this->green;
            } // End blink green LED - - - - - - - - - - - - - - - - - - - - - -
            
            
        }else{
            // If the message received represents neither a general broadcast
            // nor a specific broadcast, discard it and restart:
            
            pl; printf("\n\r[%08dms][L] Message invalid. Discarded", tm);pu;
            continue;
            
        }// end data validation - - - - - - - - - - - - - - - - - - - - - - - - 
    
    }// End listener routine loop ==============================================
    } // End Communicator::_listenerRoutine // // // // // // // // // // // // 
     
void Communicator::_communicationRoutine(void){ // // // // // // // // // // //
    /* ABOUT: Code to be executed by the communications thread.
     */
    
    // Communication routine set up ============================================
    pl; printf("\n\r[%08dms][P] Communication thread started", tm); pu;
    
    // Placeholders for communication loop -------------------------------------

    bool indexReset = false; // Whether to reset exchange index
    
    char processed[MAX_MESSAGE_LENGTH]; // Feedback to be sent back to Master 

    
    int receivedExchange = 0;  // Exchange index of a received message
    char receivedKeyword[64];  // Keyword of a received message
    char receivedCommand[MAX_MESSAGE_LENGTH]; // Possible command in a message
    
    while(true){ // Communication routine loop =================================
        // Setup = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
        // NOTE: This code will only be executed if there is no connection.
        // (i.e if this->status != CONNECTED)
        
        if(this->status == INITIALIZING){
            // Initialize ethernet interface - - - - - - - - - - - - - - - - - -
            int result = -1;
            unsigned int count = 1;
    
            while(result < 0){ // Ethernet loop ................................
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
                
            } // End ethernet loop .............................................
            pl; printf("\n\r[%08dms][C] Ethernet initialized (%s) ",tm,
                ethernet.get_ip_address());pu;
            
            // Initialize sockets - - - - - - - - - - - - - - - - - - - - - - -
            
            pl;
            printf("\n\r[%08dms][C] Initializing sockets", tm);
            pu;
            
            this->slaveMISO.open(&ethernet);
            this->slaveMISO.bind(SMISO);
            this->slaveMISO.set_timeout(TIMEOUT_MS);
            
            this->slaveMOSI.open(&ethernet);
            this->slaveMOSI.bind(SMOSI);
            this->slaveMOSI.set_timeout(TIMEOUT_MS);
            
            this->slaveListener.open(&ethernet);
            this->slaveListener.bind(SLISTENER);
            this->slaveListener.set_timeout(-1);
            
            pl;
            printf("\n\r[%08dms][C] Sockets initialized",tm);
            pu;

            this->processor.start();
            
            this->_setStatus(NO_MASTER);
            pl;printf("\n\r[%08dms][C] Ready for messages",tm);pu;  
        }
        else if (this->status == NO_NETWORK){
            // If there is no network, reconnect.
            
            // Terminate existing connection - - - - - - - - - - - - - - - - - -
            pl;printf("\n\r[%08dms][C] Network error detected. "
                    "Rebooting",tm);pu;
                    
            NVIC_SystemReset();
        } 
        
        // End setup = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
        
        // The following depends on the Slave's current status:

        else if(this->status == NO_MASTER){ // NO_MASTER = = = = = = = = = = = =
            // ABOUT: When disconnected from Master, look only for handshakes
            // and keep track of timeouts.

            // Handshake (1/2) -----------------------------------------------------
            pl;printf("\n\r[%08dms][C] On handshake (1/2)",tm);pu;

            // Receive message: - - - - - - - - - - - - - - - - - - - - - - - - - - 
            int result = this->_receive(&(this->exchangeIndex), 
                &receivedExchange, receivedKeyword, receivedCommand);
    
            pl;printf("\n\r[%08dms][C] Checking results (1/2)",tm);pu;
            // Check result:  - -  - - - - - - - - - - - - - - - - - - - - - - - - - 
            if( result <= 0 || strcmp(receivedKeyword, "MHSK") != 0){
                // Invalid results

                pl;printf("\n\r[%08dms][C] Failed to receive HS1...(%d NT's)",
                    tm, this->networkTimeouts);pu;
                    
                // Reset index:
                this->exchangeIndex = 0;

                // Check network timeouts to determine new status: .................
                if(this->networkTimeouts >= MAX_TIMEOUTS){
                    // Network timeouts past threshold. Assume network error.
                    pl;printf(
                        "\n\r[%08dms][C] Network timeouts past threshold",tm);pu;
                    
                    pl;printf("\n\r[%08dms][C] Network error detected. "
                        "Rebooting",tm);pu;
                    
                    NVIC_SystemReset();

                    } // End check network timeouts ................................
                
                // Restart loop:
                continue;

            }else{ // Valid results
                pl;printf("\n\r[%08dms][C] HSK received. Updating sockets",tm);pu;

                // Update status to stop broadcast:
                this->_setStatus(CONNECTING);

                // Update sockets: .................................................

                // Get values: . . . . . . . . . . . . . . . . . . . . . . . . . . .

                char *ptr = NULL;
                int port, periodms;
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

                    // Restart loop:
                    continue;
                }

                // Skip Master MOSI port:
                ptr = strtok(NULL, ",");
                pl;printf("\n\r[%08dms][C] Second item: %s",tm, ptr);pu;
                
                ptr = strtok(NULL, ",");
                pl;printf("\n\r[%08dms][C] Third item: %s",tm, ptr);pu;

                // Get period:
                if(ptr != NULL and (periodms = atoi(ptr)) > 0){

                    // Set timeout:
                    this->slaveMOSI.set_timeout(periodms);
                    
                    pl;printf("\n\r[%08dms][C] Timeout set to: %dms",
                        tm, periodms);pu;

                }else{
                    // Bad timeout:
                    pl;printf(
                        "\n\r[%08dms][C] HS1 ERROR. Bad period: %d(-1 if NULL)"
                        ,tm, ptr == NULL? -1:periodms);pu;

                    // Discard progress and restart:
                    this->_setStatus(NO_MASTER);

                    // Restart loop:
                    continue;
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

                    // Restart loop:
                    continue;

                }

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

                    // Restart loop:
                    continue;

                    } // End check success .....................................

            } // End check results (1/2) - - - - - - - - - - - - - - - - - - - -

        } else if(this->status == CONNECTED){ // CONNECTED = = = = = = = = = = =

            // When connected, wait for messages (or timeouts), and process them
            // in accordance w/ keywords.
            wait(0.001);
            // Receive message: ------------------------------------------------
                int result = this->_receive(&this->exchangeIndex, 
                    &receivedExchange, receivedKeyword, receivedCommand);
            
            // Check message: --------------------------------------------------
            
            if(result <=0){
                
                // Check threshold:
                if(this->masterTimeouts >= 2){
                    // Assume disconnection:
                    pl;printf("\n\r[%08dms][C] MT Threshold. "
                    "Assuming disconnection (%d/2)",
                    tm, this->masterTimeouts);pu;
                    
                    // Mark self as disconnected from Master:
                    this->_setStatus(NO_MASTER);
                }
                
                // Restart loop:
                continue;
                
            }else if(!strcmp(receivedKeyword, "MVER")){
                // Verification message. Reply w/ standard SVER to maintain
                // connection.

                // Get update from Processor:
                this->processor.get(processed);

                // Send update to Master:
                this->_send(processed, 5);
                
                // Restart loop:
                continue;


            }else if(!strcmp(receivedKeyword, "MSTD")){
                // Standard command message. Send command to Processor and for-
                // ward Processor update to Master.

                // Send command to Processor:
                this->processor.process(receivedCommand);

                // Get update from Processor:
                this->processor.get(processed);

                // Send update to Master:
                this->_send(processed, 5);
                
                // Restart loop:
                continue;

            } else if(!strcmp(receivedKeyword, "MRIP")){
                pl;printf(
                    "\n\r[%08dms][C] Connection terminated by Master",tm);pu;

                // Terminate connection:
                this->_setStatus(NO_MASTER);

                // Restart loop:
                continue;

                } // End check message -----------------------------------------


            } // End check status = = = = = = = = = = = = = = = = = = = = = = = 
        
        } // End communication routine loop ====================================

     
    } // End Communicator::_communicationRoutine // // // // // // // // // // /

int Communicator::_send(const char* message, int times){ // // // // // 
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
    
    // Format message: - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    length = sprintf(outgoing, "%d|%s", this->exchangeIndex, message); 
    
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
        pl;printf("\n\r[%08dms][C] Waiting on message",tm);pu;
        
        result = 
            this->slaveMOSI.recvfrom(&this->masterMOSI, received, MAX_MESSAGE_LENGTH);

        // Validate message = = = = = = = = = = = = = = = = = = = = = = = = = = 

        // Check result integer: ----------------------------------------------
        if(result <= 0){
            // Timeout or other error code. Exit function w/ error code.
            pl;printf(
                "\n\r[%08dms][C] Receive timeout or network error: \n\r\t\"%s\""
                ,tm, this->_interpret(result));pu;
                
            // Blink red LED for signaling: - - - - - - - - - - - - - - - - - - 
            for(int i = 0; i < (this->status == CONNECTED? 0:1); i++){
                this->red = !this->red;
                wait_ms(50);
                this->red = !this->red;
            } // End blink green LED - - - - - - - - - - - - - - - - - - - - - -

            // Increment corresponding timeout: - - - - - - - - - - - - - - - - 
            if(this->status == CONNECTED){

                // Increment Master timeouts:
                this->masterTimeouts += 1;
                pl;printf("\n\r[%08dms][C] MT incremented (%d/2)",
                    tm, this->masterTimeouts);pu;

            }else{

                // Increment networkTimeouts:
                this->networkTimeouts += 1;
                pl;printf("\n\r[%08dms][C] NT incremented (%d)",
                    tm, this->networkTimeouts);pu;

                } // End increment timeout - - - - - - - - - - - - - - - - - - -
            break; 
            
        } // Done checking result integer: -------------------------------------
        // Split message: ------------------------------------------------------
        received[result] = '\0';
        
        pl;printf("\n\r[%08dms][C] Received: %s (%d)", tm,received, result);pu;
        ptr = strtok(received,"|");
        
        // Get index: - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        if(ptr != NULL){
            *receivedIndex = atoi(ptr);
        }
        
        // Check index: - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        if((*receivedIndex < *currentIndex) or (ptr == NULL)){
            // Bad index:
            pl;printf("\n\r[%08dms][C] Bad recv'd index (%d): expected %d",tm,
                ptr == NULL? 0 : *receivedIndex, this->exchangeIndex);pu;

            // Restart loop:
            continue;
        }
        // Check keyword: - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        ptr = strtok(NULL, "|");

        if(ptr != NULL and strlen(ptr) == 4){
            strcpy(keyword, ptr);
        }
        else{
            // Bad keyword: 
            pl;printf("\n\r[%08dms][C] Bad recv'd keyword (%s)",tm,
                ptr == NULL? "[NULL]" : keyword);pu;
        }
        

        // Check command: - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        ptr = strtok(NULL, "|");

        if(ptr != NULL){

            strcpy(command, ptr);
            
        }else{
            command[0] = '\0';
        }

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

                // Reset socket timeout:
                this->slaveMOSI.set_timeout(TIMEOUT_MS);
            
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