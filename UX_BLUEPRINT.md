# UX BLUEPRINT - Inbox Nuke

## North Star

> **"Inbox peace of mind in 5 minutes."**

The ultimate goal is not just a clean inbox—it's the *confidence* that your inbox is under control without the fear of losing something important. Users should feel relieved, not anxious, when using this app.

**Success looks like:**
- User cleans 1,000+ emails in their first session
- User trusts the AI enough to let it run without reviewing every email
- User returns monthly for maintenance, not out of panic

---

## 1. Personas & Jobs-to-be-Done

### Persona A: "The Overwhelmed Professional"
**Who:** Mid-career professional (30-50), 10,000+ unread emails, subscribed to everything over the years, feels guilt every time they open Gmail.

**Job to be done:** *"Help me get my inbox under control without spending my entire weekend doing it."*

**Key anxieties:**
- "What if I delete something important from my boss or a client?"
- "I don't have time to review 10,000 emails"
- "I've tried inbox zero before and failed"

---

### Persona B: "The Privacy-Conscious User"
**Who:** Tech-aware user (25-45) who is wary of cloud services having access to their email data.

**Job to be done:** *"Clean my inbox without my emails being sent to some company's servers."*

**Key anxieties:**
- "Is my data being stored somewhere?"
- "Who can see my emails?"
- "Can I trust this app with my Gmail access?"

---

### Persona C: "The Storage Cruncher"
**Who:** Someone who just got the "Your Google storage is full" warning.

**Job to be done:** *"Find and delete the emails eating up my storage so I don't have to pay for more space."*

**Key anxieties:**
- "Which emails are actually large?"
- "I don't want to delete photos or important attachments"
- "How much space will I actually free up?"

---

### Persona D: "The Newsletter Prisoner"
**Who:** Someone who signed up for every newsletter, free trial, and promotion over the past 5 years.

**Job to be done:** *"Stop the flood of newsletters I never read without unsubscribing from each one manually."*

**Key anxieties:**
- "Unsubscribe links feel sketchy"
- "Some newsletters I actually want to keep"
- "Will they just sign me up again?"

---

## 2. Core User Journeys

### Journey A: First-Time Cleanup (Primary Flow)

This is the most important flow—the first 5 minutes determine if users trust the app.

```
Step 1: LAND
User arrives at home page → Sees clear value prop:
"Clean your inbox in 5 minutes. 100% local. Nothing leaves your computer."
→ Single button: "Connect Gmail"

Step 2: CONNECT
User clicks Connect Gmail → Google OAuth popup →
Returns to app → Sees brief "What we can access" transparency message
→ Automatic redirect to Dashboard

Step 3: SCAN
Dashboard shows: "Let's see what we're working with"
→ Big button: "Scan My Inbox"
→ Progress indicator: "Analyzing 12,847 emails..."
→ Takes 1-3 minutes, user sees real-time stats building

Step 4: DISCOVER
Scan complete → User sees "Inbox Health Report":
• "4,200 promotional emails (33%)"
• "2,100 newsletters you never open"
• "890 emails from senders you've never replied to"
• "Potential space savings: 2.4 GB"
→ Big button: "Start Cleanup"

Step 5: CHOOSE MODE
User picks cleanup approach:
• "Quick Clean" - AI handles it, just review the risky ones
• "I'll Review Everything" - See every email before it's touched
→ Most users pick Quick Clean

Step 6: REVIEW RISKY ONLY
For Quick Clean: Shows only the "uncertain" emails (maybe 50 out of 4,000)
→ "We're confident about 3,950 emails. Here are 50 we want your input on."
→ User swipes/clicks Keep or Delete on each
→ Big button: "Confirm Cleanup"

Step 7: DONE
Success screen:
• "4,200 emails cleaned up"
• "2.1 GB freed"
• "12 senders unsubscribed"
→ "Emails moved to trash (recoverable for 30 days)"
→ Option to "Set up monthly auto-cleanup"
```

---

### Journey B: Storage Emergency

For users who got the "storage full" warning.

```
Step 1: User clicks "Free Up Space" from Dashboard

Step 2: Sees "Space Hogs" view:
• Visual of what's eating storage (pie chart)
• List of largest emails, sorted by size
• "These 50 emails = 1.8 GB"

Step 3: User selects emails to delete (checkboxes, select all)

Step 4: Confirms deletion → Sees space freed counter animate up

Step 5: Returns to Dashboard with updated storage stats
```

---

### Journey C: Newsletter Detox

For users drowning in newsletters.

```
Step 1: User clicks "Manage Subscriptions" from Dashboard

Step 2: Sees list of all detected newsletters/mailing lists:
• Sender name + logo
• "142 emails, last opened: Never"
• "23 emails, you open 80% of these"

Step 3: User bulk-selects newsletters to unsubscribe from

Step 4: Clicks "Unsubscribe from 15 senders"
→ App handles mailto: and web unsubscribe methods

Step 5: Optional: "Also delete old emails from these senders?"
→ User confirms

Step 6: Success: "Unsubscribed from 15 senders. Deleted 2,400 old emails."
```

---

### Journey D: Ongoing Maintenance (Return User)

For users coming back after initial cleanup.

```
Step 1: User opens app → Dashboard shows:
• "127 new promotional emails since last cleanup"
• "Inbox health: Good"
• Quick action: "Clean new junk" (one click)

Step 2: User clicks "Clean new junk"
→ Instant cleanup, no review needed (AI learned from previous choices)

Step 3: Done in 10 seconds. "127 emails cleaned."
```

---

## 3. Proposed Screens

### Screen 1: Home (Unauthenticated)

**Purpose:** Build trust, get user to connect Gmail.

**Sections:**
```
┌─────────────────────────────────────────────────┐
│  HEADER: Logo + "100% Local" trust badge        │
├─────────────────────────────────────────────────┤
│  HERO:                                          │
│  • Headline: "Inbox peace of mind in 5 minutes" │
│  • Subhead: "AI-powered cleanup that runs       │
│    entirely on your computer"                   │
│  • [Connect Gmail] - single primary button      │
├─────────────────────────────────────────────────┤
│  TRUST SIGNALS:                                 │
│  • "Your emails never leave your computer"      │
│  • "Deleted emails go to trash (30-day undo)"   │
│  • "Open source - see exactly what it does"     │
├─────────────────────────────────────────────────┤
│  HOW IT WORKS (3 steps with icons):             │
│  1. Connect → 2. Scan → 3. Clean                │
└─────────────────────────────────────────────────┘
```

**Key UI elements:**
- One button only: "Connect Gmail"
- No sign-up, no account creation
- Privacy reassurance above the fold

---

### Screen 2: Dashboard (Authenticated - Main Hub)

**Purpose:** Show inbox health at a glance, provide clear next action.

**Sections:**
```
┌─────────────────────────────────────────────────┐
│  HEADER: Logo + user email + Disconnect         │
├─────────────────────────────────────────────────┤
│  INBOX HEALTH CARD (prominent):                 │
│  • Big status: "Needs Attention" / "Healthy"    │
│  • "3,200 emails could be cleaned"              │
│  • "1.8 GB potential space savings"             │
│  • [Start Cleanup] - primary button             │
├─────────────────────────────────────────────────┤
│  QUICK STATS (4 cards):                         │
│  • Emails cleaned (lifetime)                    │
│  • Space freed (lifetime)                       │
│  • Senders muted                                │
│  • Last cleanup date                            │
├─────────────────────────────────────────────────┤
│  QUICK ACTIONS (secondary):                     │
│  • "Free up space" → large attachments          │
│  • "Manage subscriptions" → newsletters         │
│  • "Protected senders" → whitelist              │
├─────────────────────────────────────────────────┤
│  RECENT ACTIVITY (collapsible):                 │
│  • "Yesterday: 142 emails cleaned"              │
│  • "Last week: Unsubscribed from 5 senders"     │
└─────────────────────────────────────────────────┘
```

**Key UI elements:**
- Single primary action: "Start Cleanup"
- Health status uses color (green/yellow/red)
- Quick actions are clearly secondary (outlined buttons or links)

---

### Screen 3: Scanning (Loading State)

**Purpose:** Keep user engaged while AI analyzes inbox.

**Sections:**
```
┌─────────────────────────────────────────────────┐
│  PROGRESS:                                      │
│  • "Analyzing your inbox..."                    │
│  • Progress bar (e.g., 45%)                     │
│  • "12,847 emails scanned"                      │
├─────────────────────────────────────────────────┤
│  LIVE DISCOVERIES (builds as scan runs):        │
│  • "Found 3,200 promotional emails"             │
│  • "Found 45 large attachments (890 MB)"        │
│  • "Found 12 newsletters you never open"        │
├─────────────────────────────────────────────────┤
│  WHAT'S HAPPENING (transparency):               │
│  • "Looking at email categories..."             │
│  • "Checking which senders you reply to..."     │
│  • "Identifying newsletters..."                 │
└─────────────────────────────────────────────────┘
```

**Key UI elements:**
- No actions available (user just watches)
- Stats animate/count up for engagement
- Takes 1-3 minutes for large inboxes

---

### Screen 4: Inbox Report (Post-Scan)

**Purpose:** Show user what was found, build confidence before cleanup.

**Sections:**
```
┌─────────────────────────────────────────────────┐
│  HEADLINE:                                      │
│  "We found 4,200 emails to clean up"            │
│  "Potential space savings: 2.4 GB"              │
├─────────────────────────────────────────────────┤
│  BREAKDOWN (visual pie/bar chart):              │
│  • Promotions: 2,100 (50%)                      │
│  • Newsletters: 1,400 (33%)                     │
│  • Social notifications: 500 (12%)              │
│  • Other low-value: 200 (5%)                    │
├─────────────────────────────────────────────────┤
│  WHAT'S PROTECTED (reassurance):                │
│  • "892 emails from people you email with"      │
│  • "All emails with attachments you've opened"  │
│  • "Anything from your contacts"                │
├─────────────────────────────────────────────────┤
│  CHOOSE YOUR APPROACH:                          │
│  [Quick Clean] - "AI handles it, you review     │
│                   only uncertain ones (50)"     │
│  [Review All]  - "See everything before         │
│                   it's touched"                 │
└─────────────────────────────────────────────────┘
```

**Key UI elements:**
- "What's Protected" section is critical for trust
- Two clear choices, Quick Clean is visually primary
- Numbers are specific, not vague

---

### Screen 5: Review Queue

**Purpose:** Let user make final decisions on uncertain emails.

**Sections:**
```
┌─────────────────────────────────────────────────┐
│  HEADER:                                        │
│  "Review 50 emails" (progress: 12 of 50)        │
│  [Skip All & Trust AI] - secondary action       │
├─────────────────────────────────────────────────┤
│  CURRENT EMAIL CARD (one at a time):            │
│  • From: "newsletter@company.com"               │
│  • Subject: "Weekly digest - Oct 2023"          │
│  • AI suggestion: "Delete" (with reason)        │
│  • "You've never opened emails from this sender"│
│                                                 │
│  [Keep] [Delete] - big touch-friendly buttons   │
├─────────────────────────────────────────────────┤
│  PROGRESS BAR at bottom                         │
│  "23 kept · 15 deleted · 12 remaining"          │
└─────────────────────────────────────────────────┘
```

**Key UI elements:**
- One email at a time (no overwhelming lists)
- Clear AI reasoning shown
- Big, swipeable Keep/Delete buttons (mobile-friendly)
- "Skip All & Trust AI" escape hatch

---

### Screen 6: Confirmation

**Purpose:** Final check before cleanup executes.

**Sections:**
```
┌─────────────────────────────────────────────────┐
│  HEADLINE:                                      │
│  "Ready to clean up 4,200 emails?"              │
├─────────────────────────────────────────────────┤
│  SUMMARY:                                       │
│  • 4,200 emails will be deleted                 │
│  • 12 senders will be unsubscribed              │
│  • ~2.4 GB will be freed                        │
├─────────────────────────────────────────────────┤
│  SAFETY REMINDER:                               │
│  • "Emails go to Trash, not permanently deleted"│
│  • "You have 30 days to recover anything"       │
│  • "892 important emails are protected"         │
├─────────────────────────────────────────────────┤
│  [Confirm Cleanup] - primary button             │
│  [Go Back] - secondary link                     │
└─────────────────────────────────────────────────┘
```

**Key UI elements:**
- Clear numbers
- Safety message is prominent (reduces anxiety)
- One primary action

---

### Screen 7: Success

**Purpose:** Celebrate, build habit for return visits.

**Sections:**
```
┌─────────────────────────────────────────────────┐
│  CELEBRATION:                                   │
│  ✓ "Inbox cleaned!"                             │
│  (maybe a subtle animation)                     │
├─────────────────────────────────────────────────┤
│  RESULTS:                                       │
│  • "4,200 emails cleaned"                       │
│  • "2.1 GB freed"                               │
│  • "12 senders unsubscribed"                    │
├─────────────────────────────────────────────────┤
│  NEXT STEPS:                                    │
│  • "Set up monthly auto-cleanup" - toggle       │
│  • "Protect specific senders" - link            │
├─────────────────────────────────────────────────┤
│  [Back to Dashboard] - primary button           │
└─────────────────────────────────────────────────┘
```

**Key UI elements:**
- Moment of celebration (dopamine hit)
- Specific numbers reinforce value
- Soft upsell to recurring cleanup

---

### Screen 8: Protected Senders (Settings)

**Purpose:** Let users protect important senders from ever being cleaned.

**Sections:**
```
┌─────────────────────────────────────────────────┐
│  HEADER:                                        │
│  "Protected Senders"                            │
│  "Emails from these senders will never be       │
│   deleted or filtered"                          │
├─────────────────────────────────────────────────┤
│  ADD PROTECTION:                                │
│  [Enter email or domain...] [Add]               │
├─────────────────────────────────────────────────┤
│  PROTECTED LIST:                                │
│  • boss@company.com (added Oct 15)    [Remove]  │
│  • @familyname.com (added Oct 10)     [Remove]  │
│  • bank@chase.com (added Oct 8)       [Remove]  │
├─────────────────────────────────────────────────┤
│  AUTO-PROTECTED (system):                       │
│  • People in your Google Contacts               │
│  • People you've replied to in past 6 months    │
│  • Government/financial institutions            │
└─────────────────────────────────────────────────┘
```

**Key UI elements:**
- Simple add/remove interface
- Show what's automatically protected (builds trust)

---

### Screen 9: Space Manager (For Storage Cruncher persona)

**Purpose:** Quickly find and delete large emails.

**Sections:**
```
┌─────────────────────────────────────────────────┐
│  HEADER:                                        │
│  "Free Up Space"                                │
│  "You're using 14.2 GB of 15 GB"                │
├─────────────────────────────────────────────────┤
│  FILTERS:                                       │
│  • Larger than: [5 MB ▼]                        │
│  • Older than: [1 year ▼]                       │
├─────────────────────────────────────────────────┤
│  SPACE HOGS LIST:                               │
│  [✓] "Project files.zip" - 45 MB - Jan 2022     │
│  [✓] "Video recording" - 38 MB - Mar 2021       │
│  [ ] "Tax documents" - 22 MB - Apr 2023         │
│                                                 │
│  "3 selected = 105 MB"                          │
├─────────────────────────────────────────────────┤
│  [Delete Selected] - primary button             │
└─────────────────────────────────────────────────┘
```

**Key UI elements:**
- Size shown prominently for each email
- Running total of selected size
- Easy filters

---

### Screen 10: History

**Purpose:** Show past cleanups, allow recovery if needed.

**Sections:**
```
┌─────────────────────────────────────────────────┐
│  HEADER:                                        │
│  "Cleanup History"                              │
├─────────────────────────────────────────────────┤
│  CLEANUP LIST:                                  │
│  ┌───────────────────────────────────────────┐  │
│  │ Oct 28, 2024                              │  │
│  │ 4,200 emails · 2.1 GB freed               │  │
│  │ [View Details]                            │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │ Sep 15, 2024                              │  │
│  │ 1,800 emails · 890 MB freed               │  │
│  │ [View Details]                            │  │
│  └───────────────────────────────────────────┘  │
├─────────────────────────────────────────────────┤
│  LIFETIME STATS:                                │
│  Total cleaned: 12,400 emails                   │
│  Total freed: 5.8 GB                            │
└─────────────────────────────────────────────────┘
```

---

## 4. UX Principles for Inbox Nuke

### Principle 1: Trust Before Action
> Never delete anything without building user confidence first.

- Always show what's protected before showing what will be deleted
- Use specific numbers, not vague language ("4,200 emails" not "many emails")
- Explain AI reasoning for every decision
- Default to cautious (uncertain = keep, not delete)

### Principle 2: One Primary Action Per Screen
> Every screen has ONE thing the user should do.

- Use visual hierarchy: one big button, everything else secondary
- Don't offer choices unless necessary
- "Start Cleanup" not "Start Cleanup / Customize Settings / View Options"

### Principle 3: Progressive Disclosure
> Simple by default, power features available but hidden.

- First-time users see: Connect → Scan → Quick Clean → Done
- Power users can access: Custom rules, detailed review, export data
- Don't show advanced options until user demonstrates they want them

### Principle 4: Everything is Reversible
> Users should never fear making a mistake.

- All deleted emails go to Gmail Trash (30-day recovery)
- Show "undo" option after every action
- Never use scary language ("permanently delete", "cannot be undone")
- Frame as "clean up" not "delete forever"

### Principle 5: Speed Wins
> The whole flow should take under 5 minutes.

- Quick Clean mode handles 95% of decisions automatically
- Only surface truly uncertain items for review (aim for <50 emails)
- Return users should complete maintenance in under 30 seconds
- Show progress constantly so user knows something is happening

### Principle 6: Transparency Builds Trust
> Show your work.

- Explain why AI classified each email ("you never open these", "marketing sender")
- Show what data we access and why
- Display "auto-protected" categories so users know important emails are safe
- Privacy badge always visible: "100% local - nothing leaves your computer"

### Principle 7: Design for Anxiety
> Users are scared of losing important emails.

- Lead with reassurance, not action
- "Protected" section is more prominent than "Delete" section
- Use green for safe/keep, red only for explicitly confirmed deletions
- Success messages emphasize what was saved, not just what was deleted

### Principle 8: Reduce Decisions
> Every decision is cognitive load.

- Batch similar items: "23 emails from this sender" not 23 individual decisions
- Offer sensible defaults that work for 90% of users
- "Trust AI for the rest" escape hatch when review fatigue hits
- Remember user preferences for future cleanups

---

## Current App vs. Proposed Changes

| Current State | Problem | Proposed Fix |
|--------------|---------|--------------|
| 8 navigation items | Overwhelming, unclear where to start | 4 items max: Dashboard, Cleanup, Space, Settings |
| "Score Emails" page | Technical jargon, confusing purpose | Rename to "Cleanup" with clear flow |
| KEEP/DELETE/UNCERTAIN labels | Too technical | "Safe", "Clean up", "Your call" |
| Review all emails in a list | Overwhelming for 5,000 emails | One-at-a-time card review |
| Multiple ways to delete | Confusing (runs, scoring, attachments) | One cleanup flow, space as separate tool |
| Rules page | Power feature shown to everyone | Hide unless user seeks it out |
| Subscriptions page | Duplicates cleanup functionality | Merge into main cleanup flow |

---

## Metrics That Matter

**Activation:**
- % of users who complete first cleanup within 10 minutes of connecting

**Trust:**
- % of users who choose "Quick Clean" over "Review All"
- % of users who return for a second cleanup

**Value:**
- Average emails cleaned per session
- Average storage freed per user

**Anxiety:**
- % of cleaned emails that users recover from trash (should be <1%)
- Time spent on review screen (shorter = more confident)

---

## Summary: The 5-Minute Promise

The entire experience should deliver on this promise:

> "Connect your Gmail, and in 5 minutes you'll have a clean inbox and peace of mind. No email you care about will be touched. Everything goes to trash first. You're in control."

Every design decision should be evaluated against this promise.
