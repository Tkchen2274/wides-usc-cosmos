@echo off

echo Installing Python numpy and scipy modules ...
pip install numpy scipy

echo Installing Python matplotlib module ...
pip install matplotlib

echo Installing Python keyboard module ...
pip install keyboard

echo Installing Python pyreadline module ...
pip install pyreadline

echo Installing Python colorama module ...
pip install colorama

echo Installing Python MB1 module for windows ...
installation_files\MB1-1.75.win32-py2.7.exe

echo.
echo.
echo Installation complete!
timeout /t -1
