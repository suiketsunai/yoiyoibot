"""Instagram module"""
import time
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
    base = "https://sssinstagram.com/"
    api = f"{base}request"
    s = requests.session()
    s.get(url=base, headers=fake_headers)
    log.debug(s.cookies.get_dict())
    # get response
    tries, max_tries, response, results = 1, 3, None, []
    while tries <= max_tries:
        if tries > 1:
            log.info("Retrying (%d try)...", tries)
        try:
            response = s.post(
                url=api,
                headers={
                    **fake_headers,
                    "Content-Type": "application/json;charset=utf-8",
                    "X-XSRF-TOKEN": requests.utils.unquote(
                        s.cookies["XSRF-TOKEN"]
                    ),
                },
                json={
                    "link": f"{link}/",
                },
                allow_redirects=True,
                timeout=5,
            )
            break
        except requests.exceptions.Timeout:
            log.warning("Read timed out.")
            time.sleep(5)
        finally:
            tries += 1
    if response and (r := response.json()["data"]) and r["status"] == 1:
        items = r["items"] if r["type"] == "GraphSidecar" else [r]
        for item in items:
            if "video" in item:
                _type = "video"
                _link = item["video"]["video_url"]
            else:
                _type = "image"
                _link = item["image"]["photos"][2]["url"]
            _prev = item[_type]["display_url"]
            results.append(InstaMedia(link, _prev, _link, _type))
    return results
