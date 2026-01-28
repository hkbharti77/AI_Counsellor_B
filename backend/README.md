# AI Counsellor - Backend

FastAPI backend for the AI Counsellor study abroad platform.

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update values:
- `GEMINI_API_KEY` - Get from [Google AI Studio](https://makersuite.google.com/app/apikey) (optional)

### 3. Seed Database

```bash
python seed_database.py
```

### 4. Run Server

```bash
uvicorn main:app --reload
```

Server will start at `http://localhost:8000`

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Get access token
- `GET /api/auth/me` - Get current user

### Profile
- `GET /api/profile/` - Get user profile
- `PUT /api/profile/` - Update profile
- `POST /api/profile/onboarding/complete` - Complete onboarding
- `GET /api/profile/dashboard` - Get dashboard data

### Universities
- `GET /api/universities/` - List all universities (with filters)
- `GET /api/universities/recommendations` - Get AI recommendations
- `GET /api/universities/shortlist` - Get shortlisted universities
- `POST /api/universities/shortlist` - Add to shortlist
- `POST /api/universities/lock` - Lock a university
- `POST /api/universities/unlock` - Unlock a university

### AI Counsellor
- `POST /api/counsellor/chat` - Chat with AI
- `POST /api/counsellor/voice-onboarding` - Voice onboarding
- `GET /api/counsellor/history` - Get chat history

### Tasks
- `GET /api/tasks/` - List tasks
- `POST /api/tasks/` - Create task
- `PUT /api/tasks/{id}` - Update task
- `POST /api/tasks/{id}/complete` - Complete task
