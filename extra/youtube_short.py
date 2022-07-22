"""YouTube Short module"""
import time
import json
import logging

# http requests
import requests

# import fake headers
from extra.helper import fake_headers, get_file_size

# import ArtWorkMedia
from extra.namedtuples import YouTubeShortMedia

# get logger
log = logging.getLogger("yoiyoi.extra.youtube_short")

MAX_TRIES = 3
TIMEOUT = 5


def get_youtube_short_links(link: str):
    base = "https://ytshorts.savetube.me/"
    api = "https://api.savetube.me/info"
    # get response
    tries, response = 1, None
    while tries <= MAX_TRIES:
        if tries > 1:
            log.info("Retrying (%d try)...", tries)
        try:
            response = requests.get(
                url=api,
                headers={**fake_headers, "Referer": base},
                params={"url": link},
                allow_redirects=True,
                timeout=10,
            )
            break
        except requests.exceptions.Timeout:
            log.warning("Read timed out.")
            time.sleep(TIMEOUT)
        finally:
            tries += 1
    if response:
        log.debug("Response: %r.", response.content)
        try:
            r = response.json()
            log.info("JSON: %r.", r)
            if r["status"]:
                data, videos = r["data"], r["data"]["video_formats"]
                _link, _quality = videos[0]["url"], videos[0]["quality"]
                _link_lq, _size_lq = None, 0
                for video in data["video_formats"][1:]:
                    if video["url"] and video["quality"] != _quality:
                        _link_lq = video["url"]
                        _size_lq = get_file_size(_link_lq)
                return YouTubeShortMedia(
                    link,
                    data["id"],
                    data["thumbnail"],
                    data["title"],
                    _link,
                    _link_lq,
                    get_file_size(_link),
                    _size_lq,
                    data["duration"],
                )
            else:
                log.error("Couldn't download video!")
        except json.decoder.JSONDecodeError as ex:
            log.error("Exception occured: %r.", ex)
    return None
