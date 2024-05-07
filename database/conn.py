from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

url = os.getenv("DATABASE_URI")

engine = create_engine(url)

Session = sessionmaker(bind=engine, expire_on_commit=False)

db_session = Session()
