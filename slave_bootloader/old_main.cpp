// OBSOLETE FILE. IGNORE DURING AUTOMATED COMPILATION 
#if 0

#include <errno.h>
#include "mbed.h"
#include "easy-connect.h"
#include "http_request.h"
#include "FATFileSystem.h"
#include "HeapBlockDevice.h"
#include "FlashIAP.h"

// Serial connection -----------------------------------------------------------
Serial PC(USBTX, USBRX, 460800);

// File storage ----------------------------------------------------------------
HeapBlockDevice bd(1024*72, 512);
FATFileSystem fs("fs");

/*
void return_error(int ret_val){
  if (ret_val)
    printf("Failure. %d\r\n", ret_val);
  else
    printf("done.\r\n");
}

void errno_error(void* ret_val){
  if (ret_val == NULL)
    printf(" Failure. %d \r\n", errno);
  else
    printf(" done.\r\n");
}
*/

// FlashIAP --------------------------------------------------------------------
FlashIAP flash;

void apply_update(FILE *file, uint32_t address){
    fseek(file, 0, SEEK_END);
    long len = ftell(file);
    printf("Firmware size is %ld bytes\r\n", len);
    fseek(file, 0, SEEK_SET);
  
    flash.init();

    const uint32_t page_size = flash.get_page_size();
    char *page_buffer = new char[page_size];
    uint32_t addr = address;
    uint32_t next_sector = addr + flash.get_sector_size(addr);
    bool sector_erased = false;
    size_t pages_flashed = 0;
    uint32_t percent_done = 0;
    
	wait(0.2);
	printf("\n\rpage_size: %u, sector_size: %d",
		flash.get_page_size(), flash.get_sector_size(addr));
	
	wait(3);

	while (true) {
		
		// Read data for this page
        /*printf("\n\r[639] memset(page_buffer: %x, 0, sizeof(page_buffer): %u): %x",
			page_buffer,
			sizeof(page_buffer),
			memset(page_buffer, 0, sizeof(page_buffer)));
		*/
		memset(page_buffer, 0, sizeof(page_buffer));
		/*printf("\n\r[644] fread(page_buffer: %x, 1, page_size: %u, file: %x)",
			page_buffer, page_size, file);
		*/
		//printf("\n\r[647] ferror: %d", ferror(file));

        int size_read = fread(page_buffer, 1, page_size, file);

		//printf("\n\r[648] size_read: %d\n\r", size_read);
        if (size_read <= 0) {
            break;
        }

        // Erase this page if it hasn't been erased
        if (!sector_erased) {
            /*printf("\n\r[647] flash.erase(addr: %u, flash.get_sector_size(addr): %u): %d",
				addr, flash.get_sector_size(addr),
				flash.erase(addr, flash.get_sector_size(addr)) );
			*/
			flash.erase(addr, flash.get_sector_size(addr));
            sector_erased = true;
        }
		

        // Program page
        /*printf("\n\r[654] flash.program(page_buffer: %s, addr: %u, page_size: %u)",
			page_buffer,
			addr,
			page_size,
			flash.program(page_buffer, addr, page_size) );
		*/
		flash.program(page_buffer, addr, page_size);
        
		addr += page_size;
        if (addr >= next_sector) {
            next_sector = addr + flash.get_sector_size(addr);
            sector_erased = false;
        }

        if (++pages_flashed % 3 == 0) {
            uint32_t percent_done_new = ftell(file) * 100 / len;
            if (percent_done != percent_done_new) {
                percent_done = percent_done_new;
                printf("Flashed %3ld%%\r", percent_done);
            }
        }
    }
    printf("Flashed 100%%\r\n");

    delete[] page_buffer;

    flash.deinit();
}

// -----------------------------------------------------------------------------

NetworkInterface* network;
EventQueue queue;
InterruptIn btn(USER_BUTTON);

FILE* file;
size_t received = 0;
size_t received_packets = 0;
void store_fragment(const char* buffer, size_t size) {
    fwrite(buffer, 1, size, file);

    received += size;
    received_packets++;

    if (received_packets % 20 == 0) {
        printf("Received %u bytes\n", received);
    }
}




void check_for_update() {
	//btn.fall(NULL); // remove the button listener

    file = fopen("/fs/a.bin", "wb");

    HttpRequest* req = new HttpRequest(network, HTTP_GET, "http://192.168.1.3:8000/a.bin", &store_fragment);

    HttpResponse* res = req->send();
    if (!res) {
        printf("HttpRequest failed (error code %d)\n", req->get_error());
        return;
    }

    printf("Done downloading: %d - %s\n", res->get_status_code(), res->get_status_message().c_str());

    fclose(file);

    delete req;
	
	
	file = fopen("/fs/a.bin", "rb");
	apply_update(file, POST_APPLICATION_ADDR);

	fclose(file);
	
	printf("Starting application...\r\n");
   
	
	fs.unmount();
	//bd.deinit();

	mbed_start_application(POST_APPLICATION_ADDR);

}


// Filesystem error-checking ---------------------------------------------------
void return_error(int ret_val){
  if (ret_val)
    printf("Failure. %d\r\n", ret_val);
  else
    printf("done.\r\n");
}

void errno_error(void* ret_val){
  if (ret_val == NULL)
    printf(" Failure. %d \r\n", errno);
  else
    printf(" done.\r\n");
}


#define G

#ifdef G
DigitalOut led(LED1);
#endif
#ifdef B
DigitalOut led(LED2);
#endif
#ifdef R
DigitalOut led(LED3);
#endif


void blink_led() {
    led = !led;
}

int main() {
    printf("\n\rHello from THE ORIGINAL application\n");

	
    printf("\n\rStarting event thread");
    //Thread eventThread;
    //eventThread.start(callback(&queue, &EventQueue::dispatch_forever));
    //queue.call_every(500, &blink_led);
	led = 1;

    //printf("\n\rAttaching button callback");
    //btn.mode(PullUp); // PullUp mode on the ODIN W2 EVK
    //btn.fall(queue.event(&check_for_update));


    printf("\n\rMounting filesystem");
    int r;
    if ((r = bd.init()) != 0) {
        printf("\n\rCould not initialize Heap BD (%d)", r);
        return 1;
    }
	
    int error = 0;
    printf("\n\r\tFormatting a FAT, RAM-backed filesystem. ");
    error = FATFileSystem::format(&bd);
    return_error(error);

    if ((r = fs.mount(&bd)) != 0) {
        printf("\n\rCould not mount filesystem, is the SD card formatted as FAT? (%d)", r);
        return 1;
    }

    // Connect to the network (see mbed_app.json for the connectivity method used)
    
    printf("\n\rConnecting to network");
	network = easy_connect(true);

    if (!network) {
        printf("\n\rCannot connect to the network, see serial output");
        return 1;
    }

    //printf("\n\rPress SW0 to check for update");
	check_for_update();

    wait(osWaitForever);
}



#endif // #if 0
