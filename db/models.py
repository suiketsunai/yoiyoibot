"""Database module"""
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Boolean,
    Integer,
)
from sqlalchemy.orm import declarative_base, validates

# pretty __repr__ and __str__
from sqlalchemy_repr import RepresentableBase

# import pixiv styles and link types
from extra import TwitterStyle

Base = declarative_base(cls=RepresentableBase)


class Chat(Base):
    __tablename__ = "chat"

    # chat id
    id = Column(BigInteger, primary_key=True, autoincrement=False)
    # chat type
    type = Column(String, nullable=False)
    # chat name
    name = Column(String)
    # chat username / link
    chat_link = Column(String)
    # last sent link info (currently not used, for pixiv)
    last_info = Column(String)

    # twitter original mode
    tw_orig = Column(Boolean, default=False, nullable=False)
    # twitter style
    tw_style = Column(Integer, default=0, nullable=False)

    @validates("tw_style")
    def validate_twitter_style(self, key, value):
        if TwitterStyle.validate(value):
            return value
        raise ValueError(f"Invalid value {value!r} for field {key!r}.")

    # tiktok hd mode
    tt_orig = Column(Boolean, default=False, nullable=False)
    # instagram original mode
    in_orig = Column(Boolean, default=False, nullable=False)
    # include link of media
    include_link = Column(Boolean, default=False, nullable=False)
