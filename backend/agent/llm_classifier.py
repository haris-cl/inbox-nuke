"""
LLM-based email classifier for uncertain emails.
Uses OpenAI GPT-4o-mini for cost-effective sender analysis.
Key optimization: Analyze at SENDER level, not individual email level.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

@dataclass
class SenderAnalysis:
    """Result of LLM analysis for a sender."""
    sender_email: str
    classification: str  # KEEP, DELETE
    confidence: float
    reasoning: str
    email_types: List[str]  # e.g., ["newsletter", "promotional"]
    importance_signals: List[str]  # Important patterns found
    analyzed_at: datetime

class LLMClassifier:
    """
    LLM-based classifier for uncertain emails.

    Cost optimization strategy:
    - Analyze at sender level (500 senders) not email level (10,000 emails)
    - Cache sender classifications
    - Use GPT-4o-mini ($0.15/1M tokens) instead of GPT-4 ($30/1M)
    - Batch similar senders together
    """

    SYSTEM_PROMPT = '''You are an email classification assistant helping users clean their inbox.
Your job is to analyze email senders and determine if their emails should be KEPT or DELETED.

Classification Guidelines:

ALWAYS KEEP (even if promotional):
- Financial: banks, payment processors, investment accounts, tax services
- Security: 2FA codes, password resets, security alerts, account verification
- Personal: emails from individual people (not companies), conversations
- Important services: healthcare, insurance, legal, government
- Receipts and order confirmations
- Travel: bookings, itineraries, boarding passes

USUALLY DELETE:
- Newsletters you never read
- Marketing promotions
- Social media notifications
- Promotional offers
- Deal/coupon emails
- Abandoned cart reminders

Consider the following about each sender:
1. Is this a person or a company?
2. What type of emails do they typically send?
3. Would missing an email from them cause problems?
4. Has the user engaged with emails from this sender?'''

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize LLM classifier.

        Args:
            openai_api_key: Optional OpenAI API key. If None, will try to import from config.
        """
        self.sender_cache: Dict[str, SenderAnalysis] = {}
        self.model = "gpt-4o-mini"
        self.client = None

        # Try to initialize OpenAI client
        try:
            if openai_api_key:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=openai_api_key)
            else:
                # Try to get from config
                from config import settings
                if settings.OPENAI_API_KEY:
                    from openai import AsyncOpenAI
                    self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                else:
                    logger.warning("OPENAI_API_KEY not configured. LLM classification disabled.")
        except ImportError:
            logger.warning("OpenAI package not installed. LLM classification disabled.")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}")

    def is_available(self) -> bool:
        """Check if LLM classification is available."""
        return self.client is not None

    async def classify_sender(
        self,
        sender_email: str,
        sender_name: Optional[str],
        sample_subjects: List[str],
        email_count: int,
        user_engagement: Dict[str, Any]
    ) -> SenderAnalysis:
        """
        Classify a sender based on their email patterns.

        Args:
            sender_email: Sender's email address
            sender_name: Display name if available
            sample_subjects: 3-5 sample subject lines from this sender
            email_count: Total emails from this sender
            user_engagement: Dict with replied_count, starred_count, etc.

        Returns:
            SenderAnalysis with classification and reasoning
        """
        # Check if LLM is available
        if not self.is_available():
            logger.debug(f"LLM not available, defaulting to KEEP for {sender_email}")
            return SenderAnalysis(
                sender_email=sender_email,
                classification="KEEP",
                confidence=0.0,
                reasoning="LLM classification not available",
                email_types=[],
                importance_signals=[],
                analyzed_at=datetime.utcnow()
            )

        # Check cache first
        if sender_email in self.sender_cache:
            return self.sender_cache[sender_email]

        # Build prompt
        user_prompt = self._build_sender_prompt(
            sender_email, sender_name, sample_subjects,
            email_count, user_engagement
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,  # Lower for more consistent classification
                max_tokens=500
            )

            # Parse response
            result = json.loads(response.choices[0].message.content)

            analysis = SenderAnalysis(
                sender_email=sender_email,
                classification=result.get("classification", "KEEP"),
                confidence=result.get("confidence", 0.5),
                reasoning=result.get("reasoning", ""),
                email_types=result.get("email_types", []),
                importance_signals=result.get("importance_signals", []),
                analyzed_at=datetime.utcnow()
            )

            # Cache result
            self.sender_cache[sender_email] = analysis

            logger.info(f"LLM classified {sender_email} as {analysis.classification}")
            return analysis

        except Exception as e:
            logger.error(f"LLM classification failed for {sender_email}: {e}")
            # Default to KEEP on error (safe)
            return SenderAnalysis(
                sender_email=sender_email,
                classification="KEEP",
                confidence=0.0,
                reasoning=f"Error during classification: {str(e)}",
                email_types=[],
                importance_signals=[],
                analyzed_at=datetime.utcnow()
            )

    def _build_sender_prompt(
        self,
        sender_email: str,
        sender_name: Optional[str],
        sample_subjects: List[str],
        email_count: int,
        user_engagement: Dict[str, Any]
    ) -> str:
        """Build the user prompt for sender classification."""
        prompt = f"""Analyze this email sender and classify as KEEP or DELETE.

Sender: {sender_name or 'Unknown'} <{sender_email}>
Total emails received: {email_count}

Sample subject lines:
{chr(10).join(f"- {s}" for s in sample_subjects[:5])}

User engagement:
- Replied to: {user_engagement.get('replied_count', 0)} emails
- Starred: {user_engagement.get('starred_count', 0)} emails
- Has unsubscribe link: {user_engagement.get('has_unsubscribe', False)}

Respond with JSON:
{{
    "classification": "KEEP" or "DELETE",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation",
    "email_types": ["type1", "type2"],
    "importance_signals": ["signal1", "signal2"]
}}"""
        return prompt

    async def classify_senders_batch(
        self,
        senders: List[Dict[str, Any]]
    ) -> List[SenderAnalysis]:
        """
        Classify multiple senders in batch.
        Uses asyncio.gather for parallel processing.

        Args:
            senders: List of sender dictionaries with keys:
                - email: sender email address
                - name: display name (optional)
                - subjects: list of sample subject lines
                - count: number of emails
                - engagement: dict with user engagement stats

        Returns:
            List of SenderAnalysis results
        """
        tasks = []
        for sender in senders:
            task = self.classify_sender(
                sender_email=sender['email'],
                sender_name=sender.get('name'),
                sample_subjects=sender.get('subjects', []),
                email_count=sender.get('count', 0),
                user_engagement=sender.get('engagement', {})
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch classification error: {result}")
                # Create default KEEP result for failed classifications
                valid_results.append(SenderAnalysis(
                    sender_email=senders[i]['email'],
                    classification="KEEP",
                    confidence=0.0,
                    reasoning=f"Classification failed: {str(result)}",
                    email_types=[],
                    importance_signals=[],
                    analyzed_at=datetime.utcnow()
                ))
            else:
                valid_results.append(result)

        return valid_results

    def clear_cache(self):
        """Clear the sender classification cache."""
        self.sender_cache.clear()
        logger.info("Sender classification cache cleared")
