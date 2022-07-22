import os

# working with env
from dotenv import load_dotenv

# create engine
from sqlalchemy import create_engine

# load .env file & get config
load_dotenv()

engine = create_engine(
    os.environ["DATABASE_URL"].replace("postgres://", "postgresql://"),
    future=True,
)
