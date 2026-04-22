# Setup and Installation Guide

## System Requirements

### Minimum Requirements
- CPU: Intel/AMD 2.0 GHz dual-core or better
- RAM: 4GB minimum (8GB recommended)
- Storage: 500MB free disk space
- Internet: Required for API calls and database access

### Software Requirements
- Python 3.11 or higher (Check: python --version)
- Node.js 18 or higher (Check: node --version and npm --version)
- Git (for version control)
- Windows, macOS, or Linux operating system

### Required External Accounts (for full functionality)
- MongoDB Atlas account (free tier available)
- Google Cloud project with Generative AI API enabled
- (Optional) Neo4j Aura account for graph database
- (Optional) N8N instance for workflow automation

## Database Setup

### MongoDB Atlas Setup

1. Create MongoDB Atlas Account
   - Go to https://www.mongodb.com/cloud/atlas
   - Sign up for free tier account
   - Create an organization and project

2. Create a Cluster
   - Click "Create" button
   - Select "Shared Cluster" (free tier)
   - Choose cloud provider (AWS, Google Cloud, Azure)
   - Select region closest to you
   - Click "Create Cluster"
   - Wait 5-10 minutes for cluster creation

3. Create Database User
   - Go to "Database Access" section
   - Click "Add New Database User"
   - Username: talent_admin (or your choice)
   - Password: Generate secure password (save this!)
   - Click "Add User"

4. Configure Network Access
   - Go to "Network Access" section
   - Click "Add IP Address"
   - For development: Click "Allow Access from Anywhere" (0.0.0.0/0)
   - WARNING: For production, use specific IP addresses
   - Click "Confirm"

5. Get Connection String
   - Click "Connect" button on your cluster
   - Select "Connect your application"
   - Choose "Python" and "3.11 or higher"
   - Copy the connection string
   - Replace <username> and <password> with your database credentials
   - Example: mongodb+srv://talent_admin:password123@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority

6. Create Application Database
   - Go to "Collections" tab
   - Click "Create Database"
   - Database Name: talent_partner_db
   - Collection Name: jobs (or leave empty)
   - Click "Create"

### Google Generative AI Setup

1. Create Google Cloud Project
   - Go to https://cloud.google.com/
   - Sign in or create account
   - Create new project: "Talent Partner"

2. Enable Generative AI API
   - Go to "APIs & Services"
   - Click "Enable APIs and Services"
   - Search for "Generative Language API"
   - Click "Enable"

3. Create API Keys
   - Go to "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy the API key (save securely!)
   - Repeat to create 3-5 keys for load distribution
   - Add quotas and restrictions as needed

4. Set Up Billing (Free tier available)
   - Go to "Billing"
   - Link billing account
   - Free tier includes monthly free credits

## Backend Setup

### Step 1: Clone or Download Project

```bash
cd path/to/your/projects
git clone <repository-url>
cd "New folder (2)"
cd backend
```

### Step 2: Create Python Virtual Environment

Windows CMD:
```bash
python -m venv .venv
.venv\Scripts\activate
```

Windows PowerShell:
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should see (.venv) in your terminal prompt when activated.

### Step 3: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs all required packages:
- fastapi, uvicorn (web framework)
- motor, pymongo (database)
- google-generativeai (AI)
- chromadb (vector database)
- And many more...

Installation takes 2-5 minutes depending on your internet speed.

### Step 4: Create Environment Configuration File

Create a file named `.env` in the backend directory:

Windows:
```bash
notepad .env
```

macOS/Linux:
```bash
nano .env
```

Add the following content:

```
# Database Configuration
MONGO_URI=mongodb+srv://talent_admin:your_password@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=talent_partner_db
MONGO_CONNECTION_TIMEOUT_MS=5000
MONGO_POOL_SIZE=10

# AI & API Keys
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_API_KEY_1=key1_here
GOOGLE_API_KEY_2=key2_here
OPENAI_API_KEY=your_openai_key_here

# Application Settings
PROJECT_NAME=Autonomous Talent Partner
ENV=development
DEBUG=true
LOG_LEVEL=INFO

# CORS Settings
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Vector Database
CHROMA_PATH=./data/chroma
```

IMPORTANT: Replace with your actual values!
- MongoDB URI: From MongoDB Atlas connection string
- Google API Keys: From Google Cloud console
- Keep this file private and never commit to Git

### Step 5: Test MongoDB Connection

Run the diagnostic script:

```bash
python test_mongodb_connection.py
```

Expected output:
```
MongoDB Connection Diagnostic Test
1. Environment Check:
   MONGO_URI found
   Database Name: talent_partner_db
   Connection successful!
   
3. Database Operations Test:
   Collections found: X
   
4. Required Collections Check:
   All checks passed! MongoDB is ready for use.
```

If you see errors, check TROUBLESHOOTING.md for solutions.

### Step 6: Start Backend Server

```bash
python -m uvicorn app.main:app --reload
```

Output should show:
```
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete
INFO:     Uvicorn running on http://127.0.0.1:8000
```

The backend is now running!

Access:
- API: http://127.0.0.1:8000
- API Documentation (Swagger): http://127.0.0.1:8000/docs
- Alternative Docs (Redoc): http://127.0.0.1:8000/redoc

Keep this terminal open while developing.

## Frontend Setup

### Step 1: Navigate to Frontend Directory

```bash
cd path/to/project
cd frontend
```

### Step 2: Install Node Dependencies

```bash
npm install
```

This installs:
- React and React DOM
- Vite build tool
- Lucide-react icons
- And other dependencies

Installation takes 1-3 minutes.

### Step 3: Start Development Server

```bash
npm run dev
```

Output should show:
```
  VITE v4.x.x read-only [build output directory]

  Local:        http://localhost:5173/
  Press h to show help
```

The frontend is now running!

### Step 4: Open in Browser

Navigate to http://localhost:5173 in your web browser.

You should see the "Job Management Hub" with options to:
- Upload Job
- Create Job
- Upload CV (Candidate Resume)
- Past Jobs (View existing jobs)

## Verification Checklist

After setup, verify everything works:

### Backend
- [ ] Backend server running on http://127.0.0.1:8000
- [ ] API docs accessible at http://127.0.0.1:8000/docs
- [ ] MongoDB connection test passed
- [ ] No errors in backend console

### Frontend
- [ ] Frontend accessible at http://localhost:5173
- [ ] Page loads without errors
- [ ] UI is responsive and styled correctly
- [ ] Browser console has no critical errors

### Integration
- [ ] Frontend can call backend API (check in Network tab)
- [ ] WebSocket connection shows as connected
- [ ] No CORS errors in browser console

## Running the Application

### To Start Development

Terminal 1 (Backend):
```bash
cd backend
.venv\Scripts\activate  # Windows
python -m uvicorn app.main:app --reload
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

Then open http://localhost:5173 in your browser.

### To Stop Development

- Press Ctrl+C in each terminal
- Deactivate Python environment: `deactivate`

### To Pause and Resume

If you close terminals:
- You need to restart both services
- They don't run in background

## Production Deployment

### Backend Deployment (Uvicorn)

Build:
```bash
pip install gunicorn
pip freeze > requirements.txt
```

Run with Gunicorn:
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

### Frontend Deployment (Vite)

Build optimized version:
```bash
npm run build
```

Creates production files in `dist/` folder.

Deploy `dist/` folder to:
- Vercel (recommended for React)
- Netlify
- GitHub Pages
- Your own web server

### Database for Production

Upgrade MongoDB:
- Move from shared cluster to dedicated cluster
- Enable backup and recovery
- Configure read replicas for high availability
- Set up proper IP whitelisting

## Troubleshooting Setup Issues

### Python not found
```bash
# Solution: Check Python installation
python --version
# If not recognized, add Python to PATH or use full path
C:\Users\YourUser\AppData\Local\Programs\Python\Python311\python.exe --version
```

### Module not found errors
```bash
# Solution: Ensure virtual environment is activated
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
# Then reinstall packages
pip install -r requirements.txt
```

### MongoDB connection fails
```bash
# Solution: Check .env file and MongoDB settings
# See TROUBLESHOOTING.md for detailed MongoDB error solutions
python test_mongodb_connection.py
```

### Port already in use
```bash
# Backend on different port
python -m uvicorn app.main:app --reload --port 8001

# Frontend on different port
npm run dev -- --port 5174
```

### CORS errors in browser
```bash
# Solution: Check CORS_ORIGINS in .env
# Add your frontend URL to the list
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
# Redeploy backend after change
```

For more issues, see TROUBLESHOOTING.md.

## Next Steps

After setup is complete:

1. Read API_DOCUMENTATION.md to understand endpoints
2. Check ARCHITECTURE.md for system design
3. Review TECH_STACK.md for technology details
4. Start creating jobs and uploading resumes
5. Monitor backend console for logs
6. Check browser console for frontend errors

## Quick Reference Commands

```bash
# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
npm install

# Start backend
python -m uvicorn app.main:app --reload

# Start frontend
npm run dev

# Deactivate virtual environment
deactivate

# Run MongoDB connection test
python test_mongodb_connection.py

# Build frontend for production
npm run build

# Format code (if configured)
black app/
npm run format
```

---

Last Updated: April 2026
