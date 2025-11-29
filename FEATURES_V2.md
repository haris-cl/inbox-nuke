# InboxNuke V2 - Feature List

## Short Description

InboxNuke V2 is a guided, wizard-style email cleanup tool that helps users achieve inbox peace of mind in 5 minutes. It replaces the current complex dashboard with a simple, trust-first flow: Scan → Review → Clean. The app runs 100% locally, uses AI to classify emails intelligently, and never permanently deletes anything—everything goes to Trash with a 30-day recovery window. Users get a clean inbox without the anxiety of losing important messages.

---

## Core Wizard Flow

These features form the main cleanup wizard that guides users from scanning through completion.

---

### F1 – Inbox Scanning with Live Progress

**Type:** Core Wizard

**User Story:** As a user, I want to see real-time progress while my inbox is being scanned so that I know the app is working and stay engaged during the wait.

**Brief Description:**
When the user clicks "Start Cleanup" from the Dashboard, they enter a full-screen scanning state. The app analyzes their Gmail inbox (up to 10,000 emails) and displays live progress with a percentage bar, email count, and animated discoveries (e.g., "Found 3,200 promotional emails"). Transparency messages explain what's happening ("Checking which senders you reply to...").

**Acceptance Criteria:**
- [ ] Full-screen scanning view replaces the current Score page during scan
- [ ] Progress bar shows percentage complete and "X emails scanned"
- [ ] Live discoveries animate in as scan finds promotions, newsletters, large attachments
- [ ] Transparency text updates to show current scan activity
- [ ] User cannot navigate away during scan (no back button, locked state)
- [ ] Scan completes in 1-3 minutes for typical inbox sizes

**Dependencies:** None

**Priority:** Must Have

---

### F2 – Inbox Health Report

**Type:** Core Wizard

**User Story:** As a user, I want to see a summary of what the scan found so that I can understand what will be cleaned before taking action.

**Brief Description:**
After the scan completes, users see a full-screen report with a clear headline ("We found 4,200 emails to clean up"), a visual breakdown by category (promotions, newsletters, social), potential space savings, and a "What's Protected" reassurance section. This builds confidence before the cleanup begins.

**Acceptance Criteria:**
- [ ] Headline shows total cleanable emails and potential GB savings
- [ ] Visual chart (pie or bar) breaks down emails by category
- [ ] "What's Protected" section lists protected email types (contacts, replies, financial)
- [ ] Two clear buttons: "Quick Clean" (primary) and "Review All" (secondary)
- [ ] Report appears automatically after scan completes

**Dependencies:** F1

**Priority:** Must Have

---

### F3 – Cleanup Mode Selection

**Type:** Core Wizard

**User Story:** As a user, I want to choose whether to review all emails or let AI handle most decisions so that I can balance speed with control.

**Brief Description:**
Users choose between two cleanup modes: "Quick Clean" (AI handles 95% of decisions, user reviews only ~50 uncertain emails) or "Review All" (user sees every email before deletion). Most users will choose Quick Clean for speed. The selection determines which emails appear in the review queue.

**Acceptance Criteria:**
- [ ] Two distinct buttons with clear descriptions
- [ ] Quick Clean shows estimated review count (e.g., "Review only 50 uncertain emails")
- [ ] Review All shows total email count (e.g., "Review all 4,200 emails")
- [ ] Quick Clean is visually emphasized as the recommended option
- [ ] Selection saves user preference for future cleanups

**Dependencies:** F2

**Priority:** Must Have

---

### F4 – Review Queue (One-at-a-Time)

**Type:** Core Wizard

**User Story:** As a user, I want to review uncertain emails one at a time with clear Keep/Delete buttons so that I can make decisions quickly without feeling overwhelmed.

**Brief Description:**
Users see emails in a card-based, one-at-a-time view. Each card shows the sender, subject, AI suggestion with reasoning, and large Keep/Delete buttons. A progress indicator shows "12 of 50" remaining. A "Skip All & Trust AI" button lets users exit early if they trust the AI's remaining suggestions.

**Acceptance Criteria:**
- [ ] Only one email card visible at a time
- [ ] Card shows sender, subject, AI classification, and reasoning
- [ ] Large, touch-friendly Keep and Delete buttons
- [ ] Progress indicator shows "X of Y" with visual progress bar
- [ ] "Skip All & Trust AI" button available at top of screen
- [ ] Keyboard shortcuts work (K for Keep, D for Delete, S for Skip)
- [ ] Mobile swipe gestures work (swipe right = Keep, left = Delete)
- [ ] Review queue only shows UNCERTAIN emails in Quick Clean mode
- [ ] Review queue shows all emails in Review All mode

**Dependencies:** F3

**Priority:** Must Have

---

### F5 – Cleanup Confirmation Screen

**Type:** Core Wizard

**User Story:** As a user, I want to see a final summary of what will happen before cleanup executes so that I can confirm I'm comfortable with the changes.

**Brief Description:**
Before any emails are deleted, users see a confirmation screen with clear numbers (emails to delete, senders to unsubscribe, space to free), a safety reminder that emails go to Trash (30-day recovery), and a prominent "Confirm Cleanup" button. This reduces anxiety and prevents accidental deletions.

**Acceptance Criteria:**
- [ ] Summary shows total emails to delete, senders to unsubscribe, and estimated space freed
- [ ] Safety reminder explains emails go to Trash, not permanent deletion
- [ ] Safety reminder states 30-day recovery window
- [ ] "Confirm Cleanup" button is primary action
- [ ] "Go Back" link returns to review queue
- [ ] User cannot bypass this screen (no auto-confirm)

**Dependencies:** F4

**Priority:** Must Have

---

### F6 – Cleanup Execution with Progress

**Type:** Core Wizard

**User Story:** As a user, I want to see real-time progress while emails are being cleaned so that I know the cleanup is working.

**Brief Description:**
After confirmation, the app executes the cleanup with a progress indicator showing emails deleted, senders unsubscribed, and space freed. The user watches the counters animate upward. This takes 1-3 minutes depending on volume.

**Acceptance Criteria:**
- [ ] Progress screen shows "X of Y emails cleaned" with percentage
- [ ] Counters animate for emails deleted, space freed, senders unsubscribed
- [ ] User cannot cancel during execution (prevents partial cleanup)
- [ ] Errors are logged but don't stop the entire cleanup
- [ ] Final counts reflect actual actions taken (not estimates)

**Dependencies:** F5

**Priority:** Must Have

---

### F7 – Success Screen with Next Steps

**Type:** Core Wizard

**User Story:** As a user, I want to see a celebration of my cleanup results and suggestions for next steps so that I feel accomplished and encouraged to return.

**Brief Description:**
After cleanup completes, users see a success screen with a checkmark animation, final results (emails cleaned, space freed, senders unsubscribed), and optional next steps like enabling auto-cleanup or protecting specific senders. The primary button returns them to the Dashboard.

**Acceptance Criteria:**
- [ ] Celebration animation or checkmark appears
- [ ] Results show exact counts (emails cleaned, GB freed, senders unsubscribed)
- [ ] "Back to Dashboard" button is primary action
- [ ] Optional: "Set up monthly auto-cleanup" toggle or link
- [ ] Optional: "Protect specific senders" link goes to Settings
- [ ] Success screen stays visible until user clicks Back to Dashboard

**Dependencies:** F6

**Priority:** Must Have

---

## Supporting Screens

These features support the main wizard flow but are standalone pages accessible from navigation.

---

### F8 – Dashboard with Inbox Health Card

**Type:** Supporting

**User Story:** As a user, I want to see my inbox health status at a glance so that I know when it's time to run a cleanup.

**Brief Description:**
The Dashboard is the main hub after login. It shows an "Inbox Health Card" with status (Healthy/Needs Attention), estimated cleanable emails, potential space savings, and a single "Start Cleanup" button. Quick stats show lifetime totals. Quick actions link to secondary tools like Space Manager and Settings.

**Acceptance Criteria:**
- [ ] Inbox Health Card is the most prominent element
- [ ] Status indicator uses color coding (green = healthy, yellow/red = needs attention)
- [ ] Shows estimated cleanable emails and potential space savings
- [ ] "Start Cleanup" button launches the wizard (F1)
- [ ] Quick stats show lifetime totals: emails cleaned, space freed, senders muted, last cleanup date
- [ ] Quick actions section links to Free Up Space, Settings, History
- [ ] Recent activity feed is collapsible and shows last 5 cleanup actions

**Dependencies:** None

**Priority:** Must Have

---

### F9 – Free Up Space (Large Attachments Manager)

**Type:** Supporting

**User Story:** As a user, I want to find and delete large emails to free up storage space so that I don't have to upgrade my Gmail plan.

**Brief Description:**
The Free Up Space page (renamed from Attachments) shows emails sorted by size with filters for minimum size and age. Users select emails via checkboxes and see a running total of selected size. The "Delete Selected" button removes them after confirmation. This addresses the "storage full" emergency use case.

**Acceptance Criteria:**
- [ ] Header shows user's current storage usage ("14.2 GB of 15 GB")
- [ ] Filters for minimum size (MB dropdown) and older than (days/months/years dropdown)
- [ ] Email list shows sender, subject, size, and date
- [ ] Checkboxes for individual selection
- [ ] Select All / Deselect All buttons
- [ ] Running total shows "X emails selected = Y GB"
- [ ] Delete Selected button requires confirmation before deletion
- [ ] List updates after deletion to remove deleted emails

**Dependencies:** None

**Priority:** Must Have

---

### F10 – Protected Senders Settings

**Type:** Supporting

**User Story:** As a user, I want to protect specific senders from ever being cleaned so that I never lose emails from important people or organizations.

**Brief Description:**
The Protected Senders page (formerly Whitelist in Settings) lets users add email addresses or domains that will never be deleted or filtered. It also shows an "Auto-Protected" section explaining what the system automatically protects (contacts, replied-to senders, financial/government domains).

**Acceptance Criteria:**
- [ ] Add form accepts email addresses or domains (e.g., "boss@company.com" or "@company.com")
- [ ] List shows all protected senders with added date and Remove button
- [ ] "Auto-Protected" section lists system protections (contacts, replies, financial, government)
- [ ] Auto-Protected section is read-only (user cannot remove system protections)
- [ ] Removing a sender requires confirmation
- [ ] Changes take effect immediately for future cleanups

**Dependencies:** None

**Priority:** Must Have

---

### F11 – Cleanup History

**Type:** Supporting

**User Story:** As a user, I want to see a history of my past cleanups so that I can track my progress and review what was deleted.

**Brief Description:**
The History page lists all completed cleanups with date, emails cleaned, space freed, and a "View Details" link. At the bottom, lifetime stats show total emails cleaned and total space freed across all cleanups. This replaces the current technically-focused run history.

**Acceptance Criteria:**
- [ ] List shows completed cleanups in reverse chronological order (newest first)
- [ ] Each cleanup shows date, email count, space freed, and status
- [ ] "View Details" link expands to show action log (what was deleted, unsubscribed, filtered)
- [ ] Lifetime stats section at bottom shows totals across all cleanups
- [ ] Filter to show only completed cleanups (hide failed/cancelled runs)
- [ ] Pagination for users with many cleanups (10-20 per page)

**Dependencies:** None

**Priority:** Must Have

---

### F12 – Gmail Connection Management

**Type:** Supporting

**User Story:** As a user, I want to see my Gmail connection status and disconnect if needed so that I can control app access to my account.

**Brief Description:**
The Settings page includes a Gmail Connection section showing the connected email address and a "Disconnect" button. Disconnecting removes stored credentials and logs the user out. This is merged into the main Settings page alongside Protected Senders.

**Acceptance Criteria:**
- [ ] Shows connected Gmail account email address
- [ ] Shows connection status (Connected / Not Connected)
- [ ] "Disconnect" button requires confirmation before disconnecting
- [ ] Disconnecting deletes encrypted OAuth tokens from database
- [ ] After disconnect, user is redirected to home page
- [ ] Reconnecting initiates a new OAuth flow

**Dependencies:** None

**Priority:** Must Have

---

### F13 – Trust-First Home Page

**Type:** Supporting

**User Story:** As a new user, I want to understand what the app does and feel safe connecting my Gmail so that I'm confident giving it access.

**Brief Description:**
The home page (unauthenticated) shows a clear value proposition ("Inbox peace of mind in 5 minutes"), a "100% Local" trust badge in the header, trust signals (emails never leave computer, 30-day undo, open source), and a simple 3-step "How it works" section. The only call-to-action is "Connect Gmail."

**Acceptance Criteria:**
- [ ] Headline emphasizes value ("Inbox peace of mind") not branding ("INBOX NUKE")
- [ ] "100% Local" badge is prominently displayed in header
- [ ] Trust signals section explains privacy (local processing, reversible, open source)
- [ ] "How it works" shows 3 simple steps with icons (Connect → Scan → Clean)
- [ ] Single "Connect Gmail" button is the primary action
- [ ] "Go to Dashboard" button appears if user is already connected
- [ ] Tech stack badge removed (developer-focused, not user-focused)

**Dependencies:** None

**Priority:** Must Have

---

## Technical/Infrastructure Features

These features enable the wizard to work but are not directly visible to users.

---

### F14 – Inbox Health API Endpoint

**Type:** Technical

**User Story:** As a developer, I need an API endpoint that returns inbox health status so that the Dashboard can display it without running a full scan.

**Brief Description:**
A new `/api/inbox-health` endpoint analyzes the user's Gmail inbox using category queries (promotions, social, updates) and returns estimated cleanable emails, space savings, and health status (Healthy/Needs Attention). This is faster than a full scan and updates the Dashboard in real-time.

**Acceptance Criteria:**
- [ ] Endpoint returns JSON with: status, estimated_cleanable_emails, estimated_space_savings_gb
- [ ] Uses Gmail API category queries (category:promotions, category:social, etc.)
- [ ] Caches result for 1 hour to avoid repeated API calls
- [ ] Returns in under 5 seconds for typical inboxes
- [ ] Handles OAuth errors gracefully (returns 401 if token expired)

**Dependencies:** None

**Priority:** Must Have

---

### F15 – Category Breakdown in Scan Results

**Type:** Technical

**User Story:** As a developer, I need the scoring endpoint to return email categories so that the Inbox Report can show a breakdown (promotions, newsletters, social).

**Brief Description:**
The `/api/scoring/stats` endpoint is modified to include a category breakdown field that classifies emails into promotions, newsletters, social notifications, and other. This enables the visual chart in the Inbox Report (F2).

**Acceptance Criteria:**
- [ ] Response includes `category_breakdown` field with counts for each category
- [ ] Categories: promotions, newsletters, social, other
- [ ] Uses Gmail API category labels and List-Unsubscribe headers to classify
- [ ] Breakdown totals match overall email counts
- [ ] Backend stores category in database for each scored email

**Dependencies:** F1

**Priority:** Must Have

---

### F16 – Auto-Protected Senders Endpoint

**Type:** Technical

**User Story:** As a developer, I need an endpoint that returns automatically protected sender types so that the Protected Senders page can display them.

**Brief Description:**
A new `/api/auto-protected` endpoint returns a list of auto-protected sender categories (contacts, replied-to, financial, government) with descriptions. This populates the "Auto-Protected" section in Settings (F10).

**Acceptance Criteria:**
- [ ] Endpoint returns JSON array with category name and description
- [ ] Categories include: "Google Contacts", "Senders you've replied to", "Financial institutions", "Government domains"
- [ ] Each category includes a human-readable description
- [ ] No authentication required (static data)
- [ ] Frontend caches response to avoid repeated calls

**Dependencies:** None

**Priority:** Nice to Have

---

### F17 – Cleanup Mode Preference Storage

**Type:** Technical

**User Story:** As a developer, I need to store the user's cleanup mode preference so that returning users default to their last choice (Quick Clean vs Review All).

**Brief Description:**
The database stores a `cleanup_mode_preference` field in the user's settings (or cleanup_runs table). When the user selects Quick Clean or Review All (F3), it's saved. On return visits, the Inbox Report defaults to their last choice.

**Acceptance Criteria:**
- [ ] New field `cleanup_mode_preference` in settings or user table
- [ ] Accepts values: "quick_clean", "review_all"
- [ ] Defaults to "quick_clean" for first-time users
- [ ] Updates when user makes a selection in F3
- [ ] API endpoint `/api/settings` returns current preference
- [ ] API endpoint `/api/settings` accepts updates to preference

**Dependencies:** F3

**Priority:** Nice to Have

---

### F18 – Simplified Navigation Structure

**Type:** Technical

**User Story:** As a developer, I need to update the navigation component to show only 4 items so that the UI is simpler and less overwhelming.

**Brief Description:**
The sidebar navigation is reduced from 8 items to 4: Dashboard, Free Up Space, History, Settings. The Review & Score, Subscriptions, and Rules pages are removed from navigation. Cleanup becomes a wizard flow launched from the Dashboard, not a nav item.

**Acceptance Criteria:**
- [ ] Sidebar shows exactly 4 items: Dashboard, Free Up Space, History, Settings
- [ ] "Review & Score" removed from nav (becomes wizard flow)
- [ ] "Subscriptions" removed from nav (merged into cleanup flow)
- [ ] "Rules" removed from nav (moved to Settings as Advanced section, or removed entirely)
- [ ] "Attachments" renamed to "Free Up Space"
- [ ] All nav items have clear icons
- [ ] Active route is highlighted in nav

**Dependencies:** F1, F8, F9, F10, F11

**Priority:** Must Have

---

### F19 – Wizard State Management

**Type:** Technical

**User Story:** As a developer, I need a state management system for the cleanup wizard so that users can move forward/backward through steps and the app remembers their progress.

**Brief Description:**
The wizard flow (F1-F7) requires client-side state management to track the current step, user decisions (Keep/Delete), and cleanup progress. This uses React Context or a state library (Zustand, Redux) to maintain wizard state across components.

**Acceptance Criteria:**
- [ ] State tracks current wizard step (Scanning, Report, Mode Selection, Review, Confirmation, Execution, Success)
- [ ] State stores user decisions (emails marked Keep/Delete during review)
- [ ] State stores cleanup mode selection (Quick Clean vs Review All)
- [ ] State persists during browser refresh (localStorage backup)
- [ ] State clears when user returns to Dashboard after completion
- [ ] State allows navigation between steps (e.g., back to Report from Review)

**Dependencies:** F1, F2, F3, F4, F5, F6, F7

**Priority:** Must Have

---

### F20 – Error Handling and Retry Logic

**Type:** Technical

**User Story:** As a developer, I need robust error handling for Gmail API calls so that temporary failures don't break the cleanup flow.

**Brief Description:**
All Gmail API operations (scan, delete, unsubscribe, filter creation) include retry logic with exponential backoff. Errors are logged but don't stop the entire cleanup. Users see a summary of what succeeded and what failed at the end.

**Acceptance Criteria:**
- [ ] Gmail API calls retry up to 3 times with exponential backoff (2s, 4s, 8s)
- [ ] Rate limit errors (429) trigger automatic retry with increased delay
- [ ] OAuth token expiration triggers re-authentication flow
- [ ] Partial failures during cleanup are logged but don't stop execution
- [ ] Success screen shows both successes and failures ("4,200 cleaned, 15 failed")
- [ ] Failed actions are stored in cleanup_actions table with error message

**Dependencies:** F6

**Priority:** Must Have

---

### F21 – Mobile-Responsive Review Queue

**Type:** Technical

**User Story:** As a mobile user, I want the review queue to work smoothly on my phone with swipe gestures so that I can clean my inbox on the go.

**Brief Description:**
The Review Queue (F4) is optimized for mobile with swipe gestures (right = Keep, left = Delete), large touch targets, and a vertical card stack. The desktop version uses keyboard shortcuts. This ensures the app works well on all devices.

**Acceptance Criteria:**
- [ ] Review queue is fully responsive (works on mobile, tablet, desktop)
- [ ] Mobile: swipe right gesture marks email as Keep
- [ ] Mobile: swipe left gesture marks email as Delete
- [ ] Desktop: keyboard shortcuts work (K = Keep, D = Delete, S = Skip)
- [ ] Touch targets are at least 44x44px (iOS/Android accessibility standard)
- [ ] Card animations are smooth on mobile (60fps)
- [ ] Layout adjusts for portrait and landscape orientations

**Dependencies:** F4

**Priority:** Nice to Have

---

### F22 – Language Cleanup (Technical Terminology → User-Friendly)

**Type:** Technical

**User Story:** As a developer, I need to replace all technical jargon (KEEP/DELETE/UNCERTAIN, Score, etc.) with user-friendly language so that the app feels approachable.

**Brief Description:**
A codebase-wide find-and-replace updates all user-facing language: KEEP → "Safe" or "Keep", DELETE → "Clean up" or "Remove", UNCERTAIN → "Your call" or "Review", "Score" → "Classification" (or hide entirely), "Senders Processed" → "Senders Analyzed". This makes the app less technical and more user-friendly.

**Acceptance Criteria:**
- [ ] All UI text uses "Keep" instead of "KEEP"
- [ ] All UI text uses "Clean up" or "Remove" instead of "DELETE"
- [ ] All UI text uses "Your call" or "Review this" instead of "UNCERTAIN"
- [ ] Score numbers (0-100) are hidden from users (only show reasoning)
- [ ] Dashboard stats use "Senders Analyzed" not "Senders Processed"
- [ ] API responses still use technical terms internally (only UI changes)
- [ ] TypeScript types updated to match new terminology

**Dependencies:** All wizard features (F1-F7), supporting screens (F8-F13)

**Priority:** Must Have

---

## Features Removed or Deferred

These current features are intentionally removed or moved to "Later" priority.

---

### F23 – Subscriptions Page Removal

**Type:** Technical

**User Story:** As a developer, I need to remove the standalone Subscriptions page so that subscription management is integrated into the cleanup flow instead.

**Brief Description:**
The current `/dashboard/subscriptions` page is redundant with the main cleanup flow. Subscription detection and unsubscribe actions are now part of the cleanup wizard (F6). This reduces navigation complexity.

**Acceptance Criteria:**
- [ ] `/dashboard/subscriptions` route is removed
- [ ] Subscription cards component is removed or repurposed
- [ ] Unsubscribe logic is integrated into cleanup execution (F6)
- [ ] Subscription data is still stored in database (for future use)
- [ ] No navigation link to Subscriptions page

**Dependencies:** F6

**Priority:** Must Have

---

### F24 – Rules Page Deferral

**Type:** Technical

**User Story:** As a product manager, I want to defer the Rules page to a future release so that V2 focuses on simplicity rather than power features.

**Brief Description:**
The current `/dashboard/rules` page offers custom retention rules (e.g., "keep emails from @work.com older than 30 days"). This is a power feature that 95% of users don't need. It's hidden from navigation in V2 and either moved to Settings as an "Advanced" option or deferred entirely to V3.

**Acceptance Criteria:**
- [ ] `/dashboard/rules` route is removed from navigation
- [ ] Option 1: Move rule creation to Settings → Advanced section
- [ ] Option 2: Remove entirely and defer to V3
- [ ] Default rules still apply (safety protections remain)
- [ ] Custom rules can be added via Settings if Option 1 is chosen

**Dependencies:** None

**Priority:** Later

---

### F25 – Senders Page Simplification

**Type:** Technical

**User Story:** As a developer, I need to simplify the Senders page to focus only on whitelisting so that it doesn't overlap with the cleanup flow.

**Brief Description:**
The current `/dashboard/senders` page has filters (All/Unsubscribed/Filtered) and overlaps with the Review Queue. In V2, it's simplified to show only senders the user has interacted with, with a "Protect this sender" button. Alternatively, it's merged entirely into Settings → Protected Senders (F10).

**Acceptance Criteria:**
- [ ] Option 1: Simplify page to show only senders with "Protect" button, remove filters
- [ ] Option 2: Merge entirely into Settings → Protected Senders (F10)
- [ ] If Option 1: remove "Unsubscribed" and "Filtered" status filters
- [ ] If Option 2: remove `/dashboard/senders` route and nav item

**Dependencies:** F10

**Priority:** Nice to Have

---

## Summary

**Total Features:** 25

**Must Have:** 16 (F1-F13, F14, F15, F18, F19, F20, F22, F23)
**Nice to Have:** 6 (F16, F17, F21, F25)
**Later:** 2 (F24)

**Core Wizard Flow:** 7 features (F1-F7)
**Supporting Screens:** 6 features (F8-F13)
**Technical/Infrastructure:** 12 features (F14-F25)

This feature list transforms InboxNuke from a complex, technical dashboard into a guided, trust-first cleanup wizard that delivers on the promise: "Inbox peace of mind in 5 minutes."
