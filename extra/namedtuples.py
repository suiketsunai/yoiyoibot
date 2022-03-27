from collections import namedtuple

# main namedtuple for any links
Link = namedtuple(
    "Link",
    [
        "type",
        "link",
        "id",
    ],
)

TikTokVideo = namedtuple(
    "TikTokVideo",
    [
        "id",
        "link",
        "link_hd",
        "size",
        "size_hd",
        "thumb_0",
        "thumb_1",
    ],
)

TwitterMedia = namedtuple(
    "TwitterMedia",
    [
        "link",
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
    ],
)
