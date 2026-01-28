"""
AI Counsellor Router
Chat and voice-based AI counselling with Gemini integration
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import json
import os
from datetime import datetime

from database import get_db
from models import User, Profile, University, ShortlistedUniversity, Task, Conversation
from schemas import ChatMessage, ChatResponse, VoiceOnboardingMessage, VoiceOnboardingResponse
from auth import get_current_user
from services.gemini_service import GeminiService

router = APIRouter()


def get_user_context(db: Session, user: User) -> dict:
    """Get complete user context for AI"""
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    
    shortlisted = db.query(ShortlistedUniversity).filter(
        ShortlistedUniversity.user_id == user.id
    ).all()
    
    locked = [s for s in shortlisted if s.is_locked]
    
    # Get university names for shortlisted and locked
    shortlist_info = []
    for s in shortlisted:
        uni = db.query(University).filter(University.id == s.university_id).first()
        if uni:
            shortlist_info.append({
                "name": uni.name,
                "country": uni.country,
                "category": s.category,
                "is_locked": s.is_locked
            })
    
    # Get pending tasks
    tasks = db.query(Task).filter(
        Task.user_id == user.id,
        Task.is_completed == False
    ).all()
    
    task_info = [{"title": t.title, "category": t.category, "priority": t.priority} for t in tasks]
    
    # Get recent conversation history
    history = db.query(Conversation).filter(
        Conversation.user_id == user.id
    ).order_by(Conversation.created_at.desc()).limit(10).all()
    
    history_messages = [{"role": c.role, "content": c.message} for c in reversed(history)]
    
    context = {
        "user_name": user.full_name,
        "current_stage": user.current_stage,
        "onboarding_completed": user.onboarding_completed,
        "profile": None,
        "shortlisted_universities": shortlist_info,
        "locked_universities": [s for s in shortlist_info if s.get("is_locked")],
        "pending_tasks": task_info,
        "conversation_history": history_messages
    }
    
    if profile:
        context["profile"] = {
            "education_level": profile.education_level,
            "degree": profile.degree,
            "major": profile.major,
            "graduation_year": profile.graduation_year,
            "gpa": profile.gpa,
            "intended_degree": profile.intended_degree,
            "field_of_study": profile.field_of_study,
            "target_intake": profile.target_intake,
            "preferred_countries": profile.preferred_countries,
            "budget_min": profile.budget_min,
            "budget_max": profile.budget_max,
            "funding_type": profile.funding_type,
            "ielts_status": profile.ielts_status,
            "ielts_score": profile.ielts_score,
            "gre_status": profile.gre_status,
            "gre_score": profile.gre_score,
            "sop_status": profile.sop_status
        }
    
    return context


@router.post("/chat", response_model=ChatResponse)
async def chat_with_counsellor(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Chat with AI Counsellor"""
    # Check if onboarding is complete
    if not current_user.onboarding_completed:
        return ChatResponse(
            message="Please complete your onboarding first to unlock the AI Counsellor. I need to understand your background to provide personalized guidance.",
            actions=None,
            suggestions=["Complete Onboarding"]
        )
    
    # Get user context
    context = get_user_context(db, current_user)
    
    # Save user message
    user_message = Conversation(
        user_id=current_user.id,
        message=message.message,
        role="user"
    )
    db.add(user_message)
    db.commit()
    
    # Get AI response
    gemini = GeminiService()
    response = await gemini.get_counsellor_response(message.message, context)
    
    # Save AI response
    ai_message = Conversation(
        user_id=current_user.id,
        message=response["message"],
        role="assistant"
    )
    db.add(ai_message)
    db.commit()
    
    # Log conversation to terminal
    print("\n" + "="*50)
    print(f"👤 USER: {message.message}")
    print(f"🤖 AI: {response['message']}")
    print("="*50 + "\n")
    
    return ChatResponse(
        message=response["message"],
        actions=response.get("actions"),
        suggestions=response.get("suggestions")
    )


@router.post("/voice-onboarding", response_model=VoiceOnboardingResponse)
async def voice_onboarding(
    voice_data: VoiceOnboardingMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process voice onboarding input"""
    gemini = GeminiService()
    
    # Get current profile state
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)
        db.commit()
    
    current_profile = {
        "education_level": profile.education_level,
        "degree": profile.degree,
        "major": profile.major,
        "graduation_year": profile.graduation_year,
        "gpa": profile.gpa,
        "intended_degree": profile.intended_degree,
        "field_of_study": profile.field_of_study,
        "target_intake": profile.target_intake,
        "preferred_countries": profile.preferred_countries,
        "budget_min": profile.budget_min,
        "budget_max": profile.budget_max,
        "funding_type": profile.funding_type,
        "ielts_status": profile.ielts_status,
        "ielts_score": profile.ielts_score,
        "gre_status": profile.gre_status,
        "gre_score": profile.gre_score,
        "sop_status": profile.sop_status
    }
    
    # Process with AI
    response = await gemini.process_voice_onboarding(
        transcript=voice_data.transcript,
        current_step=voice_data.current_step,
        current_profile=current_profile
    )
    
    # Update profile with extracted data
    if response.get("extracted_data"):
        for field, value in response["extracted_data"].items():
            if hasattr(profile, field) and value is not None:
                setattr(profile, field, value)
        db.commit()
    
    # Check if onboarding is complete
    is_complete = response.get("is_complete", False)
    if is_complete:
        current_user.onboarding_completed = True
        current_user.current_stage = 2
        db.commit()
    
    return VoiceOnboardingResponse(
        response_text=response["response_text"],
        next_step=response.get("next_step"),
        extracted_data=response.get("extracted_data"),
        is_complete=is_complete
    )


@router.post("/action/shortlist")
async def ai_shortlist_action(
    university_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI action: Add university to shortlist"""
    # Check if university exists
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(status_code=404, detail="University not found")
    
    # Check if already shortlisted
    existing = db.query(ShortlistedUniversity).filter(
        ShortlistedUniversity.user_id == current_user.id,
        ShortlistedUniversity.university_id == university_id
    ).first()
    
    if existing:
        return {"message": f"{university.name} is already in your shortlist", "success": False}
    
    # Add to shortlist
    shortlisted = ShortlistedUniversity(
        user_id=current_user.id,
        university_id=university_id,
        category="target"
    )
    db.add(shortlisted)
    
    if current_user.current_stage < 3:
        current_user.current_stage = 3
    
    db.commit()
    
    return {"message": f"Added {university.name} to your shortlist!", "success": True}


@router.post("/action/lock")
async def ai_lock_action(
    university_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI action: Lock a university"""
    shortlisted = db.query(ShortlistedUniversity).filter(
        ShortlistedUniversity.user_id == current_user.id,
        ShortlistedUniversity.university_id == university_id
    ).first()
    
    if not shortlisted:
        return {"message": "Please add this university to your shortlist first", "success": False}
    
    if shortlisted.is_locked:
        return {"message": "This university is already locked", "success": False}
    
    university = db.query(University).filter(University.id == university_id).first()
    
    shortlisted.is_locked = True
    shortlisted.locked_at = datetime.utcnow()
    current_user.current_stage = 4
    
    db.commit()
    
    return {"message": f"Locked {university.name}! Application guidance is now available.", "success": True}


@router.post("/action/create-task")
async def ai_create_task_action(
    title: str,
    description: str = None,
    priority: str = "medium",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI action: Create a task"""
    task = Task(
        user_id=current_user.id,
        title=title,
        description=description,
        priority=priority,
        category="general"
    )
    db.add(task)
    db.commit()
    
    return {"message": f"Created task: {title}", "success": True, "task_id": task.id}


@router.get("/history")
async def get_conversation_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation history"""
    history = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": c.id,
            "role": c.role,
            "message": c.message,
            "created_at": c.created_at
        }
        for c in reversed(history)
    ]


@router.delete("/history")
async def clear_conversation_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear conversation history"""
    db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).delete()
    db.commit()
    
    return {"message": "Conversation history cleared"}
