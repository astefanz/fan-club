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
    OFF = 0,
	ON = 1,
	TOGGLE = 3,

    // FAN MODES ---------------------------------------------------------------
    SINGLE = -1,
    DOUBLE = -2;

const char
    
    // COMMAND KEYWORDS --------------------------------------------------------
    WRITE = 'D',
    CHASE = 'C';
    

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
	maxFanTimeouts(MAX_FAN_TIMEOUTS),
	dataIndex(0),  
	rpmSlope((MAX_RPM-MIN_RPM)/(1.0-MIN_DC)),
	led(LED2),
	xled(D4),
	#ifndef JPL
	psuOff(D9),
	#endif
	inFlag(false), outFlag(false)
	{
    /* ABOUT: Constructor for class Processor. Starts processor thread.
     */

    pl;printf("\n\r[%08dms][p] Processor initialized",tm);pu;

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

			strcpy(this->inBuffer, givenCommand);
			
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
		this->setStatus(OFF);
		
		// Get values:
		int fanMode, activeFans, fanFrequencyHZ,
			counterCounts, pulsesPerRotation, maxRPM, minRPM,
			maxFanTimeouts;
		
		float chaserTolerance, minDC;

		char pwmPinout[25] = {0}, tachPinout[25] = {0};

		sscanf(givenCommand, "%d %d %d %d %d %d %d %f %f %d %s %s",
			&fanMode, &activeFans, &fanFrequencyHZ, &counterCounts,
			&pulsesPerRotation, &maxRPM, &minRPM, &minDC, &chaserTolerance,
			&maxFanTimeouts, pwmPinout, tachPinout);
		
		// Validate values:
		if( (fanMode != SINGLE and fanMode != DOUBLE) || 
			activeFans < 0 || activeFans > 24 || 
			fanFrequencyHZ <= 0 || counterCounts <= 0 || 
			pulsesPerRotation < 1 || maxRPM <= minRPM || minRPM < 0 || 
			minDC < 0 || chaserTolerance <= 0.0 || maxFanTimeouts < 0
			|| pwmPinout[0] == '\0' || tachPinout[0] == '\0') {
			
			// Invalid data. Print error and return error false.
			pl;printf("\n\r[%08dms][P][E] BAD HSK CONFIG VALUE(S): "
			"\n\r\tfanMode: %d"\
			"\n\r\tactiveFans: %d"\
			"\n\r\tfanFreqHZ: %d"\
			"\n\r\tcounterCounts: %d"\
			"\n\r\tpulsesPerRotation: %d"\
			"\n\r\tmaxRPM: %d"\
			"\n\r\tminRPM: %d"\
			"\n\r\tminDC: %f"\
			"\n\r\tchaserTolerance: %f"\
			"\n\r\tmaxFanTimeouts: %d"\
			"\n\r\tPWM pinout: \"%s\""\
			"\n\r\tTach pinout: \"%s\"",tm,
			fanMode, 
			activeFans, fanFrequencyHZ, counterCounts,
			pulsesPerRotation, maxRPM, minRPM, minDC, chaserTolerance,
			maxFanTimeouts,
			pwmPinout, tachPinout);pu;
			
			/*
			pl;printf("\n\r[%08dms][P] ERROR: BAD HSK CONFIG VALUE(S): "
			"%d,%d,%d,%d,%d,%d,%d,%f,%f,%d,\"%s\",\"%s\"",tm,
			fanMode, 
			activeFans, fanFrequencyHZ, counterCounts,
			pulsesPerRotation, maxRPM, minRPM, minDC, chaserTolerance,
			maxFanTimeouts,
			pwmPinout, tachPinout);pu;
			*/
			success = false;
	
		} else {
			// Valid data. Proceed with assignment.
			pl;printf("\n\r[%08dms][P][DB] HSK CONFIG VALUE(S): "
			"\n\r\tfanMode: %d"\
			"\n\r\tactiveFans: %d"\
			"\n\r\tfanFreqHZ: %d"\
			"\n\r\tcounterCounts: %d"\
			"\n\r\tpulsesPerRotation: %d"\
			"\n\r\tmaxRPM: %d"\
			"\n\r\tminRPM: %d"\
			"\n\r\tminDC: %f"\
			"\n\r\tchaserTolerance: %f"\
			"\n\r\tmaxFanTimeouts: %d"\
			"\n\r\tPWM pinout: \"%s\""\
			"\n\r\tTach pinout: \"%s\"",tm,
			fanMode, 
			activeFans, fanFrequencyHZ, counterCounts,
			pulsesPerRotation, maxRPM, minRPM, minDC, chaserTolerance,
			maxFanTimeouts,
			pwmPinout, tachPinout);pu;
			
			this->fanMode = fanMode;
			this->activeFans = activeFans;
			this->fanFrequencyHZ = fanFrequencyHZ;
			this->counterCounts = counterCounts;
			this->pulsesPerRotation = pulsesPerRotation;
			this->maxRPM = maxRPM;
			this->minRPM = minRPM;
			this->minDC = minDC;
			this->chaserTolerance = chaserTolerance;
			this->maxFanTimeouts = maxFanTimeouts;
			
			// RPM linear fit:
			this->rpmSlope = (maxRPM - minRPM)/(1.0 - minDC);
		
			/* DEBUG
			pl;printf("\n\r[%08dms][P] HSK CONFIG VALUES: "
			"\n\r\tfanMode: %d"\
			"\n\r\tactiveFans: %d"\
			"\n\r\tfanFreqHZ: %d"\
			"\n\r\tcounterCounts: %d"\
			"\n\r\tpulsesPerRotation: %d"\
			"\n\r\tmaxRPM: %d"\
			"\n\r\tminRPM: %d"\
			"\n\r\tminDC: %f"\
			"\n\r\tchaserTolerance: %f"\
			"\n\r\tmaxFanTimeouts: %d"\
			"\n\r\tPWM pinout: \"%s\""\
			"\n\r\tTach pinout: \"%s\"",tm,
			fanMode, 
			activeFans, fanFrequencyHZ, counterCounts,
			pulsesPerRotation, maxRPM, minRPM, minDC, chaserTolerance,
			maxFanTimeouts,
			pwmPinout, tachPinout);pu;
			*/
			/* DEBUG
			pl;printf("\n\r[%08dms][P] Configuring fan array: ", tm);pu;
			*/

			// Configure fan array:
			for(int i = 0; i < activeFans; i++){

				/* DEBUG
				pl;printf("\n\r\t Fan %d: P:%d T:%d", 
					i, int(pwmPinout[i]-'A'), int(tachPinout[i]-'[') );pu;
				 */

				this->fanArray[i].configure(
					PWMS[pwmPinout[i] - 'A'], 
					TACHS[tachPinout[i] - '['],
					this->fanFrequencyHZ, 
					this->counterCounts, 
					this->pulsesPerRotation, 
					this->minRPM,
					this->minDC,
					this->maxFanTimeouts);
			} // End fan array reconfiguration loop
			success = true;

		} // End if/else

	} // End check configure

    return success;
} // End process  // // // // // // // // // // // // // // // // // // // // //
 
bool Processor::get(char* buffer){ // // // // // // // // // // // // // // // 
    /* ABOUT: Get a reply to be sent to Master.
     * PARAMETERS:
     * -const char* buffer: pointer to char array in which to store reply.
	 * RETURNS:
	 * -bool: whether a new message was fetched (false for default)
	 *	NOTE: a false return value implies the given buffer has been left 
	 *	unmodified.
     */

	// Try to get a message from the output buffer. If it is empty, use the
	// standard "verification" message.
	bool success = false;

	this->outFlagLock.lock();

	if(this->outFlag){
		// NOTE (From a previous version):
		// ---------------------------------------------------------------------
		// The check above rules out the unlikely --yet possible-- case
		// in which the output buffer is lost. (This may happen if this
		// function checks a raised output flag while the output buffer lock
		// is taken by the processor routine. Since these output values are
		// updated frequently and automatically, it is preferable to sacrifice
		// one buffer for efficiency.
		// ---------------------------------------------------------------------
		
		// There is a message. Lock the output buffer and copy its contents into
		// the given buffer.
		strcpy(buffer, this->outBuffer[0] != '\0'? this->outBuffer : "M");
		
		this->outBuffer[0] = '\0';
		this->outFlag = false;
		success = true;

	}else{
		// If there is no message to send, use the default:
		buffer[0] = 'M';
		buffer[1] = '\0';
		success = false;

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
            this->blinker.attach(callback(this, &Processor::_blinkLED),
                    BLINK_SLOW);
                    
            break;

        case ACTIVE: // Processor active ---------------------------------------
			
			// If the Processor is being activateed after being off (not 
			// previously chasing), then reset fan configuration.
			
			/* DEBUG
			pl;printf("\n\r[%08dms][P][DEBUG] Config. V's: "
			"%d,%f,%f,%d,%d,%d,%d,%d,%d,%f,%f,%d",tm,
			this->fanMode, this->targetRelation[0], this->targetRelation[1], 
			this->activeFans, this->fanFrequencyHZ, this->counterCounts,
			this->pulsesPerRotation, this->maxRPM, this->minRPM, this->minDC, 
			this->chaserTolerance,this->maxFanTimeouts);pu;
			
			pl;printf("\n\r[%08dms][P][DEBUG] RPM SLOPE: %.2f", 
				tm, this->rpmSlope);pu;
			*/

			// Set internal status:
            this->status = ACTIVE;
            // Update LED blinking:
                // Solid blue
            this->blinker.detach();
			this->_setLED(ON);
			#ifndef JPL
			this->psuOff.write(false);
			#endif

            break;

        case OFF: // Processor offline -----------------------------------------
            this->threadLock.lock();
			
			// Set internal status:
            this->status = status;
            // Update LED blinking:
                // LED off
            this->blinker.detach();
			#ifndef JPL
			this->psuOff.write(true);
			#endif
            this->_setLED(OFF);

			// Reset data index:
			this->dataIndex = 0;
   
			// Reset buffers and flags:

			// Input:
			this->inFlagLock.lock();
			this->inBuffer[0] = '\0';
			this->inFlag = false;
			this->inFlagLock.unlock();

			// Output:
			this->outFlagLock.lock();
			this->outBuffer[0] = '\0';
			this->outFlag = false;
			this->outFlagLock.unlock();
			
			this->threadLock.unlock();

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
		this->threadLock.lock();
        //pl;printf("\n\r[%08dms][P] DEBUG: Processor loop active",tm);pu;
		//wait_us(1);		

        // Check if active = = = = = = = = = = = = = = = = = = = = = = = = = = =
		if(this->status ==  OFF){
			// Reset values

            // Processor off, set all fans to zero. (Safety redundancy)
            //pl;printf("\n\r[%08dms][P] DEBUG: Processor inactive",tm);pu;

            for(int i = 0; i < MAX_FANS; i++){
                this->fanArray[i].write(0);
            } // End set all fans to zero
			
			rpmWritten = false; // Avoid skipping RPM's before the first write
			writeCalled = false; // Keep track of whether a write was just called
			
        } else{
            // Processor active, check for commands: ---------------------------
            //pl;printf("\n\r[%08dms][P] DEBUG: Processor active",tm);pu;


    		//pl;printf("\n\r[%08dms][P] P-IN",tm);pu;


			// Reset corresponding flags:
			writeCalled = false;
						
			this->inFlagLock.lock();
				// NOTICE: This lock is released in two different places (if and
				// else) as an optimization
			if(this->inFlag){ // ===============================================
           

				//pl;printf("\n\r[%08dms][P][D] Input found",tm);pu;

                // Get command contents:
				strcpy(rawCommand, this->inBuffer);
				this->inBuffer[0] = '\0';
					// NOTE: Destroy obsolete message

				// Clear input flag:
				this->inFlag = false;
				this->inFlagLock.unlock();

                
                // Split contents: 
                char *splitPosition = NULL;
                char* splitPtr = strtok_r(rawCommand, ":", &splitPosition);
                    // NOTE: Use strtok_r instead of strtok for thread-safety
               
				/* DEBUG
				pl;printf(
					"\n\r[%08dms][P][D] Input: \n\r\t\"%s\"\n\r\tSplit: %s",
					tm, rawCommand, splitPtr);pu;
				*/

                // Verify splitting:
                if(splitPtr == NULL){
                    // Error:
                    pl;printf("\n\r[%08dms][P] ERROR: NULL splitPtr (1)",
                    tm);pu;

                    // Resume loop:
    				this->threadLock.unlock();
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

                        // Split contents for duty cycle:
                        splitPtr = strtok_r(NULL, ":", &splitPosition);

                        // Validate:
                        if(splitPtr == NULL){
                            // Error:
                            pl;printf(
                                "\n\r[%08dms][P] ERROR: NULL splitPtr (2)",
                                tm);pu;

                            // Ignore message:
    						this->threadLock.unlock();
                            continue;
                        } // End validate splitting

                        // Get float duty cycle:
                        float dutyCycle = atof(splitPtr);
						pl;printf("\n\r[%08dms][P] DC: %f",tm, dutyCycle);pu;

                        // Split contents for selected fans:
                        splitPtr = strtok_r(NULL, ":", &splitPosition);

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
    						this->threadLock.unlock();
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

								// Override Chaser, if any:
								this->fanArray[i].setTarget(NO_TARGET);
                            }
                        } // End assign duty cycles

                        pl;printf("\n\r[%08dms][P] Duty cycles assigned",tm);pu;

                        break;
					}
                    case CHASE: // Set a target RPM
					{
                        pl;printf("\n\r[%08dms][P] CHASE received",tm);pu;
					
                        // Split contents for duty cycle:
                        splitPtr = strtok_r(NULL, ":", &splitPosition);

                        // Validate:
                        if(splitPtr == NULL){
                            // Error:
                            pl;printf(
                                "\n\r[%08dms][P] ERROR: NULL splitPtr (2)",
                                tm);pu;

                            // Ignore message:
    						this->threadLock.unlock();
                            continue;
                        } // End validate splitting

                        // Get float duty cycle:
                        int target = atoi(splitPtr);
                        #ifdef DEBUG
						pl;printf("\n\r[%08dms][P] RPM: %d",tm, target);pu;
						#endif

                        // Split contents for selected fans:
                        splitPtr = strtok_r(NULL, ":", &splitPosition);

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
    						this->threadLock.unlock();
                            continue;
                        } // End validate splitting

                        // Get length of selection:
                        int numFans = strlen(splitPtr);
						
						#ifdef DEBUG
                        pl;printf("\n\r[%08dms][P] Fans: %s (%d)",
                            tm, splitPtr, numFans);pu;
						#endif

						// Calculate first-guess duty cycle:
						float dutyCycle = (target/(float)this->maxRPM);

						// Check in case of minimum RPM threshold:
						// (If requested a target below the minimum RPM)
						if(target < this->minRPM){
							dutyCycle = 0.0;
						}else if (target >= this->maxRPM){
							dutyCycle = 1.0;
						}

                        pl;printf("\n\r[%08dms][P][DEBUG] Linear-guess DC: "
						" (%d) / %lu = %.2f",tm, target, this->maxRPM, dutyCycle);pu;
                        // Loop over list and assign duty cycles:
                        for(int i = 0; i < numFans; i++){

                            // Check if the corresponding index is selected:
                            if(splitPtr[i] - '0'){
                             //\---------------/
                             // This expression will evaluate to 0 if the fan is
                             // set to 0, and nonzero (true) otherwise.

								// Make a first guess by assuming a linear fit:
                                this->fanArray[i].write(dutyCycle);

								// Override Chaser, if any:
								this->fanArray[i].setTarget(target);
                            }
                        } // End assign duty cycles

                        pl;printf("\n\r[%08dms][P] Linear-guess DC assigned",tm);pu;

                        break;
					}
                    default: // Unrecognized command:

                        // Issue error message and discard command:

                        pl;printf(
                            "\n\r[%08dms][P] ERROR: UNRECOGNIZED COMMAND: %c",
                            tm, splitPtr[0]);pu;

                } // End check command -----------------------------------------
                
            }else{
				// Nothing to process yet. Release input flag lock.
				//pl;printf("\n\r[%08dms][P][D] No input found",tm);pu;
				this->inFlagLock.unlock();
			} // End command processing ========================================


			this->outFlagLock.lock();
			if(not this->outFlag){
				#ifdef DEBUG
				pl;printf("\n\r[%08dms][P] DEBUG: Updating values",tm);pu;
				#endif
				// If the output buffer is free, write to it.

				
				// Update values: ==================================================
				int n = 0; // Keep track of string index
				
				// Increment data index:
				this->dataIndex++;
				
				// Print beginning of update message:	
				n+= snprintf(this->outBuffer, MAX_MESSAGE_LENGTH,"T|%lu|",
					this->dataIndex);

				// Update RPM's and Chase if applicable ------------------------
				
				if(not (writeCalled and rpmWritten)){
					// NOTE: Skip RPM writing if a DC was just set, to allow for 
					// fast feedback. Do this as long as there is some RPM value
					// in the buffer (i.e rpmWrite is true)	
					
					// Evaluate first fan separately due to special formatting

					Fan *fanPtr = NULL;
					int rpm = -1;
					int m = 0; 

					// Store other RPM's:
					
    				pl;printf("\n\r[%08dms][P] P-IN",tm);pu;
					for(int i = 0; i < activeFans; i++){
						// Loop over buffer and print out RPM's:
						
						fanPtr = &(this->fanArray[i]);
						rpm = fanPtr->read();

						// Chase first fan if applicable:
						if(
							// Fan is chasing:
							fanPtr->getTarget() > (int)this->minRPM &&
							// Fan is not close enough to target RPM:
							abs(rpm - fanPtr->getTarget()) > 
								this->maxRPM*this->chaserTolerance){
							
							// Check the conditions for an irresponsive fan:
							if( (not 
								// Fan is "stable"
								(fanPtr->getRPMChange() <
								this->maxRPM*this->chaserTolerance))
								// Fan reports no RPM although DC is above min.
								or (rpm == 0 and fanPtr->getDC() > this->minDC))
								{
								
								// If the fan has not stabilized, count a 
								// timeout and move on.

								if(fanPtr->incrementTimeouts()){
									// If the fan times out, set its RPM to
									// zero instantly (incrementTimeouts
									// automatically aborts Chase)
									rpm = 0;
								} // End check incrementTimeouts

							} else {

								// Adjust duty cycle:

								// Take percentage of max RPM represented by the 
								// current delta and adjust duty cycle by the
								// same percent. (i.e if 1% underneath, +1% DC)
								
								float increment = 
									(fanPtr->getTarget() - rpm)/(maxRPM);
								
								fanPtr->write(
									fanPtr->getDC() + increment);

								fanPtr->resetTimeouts();
							}
						} 
						
						m += snprintf(
						rpmBuffer + m, MAX_MESSAGE_LENGTH - m, "%d,", 
						rpm);
					}				
    				pl;printf("\n\r[%08dms][P] P-OUT",tm);pu;
					
					// Get rid of trailing comma:
					rpmBuffer[m-1] = '\0';
					rpmWritten = true;

				}
				// Save RPM buffer into output buffer
				n += snprintf(this->outBuffer + n, MAX_MESSAGE_LENGTH - n, "%s",
					rpmBuffer);

				// Store duty cycles: ----------------------------------------------

				// Store first duty cycle along w/ separator:
				 
				/*DEBUG 
				pl;printf("\n\r\t[P][D] output buffer: %s",
					outBuffer);pu;
				*/
				n += snprintf(this->outBuffer + n, MAX_MESSAGE_LENGTH - n, "|%.3f", 
					this->fanArray[0].getDC());
			

				// Store other duty cycles:
				for(int i = 1; i < activeFans; i++){
					// Loop over buffer and print out RPM's:
					n += snprintf(this->outBuffer + n, MAX_MESSAGE_LENGTH - n, ",%.4f", 
					this->fanArray[i].getDC());
					/*DEBUG
					 pl;printf("\n\r\t[P][D] output buffer: %s",
						outBuffer);pu;
					*/
				}
			
				// Raise output flag:
				this->outFlag = true;
				this->outFlagLock.unlock();
    			//pl;printf("\n\r[%08dms][P] P-OUT",tm);pu;
		} else {
			// If the output buffer is busy, wait until it has been freed.
    		
			/* DEBUG
			pl;printf("\n\r[%08dms][P] Output buffer busy",
        		tm);pu;

			*/
			this->outFlagLock.unlock();
		}
			
        } // End check if active = = = = = = = = = = = = = = = = = = = = = = = =
		
    	this->threadLock.unlock();
	} // End processor thread loop =============================================

    pl;printf("\n\r[%08dms][P] WARNING: BROKE OUT OF PROCESSOR THREAD LOOP",
        tm);pu;
} // End _processorRoutine // // // // // // // // // // // // // // // // // // 

void Processor::_setLED(int state){ // // // // // // // // // // // // // // /.
    /* ABOUT: Set LED state.
     */
	
	switch(state){
		case TOGGLE:
			// Alternate value of LED:
			this->led = !this->led;
			this->xled = this->led;
			break;
		
		case ON:
			this->led = true;
			this->xled = true;
			break;

		case OFF:
			this->led = false;
			this->xled = false;
			break;
	}
} // End _setLED // // // // // // // // // // // // // // // // // // // // // 
     
void Processor::_blinkLED(void){ // // // // // // // // // // // // // // // //
    /* ABOUT: To be set as ISR for blue LED Ticker to show status.
     */
	
	// Alternate value of LED:
	this->led = !this->led;
	this->xled = this->led;
} // End _blinkLED // // // // // // // // // // // // // // // // // // // // 
