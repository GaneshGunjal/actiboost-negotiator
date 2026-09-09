# src/models/database.py
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Get database URL from environment variable
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///actiboost_deals.db")

# Handle SQLite vs PostgreSQL
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)
    project_type = Column(String, nullable=False)
    project_size = Column(String, nullable=True)
    location = Column(String, nullable=True)
    initial_price = Column(Float, nullable=False)
    final_price = Column(Float, nullable=True)
    status = Column(String, default="pending")
    session_id = Column(String, nullable=True)
    negotiation_history = Column(JSON, default=[])
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

# Create tables
Base.metadata.create_all(bind=engine)