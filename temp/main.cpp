#include <mbed.h>
DigitalOut led(LED1);

int main(){
	while(true){
		led = !led;
		wait(0.1);
	}
	return 0;
}
