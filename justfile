
# Default recipe (shows help)
# This must be the first recipe in the file

# Set default shell based on OS
set windows-powershell

# List available recipes
default:
  just --list

# Setup virtual environment and install dependencies
setup:
  python -m venv .venv
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Run process.py from repo root
process:
  .\.venv\Scripts\python.exe src\\process.py

# Run query.py from repo root
cli:
  .\.venv\Scripts\python.exe src\\cli.py

# Run queries in GUI mode
run:
  .\.venv\Scripts\python.exe src\\gui.py

# Clean up virtual environment
clean:
  Remove-Item -Recurse -Force .venv
  Write-Host "Cleaned up virtual environment."
