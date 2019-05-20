#!/bin/bash

sudo apt-get update && sudo apt-get -yq install wine

# If 64 bit, install both 64bit and 32bit wine environments
if uname -a|grep -q "x86_64"
then
    dpkg --add-architecture i386 && apt-get update && apt-get install wine32
    export WINEPREFIX=~/.wine-python64
    DISPLAY= winecfg
    wget -q https://www.python.org/ftp/python/2.7.16/python-2.7.16.amd64.msi -O /tmp/python.msi
    wine msiexec /q /i /tmp/python.msi
    wine pip install -r requirements.txt
fi

export WINEPREFIX=~/.wine-python32
DISPLAY= winecfg
wget -q https://www.python.org/ftp/python/2.7.14/python-2.7.14.msi -O /tmp/python.msi
wine msiexec /q /i /tmp/python.msi
wine pip install -r requirements.txt

rm /tmp/python.msi

export WINEPRIX=

