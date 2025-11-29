"""
One-time migration script to fix historical user emails that were scored before protection logic.

This script:
1. Gets the user's email address from Gmail API
2. Finds all emails from the user that are not already classified as KEEP
3. Updates them to KEEP with score 0 and appropriate reasoning

Run with: python fix_user_emails.py
"""

import asyncio
import sys
from sqlalchemy import select, update
from db import AsyncSessionLocal
from models import GmailCredentials, EmailScore, SenderProfile
from gmail_client import GmailClient


async def fix_user_emails():
    """Fix historical user emails that were scored before protection logic was added."""

    print("Starting migration to fix user's own emails...")

    async with AsyncSessionLocal() as db:
        # Get Gmail credentials
        stmt = select(GmailCredentials).limit(1)
        result = await db.execute(stmt)
        creds = result.scalar_one_or_none()

        if not creds:
            print("ERROR: No Gmail credentials found. Please authenticate first.")
            return

        # Get user's email address
        print("Fetching user email from Gmail API...")
        gmail_client = GmailClient(db=db, credentials=creds)
        service = await gmail_client.get_service()
        profile = await asyncio.to_thread(
            service.users().getProfile(userId='me').execute
        )
        user_email = profile.get('emailAddress', '').lower()

        if not user_email:
            print("ERROR: Could not retrieve user email address")
            return

        print(f"User email: {user_email}")

        # Find all emails from user that are not KEEP
        stmt = select(EmailScore).where(
            EmailScore.sender_email == user_email
        )
        result = await db.execute(stmt)
        user_emails = result.scalars().all()

        print(f"\nFound {len(user_emails)} emails from user")

        # Count by classification
        classifications = {"KEEP": 0, "DELETE": 0, "UNCERTAIN": 0}
        for email in user_emails:
            classifications[email.classification] = classifications.get(email.classification, 0) + 1

        print(f"  - KEEP: {classifications.get('KEEP', 0)}")
        print(f"  - DELETE: {classifications.get('DELETE', 0)}")
        print(f"  - UNCERTAIN: {classifications.get('UNCERTAIN', 0)}")

        # Find emails that need fixing
        emails_to_fix = [
            email for email in user_emails
            if email.classification != "KEEP" or email.total_score != 0
        ]

        if not emails_to_fix:
            print("\n✓ All user emails are already protected! No changes needed.")
            return

        print(f"\nFound {len(emails_to_fix)} emails to fix")

        # Confirm before proceeding
        print("\nThis will update the following emails:")
        for email in emails_to_fix[:5]:
            print(f"  - {email.subject[:60]} (current: {email.classification}, score: {email.total_score})")
        if len(emails_to_fix) > 5:
            print(f"  ... and {len(emails_to_fix) - 5} more")

        confirm = input("\nProceed with update? (yes/no): ").lower().strip()
        if confirm != 'yes':
            print("Aborted.")
            return

        # Update emails
        print("\nUpdating emails...")
        updated_count = 0

        for email in emails_to_fix:
            email.classification = "KEEP"
            email.total_score = 0
            email.confidence = 1.0
            email.reasoning = "Classification: KEEP (score: 0/100)\nKey factors:\n  • Email from your own account - always keep"
            updated_count += 1

            if updated_count % 10 == 0:
                print(f"  Updated {updated_count}/{len(emails_to_fix)}...")

        # Also update sender profile if exists
        stmt = select(SenderProfile).where(SenderProfile.sender_email == user_email)
        result = await db.execute(stmt)
        sender_profile = result.scalar_one_or_none()

        if sender_profile:
            print(f"\nUpdating sender profile for {user_email}...")
            sender_profile.classification = "KEEP"
            sender_profile.avg_score = 0.0

        # Commit changes
        await db.commit()

        print(f"\n✓ Successfully updated {updated_count} emails!")
        print(f"✓ All emails from {user_email} are now classified as KEEP with score 0")

        # Show final stats
        stmt = select(EmailScore).where(EmailScore.sender_email == user_email)
        result = await db.execute(stmt)
        user_emails = result.scalars().all()

        final_classifications = {"KEEP": 0, "DELETE": 0, "UNCERTAIN": 0}
        for email in user_emails:
            final_classifications[email.classification] = final_classifications.get(email.classification, 0) + 1

        print("\nFinal classification counts:")
        print(f"  - KEEP: {final_classifications.get('KEEP', 0)}")
        print(f"  - DELETE: {final_classifications.get('DELETE', 0)}")
        print(f"  - UNCERTAIN: {final_classifications.get('UNCERTAIN', 0)}")


if __name__ == "__main__":
    try:
        asyncio.run(fix_user_emails())
    except KeyboardInterrupt:
        print("\n\nAborted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
