# InboxNuke V2 Implementation Log

This document tracks all changes made to implement InboxNuke V2 - the wizard-style cleanup flow.

## Summary

V2 transforms InboxNuke from a complex dashboard-based tool into a guided, wizard-style cleanup experience with the flow: **Scan → Report → Review → Confirm → Success**.

## New Files Created

### Backend

#### Services (`backend/services/`)
| File | Purpose |
|------|---------|
| `__init__.py` | Service exports |
| `cleanup_flow.py` | CleanupFlowService - manages wizard sessions, progress, decisions |
| `recommendation_engine.py` | RecommendationEngine - generates AI cleanup recommendations |
| `cleanup_executor.py` | CleanupExecutor - executes deletions, unsubscribes, filters |

#### Router (`backend/routers/`)
| File | Purpose |
|------|---------|
| `cleanup.py` | V2 cleanup wizard API endpoints (`/api/cleanup/*`) |

#### Modified Files
| File | Changes |
|------|---------|
| `models.py` | Added `CleanupSession` and `EmailRecommendation` tables |
| `schemas.py` | Added V2 cleanup flow schemas |
| `main.py` | Registered cleanup router |

### Frontend

#### Cleanup Wizard (`frontend/app/dashboard/cleanup/`)
| File | Purpose |
|------|---------|
| `page.tsx` | Entry redirect to scanning |
| `layout.tsx` | CleanupProvider wrapper |
| `cleanup-context.tsx` | React Context for wizard state management |
| `scanning/page.tsx` | F1: Live scanning progress with discoveries |
| `report/page.tsx` | F2+F3: Inbox health report + mode selection |
| `review/page.tsx` | F4: One-at-a-time review queue |
| `confirm/page.tsx` | F5: Cleanup confirmation screen |
| `success/page.tsx` | F7: Success celebration with results |

#### Space Manager (`frontend/app/dashboard/space/`)
| File | Purpose |
|------|---------|
| `page.tsx` | F9: Free Up Space (renamed from Attachments) |

#### Components (`frontend/app/dashboard/components/`)
| File | Purpose |
|------|---------|
| `inbox-health-card.tsx` | F8: Inbox Health Card for dashboard |

#### Modified Files
| File | Changes |
|------|---------|
| `lib/api.ts` | Added V2 cleanup API methods and types |
| `app/dashboard/page.tsx` | Redesigned with Inbox Health Card, simplified stats |
| `app/dashboard/layout.tsx` | Simplified navigation (8→4 items) |

## V2 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/cleanup/start` | Start new cleanup session |
| GET | `/api/cleanup/progress/{session_id}` | Get scanning progress |
| GET | `/api/cleanup/recommendations/{session_id}` | Get recommendations summary |
| POST | `/api/cleanup/mode/{session_id}` | Set cleanup mode (quick/full) |
| GET | `/api/cleanup/review-queue/{session_id}` | Get review queue items |
| POST | `/api/cleanup/review-decision/{session_id}` | Submit keep/delete decision |
| POST | `/api/cleanup/skip-all/{session_id}` | Trust AI for remaining |
| GET | `/api/cleanup/confirmation/{session_id}` | Get confirmation summary |
| POST | `/api/cleanup/execute/{session_id}` | Execute cleanup |
| GET | `/api/cleanup/results/{session_id}` | Get cleanup results |
| GET | `/api/cleanup/inbox-health` | Get inbox health status |
| GET | `/api/cleanup/auto-protected` | Get auto-protected categories |

## New Database Tables

### cleanup_sessions
Tracks wizard sessions with progress, decisions, and results.

| Column | Type | Description |
|--------|------|-------------|
| session_id | UUID | Unique session identifier |
| status | String | scanning, ready_for_review, reviewing, confirming, executing, completed, failed |
| mode | String | quick, full |
| total_emails | Integer | Total emails to scan |
| scanned_emails | Integer | Emails scanned so far |
| discoveries | JSON | Category breakdown |
| total_to_cleanup | Integer | Emails marked for deletion |
| total_protected | Integer | Protected emails |
| space_savings | BigInteger | Estimated bytes to free |
| review_decisions | JSON | User decisions {message_id: decision} |
| emails_deleted | Integer | Final count |
| space_freed | BigInteger | Final bytes freed |
| senders_unsubscribed | Integer | Senders unsubscribed |
| filters_created | Integer | Filters created |

### email_recommendations
Per-email AI recommendations for each cleanup session.

| Column | Type | Description |
|--------|------|-------------|
| session_id | String | FK to cleanup_sessions |
| message_id | String | Gmail message ID |
| sender_email | String | Sender email address |
| subject | String | Email subject |
| ai_suggestion | String | keep, delete |
| reasoning | String | Why AI suggested this |
| confidence | Float | 0.0-1.0 confidence |
| user_decision | String | User's override (null if not reviewed) |
| category | String | promotions, newsletters, social, updates, protected |

## Navigation Changes

### Before (V1)
```
Dashboard
Review & Score
Senders
History
Settings
---
Attachments
```

### After (V2)
```
Dashboard (with Inbox Health Card + Start Cleanup button)
Free Up Space
History
Settings
```

Hidden from nav (still accessible via URL):
- `/dashboard/score` - Legacy V1 scoring
- `/dashboard/senders` - Legacy V1 senders
- `/dashboard/subscriptions` - Legacy V1 subscriptions
- `/dashboard/rules` - Legacy V1 rules
- `/dashboard/attachments` - Redirects to /dashboard/space

## How to Run V2

### Backend
```bash
cd backend
source venv/bin/activate
python main.py
# Server runs on http://localhost:8000
```

### Frontend
```bash
cd frontend
npm run dev
# App runs on http://localhost:3000
```

### Access V2 Cleanup Wizard
1. Go to http://localhost:3000
2. Connect your Gmail account
3. Click "Start Cleanup" on the Dashboard
4. Follow the wizard: Scan → Report → Review → Confirm → Success

## Database Migration

Run the following to create the new tables:

```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "Add V2 cleanup tables"
alembic upgrade head
```

Or, the tables will be auto-created on first run via SQLAlchemy's `create_all()`.

## Features Implemented

| ID | Feature | Status |
|----|---------|--------|
| F1 | Inbox Scanning with Live Progress | ✅ |
| F2 | Inbox Health Report | ✅ |
| F3 | Cleanup Mode Selection | ✅ |
| F4 | Review Queue (One-at-a-Time) | ✅ |
| F5 | Cleanup Confirmation Screen | ✅ |
| F6 | Cleanup Execution with Progress | ✅ |
| F7 | Success Screen with Next Steps | ✅ |
| F8 | Dashboard with Inbox Health Card | ✅ |
| F9 | Free Up Space | ✅ |
| F10 | Protected Senders Settings | Existing (minor updates) |
| F11 | Cleanup History | Existing |
| F12 | Gmail Connection Management | Existing |
| F13 | Trust-First Home Page | Partial (existing works) |
| F14 | Inbox Health API | ✅ |
| F18 | Simplified Navigation | ✅ |
| F19 | Wizard State Management | ✅ |

## V1 Compatibility

All V1 routes and functionality remain intact:
- `/dashboard/score` - V1 scoring system
- `/dashboard/senders` - V1 sender list
- `/dashboard/subscriptions` - V1 subscription management
- `/dashboard/rules` - V1 retention rules
- All existing API endpoints continue to work

V2 is additive - it provides a new, simpler cleanup flow while preserving all V1 functionality for advanced users.

## Testing

### Backend Tests
```bash
cd backend
source venv/bin/activate
pytest tests/test_v2_cleanup.py -v
```

Test coverage:
- `test_create_session` - Session creation
- `test_update_progress` - Scan progress tracking
- `test_set_mode` - Mode selection (quick/full)
- `test_record_decision` - User review decisions
- `test_complete_session` - Cleanup completion
- `test_full_cleanup_flow` - End-to-end flow integration
- `TestRecommendationEngine` - AI recommendation logic

### Frontend E2E Tests
```bash
cd frontend
npm install               # Install Playwright
npx playwright install    # Install browsers
npm test                  # Run all tests
npm run test:ui          # Run with UI
```

Test coverage:
- Dashboard renders with Inbox Health Card
- Cleanup wizard pages render
- Space Manager (Free Up Space) functionality
- Navigation has 4 simplified items
- Start Cleanup button navigates to wizard
