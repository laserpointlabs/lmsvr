"""
Pydantic models for API requests and responses.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class CustomerCreate(BaseModel):
    name: str
    email: EmailStr
    monthly_budget: Optional[float] = None


class CustomerResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    active: bool
    monthly_budget: Optional[float] = None

    class Config:
        from_attributes = True


class APIKeyResponse(BaseModel):
    id: int
    customer_id: int
    key: str  # Only shown once when created
    created_at: datetime
    expires_at: Optional[datetime] = None
    active: bool

    class Config:
        from_attributes = True


class APIKeyListResponse(BaseModel):
    id: int
    customer_id: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    active: bool

    class Config:
        from_attributes = True


class UsageLogResponse(BaseModel):
    id: int
    customer_id: int
    endpoint: str
    model: Optional[str]
    request_count: int
    cost: float
    timestamp: datetime

    class Config:
        from_attributes = True


class PricingConfigCreate(BaseModel):
    model_name: str
    per_request_cost: float
    per_model_cost: float


class PricingConfigResponse(BaseModel):
    id: int
    model_name: str
    per_request_cost: float
    per_model_cost: float
    active: bool

    class Config:
        from_attributes = True


class ModelInfo(BaseModel):
    id: str
    name: str
    pricing_configured: bool = False


class ModelsListResponse(BaseModel):
    models: List[ModelInfo]


class ChatRequest(BaseModel):
    model: str
    messages: List[dict]
    stream: Optional[bool] = False
    options: Optional[dict] = None


class GenerateRequest(BaseModel):
    model: str
    prompt: str
    stream: Optional[bool] = False
    options: Optional[dict] = None


class OpenAICompletionsRequest(BaseModel):
    model: str
    messages: List[dict]
    stream: Optional[bool] = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None

