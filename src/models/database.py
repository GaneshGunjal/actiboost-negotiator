# src/models/database.py - SQLite Version (No Password Issues)
from typing import Optional
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# SQLite - no password needed!
DATABASE_URL = "sqlite:///./actiboost_deals.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(100))
    customer_email = Column(String(100))
    customer_phone = Column(String(20))
    
    project_type = Column(String(50))
    project_size = Column(String(50))
    location = Column(String(100))
    
    initial_price = Column(Float)
    negotiated_price = Column(Float)
    final_price = Column(Float)
    
    negotiation_history = Column(JSON, default=list)
    
    status = Column(String(20))  # pending, approved, rejected, completed
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    
    session_id = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    notes = Column(Text)


class LowIntentLead(Base):
    __tablename__ = "low_intent_leads"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=True)
    user_message = Column(Text)
    classification = Column(String(50), default="low_intent")
    reason = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


class CachedResponse(Base):
    __tablename__ = "cached_responses"

    id = Column(Integer, primary_key=True, index=True)
    query_hash = Column(String(255), unique=True, index=True)
    question = Column(Text)
    classification = Column(String(50), default="technical")
    response_text = Column(Text)
    source = Column(String(50), default="llm")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# Create tables
Base.metadata.create_all(bind=engine)


def _hash_question(question: str) -> str:
    import hashlib
    return hashlib.sha256((question or "").strip().lower().encode("utf-8")).hexdigest()


def save_cached_response(question: str, classification: str, response_text: str, source: str = "llm") -> bool:
    if not question or not response_text:
        return False
    db = SessionLocal()
    try:
        key = _hash_question(question)
        existing = db.query(CachedResponse).filter(CachedResponse.query_hash == key).first()
        if existing:
            existing.response_text = response_text
            existing.classification = classification
            existing.source = source
            existing.updated_at = datetime.now()
        else:
            db.add(CachedResponse(
                query_hash=key,
                question=question.strip(),
                classification=classification,
                response_text=response_text,
                source=source,
            ))
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()


def get_cached_response(question: str, classification: str = "technical") -> Optional[str]:
    if not question:
        return None
    db = SessionLocal()
    try:
        key = _hash_question(question)
        result = db.query(CachedResponse).filter(
            CachedResponse.query_hash == key,
            CachedResponse.classification == classification,
        ).first()
        return result.response_text if result else None
    finally:
        db.close()


def log_low_intent_lead(session_id: Optional[str], user_message: str, classification: str = "low_intent", reason: str = "Low budget and low-intent lead"):
    db = SessionLocal()
    try:
        db.add(LowIntentLead(
            session_id=session_id,
            user_message=user_message,
            classification=classification,
            reason=reason,
        ))
        db.commit()
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()