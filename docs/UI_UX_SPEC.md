# Inbox Nuke Agent - UI/UX Specification
Version 1.0 | Last Updated: November 27, 2024

---

## Table of Contents
1. [Design Philosophy](#design-philosophy)
2. [Design System](#design-system)
3. [Screen Specifications](#screen-specifications)
4. [Component Library](#component-library)
5. [User Flows](#user-flows)
6. [Micro-interactions & Animations](#micro-interactions--animations)
7. [Accessibility Guidelines](#accessibility-guidelines)
8. [Responsive Behavior](#responsive-behavior)

---

## 1. Design Philosophy

### 1.1 Core Principles

**Transparency Through Visibility**
- Users must always know what the agent is doing in real-time
- Every action should be logged and visible
- No "black box" operations - show progress, stats, and actions clearly

**Trust Through Control**
- Give users control over aggressiveness settings
- Provide whitelist capabilities for protected senders
- Show clear confirmation dialogs for destructive actions
- Allow pause/resume/cancel at any time

**Clarity in Complexity**
- Present large numbers (thousands of emails) in digestible formats
- Use visual hierarchies to highlight what matters most
- Progressive disclosure - show details on demand
- Keep the primary actions obvious and accessible

**Speed & Efficiency**
- Minimize clicks to start cleanup
- Real-time updates without manual refresh
- Fast visual feedback for all interactions
- Optimize for the "power user" who wants to get things done quickly

### 1.2 Visual Language

**Aesthetic Direction**
- Modern, clean, minimal interface
- Technology-focused but approachable
- Professional without being corporate
- Energetic but not overwhelming

**Mood & Tone**
- Confident and capable (this agent works)
- Reassuring (your data is safe)
- Empowering (take back control of your inbox)
- Slightly playful (Gmail cleanup doesn't have to be boring)

### 1.3 Color Palette

The color system leverages shadcn/ui's built-in theming with semantic color tokens:

**Primary Colors**
- `primary`: Vibrant blue (#3b82f6) - action buttons, links, progress
- `primary-foreground`: White text on primary backgrounds
- Use for: Start button, active states, primary CTAs

**Semantic Colors**
- `destructive`: Red (#ef4444) - delete actions, warnings
- `success`: Green (#10b981) - completed actions, success states
- `warning`: Amber (#f59e0b) - caution, moderate risk actions
- `muted`: Gray (#6b7280) - secondary text, disabled states

**Neutral Palette (shadcn/ui defaults)**
- `background`: Canvas background (#ffffff / #0a0a0a in dark)
- `foreground`: Primary text color
- `card`: Elevated surface color
- `border`: Subtle borders and dividers
- `muted`: Secondary backgrounds
- `accent`: Highlight color for hover states

**Data Visualization Colors**
- Emails deleted: `blue-500`
- Storage freed: `green-500`
- Senders processed: `purple-500`
- Filters created: `amber-500`

### 1.4 Typography

Use shadcn/ui's typography system with Inter font family:

**Hierarchy**
```css
h1: text-4xl font-bold tracking-tight (36px)
h2: text-3xl font-semibold tracking-tight (30px)
h3: text-2xl font-semibold (24px)
h4: text-xl font-semibold (20px)
body-large: text-base (16px)
body: text-sm (14px)
body-small: text-xs (12px)
```

**Font Weights**
- Headings: 600-700 (semibold to bold)
- Body: 400 (regular)
- Labels: 500 (medium)
- Captions: 400 (regular)

**Special Cases**
- Large numbers (stats): `text-3xl font-bold tabular-nums`
- Timestamps: `text-xs text-muted-foreground`
- Status badges: `text-xs font-medium`

### 1.5 Spacing System

Use Tailwind's spacing scale consistently:

- `xs`: 0.5rem (8px) - tight spacing
- `sm`: 0.75rem (12px) - compact spacing
- `md`: 1rem (16px) - default spacing
- `lg`: 1.5rem (24px) - comfortable spacing
- `xl`: 2rem (32px) - generous spacing
- `2xl`: 3rem (48px) - section spacing

**Component Internal Padding**
- Cards: `p-6`
- Buttons: `px-4 py-2`
- Dialog content: `p-6`
- Table cells: `px-4 py-3`

---

## 2. Design System

### 2.1 shadcn/ui Component Selection

**Core Components to Install**
```bash
npx shadcn-ui@latest init
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add progress
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add table
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add input
npx shadcn-ui@latest add slider
npx shadcn-ui@latest add switch
npx shadcn-ui@latest add select
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add avatar
npx shadcn-ui@latest add separator
npx shadcn-ui@latest add skeleton
npx shadcn-ui@latest add alert
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add scroll-area
```

### 2.2 Custom Components to Build

These extend shadcn/ui components with app-specific logic:

1. **StatCard** - Displays metric with label, value, and trend
2. **ActivityFeedItem** - Single log entry in activity stream
3. **SenderRow** - Table row showing sender details and status
4. **ProgressSection** - Combined progress bar with stats
5. **RunStatusBadge** - Status indicator for cleanup runs
6. **ControlPanel** - Start/pause/resume/cancel buttons
7. **WhitelistManager** - Domain whitelist editor
8. **AggressivenessSlider** - Safety level selector

### 2.3 Icons

Use **Lucide React** (comes with shadcn/ui):

```typescript
import {
  Play, Pause, Square, RotateCcw,  // Controls
  Mail, Trash2, Filter, Shield,     // Actions
  CheckCircle, XCircle, AlertCircle, Clock, // Status
  TrendingUp, TrendingDown,         // Trends
  Search, Settings, History,        // Navigation
  ChevronRight, ChevronDown,        // Accordions
  X, Check, Loader2,                // UI elements
  BarChart3, PieChart,              // Visualizations
  Database, Zap, Gmail              // Branding (use Gmail logo image)
} from 'lucide-react'
```

### 2.4 Dark Mode Support

Leverage shadcn/ui's built-in dark mode:

- All components automatically support dark mode via CSS variables
- Add theme toggle in header (use `next-themes` package)
- Test all screens in both light and dark modes
- Ensure data visualization colors work in both themes
- Use `dark:` Tailwind modifiers for custom components

**Theme Toggle Component**
```tsx
import { Moon, Sun } from 'lucide-react'
import { useTheme } from 'next-themes'
import { Button } from '@/components/ui/button'

// Place in header/navigation
```

---

## 3. Screen Specifications

### 3.1 Onboarding / Home Screen

**Purpose**: First-time user experience and Gmail connection

**Layout Structure**
```
┌─────────────────────────────────────────┐
│  Header (Logo + Theme Toggle)           │
├─────────────────────────────────────────┤
│                                         │
│          [Centered Content]             │
│                                         │
│   Logo / Illustration                   │
│   Headline                              │
│   Subheadline                           │
│   "Connect Gmail" Button (Primary)      │
│   Feature bullets                       │
│                                         │
│                                         │
└─────────────────────────────────────────┘
```

**Component Breakdown**

1. **Header** (fixed top)
   - Logo/App name (left)
   - Theme toggle button (right)
   - Component: Custom header with `Button` for theme toggle

2. **Hero Section** (centered, max-w-2xl)
   - App icon/illustration (optional)
   - H1: "Take Back Your Inbox"
   - Subtitle: "Automatically unsubscribe from mailing lists, delete old newsletters, and free up Gmail storage—all running locally on your computer."
   - Component: Custom layout with typography components

3. **Primary CTA**
   - Large `Button` variant="default" size="lg"
   - Icon: Gmail logo or `<Mail />`
   - Text: "Connect Gmail to Get Started"
   - onClick: Triggers OAuth flow → `/auth/google/start`

4. **Feature List** (3-column grid on desktop, stacked on mobile)
   - Each feature: Icon + heading + description
   - Icons: `<Shield>`, `<Zap>`, `<Database>`
   - Features:
     - "100% Local" - Your data never leaves your computer
     - "Fully Autonomous" - Runs on autopilot once configured
     - "Real-time Progress" - Watch cleanup happen live
   - Component: Custom feature card using `Card`

**States**

| State | Behavior |
|-------|----------|
| Default | Show "Connect Gmail" button enabled |
| Loading | Button shows `<Loader2>` spinner, text "Connecting..." |
| Connected | Redirect to `/dashboard` |
| Error | Show `Toast` with error message, keep button enabled |

**Responsive Behavior**

- Desktop (1024px+): Centered content, max-width 800px, feature grid 3 columns
- Tablet (768px-1023px): Centered content, feature grid 2 columns
- Mobile (<768px): Full-width padding, feature list stacked (1 column)

**User Interaction Flow**
1. User lands on page
2. Reads value proposition
3. Clicks "Connect Gmail"
4. Redirected to Google OAuth consent screen (external)
5. User grants permissions
6. Redirected back to app → `/dashboard`

**First-Time vs. Returning User**
- If Gmail already connected (check on mount): Auto-redirect to `/dashboard`
- Show toast: "Already connected as user@gmail.com"

---

### 3.2 Dashboard (Main Control Center)

**Purpose**: Primary interface for monitoring and controlling cleanup operations

**Layout Structure**
```
┌────────────────────────────────────────────────────────────┐
│  Header: Logo | Dashboard | Senders | History | Settings  │
├────────────────────────────────────────────────────────────┤
│  Breadcrumb: Dashboard                                     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Control Panel                                       │ │
│  │  [Start Cleanup] or [Pause][Resume][Cancel]          │ │
│  │  Status: Idle / Running / Paused / Completed         │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│  │ Stat 1  │ │ Stat 2  │ │ Stat 3  │ │ Stat 4  │        │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘        │
│                                                            │
│  ┌──────────────────────┐ ┌──────────────────────┐       │
│  │ Progress Section     │ │ Activity Feed        │       │
│  │ (if run active)      │ │ (Live Log)           │       │
│  │                      │ │                      │       │
│  │                      │ │                      │       │
│  └──────────────────────┘ └──────────────────────┘       │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Component Breakdown**

#### 1. Navigation Header
- Component: Custom nav with shadcn `Button` variants
- Items: Dashboard (active), Senders, History, Settings
- Right side: User avatar (first initial), theme toggle, settings icon
- Sticky positioning on scroll

#### 2. Control Panel Card
- Component: `Card` with `CardHeader` and `CardContent`
- **Title**: "Cleanup Controls"
- **Content**:
  - Status badge (large, prominent)
  - Primary action button(s)
  - Last run timestamp (if exists)

**Button States**:

| Status | Buttons Shown | Appearance |
|--------|---------------|------------|
| Idle (no active run) | `[Start Cleanup]` | Button variant="default", size="lg", icon=`<Play>` |
| Running | `[Pause]` `[Cancel]` | Pause: variant="secondary", Cancel: variant="destructive" |
| Paused | `[Resume]` `[Cancel]` | Resume: variant="default", Cancel: variant="destructive" |
| Completed | `[Start New Cleanup]` | variant="default" |

#### 3. Stats Cards (4-grid layout)

Each stat card displays:
- Icon (color-coded)
- Large number (primary metric)
- Label (what it represents)
- Trend indicator (optional: up/down arrow + %)

**Card 1: Emails Deleted**
```tsx
<Card>
  <CardContent className="pt-6">
    <div className="flex items-center justify-between">
      <Mail className="h-8 w-8 text-blue-500" />
      <TrendingUp className="h-4 w-4 text-green-500" />
    </div>
    <div className="mt-4">
      <div className="text-3xl font-bold tabular-nums">
        {emailsDeleted.toLocaleString()}
      </div>
      <p className="text-xs text-muted-foreground mt-1">
        Emails Deleted
      </p>
    </div>
  </CardContent>
</Card>
```

**Stat Cards**:
1. **Emails Deleted** - Icon: `<Mail>`, Color: blue-500
2. **Storage Freed** - Icon: `<Database>`, Color: green-500, Format: GB/MB
3. **Senders Processed** - Icon: `<Filter>`, Color: purple-500
4. **Filters Created** - Icon: `<Shield>`, Color: amber-500

Component: Custom `StatCard` component wrapping shadcn `Card`

#### 4. Progress Section (shown only during active run)

- Component: `Card` with title "Cleanup Progress"
- Overall progress bar showing % complete
- Sub-stats:
  - Current phase (e.g., "Unsubscribing from senders")
  - Items processed / total
  - Estimated time remaining (optional)

**Layout**:
```tsx
<Card>
  <CardHeader>
    <CardTitle>Cleanup Progress</CardTitle>
    <CardDescription>
      Processing sender {currentIndex} of {totalSenders}
    </CardDescription>
  </CardHeader>
  <CardContent>
    <Progress value={progressPercent} className="mb-4" />
    <div className="grid grid-cols-2 gap-4 text-sm">
      <div>
        <span className="text-muted-foreground">Phase:</span>
        <span className="ml-2 font-medium">{currentPhase}</span>
      </div>
      <div>
        <span className="text-muted-foreground">Completion:</span>
        <span className="ml-2 font-medium">{progressPercent}%</span>
      </div>
    </div>
  </CardContent>
</Card>
```

Component: Custom `ProgressSection` using shadcn `Progress`, `Card`

#### 5. Activity Feed (Live Log)

- Component: `Card` with `ScrollArea`
- Title: "Activity Log"
- Shows last 50 actions in reverse chronological order
- Each entry: timestamp, icon, message, metadata

**Activity Item Structure**:
```tsx
<div className="flex items-start gap-3 py-3 border-b last:border-0">
  <div className="mt-0.5">
    {getActionIcon(action.type)} {/* CheckCircle, Trash2, Filter, etc */}
  </div>
  <div className="flex-1 space-y-1">
    <p className="text-sm font-medium">{action.message}</p>
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <Clock className="h-3 w-3" />
      <span>{formatTimestamp(action.timestamp)}</span>
      {action.metadata && (
        <Badge variant="secondary" className="text-xs">
          {action.metadata}
        </Badge>
      )}
    </div>
  </div>
</div>
```

**Action Types & Icons**:
- Unsubscribe: `<CheckCircle>` green
- Delete emails: `<Trash2>` red
- Create filter: `<Filter>` blue
- Error: `<XCircle>` red
- Warning: `<AlertCircle>` amber

Component: Custom `ActivityFeedItem` component, using `ScrollArea` for container

**Auto-scroll Behavior**:
- New items appear at top
- Auto-scroll to top when new item added (unless user has scrolled manually)
- Show "New activity" badge if user scrolled away

#### 6. Empty States

**When no run has ever started**:
- Replace progress + activity feed with centered empty state
- Icon: `<Zap>` large, muted
- Message: "No cleanup runs yet"
- Subtext: "Click 'Start Cleanup' to begin cleaning your inbox"
- Component: Custom empty state with illustration

**Responsive Behavior**

- Desktop (1280px+): 4-column stat grid, progress + feed side-by-side (60/40 split)
- Tablet (768px-1279px): 2-column stat grid, progress + feed stacked
- Mobile (<768px): 1-column stat grid, full-width cards, compact padding

**Polling Behavior**

- Frontend polls `GET /runs/current` every 2 seconds when run is active
- Updates stats, progress, and activity feed in real-time
- Stop polling when run status is "completed", "cancelled", or "error"
- Show loading skeleton on initial load

---

### 3.3 Active Run View

**Purpose**: Full-screen immersive view during active cleanup (optional enhancement)

**Note**: This can be the same as Dashboard with enhanced visuals, or a separate route `/run/:id`

**Layout Structure**
```
┌────────────────────────────────────────────────────────────┐
│  [Minimize to dashboard] [Pause] [Cancel]                  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│              LARGE PROGRESS CIRCLE/BAR                     │
│              42% Complete                                  │
│              128 / 305 Senders Processed                   │
│                                                            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│  │ Stat 1  │ │ Stat 2  │ │ Stat 3  │ │ Stat 4  │        │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘        │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Live Activity Stream (auto-scrolling)              │ │
│  │  • Unsubscribed from newsletter@example.com          │ │
│  │  • Deleted 245 emails from sender@domain.com         │ │
│  │  • Created filter for updates@company.com            │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Component Breakdown**

1. **Header Controls**
   - Minimal header with action buttons only
   - Buttons: "Minimize" (back to dashboard), "Pause", "Cancel"
   - Component: Custom header with shadcn `Button`

2. **Hero Progress Indicator**
   - Large circular or linear progress visualization
   - Central percentage (e.g., "42%")
   - Items processed count below
   - Component: Enhanced `Progress` or custom circular progress with shadcn primitives

3. **Stats Grid**
   - Same as dashboard stats but slightly larger
   - Animated number counting up as values change

4. **Activity Stream**
   - Full-width auto-scrolling feed
   - Larger text, more prominent icons
   - Smooth animations as new items appear

**States & Interactions**

- Pause: Freeze progress, show "Paused" badge, enable Resume button
- Cancel: Show confirmation dialog before cancelling
- Complete: Show success screen with summary, "View Details" and "Start New Run" buttons

**Animation & Motion**

- Progress bar animates smoothly (not jumpy)
- Numbers count up with easing (use `react-countup` or similar)
- Activity items slide in from top
- Success confetti or celebration animation on completion (optional)

---

### 3.4 Senders List Screen

**Purpose**: Browse and manage discovered mailing list senders

**Layout Structure**
```
┌────────────────────────────────────────────────────────────┐
│  Navigation Header                                         │
├────────────────────────────────────────────────────────────┤
│  Breadcrumb: Dashboard > Senders                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Senders (1,234)                             [+ Whitelist] │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Search: [____________] Filters: [All ▾] [Sort ▾]     │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Table:                                               │ │
│  │ ┌─────────┬──────┬────────┬──────────┬─────────────┐│ │
│  │ │ Sender  │Count │Status  │Last Seen │Actions      ││ │
│  │ ├─────────┼──────┼────────┼──────────┼─────────────┤│ │
│  │ │ news@.. │ 1.2k │Unsub ✓│ 2d ago   │[Whitelist]  ││ │
│  │ │ promo@..│  847 │Muted  │ 1w ago   │[Whitelist]  ││ │
│  │ └─────────┴──────┴────────┴──────────┴─────────────┘│ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  Pagination: < 1 2 3 ... 42 >                             │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Component Breakdown**

#### 1. Page Header
- Title: "Senders" with count badge
- Action button: "+ Add to Whitelist" (opens dialog to manually add domain)
- Component: Custom page header

#### 2. Filters & Search Bar
- Component: `Input` with search icon for search
- Filters dropdown: `Select` component
  - All Senders
  - Unsubscribed
  - Not Unsubscribed
  - Has Filter
  - Whitelisted
- Sort dropdown: `Select` component
  - Most emails (default)
  - Recently seen
  - Alphabetical

#### 3. Senders Table
- Component: shadcn `Table`
- Columns:
  1. **Sender** - Email address + domain
  2. **Message Count** - Number formatted (e.g., "1.2k")
  3. **Status** - Badge showing unsubscribe/filter status
  4. **Last Seen** - Relative time (e.g., "2 days ago")
  5. **Actions** - Dropdown menu with options

**Table Row Example**:
```tsx
<TableRow>
  <TableCell>
    <div className="flex items-center gap-2">
      <Avatar className="h-8 w-8">
        <AvatarFallback>{getInitial(sender.email)}</AvatarFallback>
      </Avatar>
      <div>
        <div className="font-medium">{sender.email}</div>
        <div className="text-xs text-muted-foreground">{sender.domain}</div>
      </div>
    </div>
  </TableCell>
  <TableCell className="tabular-nums">
    {formatNumber(sender.messageCount)}
  </TableCell>
  <TableCell>
    <div className="flex gap-1">
      {sender.unsubscribed && (
        <Badge variant="success">Unsubscribed</Badge>
      )}
      {sender.filterCreated && (
        <Badge variant="secondary">Filtered</Badge>
      )}
    </div>
  </TableCell>
  <TableCell className="text-muted-foreground">
    {formatRelativeTime(sender.lastSeen)}
  </TableCell>
  <TableCell>
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm">
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuItem onClick={() => addToWhitelist(sender)}>
          <Shield className="mr-2 h-4 w-4" />
          Add to Whitelist
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => viewDetails(sender)}>
          <ExternalLink className="mr-2 h-4 w-4" />
          View Details
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  </TableCell>
</TableRow>
```

**Status Badges**:
- Unsubscribed: Green badge with checkmark
- Filtered: Blue badge
- Whitelisted: Amber badge with shield icon
- Pending: Gray badge

#### 4. Pagination
- Component: shadcn pagination component (custom build)
- Shows page numbers + prev/next
- Items per page: 50 (fixed for MVP, can add selector later)

**Empty State**
- When no senders found (after search/filter)
- Icon: `<Search>` muted
- Message: "No senders found"
- Clear filters button

**Responsive Behavior**

- Desktop: Full table with all columns
- Tablet: Hide "Last Seen" column
- Mobile: Card-based layout instead of table, show key info only

---

### 3.5 Run History Screen

**Purpose**: View past cleanup runs with detailed stats

**Layout Structure**
```
┌────────────────────────────────────────────────────────────┐
│  Navigation Header                                         │
├────────────────────────────────────────────────────────────┤
│  Breadcrumb: Dashboard > History                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Run History                                               │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Run #42 - Completed                   Dec 15, 2024   │ │
│  │ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │ │
│  │ │ 12.4k   │ │ 8.2 GB  │ │ 305     │ │ 280     │    │ │
│  │ │ Deleted │ │ Freed   │ │ Senders │ │ Filters │    │ │
│  │ └─────────┘ └─────────┘ └─────────┘ └─────────┘    │ │
│  │ Duration: 24m 15s              [View Details →]     │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Run #41 - Cancelled                   Dec 10, 2024   │ │
│  │ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │ │
│  │ │ 3.2k    │ │ 2.1 GB  │ │ 98      │ │ 85      │    │ │
│  │ │ Deleted │ │ Freed   │ │ Senders │ │ Filters │    │ │
│  │ └─────────┘ └─────────┘ └─────────┘ └─────────┘    │ │
│  │ Duration: 8m 42s (stopped early)   [View Details →] │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Component Breakdown**

#### 1. Run Card (List Item)
- Component: `Card` with expandable sections
- Header shows:
  - Run number/ID
  - Status badge (Completed, Cancelled, Failed)
  - Date/time
- Stats grid: 4 mini stat cards (inline)
- Footer: Duration + "View Details" link
- Component: Custom `RunHistoryCard`

**Run Status Badge Colors**:
- Completed: Green (`success`)
- Cancelled: Gray (`secondary`)
- Failed: Red (`destructive`)
- Running: Blue (`default`) - shouldn't appear in history

#### 2. View Details (Drill-down)

Clicking "View Details" navigates to `/history/:runId` showing:
- Full run metadata
- Complete activity log for that run
- Breakdown by sender
- Download CSV option (export run data)

**Layout for Detail View**:
```tsx
<div className="space-y-6">
  {/* Summary Card */}
  <Card>
    <CardHeader>
      <CardTitle>Run #{runId} - Completed</CardTitle>
      <CardDescription>
        Started: {startTime} • Ended: {endTime} • Duration: {duration}
      </CardDescription>
    </CardHeader>
    <CardContent>
      {/* 4-column stat grid */}
    </CardContent>
  </Card>

  {/* Activity Log */}
  <Card>
    <CardHeader>
      <CardTitle>Activity Log</CardTitle>
      <Button variant="outline" size="sm">
        <Download className="mr-2 h-4 w-4" />
        Export CSV
      </Button>
    </CardHeader>
    <CardContent>
      <ScrollArea className="h-[500px]">
        {/* Activity items */}
      </ScrollArea>
    </CardContent>
  </Card>
</div>
```

**Empty State**
- When no runs exist
- Icon: `<History>` muted
- Message: "No cleanup runs yet"
- CTA: "Start your first cleanup" button → back to dashboard

---

### 3.6 Settings Screen

**Purpose**: Configure whitelist, aggressiveness, and safety preferences

**Layout Structure**
```
┌────────────────────────────────────────────────────────────┐
│  Navigation Header                                         │
├────────────────────────────────────────────────────────────┤
│  Breadcrumb: Dashboard > Settings                          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Settings                                                  │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Safety Settings                                      │ │
│  │                                                      │ │
│  │ Aggressiveness Level: [●--------] Conservative      │ │
│  │ • Protects financial, government, healthcare emails │ │
│  │ • Requires explicit List-Unsubscribe header         │ │
│  │                                                      │ │
│  │ [✓] Skip emails with keywords: invoice, receipt...  │ │
│  │ [✓] Keep emails from last 30 days                   │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Whitelist Management                                 │ │
│  │                                                      │ │
│  │ Protected domains (12)              [+ Add Domain]  │ │
│  │ ┌────────────────────────────────────────────────┐  │ │
│  │ │ example.com               [Reason] [Remove]    │  │ │
│  │ │ important-sender.com      [Reason] [Remove]    │  │ │
│  │ └────────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Gmail Connection                                     │ │
│  │                                                      │ │
│  │ Connected as: user@gmail.com         [Disconnect]   │ │
│  │ Last synced: 2 minutes ago                          │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  [Save Changes]                                           │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Component Breakdown**

#### 1. Safety Settings Card
- Component: `Card`
- **Aggressiveness Slider**
  - Component: shadcn `Slider`
  - Range: 0-100 (or 1-5 levels)
  - Labels: Conservative, Moderate, Aggressive
  - Shows description of current level below slider
  - Impacts deletion criteria and safety checks

**Aggressiveness Levels**:
| Level | Description | Behavior |
|-------|-------------|----------|
| Conservative | Maximum safety | Only unsubscribe from senders with explicit List-Unsubscribe header, keep all emails <90 days, strict keyword blocking |
| Moderate | Balanced approach | Unsubscribe from high-frequency senders, delete emails >30 days, standard keyword blocking |
| Aggressive | Maximum cleanup | Unsubscribe from all bulk senders, delete emails >7 days, minimal keyword blocking |

- **Safety Toggles**
  - Component: shadcn `Switch` with labels
  - Options:
    - Skip protected keywords (invoice, receipt, bank, etc.)
    - Preserve recent emails (with days input)
    - Require List-Unsubscribe header
    - Backup before deletion (future: export to .mbox)

#### 2. Whitelist Management Card
- Component: `Card`
- Shows count of whitelisted domains
- **Add Domain Button**
  - Opens `Dialog` to add new domain
  - Input: domain (e.g., "example.com")
  - Input: reason (optional text)
  - Validates domain format

**Whitelist Item**:
```tsx
<div className="flex items-center justify-between py-2 border-b">
  <div className="flex items-center gap-2">
    <Shield className="h-4 w-4 text-amber-500" />
    <span className="font-medium">{domain}</span>
  </div>
  <div className="flex items-center gap-2">
    {reason && (
      <Badge variant="secondary" className="text-xs">
        {reason}
      </Badge>
    )}
    <Button
      variant="ghost"
      size="sm"
      onClick={() => removeFromWhitelist(domain)}
    >
      <X className="h-4 w-4" />
    </Button>
  </div>
</div>
```

Component: Custom `WhitelistItem` using shadcn primitives

**Add Domain Dialog**:
```tsx
<Dialog>
  <DialogTrigger asChild>
    <Button variant="outline">
      <Plus className="mr-2 h-4 w-4" />
      Add Domain
    </Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Add to Whitelist</DialogTitle>
      <DialogDescription>
        This domain will never be unsubscribed or deleted
      </DialogDescription>
    </DialogHeader>
    <div className="space-y-4">
      <div>
        <Label htmlFor="domain">Domain</Label>
        <Input
          id="domain"
          placeholder="example.com"
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
        />
      </div>
      <div>
        <Label htmlFor="reason">Reason (optional)</Label>
        <Input
          id="reason"
          placeholder="Important business contact"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
      </div>
    </div>
    <DialogFooter>
      <Button variant="outline" onClick={onCancel}>Cancel</Button>
      <Button onClick={onAddDomain}>Add to Whitelist</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

#### 3. Gmail Connection Card
- Shows connected account email
- Last sync timestamp
- Disconnect button (with confirmation)
- Component: `Card` with `Alert` for connection status

**Disconnect Confirmation**:
```tsx
<AlertDialog>
  <AlertDialogTrigger asChild>
    <Button variant="destructive">Disconnect Gmail</Button>
  </AlertDialogTrigger>
  <AlertDialogContent>
    <AlertDialogHeader>
      <AlertDialogTitle>Disconnect Gmail?</AlertDialogTitle>
      <AlertDialogDescription>
        This will remove access to your Gmail account.
        You'll need to reconnect to use Inbox Nuke.
      </AlertDialogDescription>
    </AlertDialogHeader>
    <AlertDialogFooter>
      <AlertDialogCancel>Cancel</AlertDialogCancel>
      <AlertDialogAction onClick={onDisconnect}>
        Disconnect
      </AlertDialogAction>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
```

#### 4. Save Changes Button
- Fixed bottom-right on desktop (sticky)
- Full-width on mobile
- Component: `Button` variant="default" size="lg"
- Shows only when settings have changed (dirty state)
- Loading state while saving

**Settings State Management**
- Local state for form values
- Compare with server state to show "unsaved changes"
- Optimistic updates with rollback on error
- Toast notification on successful save

---

## 4. Component Library

### 4.1 StatCard Component

**Purpose**: Display a metric with icon, value, label, and optional trend

**Props**:
```typescript
interface StatCardProps {
  icon: React.ReactNode
  label: string
  value: string | number
  trend?: {
    direction: 'up' | 'down'
    value: string
  }
  color?: 'blue' | 'green' | 'purple' | 'amber' | 'red'
}
```

**Usage**:
```tsx
<StatCard
  icon={<Mail className="h-8 w-8" />}
  label="Emails Deleted"
  value={12458}
  trend={{ direction: 'up', value: '+15%' }}
  color="blue"
/>
```

**Implementation**:
```tsx
export function StatCard({ icon, label, value, trend, color = 'blue' }: StatCardProps) {
  const colorClasses = {
    blue: 'text-blue-500',
    green: 'text-green-500',
    purple: 'text-purple-500',
    amber: 'text-amber-500',
    red: 'text-red-500',
  }

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div className={colorClasses[color]}>
            {icon}
          </div>
          {trend && (
            <div className={cn(
              "flex items-center gap-1 text-sm",
              trend.direction === 'up' ? 'text-green-600' : 'text-red-600'
            )}>
              {trend.direction === 'up' ? (
                <TrendingUp className="h-4 w-4" />
              ) : (
                <TrendingDown className="h-4 w-4" />
              )}
              <span>{trend.value}</span>
            </div>
          )}
        </div>
        <div className="mt-4">
          <div className="text-3xl font-bold tabular-nums">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            {label}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
```

---

### 4.2 ActivityFeedItem Component

**Purpose**: Single activity log entry with icon, message, and timestamp

**Props**:
```typescript
interface ActivityFeedItemProps {
  action: {
    type: 'unsubscribe' | 'delete' | 'filter' | 'error' | 'warning'
    message: string
    timestamp: string
    metadata?: string
  }
}
```

**Usage**:
```tsx
<ActivityFeedItem
  action={{
    type: 'unsubscribe',
    message: 'Unsubscribed from newsletter@example.com',
    timestamp: '2024-12-15T10:30:00Z',
    metadata: '245 emails'
  }}
/>
```

**Implementation**:
```tsx
export function ActivityFeedItem({ action }: ActivityFeedItemProps) {
  const getIcon = (type: string) => {
    switch (type) {
      case 'unsubscribe':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'delete':
        return <Trash2 className="h-4 w-4 text-red-500" />
      case 'filter':
        return <Filter className="h-4 w-4 text-blue-500" />
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'warning':
        return <AlertCircle className="h-4 w-4 text-amber-500" />
      default:
        return <Circle className="h-4 w-4 text-gray-500" />
    }
  }

  return (
    <div className="flex items-start gap-3 py-3 border-b last:border-0">
      <div className="mt-0.5">
        {getIcon(action.type)}
      </div>
      <div className="flex-1 space-y-1">
        <p className="text-sm font-medium">{action.message}</p>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" />
          <span>{formatRelativeTime(action.timestamp)}</span>
          {action.metadata && (
            <Badge variant="secondary" className="text-xs">
              {action.metadata}
            </Badge>
          )}
        </div>
      </div>
    </div>
  )
}
```

---

### 4.3 ProgressSection Component

**Purpose**: Display overall cleanup progress with stats

**Props**:
```typescript
interface ProgressSectionProps {
  progressPercent: number
  currentPhase: string
  currentIndex: number
  totalItems: number
  estimatedTimeRemaining?: string
}
```

**Usage**:
```tsx
<ProgressSection
  progressPercent={42}
  currentPhase="Unsubscribing from senders"
  currentIndex={128}
  totalItems={305}
  estimatedTimeRemaining="18m"
/>
```

**Implementation**: (See Dashboard section above)

---

### 4.4 RunStatusBadge Component

**Purpose**: Visual indicator for run status

**Props**:
```typescript
interface RunStatusBadgeProps {
  status: 'idle' | 'running' | 'paused' | 'completed' | 'cancelled' | 'failed'
  size?: 'sm' | 'md' | 'lg'
}
```

**Usage**:
```tsx
<RunStatusBadge status="running" size="lg" />
```

**Implementation**:
```tsx
export function RunStatusBadge({ status, size = 'md' }: RunStatusBadgeProps) {
  const config = {
    idle: { label: 'Idle', variant: 'secondary', icon: Clock },
    running: { label: 'Running', variant: 'default', icon: Loader2 },
    paused: { label: 'Paused', variant: 'secondary', icon: Pause },
    completed: { label: 'Completed', variant: 'success', icon: CheckCircle },
    cancelled: { label: 'Cancelled', variant: 'secondary', icon: XCircle },
    failed: { label: 'Failed', variant: 'destructive', icon: AlertCircle },
  }

  const { label, variant, icon: Icon } = config[status]
  const sizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base px-4 py-2',
  }

  return (
    <Badge variant={variant as any} className={sizeClasses[size]}>
      <Icon className={cn(
        "mr-1",
        size === 'sm' ? 'h-3 w-3' : 'h-4 w-4',
        status === 'running' && 'animate-spin'
      )} />
      {label}
    </Badge>
  )
}
```

---

### 4.5 ControlPanel Component

**Purpose**: Start/pause/resume/cancel buttons based on run status

**Props**:
```typescript
interface ControlPanelProps {
  status: 'idle' | 'running' | 'paused' | 'completed'
  onStart: () => void
  onPause: () => void
  onResume: () => void
  onCancel: () => void
  disabled?: boolean
}
```

**Usage**:
```tsx
<ControlPanel
  status={runStatus}
  onStart={handleStart}
  onPause={handlePause}
  onResume={handleResume}
  onCancel={handleCancel}
/>
```

**Implementation**:
```tsx
export function ControlPanel({
  status,
  onStart,
  onPause,
  onResume,
  onCancel,
  disabled = false,
}: ControlPanelProps) {
  return (
    <div className="flex items-center gap-3">
      {status === 'idle' || status === 'completed' ? (
        <Button
          size="lg"
          onClick={onStart}
          disabled={disabled}
        >
          <Play className="mr-2 h-5 w-5" />
          {status === 'completed' ? 'Start New Cleanup' : 'Start Cleanup'}
        </Button>
      ) : null}

      {status === 'running' ? (
        <>
          <Button
            variant="secondary"
            size="lg"
            onClick={onPause}
            disabled={disabled}
          >
            <Pause className="mr-2 h-5 w-5" />
            Pause
          </Button>
          <Button
            variant="destructive"
            size="lg"
            onClick={onCancel}
            disabled={disabled}
          >
            <Square className="mr-2 h-5 w-5" />
            Cancel
          </Button>
        </>
      ) : null}

      {status === 'paused' ? (
        <>
          <Button
            size="lg"
            onClick={onResume}
            disabled={disabled}
          >
            <Play className="mr-2 h-5 w-5" />
            Resume
          </Button>
          <Button
            variant="destructive"
            size="lg"
            onClick={onCancel}
            disabled={disabled}
          >
            <Square className="mr-2 h-5 w-5" />
            Cancel
          </Button>
        </>
      ) : null}
    </div>
  )
}
```

---

### 4.6 AggressivenessSlider Component

**Purpose**: Configure cleanup aggressiveness level with descriptions

**Props**:
```typescript
interface AggressivenessSliderProps {
  value: number // 0-100
  onChange: (value: number) => void
}
```

**Implementation**:
```tsx
export function AggressivenessSlider({ value, onChange }: AggressivenessSliderProps) {
  const getLevel = (val: number) => {
    if (val < 33) return { label: 'Conservative', description: 'Maximum safety. Only unsubscribe from explicit senders.' }
    if (val < 67) return { label: 'Moderate', description: 'Balanced approach. Delete emails older than 30 days.' }
    return { label: 'Aggressive', description: 'Maximum cleanup. Delete emails older than 7 days.' }
  }

  const level = getLevel(value)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Label>Aggressiveness Level</Label>
        <Badge variant="secondary">{level.label}</Badge>
      </div>
      <Slider
        value={[value]}
        onValueChange={([v]) => onChange(v)}
        max={100}
        step={1}
        className="w-full"
      />
      <p className="text-sm text-muted-foreground">
        {level.description}
      </p>
    </div>
  )
}
```

---

## 5. User Flows

### 5.1 First-Time Setup Flow

```
1. User opens http://localhost:3000
   ↓
2. Lands on Onboarding/Home screen
   ↓
3. Reads value proposition
   ↓
4. Clicks "Connect Gmail"
   ↓
5. Redirected to Google OAuth consent screen (external)
   ↓
6. User reviews permissions and clicks "Allow"
   ↓
7. Redirected back to app with auth code
   ↓
8. Backend exchanges code for tokens, saves to SQLite
   ↓
9. Frontend redirects to Dashboard
   ↓
10. Shows success toast: "Gmail connected successfully!"
```

**Error Handling**:
- OAuth denied: Show toast "Gmail connection cancelled", stay on home screen
- OAuth error: Show toast with error message, keep "Connect Gmail" button enabled
- Network error: Show toast "Connection failed. Please try again."

---

### 5.2 Starting a Cleanup Run

```
1. User on Dashboard, run status = 'idle'
   ↓
2. Clicks "Start Cleanup" button
   ↓
3. Button shows loading spinner ("Starting...")
   ↓
4. API call: POST /runs
   ↓
5. Backend creates run, starts agent
   ↓
6. Frontend receives run ID and initial status
   ↓
7. Dashboard updates:
   - Status badge changes to "Running"
   - Control panel shows "Pause" and "Cancel" buttons
   - Progress section appears
   - Activity feed starts showing logs
   ↓
8. Frontend starts polling every 2 seconds
   ↓
9. Stats update in real-time as agent works
```

**Pause/Resume Flow**:
```
User clicks "Pause"
   ↓
API call: POST /runs/{id}/pause
   ↓
Backend pauses agent
   ↓
Status badge: "Paused"
   ↓
Control panel: "Resume" + "Cancel" buttons
   ↓
User clicks "Resume"
   ↓
API call: POST /runs/{id}/resume
   ↓
Agent continues from cursor position
```

**Cancel Flow**:
```
User clicks "Cancel"
   ↓
Confirmation dialog appears:
  "Cancel cleanup? Progress will be saved but the run will stop."
   ↓
User confirms
   ↓
API call: POST /runs/{id}/cancel
   ↓
Backend stops agent gracefully
   ↓
Status: "Cancelled"
   ↓
Show summary toast with stats
   ↓
Control panel: "Start New Cleanup" button
```

---

### 5.3 Monitoring Progress

```
Run is active
   ↓
Dashboard polls GET /runs/{id} every 2 seconds
   ↓
Backend returns:
  - Current progress %
  - Senders processed / total
  - Emails deleted
  - Storage freed
  - Recent actions (last 50)
   ↓
Frontend updates:
  - Progress bar animates to new %
  - Stat cards count up to new values
  - Activity feed prepends new items
  - Scroll to top if user hasn't manually scrolled
   ↓
Loop continues until status = 'completed' | 'cancelled' | 'failed'
```

**Completion Flow**:
```
Run status changes to 'completed'
   ↓
Frontend stops polling
   ↓
Show celebration animation (optional)
   ↓
Display toast: "Cleanup completed! Deleted X emails, freed Y GB"
   ↓
Status badge: "Completed"
   ↓
Control panel: "Start New Cleanup"
   ↓
Progress section remains visible (frozen at 100%)
```

---

### 5.4 Managing Whitelist

```
User navigates to Settings
   ↓
Scrolls to "Whitelist Management" card
   ↓
Clicks "+ Add Domain"
   ↓
Dialog opens
   ↓
User enters:
  - Domain: "important-sender.com"
  - Reason: "Critical business updates"
   ↓
Clicks "Add to Whitelist"
   ↓
API call: POST /whitelist
   ↓
Backend validates and adds to database
   ↓
Dialog closes
   ↓
Whitelist table updates to show new domain
   ↓
Show toast: "Domain added to whitelist"
```

**Remove from Whitelist**:
```
User clicks "X" button next to domain
   ↓
Confirmation dialog: "Remove from whitelist?"
   ↓
User confirms
   ↓
API call: DELETE /whitelist/{domain}
   ↓
Item removed from table
   ↓
Show toast: "Domain removed from whitelist"
```

---

### 5.5 Viewing Historical Runs

```
User clicks "History" in navigation
   ↓
Lands on Run History screen
   ↓
Sees list of past runs (most recent first)
   ↓
Each run shows summary stats
   ↓
User clicks "View Details →" on a run
   ↓
Navigates to /history/{runId}
   ↓
Shows full run details:
  - Complete metadata
  - All action logs
  - Breakdown by sender
   ↓
User clicks "Export CSV"
   ↓
Downloads CSV file with run data
```

---

## 6. Micro-interactions & Animations

### 6.1 Loading States

**Button Loading**
```tsx
<Button disabled={isLoading}>
  {isLoading ? (
    <>
      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
      Loading...
    </>
  ) : (
    <>
      <Play className="mr-2 h-4 w-4" />
      Start Cleanup
    </>
  )}
</Button>
```

**Skeleton Loading (Initial Page Load)**
```tsx
import { Skeleton } from '@/components/ui/skeleton'

<Card>
  <CardContent className="pt-6">
    <Skeleton className="h-8 w-8 rounded-full" />
    <Skeleton className="h-10 w-24 mt-4" />
    <Skeleton className="h-4 w-32 mt-2" />
  </CardContent>
</Card>
```

**Table Loading**
```tsx
{isLoading ? (
  Array.from({ length: 5 }).map((_, i) => (
    <TableRow key={i}>
      <TableCell><Skeleton className="h-4 w-48" /></TableCell>
      <TableCell><Skeleton className="h-4 w-16" /></TableCell>
      <TableCell><Skeleton className="h-4 w-24" /></TableCell>
    </TableRow>
  ))
) : (
  senders.map(sender => <SenderRow key={sender.id} sender={sender} />)
)}
```

---

### 6.2 Success/Error States

**Toast Notifications**
```tsx
import { useToast } from '@/components/ui/use-toast'

const { toast } = useToast()

// Success
toast({
  title: "Cleanup completed!",
  description: "Deleted 12,458 emails and freed 8.2 GB",
  variant: "default",
})

// Error
toast({
  title: "Something went wrong",
  description: "Failed to start cleanup. Please try again.",
  variant: "destructive",
})

// Warning
toast({
  title: "Run paused",
  description: "You can resume anytime from the dashboard.",
  variant: "default",
})
```

**Inline Error States**
```tsx
{error && (
  <Alert variant="destructive">
    <AlertCircle className="h-4 w-4" />
    <AlertTitle>Error</AlertTitle>
    <AlertDescription>{error.message}</AlertDescription>
  </Alert>
)}
```

---

### 6.3 Number Counting Animation

Use `react-countup` or similar for animated number updates:

```tsx
import CountUp from 'react-countup'

<div className="text-3xl font-bold tabular-nums">
  <CountUp
    start={prevValue}
    end={currentValue}
    duration={0.5}
    separator=","
  />
</div>
```

**Use for**:
- Stat card values (emails deleted, storage freed, etc.)
- Progress percentage
- Sender counts

---

### 6.4 Progress Bar Animation

```tsx
<Progress
  value={progressPercent}
  className="transition-all duration-500 ease-out"
/>
```

**Smooth Transitions**:
- Progress bar should animate smoothly, not jump
- Use `transition-all duration-500` for smooth updates
- Consider using `react-spring` or `framer-motion` for advanced animations

---

### 6.5 Activity Feed Animations

**New Item Slide-In**
```tsx
import { motion, AnimatePresence } from 'framer-motion'

<AnimatePresence>
  {activities.map(activity => (
    <motion.div
      key={activity.id}
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      transition={{ duration: 0.3 }}
    >
      <ActivityFeedItem action={activity} />
    </motion.div>
  ))}
</AnimatePresence>
```

---

### 6.6 Confirmation Dialogs

**Destructive Action Confirmation**
```tsx
<AlertDialog>
  <AlertDialogTrigger asChild>
    <Button variant="destructive">Cancel Run</Button>
  </AlertDialogTrigger>
  <AlertDialogContent>
    <AlertDialogHeader>
      <AlertDialogTitle>Cancel cleanup run?</AlertDialogTitle>
      <AlertDialogDescription>
        Progress will be saved but the run will stop. You can start a new run anytime.
      </AlertDialogDescription>
    </AlertDialogHeader>
    <AlertDialogFooter>
      <AlertDialogCancel>Keep Running</AlertDialogCancel>
      <AlertDialogAction onClick={handleCancel} className="bg-destructive">
        Cancel Run
      </AlertDialogAction>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
```

---

### 6.7 Hover States

**Card Hover (Senders, History)**
```tsx
<Card className="transition-shadow hover:shadow-lg cursor-pointer">
  {/* Card content */}
</Card>
```

**Button Hover** (built-in to shadcn components)
- Default: Slightly darker background
- Outline: Light background fill
- Ghost: Light background fill

**Table Row Hover**
```tsx
<TableRow className="hover:bg-muted/50 transition-colors">
  {/* Row content */}
</TableRow>
```

---

### 6.8 Focus States (Accessibility)

All interactive elements should have visible focus rings:
- Buttons: Default focus ring (blue outline)
- Inputs: Blue border on focus
- Links: Underline on focus
- Table rows: Outline on keyboard focus

**Ensure keyboard navigation works**:
- Tab through all interactive elements
- Enter/Space activates buttons
- Arrow keys navigate tables (optional enhancement)

---

## 7. Accessibility Guidelines

### 7.1 Color Contrast

**WCAG AA Compliance**:
- Text on background: Minimum 4.5:1 contrast ratio
- Large text (18px+): Minimum 3:1 contrast ratio
- UI components: Minimum 3:1 contrast ratio

**Test with**:
- Chrome DevTools accessibility audit
- axe DevTools extension
- Manual testing with dark mode enabled

**Color-blind Safe**:
- Don't rely on color alone to convey information
- Use icons + text labels for status
- Status badges include both color and text

---

### 7.2 Keyboard Navigation

**All interactive elements must be keyboard accessible**:
- Buttons: `Tab` to focus, `Enter`/`Space` to activate
- Links: `Tab` to focus, `Enter` to follow
- Dialogs: `Esc` to close, `Tab` to cycle through focusable elements
- Dropdowns: Arrow keys to navigate options

**Focus Management**:
- Visible focus indicators on all interactive elements
- Logical tab order (left-to-right, top-to-bottom)
- Focus trapped in modals/dialogs
- Focus returned to trigger element after dialog closes

**Skip Links** (optional enhancement):
```tsx
<a
  href="#main-content"
  className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4"
>
  Skip to main content
</a>
```

---

### 7.3 Screen Reader Support

**Semantic HTML**:
- Use `<button>` for buttons (not `<div onClick>`)
- Use `<a>` for links
- Use `<table>` for tabular data
- Use proper heading hierarchy (h1 → h2 → h3)

**ARIA Labels**:
```tsx
<Button aria-label="Start cleanup run">
  <Play className="h-4 w-4" />
</Button>

<Progress value={42} aria-label="Cleanup progress: 42%" />

<Badge aria-label="Status: Running">Running</Badge>
```

**Live Regions** (for dynamic updates):
```tsx
<div
  role="status"
  aria-live="polite"
  aria-atomic="true"
  className="sr-only"
>
  {`Deleted ${emailCount} emails, freed ${storageFreed} GB`}
</div>
```

**Alternative Text**:
- All icons should have text labels or `aria-label`
- Decorative icons: `aria-hidden="true"`
- Informative icons: Include accessible text

---

### 7.4 Form Accessibility

**Labels**:
```tsx
<div>
  <Label htmlFor="domain">Domain</Label>
  <Input
    id="domain"
    aria-describedby="domain-help"
    aria-invalid={!!error}
  />
  <p id="domain-help" className="text-sm text-muted-foreground">
    Enter the domain name (e.g., example.com)
  </p>
  {error && (
    <p className="text-sm text-destructive" role="alert">
      {error}
    </p>
  )}
</div>
```

**Error Messages**:
- Associate errors with inputs using `aria-describedby`
- Mark invalid inputs with `aria-invalid="true"`
- Error messages should have `role="alert"` for immediate announcement

---

### 7.5 Motion & Animation

**Respect `prefers-reduced-motion`**:
```tsx
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

Or in components:
```tsx
const shouldReduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  transition={{ duration: shouldReduceMotion ? 0 : 0.3 }}
>
  {/* Content */}
</motion.div>
```

---

## 8. Responsive Behavior

### 8.1 Breakpoints

Use Tailwind's default breakpoints:
- `sm`: 640px (small tablets)
- `md`: 768px (tablets)
- `lg`: 1024px (laptops)
- `xl`: 1280px (desktops)
- `2xl`: 1536px (large desktops)

**Design for 3 viewports**:
1. **Mobile**: <768px
2. **Tablet**: 768px-1023px
3. **Desktop**: 1024px+

---

### 8.2 Responsive Layouts

**Navigation**
- Desktop: Horizontal nav bar with all items visible
- Tablet: Same as desktop (space permitting)
- Mobile: Hamburger menu (sheet/drawer) with vertical nav

**Stat Cards Grid**
```tsx
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
  {/* Stat cards */}
</div>
```
- Mobile: 1 column (stacked)
- Tablet: 2 columns
- Desktop: 4 columns

**Dashboard Layout**
```tsx
<div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
  <div className="lg:col-span-2">
    {/* Progress section */}
  </div>
  <div className="lg:col-span-1">
    {/* Activity feed */}
  </div>
</div>
```
- Mobile/Tablet: Stacked (progress on top, feed below)
- Desktop: Side-by-side (60/40 split)

**Senders Table**
- Desktop: Full table with all columns
- Tablet: Hide "Last Seen" column
- Mobile: Switch to card-based layout

```tsx
{/* Desktop/Tablet */}
<Table className="hidden md:table">
  {/* Table content */}
</Table>

{/* Mobile */}
<div className="md:hidden space-y-4">
  {senders.map(sender => (
    <Card key={sender.id}>
      <CardContent className="pt-4">
        <div className="flex justify-between items-start">
          <div>
            <p className="font-medium">{sender.email}</p>
            <p className="text-sm text-muted-foreground">{sender.domain}</p>
          </div>
          <Badge>{sender.status}</Badge>
        </div>
        <div className="mt-3 flex items-center gap-4 text-sm">
          <span>{sender.messageCount} emails</span>
          <Button size="sm" variant="outline">Whitelist</Button>
        </div>
      </CardContent>
    </Card>
  ))}
</div>
```

---

### 8.3 Typography Scaling

**Responsive Font Sizes**:
```tsx
<h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold">
  Take Back Your Inbox
</h1>

<p className="text-sm sm:text-base lg:text-lg text-muted-foreground">
  Automatically unsubscribe from mailing lists...
</p>
```

**Stat Values**:
```tsx
<div className="text-2xl sm:text-3xl lg:text-4xl font-bold tabular-nums">
  {value.toLocaleString()}
</div>
```

---

### 8.4 Touch Targets (Mobile)

**Minimum Touch Target Size**: 44x44px (iOS) / 48x48px (Android)

```tsx
<Button
  size="lg"  // Ensures adequate touch target
  className="w-full sm:w-auto"  // Full-width on mobile
>
  Start Cleanup
</Button>
```

**Spacing for Touch**:
- Increase padding on mobile for easier tapping
- Add more vertical spacing between interactive elements
- Use larger buttons on mobile

---

### 8.5 Mobile-Specific Patterns

**Bottom Sheet for Actions** (alternative to dropdowns on mobile):
```tsx
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'

{/* Mobile */}
<Sheet>
  <SheetTrigger asChild>
    <Button variant="outline" className="md:hidden">
      Actions
    </Button>
  </SheetTrigger>
  <SheetContent side="bottom">
    <div className="space-y-2">
      <Button variant="outline" className="w-full">
        Add to Whitelist
      </Button>
      <Button variant="outline" className="w-full">
        View Details
      </Button>
    </div>
  </SheetContent>
</Sheet>

{/* Desktop */}
<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <Button variant="outline" className="hidden md:flex">
      Actions
    </Button>
  </DropdownMenuTrigger>
  {/* Dropdown items */}
</DropdownMenu>
```

**Mobile Navigation**:
```tsx
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'

<Sheet>
  <SheetTrigger asChild>
    <Button variant="ghost" size="icon" className="md:hidden">
      <Menu className="h-6 w-6" />
    </Button>
  </SheetTrigger>
  <SheetContent side="left">
    <nav className="flex flex-col gap-4">
      <Link href="/dashboard">Dashboard</Link>
      <Link href="/senders">Senders</Link>
      <Link href="/history">History</Link>
      <Link href="/settings">Settings</Link>
    </nav>
  </SheetContent>
</Sheet>
```

---

## 9. Additional Considerations

### 9.1 Performance Optimization

**Code Splitting**:
- Lazy load heavy components (charts, visualizations)
- Use `next/dynamic` for large components not needed on initial render

```tsx
import dynamic from 'next/dynamic'

const ActivityFeed = dynamic(() => import('@/components/activity-feed'), {
  loading: () => <Skeleton className="h-96" />,
  ssr: false,
})
```

**Image Optimization**:
- Use `next/image` for all images
- Provide explicit width/height
- Use WebP format with fallbacks

**Data Fetching**:
- Use SWR or React Query for caching and background updates
- Implement optimistic UI updates
- Show skeleton loaders during initial fetch

---

### 9.2 Error Boundaries

Wrap sections in error boundaries to prevent full app crashes:

```tsx
import { ErrorBoundary } from 'react-error-boundary'

<ErrorBoundary
  FallbackComponent={ErrorFallback}
  onReset={() => window.location.reload()}
>
  <Dashboard />
</ErrorBoundary>

function ErrorFallback({ error, resetErrorBoundary }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <AlertCircle className="h-12 w-12 text-destructive mb-4" />
      <h2 className="text-2xl font-bold mb-2">Something went wrong</h2>
      <p className="text-muted-foreground mb-4">{error.message}</p>
      <Button onClick={resetErrorBoundary}>Try again</Button>
    </div>
  )
}
```

---

### 9.3 Offline Support (Future Enhancement)

- Show offline indicator when no network
- Queue actions to retry when connection restored
- Cache critical data locally (IndexedDB)

---

### 9.4 Testing Checklist

**Visual Regression Testing**:
- Test all screens in light and dark mode
- Test at mobile, tablet, and desktop breakpoints
- Test with different data states (empty, loading, error, populated)

**Interaction Testing**:
- Test all user flows end-to-end
- Test keyboard navigation
- Test with screen reader (VoiceOver, NVDA)
- Test error states and edge cases

**Performance Testing**:
- Lighthouse score (aim for 90+ on all metrics)
- Test with slow network (throttle to 3G)
- Test with large datasets (1000+ senders)

---

## 10. Implementation Priorities

### Phase 1: MVP (Core Functionality)
1. Onboarding/Home screen with Gmail OAuth
2. Dashboard with control panel and stats
3. Basic activity feed (no animations)
4. Settings screen with whitelist management
5. Light mode only
6. Desktop-first (responsive is Phase 2)

### Phase 2: Enhanced UX
1. Dark mode support
2. Responsive layouts for mobile/tablet
3. Animations and micro-interactions
4. Senders list screen
5. Run history screen
6. Advanced progress visualization

### Phase 3: Polish & Optimization
1. Performance optimization (code splitting, lazy loading)
2. Accessibility audit and fixes
3. Advanced animations (confetti, transitions)
4. Error boundaries and offline support
5. Telemetry and analytics (optional)

---

## Appendix: Design Resources

### Figma/Design Files
- Create mockups in Figma based on these specs (optional)
- Use shadcn/ui Figma kit for consistency
- Export assets as SVG for crisp rendering

### Color Tokens (CSS Variables)
```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --card: 0 0% 100%;
  --card-foreground: 222.2 84% 4.9%;
  --primary: 221.2 83.2% 53.3%;
  --primary-foreground: 210 40% 98%;
  --secondary: 210 40% 96.1%;
  --secondary-foreground: 222.2 47.4% 11.2%;
  --muted: 210 40% 96.1%;
  --muted-foreground: 215.4 16.3% 46.9%;
  --accent: 210 40% 96.1%;
  --accent-foreground: 222.2 47.4% 11.2%;
  --destructive: 0 84.2% 60.2%;
  --destructive-foreground: 210 40% 98%;
  --border: 214.3 31.8% 91.4%;
  --input: 214.3 31.8% 91.4%;
  --ring: 221.2 83.2% 53.3%;
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  --card: 222.2 84% 4.9%;
  --card-foreground: 210 40% 98%;
  --primary: 217.2 91.2% 59.8%;
  --primary-foreground: 222.2 47.4% 11.2%;
  --secondary: 217.2 32.6% 17.5%;
  --secondary-foreground: 210 40% 98%;
  --muted: 217.2 32.6% 17.5%;
  --muted-foreground: 215 20.2% 65.1%;
  --accent: 217.2 32.6% 17.5%;
  --accent-foreground: 210 40% 98%;
  --destructive: 0 62.8% 30.6%;
  --destructive-foreground: 210 40% 98%;
  --border: 217.2 32.6% 17.5%;
  --input: 217.2 32.6% 17.5%;
  --ring: 224.3 76.3% 48%;
}
```

### Font Loading
```tsx
import { Inter } from 'next/font/google'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
})

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={inter.variable}>
      <body>{children}</body>
    </html>
  )
}
```

---

**End of UI/UX Specification**

This document should be used as the single source of truth for implementing the Inbox Nuke Agent frontend. All UI decisions should reference back to these specifications for consistency.
