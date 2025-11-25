"""Configuration management for pocr2."""

import os
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:
    # Python < 3.11
    import tomli as tomllib


def get_config_dir() -> Path:
    """Get the configuration directory based on the platform."""
    if sys.platform == "win32":
        # Windows: Use APPDATA
        base = os.getenv("APPDATA")
        if not base:
            raise RuntimeError("APPDATA environment variable not set")
        return Path(base) / "pirafrank" / "pocr2" / "config"
    else:
        # Linux/macOS: Use XDG_CONFIG_HOME or default to ~/.config
        base = os.getenv("XDG_CONFIG_HOME")
        if not base:
            base = os.path.expanduser("~/.config")
        return Path(base) / "pirafrank" / "pocr2" / "config"


def get_data_dir() -> Path:
    """Get the data directory based on the platform."""
    if sys.platform == "win32":
        # Windows: Use LOCALAPPDATA
        base = os.getenv("LOCALAPPDATA")
        if not base:
            base = os.getenv("APPDATA")
        if not base:
            raise RuntimeError("LOCALAPPDATA/APPDATA environment variable not set")
        return Path(base) / "pirafrank" / "pocr2" / "data"
    else:
        # Linux/macOS: Use XDG_DATA_HOME or default to ~/.local/share
        base = os.getenv("XDG_DATA_HOME")
        if not base:
            base = os.path.expanduser("~/.local/share")
        return Path(base) / "pirafrank" / "pocr2" / "data"


def get_config_file() -> Path:
    """Get the config file path."""
    return get_config_dir() / "config.toml"


def get_db_file() -> Path:
    """Get the database file path."""
    return get_data_dir() / "pocr2.db"


def load_config() -> dict:
    """Load configuration from config.toml file."""
    config_file = get_config_file()

    if not config_file.exists():
        # create a default config file with a sample screenshots_dir
        default_config = {
            "screenshots_dir": str(Path.home() / "Pictures" / "Screenshots"),
        }
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, "wb") as f:
            # Use forward slashes or escape backslashes for TOML compatibility
            screenshots_path = default_config["screenshots_dir"].replace("\\", "/")
            toml_data = f'screenshots_dir = "{screenshots_path}"\n'
            f.write(toml_data.encode("utf-8"))
        return default_config

    with open(config_file, "rb") as f:
        config = tomllib.load(f)

    return config


def get_screenshots_dir() -> Path:
    """Get the screenshots directory from config."""
    try:
        config = load_config()
        screenshots_dir = config["screenshots_dir"]
        return Path(screenshots_dir)
    except KeyError as exc:
        raise RuntimeError(
            f"'screenshots_dir' key is not configured in {get_config_file()}"
        ) from exc


def get_tesseract_path() -> str:
    """Get the Tesseract path from config."""
    config = load_config()
    return config.get(
        "tesseract_path", "tesseract.exe" if sys.platform == "win32" else "tesseract"
    )


def get_max_workers() -> int:
    """Get the max workers from config."""
    config = load_config()
    return config.get("max_workers", 4)


def get_fuzzy_threshold() -> float:
    """Get the fuzzy search threshold from config."""
    config = load_config()
    return config.get("fuzzy_threshold", 0.5)


def ensure_dirs() -> None:
    """Ensure that config and data directories exist."""
    config_dir = get_config_dir()
    data_dir = get_data_dir()

    config_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)


# Module-level constants for easy access
CONFIG_DIR = get_config_dir()
DATA_DIR = get_data_dir()
CONFIG_FILE = get_config_file()
DB_FILE = get_db_file()

# Debug
if __name__ == "__main__":
    print(f"Config Directory: {CONFIG_DIR}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Config File: {CONFIG_FILE}")
    print(f"Database File: {DB_FILE}")
    print(f"Screenshots Directory: {get_screenshots_dir()}")
    print(f"Tesseract Path: {get_tesseract_path()}")
    print(f"Max Workers: {get_max_workers()}")
    print(f"Fuzzy Threshold: {get_fuzzy_threshold()}")
