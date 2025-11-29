"""
AI-powered email classification using OpenAI.
Determines email importance: KEEP, DELETE, or REVIEW.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from gmail_client import GmailClient
from models import EmailClassification, RetentionRule

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class ClassificationResult:
    """Result of email classification."""
    message_id: str
    sender_email: str
    subject: str
    classification: str  # KEEP, DELETE, REVIEW
    category: str  # financial, security, personal, documents, marketing, social, spam
    confidence: float  # 0.0-1.0
    reasoning: str


# ============================================================================
# Email Classifier
# ============================================================================


class EmailClassifier:
    """
    AI-powered email classifier using OpenAI.

    Analyzes emails to determine if they should be kept, deleted, or reviewed.
    Uses GPT-4 for intelligent classification based on content and context.

    Attributes:
        db: AsyncSession for database operations
        gmail_client: GmailClient for Gmail API operations
        openai_client: AsyncOpenAI client for API calls
    """

    CLASSIFICATION_PROMPT = """You are an email classification assistant. Analyze this email and determine if it should be KEPT or DELETED.

Email Details:
- From: {sender}
- Subject: {subject}
- Snippet: {snippet}
- Labels: {labels}
- Has Attachments: {has_attachments}
- Thread Messages: {thread_count}

Classification Rules:
KEEP if:
- Financial (receipts, invoices, bank statements, e-transfers, orders, purchase confirmations)
- Security (2FA codes, password resets, verification codes, security alerts)
- Personal conversations (emails with replies, appointments, reservations, meeting invitations)
- Important documents (medical records, legal documents, educational certificates, diplomas)
- Active service notifications you use (shipping updates, delivery confirmations)
- Work-related communications (job offers, work projects, professional correspondence)

DELETE if:
- Marketing newsletters, promotional emails, deals, sales announcements
- Social media notifications that are not conversations (likes, follows, suggestions)
- Referral programs, rewards marketing, loyalty program spam
- Expired offers, outdated promotions, old newsletters
- Subscription emails from services you don't actively engage with
- Generic updates that provide no ongoing value

REVIEW if:
- Uncertain classification
- Mixed content (part important, part promotional)
- Need more context to decide

Respond with JSON only, no other text:
{{
  "classification": "KEEP" | "DELETE" | "REVIEW",
  "category": "financial" | "security" | "personal" | "documents" | "marketing" | "social" | "spam" | "account" | "work",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of why this classification was chosen (1-2 sentences)"
}}"""

    def __init__(
        self,
        db: AsyncSession,
        gmail_client: GmailClient,
    ):
        """
        Initialize the email classifier.

        Args:
            db: Async database session
            gmail_client: Gmail client for API operations
        """
        self.db = db
        self.gmail_client = gmail_client

        # Initialize OpenAI client if API key is configured
        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.openai_client = None
            logger.warning("OpenAI API key not configured. AI classification disabled.")

    async def classify_email(
        self,
        message: Dict[str, Any],
    ) -> ClassificationResult:
        """
        Classify a single email using AI.

        Args:
            message: Gmail message dictionary from API

        Returns:
            ClassificationResult with classification details

        Raises:
            ValueError: If OpenAI is not configured
            Exception: For API errors
        """
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured. Cannot classify emails.")

        # Extract email details
        message_id = message.get("id", "")
        headers = message.get("payload", {}).get("headers", [])

        sender = self._get_header_value(headers, "From")
        sender_email = self._extract_email(sender)
        subject = self._get_header_value(headers, "Subject")
        snippet = message.get("snippet", "")
        labels = message.get("labelIds", [])

        # Get thread info
        thread_id = message.get("threadId", "")
        thread_count = 1  # Default, could be enhanced to get actual thread size

        # Check for attachments
        has_attachments = self._has_attachments(message)

        # First check if we have a retention rule for this email
        rule_result = await self._check_retention_rules(sender_email, subject)
        if rule_result:
            logger.info(f"Email {message_id} matched retention rule: {rule_result['action']}")
            return ClassificationResult(
                message_id=message_id,
                sender_email=sender_email,
                subject=subject,
                classification=rule_result["action"],
                category=rule_result["category"],
                confidence=1.0,
                reasoning=f"Matched retention rule: {rule_result['rule']}"
            )

        # Build prompt
        prompt = self.CLASSIFICATION_PROMPT.format(
            sender=sender,
            subject=subject,
            snippet=snippet,
            labels=", ".join(labels),
            has_attachments="Yes" if has_attachments else "No",
            thread_count=thread_count
        )

        try:
            # Call OpenAI API
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Use mini for cost efficiency
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert email classifier. Respond only with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Low temperature for consistent results
                max_tokens=200,
                response_format={"type": "json_object"}
            )

            # Parse response
            result_text = response.choices[0].message.content
            result_data = json.loads(result_text)

            # Validate and extract fields
            classification = result_data.get("classification", "REVIEW")
            category = result_data.get("category", "unknown")
            confidence = float(result_data.get("confidence", 0.5))
            reasoning = result_data.get("reasoning", "AI classification")

            # Ensure valid classification
            if classification not in ["KEEP", "DELETE", "REVIEW"]:
                classification = "REVIEW"
                reasoning = f"Invalid classification returned: {classification}. Defaulting to REVIEW."

            logger.debug(
                f"Classified {message_id} from {sender_email}: "
                f"{classification} ({category}, {confidence:.2f})"
            )

            return ClassificationResult(
                message_id=message_id,
                sender_email=sender_email,
                subject=subject,
                classification=classification,
                category=category,
                confidence=confidence,
                reasoning=reasoning
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            # Return REVIEW on parsing errors
            return ClassificationResult(
                message_id=message_id,
                sender_email=sender_email,
                subject=subject,
                classification="REVIEW",
                category="unknown",
                confidence=0.0,
                reasoning=f"Failed to parse AI response: {str(e)}"
            )

        except Exception as e:
            logger.error(f"Error classifying email {message_id}: {e}")
            # Return REVIEW on errors (conservative approach)
            return ClassificationResult(
                message_id=message_id,
                sender_email=sender_email,
                subject=subject,
                classification="REVIEW",
                category="unknown",
                confidence=0.0,
                reasoning=f"Classification error: {str(e)}"
            )

    async def classify_batch(
        self,
        messages: List[Dict[str, Any]],
        batch_size: int = 10,
    ) -> List[ClassificationResult]:
        """
        Classify multiple emails in batches.

        Processes emails in smaller batches to avoid rate limits
        and manage costs.

        Args:
            messages: List of Gmail message dictionaries
            batch_size: Number of emails to process at once

        Returns:
            List of ClassificationResult objects
        """
        results = []

        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            logger.info(f"Classifying batch {i // batch_size + 1}: {len(batch)} emails")

            for message in batch:
                try:
                    result = await self.classify_email(message)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error in batch classification: {e}")
                    # Add REVIEW result for failed classifications
                    message_id = message.get("id", "unknown")
                    sender = self._get_header_value(
                        message.get("payload", {}).get("headers", []),
                        "From"
                    )
                    subject = self._get_header_value(
                        message.get("payload", {}).get("headers", []),
                        "Subject"
                    )
                    results.append(ClassificationResult(
                        message_id=message_id,
                        sender_email=self._extract_email(sender),
                        subject=subject,
                        classification="REVIEW",
                        category="unknown",
                        confidence=0.0,
                        reasoning=f"Batch error: {str(e)}"
                    ))

        return results

    async def save_classification(
        self,
        result: ClassificationResult,
    ) -> EmailClassification:
        """
        Save classification result to database.

        Args:
            result: ClassificationResult to save

        Returns:
            EmailClassification model instance
        """
        # Check if already exists
        stmt = select(EmailClassification).where(
            EmailClassification.message_id == result.message_id
        )
        db_result = await self.db.execute(stmt)
        existing = db_result.scalar_one_or_none()

        if existing:
            # Update existing
            existing.classification = result.classification
            existing.category = result.category
            existing.confidence = result.confidence
            existing.reasoning = result.reasoning
            existing.processed_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            # Create new
            classification = EmailClassification(
                message_id=result.message_id,
                sender_email=result.sender_email,
                subject=result.subject,
                classification=result.classification,
                category=result.category,
                confidence=result.confidence,
                reasoning=result.reasoning,
                processed_at=datetime.utcnow()
            )
            self.db.add(classification)
            await self.db.commit()
            await self.db.refresh(classification)
            return classification

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _check_retention_rules(
        self,
        sender_email: str,
        subject: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check if email matches any retention rules.

        Args:
            sender_email: Sender email address
            subject: Email subject

        Returns:
            Dict with action and category if rule matches, None otherwise
        """
        # Get all retention rules ordered by priority
        stmt = select(RetentionRule).order_by(RetentionRule.priority.desc())
        result = await self.db.execute(stmt)
        rules = result.scalars().all()

        for rule in rules:
            matched = False

            if rule.rule_type == "sender":
                matched = sender_email.lower() == rule.pattern.lower()
            elif rule.rule_type == "domain":
                domain = sender_email.split("@")[1] if "@" in sender_email else ""
                matched = domain.lower() == rule.pattern.lower()
            elif rule.rule_type == "subject_contains":
                matched = rule.pattern.lower() in subject.lower()

            if matched:
                return {
                    "action": rule.action,
                    "category": "rule_based",
                    "rule": f"{rule.rule_type}:{rule.pattern}"
                }

        return None

    @staticmethod
    def _get_header_value(headers: List[Dict], name: str) -> str:
        """Get header value by name."""
        for header in headers:
            if header.get("name", "").lower() == name.lower():
                return header.get("value", "")
        return ""

    @staticmethod
    def _extract_email(from_header: str) -> str:
        """Extract email address from From header."""
        import re
        match = re.search(r'<([^>]+)>', from_header)
        if match:
            return match.group(1).lower()
        return from_header.lower()

    @staticmethod
    def _has_attachments(message: Dict[str, Any]) -> bool:
        """Check if message has attachments."""
        parts = message.get("payload", {}).get("parts", [])
        for part in parts:
            if part.get("filename"):
                return True
        return False
