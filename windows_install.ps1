# download Python installer
Invoke-WebRequest https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe -OutFile python-3.8.10.exe | Out-Null

# install Python version 3.8
./python-3.8.10.exe InstallAllUsers=1 PrependPath=1 Include_test=0 Include_tcltk=1 Include_pip=1 Include_lib=1 CompileAll=1 | Wait-Process

# install all required python packages
pip install -r requirements.txt
# install chromium browser with all needed dependencies
python -m playwright install --with-deps chromium