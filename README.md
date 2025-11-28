# Inbox Nuke

A fully autonomous Gmail cleanup and unsubscribe system that runs locally on your computer. Take back control of your inbox!


## What is Inbox Nuke?

Inbox Nuke is a powerful, privacy-first tool that helps you automatically clean up your Gmail inbox by:
- Finding and unsubscribing from unwanted mailing lists
- Creating Gmail filters to prevent future clutter
- Safely deleting old promotional emails and newsletters
- All while keeping your important emails (financial, government, healthcare) protected

## Key Features

- **Fully Autonomous**: Set it and forget it - the agent runs independently
- **Automatic Unsubscribe**: Discovers and unsubscribes from mailing lists using both header links and mailto: addresses
- **Smart Gmail Filters**: Creates filters to automatically archive or mute future emails from bulk senders
- **Storage Cleanup**: Deletes old newsletters and promotional emails to free up valuable Gmail space
- **Real-time Dashboard**: Beautiful web interface to monitor cleanup progress with live updates
- **Safety First**: Built-in guardrails protect important emails (financial, government, healthcare, etc.)
- **100% Local & Private**: All data stored locally in SQLite, no cloud services, your data never leaves your computer
- **Open Source**: Fully transparent codebase you can audit and customize

## Prerequisites

- Python 3.11+
- Node.js 18+
- Google Cloud Project with Gmail API enabled

## Screenshots



## Quick Start Guide

Follow these steps to get Inbox Nuke running on your machine in under 10 minutes!

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/inbox-nuke.git
cd inbox-nuke
```

### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

### Step 3: Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local
```

### Step 4: Configure Google OAuth

You'll need to set up OAuth credentials to allow Inbox Nuke to access your Gmail. This takes about 5 minutes.

See our detailed guide: [docs/OAUTH_SETUP.md](docs/OAUTH_SETUP.md)

**Quick Summary:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Gmail API
4. Create OAuth 2.0 credentials
5. Add redirect URI: `http://localhost:8000/api/auth/google/callback`
6. Copy Client ID and Client Secret to `backend/.env`

### Step 5: Generate Encryption Key

```bash
cd backend
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output and paste it as the `ENCRYPTION_KEY` value in `backend/.env`

### Step 6: Run the Application

Open two terminal windows:

**Terminal 1 - Start Backend:**
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn main:app --reload
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend
npm run dev
```

### Step 7: Access the Application

Open your browser and go to: [http://localhost:3000](http://localhost:3000)

You should see the Inbox Nuke dashboard. Click "Connect Gmail" to get started!

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLIENT_ID` | OAuth 2.0 Client ID from Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | OAuth 2.0 Client Secret |
| `GOOGLE_REDIRECT_URI` | OAuth callback URL (default: `http://localhost:8000/auth/google/callback`) |
| `ENCRYPTION_KEY` | Fernet key for encrypting OAuth tokens |
| `OPENAI_API_KEY` | (Optional) For AI-powered email classification |
| `APP_ENV` | Environment (`local` or `production`) |
| `FRONTEND_URL` | Frontend URL for CORS (default: `http://localhost:3000`) |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_BACKEND_URL` | Backend API URL (default: `http://localhost:8000`) |

## Tech Stack

**Backend:**
- **FastAPI** - High-performance Python web framework
- **SQLAlchemy** - SQL database ORM
- **SQLite** - Lightweight local database
- **Google Gmail API** - Official Gmail integration
- **Cryptography** - Secure token encryption

**Frontend:**
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Shadcn/ui** - Beautiful, accessible UI components
- **Lucide Icons** - Modern icon library

## Project Structure

```
inbox-nuke/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── db.py                # Database configuration
│   ├── models.py            # SQLAlchemy models
│   ├── gmail_client.py      # Gmail API wrapper
│   ├── agent/
│   │   ├── runner.py        # Main agent orchestrator
│   │   ├── safety.py        # Safety guardrails
│   │   ├── unsubscribe.py   # Unsubscribe handlers
│   │   ├── filters.py       # Gmail filter creation
│   │   └── cleanup.py       # Email deletion logic
│   ├── routers/             # API route handlers
│   ├── data/                # SQLite database storage
│   └── requirements.txt
├── frontend/
│   ├── app/                 # Next.js App Router pages
│   ├── components/          # React components
│   ├── lib/                 # Utilities and API client
│   └── package.json
└── docs/
    ├── OAUTH_SETUP.md      # OAuth setup guide
    ├── PRD.md              # Product Requirements
    └── UI_UX_SPEC.md       # UI/UX Specifications
```

## Safety Features

The agent will **never delete** emails that:
- Contain keywords: invoice, receipt, bank, payment, statement, tax, verification code, security alert
- Are from government, financial, or healthcare domains
- Are from manually whitelisted domains

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/google/start` | GET | Initiate OAuth flow |
| `/auth/google/callback` | GET | OAuth callback handler |
| `/runs` | POST | Start a new cleanup run |
| `/runs/{id}` | GET | Get run status and stats |
| `/runs/{id}/pause` | POST | Pause a running cleanup |
| `/runs/{id}/resume` | POST | Resume a paused cleanup |
| `/senders` | GET | List discovered senders |
| `/stats/current` | GET | Get current statistics |
| `/whitelist` | GET/POST/DELETE | Manage whitelisted domains |

## Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add some amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

Please make sure to:
- Follow the existing code style
- Add tests for new features
- Update documentation as needed
- Keep commits atomic and well-described

## Roadmap

- [ ] Support for multiple email providers (Outlook, Yahoo, etc.)
- [ ] Advanced AI-powered email categorization
- [ ] Scheduled cleanup runs
- [ ] Email analytics and insights
- [ ] Browser extension for quick actions
- [ ] Mobile app support

## Support & Community

- Open an issue on GitHub for bug reports or feature requests
- Star the repo if you find it useful!

## License

MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

Built with modern web technologies and a focus on privacy and local-first architecture. Special thanks to the open-source community for the amazing tools that made this possible.

---
