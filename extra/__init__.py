# link types
class LinkType:
    types = (
        TWITTER,
        PIXIV,
        TIKTOK,
        INSTAGRAM,
    ) = range(4)

    names = [
        "twitter",
        "pixiv",
        "tiktok",
        "instagram",
    ]

    @classmethod
    def getType(cls, value: int):
        return cls.names[value]

    @classmethod
    def validate(cls, value: int):
        return value in cls.types


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
        (?P<id>[\w\-]+)
        """,
        "link": "https://instagram.com/p/{id}",
        "type": LinkType.INSTAGRAM,
    },
}

insta_file = r"(?:.+\/)(?P<file>\w+\.\w+)(?:\?)"
