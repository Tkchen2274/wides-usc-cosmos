#!/bin/bash

if [ "$#" -eq 0 ]; then
    echo "usage: ./start_mb1_b.sh [-g | -gui] <Serial no.>"
    echo "example: ./start_mb1_b.sh SN0001"
    echo "example: ./start_mb1_b.sh -gui SN0001"
    exit
fi


{
sudo modprobe -r ftdi_sio
} &> /dev/null


cd Eder_B

LAST_ARG_IDX=$#
SERIAL_NUMBER=${!LAST_ARG_IDX}

# Default no GUI
GUI=0 

while getopts :v:gui option
do
    case "${option}"
        in
            v) GEN=${OPTARG} ;;
            g) GUI=1 ;;
            \?) ;;
    esac
done

export LD_LIBRARY_PATH=/usr/local/lib
if [ $GUI == 1 ]; then
    cd pythonGUI
    python viewNotebook.py -b MB1 -u $SERIAL_NUMBER
else
    python -i eder.py -u $SERIAL_NUMBER -b MB1
fi
