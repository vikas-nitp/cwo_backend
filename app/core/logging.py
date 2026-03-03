"""
Logging configuration for CardwiseOffer Backend

Features:
- Console logging with colors
- Daily rotating file logs (TXT and JSON)
- 15-day retention with auto-archive
- Debug level support
"""

import json
import logging
import logging.config
import logging.handlers
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import yaml


# ────────────────────────────────────────────────────────────────────
# Custom JSON Formatter
# ────────────────────────────────────────────────────────────────────

class JsonFormatter(logging.Formatter):
    """Format log records as JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra
        
        return json.dumps(log_data, ensure_ascii=False)


# ────────────────────────────────────────────────────────────────────
# Daily Rotating File Handler with Archive
# ────────────────────────────────────────────────────────────────────

class DailyRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """
    Daily rotating file handler with:
    - Date-based filenames (app_2026-03-03.log)
    - 15-day retention
    - Auto-archive old logs to archive/ folder
    """
    
    def __init__(
        self,
        filename: str,
        when: str = "midnight",
        backup_count: int = 15,
        encoding: str = "utf-8",
        **kwargs
    ):
        # Resolve paths
        self.base_dir = Path(filename).parent
        self.base_name = Path(filename).stem
        self.extension = Path(filename).suffix or ".log"
        self.archive_dir = self.base_dir / "archive"
        self.backup_count = backup_count
        
        # Create directories
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Current date filename
        current_filename = self._get_dated_filename(datetime.now())
        
        super().__init__(
            filename=str(current_filename),
            when=when,
            backupCount=0,  # We handle rotation ourselves
            encoding=encoding,
            **kwargs
        )
        
        # Archive old logs on startup
        self._archive_old_logs()
    
    def _get_dated_filename(self, dt: datetime) -> Path:
        """Generate filename with date: app_2026-03-03.log"""
        date_str = dt.strftime("%Y-%m-%d")
        return self.base_dir / f"{self.base_name}_{date_str}{self.extension}"
    
    def doRollover(self) -> None:
        """Rotate to new dated file at midnight"""
        if self.stream:
            self.stream.close()
            self.stream = None
        
        # Update to new date
        new_filename = self._get_dated_filename(datetime.now())
        self.baseFilename = str(new_filename)
        
        # Open new file
        self.stream = self._open()
        
        # Archive old logs
        self._archive_old_logs()
    
    def _archive_old_logs(self) -> None:
        """Move logs older than backup_count days to archive folder"""
        cutoff_date = datetime.now() - timedelta(days=self.backup_count)
        
        for log_file in self.base_dir.glob(f"{self.base_name}_*{self.extension}"):
            if log_file.is_file() and log_file.parent == self.base_dir:
                try:
                    # Extract date from filename
                    date_str = log_file.stem.replace(f"{self.base_name}_", "")
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    if file_date < cutoff_date:
                        # Move to archive
                        archive_path = self.archive_dir / log_file.name
                        shutil.move(str(log_file), str(archive_path))
                except (ValueError, OSError):
                    pass  # Skip files that don't match pattern


# ────────────────────────────────────────────────────────────────────
# Logger Setup
# ────────────────────────────────────────────────────────────────────

def setup_logging(config_path: Optional[str] = None) -> None:
    """
    Setup logging configuration from YAML file.
    
    Args:
        config_path: Path to logging.yaml. If None, uses default location.
    """
    if config_path is None:
        # Default: logging.yaml in cwo_backend root
        config_path = Path(__file__).parent.parent.parent / "logging.yaml"
    
    config_path = Path(config_path)
    
    # Create logs directory
    logs_dir = Path(__file__).parent.parent.parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    (logs_dir / "archive").mkdir(parents=True, exist_ok=True)
    
    if config_path.exists():
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        
        # Update file paths to absolute
        for handler_name, handler_config in config.get("handlers", {}).items():
            if "filename" in handler_config:
                handler_config["filename"] = str(logs_dir / Path(handler_config["filename"]).name)
        
        logging.config.dictConfig(config)
    else:
        # Fallback to basic config
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (e.g., "app.services.data")
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# ────────────────────────────────────────────────────────────────────
# Convenience Methods
# ────────────────────────────────────────────────────────────────────

class AppLogger:
    """
    Application logger with convenience methods.
    
    Usage:
        from app.core.logging import AppLogger
        logger = AppLogger("app.services.data")
        logger.debug("Loading data", extra={"file": "offers.xlsx"})
        logger.info("Data loaded", extra={"count": 100})
        logger.error("Failed to load", exc_info=True)
    """
    
    def __init__(self, name: str):
        self._logger = logging.getLogger(name)
    
    def debug(self, msg: str, **kwargs) -> None:
        self._logger.debug(msg, **kwargs)
    
    def info(self, msg: str, **kwargs) -> None:
        self._logger.info(msg, **kwargs)
    
    def warning(self, msg: str, **kwargs) -> None:
        self._logger.warning(msg, **kwargs)
    
    def error(self, msg: str, **kwargs) -> None:
        self._logger.error(msg, **kwargs)
    
    def critical(self, msg: str, **kwargs) -> None:
        self._logger.critical(msg, **kwargs)
    
    def exception(self, msg: str, **kwargs) -> None:
        self._logger.exception(msg, **kwargs)

