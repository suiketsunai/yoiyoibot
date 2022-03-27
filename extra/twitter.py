"""Twitter module"""
import os
import re
import logging

# http requests
import requests

# twitter
import tweepy

# import link dictionary
from extra import link_dict

# import fake headers
from extra.helper import fake_headers

# import ArtWorkMedia
from extra.namedtuples import TwitterMedia

# get logger
log = logging.getLogger("yoiyoi.extra.twitter")

################################################################################
# twitter
################################################################################


def get_twitter_media(
    tweet_id: int,
    media_type: str = None,
    image_list: list[str] = None,
) -> list[list[str], list[str]]:
    """Collect media links from tweet data

    Args:
        tweet_id (int): tweet id
        media_type (str, optional): "photo", "video" or "animated_gif".
        Defaults to None.
        image_list (list[str], optional): list of image links. Defaults to None.

    Returns:
        list[list[str], list[str]]: media links
    """
    if media_type == "photo":
        pat = r"""(?x)
            (?:
                (?:media\/)
                (?P<id>[^\.\?]+)
                (?:
                    (?:\?.*format\=)|(?:\.)
                )
            )
            (?P<format>\w+)
        """
        links = []
        for url in image_list:
            args = re.search(pat, url).groupdict()
            links.append(link_dict["twitter"]["full"].format(**args))
        return [links, [link.replace("orig", "large") for link in links]]
    else:
        base = "https://tweetpik.com/twitter-downloader/"
        api = f"https://tweetpik.com/api/tweets/{tweet_id}/video"
        log.debug("Sending request to API: %s...", api)
        s = requests.session()
        res = s.post(
            url=api,
            headers={
                **fake_headers,
                "Referer": base,
            },
        )
        if res.status_code != 200:
            log.warning("Service is unavailable.")
            return None
        log.debug("Received json: %s.", res.json())
        var = res.json()["variants"]
        return [
            [var[-1 % len(var)]["url"]],
            [var[-2 % len(var)]["url"]],
        ]


def get_twitter_links(tid: int) -> TwitterMedia:
    """Get illustration info with twitter api by id

    Args:
        tweet_id (int): tweet id

    Returns:
        ArtWorkMedia: artwork object
    """
    log.debug("Starting Twitter API client...")
    client = tweepy.Client(os.environ["TW_TOKEN"])
    res = client.get_tweet(
        id=tid,
        expansions=[
            "attachments.media_keys",
            "author_id",
        ],
        tweet_fields=[
            "id",
            "text",
            "created_at",
            "entities",
        ],
        user_fields=[
            "id",
            "name",
            "username",
        ],
        media_fields=[
            "type",
            "width",
            "height",
            "preview_image_url",
            "url",
            "duration_ms",
        ],
    )
    log.debug("Response: %s.", res)
    if error := res.errors:
        log.error("%s: %s", error[0]["title"], error[0]["detail"])
        return None
    media = [media for media in res.includes["media"]]
    user, kind = res.includes["users"][0], media[0].type
    if kind == "photo":
        links = get_twitter_media(tid, kind, [e.url for e in media])
    else:
        links = get_twitter_media(tid, kind)
    if not links[0]:
        log.warning("Unexpected error occured: no links.")
        return None
    text = res.data.text
    for url in res.data.entities["urls"][:-1]:
        text = text.replace(url["url"], url["expanded_url"])
    text = text.replace(res.data.entities["urls"][-1]["url"], "")
    return TwitterMedia(
        link_dict["twitter"]["link"].format(id=tid, author=user.username),
        link_dict["twitter"]["type"],
        tid,
        kind,
        user.id,
        user.name,
        user.username,
        res.data.created_at,
        text.strip(),
        links[0],
        links[1],
    )
