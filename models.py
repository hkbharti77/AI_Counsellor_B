"""
SQLAlchemy Models
Database models for AI Counsellor
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, ARRAY, Float, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    onboarding_completed = Column(Boolean, default=False)
    current_stage = Column(Integer, default=1)  # 1-4 stages
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False)
    shortlisted_universities = relationship("ShortlistedUniversity", back_populates="user")
    tasks = relationship("Task", back_populates="user")
    documents = relationship("Document", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")


class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Academic Background
    education_level = Column(String(100))  # high_school, bachelors, masters
    degree = Column(String(255))
    major = Column(String(255))
    graduation_year = Column(Integer)
    gpa = Column(Float)
    
    # Study Goals
    intended_degree = Column(String(100))  # bachelors, masters, mba, phd
    field_of_study = Column(String(255))
    target_intake = Column(String(50))  # fall_2025, spring_2026, etc.
    preferred_countries = Column(Text)  # JSON string array
    
    # Budget
    budget_min = Column(Integer)
    budget_max = Column(Integer)
    funding_type = Column(String(50))  # self_funded, scholarship, loan
    
    # Exam Readiness
    ielts_status = Column(String(50))  # not_started, preparing, completed
    ielts_score = Column(Float)
    toefl_status = Column(String(50))
    toefl_score = Column(Integer)
    gre_status = Column(String(50))
    gre_score = Column(Integer)
    gmat_status = Column(String(50))
    gmat_score = Column(Integer)
    sop_status = Column(String(50))  # not_started, draft, ready
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="profile")


class University(Base):
    __tablename__ = "universities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    country = Column(String(100))
    city = Column(String(100))
    ranking = Column(Integer)
    tuition_min = Column(Integer)
    tuition_max = Column(Integer)
    programs = Column(Text)  # JSON string array
    acceptance_rate = Column(Float)
    ielts_requirement = Column(Float)
    gre_requirement = Column(Integer)
    toefl_requirement = Column(Integer)
    application_deadline = Column(String(100))
    image_url = Column(String(500))
    description = Column(Text)
    
    # Relationships
    shortlisted_by = relationship("ShortlistedUniversity", back_populates="university")


class ShortlistedUniversity(Base):
    __tablename__ = "shortlisted_universities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    university_id = Column(Integer, ForeignKey("universities.id"))
    category = Column(String(20))  # dream, target, safe
    application_status = Column(String(20), default="shortlisted")  # shortlisted, preparing, submitted, interview, offer, rejected
    is_locked = Column(Boolean, default=False)
    locked_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="shortlisted_universities")
    university = relationship("University", back_populates="shortlisted_by")


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(255), nullable=False)
    type = Column(String(50))  # pdf, docx, etc.
    size = Column(String(50))  # e.g. "2.4 MB"
    category = Column(String(50))  # academic, application, financial, identity
    status = Column(String(50), default="pending")  # pending, verified, rejected, missing
    file_path = Column(String(500))  # Local path or S3 URL
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="documents")


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    university_id = Column(Integer, ForeignKey("universities.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # document, exam, application, general
    priority = Column(String(20), default="medium")  # low, medium, high
    due_date = Column(Date)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="tasks")


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="conversations")
