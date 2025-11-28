# Inbox Nuke Agent - GitHub Issues

This document contains all issues needed to build the Inbox Nuke Agent from scratch. Issues are organized into epics/milestones and ordered by dependency and priority.

---

## Milestone 1: Project Setup & Infrastructure

### Issue #1: Initialize Project Structure and Development Environment
**Priority:** P0-Critical
**Type:** infrastructure
**Complexity:** M

**Description:**
Set up the complete project folder structure for both backend and frontend, including all necessary configuration files and development tooling.

**Acceptance Criteria:**
- [ ] Create `/backend` directory with Python project structure
- [ ] Create `/frontend` directory with Next.js App Router structure
- [ ] Add `.gitignore` files for both Python and Node.js
- [ ] Create `backend/requirements.txt` with all dependencies listed in PRD
- [ ] Create `frontend/package.json` with Next.js, TailwindCSS, and shadcn/ui
- [ ] Add `README.md` with setup instructions
- [ ] Create `backend/data/` directory for SQLite database
- [ ] Set up `.env.example` files for both backend and frontend

**Dependencies:** None

---

### Issue #2: Backend FastAPI Server Setup
**Priority:** P0-Critical
**Type:** infrastructure
**Complexity:** M

**Description:**
Initialize the FastAPI backend server with basic configuration, CORS middleware, and health check endpoint.

**Acceptance Criteria:**
- [ ] Create `backend/main.py` with FastAPI app initialization
- [ ] Configure CORS middleware to allow localhost:3000 (Next.js)
- [ ] Add health check endpoint `GET /health`
- [ ] Set up Uvicorn server configuration
- [ ] Add environment variable loading with python-dotenv
- [ ] Verify server starts successfully on `http://localhost:8000`
- [ ] Add basic error handling and logging with rich (optional)

**Dependencies:** #1

---

### Issue #3: Frontend Next.js Application Setup
**Priority:** P0-Critical
**Type:** infrastructure
**Complexity:** M

**Description:**
Initialize Next.js application with App Router, TailwindCSS, and shadcn/ui component library.

**Acceptance Criteria:**
- [ ] Initialize Next.js 14+ with App Router in `/frontend`
- [ ] Configure TailwindCSS with custom theme colors
- [ ] Install and configure shadcn/ui CLI
- [ ] Add initial shadcn/ui components (Button, Card, Badge, Progress)
- [ ] Create `lib/api.ts` for backend API calls
- [ ] Set up environment variable for `NEXT_PUBLIC_BACKEND_URL`
- [ ] Create basic layout with header/footer
- [ ] Verify development server starts on `http://localhost:3000`

**Dependencies:** #1

---

## Milestone 2: Database & Data Models

### Issue #4: SQLAlchemy Database Configuration
**Priority:** P0-Critical
**Type:** infrastructure
**Complexity:** M

**Description:**
Set up SQLAlchemy with SQLite database connection, session management, and base model configuration.

**Acceptance Criteria:**
- [ ] Create `backend/db.py` with SQLAlchemy setup
- [ ] Configure SQLite database at `backend/data/inbox_nuke.db`
- [ ] Implement `get_db()` dependency for FastAPI routes
- [ ] Create Base declarative model class
- [ ] Add database initialization function `init_db()`
- [ ] Implement connection pooling and session cleanup
- [ ] Add database migration strategy (Alembic optional for local)

**Dependencies:** #2

---

### Issue #5: Gmail Credentials Database Model
**Priority:** P0-Critical
**Type:** feature
**Complexity:** S

**Description:**
Create SQLAlchemy model for storing Gmail OAuth credentials (access token, refresh token, expiry).

**Acceptance Criteria:**
- [ ] Create `GmailCredentials` model in `backend/models.py`
- [ ] Add fields: `user_id` (PK), `access_token`, `refresh_token`, `expiry`, `scopes`
- [ ] Add timestamps: `created_at`, `updated_at`
- [ ] Implement token encryption/decryption helpers (optional for MVP)
- [ ] Add model to database initialization
- [ ] Write unit tests for model creation and updates

**Dependencies:** #4

---

### Issue #6: Cleanup Runs Database Model
**Priority:** P0-Critical
**Type:** feature
**Complexity:** M

**Description:**
Create SQLAlchemy model for tracking cleanup run sessions with progress, stats, and status.

**Acceptance Criteria:**
- [ ] Create `CleanupRun` model in `backend/models.py`
- [ ] Add fields: `id`, `status` (enum: pending/running/paused/completed/failed)
- [ ] Add stats fields: `senders_total`, `senders_processed`, `emails_deleted`, `bytes_freed_estimate`
- [ ] Add timestamps: `started_at`, `finished_at`
- [ ] Add `progress_cursor` (JSON) for resumability
- [ ] Add `error_message` field
- [ ] Create enum for run status
- [ ] Add indexes on `status` and `started_at`

**Dependencies:** #4

---

### Issue #7: Senders Database Model
**Priority:** P0-Critical
**Type:** feature
**Complexity:** M

**Description:**
Create SQLAlchemy model for discovered email senders with metadata and action tracking.

**Acceptance Criteria:**
- [ ] Create `Sender` model in `backend/models.py`
- [ ] Add fields: `id`, `email`, `domain`, `message_count`
- [ ] Add boolean fields: `has_list_unsubscribe`, `unsubscribed`, `filter_created`
- [ ] Add `last_seen_at`, `first_seen_at`, `created_at`
- [ ] Add `unsubscribe_method` (enum: mailto/url/none)
- [ ] Add `unsubscribe_header` (JSON) to store raw header data
- [ ] Create unique index on `email`
- [ ] Add index on `domain`

**Dependencies:** #4

---

### Issue #8: Cleanup Actions and Whitelist Models
**Priority:** P1-High
**Type:** feature
**Complexity:** S

**Description:**
Create models for logging cleanup actions and managing whitelisted domains.

**Acceptance Criteria:**
- [ ] Create `CleanupAction` model with fields: `run_id`, `timestamp`, `action_type`, `sender_email`, `email_count`, `bytes_freed`, `notes`
- [ ] Create `WhitelistDomain` model with fields: `domain`, `reason`, `created_at`
- [ ] Add foreign key relationship: `CleanupAction.run_id` → `CleanupRun.id`
- [ ] Add index on `CleanupAction.run_id`
- [ ] Create unique index on `WhitelistDomain.domain`
- [ ] Add default whitelist entries (common financial, government domains)

**Dependencies:** #4, #6

---

## Milestone 3: Gmail OAuth & Authentication

### Issue #9: Google OAuth Configuration Setup
**Priority:** P0-Critical
**Type:** infrastructure
**Complexity:** S

**Description:**
Configure Google Cloud Project, enable Gmail API, and set up OAuth 2.0 credentials for local development.

**Acceptance Criteria:**
- [ ] Document steps to create Google Cloud Project
- [ ] Enable Gmail API in Google Cloud Console
- [ ] Create OAuth 2.0 Client ID (Desktop or Web application)
- [ ] Configure authorized redirect URI: `http://localhost:8000/auth/google/callback`
- [ ] Add required OAuth scopes to documentation: `gmail.readonly`, `gmail.modify`, `gmail.settings.basic`, `gmail.send`
- [ ] Add `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` to `.env.example`
- [ ] Create setup guide in `docs/OAUTH_SETUP.md`

**Dependencies:** None

---

### Issue #10: OAuth Backend Implementation
**Priority:** P0-Critical
**Type:** feature
**Complexity:** L

**Description:**
Implement Google OAuth 2.0 flow backend handlers for authentication and token management.

**Acceptance Criteria:**
- [ ] Create `backend/oauth.py` with OAuth helper functions
- [ ] Implement `GET /auth/google/start` endpoint to initiate OAuth flow
- [ ] Implement `GET /auth/google/callback` endpoint to handle callback
- [ ] Save access token, refresh token, and expiry to database
- [ ] Implement token refresh logic for expired tokens
- [ ] Add error handling for OAuth failures
- [ ] Return success/failure status to frontend
- [ ] Add logging for OAuth events

**Dependencies:** #2, #5, #9

---

### Issue #11: OAuth Frontend Integration
**Priority:** P0-Critical
**Type:** feature
**Complexity:** M

**Description:**
Create frontend OAuth flow with "Connect Gmail" button and callback handling.

**Acceptance Criteria:**
- [ ] Create home page with "Connect Gmail" button
- [ ] Implement OAuth redirect to backend `/auth/google/start`
- [ ] Create callback page at `/auth/callback` to handle OAuth response
- [ ] Display success/error messages after OAuth completion
- [ ] Store authentication state in localStorage or context
- [ ] Redirect to dashboard after successful authentication
- [ ] Add "Disconnect" functionality
- [ ] Show current connection status

**Dependencies:** #3, #10

---

## Milestone 4: Gmail API Integration

### Issue #12: Gmail API Client Wrapper
**Priority:** P0-Critical
**Type:** feature
**Complexity:** L

**Description:**
Create a Gmail API client wrapper with methods for common operations (list messages, get message, batch operations).

**Acceptance Criteria:**
- [ ] Create `backend/gmail_client.py` with `GmailClient` class
- [ ] Implement `list_messages(query, max_results)` method
- [ ] Implement `get_message(message_id)` method with full payload
- [ ] Implement `batch_delete(message_ids)` method using `batchModify`
- [ ] Implement `batch_trash(message_ids)` method
- [ ] Add retry logic with exponential backoff using tenacity
- [ ] Handle rate limiting (respect Gmail API quotas)
- [ ] Add proper error handling and logging
- [ ] Implement credential refresh on token expiry

**Dependencies:** #10

---

### Issue #13: Sender Discovery Scanner
**Priority:** P0-Critical
**Type:** feature
**Complexity:** XL

**Description:**
Implement sender discovery system that scans Gmail for mailing list senders and extracts metadata.

**Acceptance Criteria:**
- [ ] Create `scan_for_senders()` function in Gmail client
- [ ] Query messages: `category:promotions OR category:social OR category:updates`
- [ ] Extract sender email and domain from each message
- [ ] Check for `List-Unsubscribe` header presence
- [ ] Parse `List-Unsubscribe` header (mailto vs URL)
- [ ] Count message frequency per sender
- [ ] Store/update sender data in database
- [ ] Implement pagination for large inboxes (use `pageToken`)
- [ ] Add progress tracking (messages scanned)
- [ ] Handle API rate limits gracefully

**Dependencies:** #7, #12

---

### Issue #14: Gmail Filters API Integration
**Priority:** P1-High
**Type:** feature
**Complexity:** L

**Description:**
Implement Gmail Filters API integration to create mute/auto-archive filters for processed senders.

**Acceptance Criteria:**
- [ ] Add `create_filter()` method to Gmail client
- [ ] Filter criteria: `from:sender@example.com`
- [ ] Filter actions: skip inbox, mark as read, apply label
- [ ] Create "Muted" label if it doesn't exist
- [ ] Implement `list_existing_filters()` to avoid duplicates
- [ ] Add filter ID tracking in database
- [ ] Handle filter creation errors (quota, invalid sender)
- [ ] Add `delete_filter()` method for cleanup
- [ ] Log filter creation in cleanup actions

**Dependencies:** #12

---

### Issue #15: Email Deletion and Cleanup Logic
**Priority:** P1-High
**Type:** feature
**Complexity:** L

**Description:**
Implement bulk email deletion logic with safety checks and batch operations.

**Acceptance Criteria:**
- [ ] Create `delete_emails_from_sender(sender, older_than_days)` function
- [ ] Build Gmail query: `from:sender@example.com older_than:Nd`
- [ ] Fetch message IDs matching query
- [ ] Use `batchModify` to trash messages (soft delete)
- [ ] Implement batching (max 1000 messages per batch)
- [ ] Estimate bytes freed (approximate from message size)
- [ ] Track deletion count and bytes in cleanup actions
- [ ] Add progress callback for UI updates
- [ ] Implement safety checks before deletion (whitelist, keywords)

**Dependencies:** #12

---

## Milestone 5: Autonomous Agent System

### Issue #16: Safety Guardrails Implementation
**Priority:** P0-Critical
**Type:** feature
**Complexity:** M

**Description:**
Implement safety checks to prevent deletion of important emails (financial, transactional, etc.).

**Acceptance Criteria:**
- [ ] Create `backend/agent/safety.py` with safety check functions
- [ ] Implement keyword blocklist: "invoice", "receipt", "bank", "payment", "statement", "tax", "verification code", "security alert"
- [ ] Check subject line against blocklist before deletion
- [ ] Implement domain whitelist check against database
- [ ] Add sender category detection (financial, government, healthcare)
- [ ] Create `is_safe_to_delete(message)` function
- [ ] Log safety violations (emails skipped)
- [ ] Make blocklist configurable via settings
- [ ] Add unit tests for all safety scenarios

**Dependencies:** #8, #12

---

### Issue #17: Unsubscribe Handler - Email Method
**Priority:** P1-High
**Type:** feature
**Complexity:** M

**Description:**
Implement automatic unsubscribe via mailto: links found in List-Unsubscribe headers.

**Acceptance Criteria:**
- [ ] Create `backend/agent/unsubscribe.py` with unsubscribe functions
- [ ] Parse mailto: addresses from `List-Unsubscribe` header
- [ ] Send unsubscribe email using Gmail API (send message)
- [ ] Email subject: "Unsubscribe"
- [ ] Email body: Simple unsubscribe request
- [ ] Handle send errors gracefully
- [ ] Log successful unsubscribe attempts
- [ ] Update sender record: `unsubscribed = True`
- [ ] Add retry logic for failed sends
- [ ] Track unsubscribe success/failure rates

**Dependencies:** #12, #13

---

### Issue #18: Unsubscribe Handler - HTTP Method
**Priority:** P1-High
**Type:** feature
**Complexity:** M

**Description:**
Implement automatic unsubscribe via HTTP/HTTPS URLs found in List-Unsubscribe headers.

**Acceptance Criteria:**
- [ ] Parse HTTP(S) URLs from `List-Unsubscribe` header
- [ ] Use `httpx` to make POST/GET request to unsubscribe URL
- [ ] Follow redirects (max 5)
- [ ] Handle common unsubscribe page patterns
- [ ] Set reasonable timeout (10 seconds)
- [ ] Handle SSL/certificate errors
- [ ] Log HTTP response status codes
- [ ] Update sender record on success
- [ ] Add user-agent header for requests
- [ ] Track unsubscribe method success rates

**Dependencies:** #12, #13

---

### Issue #19: Agent Runner Orchestrator
**Priority:** P0-Critical
**Type:** feature
**Complexity:** XL

**Description:**
Create main agent orchestrator that coordinates the entire cleanup workflow from start to finish.

**Acceptance Criteria:**
- [ ] Create `backend/agent/runner.py` with `AgentRunner` class
- [ ] Implement `start_cleanup_run()` method
- [ ] Workflow: Create run → Discover senders → Process each sender → Complete run
- [ ] For each sender: Safety check → Unsubscribe → Create filter → Delete emails → Log action
- [ ] Update run progress in real-time (database + WebSocket optional)
- [ ] Handle pause/resume functionality
- [ ] Implement error recovery (continue on sender failures)
- [ ] Track overall stats (senders processed, emails deleted, bytes freed)
- [ ] Mark run as completed/failed with appropriate status
- [ ] Add configurable aggressiveness settings (days threshold, batch size)

**Dependencies:** #13, #14, #15, #16, #17, #18

---

### Issue #20: Background Task Scheduling with APScheduler
**Priority:** P1-High
**Type:** infrastructure
**Complexity:** M

**Description:**
Set up APScheduler for running cleanup runs in the background without blocking API requests.

**Acceptance Criteria:**
- [ ] Install and configure APScheduler in FastAPI app
- [ ] Create background job for agent runner
- [ ] Implement job queue management (one run at a time)
- [ ] Add job status tracking in database
- [ ] Implement graceful shutdown of background jobs
- [ ] Add job progress callbacks
- [ ] Handle job failures and retries
- [ ] Create API endpoints to start/stop/monitor jobs
- [ ] Store job logs for debugging

**Dependencies:** #19

---

## Milestone 6: Backend API Endpoints

### Issue #21: Cleanup Runs API Endpoints
**Priority:** P1-High
**Type:** feature
**Complexity:** M

**Description:**
Create REST API endpoints for managing cleanup runs (create, get, pause, resume, list).

**Acceptance Criteria:**
- [ ] `POST /runs` - Start a new cleanup run (triggers background job)
- [ ] `GET /runs/{id}` - Get run details and stats
- [ ] `POST /runs/{id}/pause` - Pause a running cleanup
- [ ] `POST /runs/{id}/resume` - Resume a paused cleanup
- [ ] `GET /runs` - List all runs with pagination
- [ ] `DELETE /runs/{id}` - Cancel a run
- [ ] Add request/response Pydantic models
- [ ] Add error handling (run not found, invalid state transitions)
- [ ] Add OpenAPI documentation
- [ ] Write integration tests

**Dependencies:** #19, #20

---

### Issue #22: Senders API Endpoints
**Priority:** P1-High
**Type:** feature
**Complexity:** S

**Description:**
Create REST API endpoints for viewing and managing discovered senders.

**Acceptance Criteria:**
- [ ] `GET /senders` - List all senders with pagination and filters
- [ ] `GET /senders/{id}` - Get sender details
- [ ] `GET /senders/stats` - Get sender statistics (total, unsubscribed, filtered)
- [ ] Add query parameters: `?domain=`, `?unsubscribed=`, `?has_filter=`
- [ ] Sort by message count (descending)
- [ ] Add Pydantic models for responses
- [ ] Return sender action history
- [ ] Add OpenAPI documentation

**Dependencies:** #7

---

### Issue #23: Cleanup Actions API Endpoints
**Priority:** P2-Medium
**Type:** feature
**Complexity:** S

**Description:**
Create API endpoints for viewing cleanup action history and logs.

**Acceptance Criteria:**
- [ ] `GET /runs/{id}/actions` - List all actions for a specific run
- [ ] `GET /actions` - List all actions with pagination
- [ ] Add filtering by `action_type`, `sender_email`, date range
- [ ] Sort by timestamp (descending)
- [ ] Include stats: total emails deleted, bytes freed
- [ ] Add Pydantic response models
- [ ] Add OpenAPI documentation

**Dependencies:** #8, #21

---

### Issue #24: Statistics and Dashboard API
**Priority:** P1-High
**Type:** feature
**Complexity:** M

**Description:**
Create API endpoint for dashboard statistics and current system state.

**Acceptance Criteria:**
- [ ] `GET /stats/current` - Get current system statistics
- [ ] Return: Total runs, active run, total senders discovered
- [ ] Return: Total emails deleted, total bytes freed (all-time)
- [ ] Return: Unsubscribe success rate, filter count
- [ ] Return: Gmail account info (email address, storage quota)
- [ ] Add caching for expensive aggregations (5 min TTL)
- [ ] Add Pydantic response model
- [ ] Add OpenAPI documentation

**Dependencies:** #6, #7, #8

---

### Issue #25: Whitelist Management API
**Priority:** P2-Medium
**Type:** feature
**Complexity:** S

**Description:**
Create API endpoints for managing whitelisted domains that should never be processed.

**Acceptance Criteria:**
- [ ] `GET /whitelist` - List all whitelisted domains
- [ ] `POST /whitelist` - Add a domain to whitelist
- [ ] `DELETE /whitelist/{domain}` - Remove domain from whitelist
- [ ] Validate domain format before adding
- [ ] Prevent duplicate entries
- [ ] Add `reason` field for documentation
- [ ] Add Pydantic models
- [ ] Add OpenAPI documentation

**Dependencies:** #8

---

## Milestone 7: Frontend Dashboard

### Issue #26: Dashboard Layout and Navigation
**Priority:** P1-High
**Type:** feature
**Complexity:** M

**Description:**
Create main dashboard layout with navigation, header, and routing structure.

**Acceptance Criteria:**
- [ ] Create `/app/dashboard` route with layout
- [ ] Add navigation sidebar/header with links: Home, Runs, Senders, Settings
- [ ] Implement responsive design (mobile, tablet, desktop)
- [ ] Add user account info display (Gmail address)
- [ ] Add "Disconnect" button
- [ ] Add route protection (redirect if not authenticated)
- [ ] Use shadcn/ui components for consistent UI
- [ ] Add loading states during navigation

**Dependencies:** #11

---

### Issue #27: Cleanup Run Control Panel
**Priority:** P1-High
**Type:** feature
**Complexity:** L

**Description:**
Create main control panel for starting, monitoring, and controlling cleanup runs.

**Acceptance Criteria:**
- [ ] Create "Start Cleanup" button (calls `POST /runs`)
- [ ] Show current run status badge (Running, Paused, Completed)
- [ ] Display real-time progress bar (percentage complete)
- [ ] Show live stats: Senders processed, Emails deleted, Storage freed
- [ ] Add Pause/Resume buttons (enabled when run is active)
- [ ] Add Cancel button with confirmation dialog
- [ ] Implement auto-refresh (poll API every 2 seconds when run is active)
- [ ] Show estimated time remaining
- [ ] Display error messages if run fails

**Dependencies:** #21, #24, #26

---

### Issue #28: Live Activity Feed Component
**Priority:** P2-Medium
**Type:** feature
**Complexity:** M

**Description:**
Create live activity feed showing recent cleanup actions in real-time.

**Acceptance Criteria:**
- [ ] Create scrollable activity feed component
- [ ] Display recent actions: "Unsubscribed from X", "Created filter for Y", "Deleted N emails from Z"
- [ ] Show timestamp for each action
- [ ] Use different icons/colors for action types
- [ ] Auto-update feed during active runs (polling)
- [ ] Limit to most recent 50 actions
- [ ] Add "View All Actions" link to detailed page
- [ ] Use shadcn/ui Card and Badge components

**Dependencies:** #23, #26

---

### Issue #29: Statistics Dashboard Cards
**Priority:** P1-High
**Type:** feature
**Complexity:** M

**Description:**
Create dashboard stat cards showing key metrics and totals.

**Acceptance Criteria:**
- [ ] Create stat card component (reusable)
- [ ] Display cards: Total Senders Found, Total Unsubscribed, Emails Deleted, Storage Freed
- [ ] Show change indicators (up/down arrows, percentages)
- [ ] Format bytes in human-readable units (GB, MB)
- [ ] Add loading skeletons while data loads
- [ ] Use shadcn/ui Card component
- [ ] Make numbers animate on update (optional)
- [ ] Responsive grid layout (2x2 on desktop, 1 column on mobile)

**Dependencies:** #24, #26

---

### Issue #30: Senders List Page
**Priority:** P2-Medium
**Type:** feature
**Complexity:** L

**Description:**
Create page to view and search discovered senders with details and actions.

**Acceptance Criteria:**
- [ ] Create `/app/dashboard/senders` route
- [ ] Display senders in a table/list with columns: Email, Domain, Message Count, Unsubscribed, Filter Created
- [ ] Add search/filter by domain or email
- [ ] Add sorting by message count, date
- [ ] Implement pagination (20 per page)
- [ ] Show "Unsubscribed" badge if unsubscribed
- [ ] Show "Filtered" badge if filter created
- [ ] Add action buttons: View Details, Manual Unsubscribe (future)
- [ ] Use shadcn/ui Table or Data Table component

**Dependencies:** #22, #26

---

### Issue #31: Run History Page
**Priority:** P2-Medium
**Type:** feature
**Complexity:** M

**Description:**
Create page to view past cleanup run history with details.

**Acceptance Criteria:**
- [ ] Create `/app/dashboard/runs` route
- [ ] Display runs in a list/table with columns: Started, Duration, Status, Senders, Emails Deleted, Storage Freed
- [ ] Add status badges (Completed, Failed, Running)
- [ ] Add "View Details" link for each run
- [ ] Create run details page showing full stats and actions
- [ ] Implement pagination
- [ ] Sort by date (most recent first)
- [ ] Use shadcn/ui Table component

**Dependencies:** #21, #23, #26

---

### Issue #32: Settings Page with Configuration
**Priority:** P2-Medium
**Type:** feature
**Complexity:** M

**Description:**
Create settings page for configuring cleanup behavior and managing whitelist.

**Acceptance Criteria:**
- [ ] Create `/app/dashboard/settings` route
- [ ] Add setting: "Delete emails older than N days" (slider, default 30)
- [ ] Add setting: "Aggressiveness level" (Conservative/Balanced/Aggressive)
- [ ] Add whitelist management section with add/remove domain functionality
- [ ] Display current whitelisted domains in a list
- [ ] Add safety keywords configuration (optional)
- [ ] Add "Test Mode" toggle (simulate without actual deletion)
- [ ] Save settings to localStorage or backend
- [ ] Show save confirmation

**Dependencies:** #25, #26

---

### Issue #33: Error Handling and Toast Notifications
**Priority:** P1-High
**Type:** feature
**Complexity:** S

**Description:**
Implement global error handling and toast notifications for user feedback.

**Acceptance Criteria:**
- [ ] Install and configure toast library (shadcn/ui Sonner or react-hot-toast)
- [ ] Create toast notification wrapper
- [ ] Show success toasts: "Cleanup started", "Run completed", "Settings saved"
- [ ] Show error toasts: API failures, authentication errors
- [ ] Add global error boundary component
- [ ] Handle network errors gracefully
- [ ] Add retry mechanisms for failed API calls
- [ ] Show loading toasts for long operations

**Dependencies:** #3

---

## Milestone 8: Advanced Features & Optimization

### Issue #34: Large Attachment Detection and Cleanup
**Priority:** P2-Medium
**Type:** enhancement
**Complexity:** M

**Description:**
Implement detection and cleanup of large emails (attachments) to maximize storage savings.

**Acceptance Criteria:**
- [ ] Add Gmail query: `larger:5M older_than:1y`
- [ ] Fetch messages with large attachments
- [ ] Display in separate dashboard section: "Large Attachments"
- [ ] Show: Sender, Subject, Size, Date
- [ ] Allow selective deletion (checkbox selection)
- [ ] Track bytes freed from large email cleanup
- [ ] Add safety checks (skip important senders)
- [ ] Update statistics to include attachment cleanup

**Dependencies:** #15, #16

---

### Issue #35: AI-Powered Email Classification (Optional)
**Priority:** P3-Low
**Type:** enhancement
**Complexity:** L

**Description:**
Integrate OpenAI GPT-4 for intelligent email classification and action recommendations.

**Acceptance Criteria:**
- [ ] Create OpenAI client wrapper in `backend/agent/classifier.py`
- [ ] Implement `classify_email(subject, sender, snippet)` function
- [ ] Classifications: newsletter, promo, transactional, financial, personal, unknown
- [ ] Return confidence score with classification
- [ ] Add classification results to sender model (optional field)
- [ ] Use classification to inform deletion decisions
- [ ] Add classification to action logs
- [ ] Handle API rate limits and errors
- [ ] Make feature toggle-able (enable/disable in settings)
- [ ] Track OpenAI API costs

**Dependencies:** #13, #16

---

### Issue #36: Export Reports and Analytics
**Priority:** P3-Low
**Type:** enhancement
**Complexity:** M

**Description:**
Add ability to export cleanup reports and analytics as CSV or PDF.

**Acceptance Criteria:**
- [ ] Implement `GET /runs/{id}/export` endpoint (CSV format)
- [ ] Export includes: All senders processed, actions taken, emails deleted, bytes freed
- [ ] Add frontend "Export Report" button on run details page
- [ ] Generate downloadable CSV file
- [ ] Include summary section with total stats
- [ ] Add date range filtering for exports
- [ ] Create formatted report view (printable HTML)
- [ ] Optional: PDF export using library like ReportLab

**Dependencies:** #21, #23

---

### Issue #37: WebSocket Real-Time Updates
**Priority:** P3-Low
**Type:** enhancement
**Complexity:** L

**Description:**
Replace polling with WebSocket connections for real-time dashboard updates.

**Acceptance Criteria:**
- [ ] Add WebSocket support to FastAPI backend
- [ ] Create WebSocket endpoint: `ws://localhost:8000/ws`
- [ ] Broadcast run progress updates to connected clients
- [ ] Broadcast action events in real-time
- [ ] Update frontend to use WebSocket instead of polling
- [ ] Handle connection drops and reconnection
- [ ] Add connection status indicator in UI
- [ ] Fallback to polling if WebSocket unavailable
- [ ] Optimize message frequency (batch updates)

**Dependencies:** #19, #27, #28

---

### Issue #38: Batch Unsubscribe Preview Mode
**Priority:** P2-Medium
**Type:** enhancement
**Complexity:** M

**Description:**
Add preview/dry-run mode to show what would happen without executing actions.

**Acceptance Criteria:**
- [ ] Add `preview_mode` parameter to cleanup run creation
- [ ] In preview mode: Scan senders, simulate unsubscribe, NO actual deletion
- [ ] Generate preview report: Senders that would be processed, estimated emails deleted, bytes freed
- [ ] Display preview results in UI before starting actual run
- [ ] Add "Start for Real" button after preview
- [ ] Save preview results to database
- [ ] Add preview badge to differentiate from real runs
- [ ] Show comparison: Preview vs. Actual results

**Dependencies:** #19, #21

---

## Milestone 9: Testing & Quality Assurance

### Issue #39: Backend Unit Tests
**Priority:** P1-High
**Type:** infrastructure
**Complexity:** L

**Description:**
Write comprehensive unit tests for backend core functionality.

**Acceptance Criteria:**
- [ ] Set up pytest with pytest-asyncio
- [ ] Write tests for database models (CRUD operations)
- [ ] Write tests for Gmail client methods (mocked API)
- [ ] Write tests for safety guardrails (all scenarios)
- [ ] Write tests for unsubscribe handlers
- [ ] Write tests for OAuth flow
- [ ] Mock external dependencies (Gmail API, OpenAI)
- [ ] Achieve >80% code coverage
- [ ] Add fixtures for test data
- [ ] Configure CI to run tests automatically

**Dependencies:** #2, #4, #5, #6, #7, #8, #12, #16, #17, #18

---

### Issue #40: API Integration Tests
**Priority:** P2-Medium
**Type:** infrastructure
**Complexity:** M

**Description:**
Write integration tests for API endpoints using TestClient.

**Acceptance Criteria:**
- [ ] Set up FastAPI TestClient with test database
- [ ] Write tests for all `/runs` endpoints
- [ ] Write tests for all `/senders` endpoints
- [ ] Write tests for OAuth endpoints (mocked)
- [ ] Write tests for statistics endpoints
- [ ] Write tests for whitelist endpoints
- [ ] Test error cases (404, 400, 500)
- [ ] Test authentication/authorization
- [ ] Clean up test database after each test
- [ ] Document test setup instructions

**Dependencies:** #21, #22, #23, #24, #25

---

### Issue #41: Frontend Component Tests
**Priority:** P3-Low
**Type:** infrastructure
**Complexity:** M

**Description:**
Write tests for critical frontend components using Jest and React Testing Library.

**Acceptance Criteria:**
- [ ] Set up Jest and React Testing Library
- [ ] Write tests for dashboard control panel
- [ ] Write tests for stat cards
- [ ] Write tests for activity feed
- [ ] Write tests for senders list with mocked API
- [ ] Test user interactions (button clicks, form submissions)
- [ ] Test loading and error states
- [ ] Mock API calls using MSW (Mock Service Worker)
- [ ] Achieve >70% coverage for components

**Dependencies:** #27, #28, #29, #30

---

### Issue #42: End-to-End Testing Setup
**Priority:** P3-Low
**Type:** infrastructure
**Complexity:** L

**Description:**
Set up end-to-end tests for critical user flows using Playwright or Cypress.

**Acceptance Criteria:**
- [ ] Install and configure Playwright
- [ ] Write E2E test: OAuth flow (mocked)
- [ ] Write E2E test: Start cleanup run and monitor progress
- [ ] Write E2E test: View senders list and details
- [ ] Write E2E test: Manage whitelist
- [ ] Write E2E test: View run history
- [ ] Set up test Gmail account (sandboxed)
- [ ] Configure CI to run E2E tests
- [ ] Add screenshots on test failures

**Dependencies:** #11, #27, #30, #31, #32

---

## Milestone 10: Documentation & Deployment

### Issue #43: API Documentation with OpenAPI/Swagger
**Priority:** P2-Medium
**Type:** infrastructure
**Complexity:** S

**Description:**
Enhance API documentation using FastAPI's built-in OpenAPI/Swagger UI.

**Acceptance Criteria:**
- [ ] Add docstrings to all API endpoints
- [ ] Add request/response examples
- [ ] Add parameter descriptions
- [ ] Add error response documentation
- [ ] Group endpoints by tags (Runs, Senders, Auth, etc.)
- [ ] Add API version information
- [ ] Verify Swagger UI accessible at `/docs`
- [ ] Generate OpenAPI JSON schema at `/openapi.json`

**Dependencies:** #21, #22, #23, #24, #25

---

### Issue #44: User Documentation and Setup Guide
**Priority:** P1-High
**Type:** infrastructure
**Complexity:** M

**Description:**
Create comprehensive user documentation for setup, usage, and troubleshooting.

**Acceptance Criteria:**
- [ ] Write `README.md` with project overview
- [ ] Create `docs/SETUP.md` with step-by-step installation
- [ ] Create `docs/OAUTH_SETUP.md` for Google Cloud setup
- [ ] Create `docs/USAGE.md` with feature walkthrough
- [ ] Create `docs/TROUBLESHOOTING.md` for common issues
- [ ] Add architecture diagram
- [ ] Add screenshots of UI
- [ ] Document environment variables
- [ ] Add FAQ section
- [ ] Include safety information and disclaimers

**Dependencies:** None (can be done anytime)

---

### Issue #45: Local Development Setup Scripts
**Priority:** P2-Medium
**Type:** infrastructure
**Complexity:** S

**Description:**
Create setup scripts to streamline local development environment setup.

**Acceptance Criteria:**
- [ ] Create `setup.sh` script for initial setup (install deps, create DB)
- [ ] Create `start_backend.sh` to start FastAPI server
- [ ] Create `start_frontend.sh` to start Next.js dev server
- [ ] Create `start_all.sh` to start both servers
- [ ] Add database initialization script
- [ ] Add seed data script (optional whitelist entries)
- [ ] Document script usage in README
- [ ] Make scripts cross-platform compatible (bash + PowerShell versions)

**Dependencies:** #1, #2, #3

---

### Issue #46: Error Logging and Monitoring
**Priority:** P2-Medium
**Type:** infrastructure
**Complexity:** M

**Description:**
Implement structured logging and error tracking for debugging and monitoring.

**Acceptance Criteria:**
- [ ] Configure Python logging with rotation (using `logging` module)
- [ ] Add structured logging for all agent operations
- [ ] Log API requests and responses (with sensitive data redaction)
- [ ] Create log files in `backend/logs/` directory
- [ ] Add log levels: DEBUG, INFO, WARNING, ERROR
- [ ] Implement log rotation (max 10MB per file, keep 5 files)
- [ ] Add request ID tracking for distributed tracing
- [ ] Create logging configuration file
- [ ] Optional: Integrate with Sentry for error tracking

**Dependencies:** #2

---

### Issue #47: Security Hardening and Best Practices
**Priority:** P1-High
**Type:** infrastructure
**Complexity:** M

**Description:**
Implement security best practices for OAuth tokens, API endpoints, and data storage.

**Acceptance Criteria:**
- [ ] Encrypt sensitive data at rest (OAuth tokens in SQLite)
- [ ] Add rate limiting to API endpoints (using slowapi)
- [ ] Implement CORS properly (strict origin checking)
- [ ] Add input validation to all endpoints (Pydantic)
- [ ] Sanitize user inputs to prevent injection attacks
- [ ] Add HTTPS requirement for production
- [ ] Store secrets in environment variables only
- [ ] Add security headers (CSP, X-Frame-Options)
- [ ] Document security considerations in README
- [ ] Add dependency vulnerability scanning (safety, pip-audit)

**Dependencies:** #2, #10

---

### Issue #48: Performance Optimization and Caching
**Priority:** P3-Low
**Type:** enhancement
**Complexity:** M

**Description:**
Optimize application performance with caching, query optimization, and batch processing.

**Acceptance Criteria:**
- [ ] Add Redis or in-memory caching for statistics (optional)
- [ ] Optimize database queries (add indexes, use eager loading)
- [ ] Implement query result caching (TTL-based)
- [ ] Optimize Gmail API calls (batch requests when possible)
- [ ] Add database connection pooling
- [ ] Implement lazy loading for frontend lists
- [ ] Add pagination to all list endpoints
- [ ] Profile slow endpoints and optimize
- [ ] Add performance monitoring metrics

**Dependencies:** #4, #12, #22, #24

---

## Summary

**Total Issues:** 48

**By Priority:**
- P0-Critical: 10 issues
- P1-High: 16 issues
- P2-Medium: 15 issues
- P3-Low: 7 issues

**By Type:**
- infrastructure: 14 issues
- feature: 28 issues
- enhancement: 6 issues

**By Complexity:**
- S (Small): 10 issues
- M (Medium): 23 issues
- L (Large): 11 issues
- XL (Extra Large): 4 issues

**Recommended Development Order:**

1. **Phase 1 (Weeks 1-2):** Issues #1-11 - Project setup, database, OAuth
2. **Phase 2 (Weeks 3-4):** Issues #12-20 - Gmail integration, agent core
3. **Phase 3 (Weeks 5-6):** Issues #21-25 - API endpoints
4. **Phase 4 (Weeks 7-8):** Issues #26-33 - Frontend dashboard
5. **Phase 5 (Weeks 9-10):** Issues #34-38 - Advanced features
6. **Phase 6 (Weeks 11-12):** Issues #39-48 - Testing, docs, deployment

---

*This issue structure provides a complete roadmap for building the Inbox Nuke Agent from scratch. Start with P0-Critical issues and work through dependencies. Good luck!*
