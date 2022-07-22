"""Instagram module"""
import time
import json
import logging

# http requests
import requests

# import fake headers
from extra.helper import fake_headers

# import InstaMedia
from extra.namedtuples import InstaMedia

# get logger
log = logging.getLogger("yoiyoi.extra.instagram")

################################################################################
# instagram
################################################################################

MAX_TRIES = 3
TIMEOUT = 5


def get_instadownloader_links(link: str) -> list[InstaMedia]:
    base = "https://instadownloader.co/"
    api = f"{base}instagram_post_data.php"
    # get response
    tries, response, results = 1, None, []
    while tries <= MAX_TRIES:
        if tries > 1:
            log.info("Retrying (%d try)...", tries)
        try:
            response = requests.post(
                url=api,
                headers={
                    **fake_headers,
                    "Referer": base,
                },
                params={
                    "path": "/",
                    "url": f"{link}/",
                },
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
            r = json.loads(response.json())
            log.debug("JSON: %r.", r)
            for key, items in r.items():
                for item in items:
                    results.append(
                        InstaMedia(
                            link,
                            item["thumbnail"],
                            item["url"],
                            key[:5],
                        )
                    )
        except json.decoder.JSONDecodeError as ex:
            log.error("Exception occured: %r.", ex)
    return results


def get_instagramdownloads_links(link: str) -> list[InstaMedia]:
    base = "https://instagramdownloads.com/"
    api = f"{base}api/post"
    s = requests.session()
    s.get(url=base, headers=fake_headers)
    log.debug(s.cookies.get_dict())
    # get response
    tries, response, results = 1, None, []
    while tries <= MAX_TRIES:
        if tries > 1:
            log.info("Retrying (%d try)...", tries)
        try:
            response = s.post(
                url=api,
                headers={
                    **fake_headers,
                    "Referer": base,
                },
                json={
                    "shortcode": link.rsplit("/", 1)[1],
                },
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
            log.debug("JSON: %r.", r)
            if "carousel_media" in r:
                r = r["carousel_media"]
            else:
                r = [r]
            for media in r:
                if "video_versions" in media:
                    results.append(
                        InstaMedia(
                            link,
                            media["image_versions2"]["candidates"][0]["url"],
                            media["video_versions"][0]["url"],
                            "video",
                        )
                    )
                elif "image_versions2" in media:
                    results.append(
                        InstaMedia(
                            link,
                            media["image_versions2"]["candidates"][1]["url"],
                            media["image_versions2"]["candidates"][0]["url"],
                            "image",
                        )
                    )
        except json.decoder.JSONDecodeError as ex:
            log.error("Exception occured: %r.", ex)
    return results


def get_sssgram_links(link: str) -> list[InstaMedia]:
    base = "https://www.sssgram.com/"
    api = "https://api.sssgram.com/st-tik/ins/dl"
    # get response
    tries, response, results = 1, None, []
    while tries <= MAX_TRIES:
        if tries > 1:
            log.info("Retrying (%d try)...", tries)
        try:
            response = requests.get(
                url=api,
                headers={
                    **fake_headers,
                    "Referer": base,
                },
                params={
                    "url": f"{link}/",
                },
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
            log.debug("JSON: %r.", r)
            for item in r["result"]["insBos"]:
                results.append(
                    InstaMedia(
                        link,
                        item["thumb"],
                        item["url"],
                        "video" if item["type"] == "mp4" else "image",
                    )
                )
        except json.decoder.JSONDecodeError as ex:
            log.error("Exception occured: %r.", ex)
    return results


def get_instagram_links(link: str) -> list[InstaMedia]:
    """Gets links for media provided by link

    Args:
        link (str): instagram link

    Returns:
        InstaMedia: media of instagram post
    """
    if not (ttv := get_instadownloader_links(link)):  # best
        log.warning("Trying another API: InstagramDownloads...")
        if not (ttv := get_instagramdownloads_links(link)):  # best info
            log.warning("Trying another API: SSSGram...")
            if not (ttv := get_sssgram_links(link)):  # okay
                log.warning("Couldn't get instagram content.")
                return []
    return ttv
