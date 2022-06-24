"""Database module"""
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Boolean,
)
from sqlalchemy.orm import declarative_base

# pretty __repr__ and __str__
from sqlalchemy_repr import RepresentableBase

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
    # tiktok hd mode
    tt_orig = Column(Boolean, default=False, nullable=False)
    # instagram original mode
    in_orig = Column(Boolean, default=False, nullable=False)
    # include link of media
    include_link = Column(Boolean, default=False, nullable=False)
