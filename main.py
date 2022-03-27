"""Main module"""
import os
import re
import logging

from pathlib import Path
from datetime import datetime
from functools import partial

# working with env
from dotenv import load_dotenv

# reading setings
import tomli

# telegram core bot api
from telegram import (
    Update,
    InlineQueryResultArticle,
    InlineQueryResultVideo,
    InputTextMessageContent as in_text,
)

# telegram core bot api extension
from telegram.ext import (
    Updater,
    CallbackContext,
    InlineQueryHandler,
)

# bad request exception
from telegram.error import BadRequest

# excape markdown
from telegram.utils.helpers import escape_markdown

# import link types and other info
from extra import *

# import namedtuples
from extra.namedtuples import Link

# import tiktok api
from extra.tiktok import get_tiktok_links

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
# telegram bot helpers
################################################################################

# escaping markdown v2
esc = partial(escape_markdown, version=2)


def formatter(query: str) -> list[Link]:
    """Exctract and format links in text

    Args:
        query (str): text

    Returns:
        list[Link]: list of Links
    """
    if not query:
        return None
    response = []
    for re_key, re_type in link_dict.items():
        for link in re.finditer(re_type["re"], query):
            # dictionary keys = format args
            _link = re_type["link"].format(**link.groupdict())
            log.info("Received %s link: '%s'.", re_key, _link)
            # add to response list
            response.append(Link(re_type["type"], _link, int(link.group("id"))))
    return response


################################################################################
# telegram bot
################################################################################


def inliner(update: Update, context: CallbackContext) -> None:
    """Answers to inline input

    Args:
        update (Update): telegram update object
        context (CallbackContext): telegram context object
    """
    if not (links := formatter(update.inline_query.query)):
        log.info("Inline: No query.")
        return
    results = []
    for in_id, in_link in enumerate(links, 1):
        data = {
            "id": str(in_id),
            "title": f"#{in_id}: {LinkType.getType(in_link.type)} link",
        }
        # send video if tiktok
        if in_link.type == LinkType.TIKTOK:
            if video := get_tiktok_links(in_link.link):
                # check size
                if video.size < 20 << 20:
                    data.update(
                        {
                            "video_url": video.link,
                            "mime_type": "video/mp4",
                            "thumb_url": video.thumb_1,
                        }
                    )
                    try:
                        results.append(InlineQueryResultVideo(**data))
                        continue
                    # if telegram couldn't get file
                    except BadRequest:
                        text = "Telegram couldn't get the video."
                # if file is too big
                else:
                    text = "File is too big, send link to bot."
            # if there is no video
            else:
                text = "This tiktok can't be found or downloaded."
        # send link if anything else
        else:
            text = in_link.link
        # add to results
        results.append(
            InlineQueryResultArticle(
                **data,
                description=text,
                input_message_content=in_text(text),
            )
        )
    context.bot.answer_inline_query(update.inline_query.id, results)


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

    # add inline mode
    dispatcher.add_handler(InlineQueryHandler(inliner, run_async=True))

    # start bot
    updater.start_polling()

    # stop bot
    updater.idle()


if __name__ == "__main__":
    main()
