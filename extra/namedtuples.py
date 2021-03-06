"""Namedtuple module"""
from collections import namedtuple

# main namedtuple for any links
Link = namedtuple(
    "Link",
    (
        "type",
        "link",
        "id",
    ),
)

TikTokVideo = namedtuple(
    "TikTokVideo",
    (
        "source",
        "id",
        "link",
        "link_hd",
        "size",
        "size_hd",
        "thumb_0",
        "thumb_1",
    ),
)

TwitterMedia = namedtuple(
    "TwitterMedia",
    (
        "source",
        "type",
        "id",
        "media",
        "user_id",
        "user",
        "username",
        "date",
        "desc",
        "links",
        "thumbs",
    ),
)

InstaMedia = namedtuple(
    "InstaMedia",
    (
        "source",
        "prev",
        "link",
        "type",
    ),
)

YouTubeShortMedia = namedtuple(
    "YouTubeShortMedia",
    (
        "source",
        "id",
        "thumb",
        "title",
        "link",
        "link_lq",
        "size",
        "size_lq",
        "duration",
    ),
)
