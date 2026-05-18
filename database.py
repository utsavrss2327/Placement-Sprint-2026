from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
import secrets

# 1. Create a local SQLite database file named 'users.db'
SQLALCHEMY_DATABASE_URL = "sqlite:///./users.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 2. Define our SQL Table Schema
class APIUser(Base):
    __tablename__ = "api_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    api_key = Column(String, unique=True, index=True)

# 3. Create the tables in the database
Base.metadata.create_all(bind=engine)

# 4. Helper function to generate a secure, random API key
def generate_api_key():
    return secrets.token_urlsafe(32)