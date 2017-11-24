#!/bin/bash

sudo dpkg --add-architecture i386 && sudo apt-get update && sudo apt-get -yq install wine32
wget -q https://www.python.org/ftp/python/2.7.14/python-2.7.14.msi -O /tmp/python-2.7.msi 
wine msiexec /q /i /tmp/python-2.7.msi
wine C:/Python27/Scripts/pip.exe install -r requirements.txt
rm /tmp/python-2.7.msi
