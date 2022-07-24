"""YouTube Short module"""
import json
import logging

from typing import Optional

# http requests
import requests

# import fake headers
from extra.helper import fake_headers, get_file_size

# import ArtWorkMedia
from extra.namedtuples import YouTubeShortMedia

# get logger
log = logging.getLogger("yoiyoi.extra.youtube_short")


def get_ytshorts_links(link: str) -> Optional[YouTubeShortMedia]:
    base = "https://ytshorts.savetube.me/"
    api = "https://api.savetube.me/info"
    # get response
    response = None
    try:
        response = requests.get(
            url=api,
            headers={**fake_headers, "Referer": base},
            params={"url": link},
            allow_redirects=True,
            timeout=3,
        )
    except requests.exceptions.Timeout:
        log.warning("Read timed out.")
    if response:
        log.debug("Response: %r.", response.content)
        try:
            r = response.json()
            log.debug("JSON: %r.", r)
            if r["status"]:
                data, videos = r["data"], r["data"]["video_formats"]
                _link = videos[0]["url"]
                _link_lq = next(
                    filter(
                        lambda video: video["url"]
                        and video["quality"] != videos[0]["quality"],
                        data["video_formats"][1:],
                    ),
                    {},
                ).get("url", None)
                if size := get_file_size(_link):
                    return YouTubeShortMedia(
                        link,
                        data["id"],
                        data["thumbnail"],
                        data["title"],
                        _link,
                        _link_lq,
                        size,
                        get_file_size(_link_lq),
                        data["duration"],
                    )
            else:
                log.error("Couldn't download video!")
        except json.decoder.JSONDecodeError as ex:
            log.error("Exception occured: %r.", ex)
    return None


def get_ssyoutube_links(link: str) -> Optional[YouTubeShortMedia]:
    base = "https://ssyoutube.com/en6/"
    api = "https://ssyoutube.com/api/convert"
    link = "https://www.youtube.com/shorts/ckUx9TCpDBU"
    # get cookies
    s = requests.session()
    s.get(url=base, headers=fake_headers)
    log.debug(s.cookies.get_dict())
    # get response
    response = None
    try:
        response = requests.post(
            url=api,
            headers={**fake_headers, "Referer": base},
            params={"url": link},
            allow_redirects=True,
            timeout=3,
        )
    except requests.exceptions.Timeout:
        log.warning("Read timed out.")
    if response:
        log.debug("Response: %r.", response.content)
        try:
            r = response.json()
            log.debug("JSON: %r.", r)
            if "meta" in r:
                meta, videos = r["meta"], (
                    url
                    for url in r["url"]
                    if url.get("downloadable", True)
                    and url.get("audio", True)
                    and url.get("ext", "mp4") in ("webm", "mp4")
                )
                _link = next(videos)["url"]
                _link_lq = next(videos, {}).get("url", _link)
                if size := get_file_size(_link):
                    return YouTubeShortMedia(
                        link,
                        r["id"],
                        r["thumb"],
                        meta["title"],
                        _link,
                        _link_lq,
                        size,
                        get_file_size(_link_lq),
                        sum(
                            unit * mul
                            for unit, mul in zip(
                                map(int, reversed(meta["duration"].split(":"))),
                                (1, 60, 3600, 86400),
                            )
                        ),
                    )
            else:
                log.error("Couldn't download video: %s.", r["message"])
        except json.decoder.JSONDecodeError as ex:
            log.error("Exception occured: %r.", ex)
    return None


def get_youtube_short_links(link: str) -> Optional[YouTubeShortMedia]:
    if not (ytsm := get_ytshorts_links(link)):  # best
        log.warning("Trying another API: SSYouTube...")
        if not (ytsm := get_ssyoutube_links(link)):  # good
            log.warning("Couldn't get youtube content.")
            return None
    return ytsm
