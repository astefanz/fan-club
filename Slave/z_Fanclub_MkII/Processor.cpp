////////////////////////////////////////////////////////////////////////////////
// Project: Fanclub Mark II "Slave" // File: Processor.cpp - Implementation   //
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
// See Processor.h                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "Processor.h"

//// CONSTANT DEFINITIONS //////////////////////////////////////////////////////

const int  

    // STATUS CODES ------------------------------------------------------------
    CHASING = 2,
    ACTIVE = 1,
    OFF = -1,

    // FAN MODES ---------------------------------------------------------------
    SINGLE = 1,
    DOUBLE = 2;

const int GET_ERROR = -2147483648;

const char
    
    // COMMAND KEYWORDS --------------------------------------------------------
    WRITE = 'W',
    CHASE = 'C',
    CONFIGURE = 'S';
    

//// CLASS IMPLEMENTATION //////////////////////////////////////////////////////

// CONSTRUCTORS AND DESTRUCTORS ------------------------------------------------

Processor::Processor(void): // // // // // // // // // // // // // // // // // /
    processorThread(osPriorityNormal, 32 * 1024 /*32K stack size*/),
    activeFans(MAX_FANS), blue(LED2),
	dataIndex(0)
	{
    /* ABOUT: Constructor for class Processor. Starts processor thread.
     */

    pl;printf("\n\r[%08dms][p] Initializing Processor",tm);pu;

    // Initialize fan array:
    for(int i = 0; i < MAX_FANS; i++){
        this->fanArray[i].setPins(pwmOut[i], tachIn[i], MAX_RPM, MIN_RPM);
        this->fanArray[i].setPeriod(1000000/PWM_FREQUENCY);
            // Note: translate period from Hz to microseconds

    } // End fan array initialization loop
    pl;printf("\n\r[%08dms][p] fan array initialized",tm);pu;

    // Set initial status:
    this->setStatus(OFF);
    
} // End Processor constructor // // // // // // // // // // // // // // // // /

// PUBLIC INTERFACE ------------------------------------------------------------

bool Processor::process(const char* givenCommand){ // // // // // // // // // //
    /* ABOUT: Take a given command for processing.
     * PARAMETERS:
     * -const char* givenCommand: NULL-terminated string representing command to
     *  process.
     */

    // Place command in input queue: ===========================================

    // Try to allocate space in input queue: -----------------------------------
    command *allocatedCommand = this->inputQueue.alloc();

    // Check allocation: -------------------------------------------------------
    if(allocatedCommand != NULL){ // Allocation successful:

        // Store given command in placeholder:
        strcpy(allocatedCommand->content, givenCommand);

        // Place into queue:
        this->inputQueue.put(allocatedCommand);

    }else{ // Allocation unsuccessful:

        pl;printf("\n\r[%08dms][P] WARNING: inputQueue full",tm);pu;
        return false;

    } // End check allocation --------------------------------------------------
 
    return true;
} // End process  // // // // // // // // // // // // // // // // // // // // //
 
void Processor::get(char* buffer){ // // // // // // // // // // // // // // // 
    /* ABOUT: Get a reply to be sent to Master.
     * -PARAMETERS:
     * -const char* buffer: pointer to char array in which to store reply.
     */

    // Set up placeholder: -----------------------------------------------------
    char placeholder[MAX_MESSAGE_LENGTH] = "SVER";// There will always be 
    // ^                                                // a message to be sent
    // |                                             // to Master.
    // |
    // Static placeholder will keep the last stored value after returning.

    // Check output queue: -----------------------------------------------------
    osEvent result = this->outputQueue.get(0 /*0ms timeout*/);

    // Check if a new reply was successfully fetched:
    if(result.status == osEventMail){
        // New reply fetched from outputQueue. Use this reply:

        command *fetchedReply = (command*)result.value.p;
            // Returns void pointer to fetched value   ^

        // Store placeholder:
        strcpy(placeholder, fetchedReply->content);

        // Free space:
        this->outputQueue.free(fetchedReply);
    }

    // Store whatever is on the placeholder in the given buffer:
    strcpy(buffer, placeholder);

    // Done:
    return;
} // End get // // // // // // // // // // // // // // // // // // // // // // /

void Processor::start(void){
    // Start processor thread:
    this->processorThread.start(callback(this, 
        &Processor::_processorRoutine));
        
    }

void Processor::setStatus(int status){ // // // // // // // // // // // // // //
    /* ABOUT: Modify Processor status.
     * PARAMETERS:
     * -int status: Integer code of new status to set. Must be defined in 
     * Processor.h.
     */

    // Check redundancy:
    if (status == this->status){
        // If this status change is redundant, ignore it:
        return;
    }
	
    // Change status:
    switch(status){
        case CHASING: // Chasing target RPM ------------------------------------
            // Set internal status:
            this->status = status;
            // Update LED blinking:
                // Blink slowly
            this->blinker.attach(callback(this, &Processor::_blinkBlue),
                    BLINK_SLOW);
                    
            break;

        case ACTIVE: // Processor active ----------------------------------------
            // Set internal status:
            this->status = status;
            // Update LED blinking:
                // Solid blue
            this->blinker.detach();
            this->blue = 1;
            
            break;

        case OFF: // Processor offline -----------------------------------------
            // Set internal status:
            this->status = status;
            // Update LED blinking:
                // LED off
            this->blinker.detach();
            this->blue = 0;
        	
			// Reset data index:
			this->dataIndex = 0;
    
            break;

        default: // Unrecognized status code -----------------------------------
            // Print error message:
            pl;printf("\n\r[%08dms][P] ERROR: UNRECOGNIZED STATUS CODE %d", 
                tm, status);pu;
		
    }
} // End setStatus // // // // // // // // // // // // // // // // // // // // /

// INNER THREAD ROUTINES -------------------------------------------------------
void Processor::_processorRoutine(void){ // // // // // // // // // // // // // 
    /* ABOUT: To be executed by this Processor's processor thread.
     */

    // Thread setup ============================================================
    pl;printf("\n\r[%08dms][P] Processor thread started",tm);pu;

    // Prepare placeholders: ---------------------------------------------------
    char updateBuffer[MAX_MESSAGE_LENGTH];


    // Thread loop =============================================================
    while(true){

        // Check if active = = = = = = = = = = = = = = = = = = = = = = = = = = =
        if(this->status <= 0){
            // Processor off, set all fans to zero. (Safety redundancy)
            for(int i = 0; i < MAX_FANS; i++){
                this->fanArray[i].write(0);
            } // End set all fans to zero
        } else{
            // Processor active, check for commands: ---------------------------
            pl;printf("\n\r[%08dms][P] DEBUG: Processor active",tm);pu;
            // Try to fetch a command from input queue:
            osEvent fetchResult = this->inputQueue.get(0 /*0ms timeout*/);

            // Check for success:
            if(fetchResult.status == osEventMail){ // ==========================
                // Command fetched. Interpret and execute it.

                // Get command contents:
                command* rawCommand = (command*)fetchResult.value.p;
            
                // Store command in placeholder:
                char placeholder[MAX_MESSAGE_LENGTH];
                strcpy(placeholder, rawCommand->content);
                char *splitPosition; 
                
                // Split contents: 
                char* splitPtr = strtok_r(placeholder, "~", &splitPosition);
                    // NOTE: Use strtok_r instead of strtok for thread-safety
                
                // Deallocate command from inputQueue:
                this->inputQueue.free(rawCommand);

                // Verify splitting:
                if(splitPtr == NULL){
                    // Error:
                    pl;printf("\n\r[%08dms][P] ERROR: NULL splitPtr (1)",
                    tm);pu;

                    // Resume loop:
                    continue;
                } // End verify splitting.
                
                // Check command: ----------------------------------------------
                char commandCode = splitPtr[0];
                switch(commandCode){

                    case WRITE: // Set fan duty cycles
			{
                        pl;printf("\n\r[%08dms][P] WRITE received",tm);pu;

                        // Update status:
                        if (this->status == CHASING){
		      	    // WRITE should overwrite CHASING when called 
                            // (and vice versa)
                            this->setStatus(ACTIVE);
                        }

                        // Split contents for duty cycle:
                        splitPtr = strtok_r(NULL, "~", &splitPosition);

                        // Validate:
                        if(splitPtr == NULL){
                            // Error:
                            pl;printf(
                                "\n\r[%08dms][P] ERROR: NULL splitPtr (2)",
                                tm);pu;

                            // Ignore message:
                            continue;
                        } // End validate splitting

                        // Get float duty cycle:
                        float dutyCycle = atof(splitPtr);
                        pl;printf("\n\r[%08dms][P] DC: %f",tm, dutyCycle);pu;

                        // Split contents for selected fans:
                        splitPtr = strtok_r(NULL, "~", &splitPosition);

                            // spliPtr now points to a string of 0's and 1's,
                            // indicating which fans are selected. For example:
                            //            " 000111000100000000000"
                            // Means fans number 4,5,6 and 10 are selected 
                            // (using indexing that starts at 1 to please the 
                            // non-CS muggles.

                        // Validate:
                        if(splitPtr == NULL){
                            // Error:
                            pl;printf(
                                "\n\r[%08dms][P] ERROR: NULL splitPtr (3)",
                                tm);pu;

                            // Ignore message:
                            continue;
                        } // End validate splitting

                        // Get length of selection:
                        int numFans = strlen(splitPtr);

                        pl;printf("\n\r[%08dms][P] Fans: %s (%d)",
                            tm, splitPtr, numFans);pu;

                        // Loop over list and assign duty cycles:
                        for(int i = 0; i < numFans; i++){

                            // Check if the corresponding index is selected:
                            if(splitPtr[i] - '0'){
                             //\---------------/
                             // This expression will evaluate to 0 if the fan is
                             // set to 0, and nonzero (true) otherwise.
                                this->fanArray[i].write(dutyCycle);
                                pl;printf("\n\r[%08dms][P] Fan %d set",tm, i);pu;
                            }
                        } // End assign duty cycles

                        pl;printf("\n\r[%08dms][P] Duty cycles assigned",tm);pu;

                        break;
			}
                    case CHASE: // Set a target RPM -- UNIMPLEMENTED ----------------------------------- *

                        // Update status:
                        if (this->status == ACTIVE){
                            // WRITE should overrite CHASING when called 
                            // (and vice versa)
                            this->setStatus(CHASING);
                        }

                        pl;printf(
                            "\n\r[%08dms][P] WARNING: CHASER UNIMPLEMENTED",
                            tm);pu;

                        break;

                    case CONFIGURE: // Configure fan array parameters -- UNIMPLEMENTED ------------------- *

                        // Update status:
                        if (this->status <= 0){
                            // Set status to active:
                            this->setStatus(ACTIVE);
                        }

                        pl;printf(
                            "\n\r[%08dms][P] WARNING: CONFIGURE UNIMPLEMENTED",
                            tm);pu;

                        break;

                    default: // Unrecognized command:

                        // Issue error message and discard command:

                        pl;printf(
                            "\n\r[%08dms][P] ERROR: UNRECOGNIZED COMMAND: %c",
                            tm, splitPtr[0]);pu;

                } // End check command -----------------------------------------
                
            } // End command processing ========================================

            pl;printf("\n\r[%08dms][P] DEBUG: Updating values",tm);pu;

            // Update values: ==================================================
            int n = 0; // Keep track of string index
			
			// Increment data index:
			this->dataIndex++;
			
			// Print beginning of update message:	
			n+= snprintf(updateBuffer, MAX_MESSAGE_LENGTH,"SSTD|%d|",
				this->dataIndex);

            // Store RPM's: ----------------------------------------------------

            // Store first RPM along w/ keyword and separator:
            n += snprintf(updateBuffer + n, MAX_MESSAGE_LENGTH - n, "%d", 
                this->fanArray[0].read());

            // Store other RPM's:
            for(int i = 1; i < activeFans; i++){
                // Loop over update placeholder and print out RPM's:
                n += snprintf(updateBuffer + n, MAX_MESSAGE_LENGTH - n, ",%d", 
                this->fanArray[i].read());
            }

            // Store duty cycles: ----------------------------------------------

            // Store first duty cycle along w/ separator:
            n += snprintf(updateBuffer + n, MAX_MESSAGE_LENGTH - n, "|%f", 
                this->fanArray[0].getPWM());

            // Store other duty cycles:
            for(int i = 1; i < activeFans; i++){
                // Loop over update placeholder and print out RPM's:
                n += snprintf(updateBuffer + n, MAX_MESSAGE_LENGTH - n, ",%f", 
                this->fanArray[i].getPWM());
            }
            
            // DEBUG:
            pl;printf("\n\r[%08dms][P] updateBuffer: %s", tm, updateBuffer);pu;

            // Store update buffer in output queue: ----------------------------

            // Try to allocate space in output queue: --------------------------
            command *allocatedCommand = this->outputQueue.alloc();

            // Check allocation: -----------------------------------------------
            if(allocatedCommand != NULL){ // Allocation successful:

                // Store given command in placeholder:
                strcpy(allocatedCommand->content, updateBuffer);

                // Place into queue:
                this->outputQueue.put(allocatedCommand);

            }else{ // Allocation unsuccessful:

                pl;printf("\n\r[%08dms][P] WARNING: outputQueue full",tm);pu;
                // In this case, the message will be discarded.

            } // End check allocation ------------------------------------------

        } // End check if active = = = = = = = = = = = = = = = = = = = = = = = =

    } // End processor thread loop =============================================

    pl;printf("\n\r[%08dms][P] WARNING: BROKE OUT OF PROCESSOR THREAD LOOP",
        tm);pu;
} // End _processorThread // // // // // // // // // // // // // // // // // // 
     
void Processor::_blinkBlue(void){ // // // // // // // // // // // // // // // /
    /* ABOUT: To be set as ISR for blue LED Ticker to show status.
     */

    // Alternate value of LED:
    this->blue = !this->blue;
} // End _blinkBlue // // // // // // // // // // // // // // // // // // // // 

/*    

    Thread processorThread; // Executes _processorRoutine
    
    // PROFILE DATA ------------------------------------------------------------
    int8_t fanMode;         // Single or double fan configuration
    int targetRelation[2];  // (If applic.) Rel. between front and rear fan RPM
    uint8_t activeFans;      // Number of active fans
    uint8_t counterCounts;  // Number of pulses to be counted when reading
    uint8_t pulsesPerRotation;   // Pulses sent by sensor in one full rotation
    uint8_t maxRPM;         // Maximum nominal RPM of fan model
    uint8_t minRPM;         // Minimum nominal nonzero RPM of fan model
    uint8_t minDC;          // Duty cycle corresponding to minRPM (nominal)
    
    // STATUS DATA -------------------------------------------------------------
    int8_t status;      // Current processor status
    DigitalOut blue;    // Access to blue LED
    Ticker blinker;     // Used to blink blue LED for status   
    Mutex dataLock; // Thread safe access
    
    // PROCESS DATA ------------------------------------------------------------
    Mail<process, 2> inputQueue, outputQueue; // For inter-thread comms.

    // Fan array data ----------------------------------------------------------
    Fan fanArray[MAX_FANS];
    
*/
