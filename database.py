"""
Database Configuration
SQLAlchemy setup with PostgreSQL
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_counsellor.db")

# Fix Render/Heroku postgres URL compatibility
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Fix common Supabase/Supavisor connection string issues (unencoded options)
# Fixes: psycopg2.ProgrammingError: invalid connection option "supa"
try:
    if "?" in DATABASE_URL:
        # Check for unencoded 'options=project=supa' or 'options=endpoint=supa'
        if "options=project=" in DATABASE_URL and "options=project%3D" not in DATABASE_URL:
            DATABASE_URL = DATABASE_URL.replace("options=project=", "options=project%3D")
        
        if "options=endpoint=" in DATABASE_URL and "options=endpoint%3D" not in DATABASE_URL:
            DATABASE_URL = DATABASE_URL.replace("options=endpoint=", "options=endpoint%3D")

        # Handle 'supa=base-pooler.x' sometimes added by Supabase UI
        if "&supa=" in DATABASE_URL:
             DATABASE_URL = DATABASE_URL.split("&supa=")[0]
except Exception:
    pass

# Debug print to verify URL transformation (masked for security)
try:
    safe_url = DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "..."
    # print(f"DEBUG: Database config using Host: {safe_url}")
except:
    pass


# Use SQLite for development if PostgreSQL not available
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
