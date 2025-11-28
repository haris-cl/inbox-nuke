Inbox Nuke Agent – Fully Autonomous Gmail Cleanup + Unsubscribe System
Version: 1.1 (Local Deployment) AI Provider: OpenAI API (GPT-4o / GPT-4.1)

1. Project Overview
Build a fully local personal AI agent system that:
	•	Connects to your Gmail via OAuth
	•	Discovers mailing list senders
	•	Automatically unsubscribes from EVERYTHING
	•	Creates Gmail filters to mute future emails
	•	Deletes massive volumes of old newsletters / promos
	•	Frees up storage so you can receive email again
	•	Runs autonomously without manual review
	•	Shows real-time progress in a local dashboard
Important:
	•	Everything except Gmail API + OpenAI API runs locally on your computer.
	•	All data is stored in a local SQLite database inside the project folder.
	•	No cloud services, no Supabase, no Postgres, no user accounts, no logins besides Google OAuth.

2. Local Tech Stack
2.1 Backend (Python)
	•	Python 3.11+
	•	FastAPI
	•	Uvicorn (for running backend)
	•	SQLite (via SQLAlchemy)
	•	Background Tasks:
	•	APScheduler (preferred) OR FastAPI BackgroundTasks
	•	Gmail API SDKs:
	•	google-api-python-client
	•	google-auth
	•	google-auth-oauthlib
	•	google-auth-httplib2
	•	HTTP:
	•	httpx
	•	LLM:
	•	openai Python SDK
	•	Serialization:
	•	pydantic
	•	orjson
	•	Utility:
	•	python-dotenv
	•	tenacity (retry for rate limits)
	•	rich (optional for console logs)
Everything installed locally via:
pip install -r requirements.txt


2.2 Frontend (Next.js)
	•	Next.js (App Router)
	•	TailwindCSS
	•	shadcn/ui components
	•	Axios or fetch for API calls
	•	Local development via:
npm install
npm run dev


2.3 Local Storage
No cloud DB.
Use:
	•	A single SQLite file
	•	/backend/data/inbox_nuke.db
Stored locally in project folder. Backups can be done manually by copying the file.

2.4 Folder Structure
Claude Code should generate:
/inbox-nuke-agent
    /backend
        main.py
        models.py
        db.py
        oauth.py
        gmail_client.py
        agent
            runner.py
            unsubscribe.py
            filters.py
            cleanup.py
            safety.py
        data/
            inbox_nuke.db
        .env
        requirements.txt
    /frontend
        app/
        components/
        lib/
        public/
        .env.local
        package.json
    README.md


3. Environment Variables (Local Only)
Backend (backend/.env)
OPENAI_API_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
APP_ENV=local

Frontend (frontend/.env.local)
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000


4. How the Local App Works (Simple Explanation)
Step 1 — You open http://localhost:3000
The frontend loads.
Step 2 — You click “Connect Gmail”
This opens Google’s OAuth consent page.
Step 3 — You click “Allow”
Backend receives:
	•	Code
	•	Exchanges it for tokens
	•	Saves tokens encrypted in SQLite
Step 4 — You click Start Cleanup
Backend starts background agent using APScheduler.
Step 5 — The Agent Cleans Everything Autonomously
It:
	•	Unsubscribes from every sender
	•	Creates Gmail filters
	•	Deletes emails older than X days
	•	Frees up storage
	•	Logs every action to SQLite
Step 6 — Frontend shows real-time progress
Pulls data from backend every 2–3 seconds:
	•	Progress bars
	•	Logs
	•	Deleted emails count
	•	Storage freed

5. Functional Requirements
5.1 Gmail OAuth Integration
Backend handles:
	•	/auth/google/start
	•	/auth/google/callback
	•	Save refresh token + access token locally in SQLite
OAuth scopes required:
	•	gmail.readonly
	•	gmail.modify
	•	gmail.settings.basic
	•	gmail.send

5.2 Sender Discovery System
The agent must:
Scan categories: category:promotions OR category:social OR category:updates
has:list-unsubscribe
	•	
	•	Extract sender:
	•	Email address
	•	Domain
	•	Track:
	•	Frequency
	•	Whether mailing-list header exists
	•	History of actions
Store in senders table in SQLite.

5.3 Autonomous Unsubscribe Logic
If List-Unsubscribe: header includes:
	•	mailto: → send unsubscribe email
	•	URL: → visit unsubscribe page using httpx
If no header but frequency > N:
Treat as bulk sender → mute + delete.

5.4 Filter Creation
Use Gmail Filters API.
Filter rule:
	•	Criteria: from:sender@example.com
	•	Actions:
	•	Skip Inbox
	•	Mark as read
	•	Apply label: Muted/<domain>
Avoid duplicates.

5.5 Massive Storage Cleanup
Agent must run queries like:
from:sender@example.com older_than:30d
larger:5M older_than:1y
category:promotions older_than:1y

Delete using batchModify → move to Trash (soft delete).
Track estimated bytes freed (from Gmail message metadata).

5.6 Safety Guardrails
Never delete when subject contains:
	•	“invoice”
	•	“receipt”
	•	“bank”
	•	“payment”
	•	“statement”
	•	“tax”
	•	“verification code”
	•	“security alert”
Never delete emails from:
	•	Government
	•	Financial institutions
	•	Healthcare
	•	emails whitelisted in SQLite manually

5.7 Optional AI Classification (Local Phase 2)
LLM classifies emails into:
	•	newsletter
	•	promo
	•	transactional
	•	financial
	•	personal
	•	unknown
Action mapping based on classification.
All using OpenAI API.

6. Database Schema (SQLite)
Tables:
gmail_credentials
	•	user_id (1 row only)
	•	access_token
	•	refresh_token
	•	expiry
	•	scopes
cleanup_runs
Tracks each run:
	•	id
	•	status
	•	started_at
	•	finished_at
	•	senders_total
	•	senders_processed
	•	emails_deleted
	•	bytes_freed_estimate
	•	progress_cursor
	•	error_message
senders
	•	id
	•	email
	•	domain
	•	message_count
	•	has_list_unsubscribe
	•	unsubscribed
	•	filter_created
cleanup_actions
	•	run_id
	•	timestamp
	•	action_type
	•	sender_email
	•	email_count
	•	bytes_freed
	•	notes
whitelist_domains
	•	domain
	•	reason

7. Backend API Endpoints
OAuth
	•	GET /auth/google/start
	•	GET /auth/google/callback
Runs
	•	POST /runs (start)
	•	POST /runs/{id}/pause
	•	POST /runs/{id}/resume
	•	GET /runs/{id} (stats)
	•	GET /runs/{id}/actions
Utils
	•	GET /senders
	•	GET /stats/current

8. Agent Workflow (Final Local Version)
Step 1 — Initialize Run
Create a cleanup_run entry.
Step 2 — Discover Senders
Scan Gmail messages → store sender metadata.
Step 3 — For Each Sender
	•	Safety check
	•	Try unsubscribe
	•	Create mute filter
	•	Delete historical emails
	•	Log actions to SQLite
	•	Update run progress
Step 4 — Complete
Mark run completed.

9. Frontend Requirements
Main Screens
	•	Home (connect Gmail)
	•	Cleanup Dashboard
	•	Run Details
	•	Settings (whitelist, aggressiveness)
Dashboard Must Show
	•	Progress bar
	•	Senders processed
	•	Emails deleted
	•	Storage freed
	•	Live activity feed
	•	Run status

10. Local Development Commands
Backend:
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

Frontend:
cd frontend
npm install
npm run dev

Both run locally without deploying anything.

11. Deliverables for Claude Code
Claude Code should generate:
Backend
	•	Fully working FastAPI backend
	•	SQLite DB + SQLAlchemy models
	•	Gmail OAuth flow
	•	Gmail API helper functions
	•	Background agent system (APScheduler)
	•	Cleanup logic
	•	Logging system
	•	Complete CRUD endpoints
Frontend
	•	Next.js frontend
	•	Tailwind + shadcn VIP components
	•	Dashboard UI
	•	OAuth connection button
	•	Real-time progress polling
Documentation
	•	README.md with:
	•	How to set up Google OAuth
	•	How to run locally
	•	How to configure .env
	•	How to start backend + frontend

12. MVP Done When
	•	You connect Gmail
	•	Hit Start Cleanup
	•	Agent unsubscribes from everything
	•	Agent deletes thousands of emails
	•	Inbox frees storage
	•	Dashboard shows progress in real-time
	•	Everything runs fully locally

