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


class User(Base):
    __tablename__ = "user"

    # telegram id
    id = Column(BigInteger, primary_key=True, autoincrement=False)
    # telegram full name
    full_name = Column(String)
    # telegram user name
    nick_name = Column(String)
    # last sent link (currently not used)
    last_link = Column(String)

    # twitter original mode
    tw_orig = Column(Boolean, default=False, nullable=False)
    # tiktok hd mode
    tt_orig = Column(Boolean, default=False, nullable=False)
    # instagram original mode
    in_orig = Column(Boolean, default=False, nullable=False)
    # include link of media
    include_link = Column(Boolean, default=False, nullable=False)
