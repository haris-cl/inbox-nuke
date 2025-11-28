# Inbox Nuke Frontend

Modern Next.js 14 frontend for the Inbox Nuke Agent project - an autonomous AI agent that declutters your Gmail inbox.

## Features

- **Next.js 14** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling with custom design system
- **Dark Mode** support with next-themes
- **Responsive UI** components built with class-variance-authority
- **API Client** with proper TypeScript types
- **Real-time Updates** using SWR for data fetching

## Project Structure

```
frontend/
├── app/
│   ├── globals.css          # Global styles and CSS variables
│   ├── layout.tsx           # Root layout with theme provider
│   └── page.tsx             # Home/onboarding page
├── components/
│   ├── ui/
│   │   ├── badge.tsx        # Badge component with variants
│   │   ├── button.tsx       # Button component with variants
│   │   ├── card.tsx         # Card components
│   │   └── progress.tsx     # Progress bar component
│   └── theme-toggle.tsx     # Dark mode toggle
├── lib/
│   ├── api.ts              # API client with typed methods
│   └── utils.ts            # Utility functions
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

## Getting Started

### Prerequisites

- Node.js 18.x or higher
- npm or yarn

### Installation

1. Install dependencies:

```bash
npm install
```

2. Create environment file:

```bash
cp .env.example .env
```

3. Update `.env` with your backend URL:

```
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### Development

Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

Create a production build:

```bash
npm run build
```

### Start Production Server

```bash
npm start
```

## Components

### UI Components

All UI components are built with:
- **TypeScript** for type safety
- **forwardRef** pattern for ref forwarding
- **class-variance-authority** for variant styling
- **Tailwind CSS** for styling

#### Button

Variants: default, destructive, outline, secondary, ghost, link
Sizes: default, sm, lg, icon

```tsx
<Button variant="default" size="lg">Click me</Button>
```

#### Card

```tsx
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>Content</CardContent>
  <CardFooter>Footer</CardFooter>
</Card>
```

#### Badge

Variants: default, secondary, destructive, success, warning, outline

```tsx
<Badge variant="success">Active</Badge>
```

#### Progress

```tsx
<Progress value={75} />
```

### Theme Toggle

The theme toggle component supports light/dark mode switching:

```tsx
<ThemeToggle />
```

## API Client

The API client provides typed methods for all backend endpoints:

```tsx
import api from '@/lib/api'

// Get current stats
const stats = await api.getCurrentStats()

// Start a cleanup run
const run = await api.startRun()

// Get senders
const senders = await api.getSenders({ limit: 50 })
```

## Utilities

### cn() - Class Name Merger

Merges Tailwind CSS classes with proper precedence:

```tsx
import { cn } from '@/lib/utils'

<div className={cn("base-class", someCondition && "conditional-class")} />
```

### formatBytes()

Formats bytes into human-readable sizes:

```tsx
formatBytes(1024) // "1 KB"
formatBytes(1048576) // "1 MB"
```

### formatNumber()

Formats numbers with locale-specific separators:

```tsx
formatNumber(1000000) // "1,000,000"
```

### formatRelativeTime()

Converts dates to relative time strings:

```tsx
formatRelativeTime("2024-01-20T10:00:00Z") // "2 hours ago"
```

## Design System

The design system uses CSS variables for colors, supporting both light and dark modes:

- Primary: Brand color for main actions
- Secondary: Secondary elements
- Destructive: Error states and dangerous actions
- Success: Success states
- Warning: Warning states
- Muted: Subtle text and backgrounds
- Accent: Accent elements

## Development Tools

- **ESLint**: Code linting
- **TypeScript**: Type checking
- **Tailwind CSS**: Utility-first styling
- **PostCSS**: CSS processing

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## License

This project is part of the Inbox Nuke Agent system.
