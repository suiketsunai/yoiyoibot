import os
import time
import base64
import logging

from pathlib import Path

# http requests
import requests

# logger file handler
from extra.loggers import file_handler

# get logger
log = logging.getLogger("yoiyoi.upload")

# set upload timeout
UPLOAD_TIMEOUT = 3


def upload_log() -> None:
    """Upload log file to Google Drive"""
    if not file_handler:
        return  # silently exit
    if not (link := os.environ["GD_LOG"]):
        return log.error("No log upload link.")
    if not (file := Path(file_handler.baseFilename)).exists():
        return log.error("No such file!")
    for attempt in range(3):
        if attempt:
            log.info("Waiting for %d seconds...", UPLOAD_TIMEOUT)
            time.sleep(UPLOAD_TIMEOUT)
            log.info("Done. Current attempt: #%d.", attempt + 1)
        log.info("Uploading log file %r...", file.name)
        r = requests.post(
            url=link,
            params={"name": file.name},
            data=base64.urlsafe_b64encode(file.read_bytes()),
        )
        try:
            if r.json()["ok"]:
                log.info("Done uploading log file %r.", file.name)
            else:
                log.info("Log file %r already exists.", file.name)
            break
        except Exception as ex:
            log.error("Exception occured: %s.", ex)
    else:
        log.error("Error: Run out of attempts.")
        log.error("Couldn't upload log file %r.", file.name)
