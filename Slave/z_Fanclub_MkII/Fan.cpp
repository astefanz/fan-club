////////////////////////////////////////////////////////////////////////////////
// INIT. TUESDAY, AUGUST 22ND, 2017  | FILE Fan.cpp
// ALEJANDRO A. STEFAN ZAVALA | CALIFORNIA INSTITUTE OF TECHNOLOGY | GALCIT
//
// FANCLUB MARK ONE | FAN OBJECT MODULE IMPLEMENTATION FILE
////////////////////////////////////////////////////////////////////////////////

/*******************************************************************************
 * ABOUT: This file contains the implementation of the interface defined in 
 * Fan.h
 *******************************************************************************
 */
 
#include "Fan.h"
 
// CLASS IMPLEMENTATION ////////////////////////////////////////////////////////

// CONSTRUCTORS AND DESTRUCTORS

Fan::Fan(){
    initialized = false;    
}

Fan::Fan(PwmOut pwm, PinName tach, int p, int max, int min, bool test){
    
    pwmPin = new PwmOut(pwm);
    period = p;
    (*pwmPin).period_us(period);
    tachPin = tach;
    initialized = true;
    maxRPM = max;
    minRPM = min;
    active = true; // Set by default
    write(0,0,NO_DEBUG);
    
}

Fan::~Fan(){
    delete pwmPin;    
}

// READ AND WRITE

int Fan::read(bool debug){

    if(initialized) {
        
        Counter counter(tachPin); // Create temporary Counter
        int result = counter.read();

        return result;
    }
    else {

        return -1;    
    }

}

float Fan::write(float newPwm, int waitTime, bool debug){

    if(initialized){

        *pwmPin = newPwm;
        pwm = newPwm;
  
        wait(waitTime);
        return pwm;
    }
    else{
  
        return -1;  
    }
}

// GETTERS AND SETTERS

     
int Fan::getMaxRPM(void){

     return maxRPM;    
}

int Fan::getMinRPM(void){

     return minRPM;    
}

int Fan::getPeriod(void){

     return period;
}

float Fan::getPWM(void){

     if(initialized){
        return pwm;    
     }
     else {
        return -1;    
     }
}

bool Fan::testActivity(int waitTime, bool debug){

     if(initialized){ // Check whether fan is initialized in the first place
  
        write(0.1, waitTime, debug); // Set this fan to 10%
        int rpm = read(debug);
        if ( rpm > minRPM){ // Check whether fan has responded
  
            active = true; // Set this fan as active
            return true;
        }
        else{ // If fan did not respond...

            active = false; // Set this fan as inactive
            return false;
            
        }
     }
     else{ // If the fan is not initialized, its activity is irrelevant, as it
           // is out of reach
        
        return false;
         
     }
     
}

bool Fan::isActive(void){

     
     return active;
    
}

void Fan::setPeriod(int p){
  
     period = p;
     (*pwmPin).period_us(period);
}

void Fan::setPins(PwmOut pwm, PinName tach, int max, int min){

    pwmPin = new PwmOut(pwm);
    tachPin = tach;
    initialized = true;
    maxRPM = max;
    minRPM = min;
    write(0);
}






