"""
Profile Router
Onboarding and profile management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json

from database import get_db
from models import User, Profile, Task
from schemas import (
    ProfileCreate, 
    ProfileUpdate, 
    ProfileResponse, 
    OnboardingComplete,
    ProfileStrength,
    DashboardResponse,
    TaskResponse
)
from auth import get_current_user

router = APIRouter()


def calculate_profile_strength(profile: Profile) -> ProfileStrength:
    """Calculate profile strength based on completed fields"""
    # Academic strength
    has_gpa = profile.gpa is not None and profile.gpa > 0
    has_degree = profile.degree is not None
    has_major = profile.major is not None
    
    academic_score = sum([has_gpa, has_degree, has_major])
    if academic_score >= 3:
        academics = "strong"
    elif academic_score >= 1:
        academics = "average"
    else:
        academics = "weak"
    
    # Exam readiness
    ielts_done = profile.ielts_status == "completed"
    gre_done = profile.gre_status == "completed"
    
    exam_score = sum([ielts_done, gre_done])
    if exam_score >= 2:
        exams = "completed"
    elif profile.ielts_status == "preparing" or profile.gre_status == "preparing":
        exams = "in_progress"
    else:
        exams = "not_started"
    
    # SOP status
    sop = profile.sop_status or "not_started"
    
    # Overall score (0-100)
    overall = 0
    overall += 30 if academics == "strong" else (15 if academics == "average" else 0)
    overall += 30 if exams == "completed" else (15 if exams == "in_progress" else 0)
    overall += 20 if sop == "ready" else (10 if sop == "draft" else 0)
    overall += 20 if profile.preferred_countries else 0
    
    return ProfileStrength(
        academics=academics,
        exams=exams,
        sop=sop,
        overall_score=overall
    )


@router.get("/", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile"""
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    return profile


@router.put("/", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)
    
    # Update only provided fields
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/onboarding/complete", response_model=ProfileResponse)
async def complete_onboarding(
    onboarding_data: OnboardingComplete,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete onboarding and save profile"""
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)
    
    # Update profile with onboarding data
    update_data = onboarding_data.profile.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    # Mark onboarding as complete
    current_user.onboarding_completed = True
    current_user.current_stage = 2  # Move to Stage 2: Discovering Universities
    
    db.commit()
    db.refresh(profile)
    
    # Create initial tasks
    create_initial_tasks(db, current_user.id, profile)
    
    return profile


def create_initial_tasks(db: Session, user_id: int, profile: Profile):
    """Create initial tasks based on profile"""
    tasks_to_create = []
    
    # Exam tasks
    if profile.ielts_status != "completed":
        tasks_to_create.append(Task(
            user_id=user_id,
            title="Prepare for IELTS/TOEFL",
            description="Register and prepare for English proficiency test",
            category="exam",
            priority="high"
        ))
    
    if profile.gre_status != "completed" and profile.intended_degree in ["masters", "phd"]:
        tasks_to_create.append(Task(
            user_id=user_id,
            title="Prepare for GRE",
            description="Register and prepare for GRE exam",
            category="exam",
            priority="high"
        ))
    
    # SOP task
    if profile.sop_status != "ready":
        tasks_to_create.append(Task(
            user_id=user_id,
            title="Draft Statement of Purpose",
            description="Write the first draft of your SOP",
            category="document",
            priority="medium"
        ))
    
    # General tasks
    tasks_to_create.append(Task(
        user_id=user_id,
        title="Research universities",
        description="Use AI Counsellor to discover matching universities",
        category="general",
        priority="high"
    ))
    
    for task in tasks_to_create:
        db.add(task)
    db.commit()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard data for current user"""
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    
    # Calculate profile strength
    profile_strength = None
    if profile:
        profile_strength = calculate_profile_strength(profile)
    
    # Count shortlisted and locked universities
    from models import ShortlistedUniversity
    shortlisted = db.query(ShortlistedUniversity).filter(
        ShortlistedUniversity.user_id == current_user.id
    ).all()
    
    shortlisted_count = len(shortlisted)
    locked_count = len([s for s in shortlisted if s.is_locked])
    
    # Count tasks
    tasks = db.query(Task).filter(Task.user_id == current_user.id).all()
    pending_tasks = len([t for t in tasks if not t.is_completed])
    completed_tasks = len([t for t in tasks if t.is_completed])
    
    return DashboardResponse(
        user=current_user,
        profile=profile,
        profile_strength=profile_strength,
        shortlisted_count=shortlisted_count,
        locked_count=locked_count,
        pending_tasks=pending_tasks,
        completed_tasks=completed_tasks,
        recent_tasks=[t for t in tasks if not t.is_completed]
    )


@router.get("/strength", response_model=ProfileStrength)
async def get_profile_strength(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get profile strength analysis"""
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    return calculate_profile_strength(profile)
