# allow execution of PowerShell scripts
Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope CurrentUser

# download Python installer
Invoke-WebRequest https://www.python.org/ftp/python/3.13.3/python-3.13.3-amd64.exe -OutFile python-3.13.3.exe | Out-Null

# install Python version 3.13.3
./python-3.13.3.exe InstallAllUsers=1 PrependPath=1 Include_test=0 Include_tcltk=1 Include_pip=1 Include_lib=1 CompileAll=1 | Wait-Process

# add Python executable to PATH
$env:Path += ";C:\Program Files\Python313\python.exe;"

# install all required python packages
pip install -r requirements.txt
# install chromium (+chrome, firefox, edge and webkit) browsers with all needed dependencies
python -m playwright install --with-deps chromium #chrome firefox msedge webkit

# install winldd for playwright
python -m playwright install winldd

# compile ems_screenshot.py to ems_screenshot.pyc
python -m compileall -f ems_screenshot.py

# Restore Restricted setting for ExecutionPolicy
Set-ExecutionPolicy -ExecutionPolicy Restricted -Scope CurrentUser
