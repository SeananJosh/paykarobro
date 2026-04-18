from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    totp_secret = Column(String, nullable=True) # For 2FA
    is_2fa_enabled = Column(Integer, default=0) # 0=Disabled, 1=Enabled
    role = Column(String, default="owner")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    businesses = relationship("Business", back_populates="owner")


class Business(Base):
    __tablename__ = "businesses"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    name = Column(String, nullable=False)
    owner_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="businesses")
    obligations = relationship("Obligation", back_populates="business")
    forecasts = relationship("Forecast", back_populates="business")
    audit_logs = relationship("AgentAuditLog", back_populates="business")


class Obligation(Base):
    __tablename__ = "obligations"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"))
    vendor_name = Column(String, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String, default="INR")
    due_date = Column(Date, nullable=False)
    category = Column(String)
    priority_score = Column(Numeric(5, 2))
    status = Column(String, default="pending")  # pending, approved, paid, deferred
    approval_required = Column(Integer, default=0)
    is_manager_approved = Column(Integer, default=0)
    ai_reasoning = Column(String, nullable=True) # reasoning from the priority agent
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    business = relationship("Business", back_populates="obligations")


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"))
    forecast_date = Column(Date, nullable=False)
    predicted_balance = Column(Numeric(15, 2))
    confidence_lower = Column(Numeric(15, 2))
    confidence_upper = Column(Numeric(15, 2))
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    business = relationship("Business", back_populates="forecasts")


class AgentAuditLog(Base):
    __tablename__ = "agent_audit_log"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"))
    agent_name = Column(String, nullable=False)
    input_summary = Column(String)
    output_summary = Column(String)
    reasoning = Column(String)
    user_action = Column(String) # approved, overridden, dismissed
    executed_at = Column(DateTime(timezone=True), server_default=func.now())

    business = relationship("Business", back_populates="audit_logs")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    obligation_id = Column(String, ForeignKey("obligations.id"))
    business_id = Column(String, ForeignKey("businesses.id"))
    amount = Column(Numeric(15, 2), nullable=False)
    payment_method = Column(String)  # UPI, NEFT, card
    gateway_ref = Column(String)
    status = Column(String, default="initiated") # initiated, success, failed
    executed_at = Column(DateTime(timezone=True), server_default=func.now())


class TransactionHistory(Base):
    """Stores historical bank data for better AI forecasting"""
    __tablename__ = "transaction_history"
    
    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"))
    transaction_date = Column(Date, nullable=False)
    description = Column(String)
    amount = Column(Numeric(15, 2), nullable=False) # positive for credit, negative for debit
    balance_after = Column(Numeric(15, 2))
    category = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
