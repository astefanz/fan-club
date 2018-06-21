////////////////////////////////////////////////////////////////////////////////
// Project: Fanclub Mark II "Bootloader" // File: BTCommunicator.h            //
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

#ifndef BTCOMMUNICATOR_H
#define BTCOMMUNICATOR_H

class EthernetInterface;
class UDPSocket;
class SocketAddress;

class BTDownloader;

enum BTCode {START, UPDATE, REBOOT};

class BTCommunicator{
public:
	/*	Constructor for class BTCommunicator. Sets up networking and starts
	 *	threads. Will reboot MCU upon network failure. 
	 */
	BTCommunicator(int socketTimeoutMS, int maxRebootTimeouts
		uint16_t listenerPort, uint16_t misoPort, uint16_t mosiPort);
	
	/*	Destructor for class BTCommunicator. 
	 */
	~BTCommunicator(void);

	/* Listen listen for broadcast and return integer result code.
	 */
	BTCode listen(uint16_t bufferSize);
	
	/* Download firmware into given file (opened w/ binary write).
	 */
	bool download(FILE* file, char errormsg[], int msglength);

	/* Send error message to Master
	 */
	int error(char message[], int msglength) const;

private:

	// Network attributes:
	EthernetInterface ethernet;
	UDPSocket listenerSocket;
	SocketAddress masterBroadcastAddress;
	uint16_t listenerPort;
	uint16_t misoPort;
	uint16_t updatePort;
	int socketTimeoutMS, 
	int maxRebootTimeouts;
	bool networkError;
	char passwordBuffer[32];

	// FCMkIIB:
	BTDownloader downloader;
};

#endif // BTCOMMUNICATOR_H
