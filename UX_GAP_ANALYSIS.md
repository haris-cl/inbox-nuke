# UX GAP ANALYSIS - Inbox Nuke

This document compares the current app implementation against the UX Blueprint to identify what exists, what's missing, what's redundant, and how to migrate.

---

## Part 1: Current Screens Inventory

### What We Have Today

| # | Route | File | What It Does Today |
|---|-------|------|--------------------|
| 1 | `/` | `app/page.tsx` | Landing page with "Connect Gmail" button, feature cards, tech stack badge |
| 2 | `/dashboard` | `app/dashboard/page.tsx` | Stats cards (deleted, freed, processed), control panel (Start/Pause/Resume/Cancel), scoring summary card, activity feed |
| 3 | `/dashboard/score` | `app/dashboard/score/page.tsx` | Workflow guide (3 steps), scan control, stats cards (Keep/Delete/Uncertain), score distribution chart, top senders, tabs for "By Sender" and "By Email" with filter buttons and override actions |
| 4 | `/dashboard/senders` | `app/dashboard/senders/page.tsx` | Search box, filter dropdown (All/Unsubscribed/Filtered), paginated table of senders with Whitelist button |
| 5 | `/dashboard/history` | `app/dashboard/history/page.tsx` | Status filter dropdown, paginated list of past runs with stats |
| 6 | `/dashboard/history/[runId]` | `app/dashboard/history/[runId]/page.tsx` | Detailed view of specific cleanup run with action log |
| 7 | `/dashboard/attachments` | `app/dashboard/attachments/page.tsx` | Filters (min size, older than), stats cards, selectable email list with checkboxes, Delete Selected button |
| 8 | `/dashboard/settings` | `app/dashboard/settings/page.tsx` | Whitelist management (add/remove), Gmail connection status with Disconnect button, Learned Preferences section |
| 9 | `/dashboard/subscriptions` | `app/dashboard/subscriptions/page.tsx` | Stats cards, bulk actions (Select All, Clear, Bulk Unsubscribe), search, subscription cards with Unsubscribe/Cleanup buttons |
| 10 | `/dashboard/rules` | `app/dashboard/rules/page.tsx` | Stats cards, Add Rule button, Preview Impact button, Default rules list, Custom rules list, Add Rule dialog with form |

### Current Navigation Structure

```
Sidebar (8 items):
├── Dashboard          ← Main hub
├── Review & Score     ← Primary cleanup flow
├── Senders            ← View discovered senders
├── History            ← Past runs
├── Settings           ← Whitelist, connection
└── Tools:
    └── Attachments    ← Large email cleanup

Hidden (not in nav):
├── Subscriptions
└── Rules
```

### Current Components Inventory

| Component | File | Used In | Purpose |
|-----------|------|---------|---------|
| StatCard | `stat-card.tsx` | Dashboard, Score, Subscriptions, Rules | Display single metric with icon |
| ControlPanel | `control-panel.tsx` | Dashboard | Start/Pause/Resume/Cancel buttons |
| ProgressSection | `progress-section.tsx` | Dashboard | Shows cleanup progress bar |
| ActivityFeed | `activity-feed.tsx` | Dashboard | List of recent actions |
| SenderRow | `sender-row.tsx` | Score page | Single sender with stats and View Emails button |
| EmailScoreCard | `email-score-card.tsx` | Score page | Single email with score, reasoning, Keep/Delete buttons |
| SubscriptionCard | `subscription-card.tsx` | Subscriptions page | Single subscription with actions |
| RuleCard | `rule-card.tsx` | Rules page | Single retention rule |
| RunHistoryCard | `run-history-card.tsx` | History page | Single run summary |

---

## Part 2: Gap Analysis by Blueprint Section

### Blueprint Screen 1: Home (Unauthenticated)

**What Blueprint Wants:**
- Single "Connect Gmail" button
- "100% Local" trust badge in header
- Trust signals section (privacy, reversibility, open source)
- How it works (3 steps with icons)

**What We Have:**
- ✅ "Connect Gmail" button
- ✅ "Go to Dashboard" button when already connected
- ✅ Feature cards (100% Local, Autonomous, Real-time)
- ⚠️ Tech stack badge at bottom

**What's Missing:**
- ❌ "100% Local" badge in header (currently only in feature cards)
- ❌ Explicit trust signals section ("emails never leave computer", "30-day undo")
- ❌ Simple 3-step "How it works" (Connect → Scan → Clean)
- ❌ The headline is "INBOX NUKE" not the value prop "Inbox peace of mind"

**What's Redundant/Confusing:**
- Tech stack badge ("Powered by FastAPI + Next.js + OpenAI") is developer-focused, not user-focused
- Feature cards are verbose; users want quick reassurance, not marketing copy

**Gap Rating: 🟡 Partial Match** - Has the basics, needs trust-focused redesign

---

### Blueprint Screen 2: Dashboard (Authenticated)

**What Blueprint Wants:**
- Inbox Health Card (status: "Needs Attention" / "Healthy", potential cleanup count, space savings)
- Single primary action: "Start Cleanup"
- Quick Stats (lifetime totals)
- Quick Actions (secondary): Free up space, Manage subscriptions, Protected senders
- Recent Activity (collapsible)

**What We Have:**
- ✅ Stats cards (Emails Deleted, Storage Freed, Senders Processed, Total Senders)
- ✅ Control Panel with Start button
- ✅ Scoring Summary Card when data exists
- ✅ Activity Feed

**What's Missing:**
- ❌ "Inbox Health" status (Needs Attention / Healthy)
- ❌ "Potential cleanup" count before user scans
- ❌ Clear "Quick Actions" section linking to Space/Subscriptions/Settings
- ❌ Stats are "current run" focused, not "lifetime" focused
- ❌ "Start Scan" goes to Score page instead of keeping user on Dashboard during scan

**What's Redundant/Confusing:**
- Control panel has Pause/Resume/Cancel buttons that rarely apply (only during active run)
- Stats cards show zeros on first visit - not helpful
- "Start Scan" immediately navigates away, breaking the flow
- Scoring Summary Card is developer-focused (shows KEEP/DELETE/UNCERTAIN jargon)

**Gap Rating: 🔴 Major Gaps** - Needs significant restructuring

---

### Blueprint Screen 3: Scanning (Loading State)

**What Blueprint Wants:**
- Full-screen progress view
- Progress bar with count ("12,847 emails scanned")
- Live discoveries building up ("Found 3,200 promotional emails")
- Transparency text ("Looking at email categories...")

**What We Have:**
- ⚠️ Progress bar exists in Score page's Scan Control Panel
- ⚠️ Shows "X / Y emails" count

**What's Missing:**
- ❌ Dedicated scanning screen/state - currently just a small section in Score page
- ❌ Live discoveries ("Found X promotional emails")
- ❌ Transparency text ("What's happening now")
- ❌ Engaging animation during wait
- ❌ User navigates to Score page instead of staying on Dashboard

**What's Redundant/Confusing:**
- Scanning happens on Score page which also shows results, making it cluttered
- Progress is shown in a small card, not as the primary focus

**Gap Rating: 🔴 Major Gaps** - No dedicated scanning experience

---

### Blueprint Screen 4: Inbox Report (Post-Scan)

**What Blueprint Wants:**
- Big headline: "We found 4,200 emails to clean up"
- Visual breakdown (pie/bar chart by category)
- "What's Protected" reassurance section
- Two clear choices: "Quick Clean" vs "Review All"

**What We Have:**
- ✅ Stats cards showing Keep/Delete/Uncertain counts
- ✅ Score Distribution chart
- ✅ Top Delete Candidates / Top Keep Senders cards

**What's Missing:**
- ❌ Clear "We found X emails to clean up" headline
- ❌ "What's Protected" reassurance section
- ❌ "Quick Clean" vs "Review All" choice - currently only one flow
- ❌ Category breakdown (promotions, newsletters, social) - only have score distribution
- ❌ This is not a separate screen, it's mixed into Score page

**What's Redundant/Confusing:**
- Score Distribution shows technical score ranges (0-10, 10-20) not meaningful categories
- KEEP/DELETE/UNCERTAIN terminology is technical
- No clear "next step" - user has to figure out what to do with the data

**Gap Rating: 🔴 Major Gaps** - No distinct report/decision screen

---

### Blueprint Screen 5: Review Queue

**What Blueprint Wants:**
- One email at a time (card view)
- Progress indicator (12 of 50)
- AI suggestion with reasoning
- Big Keep/Delete buttons
- "Skip All & Trust AI" escape hatch

**What We Have:**
- ✅ EmailScoreCard component with Keep/Delete buttons
- ✅ Shows reasoning in card
- ⚠️ Displayed as a grid of cards, not one at a time

**What's Missing:**
- ❌ One-at-a-time view (currently shows grid of all emails)
- ❌ Clear progress indicator ("12 of 50")
- ❌ "Skip All & Trust AI" escape hatch
- ❌ Focus on uncertain emails only - currently shows all
- ❌ Swipe-friendly mobile design

**What's Redundant/Confusing:**
- Grid view is overwhelming with many emails
- Filter buttons require user to manually select "Uncertain"
- No guided flow - user must figure out to filter by UNCERTAIN

**Gap Rating: 🔴 Major Gaps** - Review UX needs complete redesign

---

### Blueprint Screen 6: Confirmation

**What Blueprint Wants:**
- Clear summary of what will happen
- Safety reminder (goes to Trash, 30-day recovery)
- Single "Confirm Cleanup" button

**What We Have:**
- ⚠️ `confirm()` JavaScript dialog for bulk delete
- ⚠️ Alert shows "Successfully deleted X emails" after

**What's Missing:**
- ❌ Dedicated confirmation screen
- ❌ Safety reassurance about Trash recovery
- ❌ Summary of what's protected
- ❌ Professional UI (currently browser `confirm()` dialog)

**What's Redundant/Confusing:**
- Browser confirm dialogs feel jarring and untrustworthy
- No clear indication that emails go to Trash, not permanent delete

**Gap Rating: 🔴 Major Gaps** - No proper confirmation flow

---

### Blueprint Screen 7: Success

**What Blueprint Wants:**
- Celebration moment (animation, checkmark)
- Results summary (emails cleaned, space freed)
- Next steps (auto-cleanup toggle, protect senders link)
- "Back to Dashboard" button

**What We Have:**
- ⚠️ `alert()` JavaScript dialog showing "Successfully deleted X emails"

**What's Missing:**
- ❌ Dedicated success screen
- ❌ Celebration animation
- ❌ Detailed results breakdown
- ❌ Next steps suggestions
- ❌ Auto-cleanup scheduling option

**What's Redundant/Confusing:**
- Browser alert is anticlimactic after major cleanup
- User stays on Score page, doesn't return to Dashboard naturally
- No habit-building for return visits

**Gap Rating: 🔴 Major Gaps** - No success experience

---

### Blueprint Screen 8: Protected Senders (Settings)

**What Blueprint Wants:**
- Add email/domain form
- List of protected senders with remove button
- Auto-protected section (contacts, replied-to, financial)

**What We Have:**
- ✅ Whitelist Management section in Settings
- ✅ Add form with email/domain input
- ✅ List with remove buttons
- ✅ Added date shown

**What's Missing:**
- ❌ "Auto-protected" section explaining system protections
- ❌ Clear explanation of what whitelist does

**What's Redundant/Confusing:**
- Mixed in with Gmail Connection and Learned Preferences
- Term "Whitelist" is less clear than "Protected Senders"
- No visibility into what's automatically protected

**Gap Rating: 🟡 Partial Match** - Core functionality exists, needs clarity

---

### Blueprint Screen 9: Space Manager

**What Blueprint Wants:**
- Header showing storage usage ("14.2 GB of 15 GB")
- Filters (size, age)
- Email list with checkboxes and sizes
- Running total of selected
- "Delete Selected" button

**What We Have:**
- ✅ Filters (min size MB, older than days)
- ✅ Stats cards (Large Emails count, Total Size, Selected count/size)
- ✅ Email list with checkboxes
- ✅ Select All / Delete Selected buttons

**What's Missing:**
- ❌ Storage usage context ("You're using X of Y GB")
- ❌ Visual emphasis on potential space savings

**What's Redundant/Confusing:**
- Page is functional but lacks context about WHY user needs it
- Could benefit from more prominent size display per email

**Gap Rating: 🟢 Good Match** - Minor improvements needed

---

### Blueprint Screen 10: History

**What Blueprint Wants:**
- List of past cleanups with date, count, space freed
- View Details link for each
- Lifetime stats at bottom

**What We Have:**
- ✅ Paginated list of runs
- ✅ Status filter dropdown
- ✅ Status badges, timing, stats per run
- ✅ Expandable to run details page

**What's Missing:**
- ❌ Lifetime stats summary at bottom
- ❌ Cleaner presentation (current cards are technical)

**What's Redundant/Confusing:**
- Shows technical statuses (pending, running, paused, etc.) - users just want to see completed cleanups
- Doesn't emphasize the value delivered (space freed, emails cleaned)

**Gap Rating: 🟡 Partial Match** - Functional but could be simpler

---

## Part 3: Redundancy Analysis

### Screens That Are Redundant or Confusing

| Current Screen | Problem | Recommendation |
|----------------|---------|----------------|
| **Subscriptions** | Duplicates cleanup flow - subscriptions are just another type of sender to clean | **Delete** - merge into main cleanup, surface during review |
| **Rules** | Power feature that 95% of users don't need, adds confusion | **Hide** - move to Settings as advanced option |
| **Senders** | Useful for whitelist but overlaps with Score page's sender view | **Simplify** - keep for whitelist only, remove filters |

### Features That Exist But Are Buried

| Feature | Current Location | Should Be |
|---------|------------------|-----------|
| Whitelist a sender | Settings page, also via button in Senders page | In review flow when marking as KEEP |
| Unsubscribe | Hidden Subscriptions page | In cleanup flow as part of sender actions |
| Override classification | Small buttons on email cards | Prominent during review queue |

### Technical Jargon to Replace

| Current Term | User-Friendly Alternative |
|--------------|--------------------------|
| KEEP | Safe / Keep |
| DELETE | Clean up / Remove |
| UNCERTAIN | Your call / Review this |
| Score (0-100) | Hide internal score, show reasoning |
| Senders Processed | Senders analyzed |
| Scoring | Scanning / Analysis |

---

## Part 4: Proposed Target Screen List

### Keep As-Is
| Screen | Why Keep |
|--------|----------|
| **Attachments** (`/dashboard/attachments`) | Solid standalone tool, matches blueprint's "Space Manager" |
| **History** (`/dashboard/history`) | Core functionality present |

### Keep But Simplify
| Screen | Changes Needed |
|--------|----------------|
| **Home** (`/`) | Add trust signals, simplify to single CTA, remove tech badge |
| **Settings** (`/dashboard/settings`) | Rename "Whitelist" → "Protected Senders", add auto-protected section, hide or move Rules here |
| **Senders** (`/dashboard/senders`) | Remove filters, simplify to "protect this sender" only, or merge into Settings |

### Delete or Hide
| Screen | Reason |
|--------|--------|
| **Subscriptions** (`/dashboard/subscriptions`) | Merge into main cleanup flow |
| **Rules** (`/dashboard/rules`) | Move to Settings as "Advanced" or remove entirely |
| **History Detail** (`/dashboard/history/[runId]`) | Keep but simplify - most users don't need action log |

### Create New
| New Screen | Purpose | Blueprint Reference |
|------------|---------|---------------------|
| **Cleanup Flow** (multi-step) | Replace Score page with guided wizard | Screens 3-7 |
| **Inbox Report** | Show what scan found, offer Quick Clean vs Review All | Screen 4 |
| **Review Queue** | One-at-a-time email review for uncertain items | Screen 5 |
| **Confirmation** | Final check before cleanup executes | Screen 6 |
| **Success** | Celebrate results, suggest next steps | Screen 7 |

---

## Part 5: Target Navigation Structure

### Proposed Simplified Navigation

```
Sidebar (4 items):
├── Dashboard          ← Inbox health, start cleanup
├── Free Up Space      ← Large attachments (rename from Attachments)
├── History            ← Past cleanups
└── Settings           ← Protected senders, connection, (advanced rules)

Cleanup is NOT a nav item - it's a flow launched from Dashboard
```

### Flow vs. Page Distinction

**Pages** (have nav items, can be accessed directly):
- Dashboard
- Free Up Space
- History
- Settings

**Flows** (multi-step, launched from Dashboard, no direct nav):
- Cleanup Flow: Scanning → Report → Mode Selection → Review Queue → Confirmation → Success

---

## Part 6: Migration Plan

### Overview

This is a phased approach that keeps the current app working while building the new experience.

---

### Phase 1: Foundation (Week 1)

**Goal:** Build the new Dashboard without breaking anything.

**Step 1.1: Create new Dashboard component**
- Create `/dashboard/v2/page.tsx` as a new route
- Build "Inbox Health Card" with status indicator
- Add "Start Cleanup" as single primary button
- Add Quick Actions section (links to Space, Settings)
- Keep old Dashboard at `/dashboard` working

**Step 1.2: Simplify Home page**
- Replace feature cards with trust signals
- Change headline from "INBOX NUKE" branding to value prop
- Add simple "How it works" section
- Remove tech stack badge

**Step 1.3: Rename navigation items**
- "Review & Score" → remove from nav (will become flow)
- "Attachments" → "Free Up Space"
- Keep Senders for now (will simplify later)

**What Users See:** Old app still works, new Dashboard available at /dashboard/v2 for testing.

---

### Phase 2: Cleanup Flow (Week 2)

**Goal:** Build the new guided cleanup experience.

**Step 2.1: Create Scanning screen**
- New component that shows during scan
- Full-screen progress with live discoveries
- No navigation during scan - user watches

**Step 2.2: Create Inbox Report screen**
- Shows after scan completes
- "What we found" headline
- "What's Protected" section
- Two buttons: "Quick Clean" and "Review All"

**Step 2.3: Create Review Queue**
- One email at a time view
- Big Keep/Delete buttons
- Progress indicator (12 of 50)
- "Skip All & Trust AI" button
- Only shows UNCERTAIN emails

**Step 2.4: Create Confirmation screen**
- Summary of what will be deleted
- Safety reminder (Trash, 30-day recovery)
- "Confirm Cleanup" button

**Step 2.5: Create Success screen**
- Celebration animation
- Results summary
- "Back to Dashboard" button
- Optional: auto-cleanup scheduling

**What Users See:** New cleanup flow works end-to-end, launched from new Dashboard.

---

### Phase 3: Cleanup & Migration (Week 3)

**Goal:** Remove old pages, switch to new experience.

**Step 3.1: Make new Dashboard the default**
- Move `/dashboard/v2/page.tsx` to `/dashboard/page.tsx`
- Delete old Dashboard code

**Step 3.2: Remove Score page from navigation**
- Score page still exists (for direct URL access) but not in nav
- Cleanup is only accessible via Dashboard flow

**Step 3.3: Hide or delete Subscriptions page**
- Remove from any remaining nav/links
- Subscription handling is now part of cleanup flow

**Step 3.4: Move Rules to Settings**
- Add "Advanced" section to Settings
- Move rule creation there
- Delete standalone Rules page

**Step 3.5: Simplify Senders page**
- Remove filters (All/Unsubscribed/Filtered)
- Focus on "Protect this sender" action
- Or merge entirely into Settings → Protected Senders

**What Users See:** Clean, simple app matching the blueprint.

---

### Phase 4: Polish (Week 4)

**Goal:** Refine the experience based on the blueprint principles.

**Step 4.1: Language cleanup**
- Replace KEEP/DELETE/UNCERTAIN throughout codebase
- Use "Safe", "Clean up", "Your call" instead

**Step 4.2: Add trust elements**
- "100% Local" badge in header
- Safety reminders on all delete actions
- "What's auto-protected" section in Settings

**Step 4.3: Mobile optimization**
- Make Review Queue swipeable
- Ensure all flows work on phone
- Test touch targets on buttons

**Step 4.4: Return user experience**
- Dashboard shows "new junk since last cleanup"
- One-click maintenance cleanup
- Remember user preferences

---

## Summary: Before & After

### Navigation Before (8 items)
```
Dashboard | Review & Score | Subscriptions | Rules | Senders | Attachments | History | Settings
```

### Navigation After (4 items)
```
Dashboard | Free Up Space | History | Settings
```

### Screens Before (10)
1. Home
2. Dashboard
3. Review & Score
4. Senders
5. History
6. History Detail
7. Attachments
8. Settings
9. Subscriptions
10. Rules

### Screens After (9, but clearer purpose)
1. Home (simplified)
2. Dashboard (with Inbox Health)
3. Cleanup Flow: Scanning
4. Cleanup Flow: Inbox Report
5. Cleanup Flow: Review Queue
6. Cleanup Flow: Confirmation
7. Cleanup Flow: Success
8. Free Up Space (renamed Attachments)
9. History (simplified)
10. Settings (with Protected Senders + Advanced)

### Key Wins
- **Fewer decisions:** 4 nav items instead of 8
- **Guided flow:** Cleanup is step-by-step, not "figure it out"
- **Trust first:** "What's Protected" shown before "What's Deleted"
- **Less jargon:** No KEEP/DELETE/UNCERTAIN, no scores
- **Clear purpose:** Each screen does one thing

---

## Appendix: Backend Changes Needed

The backend (API endpoints) mostly stays the same. Changes needed:

| Change | Why |
|--------|-----|
| New endpoint: `/api/inbox-health` | Dashboard needs to show health status without running full scan |
| Modify: `/api/scoring/stats` | Include "category breakdown" (promotions, newsletters, etc.) |
| New endpoint: `/api/auto-protected` | Show what's automatically protected |
| Modify: delete responses | Return Trash confirmation (recoverable for 30 days) |

These backend changes are **optional for Phase 1-2** - the new UI can work with existing endpoints initially.
