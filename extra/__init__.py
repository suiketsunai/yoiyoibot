"""Extra module"""


# link types
class LinkType:
    types = (
        TWITTER,
        PIXIV,
        TIKTOK,
        INSTAGRAM,
        YOUTUBE_SHORT,
    ) = range(5)

    names = [
        "twitter",
        "pixiv",
        "tiktok",
        "instagram",
        "youtube short",
    ]

    @classmethod
    def getType(cls, value: int):
        return cls.names[value]

    @classmethod
    def validate(cls, value: int):
        return value in cls.types


# twitter styles
class TwitterStyle:
    styles = (
        IMAGE_LINK,
        IMAGE_INFO_EMBED_LINK,
        IMAGE_INFO_EMBED_LINK_DESC,
    ) = range(3)

    @classmethod
    def validate(cls, value: int):
        return value in cls.styles


# link dictionary
link_dict = {
    "twitter": {
        "re": r"""(?x)
            (?:
                (?:www\.)?
                (?:twitter\.com\/)
                (?P<author>.+?)\/
                (?:status(?:es)?\/)
            )
            (?P<id>\d+)
        """,
        "file": r"""(?x)
            (?:
                (?:media\/)
                (?P<id>[^\.\?]+)
                (?:
                    (?:\?.*format\=)|(?:\.)
                )
            )
            (?P<format>\w+)
        """,
        "link": "https://twitter.com/{author}/status/{id}",
        "full": "https://pbs.twimg.com/media/{id}?format={format}&name=orig",
        "type": LinkType.TWITTER,
    },
    "pixiv": {
        "re": r"""(?x)
            (?:
                (?:www\.)?
                (?:pixiv\.net\/)
                (?:\w{2}\/)?
                (?:artworks\/)
            )
            (?P<id>\d+)
        """,
        "link": "https://www.pixiv.net/artworks/{id}",
        "type": LinkType.PIXIV,
    },
    "tiktok": {
        "re": r"""(?x)
            (?:
                (?:(?:www|m)\.)?
                (?:tiktok.com\/)
                (?:v|embed|trending|\@[\w\.]+\/video)
                (?:\/)?
                (?:\?shareId=)?
            )
            (?P<id>\d+)
        """,
        "link": "https://m.tiktok.com/v/{id}",
        "source": "https://www.tiktok.com/@{author}/video/{id}",
        "type": LinkType.TIKTOK,
    },
    "vtiktok": {
        "re": r"""(?x)
            (?:
                (?P<pre>v\w{1})\.
                (?:tiktok.com\/)
            )
            (?P<id>[\w]+)
        """,
        "link": "https://{pre}.tiktok.com/{id}",
        "type": LinkType.TIKTOK,
    },
    "instagram": {
        "re": r"""(?x)
        (?:
            (?:instagram\.com|instagr\.(?:am|com))\/
            (?:p|reel|tv)\/
        )
        (?P<id>[\w\-]{11})
        """,
        "file": r"""(?x)
        (?:
            (?:.+\/)
            (?P<id>\w+)\.
            (?P<ext>\w{3,4})
        )
        """,
        "link": "https://instagram.com/p/{id}",
        "type": LinkType.INSTAGRAM,
    },
    "youtube_short": {
        "re": r"""(?x)
        (?:
            (?:youtube\.com)\/
            (?:shorts)\/
        )
        (?P<id>[\w]{11})
        """,
        "link": "https://www.youtube.com/shorts/{id}",
        "type": LinkType.YOUTUBE_SHORT,
    },
}
