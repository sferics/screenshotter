# install brew package manager
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"

# check which MacOS version we are using
MAJOR_MAC_VERSION=$(sw_vers -productVersion | awk -F '.' '{print $1 "." $2}')

# if MacOS > 10.12: export python path this way
if awk "BEGIN {exit !($MAJOR_MAC_VERSION > 10.12)}"; then
   export PATH="/usr/local/opt/python/libexec/bin:$PATH"
else
   # else on MacOS Sierra or below that way
   export PATH=/usr/local/bin:/usr/local/sbin:$PATH
fi

# install python version 3.13
brew install python@3.13

# install all required python packages
pip install -r requirements.txt
# install chromium, firefox, edge and webkit browsers with all needed dependencies
playwright install --with-deps chromium firefox msedge webkit

# compile ems_screenshot.py to ems_screenshot.pyc
python3 -m compileall -f ems_screenshot.py
