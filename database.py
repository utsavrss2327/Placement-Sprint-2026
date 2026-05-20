from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
import secrets

SQLALCHEMY_DATABASE_URL = "sqlite:///./users.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- 1. Our Existing User Table ---
class APIUser(Base):
    __tablename__ = "api_users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    api_key = Column(String, unique=True, index=True)

# --- 2. NEW: Our Secure Notes Table ---
class SecureNote(Base):
    __tablename__ = "secure_notes"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)  # To track WHO owns the note
    content = Column(String)               # The actual secret message

Base.metadata.create_all(bind=engine)

def generate_api_key():
    return secrets.token_urlsafe(32)