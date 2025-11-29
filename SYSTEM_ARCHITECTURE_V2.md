# SYSTEM ARCHITECTURE V2 - Inbox Nuke

This document provides the complete technical specification for implementing Inbox Nuke V2, based on the UX Blueprint. It includes detailed schemas, API contracts, component lists, and a migration plan.

---

## Table of Contents

1. [Frontend Architecture](#1-frontend-architecture)
2. [Backend Architecture](#2-backend-architecture)
3. [Cleanup Engine Logic](#3-cleanup-engine-logic)
4. [Data Consistency Rules](#4-data-consistency-rules)
5. [Migration Plan](#5-migration-plan)

---

## 1. Frontend Architecture

### 1.1 Route Structure

```
app/
├── page.tsx                              # Home (unauthenticated)
├── auth/callback/page.tsx                # OAuth callback (keep as-is)
└── dashboard/
    ├── layout.tsx                        # Sidebar navigation
    ├── page.tsx                          # Dashboard (V2 redesign)
    ├── cleanup/                          # NEW: Cleanup Flow (wizard)
    │   ├── page.tsx                      # Entry redirect to /scanning
    │   ├── scanning/page.tsx             # Step 1: Scanning progress
    │   ├── report/page.tsx               # Step 2: Inbox Report
    │   ├── review/page.tsx               # Step 3: Review Queue
    │   ├── confirm/page.tsx              # Step 4: Confirmation
    │   └── success/page.tsx              # Step 5: Success screen
    ├── space/                            # Renamed from attachments/
    │   └── page.tsx                      # Large email cleanup (keep logic)
    ├── history/
    │   ├── page.tsx                      # Run history list
    │   └── [runId]/page.tsx              # Run details (keep)
    └── settings/
        └── page.tsx                      # Protected senders, connection, advanced
```

**Route Changes Summary:**
- `DELETE` `/dashboard/score` (replaced by cleanup flow)
- `DELETE` `/dashboard/senders` (merge into settings or remove)
- `DELETE` `/dashboard/subscriptions` (merge into cleanup flow)
- `DELETE` `/dashboard/rules` (move to settings/advanced)
- `RENAME` `/dashboard/attachments` → `/dashboard/space`
- `CREATE` `/dashboard/cleanup/*` (new wizard flow)

---

### 1.2 Component Architecture

#### 1.2.1 Reusable Components (Keep)

| Component | File | Purpose | Used In |
|-----------|------|---------|---------|
| **StatCard** | `stat-card.tsx` | Display single metric with icon | Dashboard, Space |
| **ActivityFeed** | `activity-feed.tsx` | List of recent actions | Dashboard |
| **Card, Button, Badge** | `ui/*.tsx` | shadcn/ui components | All pages |

#### 1.2.2 Components to Remove

| Component | File | Reason |
|-----------|------|--------|
| **ControlPanel** | `control-panel.tsx` | Replaced by single "Start Cleanup" button |
| **ProgressSection** | `progress-section.tsx` | Replaced by Scanning screen |
| **SenderRow** | `sender-row.tsx` | Sender list removed |
| **EmailScoreCard** | `email-score-card.tsx` | Replaced by ReviewEmailCard |
| **SubscriptionCard** | `subscription-card.tsx` | Subscriptions merged into cleanup |
| **RuleCard** | `rule-card.tsx` | Rules moved to settings |
| **RunHistoryCard** | `run-history-card.tsx` | Keep but simplify |

#### 1.2.3 New Components for V2

| Component | File | Purpose |
|-----------|------|---------|
| **InboxHealthCard** | `inbox-health-card.tsx` | Shows health status (Healthy/Needs Attention), cleanup count, space savings |
| **QuickActions** | `quick-actions.tsx` | Secondary action buttons (Space, Settings links) |
| **ScanningProgress** | `scanning-progress.tsx` | Full-screen progress with live discoveries |
| **CategoryBreakdown** | `category-breakdown.tsx` | Pie/bar chart showing promotions/newsletters/social |
| **ProtectedSection** | `protected-section.tsx` | Reassurance section showing what's safe |
| **ReviewEmailCard** | `review-email-card.tsx` | One-at-a-time email review card with Keep/Delete |
| **CleanupSummary** | `cleanup-summary.tsx` | Confirmation summary (emails, space, unsubscribes) |
| **SuccessCelebration** | `success-celebration.tsx` | Success screen with results and next steps |
| **ModeSelector** | `mode-selector.tsx` | Choose between Quick Clean and Review All |
| **ProgressIndicator** | `progress-indicator.tsx` | "12 of 50" progress in review queue |
| **ProtectedSendersList** | `protected-senders-list.tsx` | Whitelist management in Settings |

---

### 1.3 State Management

#### 1.3.1 Cleanup Flow State (Context)

**File:** `app/dashboard/cleanup/cleanup-context.tsx`

```typescript
interface CleanupState {
  // Flow control
  currentStep: 'scanning' | 'report' | 'review' | 'confirm' | 'success'
  mode: 'quick' | 'full' | null  // User's choice

  // Scanning state
  scanProgress: {
    status: 'idle' | 'running' | 'completed' | 'failed'
    totalEmails: number
    scannedEmails: number
    discoveries: {
      promotions: number
      newsletters: number
      social: number
      lowValue: number
    }
  }

  // Report data
  recommendations: {
    totalToCleanup: number
    totalProtected: number
    spaceSavings: number
    categoryBreakdown: {
      promotions: number
      newsletters: number
      social: number
      other: number
    }
    topDeleteSenders: string[]
  }

  // Review queue
  reviewQueue: EmailItem[]
  reviewIndex: number
  reviewDecisions: Record<string, 'keep' | 'delete'>

  // Confirmation
  finalSummary: {
    emailsToDelete: number
    sendersToUnsubscribe: number
    spaceToBeFeed: number
    protectedCount: number
  }

  // Results
  results: {
    emailsDeleted: number
    spaceFeed: number
    sendersUnsubscribed: number
  }
}

interface CleanupActions {
  startScan: (maxEmails: number) => Promise<void>
  selectMode: (mode: 'quick' | 'full') => void
  reviewNext: () => void
  reviewPrevious: () => void
  markKeep: (messageId: string) => void
  markDelete: (messageId: string) => void
  skipAllAndTrustAI: () => void
  confirmCleanup: () => Promise<void>
  resetFlow: () => void
}
```

**Key Principles:**
- Cleanup flow state is NOT persisted (starts fresh each time)
- Uses React Context + useReducer for flow state management
- Backend stores final results in cleanup_runs table
- Progress polling uses SWR for real-time updates during scanning

#### 1.3.2 Dashboard State (SWR)

**File:** `app/dashboard/page.tsx`

```typescript
// SWR for polling active cleanup run
const { data: stats } = useSWR('/api/stats/current', {
  refreshInterval: activeRun ? 2000 : 60000
})

// SWR for inbox health
const { data: health } = useSWR('/api/inbox-health', {
  refreshInterval: 60000
})
```

---

### 1.4 User Flow Diagram (Wizard Steps)

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLEANUP FLOW (V2)                          │
└─────────────────────────────────────────────────────────────────┘

[Dashboard]
     │
     │ User clicks "Start Cleanup"
     ▼
[/dashboard/cleanup/scanning]
     │ - Full screen progress bar
     │ - Live discoveries ("Found 3,200 promotions")
     │ - No user actions (just watch)
     │ - Polls /api/cleanup/progress every 2s
     │
     │ On scan complete
     ▼
[/dashboard/cleanup/report]
     │ - Shows "We found X emails to clean up"
     │ - Category breakdown (chart)
     │ - "What's Protected" section
     │ - Two choices: [Quick Clean] [Review All]
     │
     │ User selects mode
     ▼
[/dashboard/cleanup/review] (if mode = 'full' OR uncertain count > 0)
     │ - One email at a time (card view)
     │ - [Keep] [Delete] buttons
     │ - Progress: "12 of 50"
     │ - [Skip All & Trust AI] escape hatch
     │
     │ Review complete
     ▼
[/dashboard/cleanup/confirm]
     │ - Summary: X emails, Y GB, Z unsubscribes
     │ - Safety reminder (Trash, 30-day recovery)
     │ - [Confirm Cleanup] button
     │
     │ User confirms
     ▼
[/dashboard/cleanup/success]
     │ - Celebration animation
     │ - Results: emails cleaned, space freed
     │ - Next steps: auto-cleanup toggle
     │ - [Back to Dashboard]
     │
     ▼
[Dashboard] (with updated stats)
```

---

## 2. Backend Architecture

### 2.1 New API Endpoints for V2

#### 2.1.1 Inbox Health Endpoint (NEW)

**Endpoint:** `GET /api/inbox-health`

**Purpose:** Provides dashboard health status without running full scan

**Response Schema:**
```python
class InboxHealthResponse(BaseModel):
    status: str  # "healthy", "needs_attention", "critical"
    unread_count: int
    potential_cleanup_count: int  # Estimate based on categories
    potential_space_savings: int  # Bytes
    last_scan_at: Optional[datetime]
    categories: Dict[str, int]  # {"promotions": 1200, "social": 450, ...}
```

**Logic:**
1. Query Gmail for category counts (promotions, social, updates)
2. If no previous scan: estimate cleanup count = 70% of (promotions + social)
3. If previous scan exists: use stored sender profiles to estimate
4. Status determination:
   - `healthy`: < 100 potential cleanup emails
   - `needs_attention`: 100-1000
   - `critical`: > 1000

---

#### 2.1.2 Cleanup Flow Endpoints (NEW)

**Endpoint:** `POST /api/cleanup/start`

**Request:**
```python
class CleanupStartRequest(BaseModel):
    max_emails: int = Field(default=10000, ge=100, le=50000)
```

**Response:**
```python
class CleanupStartResponse(BaseModel):
    session_id: str  # UUID for this cleanup session
    status: str  # "scanning"
```

**Purpose:** Initiates a new cleanup session (like current scoring/start but returns session_id)

---

**Endpoint:** `GET /api/cleanup/progress/{session_id}`

**Response:**
```python
class CleanupProgressResponse(BaseModel):
    session_id: str
    status: str  # "scanning", "ready_for_review", "completed", "failed"
    progress: float  # 0.0 to 1.0
    total_emails: int
    scanned_emails: int

    # Live discoveries (updated as scan progresses)
    discoveries: Dict[str, int]  # {"promotions": 3200, "newsletters": 1400, ...}

    # Set when status = "ready_for_review"
    recommendations: Optional[RecommendationSummary]

    error: Optional[str]
```

**Purpose:** Polling endpoint for scanning screen

---

**Endpoint:** `GET /api/cleanup/recommendations/{session_id}`

**Response:**
```python
class RecommendationSummary(BaseModel):
    session_id: str
    total_to_cleanup: int
    total_protected: int
    space_savings: int

    category_breakdown: Dict[str, int]  # {"promotions": 2100, "newsletters": 1400, ...}

    protected_reasons: List[str]  # ["892 emails from people you email with", ...]

    top_delete_senders: List[SenderRecommendation]
    top_keep_senders: List[SenderRecommendation]

class SenderRecommendation(BaseModel):
    email: str
    display_name: Optional[str]
    count: int
    reason: str  # "You never open these", "Marketing sender", etc.
```

**Purpose:** Powers Inbox Report screen

---

**Endpoint:** `GET /api/cleanup/review-queue/{session_id}`

**Query Params:**
- `mode`: "quick" | "full"

**Response:**
```python
class ReviewQueueResponse(BaseModel):
    session_id: str
    mode: str
    total_items: int
    items: List[ReviewItem]

class ReviewItem(BaseModel):
    message_id: str
    sender_email: str
    sender_name: Optional[str]
    subject: str
    date: datetime
    snippet: str  # Email preview
    ai_suggestion: str  # "delete" | "keep"
    reasoning: str  # Why AI thinks this
    confidence: float
```

**Logic:**
- If `mode = "quick"`: return only UNCERTAIN emails (confidence < 0.85)
- If `mode = "full"`: return all non-KEEP emails
- Aim for < 50 items in quick mode

---

**Endpoint:** `POST /api/cleanup/review-decision/{session_id}`

**Request:**
```python
class ReviewDecisionRequest(BaseModel):
    message_id: str
    decision: str  # "keep" | "delete"
```

**Response:**
```python
class ReviewDecisionResponse(BaseModel):
    message_id: str
    decision: str
    remaining_in_queue: int
```

**Purpose:** Records user's review decision

---

**Endpoint:** `GET /api/cleanup/confirmation-summary/{session_id}`

**Response:**
```python
class ConfirmationSummary(BaseModel):
    session_id: str
    emails_to_delete: int
    senders_to_unsubscribe: int
    space_to_be_freed: int
    protected_count: int

    safety_info: SafetyInfo

class SafetyInfo(BaseModel):
    trash_recovery_days: int  # 30
    auto_protected_categories: List[str]  # ["Emails from contacts", ...]
```

---

**Endpoint:** `POST /api/cleanup/execute/{session_id}`

**Request:**
```python
class CleanupExecuteRequest(BaseModel):
    confirmed: bool = True
```

**Response:**
```python
class CleanupExecuteResponse(BaseModel):
    session_id: str
    status: str  # "executing", "completed"
    job_id: str  # For tracking progress
```

**Purpose:** Starts actual cleanup (async job)

---

**Endpoint:** `GET /api/cleanup/results/{session_id}`

**Response:**
```python
class CleanupResults(BaseModel):
    session_id: str
    status: str  # "executing", "completed", "failed"

    emails_deleted: int
    space_freed: int
    senders_unsubscribed: int
    filters_created: int

    errors: List[str]  # Any errors that occurred
    completed_at: Optional[datetime]
```

---

#### 2.1.3 Auto-Protected Endpoint (NEW)

**Endpoint:** `GET /api/auto-protected`

**Response:**
```python
class AutoProtectedResponse(BaseModel):
    categories: List[ProtectedCategory]

class ProtectedCategory(BaseModel):
    name: str  # "Google Contacts", "Recent Conversations", "Financial Institutions"
    description: str  # "People in your Google Contacts"
    count: int  # How many emails/senders protected by this
    icon: str  # Icon identifier for frontend
```

**Purpose:** Powers Settings page "What's Auto-Protected" section

---

### 2.2 Modified Existing Endpoints

#### 2.2.1 Stats Endpoint Enhancement

**Endpoint:** `GET /api/stats/current`

**Add to response:**
```python
class StatsResponse(BaseModel):
    # ... existing fields ...

    # NEW FIELDS for V2
    inbox_health_status: str  # "healthy", "needs_attention", "critical"
    potential_cleanup_count: int
    potential_space_savings: int
```

---

#### 2.2.2 Whitelist → Protected Senders

**Rename endpoints:**
- `GET /api/whitelist` → `GET /api/protected-senders`
- `POST /api/whitelist` → `POST /api/protected-senders`
- `DELETE /api/whitelist/{email}` → `DELETE /api/protected-senders/{email}`

**No schema changes, just endpoint renaming**

---

### 2.3 Database Schema Changes

#### 2.3.1 New Table: cleanup_sessions

```sql
CREATE TABLE cleanup_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,  -- UUID
    status TEXT NOT NULL,  -- scanning, ready_for_review, executing, completed, failed
    mode TEXT,  -- quick, full (set when user chooses)

    -- Scanning progress
    total_emails INTEGER DEFAULT 0,
    scanned_emails INTEGER DEFAULT 0,

    -- Recommendations
    total_to_cleanup INTEGER DEFAULT 0,
    total_protected INTEGER DEFAULT 0,
    space_savings INTEGER DEFAULT 0,

    -- Review decisions (JSON)
    review_decisions TEXT,  -- {message_id: decision}

    -- Final results
    emails_deleted INTEGER DEFAULT 0,
    space_freed INTEGER DEFAULT 0,
    senders_unsubscribed INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Error tracking
    error_message TEXT
);
```

**Purpose:** Tracks cleanup flow sessions (separate from cleanup_runs which track execution)

**Lifecycle:**
1. Created on `POST /api/cleanup/start`
2. Updated during scanning
3. Updated with review decisions
4. Finalized on execution complete
5. Auto-deleted after 24 hours (cleanup job)

---

#### 2.3.2 New Table: email_recommendations

```sql
CREATE TABLE email_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    message_id TEXT NOT NULL,
    thread_id TEXT,

    sender_email TEXT NOT NULL,
    sender_name TEXT,
    subject TEXT,
    snippet TEXT,
    received_date TIMESTAMP,

    -- AI recommendation
    ai_suggestion TEXT NOT NULL,  -- delete, keep
    reasoning TEXT,
    confidence REAL,

    -- User decision
    user_decision TEXT,  -- keep, delete (NULL if not reviewed)

    -- Categorization
    category TEXT,  -- promotions, newsletters, social, etc.

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (session_id) REFERENCES cleanup_sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX idx_recommendations_session ON email_recommendations(session_id);
CREATE INDEX idx_recommendations_suggestion ON email_recommendations(ai_suggestion);
```

**Purpose:** Stores per-email recommendations during cleanup flow

---

#### 2.3.3 Modify Table: whitelist_domains → protected_senders

```sql
ALTER TABLE whitelist_domains RENAME TO protected_senders;
-- No other changes needed
```

---

### 2.4 Services Architecture

#### 2.4.1 CleanupFlowService

**File:** `backend/services/cleanup_flow.py`

**Responsibilities:**
- Manages cleanup sessions (create, update, retrieve)
- Coordinates scanning, recommendation, review, execution steps
- Stores review decisions
- Generates confirmation summaries

**Key Methods:**
```python
class CleanupFlowService:
    async def create_session(max_emails: int) -> str  # Returns session_id
    async def start_scanning(session_id: str) -> None
    async def get_progress(session_id: str) -> CleanupProgressResponse
    async def get_recommendations(session_id: str) -> RecommendationSummary
    async def get_review_queue(session_id: str, mode: str) -> ReviewQueueResponse
    async def record_decision(session_id: str, message_id: str, decision: str) -> None
    async def get_confirmation_summary(session_id: str) -> ConfirmationSummary
    async def execute_cleanup(session_id: str) -> str  # Returns job_id
    async def get_results(session_id: str) -> CleanupResults
```

---

#### 2.4.2 RecommendationEngine

**File:** `backend/services/recommendation_engine.py`

**Responsibilities:**
- Generates cleanup recommendations based on email analysis
- Categorizes emails (promotions, newsletters, social, etc.)
- Determines what's protected vs. cleanable
- Provides reasoning for each recommendation

**Key Methods:**
```python
class RecommendationEngine:
    async def analyze_email(email: Dict) -> EmailAnalysis
    async def categorize(emails: List[Dict]) -> CategoryBreakdown
    async def generate_recommendations(session_id: str) -> RecommendationSummary
    async def determine_confidence(email: Dict) -> float
    async def explain_reasoning(email: Dict, suggestion: str) -> str
```

**Categorization Logic:**

| Category | Gmail Label | Signals |
|----------|-------------|---------|
| **Promotions** | CATEGORY_PROMOTIONS | Gmail category promotions |
| **Newsletters** | Has List-Unsubscribe header | List-Unsubscribe header present |
| **Social** | CATEGORY_SOCIAL | Gmail category social |
| **Updates** | CATEGORY_UPDATES | Gmail category updates |
| **Low Engagement** | N/A | Never opened, never replied, not starred |
| **Protected** | N/A | From contacts, replied to, whitelisted, financial/security |

---

#### 2.4.3 CleanupExecutor

**File:** `backend/services/cleanup_executor.py`

**Responsibilities:**
- Executes final cleanup based on review decisions
- Handles unsubscribing, filter creation, deletion
- Tracks progress and errors
- Updates cleanup_sessions and cleanup_runs tables

**Key Methods:**
```python
class CleanupExecutor:
    async def execute(session_id: str) -> str  # Returns job_id
    async def process_deletions(emails: List[str]) -> DeletionResult
    async def process_unsubscribes(senders: List[str]) -> UnsubscribeResult
    async def create_filters(senders: List[str]) -> FilterResult
    async def finalize_session(session_id: str, results: CleanupResults) -> None
```

---

### 2.5 Error Handling Strategy

#### 2.5.1 Error Categories

| Error Type | HTTP Code | Response | User Message |
|------------|-----------|----------|--------------|
| **Validation Error** | 422 | `{"error": "Invalid input", "detail": "..."}` | "Please check your input and try again" |
| **Gmail API Error** | 503 | `{"error": "Gmail unavailable", "retry_after": 60}` | "Gmail is temporarily unavailable. Retrying..." |
| **Rate Limit** | 429 | `{"error": "Rate limited", "retry_after": 120}` | "Too many requests. Please wait a moment." |
| **Session Not Found** | 404 | `{"error": "Session not found"}` | "This cleanup session has expired. Please start a new one." |
| **Internal Error** | 500 | `{"error": "Internal error", "id": "err_xyz"}` | "Something went wrong. Our team has been notified." |

#### 2.5.2 Retry Logic

**Gmail API calls:**
- Use `tenacity` library for exponential backoff
- Retry on 429 (rate limit) and 503 (service unavailable)
- Max retries: 3
- Backoff: 2s, 4s, 8s

**Cleanup execution:**
- If deletion fails for individual email: log error, continue
- If unsubscribe fails: log error, continue
- If Gmail connection lost: pause execution, show reconnect prompt

#### 2.5.3 Logging Strategy

**File:** `backend/utils/logging_config.py`

```python
# Log levels by module
LOGGING_CONFIG = {
    "cleanup_flow": "INFO",
    "recommendation_engine": "DEBUG",
    "cleanup_executor": "INFO",
    "gmail_client": "WARNING",
}

# Structured logging format
{
    "timestamp": "2024-11-29T12:00:00Z",
    "level": "INFO",
    "module": "cleanup_flow",
    "session_id": "abc-123",
    "message": "Scanning complete",
    "metadata": {
        "emails_scanned": 10000,
        "duration_seconds": 45
    }
}
```

---

## 3. Cleanup Engine Logic

### 3.1 Scanning Process

#### 3.1.1 Gmail API Query Strategy

**Batch 1: Category-based (Gmail native categories)**
```python
queries = [
    "category:promotions",
    "category:social",
    "category:updates",
]
```

**Batch 2: Header-based (List-Unsubscribe)**
```python
queries = [
    "list:(<.*>)",  # Has List-Unsubscribe header
]
```

**Batch 3: Sender pattern-based**
```python
queries = [
    "from:noreply@",
    "from:no-reply@",
    "from:newsletter@",
    "from:marketing@",
]
```

**Batching Logic:**
- Fetch messages in batches of 500
- Use `gmail.users().messages().list()` with pagination
- For each message ID, fetch full message with `gmail.users().messages().get()`
- Batch `get()` requests using `BatchHttpRequest` (up to 100 per batch)

#### 3.1.2 Scanning Progress Updates

**Update frequency:** Every 100 emails scanned

**Update logic:**
```python
async def update_scan_progress(session_id: str, scanned: int, total: int):
    discoveries = {
        "promotions": count_by_category("promotions"),
        "newsletters": count_with_unsubscribe(),
        "social": count_by_category("social"),
        "low_value": count_low_engagement(),
    }

    await db.execute(
        UPDATE cleanup_sessions
        SET scanned_emails = :scanned,
            total_emails = :total,
            discoveries = :discoveries
        WHERE session_id = :session_id
    )
```

---

### 3.2 Recommendation Generation

#### 3.2.1 Scoring Signals (Reuse from V1)

Use existing multi-signal scoring system from `agent/scoring.py`:

| Signal | Weight | Criteria |
|--------|--------|----------|
| **Category Score** | 30% | Gmail category (promotions = +30, primary = -30) |
| **Header Score** | 25% | List-Unsubscribe (+20), bulk sender patterns (+10) |
| **Engagement Score** | 25% | Never opened (+20), never replied (+15), not starred (+10) |
| **Keyword Score** | 10% | Spam keywords ("unsubscribe", "deal", "offer") |
| **Thread Score** | 10% | Single email thread (+10), low thread activity (+5) |

**Total Score Range:** 0-100
- **0-30:** KEEP (confident)
- **31-70:** UNCERTAIN (needs review)
- **71-100:** DELETE (confident)

**Confidence Calculation:**
```python
def calculate_confidence(score: int) -> float:
    # Distance from threshold determines confidence
    if score <= 30:
        return min(1.0, (30 - score) / 30)  # 0.0 to 1.0
    elif score >= 70:
        return min(1.0, (score - 70) / 30)  # 0.0 to 1.0
    else:
        return 0.0  # UNCERTAIN always has 0.0 confidence
```

#### 3.2.2 Protected Email Detection

**Auto-protected categories:**

```python
PROTECTED_RULES = [
    # People you communicate with
    {
        "name": "Emails from people you email with",
        "check": lambda email: email.user_replied_count > 0
    },

    # Google Contacts
    {
        "name": "People in your Google Contacts",
        "check": lambda email: email.sender_email in contacts
    },

    # Financial institutions
    {
        "name": "Financial institutions",
        "check": lambda email: any(domain in email.sender_domain
            for domain in FINANCIAL_DOMAINS)
    },

    # Security/verification emails
    {
        "name": "Security and verification emails",
        "check": lambda email: any(kw in email.subject.lower()
            for kw in ["verify", "confirmation", "otp", "2fa", "password reset"])
    },

    # Whitelisted senders
    {
        "name": "Protected senders (your list)",
        "check": lambda email: email.sender_domain in whitelist
    },
]
```

**Constants:**
```python
FINANCIAL_DOMAINS = [
    "chase.com", "wellsfargo.com", "bankofamerica.com", "paypal.com",
    "venmo.com", "stripe.com", "square.com", "coinbase.com",
]

SECURITY_KEYWORDS = [
    "verify", "verification", "confirm", "confirmation", "otp",
    "2fa", "two-factor", "password reset", "security alert",
    "suspicious activity", "login attempt"
]
```

---

### 3.3 Preview Mode (Dry Run)

**Purpose:** Show user what WOULD happen without actually deleting

**Implementation:**
```python
async def preview_cleanup(session_id: str) -> PreviewResult:
    # Get all emails marked for deletion
    delete_emails = await get_emails_to_delete(session_id)

    # Simulate deletion logic
    preview = {
        "emails_to_delete": len(delete_emails),
        "space_to_be_freed": sum(e.size for e in delete_emails),
        "senders_to_unsubscribe": get_unique_senders_with_unsubscribe(delete_emails),
        "filters_to_create": get_unique_senders(delete_emails),
    }

    # Return preview WITHOUT executing
    return preview
```

**Used in:** Confirmation screen (`/dashboard/cleanup/confirm`)

---

### 3.4 Real Deletion Process

#### 3.4.1 Deletion Strategy

**Two-phase approach:**

**Phase 1: Move to Trash**
```python
async def move_to_trash(message_ids: List[str]) -> DeletionResult:
    # Gmail API: trash() moves to Trash (recoverable for 30 days)
    results = []
    for message_id in message_ids:
        try:
            await gmail.users().messages().trash(
                userId='me',
                id=message_id
            ).execute()
            results.append({"id": message_id, "status": "trashed"})
        except Exception as e:
            results.append({"id": message_id, "status": "failed", "error": str(e)})

    return DeletionResult(
        total=len(message_ids),
        succeeded=len([r for r in results if r["status"] == "trashed"]),
        failed=len([r for r in results if r["status"] == "failed"]),
        errors=[r["error"] for r in results if "error" in r]
    )
```

**Phase 2: Permanent Delete (Optional, NOT default)**
```python
async def permanently_delete(message_ids: List[str]) -> DeletionResult:
    # Gmail API: delete() permanently removes (no recovery)
    # ONLY used if user explicitly enables "Permanent Delete" in settings
    # DEFAULT is Trash only
    ...
```

**Default behavior:** Always use Trash, never permanent delete

#### 3.4.2 Unsubscribe Methods

**Priority order:**

1. **mailto: unsubscribe** (most reliable)
```python
async def unsubscribe_mailto(mailto_url: str) -> bool:
    # Parse mailto:unsubscribe@example.com?subject=Unsubscribe
    email_to, subject = parse_mailto(mailto_url)

    # Send email via Gmail API
    await send_email(
        to=email_to,
        subject=subject or "Unsubscribe",
        body="Please unsubscribe me from this mailing list."
    )
    return True
```

2. **HTTP POST unsubscribe** (common for newsletters)
```python
async def unsubscribe_http_post(url: str) -> bool:
    # POST to unsubscribe URL
    response = await http_client.post(url, data={"unsubscribe": "true"})
    return response.status_code == 200
```

3. **HTTP GET unsubscribe** (one-click unsubscribe)
```python
async def unsubscribe_http_get(url: str) -> bool:
    # GET request to unsubscribe URL
    response = await http_client.get(url)
    return response.status_code == 200
```

**Error handling:**
- If unsubscribe fails: log error, continue with filter creation
- If sender has no unsubscribe method: skip, just create filter

---

### 3.5 AI Learning from Feedback

#### 3.5.1 Feedback Collection

**When user overrides AI suggestion:**
```python
async def record_feedback(
    message_id: str,
    original_classification: str,
    corrected_classification: str,
    reason: Optional[str] = None
):
    # Store in user_feedback table
    feedback = UserFeedback(
        feedback_type="email_override",
        target_id=message_id,
        original_classification=original_classification,
        corrected_classification=corrected_classification,
        reason=reason,
    )
    await db.add(feedback)

    # Update email_recommendations
    await db.execute(
        UPDATE email_recommendations
        SET user_decision = :decision
        WHERE message_id = :message_id
    )

    # Apply learning
    await apply_learning(feedback)
```

#### 3.5.2 Learning Algorithm

**Pattern extraction:**
```python
async def apply_learning(feedback: UserFeedback):
    # Extract pattern from feedback
    email = await get_email(feedback.target_id)

    # Sender-based learning
    if feedback_count_for_sender(email.sender_email) >= 3:
        # User has corrected 3+ emails from this sender in same direction
        create_preference(
            pref_type="sender_email",
            pattern=email.sender_email,
            classification=feedback.corrected_classification,
            confidence=0.8
        )

    # Domain-based learning
    if feedback_count_for_domain(email.sender_domain) >= 5:
        create_preference(
            pref_type="sender_domain",
            pattern=email.sender_domain,
            classification=feedback.corrected_classification,
            confidence=0.7
        )

    # Subject pattern learning
    if feedback.reason and "subject contains" in feedback.reason.lower():
        # User indicated subject pattern
        create_preference(
            pref_type="subject_pattern",
            pattern=extract_subject_pattern(email.subject),
            classification=feedback.corrected_classification,
            confidence=0.6
        )
```

**Preference storage:**
```python
class UserPreference(Base):
    pref_type: str  # sender_email, sender_domain, subject_pattern
    pattern: str  # The pattern to match
    classification: str  # KEEP or DELETE
    confidence: float  # 0.0 to 1.0
    feedback_count: int  # How many feedbacks led to this
    last_feedback: datetime
```

**Applying preferences in future scans:**
```python
async def apply_learned_preferences(email: Dict) -> Optional[str]:
    # Check user preferences first (highest priority)
    prefs = await get_user_preferences()

    for pref in sorted(prefs, key=lambda p: p.confidence, reverse=True):
        if matches_preference(email, pref):
            # Override AI classification with learned preference
            return pref.classification

    return None  # No preference matched, use AI classification
```

---

## 4. Data Consistency Rules

### 4.1 Schema Definitions

#### 4.1.1 EmailItem (Frontend + Backend)

**TypeScript (Frontend):**
```typescript
interface EmailItem {
  messageId: string
  threadId: string

  // Sender
  senderEmail: string
  senderName: string | null

  // Content
  subject: string
  snippet: string
  receivedDate: string  // ISO 8601

  // Size
  sizeBytes: number

  // Labels
  gmailLabels: string[]

  // AI Analysis
  aiSuggestion: "keep" | "delete"
  reasoning: string
  confidence: number  // 0.0 to 1.0

  // User Decision
  userDecision: "keep" | "delete" | null

  // Categorization
  category: "promotions" | "newsletters" | "social" | "updates" | "low_value" | "protected"
}
```

**Python (Backend):**
```python
class EmailRecommendation(Base):
    __tablename__ = "email_recommendations"

    id: int
    session_id: str
    message_id: str
    thread_id: str

    sender_email: str
    sender_name: Optional[str]

    subject: str
    snippet: str
    received_date: datetime

    size_bytes: int

    gmail_labels: str  # JSON array

    ai_suggestion: str  # "keep", "delete"
    reasoning: str
    confidence: float

    user_decision: Optional[str]  # "keep", "delete", NULL

    category: str

    created_at: datetime
```

**Validation Rules:**
- `messageId`: Required, unique per session
- `senderEmail`: Required, valid email format
- `subject`: Required, max 500 chars
- `aiSuggestion`: Required, enum ["keep", "delete"]
- `confidence`: Required, 0.0 <= value <= 1.0
- `category`: Required, enum ["promotions", "newsletters", "social", "updates", "low_value", "protected"]

---

#### 4.1.2 Recommendation (Summary Object)

**TypeScript (Frontend):**
```typescript
interface Recommendation {
  totalToCleanup: number
  totalProtected: number
  spaceSavings: number  // Bytes

  categoryBreakdown: {
    promotions: number
    newsletters: number
    social: number
    other: number
  }

  protectedReasons: string[]  // ["892 emails from people you email with"]

  topDeleteSenders: SenderRecommendation[]
  topKeepSenders: SenderRecommendation[]
}

interface SenderRecommendation {
  email: string
  displayName: string | null
  count: number
  reason: string
}
```

**Python (Backend):**
```python
class RecommendationSummary(BaseModel):
    session_id: str
    total_to_cleanup: int
    total_protected: int
    space_savings: int

    category_breakdown: Dict[str, int]
    protected_reasons: List[str]

    top_delete_senders: List[SenderRecommendation]
    top_keep_senders: List[SenderRecommendation]

class SenderRecommendation(BaseModel):
    email: str
    display_name: Optional[str]
    count: int
    reason: str
```

**Validation Rules:**
- All counts must be >= 0
- `spaceSavings` must be >= 0
- `categoryBreakdown` keys must match enum ["promotions", "newsletters", "social", "other"]
- Sum of category counts should equal `totalToCleanup`

---

#### 4.1.3 CleanupResult

**TypeScript (Frontend):**
```typescript
interface CleanupResult {
  sessionId: string
  status: "executing" | "completed" | "failed"

  emailsDeleted: number
  spaceFeed: number
  sendersUnsubscribed: number
  filtersCreated: number

  errors: string[]
  completedAt: string | null  // ISO 8601
}
```

**Python (Backend):**
```python
class CleanupResults(BaseModel):
    session_id: str
    status: str  # "executing", "completed", "failed"

    emails_deleted: int
    space_freed: int
    senders_unsubscribed: int
    filters_created: int

    errors: List[str]
    completed_at: Optional[datetime]
```

**Validation Rules:**
- All counts must be >= 0
- `status` must be enum ["executing", "completed", "failed"]
- If `status = "completed"`, `completedAt` must be set
- `errors` should be empty list if `status = "completed"`

---

### 4.2 Field Validation Rules

| Field | Type | Required | Min | Max | Pattern/Enum | Default |
|-------|------|----------|-----|-----|--------------|---------|
| **emailsToDelete** | int | Yes | 0 | ∞ | - | - |
| **spaceSavings** | int | Yes | 0 | ∞ | - | 0 |
| **confidence** | float | Yes | 0.0 | 1.0 | - | - |
| **aiSuggestion** | str | Yes | - | - | ["keep", "delete"] | - |
| **category** | str | Yes | - | - | ["promotions", "newsletters", "social", "updates", "low_value", "protected"] | - |
| **status** | str | Yes | - | - | ["scanning", "ready_for_review", "executing", "completed", "failed"] | - |
| **senderEmail** | str | Yes | 3 | 320 | Email regex | - |
| **subject** | str | Yes | 0 | 500 | - | "" |

---

### 4.3 API Request/Response Contracts

#### 4.3.1 POST /api/cleanup/start

**Request:**
```json
{
  "max_emails": 10000
}
```

**Response (Success):**
```json
{
  "session_id": "abc-123-def-456",
  "status": "scanning"
}
```

**Response (Error - Invalid Input):**
```json
{
  "error": "Invalid input",
  "detail": "max_emails must be between 100 and 50000"
}
```

---

#### 4.3.2 GET /api/cleanup/progress/{session_id}

**Response (Scanning):**
```json
{
  "session_id": "abc-123",
  "status": "scanning",
  "progress": 0.45,
  "total_emails": 10000,
  "scanned_emails": 4500,
  "discoveries": {
    "promotions": 3200,
    "newsletters": 1400,
    "social": 500,
    "low_value": 200
  },
  "recommendations": null,
  "error": null
}
```

**Response (Ready for Review):**
```json
{
  "session_id": "abc-123",
  "status": "ready_for_review",
  "progress": 1.0,
  "total_emails": 10000,
  "scanned_emails": 10000,
  "discoveries": {
    "promotions": 3200,
    "newsletters": 1400,
    "social": 500,
    "low_value": 200
  },
  "recommendations": {
    "total_to_cleanup": 4200,
    "total_protected": 5800,
    "space_savings": 2400000000
  },
  "error": null
}
```

---

#### 4.3.3 POST /api/cleanup/review-decision/{session_id}

**Request:**
```json
{
  "message_id": "msg-123",
  "decision": "keep"
}
```

**Response:**
```json
{
  "message_id": "msg-123",
  "decision": "keep",
  "remaining_in_queue": 42
}
```

---

### 4.4 Frontend-Backend Type Matching

**Generate TypeScript types from Pydantic schemas:**

**Script:** `scripts/generate-types.py`

```python
# Existing script - ensure it handles new V2 schemas
# Should auto-generate types for:
# - CleanupProgressResponse
# - RecommendationSummary
# - ReviewQueueResponse
# - CleanupResults
# etc.
```

**Validation:**
After modifying `schemas.py`, ALWAYS run:
```bash
cd backend && source venv/bin/activate && cd .. && python scripts/generate-types.py
```

This regenerates `frontend/lib/api-types.ts` to match backend.

---

## 5. Migration Plan

### 5.1 V2 Folder Structure

**Approach:** Side-by-side V1 and V2 during development

```
backend/
├── routers/
│   ├── v1/                          # Move existing routers here
│   │   ├── auth.py
│   │   ├── runs.py
│   │   ├── scoring.py
│   │   ├── ... (all existing)
│   └── v2/                          # New V2 routers
│       ├── cleanup_flow.py          # /api/v2/cleanup/*
│       ├── inbox_health.py          # /api/v2/inbox-health
│       ├── protected_senders.py     # /api/v2/protected-senders
│       └── auto_protected.py        # /api/v2/auto-protected
├── services/
│   ├── cleanup_flow.py              # NEW
│   ├── recommendation_engine.py     # NEW
│   └── cleanup_executor.py          # NEW
└── main.py                          # Register both V1 and V2 routers

frontend/
├── app/
│   ├── dashboard/
│   │   ├── v1/                      # Move existing pages here
│   │   │   ├── score/page.tsx
│   │   │   ├── senders/page.tsx
│   │   │   └── ... (all existing)
│   │   ├── cleanup/                 # NEW V2 cleanup flow
│   │   │   ├── scanning/page.tsx
│   │   │   ├── report/page.tsx
│   │   │   └── ...
│   │   └── page.tsx                 # V2 dashboard (replaces v1)
└── lib/
    ├── api-v1.ts                    # Rename existing api.ts
    └── api-v2.ts                    # NEW V2 API client
```

---

### 5.2 V1 and V2 Coexistence

#### 5.2.1 Backend Route Registration

**File:** `backend/main.py`

```python
from fastapi import FastAPI
from routers.v1 import auth as auth_v1, runs as runs_v1, scoring as scoring_v1
from routers.v2 import cleanup_flow, inbox_health, protected_senders

app = FastAPI()

# V1 routes (existing)
app.include_router(auth_v1.router, prefix="/api/auth", tags=["auth"])
app.include_router(runs_v1.router, prefix="/api/runs", tags=["runs"])
app.include_router(scoring_v1.router, prefix="/api/scoring", tags=["scoring"])
# ... all existing V1 routers

# V2 routes (new)
app.include_router(cleanup_flow.router, prefix="/api/v2/cleanup", tags=["cleanup-v2"])
app.include_router(inbox_health.router, prefix="/api/v2", tags=["health-v2"])
app.include_router(protected_senders.router, prefix="/api/v2/protected-senders", tags=["protected-v2"])
```

**Benefits:**
- V1 and V2 APIs run simultaneously
- No breaking changes to existing users
- Can switch between V1 and V2 with feature flag

---

#### 5.2.2 Frontend Feature Flag

**File:** `frontend/lib/feature-flags.ts`

```typescript
export const FEATURE_FLAGS = {
  USE_V2_CLEANUP: process.env.NEXT_PUBLIC_USE_V2_CLEANUP === "true",
  USE_V2_DASHBOARD: process.env.NEXT_PUBLIC_USE_V2_DASHBOARD === "true",
}
```

**File:** `frontend/app/dashboard/page.tsx`

```typescript
import { FEATURE_FLAGS } from "@/lib/feature-flags"
import DashboardV1 from "./v1/dashboard-v1"
import DashboardV2 from "./dashboard-v2"

export default function DashboardPage() {
  if (FEATURE_FLAGS.USE_V2_DASHBOARD) {
    return <DashboardV2 />
  }
  return <DashboardV1 />
}
```

---

### 5.3 Database Migration Strategy

#### 5.3.1 Alembic Migration

**Create migration:**
```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "Add V2 cleanup tables"
```

**Migration file:** `backend/alembic/versions/xxx_add_v2_cleanup_tables.py`

```python
def upgrade():
    # Create cleanup_sessions table
    op.create_table(
        'cleanup_sessions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('session_id', sa.String(), unique=True, nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('mode', sa.String()),
        # ... all columns from schema
    )

    # Create email_recommendations table
    op.create_table(
        'email_recommendations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('session_id', sa.String(), nullable=False),
        # ... all columns from schema
    )

    # Rename whitelist_domains to protected_senders
    op.rename_table('whitelist_domains', 'protected_senders')

def downgrade():
    op.drop_table('email_recommendations')
    op.drop_table('cleanup_sessions')
    op.rename_table('protected_senders', 'whitelist_domains')
```

**Run migration:**
```bash
alembic upgrade head
```

#### 5.3.2 Data Preservation

**V1 tables remain untouched:**
- `cleanup_runs` - Keep all existing run history
- `senders` - Keep all discovered senders
- `cleanup_actions` - Keep all action logs
- `email_scores` - Keep all scored emails
- `sender_profiles` - Keep all sender profiles

**V2 uses NEW tables:**
- `cleanup_sessions` - New session-based cleanup
- `email_recommendations` - New recommendation system

**No data loss during migration**

---

### 5.4 Rollback Plan

#### 5.4.1 Immediate Rollback (Feature Flag)

**If V2 has critical bug:**

1. **Disable V2 via environment variable:**
```bash
# .env.local
NEXT_PUBLIC_USE_V2_CLEANUP=false
NEXT_PUBLIC_USE_V2_DASHBOARD=false
```

2. **Restart frontend:**
```bash
cd frontend
npm run dev
```

**Result:** App instantly reverts to V1 (no deployment needed)

---

#### 5.4.2 Database Rollback

**If V2 database migration causes issues:**

```bash
cd backend
source venv/bin/activate
alembic downgrade -1
```

**Result:**
- Drops V2 tables (`cleanup_sessions`, `email_recommendations`)
- Renames `protected_senders` back to `whitelist_domains`
- V1 fully functional

---

#### 5.4.3 API Rollback

**If V2 API has issues:**

1. **Disable V2 routes in `main.py`:**
```python
# Comment out V2 routers
# app.include_router(cleanup_flow.router, prefix="/api/v2/cleanup")
# app.include_router(inbox_health.router, prefix="/api/v2")
```

2. **Restart backend:**
```bash
cd backend
python main.py
```

**Result:** V2 API endpoints return 404, frontend falls back to V1

---

### 5.5 Phased Rollout Plan

#### Week 1: Foundation

**Backend:**
- [ ] Create `routers/v2/` directory structure
- [ ] Implement `cleanup_flow.py` with basic endpoints
- [ ] Create `services/cleanup_flow.py`
- [ ] Create database migration
- [ ] Run migration on dev database

**Frontend:**
- [ ] Create `app/dashboard/cleanup/` directory
- [ ] Implement feature flag system
- [ ] Create `scanning/page.tsx` with progress UI
- [ ] Create `api-v2.ts` client

**Testing:**
- [ ] Test V1 still works (no regression)
- [ ] Test V2 scanning endpoint with curl
- [ ] Verify database migration successful

---

#### Week 2: Cleanup Flow

**Backend:**
- [ ] Implement `recommendation_engine.py`
- [ ] Create `/api/v2/cleanup/recommendations` endpoint
- [ ] Create `/api/v2/cleanup/review-queue` endpoint
- [ ] Implement review decision recording

**Frontend:**
- [ ] Create `report/page.tsx` (Inbox Report)
- [ ] Create `review/page.tsx` (Review Queue)
- [ ] Implement cleanup flow context
- [ ] Wire up mode selection

**Testing:**
- [ ] End-to-end test: scan → report → review
- [ ] Test review decisions are saved
- [ ] Verify no V1 breakage

---

#### Week 3: Execution & Polish

**Backend:**
- [ ] Implement `cleanup_executor.py`
- [ ] Create `/api/v2/cleanup/execute` endpoint
- [ ] Implement unsubscribe logic
- [ ] Implement filter creation

**Frontend:**
- [ ] Create `confirm/page.tsx` (Confirmation)
- [ ] Create `success/page.tsx` (Success screen)
- [ ] Implement execution progress tracking
- [ ] Add error handling

**Testing:**
- [ ] Test full cleanup flow end-to-end
- [ ] Test deletion (move to trash)
- [ ] Test unsubscribe methods
- [ ] Verify cleanup_sessions finalized correctly

---

#### Week 4: Dashboard & Settings

**Backend:**
- [ ] Implement `/api/v2/inbox-health` endpoint
- [ ] Implement `/api/v2/auto-protected` endpoint
- [ ] Rename whitelist endpoints to protected-senders

**Frontend:**
- [ ] Redesign Dashboard with InboxHealthCard
- [ ] Simplify Settings page
- [ ] Add "What's Auto-Protected" section
- [ ] Update navigation (4 items only)

**Testing:**
- [ ] Test Dashboard health status
- [ ] Test Settings whitelist → protected senders
- [ ] Full regression test on V1

---

#### Week 5: Migration & Cutover

**Tasks:**
- [ ] Move V1 pages to `v1/` subdirectory
- [ ] Set `USE_V2_CLEANUP=true` as default
- [ ] Remove V1 nav items (Score, Senders, Subscriptions, Rules)
- [ ] Update README with V2 docs

**Testing:**
- [ ] Full E2E test on V2
- [ ] Test rollback plan (flip feature flag)
- [ ] Performance testing (10k+ emails)
- [ ] User acceptance testing

**Go-Live:**
- [ ] Deploy V2 to production
- [ ] Monitor error logs
- [ ] Collect user feedback
- [ ] Iterate based on feedback

---

## Appendix: ASCII Diagrams

### A1. Cleanup Flow State Machine

```
┌─────────┐
│  IDLE   │
└────┬────┘
     │ POST /api/cleanup/start
     ▼
┌─────────┐
│SCANNING │ ◄─── Poll /api/cleanup/progress every 2s
└────┬────┘
     │ Scan complete
     ▼
┌──────────────┐
│READY_FOR_    │
│REVIEW        │
└────┬─────────┘
     │ User selects mode
     ▼
┌─────────┐
│REVIEWING│ ◄─── POST /api/cleanup/review-decision
└────┬────┘
     │ Review complete
     ▼
┌─────────┐
│CONFIRMING│
└────┬────┘
     │ POST /api/cleanup/execute
     ▼
┌─────────┐
│EXECUTING│ ◄─── Poll /api/cleanup/results every 2s
└────┬────┘
     │ Execution complete
     ▼
┌─────────┐
│COMPLETED│
└─────────┘
```

---

### A2. Component Hierarchy (Dashboard)

```
DashboardPage
├── InboxHealthCard
│   ├── StatusBadge (Healthy/Needs Attention)
│   ├── CleanupCountText
│   ├── SpaceSavingsText
│   └── StartCleanupButton
├── QuickStats (4 cards)
│   ├── StatCard (Emails Cleaned)
│   ├── StatCard (Space Freed)
│   ├── StatCard (Senders Muted)
│   └── StatCard (Last Cleanup)
├── QuickActions
│   ├── Link (Free Up Space → /dashboard/space)
│   ├── Link (Protected Senders → /dashboard/settings)
│   └── Link (History → /dashboard/history)
└── ActivityFeed
    └── ActivityItem[] (Recent actions)
```

---

### A3. Database Relationships (V2)

```
cleanup_sessions
├── id (PK)
├── session_id (UUID, unique)
└── ... (session data)
     │
     │ 1:N relationship
     ▼
email_recommendations
├── id (PK)
├── session_id (FK)
├── message_id
└── ... (recommendation data)

protected_senders (renamed from whitelist_domains)
├── id (PK)
├── domain
└── ... (whitelist data)
     │
     │ Referenced by safety checks
     ▼
(No FK, just domain matching)
```

---

## Summary: V2 Key Improvements

| Aspect | V1 | V2 |
|--------|----|----|
| **Navigation** | 8 items | 4 items |
| **Cleanup Flow** | One page (Score) with tabs | 5-step wizard (Scanning → Report → Review → Confirm → Success) |
| **Review UX** | Grid of all emails | One-at-a-time card review |
| **Trust Building** | Technical jargon (KEEP/DELETE/UNCERTAIN) | "What's Protected" section, plain language |
| **Mode Selection** | None (all-or-nothing) | Quick Clean vs. Review All |
| **Terminology** | Whitelist, Scoring, Senders | Protected Senders, Cleanup, Inbox Health |
| **API Structure** | V1 endpoints only | V1 + V2 coexist (feature flagged) |
| **Database** | 5 tables (cleanup_runs, senders, etc.) | +2 tables (cleanup_sessions, email_recommendations) |
| **Reversibility** | Browser confirm() dialogs | Dedicated confirmation screen with safety info |
| **Success Experience** | Alert popup | Full success screen with celebration |

---

## End of Document

This architecture document provides complete specifications for implementing Inbox Nuke V2. All sections are detailed enough for a developer to implement without additional design decisions.

For questions or clarifications, refer to:
- **UX Blueprint** (`UX_BLUEPRINT.md`) for user experience goals
- **UX Gap Analysis** (`UX_GAP_ANALYSIS.md`) for V1 vs. Blueprint comparison
- **App Map** (`APP_MAP.md`) for current V1 implementation details
- **CLAUDE.md** for project-specific development practices
