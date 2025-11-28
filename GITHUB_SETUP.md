# GitHub Setup Guide

Your Inbox Nuke project is now ready for GitHub upload! Follow these steps to publish your repository.

## Pre-Upload Checklist

All of these have been completed for you:

- [x] `.env.example` files created (backend and frontend)
- [x] `.gitignore` file configured to exclude sensitive data
- [x] `README.md` updated with YouTube-friendly content
- [x] `LICENSE` file (MIT) added
- [x] No hardcoded secrets in source code
- [x] `.github/` folder structure created
- [x] Issue and PR templates added

## Files Created/Modified

### New Files
- `/Users/hnaeem/inbox-nuke/backend/.env.example` - Backend environment variables template
- `/Users/hnaeem/inbox-nuke/LICENSE` - MIT License
- `/Users/hnaeem/inbox-nuke/.github/FUNDING.yml` - Sponsor links (customize as needed)
- `/Users/hnaeem/inbox-nuke/.github/ISSUE_TEMPLATE/bug_report.md` - Bug report template
- `/Users/hnaeem/inbox-nuke/.github/ISSUE_TEMPLATE/feature_request.md` - Feature request template
- `/Users/hnaeem/inbox-nuke/.github/pull_request_template.md` - PR template

### Modified Files
- `/Users/hnaeem/inbox-nuke/frontend/.env.example` - Updated with helpful comments
- `/Users/hnaeem/inbox-nuke/README.md` - YouTube-friendly with detailed setup guide

### Already Protected (in .gitignore)
- `backend/.env` - Contains your real credentials (WILL NOT be committed)
- `frontend/.env.local` - Contains your real credentials (WILL NOT be committed)
- `backend/data/*.db` - Your SQLite database (WILL NOT be committed)
- `node_modules/` - Dependencies (WILL NOT be committed)
- `venv/` - Python virtual environment (WILL NOT be committed)

## Step 1: Initialize Git Repository

```bash
cd /Users/hnaeem/inbox-nuke
git init
git add .
git commit -m "Initial commit: Inbox Nuke - Gmail cleanup automation tool"
```

## Step 2: Create GitHub Repository

1. Go to [GitHub](https://github.com/new)
2. Repository name: `inbox-nuke`
3. Description: "A fully autonomous Gmail cleanup and unsubscribe system that runs locally"
4. Choose: **Public** (for YouTube audience)
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

## Step 3: Push to GitHub

After creating the repository on GitHub, run:

```bash
git remote add origin https://github.com/YOUR_USERNAME/inbox-nuke.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

## Step 4: Configure Repository Settings (Optional)

### Add Topics/Tags
Go to your repository page and add topics:
- `gmail`
- `automation`
- `email-management`
- `python`
- `nextjs`
- `fastapi`
- `typescript`

### Enable GitHub Pages (Optional)
If you want to host documentation:
1. Go to Settings → Pages
2. Select source: `main` branch, `/docs` folder or root

### Configure Branch Protection (Optional)
1. Go to Settings → Branches
2. Add rule for `main` branch
3. Enable "Require pull request reviews before merging"

## Step 5: Update README Placeholders

Before making your repository public, update these placeholders in `/Users/hnaeem/inbox-nuke/README.md`:

1. Line 7: `[YouTube Tutorial Coming Soon!](#)` - Add your YouTube video link
2. Line 45: `git clone https://github.com/YOUR_USERNAME/inbox-nuke.git` - Replace YOUR_USERNAME
3. Line 255: `**Made with code by [Your Name]**` - Add your name and social links

You can do a find & replace:
- Search: `YOUR_USERNAME` → Replace with your GitHub username
- Search: `[Your Name]` → Replace with your name
- Search: `[YouTube Channel](#)` → Replace with your YouTube channel link

## Step 6: Verify No Secrets Are Exposed

Before pushing, double-check:

```bash
# Search for any API keys (should only find .env and .env.example)
grep -r "GOCSPX" .
grep -r "sk-proj" .

# Should NOT show .env files in the commit list
git status
```

If you see `backend/.env` or `frontend/.env.local` in git status, **STOP** and check your `.gitignore`.

## Step 7: Create Your First Release (Optional)

Once everything is pushed:

1. Go to your repository → Releases → "Create a new release"
2. Tag version: `v1.0.0`
3. Release title: `Inbox Nuke v1.0.0 - Initial Release`
4. Description: Add release notes, features, and known issues
5. Publish release

## Step 8: Share on YouTube

Update your YouTube video description with:

```
📦 Source Code: https://github.com/YOUR_USERNAME/inbox-nuke
⭐ Don't forget to star the repo if you find it useful!

🔗 Quick Links:
- Setup Guide: https://github.com/YOUR_USERNAME/inbox-nuke#quick-start-guide
- OAuth Setup: https://github.com/YOUR_USERNAME/inbox-nuke/blob/main/docs/OAUTH_SETUP.md
- Report Issues: https://github.com/YOUR_USERNAME/inbox-nuke/issues
```

## Important Security Notes

1. **Never commit your `.env` files** - They contain real API keys
2. **The `.gitignore` is configured to protect**:
   - All `.env` files
   - Database files (`*.db`)
   - Virtual environments (`venv/`)
   - Node modules (`node_modules/`)
   - Build directories (`.next/`)

3. **If you accidentally commit secrets**:
   ```bash
   # Remove from history (use with caution)
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch backend/.env" \
     --prune-empty --tag-name-filter cat -- --all

   # Force push (only if you haven't shared the repo yet)
   git push origin --force --all
   ```

4. **Consider rotating your API keys** if you accidentally exposed them

## Next Steps

- [ ] Initialize git and push to GitHub
- [ ] Update README placeholders with your information
- [ ] Add repository topics/tags
- [ ] Create a release tag
- [ ] Add GitHub repository link to your YouTube video description
- [ ] (Optional) Set up GitHub Actions for CI/CD
- [ ] (Optional) Add screenshots to README
- [ ] (Optional) Create a demo video/GIF for README

## Need Help?

If you run into issues:
1. Check that `.gitignore` is working: `git status` should NOT show `.env` files
2. Verify no secrets in code: `git log -p | grep -i "gocspx\|sk-proj"`
3. Review GitHub's [repository security guide](https://docs.github.com/en/code-security)

---

Your project is ready for the world! Good luck with your YouTube video! 🚀
