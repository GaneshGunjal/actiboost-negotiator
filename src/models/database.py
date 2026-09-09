# src/models/database.py
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

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


class LowIntentLead(Base):
    __tablename__ = "low_intent_leads"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=True)
    user_message = Column(Text, nullable=True)
    assistant_response = Column(Text, nullable=True)
    intent_type = Column(String, default="low_intent")
    confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)


class CachedResponse(Base):
    __tablename__ = "cached_responses"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime, nullable=True)


# Create tables
Base.metadata.create_all(bind=engine)


# ========== DATABASE FUNCTIONS ==========

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def log_low_intent_lead(session_id: str, user_message: str, assistant_response: str = "", 
                        intent_type: str = "low_intent", confidence_score: float = 0.0):
    """Log a low intent lead to the database"""
    db = SessionLocal()
    try:
        lead = LowIntentLead(
            session_id=session_id,
            user_message=user_message,
            assistant_response=assistant_response,
            intent_type=intent_type,
            confidence_score=confidence_score
        )
        db.add(lead)
        db.commit()
        return {"success": True, "lead_id": lead.id}
    except Exception as e:
        db.rollback()
        print(f"Error logging low intent lead: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def get_cached_response(query: str):
    """Get a cached response from the database"""
    db = SessionLocal()
    try:
        cache = db.query(CachedResponse).filter(CachedResponse.query == query).first()
        if cache:
            return cache.response
        return None
    except Exception as e:
        print(f"Error getting cached response: {e}")
        return None
    finally:
        db.close()


def save_cached_response(query: str, response: str, ttl_hours: int = 24):
    """Save a response to cache"""
    from datetime import timedelta
    db = SessionLocal()
    try:
        existing = db.query(CachedResponse).filter(CachedResponse.query == query).first()
        if existing:
            existing.response = response
            existing.expires_at = datetime.now() + timedelta(hours=ttl_hours)
            db.commit()
            return {"success": True}
        
        cache = CachedResponse(
            query=query,
            response=response,
            expires_at=datetime.now() + timedelta(hours=ttl_hours)
        )
        db.add(cache)
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        print(f"Error saving cached response: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def get_all_deals():
    """Get all deals from the database"""
    db = SessionLocal()
    try:
        deals = db.query(Deal).order_by(Deal.created_at.desc()).all()
        return [{
            "id": d.id,
            "customer_name": d.customer_name,
            "customer_email": d.customer_email,
            "customer_phone": d.customer_phone,
            "project_type": d.project_type,
            "project_size": d.project_size,
            "location": d.location,
            "initial_price": d.initial_price,
            "final_price": d.final_price,
            "status": d.status,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "approved_by": d.approved_by
        } for d in deals]
    except Exception as e:
        print(f"Error getting deals: {e}")
        return []
    finally:
        db.close()


def save_deal(deal_data: dict):
    """Save a deal to the database"""
    db = SessionLocal()
    try:
        deal = Deal(
            customer_name=deal_data.get("customer_name"),
            customer_email=deal_data.get("customer_email"),
            customer_phone=deal_data.get("customer_phone"),
            project_type=deal_data.get("project_type", "Construction"),
            project_size=deal_data.get("project_size", ""),
            location=deal_data.get("location", ""),
            initial_price=deal_data.get("initial_price", 0),
            final_price=deal_data.get("final_price", 0),
            status=deal_data.get("status", "pending"),
            session_id=deal_data.get("session_id"),
            negotiation_history=deal_data.get("negotiation_history", [])
        )
        db.add(deal)
        db.commit()
        db.refresh(deal)
        return {"success": True, "deal_id": deal.id}
    except Exception as e:
        db.rollback()
        print(f"Error saving deal: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()