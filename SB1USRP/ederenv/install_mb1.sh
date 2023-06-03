#!/bin/bash

echo 'Installing Python pip ...'
sudo apt-get install python-pip

echo 'Installing Python numpy module ...'
sudo pip install numpy scipy

echo 'Installing Python matplotlib module ...'
sudo pip install matplotlib

echo 'Installing Python-tk ...'
sudo apt-get install python-tk

echo 'Installing Python-smbus ...'
sudo apt-get install python-smbus

processor=`uname -m|awk '{print $1}'`

if [ $processor == "armv7l" ]
then
    echo 'Installing Python ederftdi module for armv7l ...'
    tar -xvzpf installation_files/EderFtdi-1.5.linux-armv7l.tar.gz .
else
    echo 'Installing Python ederftdi module for x86_64...'
    tar -xvzpf installation_files/EderFtdi-1.5.linux-x86_64.tar.gz .
fi

sudo cp usr/local/lib/python2.7/dist-packages/* /usr/local/lib/python2.7/dist-packages/
rm -rf usr

if [ $processor == "armv7l" ]
then
    echo 'Installing ftd2xx drivers and libs for armv7l ...'
    tar xfvz installation_files/libftd2xx-arm-v6-hf-1.4.6.tgz
else
    echo 'Installing ftd2xx drivers and libs for x86_64...'
    tar xfvz installation_files/libftd2xx-x86_64-1.4.6.tgz
fi

pushd release/build
sudo cp libftd2xx.* /usr/lib
sudo chmod 0755 /usr/lib/libftd2xx.so.1.4.6
sudo ln -sf /usr/lib/libftd2xx.so.1.4.6 /usr/lib/libftd2xx.so
popd
sudo cp installation_files/11-ftdi.rules /etc/udev/rules.d/
rm -rf release

echo 'Installation complete.'
