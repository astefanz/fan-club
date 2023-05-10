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

// MkII:
#include "BTUtils.h"

// Mbed:
#include "FlashIAP.h"
#include "mbed.h"

namespace BTFlash{

FlashIAP flashIAP;

////////////////////////////////////////////////////////////////////////////////

/* Flash given file into the given application address in flash memory.
 */
void flash(char storage[], uint32_t amount, uint32_t address){
	printf("\tFirmware size is %lu B\n\r", amount);

    const uint32_t page_size = flashIAP.get_page_size();
    char *page_buffer = new char[page_size];
    uint32_t addr = address;
    uint32_t next_sector = addr + flashIAP.get_sector_size(addr);
    bool sector_erased = false;
    size_t pages_flashed = 0;
    uint32_t percent_done = 0;
	int result = -666; // Store returned codes for error checking

	/* DEBUG
	printf("\t Page size: %uB \n\r\tSector size: %dB\n\r",
		flashIAP.get_page_size(), flash.get_sector_size(addr));
	*/
	
	putchar('\n');
	uint32_t copied = 0;
	uint32_t count = 0;
	while (count < amount) {
		if(count%20 ==0) printf("\r\tFlashing");

		// Read data for this page
		memset(page_buffer, 0, sizeof(page_buffer));
        
		for(uint32_t i = 0; i < page_size; i++){
			page_buffer[i] = storage[count + i];
			copied++;
		}


        // Erase this page if it hasn't been erased
        if (!sector_erased) {
			result = flashIAP.erase(addr, flashIAP.get_sector_size(addr));
        	if (result != 0){
				printf("\n\r\tError (%d) while erasing on %lx\n\r",
					result, addr);

				// Error erasing
				break;
			}
			sector_erased = true;
        }
		

        // Program page
		result = flashIAP.program(page_buffer, addr, page_size);
		if (result != 0){
			// Error erasing
			printf("\n\r\tError (%d) while writing on %lx\n\r",
				result, (long int)addr);

			break;
		}
        

		addr += page_size;
        if (addr >= next_sector) {
            next_sector = addr + flashIAP.get_sector_size(addr);
            sector_erased = false;
        }

		pages_flashed++;
        if (count % 20 == 0) {
            uint32_t percent_done_new = count * 100 / amount;
            if (percent_done != percent_done_new) {
                percent_done = percent_done_new;
                printf("%lu/%lu [%3ld%%]", count, amount, percent_done);
            }
        }

		count++;
    }

    delete[] page_buffer;

	printf("\n\r\tFlashed %lu/%lu [%3ld%%]", count, amount, count*100/amount);

	return;

} // End flash

/* Copy data from one side of flash to the other.
 */
void copy(uint32_t from, uint32_t amount, uint32_t to,
	char errorBuffer[], size_t errorBufferSize){
	
	printf("\tFirmware size is %lu B. \n\r"\
		"Copying from [0x%lx, 0x%lx] to [0x%lx, 0x%lx]",
		amount, from, from + amount, to, to + amount);

    const uint32_t page_size = flashIAP.get_page_size();
    char *page_buffer = new char[page_size];
    uint32_t addr = to;
    uint32_t next_sector = addr + flashIAP.get_sector_size(addr);
    bool sector_erased = false;
    size_t pages_flashed = 0;
	int result = -666; // Store returned codes for error checking

	/* DEBUG
	printf("\t Page size: %uB \n\r\tSector size: %dB\n\r",
		flashIAP.get_page_size(), flash.get_sector_size(addr));
	*/
	
	putchar('\n');
	putchar('\r');
	uint32_t count = 0;
	errorBuffer[0] = '\0';
	while (addr < from + amount) {
		
		// Read data for this page
		memset(page_buffer, 0, sizeof(page_buffer));
        
		flashIAP.read(page_buffer, from + count, page_size);
		count += page_size;

        // Erase this page if it hasn't been erased
        if (!sector_erased) {
			printf("\n\n\r\tErasing sector on 0x%lx", addr);
			result = flashIAP.erase(addr, flashIAP.get_sector_size(addr));
        	if (result != 0){
				printf("(got %d)\n\r",
				result);
				// NOTE: error code occurs when erasing previously erased flash
				// (benign)
				// Error erasing
				//BTUtils::fatal();
			//	break;
			} else{
				printf("\n\r");
			}
			sector_erased = true;
        }
		

        // Program page
		result = flashIAP.program(page_buffer, addr, page_size);
		if (result != 0){
			// Error erasing
			snprintf(errorBuffer, errorBufferSize,
				"Error (%d) while writing on 0x%lx",
				result, addr);
			
			break;
		}
        

		addr += page_size;
        if (addr >= next_sector) {
            next_sector = addr + flashIAP.get_sector_size(addr);
            sector_erased = false;
        }

		pages_flashed++;
        if (count % 256 == 0) {
                printf("\r\t [0x%lx -> 0x%lx]",
					addr, from + amount);
				BTUtils::setLED(BTUtils::MID, BTUtils::TOGGLE);
            }

    }

    delete[] page_buffer;
	printf("\r\tDone. Dest: [0x%lx, 0x%lx] Source: [0x%lx, 0x%lx]",
		addr, from + amount, to + addr - from, to + amount);
	BTUtils::setLED(BTUtils::MID, BTUtils::ON);

	if(addr != from + amount and errorBuffer[0] == '\0'){
		// If there is a mismatch in the amount of bytes counted and what is
		// supposed to have been written, and there is no previous error
		// recorded, then something else has gone wrong.

		snprintf(errorBuffer, errorBufferSize, 
			"Flash error -- address mismatch: expected 0x%lx, got 0x%lx",
			from + amount, addr);
	}
 
	return;

} // End flash
} // End namespace

#endif // BTFLASH_H
