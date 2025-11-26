# Launch GUI without console window
# This script runs the GUI using pythonw.exe to avoid keeping a terminal open

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Set the working directory to the script's location
Set-Location $ScriptDir

# Launch the GUI using pythonw.exe (no console window)
& "$ScriptDir\.venv\Scripts\pythonw.exe" "$ScriptDir\src\gui.py"
