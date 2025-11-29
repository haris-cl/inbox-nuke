# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Inbox Nuke Agent is a fully local Gmail cleanup and unsubscribe system. It autonomously:
- Connects to Gmail via OAuth
- Discovers mailing list senders (scans up to 10,000 emails)
- Unsubscribes from bulk senders (mailto: and HTTP methods)
- Creates Gmail filters to mute future emails
- Deletes old newsletters/promos to free storage
- Detects and cleans large attachments

**Key constraint:** Everything runs locally. No cloud services except Gmail API and OpenAI API (optional).

## Development Commands

### Backend (Python/FastAPI)
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py                      # Runs on http://localhost:8000

# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev                         # Runs on http://localhost:3000
npm run build                       # Production build
npm run lint                        # Run linter
```

### Testing
```bash
cd backend
pytest                              # Run all tests
pytest tests/test_safety.py -v      # Run specific test file
pytest -m "not slow"                # Skip slow tests
```

## Architecture

### Backend Structure (`/backend`)
```
backend/
├── main.py              # FastAPI app, lifespan, router registration
├── config.py            # Pydantic settings from .env
├── db.py                # SQLAlchemy async setup, session management
├── models.py            # ORM models (5 tables)
├── schemas.py           # Pydantic request/response schemas
├── gmail_client.py      # Gmail API wrapper with retry logic
├── routers/
│   ├── auth.py          # OAuth endpoints
│   ├── runs.py          # Cleanup run management
│   ├── senders.py       # Sender discovery data
│   ├── stats.py         # Dashboard statistics
│   ├── whitelist.py     # Domain whitelist CRUD
│   ├── exports.py       # CSV export endpoints
│   └── attachments.py   # Large attachment detection
├── agent/
│   ├── runner.py        # Main orchestrator (CleanupAgent class)
│   ├── scheduler.py     # APScheduler background jobs
│   ├── discovery.py     # Sender scanning with promotional patterns
│   ├── safety.py        # Protection guardrails + junk detection
│   ├── unsubscribe.py   # Mailto/HTTP unsubscribe
│   ├── filters.py       # Gmail filter creation
│   └── cleanup.py       # Bulk email deletion
├── utils/
│   └── encryption.py    # Fernet token encryption
├── tests/
└── data/
    └── inbox_nuke.db    # SQLite database (auto-created)
```

### Frontend Structure (`/frontend`)
```
frontend/
├── app/
│   ├── page.tsx                    # Home/onboarding
│   ├── layout.tsx                  # Root layout with theme
│   ├── auth/callback/page.tsx      # OAuth callback
│   └── dashboard/
│       ├── page.tsx                # Main dashboard
│       ├── senders/page.tsx        # Senders list
│       ├── history/page.tsx        # Run history
│       ├── history/[runId]/page.tsx # Run details
│       ├── attachments/page.tsx    # Large attachments
│       └── settings/page.tsx       # Settings/whitelist
├── components/
│   ├── ui/                         # shadcn/ui components
│   ├── stat-card.tsx, activity-feed.tsx, control-panel.tsx, etc.
└── lib/
    ├── api.ts                      # Backend API client with types
    └── utils.ts                    # Formatting helpers
```

## Agent Workflow

The cleanup agent follows this workflow:

```
1. INITIALIZATION
   └─> Load run from DB, init GmailClient, set status="running"

2. SENDER DISCOVERY (if senders_total == 0)
   └─> Query Gmail with patterns:
       - category:promotions/social/updates
       - has:unsubscribe
       - from:noreply@, newsletter@, marketing@, promo@, etc.
   └─> Parse List-Unsubscribe headers (mailto/HTTP)
   └─> Store senders with message counts

3. PRIORITIZE SENDERS
   └─> Sort order: junk senders → has unsubscribe → high volume

4. PROCESS EACH SENDER (loop)
   ├─> SAFETY CHECK (check_sender_safety)
   │   └─> Skip if: whitelisted, protected domain, protected pattern
   ├─> UNSUBSCRIBE (if has List-Unsubscribe)
   │   └─> Try mailto first, then HTTP POST/GET
   ├─> CREATE FILTER (skip inbox, mark read, apply "Muted" label)
   ├─> DELETE EMAILS older than threshold
   │   └─> Junk senders: 7 days
   │   └─> Regular senders: 30 days
   └─> LOG ACTION & UPDATE PROGRESS

5. FINALIZE
   └─> Set status="completed", record finished_at
```

## Safety & Junk Detection

### Protected (NEVER deleted)
**Keywords:** verification code, OTP, 2FA, password reset, security alert, invoice, receipt, bank, payment, tax, insurance, legal, court

**Domains:** .gov, .mil, major banks (chase.com, wellsfargo.com), payment processors (paypal.com, venmo.com), healthcare providers

**Patterns:** `security@*`, `alert@*`, `verification@*`, `noreply@*bank*`

### Junk Detection (aggressive cleanup)
**Sender patterns (40 pts):** noreply@, no-reply@, newsletter@, marketing@, promo@, offers@, sales@, deals@

**Subject patterns (30 pts):** "% off", sale, deal, discount, coupon, newsletter, weekly digest, free shipping

**Has List-Unsubscribe (30 pts)**

Junk score 60+ = use 7-day deletion threshold instead of 30 days.

## Database Schema

| Table | Purpose |
|-------|---------|
| `gmail_credentials` | Encrypted OAuth tokens (single row) |
| `cleanup_runs` | Run tracking with status, progress_cursor for pause/resume |
| `senders` | Discovered senders with unsubscribe_method, filter_id |
| `cleanup_actions` | Audit log (action_type: delete, unsubscribe, filter, skip) |
| `whitelist_domains` | User-protected domains |

## API Endpoints

### Authentication (`/api/auth`)
- `GET /google/start` - Returns OAuth URL
- `GET /google/callback` - Exchanges code for tokens
- `GET /status` - Check connection status
- `POST /disconnect` - Remove credentials

### Runs (`/api/runs`)
- `POST /start` - Start new cleanup run
- `GET /` - List runs (paginated, filterable by status)
- `GET /{id}` - Get run details
- `POST /{id}/pause` - Pause (saves cursor)
- `POST /{id}/resume` - Resume from cursor
- `POST /{id}/cancel` - Cancel run

### Senders (`/api/senders`)
- `GET /` - List senders (filter by domain, unsubscribed, has_filter)

### Stats (`/api/stats`)
- `GET /current` - Dashboard stats including active_run progress

## Environment Variables

### Backend (`backend/.env`)
```
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
ENCRYPTION_KEY=your-fernet-key
FRONTEND_URL=http://localhost:3000
APP_ENV=local
```

### Frontend (`frontend/.env.local`)
```
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

## Key Patterns

- **Async/await** - All DB and API operations are async (aiosqlite, AsyncSession)
- **Tenacity retry** - Gmail API calls use exponential backoff (2s, 4s, 8s)
- **Batch operations** - Gmail API batches up to 1000 messages
- **SWR polling** - Frontend polls every 2s during active runs
- **Progress cursor** - JSON cursor enables pause/resume from any point
- **Fernet encryption** - OAuth tokens encrypted at rest

## Troubleshooting

**"ENCRYPTION_KEY not configured"**
Generate with: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

**OAuth callback fails / redirect_uri_mismatch**
Ensure GOOGLE_REDIRECT_URI exactly matches Google Cloud Console (including `/api/auth/google/callback`)

**Rate limit errors (429)**
Agent auto-retries with exponential backoff. Check Gmail API quotas (250 units/user/sec).

**405 Method Not Allowed**
Check frontend API calls match backend routes (e.g., POST /api/runs/start not /api/runs)

**Run history not showing**
Backend must return `{runs: [], total, limit, offset}` format, not raw array.

## Gmail API Scopes
`openid`, `gmail.readonly`, `gmail.modify`, `gmail.settings.basic`, `gmail.send`, `userinfo.email`

## Claude Code Workflow (IMPORTANT)

When working on this project, Claude Code MUST follow these practices to prevent bugs:

### End-to-End Verification (After Building Features)
Before marking a feature complete, verify the full data flow:

1. **Test API directly with curl:**
   ```bash
   # Check endpoint returns data
   curl -s http://localhost:8000/api/[endpoint]

   # Test POST operations
   curl -s -X POST http://localhost:8000/api/[endpoint] -H "Content-Type: application/json" -d '{"key": "value"}'
   ```

2. **Verify database persistence:**
   ```bash
   # Check data was saved (follow up GET after POST)
   curl -s http://localhost:8000/api/[endpoint]
   ```

3. **Test external API integration (Gmail):**
   ```bash
   # Start a scan/scoring operation
   curl -s -X POST http://localhost:8000/api/scoring/start -H "Content-Type: application/json" -d '{"max_emails": 5}'

   # Check progress
   sleep 3 && curl -s http://localhost:8000/api/scoring/progress
   ```

4. **If something fails, trace the error:**
   - Check if it's a parameter mismatch (wrong arguments to class/function)
   - Check if async/await is missing
   - Check if frontend types match backend response

### After Modifying Backend Schemas (`schemas.py` or `models.py`)
1. **Regenerate TypeScript types:**
   ```bash
   cd /Users/hnaeem/inbox-nuke/backend && source venv/bin/activate && cd .. && python scripts/generate-types.py
   ```
2. **If models.py changed, create a migration:**
   ```bash
   cd /Users/hnaeem/inbox-nuke/backend && source venv/bin/activate && alembic revision --autogenerate -m "Description"
   ```

### Before Saying "Done" on Any Task
1. **Check for type errors (catches missing await):**
   ```bash
   cd /Users/hnaeem/inbox-nuke/backend && source venv/bin/activate && pyright 2>&1 | head -20
   ```
2. **Verify frontend/backend match:** If you modified an API endpoint or response format, check that `frontend/lib/api.ts` matches the backend schema.

### Common Error Prevention Checklist
| When You... | Do This |
|-------------|---------|
| Add new endpoint | Update `frontend/lib/api.ts` with correct URL and types |
| Change response shape | Run `python scripts/generate-types.py` |
| Add column to model | Run `alembic revision --autogenerate` |
| Call async Gmail methods | Always use `await` (list_messages, get_message, get_thread_info) |
| Leave TODO comment | Mark as `TODO CRITICAL` if it must be done before release |

### Integration Points to Verify
When changing code, verify these connection points match:
1. **Backend schema ↔ Database model** (field names, types)
2. **Backend response ↔ Frontend interface** (property names, optional vs required)
3. **Frontend API call ↔ Backend endpoint** (URL path, HTTP method, request body)
4. **Async function ↔ Caller** (await present when calling async methods)

### Files That Must Stay In Sync
| Backend File | Frontend File | Sync Method |
|--------------|---------------|-------------|
| `schemas.py` | `lib/api-types.ts` | Run `generate-types.py` |
| `routers/*.py` endpoints | `lib/api.ts` | Manual update |
| `models.py` | Database | Run `alembic` migration |
