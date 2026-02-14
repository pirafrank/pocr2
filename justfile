
# Default recipe (shows help)
# This must be the first recipe in the file

# Set default shell based on OS
set windows-powershell

# List available recipes
default:
  just --list

# Lint
lint:
  ruff check .

# Format
format:
  ruff format .

# Fix
fix:
  ruff check --fix .

# Compile
compile:
  .\.venv\Scripts\python.exe -m compileall .

# Setup virtual environment and install dependencies
prepare:
  python --version
  python -m pip install virtualenv
  python -m virtualenv .venv

# Install requirements
setup:
  .\.venv\Scripts\python.exe --version
  .\.venv\Scripts\python.exe -m pip install --upgrade pip
  .\.venv\Scripts\python.exe -m pip install -e .

# Check python version
check:
  Write-Host "Using Python version:"
  .\.venv\Scripts\python.exe --version

# Run OCR indexing command
index:
  .\.venv\Scripts\pocr2.exe index

# Run CLI search command
search:
  .\.venv\Scripts\pocr2.exe search

# Run queries in GUI mode
run:
  .\.venv\Scripts\pocr2.exe --gui

# Clean up virtual environment
clean:
  Remove-Item -Recurse -Force .venv
  Write-Host "Cleaned up virtual environment."
