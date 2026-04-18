from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

class BusinessBase(BaseModel):
    name: str

class BusinessCreate(BusinessBase):
    pass

class Business(BusinessBase):
    id: str
    owner_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ObligationBase(BaseModel):
    vendor_name: str
    amount: Decimal
    currency: Optional[str] = "INR"
    due_date: date
    category: Optional[str] = None
    status: Optional[str] = "pending"

class ObligationCreate(ObligationBase):
    pass

class Obligation(ObligationBase):
    id: str
    business_id: str
    priority_score: Optional[Decimal] = None
    ai_reasoning: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ForecastBase(BaseModel):
    forecast_date: date
    predicted_balance: Decimal
    confidence_lower: Decimal
    confidence_upper: Decimal

class ForecastCreate(ForecastBase):
    pass

class Forecast(ForecastBase):
    id: str
    business_id: str
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class UserLogin(BaseModel):
    email: str
    password: str
