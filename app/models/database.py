from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///app.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Scan(Base):
    __tablename__ = "scans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    onion_url = Column(String)
    http_proxy = Column(String)
    https_proxy = Column(String)
    timestamp = Column(DateTime)
    status = Column(String)
    result = Column(Text)  # Base64 encoded JSON containing posts

class AIReport(Base):
    __tablename__ = "ai_reports"
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), index=True)
    name = Column(String, index=True)  # Matches the scan's name
    timestamp = Column(DateTime)
    status = Column(String)
    classification = Column(Text)  # JSON string of all post classifications


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

