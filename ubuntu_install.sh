# install Python 3.8
sudo apt install python3.8 python3-pip python3-tk python3-dev

# install all required python packages
pip install -r requirements.txt
# install chromium, firefox, edge and webkit browsers with all needed dependencies
playwright install --with-deps chromium firefox msedge webkit

# compile ems_screenshot.py to ems_screenshot.pyc
python3 -m compileall -f ems_screenshot.py
