#include "mbed.h"

InterruptIn *interruptInPtr = NULL;
DigitalOut led(D5);

void isr(void){
	led = !led;
}

DigitalOut PSUOFF(D9);

int main(){

	PSUOFF.write(false);

	interruptInPtr = new InterruptIn(USER_BUTTON);
	interruptInPtr->rise(callback(&isr));

	while(true);

	return 0;
}
