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
    InputMediaVideo,
    InputMediaDocument,
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
from db.models import Chat

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

# import instagram api
from extra.instagram import get_instagram_links

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
                log.info("Created log directory: %r.", log_dir.resolve())
            except Exception as ex:
                log.error("Exception occured: %s", ex)
                log.info("Can't execute program.")
                quit()
        log_date = date_run.strftime(file_log["date"])
        log_name = f'{file_log["pref"]}{log_date}.log'
        log_file = log_dir / log_name
        log.info("Logging to file: %r.", log_name)
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


def notify(
    update: Update,
    *,
    command: str = None,
    func: str = None,
    inline: bool = False,
) -> None:
    """Log that something hapened

    Args:
        update (Update): current update
        command (str, optional): called command. Defaults to None.
    """
    if inline:
        return log.info(
            "Inline mode was invoked by %r [%r].",
            update.effective_user.full_name,
            update.effective_user.id,
        )
    cht = update.effective_chat
    if command:
        return log.info(
            "%r command was called by %r [%r].",
            command,
            cht.title if cht.id < 0 else cht.full_name,
            cht.id,
        )
    if func:
        return log.info(
            "%r function was called by %r [%r].",
            func,
            cht.title if cht.id < 0 else cht.full_name,
            cht.id,
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
            log.info("Received %s link: %r.", re_key, _link)
            # add to response list
            response.append(Link(re_type["type"], _link, link.group("id")))
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
        u = s.get(Chat, update.effective_chat.id)
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
    cht = update.effective_chat
    with Session(engine) as s:
        if not s.get(Chat, cht.id):
            s.add(
                Chat(
                    id=cht.id,
                    type=cht.type,
                    name=cht.title if cht.id < 0 else cht.full_name,
                    chat_link=cht.username,
                )
            )
            s.commit()
    update.effective_message.reply_markdown_v2(
        text=f"Yo\\~, {update.effective_user.mention_markdown_v2()}\\!\n"
        "I'm *Yoi Yoi* chan\\! 🎉\n"
        "Call for \\/help if in need\\!",
    )


def command_help(update: Update, _) -> None:
    """Send help message"""
    notify(update, command="/help")
    send_reply(
        update, Path(os.environ["HELP_FILE"]).read_text(encoding="utf-8")
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


def command_include_link(update: Update, _) -> None:
    """Enables/Disables TikTok HD mode"""
    notify(update, command="/command_include_link")
    send_reply(
        update,
        f"Including source is *{_switch[toggler(update, 'include_link')]}*\\.",
    )


def inliner(update: Update, context: CallbackContext) -> None:
    """Answers to inline input

    Args:
        update (Update): telegram update object
        context (CallbackContext): telegram context object
    """
    notify(update, inline=True)
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
    chat: Chat,
):
    mes = update.effective_message
    reply = {
        "reply_to_message_id": None if chat.include_link else mes.message_id,
        "chat_id": mes.chat_id,
    }
    if media := get_twitter_links(link.id):
        log.debug("Twitter media info: %s.", media)
        info = media.source if chat.include_link else None
        if media.media == "photo":
            photos, documents = [], []
            for photo in media.links:
                log.debug("Link: %r.", photo)
                log.debug("Downloading...")
                file = requests.get(
                    url=photo,
                    headers=fake_headers,
                    allow_redirects=True,
                )
                log.debug("Adding content to collection...")
                photos.append(InputMediaPhoto(file.content))
                filename = "{}.{}".format(
                    re.search(link_dict["twitter"]["file"], photo)["id"],
                    magic.from_buffer(file.content, mime=True).split("/")[1],
                )
                log.debug("Filename: %r.", filename)
                # log.debug("Full ext: %r.", magic.from_buffer(file.content))
                documents.append(
                    InputMediaDocument(
                        media=file.content,
                        filename=filename,
                        disable_content_type_detection=True,
                    )
                )
            log.debug("Finished adding to collection.")
            log.debug("Changing caption to %r.", link.link)
            photos[0].caption = info
            log.debug("Sending media group...")
            if chat.type == "private":
                update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)
            # send photo group
            post = context.bot.send_media_group(**reply, media=photos)
            # send document group
            if chat.tw_orig and post:
                # documents[-1].caption = info
                context.bot.send_media_group(
                    chat_id=mes.chat_id,
                    reply_to_message_id=post[0].message_id,
                    media=documents,
                )
        else:
            # send video and gifs as is
            for media in media.links:
                context.bot.send_document(**reply, caption=info, document=media)
        return
    else:
        text = (
            f"[This twitter content]({link.link}) can\\'t be found or "
            "downloaded\\. If this seems to be wrong, try again later\\."
        )
    send_error(update, text)


def send_tiktok(
    update: Update,
    context: CallbackContext,
    link: Link,
    chat: Chat,
):
    mes = update.effective_message
    reply = {
        "reply_to_message_id": None if chat.include_link else mes.message_id,
        "chat_id": mes.chat_id,
    }
    if video := get_tiktok_links(link.link):
        info = video.source if chat.include_link else None
        # check size
        if video.size < 50 << 20:
            if chat.tt_orig and video.size_hd < 50 << 20:
                reply["video"] = video.link_hd
            else:
                reply["video"] = video.link
            # download
            vid = requests.get(
                url=reply["video"],
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
                reply["video"] = mp4.read_bytes()
                mp4.unlink()
            else:
                reply["video"] = file.read_bytes()
            # notify user
            if chat.type == "private":
                update.message.chat.send_action(ChatAction.UPLOAD_VIDEO)
            # upload
            context.bot.send_video(**reply, caption=info)
            # delete
            file.unlink()
            return
        # if file is too big
        else:
            text = "Sorry, this file is too big\\!"
    # if there is no video
    else:
        text = (
            f"[This tiktok content]({link.link}) can\\'t be found or "
            "downloaded\\. If this seems to be wrong, try again later\\."
        )
    send_error(update, text)


def send_instagram(
    update: Update,
    context: CallbackContext,
    link: Link,
    chat: Chat,
):
    mes = update.effective_message
    reply = {
        "reply_to_message_id": None if chat.include_link else mes.message_id,
        "chat_id": mes.chat_id,
    }
    if media := get_instagram_links(link.link):
        files, documents = [], []
        info = media[0].source if chat.include_link else None
        for item in media:
            log.debug("Link: %r.", item.link)
            log.debug("Downloading...")
            file = requests.get(
                item.link,
                headers=fake_headers,
                allow_redirects=True,
            )
            log.debug("Adding content to collection...")
            if item.type == "image":
                if chat.type == "private":
                    update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)
                files.append(InputMediaPhoto(file.content))
                filename = "{}.{}".format(
                    re.search(link_dict["instagram"]["file"], item.link)["id"],
                    magic.from_buffer(file.content, mime=True).split("/")[1],
                )
                log.debug("Filename: %r.", filename)
                # log.debug("Full ext: %r.", magic.from_buffer(file.content))
                documents.append(
                    InputMediaDocument(
                        media=file.content,
                        filename=filename,
                        disable_content_type_detection=True,
                    )
                )
            if item.type == "video":
                if chat.type == "private":
                    update.message.chat.send_action(ChatAction.UPLOAD_VIDEO)
                files.append(InputMediaVideo(file.content))
        log.debug("Finished adding to collection.")
        log.debug("Changing caption to: %r.", link.link)
        files[0].caption = info
        log.debug("Sending media group...")
        # send file group
        post = context.bot.send_media_group(**reply, media=files)
        # send document group
        if chat.in_orig and documents and post:
            # documents[-1].caption = info
            context.bot.send_media_group(
                chat_id=mes.chat_id,
                reply_to_message_id=post[0].message_id,
                media=documents,
            )
        return
    # if no links returned
    else:
        text = (
            f"[This instagram content]({link.link}) can\\'t be found or "
            "downloaded\\. If this seems to be wrong, try again later\\."
        )
    send_error(update, text)


def echo(update: Update, context: CallbackContext) -> None:
    """Answers to user's links

    Args:
        update (Update): telegram update object
        context (CallbackContext): telegram context object
    """
    notify(update, func="echo")
    # get message
    mes = update.effective_message
    cht = update.effective_chat
    # if no text
    if not ((text := mes.text) or (text := mes.caption)):
        log.info("Echo: No text.")
        return

    with Session(engine) as session:
        is_not_user = cht.id < 0
        if not (chat := session.get(Chat, cht.id)):
            session.add(
                chat := Chat(
                    id=cht.id,
                    type=cht.type,
                    name=cht.title if is_not_user else cht.full_name,
                    chat_link=cht.username,
                    tw_orig=is_not_user,
                    tt_orig=is_not_user,
                    in_orig=is_not_user,
                    include_link=is_not_user,
                )
            )
        else:
            chat.name = cht.title if is_not_user else cht.full_name
            chat.chat_link = cht.username
        session.commit()
        log.debug(chat)

    for link in formatter(text):
        match link.type:
            case LinkType.INSTAGRAM:
                send_instagram(update, context, link, chat)
            case LinkType.TIKTOK:
                send_tiktok(update, context, link, chat)
            case LinkType.TWITTER:
                send_twitter(update, context, link, chat)
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
    updater = Updater(os.environ["TOKEN"])

    # start bot
    webhook = (
        "https://"
        + os.environ["APP_NAME"]
        + ".herokuapp.com/"
        + os.environ["TOKEN"]
    )
    updater.start_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", "8443")),
        url_path=os.environ["TOKEN"],
        webhook_url=webhook,
    )
    dispatcher = updater.dispatcher

    # start the bot
    dispatcher.add_handler(CommandHandler("start", command_start))

    # get help
    dispatcher.add_handler(CommandHandler("help", command_help))

    # toggle hd quality for instagram
    dispatcher.add_handler(CommandHandler("instagram_hd", command_instagram_hd))

    # toggle hd quality for twitter
    dispatcher.add_handler(CommandHandler("twitter_hd", command_twitter_hd))

    # toggle hd quality for tiktok
    dispatcher.add_handler(CommandHandler("tiktok_hd", command_tiktok_hd))

    # toggle including links
    dispatcher.add_handler(CommandHandler("include_link", command_include_link))

    # add inline mode
    dispatcher.add_handler(InlineQueryHandler(inliner, run_async=True))

    # add echo command
    dispatcher.add_handler(
        MessageHandler(~Filters.command, echo, run_async=True)
    )

    # stop the bot
    updater.idle()


if __name__ == "__main__":
    main()
