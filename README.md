# Fan Club MkIV

Alejandro A. Stefan-Zavala `aastefan@caltech.edu`

We're in the process of open-sourcing this repository, which has been in development since 2017 within GALCIT, at Caltech. ==This documentation is incomplete.==

![](/home/asz/Dropbox/Research/fan-club/doc/screenshots/fcmkiv_screenshot_donut.png)

## Quickstart [incomplete]

1. Flash microcontrollers. This version only supports **NUCLEO F429ZI** boards. NUCLEO F439ZI boards appear to work too, but have not been tested. There's a pre-compiled binary in `master/FC_MkIV_binaries.zip`. Flash the file `Slave.bin` within that archive in your boards.
2. Connect master computer and all slave boards in the same network
3. Run the master software by executing `master/main.py`
4. Talk to slave-side from master-side [IOU]
5. Set up a profile [IOU]
6. Connect boards to fans [IOU]
7. Control array [IOU]



## Dependencies

The master side of the software is written entirely in Python 3. The only package not built into Python 3 is `numpy`. Future versions will remove this requirement. It can run on Linux, macOS and Windows. It has been most thoroughly tested and is most reliable in Ubuntu, followed by Windows 10 and last macOS.













































