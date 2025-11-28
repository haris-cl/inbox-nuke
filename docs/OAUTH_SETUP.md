# Google OAuth 2.0 Setup Guide

This guide walks you through setting up Google OAuth 2.0 for the Inbox Nuke Agent.

## Prerequisites

- A Google account
- Access to [Google Cloud Console](https://console.cloud.google.com/)

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top of the page
3. Click "New Project"
4. Enter a project name (e.g., "Inbox Nuke Agent")
5. Click "Create"
6. Wait for the project to be created, then select it

## Step 2: Enable the Gmail API

1. In the left sidebar, go to **APIs & Services** → **Library**
2. Search for "Gmail API"
3. Click on "Gmail API"
4. Click "Enable"

## Step 3: Configure OAuth Consent Screen

1. In the left sidebar, go to **APIs & Services** → **OAuth consent screen**
2. Select "External" as the User Type (unless you have a Google Workspace organization)
3. Click "Create"

### Fill in the OAuth consent screen:

**App Information:**
- App name: "Inbox Nuke Agent"
- User support email: Your email address
- App logo: (optional)

**App domain:**
- Leave blank for local development

**Developer contact information:**
- Add your email address

4. Click "Save and Continue"

### Scopes:

1. Click "Add or Remove Scopes"
2. Search for and add the following scopes:
   - `https://www.googleapis.com/auth/gmail.readonly` - Read emails
   - `https://www.googleapis.com/auth/gmail.modify` - Modify emails (delete, move)
   - `https://www.googleapis.com/auth/gmail.settings.basic` - Create filters
   - `https://www.googleapis.com/auth/gmail.send` - Send unsubscribe emails

3. Click "Update"
4. Click "Save and Continue"

### Test Users:

1. Click "Add Users"
2. Add your Gmail address
3. Click "Add"
4. Click "Save and Continue"

5. Review the summary and click "Back to Dashboard"

## Step 4: Create OAuth 2.0 Credentials

1. In the left sidebar, go to **APIs & Services** → **Credentials**
2. Click "Create Credentials" → "OAuth client ID"
3. Select "Web application" as the Application type
4. Enter a name (e.g., "Inbox Nuke Web Client")

### Configure URIs:

**Authorized JavaScript origins:**
```
http://localhost:3000
```

**Authorized redirect URIs:**
```
http://localhost:8000/api/auth/google/callback
```

5. Click "Create"

## Step 5: Copy Your Credentials

After creating the OAuth client, you'll see a popup with:
- **Client ID**: Something like `123456789-abc123.apps.googleusercontent.com`
- **Client Secret**: Something like `GOCSPX-xxxxxxxxxx`

Copy these values to your `backend/.env` file:

```env
GOOGLE_CLIENT_ID=your-client-id-here
GOOGLE_CLIENT_SECRET=your-client-secret-here
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
```

## Step 6: Generate Encryption Key

Generate a Fernet encryption key for securely storing OAuth tokens:

```bash
cd backend
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output to your `backend/.env` file:

```env
ENCRYPTION_KEY=your-generated-key-here
```

## Verification

Your complete `backend/.env` file should look like:

```env
GOOGLE_CLIENT_ID=123456789-abc.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxx
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
ENCRYPTION_KEY=your-fernet-key
APP_ENV=local
FRONTEND_URL=http://localhost:3000
```

## OAuth Scopes Explained

| Scope | Purpose |
|-------|---------|
| `gmail.readonly` | Read email headers and content for sender discovery |
| `gmail.modify` | Delete emails, move to trash, modify labels |
| `gmail.settings.basic` | Create and manage Gmail filters |
| `gmail.send` | Send unsubscribe emails (for mailto: links) |

## Security Notes

1. **Never commit credentials**: Your `.env` file is in `.gitignore`
2. **Test user limitation**: In "Testing" mode, only added test users can authenticate
3. **Token storage**: OAuth tokens are encrypted with Fernet before storing in SQLite
4. **Local only**: All data stays on your machine

## Publishing Your App (Optional)

For personal use, you can keep the app in "Testing" mode. If you want to publish:

1. Go to OAuth consent screen
2. Click "Publish App"
3. Submit for verification (may take weeks)
4. Requires privacy policy and terms of service

For local/personal use, "Testing" mode is sufficient.

## Troubleshooting

### "Access blocked: This app's request is invalid"
- Check that the redirect URI exactly matches what's in Google Cloud Console
- Ensure you're using `http://localhost:8000/api/auth/google/callback`

### "Error 403: access_denied"
- Your email isn't in the test users list
- Add your email in OAuth consent screen → Test users

### "Error 400: redirect_uri_mismatch"
- The redirect URI doesn't match
- Check for trailing slashes or http vs https

### Token refresh fails
- The refresh token may have expired (7 days for apps in testing)
- Re-authenticate by disconnecting and reconnecting Gmail

## Next Steps

Once OAuth is configured:

1. Start the backend: `uvicorn main:app --reload`
2. Start the frontend: `npm run dev`
3. Visit `http://localhost:3000`
4. Click "Connect Gmail"
5. Complete the OAuth flow
6. Start your first cleanup!
