from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

url = URL.create(
    drivername="postgresql",
    host=os.getenv("HOST"),
    password=os.getenv("PASSWORD"),
    database=os.getenv("DATABASE"),
    username=os.getenv("USER"),
)

engine = create_engine(url)

Session = sessionmaker(bind=engine, expire_on_commit=False)

db_session = Session()
