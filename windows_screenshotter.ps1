# allow script executioon for this process
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

# source virtual environment "venv"
.\venv\Scripts\Activate.ps1

# execute python script and pass all arguments on to it
python ems_screenshot.py $args