"""Instagram module"""
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
    try:
        response = s.post(
            url=api,
            headers={
                **fake_headers,
                "Content-Type": "application/json;charset=utf-8",
                "X-XSRF-TOKEN": requests.utils.unquote(s.cookies["XSRF-TOKEN"]),
            },
            json={
                "link": f"{link}/",
            },
            allow_redirects=True,
            timeout=5,
        )
    except requests.exceptions.Timeout:
        log.error("Read timed out.")
        return None
    r = response.json()["data"]
    if r["status"] == 1:
        if r["type"] == "GraphSidecar":
            items = r["items"]
        else:
            items = [r]
        results = []
        for item in items:
            if "video" in item:
                _type = "video"
                _link = item["video"]["video_url"]
            else:
                _type = "image"
                _link = item["image"]["photos"][2]["url"]
            _prev = item[_type]["display_url"]
            results.append(InstaMedia(_prev, _link, _type))
        return results
    return None
