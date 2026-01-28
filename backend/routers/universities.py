"""
Universities Router
University discovery, shortlisting, and locking endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from database import get_db
from models import User, Profile, University, ShortlistedUniversity, Task
from schemas import (
    UniversityResponse, 
    ShortlistCreate, 
    ShortlistedUniversityResponse,
    LockUniversityRequest,
    LockUniversityRequest,
    UnlockUniversityRequest,
    UpdateApplicationStatus
)
from auth import get_current_user

router = APIRouter()


def calculate_fit_score(university: University, profile: Profile) -> tuple:
    """Calculate how well a university fits a user's profile"""
    if not profile:
        return 50, "target", "medium"
    
    score = 50  # Base score
    
    # GPA comparison (if available)
    if profile.gpa and university.acceptance_rate:
        if profile.gpa >= 3.7:
            score += 15
        elif profile.gpa >= 3.3:
            score += 10
        elif profile.gpa >= 3.0:
            score += 5
    
    # Budget match
    if profile.budget_max and university.tuition_max:
        if profile.budget_max >= university.tuition_max:
            score += 15
        elif profile.budget_max >= university.tuition_min:
            score += 8
        else:
            score -= 10
    
    # Exam readiness
    if profile.ielts_score and university.ielts_requirement:
        if profile.ielts_score >= university.ielts_requirement:
            score += 10
        else:
            score -= 5
    
    if profile.gre_score and university.gre_requirement:
        if profile.gre_score >= university.gre_requirement:
            score += 10
        else:
            score -= 5
    
    # Country preference match
    if profile.preferred_countries:
        try:
            countries = json.loads(profile.preferred_countries)
            if university.country and university.country.lower() in [c.lower() for c in countries]:
                score += 10
        except:
            pass
    
    # Determine category based on acceptance rate and score
    if university.acceptance_rate:
        if university.acceptance_rate < 15 or score < 50:
            category = "dream"
            risk = "high"
        elif university.acceptance_rate < 35 or score < 70:
            category = "target"
            risk = "medium"
        else:
            category = "safe"
            risk = "low"
    else:
        if score >= 70:
            category = "safe"
            risk = "low"
        elif score >= 50:
            category = "target"
            risk = "medium"
        else:
            category = "dream"
            risk = "high"
    
    return min(100, max(0, score)), category, risk


@router.get("/", response_model=List[UniversityResponse])
async def get_universities(
    country: Optional[str] = Query(None),
    budget_max: Optional[int] = Query(None),
    program: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all universities with optional filters"""
    query = db.query(University)
    
    if country:
        query = query.filter(University.country.ilike(f"%{country}%"))
    
    if budget_max:
        query = query.filter(University.tuition_max <= budget_max)
    
    if program:
        query = query.filter(University.programs.ilike(f"%{program}%"))
    
    universities = query.all()
    
    # Get user profile for fit calculation
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    
    # Add calculated fields
    result = []
    for uni in universities:
        fit_score, category, risk = calculate_fit_score(uni, profile)
        uni_dict = {
            "id": uni.id,
            "name": uni.name,
            "country": uni.country,
            "city": uni.city,
            "ranking": uni.ranking,
            "tuition_min": uni.tuition_min,
            "tuition_max": uni.tuition_max,
            "programs": uni.programs,
            "acceptance_rate": uni.acceptance_rate,
            "ielts_requirement": uni.ielts_requirement,
            "gre_requirement": uni.gre_requirement,
            "toefl_requirement": uni.toefl_requirement,
            "application_deadline": uni.application_deadline,
            "image_url": uni.image_url,
            "description": uni.description,
            "fit_score": fit_score,
            "category": category,
            "risk_level": risk
        }
        result.append(uni_dict)
    
    # Sort by fit score
    result.sort(key=lambda x: x["fit_score"], reverse=True)
    
    return result


@router.get("/recommendations", response_model=List[UniversityResponse])
async def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI-recommended universities based on user profile"""
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete onboarding first to get recommendations"
        )
    
    # Get universities matching user preferences
    query = db.query(University)
    
    # Filter by budget if set
    if profile.budget_max:
        query = query.filter(University.tuition_max <= profile.budget_max * 1.2)  # 20% buffer
    
    # Filter by preferred countries
    if profile.preferred_countries:
        try:
            countries = json.loads(profile.preferred_countries)
            if countries:
                query = query.filter(University.country.in_(countries))
        except:
            pass
    
    universities = query.all()
    
    # Calculate fit and categorize
    result = []
    for uni in universities:
        fit_score, category, risk = calculate_fit_score(uni, profile)
        uni_dict = {
            "id": uni.id,
            "name": uni.name,
            "country": uni.country,
            "city": uni.city,
            "ranking": uni.ranking,
            "tuition_min": uni.tuition_min,
            "tuition_max": uni.tuition_max,
            "programs": uni.programs,
            "acceptance_rate": uni.acceptance_rate,
            "ielts_requirement": uni.ielts_requirement,
            "gre_requirement": uni.gre_requirement,
            "toefl_requirement": uni.toefl_requirement,
            "application_deadline": uni.application_deadline,
            "image_url": uni.image_url,
            "description": uni.description,
            "fit_score": fit_score,
            "category": category,
            "risk_level": risk
        }
        result.append(uni_dict)
    
    result.sort(key=lambda x: x["fit_score"], reverse=True)
    
    return result


@router.get("/shortlist", response_model=List[ShortlistedUniversityResponse])
async def get_shortlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's shortlisted universities"""
    shortlisted = db.query(ShortlistedUniversity).filter(
        ShortlistedUniversity.user_id == current_user.id
    ).all()
    
    result = []
    for s in shortlisted:
        university = db.query(University).filter(University.id == s.university_id).first()
        result.append({
            "id": s.id,
            "university_id": s.university_id,
            "category": s.category,
            "is_locked": s.is_locked,
            "locked_at": s.locked_at,
            "notes": s.notes,
            "university": university
        })
    
    return result


@router.post("/shortlist", response_model=ShortlistedUniversityResponse)
async def add_to_shortlist(
    shortlist_data: ShortlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a university to shortlist"""
    # Check if university exists
    university = db.query(University).filter(University.id == shortlist_data.university_id).first()
    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University not found"
        )
    
    # Check if already shortlisted
    existing = db.query(ShortlistedUniversity).filter(
        ShortlistedUniversity.user_id == current_user.id,
        ShortlistedUniversity.university_id == shortlist_data.university_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="University already in shortlist"
        )
    
    # Calculate category if not provided
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    _, category, _ = calculate_fit_score(university, profile)
    
    shortlisted = ShortlistedUniversity(
        user_id=current_user.id,
        university_id=shortlist_data.university_id,
        category=shortlist_data.category or category,
        notes=shortlist_data.notes
    )
    db.add(shortlisted)
    
    # Update user stage if first shortlist
    if current_user.current_stage < 3:
        current_user.current_stage = 3  # Stage 3: Finalizing Universities
    
    db.commit()
    db.refresh(shortlisted)
    
    return {
        "id": shortlisted.id,
        "university_id": shortlisted.university_id,
        "category": shortlisted.category,
        "is_locked": shortlisted.is_locked,
        "locked_at": shortlisted.locked_at,
        "notes": shortlisted.notes,
        "university": university
    }


@router.delete("/shortlist/{university_id}")
async def remove_from_shortlist(
    university_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a university from shortlist"""
    shortlisted = db.query(ShortlistedUniversity).filter(
        ShortlistedUniversity.user_id == current_user.id,
        ShortlistedUniversity.university_id == university_id
    ).first()
    
    if not shortlisted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University not in shortlist"
        )
    
    if shortlisted.is_locked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove a locked university. Unlock it first."
        )
    
    db.delete(shortlisted)
    db.commit()
    
    return {"message": "University removed from shortlist"}


@router.post("/lock")
async def lock_university(
    lock_data: LockUniversityRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lock a university (commitment step)"""
    shortlisted = db.query(ShortlistedUniversity).filter(
        ShortlistedUniversity.user_id == current_user.id,
        ShortlistedUniversity.university_id == lock_data.university_id
    ).first()
    
    if not shortlisted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University not in shortlist. Add it first."
        )
    
    if shortlisted.is_locked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="University already locked"
        )
    
    shortlisted.is_locked = True
    shortlisted.locked_at = datetime.utcnow()
    
    # Update user stage
    current_user.current_stage = 4  # Stage 4: Preparing Applications
    
    # Create application tasks for this university
    university = db.query(University).filter(University.id == lock_data.university_id).first()
    create_application_tasks(db, current_user.id, university)
    
    db.commit()
    
    return {
        "message": f"University locked successfully. Application guidance is now available.",
        "university_id": lock_data.university_id
    }


def create_application_tasks(db: Session, user_id: int, university: University):
    """Create application tasks for a locked university"""
    tasks_to_create = [
        Task(
            user_id=user_id,
            university_id=university.id,
            title=f"Complete SOP for {university.name}",
            description="Write a tailored Statement of Purpose for this university",
            category="document",
            priority="high"
        ),
        Task(
            user_id=user_id,
            university_id=university.id,
            title=f"Gather transcripts for {university.name}",
            description="Request official transcripts from your institution",
            category="document",
            priority="high"
        ),
        Task(
            user_id=user_id,
            university_id=university.id,
            title=f"Get recommendation letters for {university.name}",
            description="Request 2-3 recommendation letters from professors/employers",
            category="document",
            priority="high"
        ),
        Task(
            user_id=user_id,
            university_id=university.id,
            title=f"Submit application to {university.name}",
            description="Complete and submit the online application",
            category="application",
            priority="high"
        )
    ]
    
    for task in tasks_to_create:
        db.add(task)


@router.post("/unlock")
async def unlock_university(
    unlock_data: UnlockUniversityRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unlock a university with confirmation"""
    if not unlock_data.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please confirm unlocking. This will remove associated tasks."
        )
    
    shortlisted = db.query(ShortlistedUniversity).filter(
        ShortlistedUniversity.user_id == current_user.id,
        ShortlistedUniversity.university_id == unlock_data.university_id
    ).first()
    
    if not shortlisted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University not in shortlist"
        )
    
    if not shortlisted.is_locked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="University is not locked"
        )
    
    shortlisted.is_locked = False
    shortlisted.locked_at = None
    
    # Delete associated incomplete tasks
    db.query(Task).filter(
        Task.university_id == unlock_data.university_id,
        Task.user_id == current_user.id,
        Task.is_completed == False
    ).delete()
    
    # Check if user still has locked universities
    locked_count = db.query(ShortlistedUniversity).filter(
        ShortlistedUniversity.user_id == current_user.id,
        ShortlistedUniversity.is_locked == True
    ).count()
    
    if locked_count == 0:
        current_user.current_stage = 3  # Back to Stage 3
    
    db.commit()
    
    return {
        "message": "University unlocked. Associated incomplete tasks have been removed.",
        "warning": "You may need to lock a university again to access application guidance."
    }


@router.put("/shortlist/{id}/status")
async def update_application_status(
    id: int,
    status_update: UpdateApplicationStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update application status for a shortlisted university"""
    shortlisted = db.query(ShortlistedUniversity).filter(
        ShortlistedUniversity.id == id,
        ShortlistedUniversity.user_id == current_user.id
    ).first()
    
    if not shortlisted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
        
    shortlisted.application_status = status_update.status
    db.commit()
    
    return {"message": "Application status updated", "status": shortlisted.application_status}


@router.get("/{university_id}", response_model=UniversityResponse)
async def get_university(
    university_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific university by ID"""
    university = db.query(University).filter(University.id == university_id).first()
    
    if not university:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University not found"
        )
    
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    fit_score, category, risk = calculate_fit_score(university, profile)
    
    return {
        "id": university.id,
        "name": university.name,
        "country": university.country,
        "city": university.city,
        "ranking": university.ranking,
        "tuition_min": university.tuition_min,
        "tuition_max": university.tuition_max,
        "programs": university.programs,
        "acceptance_rate": university.acceptance_rate,
        "ielts_requirement": university.ielts_requirement,
        "gre_requirement": university.gre_requirement,
        "toefl_requirement": university.toefl_requirement,
        "application_deadline": university.application_deadline,
        "image_url": university.image_url,
        "description": university.description,
        "fit_score": fit_score,
        "category": category,
        "risk_level": risk
    }
