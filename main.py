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

# http requests
import requests

# file extension check
import magic

# convert video files
import ffmpeg

# telegram core bot api
from telegram import (
    Update,
    InlineQueryResultArticle,
    InlineQueryResultVideo,
    InputMediaPhoto,
    InputTextMessageContent as in_text,
    Message,
    ChatAction,
)

# telegram core bot api extension
from telegram.ext import (
    Updater,
    CallbackContext,
    InlineQueryHandler,
    CommandHandler,
    MessageHandler,
    Filters,
)

# bad request exception
from telegram.error import BadRequest

# excape markdown
from telegram.utils.helpers import escape_markdown

# working with database
from sqlalchemy.orm import Session

# import engine
from db import engine

# import database
from db.models import User

# import link types and other info
from extra import *

# import fake headers
from extra.helper import fake_headers

# import namedtuples
from extra.namedtuples import Link

# import tiktok api
from extra.tiktok import get_tiktok_links

# import twitter api
from extra.twitter import get_twitter_links

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

# helper dictionary
_switch = {
    True: "enabled",
    False: "disabled",
}

# escaping markdown v2
esc = partial(escape_markdown, version=2)


def send_reply(update: Update, text: str, **kwargs) -> Message:
    """Reply to current message

    Args:
        update (Update): current update
        text (str): text to send in markdown v2

    Returns:
        Message: Telegram Message
    """
    return update.effective_message.reply_markdown_v2(
        reply_to_message_id=update.effective_message.message_id,
        text=text,
        **kwargs,
    )


def send_error(update: Update, text: str, **kwargs) -> Message:
    """Reply to current message with error

    Args:
        update (Update): current update
        text (str): text to send in markdown v2

    Returns:
        Message: Telegram Message
    """
    return update.effective_message.reply_markdown_v2(
        reply_to_message_id=update.effective_message.message_id,
        text=f"\\[`ERROR`\\] {text}",
        **kwargs,
    )


def notify(update: Update, *, command: str = None, func: str = None) -> None:
    """Log that something hapened

    Args:
        update (Update): current update
        command (str, optional): called command. Defaults to None.
    """
    if command:
        log.info(
            "%s command was called by %s [%s].",
            command,
            update.effective_user.full_name,
            update.effective_user.id,
        )
    if func:
        log.info(
            "%s function was called by %s [%s].",
            func,
            update.effective_user.full_name,
            update.effective_user.id,
        )


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


def toggler(update: Update, attr: str) -> bool:
    """Toggle state between True and False

    Args:
        update (Update): current update
        attr (str): attribute to change

    Returns:
        bool: new state
    """
    with Session(engine) as s:
        u = s.get(User, update.effective_chat.id)
        state = getattr(u, attr)
        setattr(u, attr, not state)
        s.commit()
        return not state


################################################################################
# telegram bot
################################################################################


def command_start(update: Update, _) -> None:
    """Start the bot"""
    notify(update, command="/start")
    with Session(engine) as s:
        if not s.get(User, update.effective_chat.id):
            s.add(
                User(
                    id=update.effective_chat.id,
                    full_name=update.effective_chat.full_name,
                    nick_name=update.effective_chat.username,
                )
            )
            s.commit()
    update.effective_message.reply_markdown_v2(
        text=f"Yo\\~, {update.effective_user.mention_markdown_v2()}\\!\n"
        "I'm *Yoi Yoi* chan\\! 🎉\n"
        "Call for \\/help if in need\\!",
    )


def command_instagram_hd(update: Update, _) -> None:
    """Enables/Disables Instagram HD mode"""
    notify(update, command="/command_instagram_hd")
    send_reply(
        update,
        f"Instagram HD mode is *{_switch[toggler(update, 'in_orig')]}*\\.",
    )


def command_twitter_hd(update: Update, _) -> None:
    """Enables/Disables Twitter HD mode"""
    notify(update, command="/command_twitter_hd")
    send_reply(
        update,
        f"Twitter HD mode is *{_switch[toggler(update, 'tw_orig')]}*\\.",
    )


def command_tiktok_hd(update: Update, _) -> None:
    """Enables/Disables TikTok HD mode"""
    notify(update, command="/command_tiktok_hd")
    send_reply(
        update,
        f"Tiktok HD mode is *{_switch[toggler(update, 'tt_orig')]}*\\.",
    )


def inliner(update: Update, context: CallbackContext) -> None:
    """Answers to inline input

    Args:
        update (Update): telegram update object
        context (CallbackContext): telegram context object
    """
    notify(update, func="inliner")
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
# telegram text message handlers
################################################################################


def send_twitter(
    update: Update,
    context: CallbackContext,
    link: Link,
    user: User,
):
    if media := get_twitter_links(link.id):
        log.debug("Twitter media info: %s.", media)
        if media.media == "photo":
            group = []
            for photo in media.links:
                update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)
                log.debug("Link: %s.", photo)
                log.debug("Downloading...")
                file = requests.get(
                    url=photo,
                    headers=fake_headers,
                    allow_redirects=True,
                )
                log.debug("Adding content to collection...")
                group.append(InputMediaPhoto(file.content))
            log.debug("Finished adding to collection.")
            log.debug("Changing caption to '%s'.", link.link)
            group[0].caption = link.link
            log.debug("Sending media group...")
            context.bot.send_media_group(
                reply_to_message_id=update.effective_message.message_id,
                chat_id=update.effective_message.chat_id,
                media=group,
            )
        if user.tw_orig or media.media != "photo":
            for media_link in media.links:
                context.bot.send_document(
                    reply_to_message_id=update.effective_message.message_id,
                    chat_id=update.effective_message.chat_id,
                    caption=link.link,
                    document=media_link,
                )
        return
    else:
        text = "This tweet content can't be found or downloaded."
    send_error(update, esc(text))


def send_tiktok(
    update: Update,
    context: CallbackContext,
    link: Link,
    user: User,
):
    if video := get_tiktok_links(link.link):
        # check size
        data = {}
        if video.size < 50 << 20:
            if user.tt_orig and video.size_hd < 50 << 20:
                data["video"] = video.link_hd
            else:
                data["video"] = video.link
            # notify user
            update.message.chat.send_action(action=ChatAction.UPLOAD_VIDEO)
            # download
            vid = requests.get(
                url=data["video"],
                headers=fake_headers,
                allow_redirects=True,
            )
            file = file_dir / f"{video.id}-{update.effective_message.chat_id}"
            # save
            file.write_bytes(vid.content)
            # check extension
            file_ext = magic.from_file(str(file))
            log.info(f"File extension: {file_ext}")
            # convert if needed
            if "mp4" not in file_ext.lower():
                mp4 = file_dir / f"{video.id}.mp4"
                log.info("Converting...")
                ffmpeg.input(str(file)).output(str(mp4)).run()
                data["video"] = mp4.read_bytes()
                mp4.unlink()
            else:
                data["video"] = file.read_bytes()
            # upload
            context.bot.send_video(
                reply_to_message_id=update.effective_message.message_id,
                chat_id=update.effective_message.chat_id,
                **data,
            )
            # delete
            file.unlink()
            return
        # if file is too big
        else:
            text = "File is too big."
    # if there is no video
    else:
        text = "This tiktok can't be found or downloaded."
    send_error(update, esc(text))


def send_instagram():
    return False


def echo(update: Update, context: CallbackContext) -> None:
    """Answers to user's links

    Args:
        update (Update): telegram update object
        context (CallbackContext): telegram context object
    """
    notify(update, func="echo")
    # get message
    mes = update.effective_message
    # if no text
    if not ((text := mes.text) or (text := mes.caption)):
        log.info("Echo: No text.")
        return

    with Session(engine) as session:
        if not (user := session.get(User, mes.chat_id)):
            send_error(update, "The bot doesn\\'t know you\\! Send /start\\.")
            return
        log.debug(user)

    for link in formatter(text):
        match link.type:
            case LinkType.INSTAGRAM:
                send_instagram()
            case LinkType.TIKTOK:
                send_tiktok(update, context, link, user)
            case LinkType.TWITTER:
                send_twitter(update, context, link, user)
            case _:
                send_reply(update, esc(link.link))


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

    # hd quality for instagram
    dispatcher.add_handler(CommandHandler("start", command_start))

    # hd quality for instagram
    dispatcher.add_handler(CommandHandler("instagram_hd", command_instagram_hd))

    # hd quality for twitter
    dispatcher.add_handler(CommandHandler("twitter_hd", command_twitter_hd))

    # hd quality for tiktok
    dispatcher.add_handler(CommandHandler("tiktok_hd", command_tiktok_hd))

    # add inline mode
    dispatcher.add_handler(InlineQueryHandler(inliner, run_async=True))

    # add echo command
    dispatcher.add_handler(
        MessageHandler(~Filters.command, echo, run_async=True)
    )

    # start bot
    updater.start_polling()

    # stop bot
    updater.idle()


if __name__ == "__main__":
    main()
