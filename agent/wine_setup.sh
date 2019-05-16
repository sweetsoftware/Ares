#!/bin/bash

sudo apt-get update && sudo apt-get -yq install wine

winecfg

if uname -a|grep -q "x86_64"
then
    dpkg --add-architecture i386 && apt-get update && apt-get install wine32
    wget -q https://www.python.org/ftp/python/2.7.16/python-2.7.16.amd64.msi -O /tmp/python.msi
else
    wget -q https://www.python.org/ftp/python/2.7.14/python-2.7.14.msi -O /tmp/python.msi
fi

wine msiexec /q /i /tmp/python.msi

wine pip.exe install pyinstaller

rm /tmp/python.msi
