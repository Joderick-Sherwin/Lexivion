# Quick Start Guide

Get Lexivion up and running in 5 minutes!

## Prerequisites Check

- [ ] Python 3.8+ installed (`python --version`)
- [ ] Node.js 18+ installed (`node --version`)
- [ ] PostgreSQL running and accessible
- [ ] Database `RAG_Bot` created

## Step-by-Step Setup

### 1. Database Setup (One-time)

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE RAG_Bot;

-- Connect to database
\c RAG_Bot

-- Run migration
\i scripts/migrations/001_init.sql
\i scripts/migrations/002_rag_pipeline.sql
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
# Copy .env.example and update with your database credentials
# Add GEMINI_API_KEY and GEMINI_MODEL (e.g., gemini-2.0-flash)
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Run the Application

**Option A: Using Scripts (Windows)**
```bash
# Terminal 1
start_backend.bat

# Terminal 2
start_frontend.bat
```

**Option B: Manual (All Platforms)**
```bash
# Terminal 1 - Backend
cd backend
python server.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 5. Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Health Check: http://localhost:8000/api/health

## First Use

1. Open http://localhost:3000 in your browser
2. Upload a PDF file using the upload section
3. Wait for processing to complete (first time may take longer due to model downloads)
4. Enter a search query
5. View results with associated images
6. Click any context chip to preview the original PDF page in a modal

## Troubleshooting

### Backend won't start
- Check PostgreSQL is running
- Verify database credentials in `.env`
- Ensure port 8000 is not in use

### Frontend won't start
- Run `npm install` in frontend directory
- Check Node.js version (18+)
- Ensure port 3000 is not in use

### Models not loading
- First run downloads models (~500MB)
- Ensure stable internet connection
- Check disk space

### Database connection errors
- Verify PostgreSQL is running
- Check credentials in `.env`
- Ensure database `RAG_Bot` exists

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [PROJECT_ANALYSIS.md](PROJECT_ANALYSIS.md) for architecture details
- Customize `.env` for your environment

