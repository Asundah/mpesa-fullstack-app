from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Transaction
from datetime import datetime
from .database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, index=True)
    amount = Column(Float)
    account_reference = Column(String)
    checkout_request_id = Column(String, unique=True, index=True)
    merchant_request_id = Column(String)
    status = Column(String, default="pending") #pending, success, failed
    result_code = Column(Integer, nullable=True)
    result_desc = Column(String, nullable=True)
    mpesa_receipt = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)