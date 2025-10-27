from __future__ import annotations

import os
import sys
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

# ---------- Public API ----------
def get_logger(name: str, *, app_root: Path | None = None) -> logging.Logger:
    logger = logging.getLogger(name)

    # already configured for this name
    if logger.handlers:
        return logger  

    # Resolve level from env (default INFO)
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(level)

    # Formatter: include time, level, module, and message
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler to stderr
    sh = logging.StreamHandler(stream=sys.stderr)
    sh.setLevel(level)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    # Rotating file handler
    root = app_root or Path.cwd()
    log_dir = root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    fh = RotatingFileHandler(
        filename=log_dir / "app.log",
        maxBytes=512 * 1024,   # 512 KB
        backupCount=3,         # keep 3 old logs
        encoding="utf-8",
    )
    fh.setLevel(level)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Avoid double logging through root handler in some environments
    logger.propagate = False
    return logger