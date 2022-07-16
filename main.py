"""Main module"""
import os
import re
import time
import logging

from pathlib import Path
from functools import partial

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
from telegram.error import BadRequest, RetryAfter, TimedOut

# telegram constants
from telegram.constants import PARSEMODE_MARKDOWN_V2 as MDV2

# excape markdown
from telegram.utils.helpers import escape_markdown

# working with database
from sqlalchemy.orm import Session

# working with images
from PIL import Image

# import engine
from db import engine

# import database
from db.models import Chat

# import link types and other info
from extra import LinkType, link_dict, TwitterStyle

# settings
from extra.loggers import root_log, file_dir

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

# uploading media
from extra.upload import upload_log

# setup logger
log = logging.getLogger("yoiyoi.app")

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


def exception_handler(func):
    def handler(*args, **kwargs):
        tries = 1
        max_tries = 3
        while tries <= max_tries:
            if tries > 1:
                log.info("Retrying (%d try)...", tries)
            try:
                return func(*args, **kwargs)
            except RetryAfter as ex:
                log.warning("Exception occured: %s.", ex)
                time.sleep(ex.retry_after + 1)
            except TimedOut as ex:
                log.warning("Exception occured: %s.", ex)
                time.sleep(7)
            except Exception as ex:
                log.warning("Exception occured: %s.", ex)
                time.sleep(15)
                break
            finally:
                tries += 1
        else:
            args[0].effective_message.reply_markdown_v2(
                reply_to_message_id=args[0].effective_message.message_id,
                text=f"\\[`ERROR`\\] Couldn't send message, try again later\\.",
            )
            return None

    return handler


@exception_handler
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


@exception_handler
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
    toggle: tuple[str, bool] = None,
) -> None:
    """Log that something hapened

    Args:
        update (Update): current update
        command (str, optional): called command. Defaults to None.
    """
    if inline:
        return log.info(
            "[%d] %r invoked inline mode.",
            update.effective_user.id,
            update.effective_user.full_name,
        )
    cht = update.effective_chat
    if command:
        return log.info(
            "[%d] %r called command: %r.",
            cht.id,
            cht.full_name or cht.title,
            command,
        )
    if func:
        return log.info(
            "[%d] %r called function: %r.",
            cht.id,
            cht.full_name or cht.title,
            func,
        )
    if toggle:
        return log.info(
            "[%d] %r called toggler: %r is now %s.",
            cht.id,
            cht.full_name or cht.title,
            toggle[0],
            _switch[toggle[1]],
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
        state = not getattr(u, attr)
        setattr(u, attr, state)
        s.commit()
        notify(update, toggle=(attr, state))
        return state


def get_chat(cht: Chat):
    with Session(engine) as session:
        session.expire_on_commit = False
        is_not_user = cht.id < 0
        if not (chat := session.get(Chat, cht.id)):
            session.add(
                chat := Chat(
                    id=cht.id,
                    type=cht.type,
                    name=cht.title if is_not_user else cht.full_name,
                    chat_link=cht.username,
                    tw_orig=is_not_user,
                    tw_style=2 if is_not_user else 0,
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
    return chat


################################################################################
# telegram bot
################################################################################


def command_start(update: Update, _) -> None:
    """Start the bot"""
    notify(update, command="/start")
    get_chat(update.effective_chat)
    update.effective_message.reply_markdown_v2(
        text=f"Yo\\~, {update.effective_user.mention_markdown_v2()}\\!\n"
        "I'm *Yoi Yoi* chan\\! 🎉\n"
        "Call for /help if in need\\!",
    )


def command_help(update: Update, _) -> None:
    """Send help message"""
    notify(update, command="/help")
    send_reply(
        update, Path(os.environ["HELP_FILE"]).read_text(encoding="utf-8")
    )


def command_in_hd(update: Update, _) -> None:
    """Enables/Disables Instagram HD mode"""
    notify(update, command="/command_instagram_hd")
    send_reply(
        update,
        f"Instagram HD mode is *{_switch[toggler(update, 'in_orig')]}*\\.",
    )


def command_tw_hd(update: Update, _) -> None:
    """Enables/Disables Twitter HD mode"""
    notify(update, command="/command_twitter_hd")
    send_reply(
        update,
        f"Twitter HD mode is *{_switch[toggler(update, 'tw_orig')]}*\\.",
    )


def command_tt_hd(update: Update, _) -> None:
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


def command_tw_style(update: Update, _) -> None:
    """Change twitter style."""
    notify(update, command="/twitter_style")
    # get old and new styles
    with Session(engine) as s:
        u = s.get(Chat, update.effective_chat.id)
        style = TwitterStyle.styles[(u.tw_style + 1) % len(TwitterStyle.styles)]
        u.tw_style = style
        s.commit()
    # demonstrate new style
    link = esc("https://twitter.com/")
    match style:
        case TwitterStyle.IMAGE_LINK:
            style = "\\[ `Image(s)` \\]\n\nLink"
        case TwitterStyle.IMAGE_INFO_EMBED_LINK:
            style = f"\\[ `Image(s)` \\]\n\n[Author \\| @Username]({link})"
        case TwitterStyle.IMAGE_INFO_EMBED_LINK_DESC:
            style = f"\\[ `Image(s)` \\]\n\n[Author \\| @Username]({link})\n\nDescription"
        case _:
            style = "Unknown"
    send_reply(update, f"_Twitter style has been changed to_\\:\n\n{style}")


def inliner(update: Update, context: CallbackContext) -> None:
    """Answers to inline input

    Args:
        update (Update): telegram update object
        context (CallbackContext): telegram context object
    """
    notify(update, inline=True)
    if not (links := formatter(update.inline_query.query)):
        return log.info("Inline: No query.")
    results = []
    for in_id, in_link in enumerate(links, 1):
        log.info(
            "Inline: [#%02d] Received %s link: %s.",
            in_id,
            LinkType.getType(in_link.type),
            in_link.link,
        )
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
                        log.info("Inline: [#%02d] Appended video.", in_id)
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
            log.info("Inline: [#%02d] Error: %s.", in_id, text)
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

# max image side length
IMAGE_LIMIT = 2560


def to_png(image: bytes, filename: str = "temp") -> bytes:
    # check extension
    file_ext = magic.from_buffer(image, mime=True).split("/")[1]
    log.info(f"Image extension: %s.", file_ext)
    # failed case
    if file_ext == "xml":
        log.info("XML: %r.", image.decode('utf-8'))
    # convert if needed
    if file_ext != "png":
        # save as file
        file = file_dir / f"{filename}.{file_ext}"
        file.write_bytes(image)
        log.debug("Fitting into %d x %d size...", IMAGE_LIMIT, IMAGE_LIMIT)
        try:
            image = Image.open(file)
            image.thumbnail([IMAGE_LIMIT, IMAGE_LIMIT])
            image.save(file, format="png", optimize=True)
        except Exception as ex:
            log.error("Exception occured: %s.", ex)
        image = file.read_bytes()
        file.unlink()
    return image


def get_text(update: Update):
    mes = update.effective_message
    return "|".join(
        text
        for text in [mes.text, mes.caption]
        + [entity.url for entity in mes.entities + mes.caption_entities]
        if text
    )


@exception_handler
def send_media_group(update: Update, context: CallbackContext, **kwargs):
    return context.bot.send_media_group(**kwargs)


def send_tw(
    update: Update,
    context: CallbackContext,
    link: Link,
    chat: Chat,
) -> None:
    notify(update, func="send_twitter")
    # prepare data
    mes = update.effective_message
    reply = {
        "reply_to_message_id": None if chat.include_link else mes.message_id,
        "chat_id": mes.chat_id,
    }
    # get media
    log.info("Send Twitter: Link: %s.", link.link)
    if media := get_twitter_links(link.id):
        log.debug("Send Twitter: Media info: %r.", media)
        info = None
        if chat.include_link:
            _link, _user, _username, _desc = (
                esc(media.source),
                esc(media.user),
                esc(media.username),
                esc(media.desc),
            )
            match chat.tw_style:
                case TwitterStyle.IMAGE_LINK:
                    info = _link
                case TwitterStyle.IMAGE_INFO_EMBED_LINK:
                    info = f"[{_user} \\| @{_username}]({_link})"
                case TwitterStyle.IMAGE_INFO_EMBED_LINK_DESC:
                    info = f"[{_user} \\| @{_username}]({_link})\n\n{_desc}"
                case _:
                    info = _link
        if media.media == "photo":
            photos, documents = [], []
            for photo in media.links:
                log.debug("Send Twitter: Link: %r.", photo)
                log.debug("Send Twitter: Downloading...")
                file = requests.get(
                    url=photo,
                    headers=fake_headers,
                    allow_redirects=True,
                )
                log.debug("Send Twitter: Adding content to collection...")
                filename = "{}.{}".format(
                    re.search(link_dict["twitter"]["file"], photo)["id"],
                    magic.from_buffer(file.content, mime=True).split("/")[1],
                )
                log.debug("Send Twitter: Filename: %r.", filename)
                log.info(
                    "Send Twitter: File extension: %s.",
                    magic.from_buffer(file.content),
                )
                photos.append(
                    InputMediaPhoto(
                        to_png(image=file.content, filename=filename)
                    )
                )
                documents.append(
                    InputMediaDocument(
                        media=file.content,
                        filename=filename,
                        disable_content_type_detection=True,
                    )
                )
            log.debug("Send Twitter: Finished adding to collection.")
            log.debug("Send Twitter: Changing caption to %r.", info)
            photos[0].caption = info
            photos[0].parse_mode = MDV2
            log.info("Send Twitter: Sending media group...")
            if chat.type == "private":
                mes.chat.send_action(ChatAction.UPLOAD_PHOTO)
            # send photo group
            post = send_media_group(update, context, **reply, media=photos)
            # send document group
            if chat.tw_orig and post:
                # documents[-1].caption = info
                log.info("Send Twitter: Sending document group...")
                send_media_group(
                    update,
                    context,
                    chat_id=mes.chat_id,
                    reply_to_message_id=post[0].message_id,
                    media=documents,
                )
        else:
            # send video and gifs as is
            log.info("Send Twitter: Sending media as is...")
            for media in media.links:
                context.bot.send_document(
                    **reply,
                    caption=info,
                    document=media,
                    parse_mode=MDV2,
                )
        return
    else:
        text = (
            f"[This twitter content]({link.link}) can't be found or "
            "downloaded\\. If this seems to be wrong, try again later\\."
        )
        log.error("Send Twitter: Couldn't get content.")
    send_error(update, text)


def send_tt(
    update: Update,
    context: CallbackContext,
    link: Link,
    chat: Chat,
) -> None:
    notify(update, func="send_tiktok")
    # prepare data
    mes = update.effective_message
    reply = {
        "reply_to_message_id": None if chat.include_link else mes.message_id,
        "chat_id": mes.chat_id,
    }
    # get media
    log.info("Send Tiktok: Link: %s.", link.link)
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
            # check extension
            file_ext = magic.from_buffer(vid.content, mime=True).split("/")[1]
            log.info("Send Tiktok: File extension: %s.", file_ext)
            # save as file
            filename = f"{video.id}-{mes.chat_id}.{file_ext}"
            file = file_dir / filename
            file.write_bytes(vid.content)
            # convert if needed
            if file_ext != "mp4":
                mp4 = file_dir / f"{video.id}.mp4"
                log.info("Send Tiktok: Converting...")
                ffmpeg.input(str(file)).output(str(mp4)).run()
                reply["video"] = mp4.read_bytes()
                mp4.unlink()
            else:
                reply["video"] = file.read_bytes()
            # notify user
            if chat.type == "private":
                mes.chat.send_action(ChatAction.UPLOAD_VIDEO)
            # upload
            log.info("Send Tiktok: Sending video...")
            context.bot.send_video(
                **reply,
                caption=info,
                filename=f"{video.id}.mp4",
            )
            # delete
            file.unlink()
            return
        # if file is too big
        else:
            text = "Sorry, this file is too big\\!"
    # if there is no video
    else:
        text = (
            f"[This tiktok content]({link.link}) can't be found or "
            "downloaded\\. If this seems to be wrong, try again later\\."
        )
        log.error("Send Tiktok: Couldn't get content.")
    send_error(update, text)


def send_in(
    update: Update,
    context: CallbackContext,
    link: Link,
    chat: Chat,
) -> None:
    notify(update, func="send_instagram")
    # prepare data
    mes = update.effective_message
    reply = {
        "reply_to_message_id": None if chat.include_link else mes.message_id,
        "chat_id": mes.chat_id,
    }
    # get media
    log.info("Send Instagram: Link: %s.", link.link)
    if media := get_instagram_links(link.link):
        files, documents = [], []
        info = media[0].source if chat.include_link else None
        for item in media:
            log.debug("Send Instagram: Link: %s.", item.link)
            log.debug("Send Instagram: Downloading...")
            file = requests.get(
                item.link,
                headers=fake_headers,
                allow_redirects=True,
            )
            log.debug("Send Instagram: Adding content to collection...")
            if item.type == "image":
                if chat.type == "private":
                    mes.chat.send_action(ChatAction.UPLOAD_PHOTO)
                filename = "{}.{}".format(
                    re.search(link_dict["instagram"]["file"], item.link)["id"],
                    magic.from_buffer(file.content, mime=True).split("/")[1],
                )
                log.debug("Send Instagram: Filename: %r.", filename)
                log.info(
                    "Send Instagram: File extension: %s.",
                    magic.from_buffer(file.content),
                )
                files.append(InputMediaPhoto(to_png(file.content, filename)))
                documents.append(
                    InputMediaDocument(
                        media=file.content,
                        filename=filename,
                        disable_content_type_detection=True,
                    )
                )
            if item.type == "video":
                if chat.type == "private":
                    mes.chat.send_action(ChatAction.UPLOAD_VIDEO)
                files.append(InputMediaVideo(file.content))
        log.debug("Send Instagram: Finished adding to collection.")
        log.debug("Send Instagram: Changing caption to: %r.", info)
        files[0].caption = info
        log.info("Send Instagram: Sending media group...")
        # send file group
        post = send_media_group(update, context, **reply, media=files)
        # send document group
        if chat.in_orig and documents and post:
            # documents[-1].caption = info
            log.info("Send Instagram: Sending document group...")
            send_media_group(
                update,
                context,
                chat_id=mes.chat_id,
                reply_to_message_id=post[0].message_id,
                media=documents,
            )
        return
    # if no links returned
    else:
        text = (
            f"[This instagram content]({link.link}) can't be found or "
            "downloaded\\. If this seems to be wrong, try again later\\."
        )
        log.error("Send Instagram: Couldn't get content.")
    send_error(update, text)


def echo(update: Update, context: CallbackContext) -> None:
    """Answers to user's links

    Args:
        update (Update): telegram update object
        context (CallbackContext): telegram context object
    """
    notify(update, func="echo")
    # check for text
    if not (text := get_text(update)):
        # no text found!
        return log.info("Echo: No text.")
    log.debug("Echo: Received text: %r.", text)
    chat = get_chat(update.effective_chat)
    for link in formatter(text):
        match link.type:
            case LinkType.INSTAGRAM:
                send_in(update, context, link, chat)
            case LinkType.TIKTOK:
                send_tt(update, context, link, chat)
            case LinkType.TWITTER:
                send_tw(update, context, link, chat)
            case _:
                send_reply(update, esc(link.link))
        time.sleep(5)


################################################################################
# main body
################################################################################


def main() -> None:
    """Set up and run the bot"""
    # create updater & dispatcher
    updater = Updater(os.environ["TOKEN"])

    # start bot
    updater.start_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", "8443")),
        url_path=os.environ["TOKEN"],
        webhook_url=f"https://{os.environ['APP_NAME']}.herokuapp.com/{os.environ['TOKEN']}",
    )
    dispatcher = updater.dispatcher

    # start the bot
    dispatcher.add_handler(CommandHandler("start", command_start))

    # get help
    dispatcher.add_handler(CommandHandler("help", command_help))

    # toggle hd quality for instagram
    dispatcher.add_handler(CommandHandler("instagram_hd", command_in_hd))

    # toggle hd quality for twitter
    dispatcher.add_handler(CommandHandler("twitter_hd", command_tw_hd))

    # cycle through twitter styles
    dispatcher.add_handler(CommandHandler("twitter_style", command_tw_style))

    # toggle hd quality for tiktok
    dispatcher.add_handler(CommandHandler("tiktok_hd", command_tt_hd))

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
    root_log.info("Starting the bot...")
    # start the bot
    main()
    # upload log
    upload_log()
