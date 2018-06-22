
#include "HeapBlockDevice.h"
#include "LittleFileSystem.h"
#include "FileHandle.h"
#include "mbed.h"

#define MODE "CPP"
#define CPPM

HeapBlockDevice bd(1024*160, 512);
LittleFileSystem fs("fs");

Serial PC(USBTX, USBRX, 460800);

int main(){

	printf("Filesystem experiment launched. Using %s mode\n\r",
		MODE);

	printf("Initializing filesystem and block device\n\r");
	printf("\tBD Initializd: %d\n\r", bd.init());
	printf("\tBD Formatted: %d\n\r", 
		LittleFileSystem::format(&bd));
	printf("\tFS Mounted: %d\n\r", fs.mount(&bd));

	#ifdef CM
	

	// Create file
	FILE* file;
	file = fopen("/fs/a.txt","wb");

	printf("\n\rFile created: %s", file == NULL? "NULL":"OK");

	// Write file
	printf("\n\rWriting: ");
	char chars[3] = ".!";
	uint32_t count = 0;
	while(count++ < 140000){
		fwrite(chars, 1, 1, file);
		printf("\rWriting: %5d [%3d]", count, ferror(file));

		if (ferror(file)){
			perror("\n\rFILE ERROR: ");
			break;
		}
	}
	fwrite(chars + 1, 1, 1, file);
	fclose(file);

	// Scan file
	file = fopen("/fs/a.txt", "rb");
	fseek(file, 0, SEEK_END);
	printf("\n\rftell: %lu\n\r", ftell(file));
	fseek(file, 0, SEEK_SET);

	// Read file
	printf("Printing file: ");
	while(feof(file) == 0 and ferror(file) == 0){
		putchar(fgetc(file));
	}
	printf("\n\r Done");

	printf("\n\rftell: %lu\n\r", ftell(file));
	fclose(file);
	#endif // CM

	#ifdef CPPM
	
	printf("Creating FileHandle: \n\r");
	const char* path = "/fs/a.txt";
	FileHandle* fhp = fs.open((const char*)path, O_RDWR | O_CREAT);
	//fs.open(&fhp, "/fs/a.txt", O_RDWR | O_CREAT);
	if (fhp == NULL){
		printf("\tERROR: Null FileHandle");
		return 0;
	}


	// Write file
	printf("\n\rWriting: ");
	char chars[3] = ".!";
	uint32_t count = 0;
	while(count++ < 140000){
		ssize_t s = fhp->write(chars, 1);
		printf("\rWriting: %5d [%3d]", count, int(s));

		if (s < 0){
			printf("\n\rFILE ERROR: %d", int(s));
			break;
		}
	}

	printf("Done\n\rFile length: %d\n\r", int(fhp->flen()));


	#endif // CPPM

	return 0;
}
