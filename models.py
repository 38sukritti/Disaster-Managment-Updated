"""
Pydantic models for data validation in the Disaster Management System
"""
from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

# Enums for validation
class GenderEnum(str, Enum):
    male = "male"
    female = "female"
    other = "other"

class StatusEnum(str, Enum):
    pending = "pending"
    verified = "verified"
    found = "found"
    deceased = "deceased"

class VolunteerStatusEnum(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class AvailabilityEnum(str, Enum):
    immediate = "immediate"
    flexible = "flexible"
    weekends = "weekends"
    evenings = "evenings"

class AgeRangeEnum(str, Enum):
    child = "0-12"
    teen = "13-17"
    adult = "18-59"
    senior = "60+"

# API Request Models
class SOSRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    address: Optional[str] = Field(None, max_length=500, description="Human readable address")

    @validator('latitude')
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @validator('longitude')
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="User message")

    @validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()

class RumorCheckRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Rumor text to verify")
    context: Optional[str] = Field(None, max_length=500, description="Additional context")
    source: Optional[str] = Field(None, max_length=300, description="Source of the rumor")

    @validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()

class UserRegistration(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    location: str = Field(..., min_length=2, max_length=255, description="User location")

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User email address")

class AdminLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Admin username")
    password: str = Field(..., min_length=6, max_length=100, description="Admin password")

class AdminAlert(BaseModel):
    location: str = Field(..., min_length=2, max_length=255, description="Target location")
    message: str = Field(..., min_length=10, max_length=1000, description="Alert message")

class MissingPersonReport(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120, description="Full name of missing person")
    age: Optional[int] = Field(None, ge=0, le=150, description="Age of missing person")
    gender: Optional[GenderEnum] = Field(None, description="Gender")
    last_location: str = Field(..., min_length=2, max_length=255, description="Last known location")
    last_seen_date: Optional[date] = Field(None, description="Last seen date")
    description: str = Field(..., min_length=10, max_length=2000, description="Physical description")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    reporter_name: str = Field(..., min_length=2, max_length=120, description="Reporter name")
    reporter_contact: str = Field(..., min_length=10, max_length=120, description="Reporter contact")
    reporter_relation: str = Field(..., min_length=2, max_length=120, description="Relation to missing person")

    @validator('last_seen_date')
    def validate_date(cls, v):
        if v and v > date.today():
            raise ValueError('Last seen date cannot be in the future')
        return v

class SightingReport(BaseModel):
    missing_person_id: int = Field(..., gt=0, description="Missing person ID")
    sighting_date: date = Field(..., description="Sighting date")
    location: str = Field(..., min_length=2, max_length=255, description="Sighting location")
    details: str = Field(..., min_length=10, max_length=2000, description="Sighting details")
    contact_info: str = Field(..., min_length=10, max_length=120, description="Reporter contact")

    @validator('sighting_date')
    def validate_sighting_date(cls, v):
        if v > date.today():
            raise ValueError('Sighting date cannot be in the future')
        return v

class VolunteerRegistration(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120, description="Volunteer name")
    email: EmailStr = Field(..., description="Volunteer email")
    phone: str = Field(..., min_length=10, max_length=50, description="Phone number")
    location: str = Field(..., min_length=2, max_length=255, description="Volunteer location")
    skills: Optional[str] = Field(None, max_length=1000, description="Skills and expertise")
    availability: AvailabilityEnum = Field(..., description="Availability")
    interests: Optional[List[str]] = Field(None, description="Areas of interest")

    @validator('phone')
    def validate_phone(cls, v):
        # Basic phone validation - digits, spaces, hyphens, parentheses
        import re
        if not re.match(r'^[\d\s\-\(\)\+]+$', v):
            raise ValueError('Invalid phone number format')
        return v

class VolunteerRoleApplication(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120, description="Volunteer name")
    email: EmailStr = Field(..., description="Volunteer email")
    phone: str = Field(..., min_length=10, max_length=50, description="Phone number")
    location: Optional[str] = Field(None, max_length=255, description="Volunteer location")
    role_name: str = Field(..., min_length=2, max_length=120, description="Applied role")
    experience: Optional[str] = Field(None, max_length=2000, description="Relevant experience")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    immediate: Optional[bool] = Field(False, description="Immediate availability")

class MissingPersonSearch(BaseModel):
    name: Optional[str] = Field(None, max_length=120, description="Name to search")
    location: Optional[str] = Field(None, max_length=255, description="Location to search")
    age_range: Optional[AgeRangeEnum] = Field(None, description="Age range filter")

class StatusUpdate(BaseModel):
    status: str = Field(..., min_length=2, max_length=20, description="New status")

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['pending', 'verified', 'found', 'deceased', 'approved', 'rejected']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {valid_statuses}')
        return v

# API Response Models
class SOSResponse(BaseModel):
    success: bool
    message: str
    coordinates: Optional[str] = None
    address: Optional[str] = None
    error: Optional[str] = None

class ChatResponse(BaseModel):
    response: str

class RumorCheckResponse(BaseModel):
    classification: str
    confidence: float
    advice: str
    raw_label: str
    reasons: List[str]
    evaluated_at: str
    error: Optional[str] = None

class StandardResponse(BaseModel):
    success: bool
    message: str
    error: Optional[str] = None

class ValidationErrorResponse(BaseModel):
    error: str
    details: Optional[dict] = None

# Utility function for validation
def validate_request_data(model_class: BaseModel, data: dict):
    """
    Validate request data against a Pydantic model
    Returns: (is_valid: bool, validated_data: dict, errors: dict)
    """
    try:
        validated = model_class(**data)
        return True, validated.dict(), None
    except Exception as e:
        error_details = {}
        if hasattr(e, 'errors'):
            for error in e.errors():
                field = '.'.join(str(x) for x in error['loc'])
                error_details[field] = error['msg']
        return False, None, error_details