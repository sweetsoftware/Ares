#!/bin/bash

dpkg --add-architecture i386 && apt-get update && apt-get -yq install wine32
wget -q https://www.python.org/ftp/python/2.7/python-2.7.msi -O /tmp/python-2.7.msi 
wget -q https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py
wine msiexec /q /i /tmp/python-2.7.msi
wine C:/Python27/python.exe /tmp/get-pip.py
wine C:/Python27/Scripts/pip.exe install -r agent_requirements.txt
wine C:/Python27/Scripts/pip.exe install pyinstaller
rm /tmp/python-2.7.msi
rm /tmp/get-pip.py
