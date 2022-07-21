"""Instagram module"""
import time
import json
import logging

# http requests
import requests

# import fake headers
from extra.helper import fake_headers

# import ArtWorkMedia
from extra.namedtuples import InstaMedia

# get logger
log = logging.getLogger("yoiyoi.extra.instagram")

################################################################################
# instagram
################################################################################


def get_instagram_links(link: str) -> list[InstaMedia]:
    """Gets links for media provided by link

    Args:
        link (str): instagram link

    Returns:
        InstaMedia: media of instagram post
    """
    base = "https://instadownloader.co/"
    api = f"{base}instagram_post_data.php"
    # get response
    tries, max_tries, response, results = 1, 3, None, []
    while tries <= max_tries:
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
            time.sleep(10)
        finally:
            tries += 1
    if response:
        log.debug("Response: %r.", response.content)
        try:
            r = json.loads(response.json())
        except json.decoder.JSONDecodeError as ex:
            log.error("Exception occured: %r.", ex)
            return results
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
    return results
