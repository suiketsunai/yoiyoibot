"""TikTok module"""
import re
import logging

# http requests
import requests

# import link dictionary
from extra import link_dict

# import fake headers and getting file size function
from extra.helper import fake_headers, get_file_size

# import ArtWorkMedia
from extra.namedtuples import TikTokVideo

# get logger
log = logging.getLogger("yoiyoi.extra.tiktok")

# tiktok thumbnail link
thumb = "https://www.tiktok.com/api/img/?itemId={0}&location={1}"

################################################################################
# tiktok
################################################################################


def get_yt4k_links(link: str) -> TikTokVideo:
    """Makes POST request to YouTube4K API

    Args:
        link (str): formatted tiktok link

    Returns:
        TikTokVideo: tiktok video namedtuple
    """
    base = "youtube4kdownloader.com"
    api = f"https://{base}/ajax/getLinks.php?"

    pat = r"bytevc1_540p_\d+-0"
    pat_hd = r"h264_540p_\d+-0"

    log.debug("Sending request to API: %s...", api)
    res = requests.post(
        url=api,
        headers={
            **fake_headers,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": f"https://{base}/",
        },
        params={
            "video": link,
            "rand": 11,
        },
    )

    if res.status_code == 200:
        log.debug("YouTube4K: Request to API succeeded.")
        r = res.json()
        log.debug("YouTube4K: Converted to json: %s.", r)

        if r["status"] == "success":
            r = r["data"]
            _id = r["id"]
            log.info("YouTube4K: Getting links...")
            for tto in r["av"]:
                if re.match(pat, tto["fid"]):
                    link = tto["url"]
                if re.match(pat_hd, tto["fid"]):
                    link_hd = tto["url"]
            log.info("YouTube4K: Collecting file sizes...")
            if size := get_file_size(link):
                return TikTokVideo(
                    link_dict["tiktok"]["link"].format(id=_id),
                    _id,
                    link,
                    link_hd,
                    size,
                    get_file_size(link_hd),
                    thumb.format(_id, 0),
                    thumb.format(_id, 1),
                )
            else:
                log.debug("YouTube4K: No content.")
        else:
            log.info("YouTube4K: Couldn't download tiktok video.")
    else:
        log.info("YouTube4K: Request to API failed.")
        log.debug("YouTube4K: Response: %s", res.text)

    return None


def get_tikmate_links(link: str) -> TikTokVideo:
    """Makes POST request to TikMate API

    Args:
        link (str): formatted tiktok link

    Returns:
        TikTokVideo: tiktok video namedtuple
    """
    base = "tikmate.app"
    api = f"https://api.{base}/api/lookup"
    tikmate = "https://tikmate.app/download/{0}/{1}.mp4{2}"

    log.debug("Sending request to API: %s...", api)
    res = requests.post(
        url=api,
        headers={
            **fake_headers,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": f"https://{base}/",
        },
        data={"url": link},
    )

    if res.status_code == 200:
        log.debug("TikMate: Request to API succeeded.")
        r = res.json()
        log.debug("TikMate: Converted to json: %s.", r)

        if r["success"]:
            _id = r["id"]
            _token = r["token"]
            log.info("TikMate: Getting links...")
            link = tikmate.format(_token, _id, "")
            link_hd = tikmate.format(_token, _id, "?hd=1")
            log.info("TikMate: Collecting file sizes...")
            if size := get_file_size(link):
                return TikTokVideo(
                    link_dict["tiktok"]["source"].format(
                        id=_id,
                        author=r["author_id"],
                    ),
                    _id,
                    link,
                    link_hd,
                    size,
                    get_file_size(link_hd),
                    thumb.format(_id, 0),
                    thumb.format(_id, 1),
                )
            else:
                log.debug("TikMate: No content.")
        else:
            log.info("TikMate: Couldn't download tiktok video.")
    else:
        log.info("TikMate: Request to API failed.")
        log.debug("TikMate: Response: %s", res.text)

    return None


def get_lovetik_links(link: str) -> TikTokVideo:
    """Makes POST request to LoveTik API

    Args:
        link (str): formatted tiktok link

    Returns:
        TikTokVideo: tiktok video namedtuple
    """
    base = "lovetik.com"
    api = f"https://{base}/api/ajax/search"

    log.debug("Sending request to API: %s...", api)
    res = requests.post(
        url=api,
        headers={
            **fake_headers,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": f"https://{base}/",
        },
        data={"query": link},
    )

    if res.status_code == 200:
        log.debug("LoveTik: Request to API succeeded.")
        r = res.json()
        log.debug("LoveTik: Converted to json: %s.", r)

        if r["status"] == "ok" and not r["mess"].startswith("Error"):
            _id = r["vid"]
            log.info("LoveTik: Getting links...")
            link = link_hd = r["links"][0]["a"]
            log.info("LoveTik: Collecting file sizes...")
            if size := get_file_size(link):
                return TikTokVideo(
                    link_dict["tiktok"]["source"].format(
                        id=_id,
                        author=r["author"][1:],
                    ),
                    _id,
                    link,
                    link_hd,
                    size,
                    size,
                    thumb.format(_id, 0),
                    thumb.format(_id, 1),
                )
            else:
                log.debug("LoveTik: No content.")
        else:
            log.info("LoveTik: Couldn't download tiktok video.")
    else:
        log.info("LoveTik: Request to API failed.")
        log.debug("LoveTik: Response: %s", res.text)

    return None


def get_tiktok_links(link: str) -> TikTokVideo:
    """Gets links for tiktok provided by link

    Args:
        link (str): formatted tiktok link

    Returns:
        TikTokVideo: tiktok video namedtuple
    """
    if not (ttv := get_tikmate_links(link)):
        log.warning("Trying another API: LoveTik...")
        if not (ttv := get_lovetik_links(link)):
            log.warning("Couldn't get tiktok.")
            return None
    return ttv
