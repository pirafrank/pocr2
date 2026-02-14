"""Configuration management for pocr2."""

import os
import sys
from pathlib import Path
from typing import Optional

try:
    import tomllib
except ImportError:
    # Python < 3.11
    import tomli as tomllib

_CONFIG_FILE_OVERRIDE: Optional[Path] = None


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
    if _CONFIG_FILE_OVERRIDE is not None:
        return _CONFIG_FILE_OVERRIDE
    return get_config_dir() / "config.toml"


def set_config_file(path: Optional[str | Path]) -> None:
    """Override config file location at runtime; pass None to clear override."""
    global _CONFIG_FILE_OVERRIDE
    if path is None:
        _CONFIG_FILE_OVERRIDE = None
        return
    _CONFIG_FILE_OVERRIDE = Path(path).expanduser().resolve()


def get_db_file() -> Path:
    """Get the database file path."""
    default_db_file = get_data_dir() / "pocr2.db"
    config = load_config()
    db_path = str(config.get("db_path", "")).strip()

    if not db_path:
        db_file = default_db_file
    else:
        db_file = Path(db_path).expanduser()
        if not db_file.is_absolute():
            db_file = (Path.cwd() / db_file).resolve()
        else:
            db_file = db_file.resolve()

    db_file.parent.mkdir(parents=True, exist_ok=True)
    return db_file


def load_config() -> dict:
    """Load configuration from config.toml file."""
    config_file = get_config_file()
    default_config = {
        "screenshots_dir": str(Path.home() / "Pictures" / "Screenshots"),
        "db_path": str(get_data_dir() / "pocr2.db"),
        "ocr_engine": "tesseract",
        "ollama_host": "http://localhost:11434",
        "ollama_model": "glm-ocr",
        "ollama_prompt": "Extract the text from this image and format it as Markdown.",
    }

    if not config_file.exists():
        # create a default config file with a sample screenshots_dir
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, "wb") as f:
            # Use forward slashes or escape backslashes for TOML compatibility
            screenshots_path = default_config["screenshots_dir"].replace("\\", "/")
            toml_data = (
                f'screenshots_dir = "{screenshots_path}"\n'
                f'db_path = "{default_config["db_path"].replace("\\\\", "/")}"\n'
                f'ocr_engine = "{default_config["ocr_engine"]}"\n'
                f'ollama_host = "{default_config["ollama_host"]}"\n'
                f'ollama_model = "{default_config["ollama_model"]}"\n'
                f'ollama_prompt = "{default_config["ollama_prompt"]}"\n'
            )
            f.write(toml_data.encode("utf-8"))
        return default_config

    with open(config_file, "rb") as f:
        config = tomllib.load(f)

    # Merge defaults with user config so newly-added keys stay backward compatible.
    return {**default_config, **config}


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


def get_ocr_engine() -> str:
    """Get selected OCR engine from config."""
    config = load_config()
    engine = str(config.get("ocr_engine", "tesseract")).strip().lower()
    return engine if engine in ("tesseract", "glm-ocr") else "tesseract"


def get_ollama_host() -> str:
    """Get Ollama host URL from config."""
    config = load_config()
    return str(config.get("ollama_host", "http://localhost:11434")).strip()


def get_ollama_model() -> str:
    """Get Ollama model name from config."""
    config = load_config()
    return str(config.get("ollama_model", "glm-ocr")).strip()


def get_ollama_prompt() -> str:
    """Get GLM-OCR prompt from config."""
    config = load_config()
    return str(
        config.get(
            "ollama_prompt", "Extract the text from this image and format it as Markdown."
        )
    ).strip()


def ensure_dirs() -> None:
    """Ensure that config and data directories exist."""
    config_dir = get_config_file().parent
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
    print(f"OCR Engine: {get_ocr_engine()}")
    print(f"Ollama Host: {get_ollama_host()}")
    print(f"Ollama Model: {get_ollama_model()}")
