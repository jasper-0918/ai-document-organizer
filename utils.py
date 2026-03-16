"""
Utilities
=========
Logging setup, config loading, and miscellaneous helpers.
"""

import logging
import sys
from pathlib import Path

import yaml


def load_config(config_path: str = "config.yaml") -> dict:
    """Load YAML config. Raises FileNotFoundError if missing."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}\n"
            "Copy config.yaml.example → config.yaml and edit as needed."
        )
    with open(path) as f:
        return yaml.safe_load(f)


def setup_logging(level: str = "INFO", log_file: str = None):
    """
    Configure root logger with:
      - coloured console output (if colorlog is installed)
      - optional file handler
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handlers: list[logging.Handler] = []

    # Console handler
    try:
        import colorlog
        console = colorlog.StreamHandler(sys.stdout)
        console.setFormatter(
            colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s [%(levelname)s]%(reset)s %(name)s — %(message)s",
                datefmt="%H:%M:%S",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                },
            )
        )
    except ImportError:
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s — %(message)s", datefmt="%H:%M:%S")
        )
    handlers.append(console)

    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s — %(message)s")
        )
        handlers.append(file_handler)

    logging.basicConfig(level=numeric_level, handlers=handlers, force=True)


def human_readable_size(size_bytes: int) -> str:
    """Convert bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes //= 1024
    return f"{size_bytes:.1f} TB"
