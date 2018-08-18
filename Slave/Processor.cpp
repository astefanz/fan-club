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
    processorThread(
		osPriorityNormal, 
		STACK_SIZE * 1024, /*16K stack size*/
		NULL, // Stack memory
		"PROS" // Name
	),
	dataIndex(0),  

	pastDutyCycle(-1.0),

	interrupt(PD_3),
	led(LED2),
	#ifndef JPL
	xled(D4),
	psuOff(D9),
	#endif
	inFlag(false), 
	outFlag(false)
	{
    /* ABOUT: Constructor for class Processor. Starts processor thread.
     */
	
    pl;printf("\n\r[%08dms][p] Processor initialized",tm);pu;

	this->pastSelection[0] = '\0';

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
		// Standard usage. Execute command
		
			//pl;printf("\n\r[%08dms][P][D] Input found",tm);pu;

			// Get command contents:
			strcpy(this->inBuffer, givenCommand);
				// NOTE: Destroy obsolete message

			// Split contents: 
			char *splitPosition = NULL;
			char* splitPtr = strtok_r(this->inBuffer, ":", &splitPosition);
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
				return false;

			} // End verify splitting.
			
			// Check command: ----------------------------------------------
			char commandCode = splitPtr[0];
			switch(commandCode){

				case WRITE: // Set fan duty cycles
				{
					pl;printf("\n\r[%08dms][P] WRITE received",tm);pu;
				
					// Split contents for duty cycle:
					splitPtr = strtok_r(NULL, ":", &splitPosition);

					// Validate:
					if(splitPtr == NULL){
						// Error:
						pl;printf(
							"\n\r[%08dms][P] ERROR: NULL splitPtr (2)",
							tm);pu;

						// Ignore message:
						return false;

					} // End validate splitting

					// Get float duty cycle:
					float dutyCycle = atof(splitPtr);

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
						return false;
					} // End validate splitting

					// Get length of selection:
					int numFans = strlen(splitPtr);
			
					// Check for redundant writes:
					if(dutyCycle == this->pastDutyCycle and \
						strcmp(splitPtr, this->pastSelection) == 0){
					
						pl;printf("\n\r[%08dms][P] No new WRITEs",tm);pu;
						
						// Redundant write.. ignore
						return true;
						 
					} else {

						// Loop over list and assign duty cycles:
						this->arrayLock.lock();
						for(int i = 0; i < numFans; i++){

							// Check if the corresponding index is selected:
							if(splitPtr[i] - '0'){
							 //\---------------/
							 // This expression will evaluate to 0 if the fan is
							 // set to 0, and nonzero (true) otherwise.
								this->fanArray[i].write(dutyCycle);

							}
						} // End assign duty cycles
						this->arrayLock.unlock();

						pl;printf("\n\r[%08dms][P] New WRITE applied: "\
							"\n\r\tDC: %f"\
							"\n\r\tFans: %s (%d)",
							tm,
							dutyCycle,
							splitPtr,
							numFans
						);pu;

						this->pastDutyCycle = dutyCycle;
						strcpy(this->pastSelection, splitPtr);

						return true;

					} // End check redundance

				} // End WRITE
				
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
						return false;
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
						return false;
					} // End validate splitting

					// Get length of selection:
					int numFans = strlen(splitPtr);
					
					#ifdef DEBUG
					pl;printf("\n\r[%08dms][P] Fans: %s (%d)",
						tm, splitPtr, numFans);pu;
					#endif

					// Calculate first-guess duty cycle:
					float dutyCycle = (target/(float)this->maxRPM);


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
						}
					} // End assign duty cycles

					pl;printf("\n\r[%08dms][P] Linear-guess DC assigned",tm);pu;

					return true;

				}
				
				default: // Unrecognized command:

					// Issue error message and discard command:

					pl;printf(
						"\n\r[%08dms][P] ERROR: UNRECOGNIZED COMMAND: %c",
						tm, splitPtr[0]);pu;

					return false;

			} // End check command -----------------------------------------
	
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

void Processor::start(void){ // // // // // // // // // // // // // // // // //
    // Start processor thread:
    this->processorThread.start(callback(this, 
        &Processor::_processorRoutine));
        
} // End Processor::start // // // // // // // // // // // // // // // // // // 

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
    } else {
	
		this->threadLock.lock();

		// Change status:
		switch(status){
			
			case ACTIVE: // Processor active -----------------------------------
				
				// Set internal status:
				this->status = ACTIVE;
				// Update LED blinking:
					// Solid blue
				this->_setLED(ON);
				#ifndef JPL
				this->psuOff.write(false);
				#endif
				

				break;

			case OFF: // Processor offline -------------------------------------
				
				// Set internal status:
				this->status = status;
				#ifndef JPL

				this->psuOff.write(true);
				#endif
				this->_setLED(OFF);

				// Reset data index:
				this->dataIndex = 0;
	   
				// Reset buffers and flags:

				// Output:
				this->outFlagLock.lock();
				this->outBuffer[0] = '\0';
				this->outFlag = false;
				this->outFlagLock.unlock();

				break;

			default: // Unrecognized status code -------------------------------
				// Print error message:
				pl;printf("\n\r[%08dms][P] ERROR: UNRECOGNIZED STATUS CODE %d", 
					tm, status);pu;

		} // End switch

		this->threadLock.unlock();

	} // End redundancy check

} // End setStatus // // // // // // // // // // // // // // // // // // // // /

// INNER THREAD ROUTINES -------------------------------------------------------
void Processor::_processorRoutine(void){ // // // // // // // // // // // // // 
    /* ABOUT: To be executed by this Processor's processor thread.
     */

	this->threadID = (uint32_t)Thread::gettid();

    // Thread setup ============================================================
    pl;printf("\n\r[%08dms][P] Processor thread started",tm);pu;

    // Prepare placeholders: ---------------------------------------------------
	char rpmBuffer[MAX_MESSAGE_LENGTH]; // Save last RPM value

    // Thread loop =============================================================
    while(true){
		
		// DEBUG: PRINT STACK OF PROCESSOR THREAD
		#ifdef STACK_PRINTS // -------------------------------------------------
		pl;printf(
			"\n\r\tPROS (%10X): Used: %6lu Size: %6lu Max: %6lu",
			this->threadID,
			this->processorThread.used_stack(),
			this->processorThread.stack_size(),
			this->processorThread.max_stack()
		);pu;
		#endif // STACK_PRINTS -------------------------------------------------
		
		this->threadLock.lock();

        // Check if active = = = = = = = = = = = = = = = = = = = = = = = = = = =
		if(this->status ==  OFF){
			// Reset values

            // Processor off, set all fans to zero. (Safety redundancy)
			
            for(int i = 0; i < MAX_FANS; i++){
                this->fanArray[i].write(0);

            } // End set all fans to zero
			
        } else{
			// Processor active. Update values
			
			this->_setLED(TOGGLE);

			this->outFlagLock.lock();

			if(not this->outFlag) {
				// If the output buffer is free, write to it.

				int n = 0; // Keep track of string index
				
				// Increment data index:
				this->dataIndex++;
				
				// Print beginning of update message:	
				n+= snprintf(this->outBuffer, MAX_MESSAGE_LENGTH,"T|%lu|",
					this->dataIndex);
				
				Fan *fanPtr = NULL;
				int rpm = -1;
				int m = 0; 

				// Store RPM's:-------------------------------------------------
				for(int i = 0; i < activeFans; i++){
					// Loop over buffer and print out RPM's:
					
					this->arrayLock.lock();
					fanPtr = &(this->fanArray[i]);
					rpm = fanPtr->read(
						this->timer, 
						this->timeout, 
						this->interrupt
					);
					this->arrayLock.unlock();
					
					m += snprintf(
					rpmBuffer + m, MAX_MESSAGE_LENGTH - m, "%d,", 
					rpm);

				} // End RPM read loop
				
				// Get rid of trailing comma:
				rpmBuffer[m-1] = '\0';

				// Save RPM buffer into output buffer
				n += snprintf(this->outBuffer + n, MAX_MESSAGE_LENGTH - n, "%s",
					rpmBuffer);

				// Store duty cycles: ------------------------------------------

				// Store first duty cycle along w/ separator:
				 
				/*DEBUG 
				pl;printf("\n\r\t[P][D] output buffer: %s",
					outBuffer);pu;
				*/
				n += snprintf(this->outBuffer + n, MAX_MESSAGE_LENGTH - n, 
					"|%.4f", this->fanArray[0].getDC());

				// Store other duty cycles:
				for(int i = 1; i < activeFans; i++){
					// Loop over buffer and print out RPM's:
					this->arrayLock.lock();
					n += snprintf(this->outBuffer + n, MAX_MESSAGE_LENGTH - n, 
					",%.4f", this->fanArray[i].getDC());
					this->arrayLock.unlock();
				} // End duty cycle storage loop

				// Raise output flag:
				this->outFlag = true;

			} // End check output flag 			

			this->outFlagLock.unlock();
			
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
			#ifndef JPL
			this->xled = this->led;
			#endif
			break;
		
		case ON:
			this->led = true;
			#ifndef JPL
			this->xled = true;
			#endif
			break;

		case OFF:
			this->led = false;
			#ifndef JPL
			this->xled = false;
			#endif
			break;
	}
} // End _setLED // // // // // // // // // // // // // // // // // // // // // 
     
void Processor::_blinkLED(void){ // // // // // // // // // // // // // // // //
    /* ABOUT: To be set as ISR for blue LED Ticker to show status.
     */
	
	// Alternate value of LED:
	this->led = !this->led;
	#ifndef JPL
	this->xled = this->led;
	#endif
} // End _blinkLED // // // // // // // // // // // // // // // // // // // // 
