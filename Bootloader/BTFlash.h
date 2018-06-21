////////////////////////////////////////////////////////////////////////////////
// Project: Fanclub Mark II "Bootloader" // File: BTFlash.h                   //
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
// Alejandro A. Stefan Zavala // <astefanz@berkeley.com> //                   //
////////////////////////////////////////////////////////////////////////////////

#ifndef BTFLASH_H
#define BTFLASH_H

// ABOUT: Repository of functions and definitions for flashing downloaded 
// firmware.

// SEE 
// https://github.com/ARMmbed/mbed-os-example-bootloader
// https://os.mbed.com/docs/v5.9/tutorials/bootloader.html



//// INCLUDES //////////////////////////////////////////////////////////////////

// Mbed:
#include "FlashIAP.h"
#include "DigitalIn.h"
#include "mbed.h"

namespace BTFlash{
////////////////////////////////////////////////////////////////////////////////

/* Flash given file into the given application address in flash memory.
 */
void flash(FILE* file, uint32_t address, char errormsg[], int msglength){
	FlashIAP flashIAP;
	
	fseek(file, 0, SEEK_END);https://os.mbed.com/docs/v5.9/tutorials/bootloader.html
	long len = ftell(file);

	if(debug.get())	printf("\tFirmware size is %ldB\n\r", len);
	
    flash.init();

    const uint32_t page_size = flash.get_page_size();
    char *page_buffer = new char[page_size];
    uint32_t addr = address;
    uint32_t next_sector = addr + flash.get_sector_size(addr);
    bool sector_erased = false;
    size_t pages_flashed = 0;
    uint32_t percent_done = 0;
	int result = -666 // Store returned codes for error checking
	bool success = false;

	printf("\t Page size: %uB \n\r\tSector size: %dB\n\r",
		flash.get_page_size(), flash.get_sector_size(addr));

	
	while (true) {
		
		memset(page_buffer, 0, sizeof(page_buffer));
        int size_read = fread(page_buffer, 1, page_size, file);

        if (size_read <= 0) {
			errorhttps://os.mbed.com/docs/v5.9/tutorials/bootloader.htmlmsg[0] = '\0'; 
		    printf("\tFlashed 100%%\n\tDone\r");
            break;
        }

        // Erase this page if it hasn't been erased
        if (!sector_erased) {
			result = flash.erase(addr, flash.get_sector_size(addr));
        	if (result != 0){
				// Error erasing
				snprintf(errormsg, msglenth "Error (%d) while erasing on %x",
					result, addr);
				break;
			}
			sector_erased = true;
        }
		

        // Program page
		result = flash.program(page_buffer, addr, page_size);
		if (result != 0){
			// Error erasing
			snprintf(errormsg, msglength, "Error (%d) while writing on %x",
				result, addr);
			break;
		}
        

		addr += page_size;
        if (addr >= next_sector) {
            next_sector = addr + flash.get_sector_size(addr);
            sector_erased = false;
        }

        if (++pages_flashed % 3 == 0) {
            uint32_t percent_done_new = ftell(file) * 100 / len;
            if (percent_done != percent_done_new) {
                percent_done = percent_done_new;
                printf("\tFlashed %3ld%%\r", percent_done);
            }
        }
    }

    delete[] page_buffer;
    flash.deinit();

	return;

} // End flash

} // End namespace

#endif // BTFLASH_H
