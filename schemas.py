"""
Pydantic Schemas
Request/Response models for API validation
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date


# ============ Auth Schemas ============
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    onboarding_completed: bool
    current_stage: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# ============ Profile Schemas ============
class ProfileBase(BaseModel):
    # Academic Background
    education_level: Optional[str] = None
    degree: Optional[str] = None
    major: Optional[str] = None
    graduation_year: Optional[int] = None
    gpa: Optional[float] = None
    
    # Study Goals
    intended_degree: Optional[str] = None
    field_of_study: Optional[str] = None
    target_intake: Optional[str] = None
    preferred_countries: Optional[str] = None  # JSON string
    
    # Budget
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    funding_type: Optional[str] = None
    
    # Exam Readiness
    ielts_status: Optional[str] = None
    ielts_score: Optional[float] = None
    toefl_status: Optional[str] = None
    toefl_score: Optional[int] = None
    gre_status: Optional[str] = None
    gre_score: Optional[int] = None
    gmat_status: Optional[str] = None
    gmat_score: Optional[int] = None
    sop_status: Optional[str] = None


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(ProfileBase):
    pass


class ProfileResponse(ProfileBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class OnboardingComplete(BaseModel):
    profile: ProfileCreate


# ============ University Schemas ============
class UniversityBase(BaseModel):
    name: str
    country: Optional[str] = None
    city: Optional[str] = None
    ranking: Optional[int] = None
    tuition_min: Optional[int] = None
    tuition_max: Optional[int] = None
    programs: Optional[str] = None
    acceptance_rate: Optional[float] = None
    ielts_requirement: Optional[float] = None
    gre_requirement: Optional[int] = None
    toefl_requirement: Optional[int] = None
    application_deadline: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None


class UniversityResponse(UniversityBase):
    id: int
    # AI-calculated fields
    fit_score: Optional[float] = None
    category: Optional[str] = None  # dream, target, safe
    risk_level: Optional[str] = None
    
    class Config:
        from_attributes = True


class ShortlistCreate(BaseModel):
    university_id: int
    category: Optional[str] = None
    notes: Optional[str] = None


class ShortlistedUniversityResponse(BaseModel):
    id: int
    university_id: int
    category: Optional[str] = None
    application_status: Optional[str] = "shortlisted"
    is_locked: bool
    locked_at: Optional[datetime] = None
    notes: Optional[str] = None
    university: UniversityResponse
    
    class Config:
        from_attributes = True


class LockUniversityRequest(BaseModel):
    university_id: int


class UnlockUniversityRequest(BaseModel):
    university_id: int
    confirm: bool = False


# ============ Task Schemas ============
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = "medium"
    due_date: Optional[date] = None


class TaskCreate(TaskBase):
    university_id: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    is_completed: Optional[bool] = None


class TaskResponse(TaskBase):
    id: int
    user_id: int
    university_id: Optional[int] = None
    is_completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Counsellor Schemas ============
class ChatMessage(BaseModel):
    message: str


class ChatResponse(BaseModel):
    message: str
    actions: Optional[List[dict]] = None  # Actions AI wants to take
    suggestions: Optional[List[str]] = None


class VoiceOnboardingMessage(BaseModel):
    transcript: str
    current_step: Optional[str] = None


class VoiceOnboardingResponse(BaseModel):
    response_text: str
    next_step: Optional[str] = None
    extracted_data: Optional[dict] = None
    is_complete: bool = False


# ============ Dashboard Schemas ============
class ProfileStrength(BaseModel):
    academics: str  # strong, average, weak
    exams: str  # not_started, in_progress, completed
    sop: str  # not_started, draft, ready
    overall_score: int  # 0-100


class DashboardResponse(BaseModel):
    user: UserResponse
    profile: Optional[ProfileResponse] = None
    profile_strength: Optional[ProfileStrength] = None
    shortlisted_count: int
    locked_count: int
    pending_tasks: int
    completed_tasks: int
    recent_tasks: List[TaskResponse] = []


# ============ Document Schemas ============
class DocumentBase(BaseModel):
    name: str
    type: str
    size: str
    category: Optional[str] = "academic"
    status: Optional[str] = "pending"


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    id: int
    user_id: int
    file_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UpdateApplicationStatus(BaseModel):
    status: str
