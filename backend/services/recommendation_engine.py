"""
V2 Recommendation Engine - Generates cleanup recommendations.
Analyzes emails and determines what should be kept vs deleted.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import EmailRecommendation, WhitelistDomain, SenderProfile


# Protected domains that should never be deleted
FINANCIAL_DOMAINS = [
    "chase.com", "wellsfargo.com", "bankofamerica.com", "paypal.com",
    "venmo.com", "stripe.com", "square.com", "coinbase.com", "fidelity.com",
    "schwab.com", "vanguard.com", "americanexpress.com", "discover.com",
    "capitalone.com", "usbank.com", "pnc.com", "ally.com",
]

SECURITY_KEYWORDS = [
    "verify", "verification", "confirm", "confirmation", "otp",
    "2fa", "two-factor", "password reset", "security alert",
    "suspicious activity", "login attempt", "authentication",
    "one-time", "passcode", "code:", "your code",
]

GOVERNMENT_DOMAINS = [
    ".gov", ".mil", "irs.gov", "ssa.gov", "medicare.gov",
    "healthcare.gov", "dmv.org", "usps.com",
]

# Signals for deletion
PROMOTIONAL_SENDER_PATTERNS = [
    "noreply@", "no-reply@", "newsletter@", "marketing@",
    "promo@", "offers@", "sales@", "deals@", "info@",
    "notifications@", "updates@", "news@", "hello@",
]

PROMOTIONAL_SUBJECT_KEYWORDS = [
    "% off", "sale", "deal", "discount", "coupon",
    "free shipping", "limited time", "act now", "don't miss",
    "exclusive", "special offer", "save", "clearance",
    "unsubscribe", "weekly digest", "newsletter",
]


class RecommendationEngine:
    """
    Generates AI recommendations for email cleanup.
    Uses multi-signal scoring to determine keep/delete suggestions.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._whitelist_cache: Optional[set] = None

    async def _get_whitelist(self) -> set:
        """Get cached whitelist domains."""
        if self._whitelist_cache is None:
            result = await self.db.execute(select(WhitelistDomain.domain))
            self._whitelist_cache = {row.domain.lower() for row in result.all()}
        return self._whitelist_cache

    def _extract_domain(self, email: str) -> str:
        """Extract domain from email address."""
        if "@" in email:
            return email.split("@")[1].lower()
        return email.lower()

    def _is_protected_domain(self, domain: str) -> bool:
        """Check if domain is in protected list."""
        domain = domain.lower()

        # Check financial domains
        for fin_domain in FINANCIAL_DOMAINS:
            if domain == fin_domain or domain.endswith(f".{fin_domain}"):
                return True

        # Check government domains
        for gov_domain in GOVERNMENT_DOMAINS:
            if domain.endswith(gov_domain):
                return True

        return False

    def _is_security_email(self, subject: str) -> bool:
        """Check if email is security-related based on subject."""
        subject_lower = subject.lower()
        return any(keyword in subject_lower for keyword in SECURITY_KEYWORDS)

    def _is_promotional_sender(self, sender_email: str) -> bool:
        """Check if sender email matches promotional patterns."""
        sender_lower = sender_email.lower()
        return any(pattern in sender_lower for pattern in PROMOTIONAL_SENDER_PATTERNS)

    def _has_promotional_subject(self, subject: str) -> bool:
        """Check if subject contains promotional keywords."""
        subject_lower = subject.lower()
        return any(keyword in subject_lower for keyword in PROMOTIONAL_SUBJECT_KEYWORDS)

    def _categorize_email(self, gmail_labels: List[str]) -> str:
        """Categorize email based on Gmail labels."""
        labels_set = set(label.upper() for label in gmail_labels)

        if "CATEGORY_PROMOTIONS" in labels_set:
            return "promotions"
        elif "CATEGORY_SOCIAL" in labels_set:
            return "social"
        elif "CATEGORY_UPDATES" in labels_set:
            return "updates"
        elif "CATEGORY_FORUMS" in labels_set:
            return "newsletters"
        else:
            return "other"

    async def analyze_email(
        self,
        session_id: str,
        message_id: str,
        thread_id: str,
        sender_email: str,
        sender_name: Optional[str],
        subject: str,
        snippet: str,
        received_date: datetime,
        size_bytes: int,
        gmail_labels: List[str],
        has_unsubscribe: bool = False,
        unsubscribe_url: Optional[str] = None,
        unsubscribe_mailto: Optional[str] = None,
        unsubscribe_one_click: bool = False,
        user_replied: bool = False,
        is_starred: bool = False,
    ) -> EmailRecommendation:
        """
        Analyze a single email and generate a recommendation.
        Returns an EmailRecommendation object (not yet saved).
        """
        whitelist = await self._get_whitelist()
        domain = self._extract_domain(sender_email)

        # Initialize scores
        keep_score = 0
        delete_score = 0
        reasoning_parts = []

        # === PROTECTION SIGNALS (increase keep_score) ===

        # Whitelisted domain
        if domain in whitelist or sender_email.lower() in whitelist:
            keep_score += 100
            reasoning_parts.append("Sender is on your protected list")

        # Protected domain (financial, government)
        if self._is_protected_domain(domain):
            keep_score += 80
            reasoning_parts.append("Important domain (financial/government)")

        # Security email
        if self._is_security_email(subject):
            keep_score += 70
            reasoning_parts.append("Security or verification email")

        # User replied to this sender (engagement)
        if user_replied:
            keep_score += 60
            reasoning_parts.append("You've replied to this sender")

        # Starred email
        if is_starred:
            keep_score += 50
            reasoning_parts.append("Email is starred")

        # Primary inbox
        if "INBOX" in gmail_labels and "CATEGORY_PRIMARY" in [l.upper() for l in gmail_labels]:
            keep_score += 30
            reasoning_parts.append("In primary inbox")

        # === DELETION SIGNALS (increase delete_score) ===

        # Promotional category
        category = self._categorize_email(gmail_labels)
        if category == "promotions":
            delete_score += 40
            reasoning_parts.append("Gmail categorized as Promotions")
        elif category == "social":
            delete_score += 30
            reasoning_parts.append("Gmail categorized as Social")

        # Has unsubscribe header (newsletter/mailing list)
        if has_unsubscribe:
            delete_score += 25
            reasoning_parts.append("Has unsubscribe option (mailing list)")

        # Promotional sender pattern
        if self._is_promotional_sender(sender_email):
            delete_score += 30
            reasoning_parts.append("Sender pattern suggests automated email")

        # Promotional subject
        if self._has_promotional_subject(subject):
            delete_score += 20
            reasoning_parts.append("Subject contains promotional keywords")

        # === DETERMINE SUGGESTION ===

        # Calculate final score (higher = more likely to delete)
        # Range: -100 (definitely keep) to +100 (definitely delete)
        final_score = delete_score - keep_score

        if final_score <= -30:
            ai_suggestion = "keep"
            confidence = min(1.0, abs(final_score) / 100)
        elif final_score >= 30:
            ai_suggestion = "delete"
            confidence = min(1.0, final_score / 100)
        else:
            # Uncertain - low confidence
            ai_suggestion = "delete" if final_score > 0 else "keep"
            confidence = 0.3 + (abs(final_score) / 100) * 0.4

        # Build reasoning string
        if not reasoning_parts:
            reasoning_parts.append("No specific signals detected")

        reasoning = "; ".join(reasoning_parts[:3])  # Limit to 3 reasons

        # Determine category
        if keep_score > delete_score:
            category = "protected"

        return EmailRecommendation(
            session_id=session_id,
            message_id=message_id,
            thread_id=thread_id,
            sender_email=sender_email,
            sender_name=sender_name,
            subject=subject,
            snippet=snippet,
            received_date=received_date,
            size_bytes=size_bytes,
            ai_suggestion=ai_suggestion,
            reasoning=reasoning,
            confidence=confidence,
            category=category,
            gmail_labels=json.dumps(gmail_labels),
            has_unsubscribe=has_unsubscribe,
            unsubscribe_url=unsubscribe_url,
            unsubscribe_mailto=unsubscribe_mailto,
            unsubscribe_one_click=unsubscribe_one_click,
        )

    async def save_recommendation(self, recommendation: EmailRecommendation) -> None:
        """Save a recommendation to the database."""
        self.db.add(recommendation)
        await self.db.commit()

    async def batch_save_recommendations(
        self, recommendations: List[EmailRecommendation]
    ) -> None:
        """Save multiple recommendations in a batch."""
        for rec in recommendations:
            self.db.add(rec)
        await self.db.commit()
