#!/bin/bash

cd Eder_A

if [ "$1" == "-gui" ]; then
    cd pythonGUI
    python viewNotebook.py -b MB0
else
    python -i eder.py -b MB0
fi
