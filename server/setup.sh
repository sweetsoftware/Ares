wine msiexec /package python-2.7.13.msi /quiet
wine C:/Python27/python.exe get-pip.py
wine C:/Python27/Scripts/pip.exe install pypiwin32 pyinstaller requests
