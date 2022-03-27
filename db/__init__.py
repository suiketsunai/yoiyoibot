import os

# working with env
from dotenv import load_dotenv

# create engine
from sqlalchemy import create_engine

# import base
from db.models import Base

# load .env file & get config
load_dotenv()

engine = create_engine(
    os.environ["DATABASE_URL"].replace("postgres://", "postgresql://"),
    echo=True,
    future=True,
)
