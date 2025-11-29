# APP MAP - Inbox Nuke

This document explains every screen in the app, what you can do on each screen, and which backend services power each feature.

---

## Overview: What This App Does

Inbox Nuke is a Gmail cleanup tool that:
1. Connects to your Gmail account
2. Scans your inbox to find newsletters, promotions, and unwanted emails
3. Scores each email to decide if it should be kept or deleted
4. Lets you review and override decisions
5. Deletes unwanted emails and unsubscribes from mailing lists

---

## Frontend Pages (What You See)

### 1. Home Page
**URL:** `/`
**File:** `frontend/app/page.tsx`

**What it does:** Landing page where you connect your Gmail account.

**What you can do:**
| Element | What it does |
|---------|--------------|
| "Connect Gmail" button | Opens Google login to authorize the app |
| "Go to Dashboard" button | (Shows after connecting) Takes you to main dashboard |

**Backend endpoints used:**
- `GET /api/auth/status` - Checks if Gmail is already connected
- `GET /api/auth/google/start` - Gets the Google login URL

---

### 2. Dashboard (Main Control Center)
**URL:** `/dashboard`
**File:** `frontend/app/dashboard/page.tsx`

**What it does:** Your home base - shows stats and lets you start email scanning.

**What you can do:**
| Element | What it does |
|---------|--------------|
| "Start Scan" button | Begins scanning your emails (goes to Review & Score page) |
| "Pause" button | Pauses an active scan |
| "Resume" button | Continues a paused scan |
| "Cancel" button | Stops and cancels current scan |
| "View Details" link | Goes to Review & Score page for full results |

**What you see:**
- **Emails Deleted** - Number of emails removed
- **Storage Freed** - How much space you've recovered (MB/GB)
- **Senders Processed** - How many email senders analyzed
- **Total Senders** - Total senders found in your inbox
- **Scoring Summary Card** - Shows Keep/Delete/Uncertain counts
- **Activity Feed** - Recent actions taken by the cleanup agent

**Backend endpoints used:**
- `GET /api/stats/current` - Gets all dashboard statistics
- `GET /api/scoring/stats` - Gets email scoring summary
- `POST /api/scoring/start` - Starts email scanning
- `POST /api/runs/{id}/pause` - Pauses a run
- `POST /api/runs/{id}/resume` - Resumes a run
- `POST /api/runs/{id}/cancel` - Cancels a run
- `GET /api/runs/{id}/actions` - Gets activity log

---

### 3. Review & Score Page
**URL:** `/dashboard/score`
**File:** `frontend/app/dashboard/score/page.tsx`

**What it does:** The main cleanup workspace. Scan emails, review scores, and decide what to delete.

**Sections:**

#### Workflow Guide (top banner)
Shows the 3-step process:
1. Scan your inbox
2. Review classifications
3. Clean up

#### Scan Control Panel
| Element | What it does |
|---------|--------------|
| "Start Full Scan" button | Scans up to 50,000 emails |
| "Scan New Emails" button | Only scans emails not previously scanned |
| "Rescan All" button | Re-analyzes all emails from scratch |
| Progress bar | Shows scan progress (X / Y emails) |

#### Stats Cards
Shows 4 numbers:
- **Keep** - Emails marked safe to keep
- **Delete** - Emails marked for deletion
- **Uncertain** - Emails that need your review
- **Total Scored** - Total emails analyzed

#### Score Distribution Chart
Bar chart showing how many emails fall into each score range (0-10, 10-20, etc.)
- Low scores (green) = likely to keep
- High scores (red) = likely to delete

#### Top Senders Cards
- **Top Delete Candidates** - Senders whose emails are mostly marked for deletion
- **Top Keep Senders** - Senders whose emails are mostly important

#### Tabs: By Sender / By Email

**By Sender Tab:**
| Element | What it does |
|---------|--------------|
| Filter buttons (All, Keep, Delete, Uncertain) | Filter senders by their classification |
| Sender rows | Shows each sender with email count and classification |
| "View Emails" button | Shows all emails from that sender |

**By Email Tab:**
| Element | What it does |
|---------|--------------|
| Filter buttons (All, Keep, Delete, Uncertain) | Filter emails by classification |
| "Delete All" button | (When filtering DELETE) Permanently deletes all DELETE emails |
| Email cards | Shows subject, sender, score, and classification |
| "Keep" button on each email | Override to mark as KEEP |
| "Delete" button on each email | Override to mark as DELETE |

**Backend endpoints used:**
- `POST /api/scoring/start` - Start scanning
- `GET /api/scoring/progress` - Get scan progress
- `GET /api/scoring/stats` - Get scoring statistics
- `GET /api/scoring/senders` - Get sender profiles with scores
- `GET /api/scoring/emails` - Get scored emails list
- `POST /api/scoring/emails/{id}/override` - Override email classification
- `POST /api/scoring/execute` - Delete emails by classification
- `POST /api/feedback/submit` - Submit feedback when you override (teaches the AI)

---

### 4. Senders Page
**URL:** `/dashboard/senders`
**File:** `frontend/app/dashboard/senders/page.tsx`

**What it does:** View all email senders discovered in your inbox.

**What you can do:**
| Element | What it does |
|---------|--------------|
| Search box | Search senders by email or name |
| Filter dropdown | Filter by: All, Unsubscribed, Filtered |
| "Whitelist" button | Protect this sender from future cleanup |
| Previous/Next buttons | Navigate through sender pages |

**What you see for each sender:**
- Email address and display name
- How many emails they've sent you
- Status badges: Active, Unsubscribed, or Filtered

**Backend endpoints used:**
- `GET /api/senders` - List discovered senders
- `POST /api/whitelist` - Add sender to protected list

---

### 5. History Page
**URL:** `/dashboard/history`
**File:** `frontend/app/dashboard/history/page.tsx`

**What it does:** View past cleanup runs and their results.

**What you can do:**
| Element | What it does |
|---------|--------------|
| Status dropdown | Filter by: All, Completed, Failed, Running, Paused |
| Run cards | Click to see details of each run |
| Previous/Next buttons | Navigate through history pages |

**What you see for each run:**
- When it started and finished
- Status (completed, failed, running, etc.)
- How many emails deleted
- How much storage freed

**Backend endpoints used:**
- `GET /api/runs` - List all cleanup runs

---

### 6. History Detail Page
**URL:** `/dashboard/history/[runId]`
**File:** `frontend/app/dashboard/history/[runId]/page.tsx`

**What it does:** Detailed view of a specific cleanup run.

**What you see:**
- Full statistics for that run
- List of all actions taken (deletes, unsubscribes, filters created)

**Backend endpoints used:**
- `GET /api/runs/{id}` - Get run details
- `GET /api/runs/{id}/actions` - Get actions from that run

---

### 7. Attachments Page
**URL:** `/dashboard/attachments`
**File:** `frontend/app/dashboard/attachments/page.tsx`

**What it does:** Find and delete large emails to free up storage space.

**What you can do:**
| Element | What it does |
|---------|--------------|
| Minimum Size (MB) input | Only show emails larger than X MB |
| Older Than (Days) input | Only show emails older than X days |
| "Apply Filters" button | Search with current filters |
| Checkboxes | Select emails for deletion |
| "Select All" button | Select all visible emails |
| "Delete Selected" button | Delete checked emails |

**What you see:**
- List of large emails with subject, sender, size, and date
- Stats: Total large emails found, total size, selected count

**Backend endpoints used:**
- `GET /api/attachments/large` - Find large emails
- `POST /api/attachments/cleanup` - Delete selected emails

---

### 8. Settings Page
**URL:** `/dashboard/settings`
**File:** `frontend/app/dashboard/settings/page.tsx`

**What it does:** Manage protected senders, Gmail connection, and AI learning.

**Sections:**

#### Whitelist Management
| Element | What it does |
|---------|--------------|
| Input field | Enter email or domain to protect |
| "Add" button | Add to whitelist |
| Trash icon | Remove from whitelist |

Whitelisted emails/domains will NEVER be deleted.

#### Gmail Connection
| Element | What it does |
|---------|--------------|
| Connection status | Shows connected email |
| "Disconnect Gmail" button | Revokes access and logs you out |

#### Learned Preferences
Shows what the AI has learned from your feedback:
| Element | What it does |
|---------|--------------|
| Preference cards | Shows patterns the AI learned (e.g., "always keep emails from boss@company.com") |
| Trash icon | Delete a learned preference |
| Stats | Total feedback given, preferences learned |

**Backend endpoints used:**
- `GET /api/whitelist` - List whitelisted entries
- `POST /api/whitelist` - Add to whitelist
- `DELETE /api/whitelist/{email}` - Remove from whitelist
- `GET /api/auth/status` - Check Gmail connection
- `POST /api/auth/disconnect` - Disconnect Gmail
- `GET /api/feedback/preferences` - Get learned preferences
- `DELETE /api/feedback/preferences/{id}` - Delete a preference
- `GET /api/feedback/stats` - Get feedback statistics

---

### 9. Subscriptions Page (Hidden from Nav)
**URL:** `/dashboard/subscriptions`
**File:** `frontend/app/dashboard/subscriptions/page.tsx`

**What it does:** Manage email subscriptions (newsletters, mailing lists).

**What you can do:**
| Element | What it does |
|---------|--------------|
| Search box | Search subscriptions by sender |
| "Select All Active" button | Select all active subscriptions |
| "Clear Selection" button | Deselect all |
| "Unsubscribe Selected" button | Bulk unsubscribe from selected |
| Individual subscription cards | Unsubscribe or cleanup old emails |

**Backend endpoints used:**
- `GET /api/subscriptions` - List subscriptions
- `POST /api/subscriptions/{id}/unsubscribe` - Unsubscribe from one
- `POST /api/subscriptions/bulk-unsubscribe` - Unsubscribe from multiple
- `POST /api/subscriptions/{id}/cleanup` - Delete old emails from subscription

---

### 10. Rules Page (Hidden from Nav)
**URL:** `/dashboard/rules`
**File:** `frontend/app/dashboard/rules/page.tsx`

**What it does:** Create custom rules to control email retention.

**What you can do:**
| Element | What it does |
|---------|--------------|
| "Add Custom Rule" button | Opens dialog to create new rule |
| "Preview Cleanup Impact" button | Shows what cleanup would do with current rules |
| Rule cards | View existing rules, delete custom ones |

**Add Rule Dialog:**
| Field | What it does |
|-------|--------------|
| Rule Type dropdown | Sender Domain, Sender Pattern, Subject Pattern, Keyword, Category |
| Pattern input | The pattern to match (e.g., @spam.com) |
| Action dropdown | KEEP, DELETE, or REVIEW |
| Priority input | 1-10, higher = more important |

**Backend endpoints used:**
- `GET /api/retention/rules` - List rules
- `POST /api/retention/rules` - Create rule
- `DELETE /api/retention/rules/{index}` - Delete rule
- `GET /api/retention/preview` - Preview cleanup impact

---

## Navigation Structure

**Primary Navigation (always visible):**
1. Dashboard - Main control center
2. Review & Score - Email scoring and cleanup
3. Senders - View discovered senders
4. History - Past cleanup runs
5. Settings - Whitelist and preferences

**Tools Section:**
6. Attachments - Find large emails

**Hidden Pages (not in nav but accessible):**
- Subscriptions (`/dashboard/subscriptions`)
- Rules (`/dashboard/rules`)

---

## Backend API Endpoints (Complete List)

### Authentication (`/api/auth`)
| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/status` | Check if Gmail is connected |
| GET | `/google/start` | Get Google OAuth URL |
| GET | `/google/callback` | Handle OAuth callback |
| POST | `/disconnect` | Revoke Gmail access |

### Cleanup Runs (`/api/runs`)
| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/` | List all cleanup runs |
| GET | `/{id}` | Get single run details |
| POST | `/start` | Start new cleanup run |
| POST | `/{id}/pause` | Pause a run |
| POST | `/{id}/resume` | Resume a run |
| POST | `/{id}/cancel` | Cancel a run |
| GET | `/{id}/actions` | Get actions from a run |

### Scoring (`/api/scoring`)
| Method | Endpoint | What it does |
|--------|----------|--------------|
| POST | `/start` | Start email scoring |
| GET | `/progress` | Get scoring progress |
| GET | `/stats` | Get scoring statistics |
| GET | `/emails` | List scored emails |
| GET | `/emails/{id}` | Get single email score |
| POST | `/emails/{id}/override` | Override classification |
| GET | `/senders` | List sender profiles |
| POST | `/execute` | Delete emails by classification |

### Senders (`/api/senders`)
| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/` | List discovered senders |

### Whitelist (`/api/whitelist`)
| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/` | List protected domains |
| POST | `/` | Add to whitelist |
| DELETE | `/{email}` | Remove from whitelist |

### Statistics (`/api/stats`)
| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/current` | Get dashboard stats |

### Attachments (`/api/attachments`)
| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/large` | Find large emails |
| POST | `/cleanup` | Delete selected large emails |

### Subscriptions (`/api/subscriptions`)
| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/` | List subscriptions |
| POST | `/{id}/unsubscribe` | Unsubscribe from one |
| POST | `/bulk-unsubscribe` | Unsubscribe from multiple |
| POST | `/{id}/cleanup` | Delete old subscription emails |

### Retention Rules (`/api/retention`)
| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/rules` | List retention rules |
| POST | `/rules` | Create new rule |
| DELETE | `/rules/{index}` | Delete rule |
| GET | `/preview` | Preview cleanup impact |

### Feedback (`/api/feedback`)
| Method | Endpoint | What it does |
|--------|----------|--------------|
| POST | `/submit` | Submit user feedback |
| GET | `/history` | Get feedback history |
| GET | `/preferences` | Get learned preferences |
| DELETE | `/preferences/{id}` | Delete a preference |
| GET | `/stats` | Get feedback statistics |

### Exports (`/api/exports`)
| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/runs/{id}/csv` | Download run as CSV |
| GET | `/senders/csv` | Download senders as CSV |

---

## Typical User Journey

1. **Connect Gmail** (Home page)
   - Click "Connect Gmail"
   - Authorize with Google
   - Redirected to Dashboard

2. **Scan Inbox** (Dashboard → Review & Score)
   - Click "Start Scan" on Dashboard
   - Wait for scan to complete (can take a few minutes)
   - View results on Review & Score page

3. **Review Results** (Review & Score page)
   - Check the scoring summary (Keep/Delete/Uncertain)
   - Look at "Top Delete Candidates" to see biggest offenders
   - Switch to "By Email" tab to review individual emails

4. **Override Mistakes** (Review & Score page)
   - Find emails incorrectly marked DELETE → click "Keep"
   - Find emails incorrectly marked KEEP → click "Delete"
   - AI learns from your corrections

5. **Clean Up** (Review & Score page)
   - Filter by "Delete"
   - Click "Delete All" to remove all DELETE-marked emails
   - Or delete individually

6. **Protect Important Senders** (Settings page)
   - Add important domains to whitelist
   - These will never be deleted in future scans

7. **Free Up Storage** (Attachments page)
   - Find large old emails
   - Select and delete to free space

---

## File Structure Summary

```
frontend/
├── app/
│   ├── page.tsx                        → Home (/)
│   ├── auth/callback/page.tsx          → OAuth callback
│   └── dashboard/
│       ├── page.tsx                    → Dashboard (/dashboard)
│       ├── layout.tsx                  → Navigation sidebar
│       ├── score/page.tsx              → Review & Score (/dashboard/score)
│       ├── senders/page.tsx            → Senders (/dashboard/senders)
│       ├── history/
│       │   ├── page.tsx                → History (/dashboard/history)
│       │   └── [runId]/page.tsx        → Run details (/dashboard/history/123)
│       ├── attachments/page.tsx        → Attachments (/dashboard/attachments)
│       ├── settings/page.tsx           → Settings (/dashboard/settings)
│       ├── subscriptions/page.tsx      → Subscriptions (hidden)
│       └── rules/page.tsx              → Rules (hidden)
└── lib/
    └── api.ts                          → API client (all backend calls)

backend/
├── main.py                             → App entry point, routes
├── routers/
│   ├── auth.py                         → /api/auth/*
│   ├── runs.py                         → /api/runs/*
│   ├── scoring.py                      → /api/scoring/*
│   ├── senders.py                      → /api/senders/*
│   ├── whitelist.py                    → /api/whitelist/*
│   ├── stats.py                        → /api/stats/*
│   ├── attachments.py                  → /api/attachments/*
│   ├── subscriptions.py                → /api/subscriptions/*
│   ├── retention.py                    → /api/retention/*
│   ├── feedback.py                     → /api/feedback/*
│   └── exports.py                      → /api/exports/*
└── agent/
    ├── scoring.py                      → Email scoring logic
    ├── runner.py                       → Cleanup orchestration
    └── safety.py                       → Protection rules
```
