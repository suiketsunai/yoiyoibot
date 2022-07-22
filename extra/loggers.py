"""Loggers module"""
import os
import logging

from pathlib import Path
from datetime import datetime

# working with env
from dotenv import load_dotenv

# reading setings
import tomli

# current timestamp & this file directory
date_run = datetime.now()
file_dir = Path(__file__).parent.parent

################################################################################
# logger
################################################################################

# load .env file & get config
load_dotenv()
config = tomli.load(Path(os.getenv("PATH_SETTINGS")).open("rb"))

# set basic config to logger
logging.basicConfig(
    format=config["log"]["form"],
    level=config["log"]["level"],
)

# get root logger
root_log = logging.getLogger()


def get_file_handler() -> logging.FileHandler | None:
    """Create file handler"""
    file_log = config["log"]["file"]
    if file_log["enable"]:
        root_log.info("Logging to file enabled.")
        log_dir = file_dir / file_log["path"]
        if not log_dir.is_dir():
            root_log.warning("Log directory doesn't exist.")
            try:
                root_log.info("Creating log directory...")
                log_dir.mkdir()
                root_log.info("Created log directory: %r.", log_dir.resolve())
            except Exception as ex:
                root_log.error("Exception occured: %s.", ex)
                root_log.info("Can't execute program.")
                quit()
        log_date = date_run.strftime(file_log["date"])
        log_name = f'{file_log["pref"]}{log_date}.log'
        log_file = log_dir / log_name
        root_log.info("Logging to file: %r.", log_name)
        # add file handler
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter(file_log["form"]))
        fh.setLevel(file_log["level"])
        return fh
    root_log.info("Logging to file disabled.")
    return None


# get file handler
file_handler = get_file_handler()


def add_file_handler(logger: logging.Logger | str) -> None:
    """Add file handler to logger

    Args:
        logger (str): logger or name of logger
    """
    if not logger:
        root_log.error("No logger to add file handler to.")
    if not isinstance(logger, logging.Logger):
        logger = logging.getLogger(name)
    if file_handler:
        logger.addHandler(file_handler)


# setup root logger
add_file_handler(root_log)

# setup sqlalchemy loggers
for name, module in config["log"]["sqlalchemy"].items():
    if module["enable"]:
        logging.getLogger(f"sqlalchemy.{name}").setLevel(module["level"])
