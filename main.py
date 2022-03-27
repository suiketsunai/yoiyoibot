"""Main module"""
import os
import logging

from pathlib import Path
from datetime import datetime

# working with env
from dotenv import load_dotenv

# reading setings
import tomli

# telegram core bot api extension
from telegram.ext import Updater

# current timestamp & this file directory
date_run = datetime.now()
file_dir = Path(__file__).parent

# load .env file & get config
load_dotenv()
config = tomli.load(Path(os.environ["PATH_SETTINGS"]).open("rb"))

################################################################################
# logger
################################################################################

# get logger
log = logging.getLogger("yoiyoichan")


def setup_logging():
    """Set up logger"""
    # set basic config to logger
    logging.basicConfig(
        format=config["log"]["form"],
        level=config["log"]["level"],
    )
    # sqlalchemy logging
    for name, module in config["log"]["sqlalchemy"].items():
        if module["enable"]:
            logging.getLogger(f"sqlalchemy.{name}").setLevel(module["level"])
    # setup logging to file
    file_log = config["log"]["file"]
    if file_log["enable"]:
        log.info("Logging to file enabled.")
        log_dir = file_dir / file_log["path"]
        if not log_dir.is_dir():
            log.warning("Log directory doesn't exist.")
            try:
                log.info("Creating log directory...")
                log_dir.mkdir()
                log.info("Created log directory: '%s'.", log_dir.resolve())
            except Exception as ex:
                log.error("Exception occured: %s", ex)
                log.info("Can't execute program.")
                quit()
        log_date = date_run.strftime(file_log["date"])
        log_name = f'{file_log["pref"]}{log_date}.log'
        log_file = log_dir / log_name
        log.info("Logging to file: '%s'.", log_name)
        # add file handler
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter(file_log["form"]))
        fh.setLevel(file_log["level"])
        logging.getLogger().addHandler(fh)
    else:
        log.info("Logging to file disabled.")


################################################################################
# main body
################################################################################


def main() -> None:
    """Set up and run the bot"""
    # setup logging
    setup_logging()

    # create updater & dispatcher
    updater = Updater(
        os.environ["TOKEN"],
        request_kwargs={
            "read_timeout": 6,
            "connect_timeout": 7,
        },
    )
    dispatcher = updater.dispatcher

    # start bot
    updater.start_polling()

    # stop bot
    updater.idle()


if __name__ == "__main__":
    main()
