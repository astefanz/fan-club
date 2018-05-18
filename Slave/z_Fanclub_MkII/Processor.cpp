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
#include "mbed_stats.h"

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
    processorThread(osPriorityNormal, 16 * 1024 /*32K stack size*/),
    fanMode(FAN_MODE),
	activeFans(MAX_FANS),
	fanFrequencyHZ(PWM_FREQUENCY),
	counterCounts(COUNTER_COUNTS),
	pulsesPerRotation(PULSES_PER_ROTATION),
	maxRPM(MAX_RPM),
	minRPM(MIN_RPM),
	minDC(MIN_DC),
	chaserTolerance(CHASER_TOLERANCE),
	dataIndex(0),  
	blue(LED2),
	inFlag(false), outFlag(false)
	{
    /* ABOUT: Constructor for class Processor. Starts processor thread.
     */

    pl;printf("\n\r[%08dms][p] initializing processor",tm);pu;

	this->targetRelation[0] = TARGET_RELATION_0;
	this->targetRelation[1] = TARGET_RELATION_1;
    // Initialize fan array:
    for(int i = 0; i < MAX_FANS; i++){
        this->fanArray[i].configure(pwmOut[i], tachIn[i], 
			this->fanFrequencyHZ, this->counterCounts, this->pulsesPerRotation);

    } // End fan array initialization loop
    pl;printf("\n\r[%08dms][p] fan array initialized",tm);pu;

    // Set initial status:
    this->setStatus(OFF);
    
} // End Processor constructor // // // // // // // // // // // // // // // // /

// PUBLIC INTERFACE ------------------------------------------------------------

bool Processor::process(const char* givenCommand, bool configure){ // // // // /
	/* ABOUT: Take a given command for processing.
		* PARAMETERS:
		* -const char* givenCommand: NULL-terminated string representing command 
		* to process.
		* -bool configure: whether this message is to configure the Processor.
		*	Defaults to false.
		*/
	
	// Use a placeholder to return once:
	bool success = false;
	
	if(not configure){
		// Standard usage. Try to place this command in the input buffer:

		this->inFlagLock.lock();
		if(not this->inFlag){
			// If the input flag is not set, then the buffer is available.
			// Acquire buffer lock and edit buffer:

			this->inBufferLock.lock();
			strcpy(this->inBuffer, givenCommand);
			this->inBufferLock.unlock();
			
			this->inFlag = true;
			success = true;
			
		}else{ 
			// Allocation unsuccessful:
			
			pl;printf("\n\r[%08dms][P] WARNING: inputQueue full",tm);pu;

		} // End check input flag
		this->inFlagLock.unlock();
	
	} else {
		// Configure Processor.

		// Ensure configuration is done on a deactivated Processor:
		int previousStatus = this->status;
		if(previousStatus != OFF){
			this->setStatus(OFF);
		}
		
		// Get values:
		int fanMode, activeFans, fanFrequencyHZ,
			counterCounts, pulsesPerRotation, maxRPM, minRPM;
		
		float targetRelation0, targetRelation1, chaserTolerance, minDC;

		sscanf(givenCommand, "%d %f %f %d %d %d %d %d %d %f %f",
			&fanMode, &targetRelation0, &targetRelation1, 
			&activeFans, &fanFrequencyHZ, &counterCounts,
			&pulsesPerRotation, &maxRPM, &minRPM, &minDC, &chaserTolerance);
		
		// Validate values:
		if( (fanMode != SINGLE and fanMode != DOUBLE) || 
			activeFans < 0 || fanFrequencyHZ <= 0 || counterCounts <= 0 || 
			pulsesPerRotation < 1 || maxRPM <= minRPM || minRPM < 0 || 
			minDC < 0 || chaserTolerance <= 0.0) {
			
			// Invalid data. Print error and return error false.
			
    		pl;printf("\n\r[%08dms][P] ERROR: BAD HSK CONFIG VALUE(S): "
			"%d,%f,%f,%d,%d,%d,%d,%d,%d,%f,%f",tm,
			fanMode, targetRelation0, targetRelation1, 
			activeFans, fanFrequencyHZ, counterCounts,
			pulsesPerRotation, maxRPM, minRPM, minDC, chaserTolerance);pu;
		
			success = false;
	
		} else {
			// Valid data. Proceed with assignment.
		
			this->fanMode = (int8_t) fanMode;
			this->targetRelation[0] = targetRelation0;
			this->targetRelation[1] = targetRelation1;
			this->activeFans = (uint32_t)activeFans;
			this->fanFrequencyHZ = (uint32_t)fanFrequencyHZ;
			this->counterCounts = (uint32_t)counterCounts;
			this->pulsesPerRotation = (uint32_t)pulsesPerRotation;
			this->maxRPM = (uint32_t)maxRPM;
			this->minRPM = (uint32_t)minRPM;
			this->minDC = minDC;
			this->chaserTolerance = chaserTolerance;


			// Reconfigure fan array:
			for(int i = 0; i < this->activeFans; i++){
				this->fanArray[i].configure(pwmOut[i], tachIn[i], 
					this->fanFrequencyHZ, this->counterCounts, 
					this->pulsesPerRotation);

			} // End fan array reconfiguration loop


				success = true;
		
		} // End if/else


		// Restore previous status:
		if(previousStatus != OFF){
			this->setStatus(previousStatus);
		}
		
	
	} // End check configure

    return success;
} // End process  // // // // // // // // // // // // // // // // // // // // //
 
bool Processor::get(char* buffer){ // // // // // // // // // // // // // // // 
    /* ABOUT: Get a reply to be sent to Master.
     * PARAMETERS:
     * -const char* buffer: pointer to char array in which to store reply.
	 * RETURNS:
	 * -bool: whether a new message was fetched (false for default)
     */

	// Try to get a message from the output buffer. If it is empty, use the
	// standard "verification" message.
	bool success = false;

	this->outFlagLock.lock();

	if(this->outFlag){
		// There is a message. Lock the output buffer and copy its contents into
		// the given buffer.

		this->outBufferLock.lock();

		strcpy(buffer, this->outBuffer[0] == '\0'? "SVER": this->outBuffer);
		// NOTE: The check above rules out the unlikely --yet possible-- case
		// in which the output buffer is lost. (This may happen if this
		// function checks a raised output flag while the output buffer lock
		// is taken by the processor routine. Since these output values are
		// updated frequently and automatically, it is preferable to sacrifice
		// one buffer for efficiency.


		this->outBuffer[0] = '\0';
			// NOTE: Neutralize obsolete message.
		this->outFlag = false;
		
		success = true;

		this->outBufferLock.unlock();

	}else{
		// If there is no message to send, use the default:

		strcpy(buffer, "SVER");

	}
	this->outFlagLock.unlock();
	return success;

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

        case ACTIVE: // Processor active ---------------------------------------
			
			// If the Processor is being activateed after being off (not 
			// previously chasing), then reset fan configuration.
			
			#ifdef DEBUG
    		pl;printf("\n\r[%08dms][P][DEBUG] Config. V's: "
			"%d,%f,%f,%d,%d,%d,%d,%d,%d,%f,%f",tm,
			this->fanMode, this->targetRelation[0], this->targetRelation[1], 
			this->activeFans, this->fanFrequencyHZ, this->counterCounts,
			this->pulsesPerRotation, this->maxRPM, this->minRPM, this->minDC, 
			this->chaserTolerance);pu;
			
			#endif		

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
   
			// Reset buffers and flags:

			// Input:
			this->inFlagLock.lock();
			this->inBufferLock.lock();
			this->inBuffer[0] = '\0';
			this->inFlag = false;
			this->inBufferLock.unlock();
			this->inFlagLock.unlock();

			// Output:
			this->outFlagLock.lock();
			this->outBufferLock.lock();
			this->outBuffer[0] = '\0';
			this->outFlag = false;
			this->outBufferLock.unlock();
			this->outFlagLock.unlock();

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
	char rawCommand[MAX_MESSAGE_LENGTH];
	char rpmBuffer[MAX_MESSAGE_LENGTH]; // Save last RPM value
	bool rpmWritten = false; // Avoid skipping RPM's before the first write
	bool writeCalled = false; // Keep track of whether a write was just called

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
            // pl;printf("\n\r[%08dms][P] DEBUG: Processor active",tm);pu;

			// Reset corresponding flags:
			writeCalled = false;

			this->inFlagLock.lock();
				// NOTICE: This lock is released in two different places (if and
				// else) as an optimization
			if(this->inFlag){ // ===============================================
           

                // Get command contents:
				this->inBufferLock.lock();
				strcpy(rawCommand, this->inBuffer);
				this->inBuffer[0] = '\0';
					// NOTE: Destroy obsolete message
				this->inBufferLock.unlock();

				// Clear input flag:
				this->inFlag = false;
				this->inFlagLock.unlock();

                
                // Split contents: 
                char *splitPosition; 
                char* splitPtr = strtok_r(rawCommand, "~", &splitPosition);
                    // NOTE: Use strtok_r instead of strtok for thread-safety
                
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
						writeCalled = true;
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
                        #ifdef DEBUG
						pl;printf("\n\r[%08dms][P] DC: %f",tm, dutyCycle);pu;
						#endif

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
						
						#ifdef DEBUG
                        pl;printf("\n\r[%08dms][P] Fans: %s (%d)",
                            tm, splitPtr, numFans);pu;
						#endif

                        // Loop over list and assign duty cycles:
                        for(int i = 0; i < numFans; i++){

                            // Check if the corresponding index is selected:
                            if(splitPtr[i] - '0'){
                             //\---------------/
                             // This expression will evaluate to 0 if the fan is
                             // set to 0, and nonzero (true) otherwise.
                                this->fanArray[i].write(dutyCycle);
                            }
                        } // End assign duty cycles

                        pl;printf("\n\r[%08dms][P] Duty cycles assigned",tm);pu;

                        break;
					}
                    case CHASE: // Set a target RPM -- UNIMPLEMENTED ----------------------------------- *

                        // Update status:
                        if (this->status == ACTIVE){
                            this->setStatus(CHASING);
                        }

                        pl;printf(
                            "\n\r[%08dms][P] WARNING: CHASER UNIMPLEMENTED",
                            tm);pu;

                        break;

                    default: // Unrecognized command:

                        // Issue error message and discard command:

                        pl;printf(
                            "\n\r[%08dms][P] ERROR: UNRECOGNIZED COMMAND: %c",
                            tm, splitPtr[0]);pu;

                } // End check command -----------------------------------------
                
            }else{
				// Nothing to process yet. Release input flag lock.
				this->inFlagLock.unlock();
			} // End command processing ========================================


			this->outFlagLock.lock();
			if(not this->outFlag){
				#ifdef DEBUG
				pl;printf("\n\r[%08dms][P] DEBUG: Updating values",tm);pu;
				#endif
				// If the output buffer is free, write to it.
				this->outFlagLock.unlock();

				this->outBufferLock.lock();
				
				// Update values: ==================================================
				int n = 0; // Keep track of string index
				
				// Increment data index:
				this->dataIndex++;
				
				// Print beginning of update message:	
				n+= snprintf(this->outBuffer, MAX_MESSAGE_LENGTH,"SSTD|%d|",
					this->dataIndex);

				// Store RPM's: ----------------------------------------------------
				
				if(not (writeCalled and rpmWritten)){
					// NOTE: Skip RPM writing if a DC was just set, to allow for 
					// fast feedback. Do this as long as there is some RPM value
					// in the buffer (i.e rpmWritte is true)	

					// Store first RPM along w/ keyword and separator:
					int m = snprintf(rpmBuffer, MAX_MESSAGE_LENGTH, "%d", 
						this->fanArray[0].read());

					// Store other RPM's:
					for(int i = 1; i < activeFans; i++){
						// Loop over buffer and print out RPM's:
						m += snprintf(
						rpmBuffer + m, MAX_MESSAGE_LENGTH - m, ",%d", 
						this->fanArray[i].read());
					}				

					// Save DC index for later
					rpmWritten = true;

				}
				// Save RPM buffer into output buffer
				n += snprintf(this->outBuffer + n, MAX_MESSAGE_LENGTH - n, "%s",
					rpmBuffer);

				// Store duty cycles: ----------------------------------------------

				// Store first duty cycle along w/ separator:
				n += snprintf(this->outBuffer + n, MAX_MESSAGE_LENGTH - n, "|%.4f", 
					this->fanArray[0].getDC());

				// Store other duty cycles:
				for(int i = 1; i < activeFans; i++){
					// Loop over buffer and print out RPM's:
					n += snprintf(this->outBuffer + n, MAX_MESSAGE_LENGTH - n, ",%.4f", 
					this->fanArray[i].getDC());
				}
			
				this->outBufferLock.unlock();

				// Raise output flag:
				this->outFlagLock.lock();
				this->outFlag = true;
				this->outFlagLock.unlock();
		} else {
			// If the output buffer is busy, wait until it has been freed.
			this->outFlagLock.unlock();
		}
			
        } // End check if active = = = = = = = = = = = = = = = = = = = = = = = =

    } // End processor thread loop =============================================

    pl;printf("\n\r[%08dms][P] WARNING: BROKE OUT OF PROCESSOR THREAD LOOP",
        tm);pu;
} // End _processorRoutine // // // // // // // // // // // // // // // // // // 
     
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
    // PROCESS DATA ------------------------------------------------------------
    Mail<process, 2> inputQueue, outputQueue; // For inter-thread comms.

    // Fan array data ----------------------------------------------------------
    Fan fanArray[MAX_FANS];
    
*/
