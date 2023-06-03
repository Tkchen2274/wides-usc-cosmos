#!/bin/bash

if [ "$#" -eq 0 ]; then
    echo "usage: ./start_mb1.sh [-g | -gui] [-v <Eder Gen number>] <Serial no.>"
    echo "example: ./start_mb1.sh SN0001"
    echo "example: ./start_mb1.sh -gui SN0001"
    echo "example: ./start_mb1.sh -g -v 2 SN0001"
    exit
fi


{
sudo modprobe -r ftdi_sio
} &> /dev/null


cd Eder_A

LAST_ARG_IDX=$#
SERIAL_NUMBER=${!LAST_ARG_IDX}

# Default Eder Gen 2
GEN=2

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
    python viewNotebook.py -b MB1 -v $GEN -u $SERIAL_NUMBER
else
    python -i eder.py -u $SERIAL_NUMBER -v $GEN -b MB1
fi
