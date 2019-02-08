################################################################################
## Project: Fanclub Mark IV "Master" build script ## File: makefile           ##
##----------------------------------------------------------------------------##
## CALIFORNIA INSTITUTE OF TECHNOLOGY ## GRADUATE AEROSPACE LABORATORY ##     ##
## CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES                      ##     ##
##----------------------------------------------------------------------------##
##      ____      __      __  __      _____      __      __    __    ____     ##
##     / __/|   _/ /|    / / / /|  _- __ __\    / /|    / /|  / /|  / _  \    ##
##    / /_ |/  / /  /|  /  // /|/ / /|__| _|   / /|    / /|  / /|/ /   --||   ##
##   / __/|/ _/    /|/ /   / /|/ / /|    __   / /|    / /|  / /|/ / _  \|/    ##
##  / /|_|/ /  /  /|/ / // //|/ / /|__- / /  / /___  / -|_ - /|/ /     /|     ##
## /_/|/   /_/ /_/|/ /_/ /_/|/ |\ ___--|_|  /_____/| |-___-_|/  /____-/|/     ##
## |_|/    |_|/|_|/  |_|/|_|/   \|___|-    |_____|/   |___|     |____|/       ##
##                   _ _    _    ___   _  _      __  __   __                  ##
##                  | | |  | |  | T_| | || |    |  ||_ | | _|                 ##
##                  | _ |  |T|  |  |  |  _|      ||   \\_//                   ##
##                  || || |_ _| |_|_| |_| _|    |__|  |___|                   ##
##                                                                            ##
##----------------------------------------------------------------------------##
## Alejandro A. Stefan Zavala ## <astefanz@berkeley.edu>   ##                 ##
## Chris J. Dougherty         ## <cdougher@caltech.edu>    ##                 ##
## Marcel Veismann            ## <mveisman@caltech.edu>    ##                 ##
################################################################################

## DETECT PLATFORM #############################################################
# See:
# https://gist.github.com/sighingnow/deee806603ec9274fd47

# Detect operating system in Makefile.
# Author: He Tao
# Date: 2015-05-30

ifeq ($(OS),Windows_NT)
	OSFLAG = win32
	ifeq ($(PROCESSOR_ARCHITECTURE),AMD64)
		ARCH = AMD64
	endif
	ifeq ($(PROCESSOR_ARCHITECTURE),x86)
		ARCH = IA32
	endif
else
	UNAME_S := $(shell uname -s)
	ifeq ($(UNAME_S),Linux)
		OSFLAG = linux
	endif
	ifeq ($(UNAME_S),Darwin)
		OSFLAG = osx
	endif
		UNAME_P := $(shell uname -p)
	ifeq ($(UNAME_P),x86_64)
		ARCH = AMD64
	endif
	ifneq ($(filter %86,$(UNAME_P)),)
		ARCH = IA32
	endif
	ifneq ($(filter arm%,$(UNAME_P)),)
		ARCH = ARM
	endif
endif
## DEFINE OS-DEPENDENT VARIABLES ###############################################
DPATH = dist/$(OSFLAG)/
ifeq ($(OSFLAG),osx)
	IPATH = resource/osx.icns
else
	IPATH = resource/$(OSFLAG).ico
endif

## DEFINE GENERAL VARIABLES ####################################################
M = "[No message given]"

## MAIN ########################################################################

default: unit build clean

warn:
	@echo "WARNING: See PyInstaller Platform-specific notes"
# See: https://pyinstaller.readthedocs.io/en/stable/
#   usage.html#supporting-multiple-platforms
	@echo "REMINDER: Check PyInstaller bytecode encryption"
	@echo "REMINDER: Use 'peek' flag for basic integration testing"

build: warn
	@echo "WARNING: No icons yet"
	python3 -OO -m PyInstaller \
        --clean --onefile --noconsole --name FanClub main.py --distpath=$(DPATH)

unit:
	python3 -m unittest

check:
	@echo "WARNING: empty check recipe"

clean:
	rm -rf *.pyc *.spec build __pycache__ */__pycache__

wipe: clean
	rm -rf dist

save: wipe
	@echo Committing and pushing changes with message \"$(M)\"
	@echo git add -a && git commit -m "$(M)" && git push
