from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class PaymentRequest(BaseModel):
    phone_number: str
    amount: float
    account_reference: str = "Order123"
    transaction_desc: str = "Payment"

    @validator('phone_number')
    def validate_phone(cls, v):
        v = ''.join(filter(str.isdigit, v))
        if not v.startswith('254'):
            v = '254' + v.lstrip('0')
        if len(v) != 12:
            raise ValueError('Phone number must be 12 digits (2547XXXXXXXX)')
        return v

    @validator('amount')
    def validate_amount(cls, v):
        if v < 1:
            raise ValueError('Amount must be at least 1KES')
        return v

class TransactionResponse(BaseModel):
    id: int
    phone_number: str
    amount: float
    account_reference: str
    status: str
    mpesa_receipt: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True

class PaymentResponse(BaseModel):
    status: str
    message: str
    checkout_request_id: Optional[str] = None
    transaction_id: Optional[int] = None