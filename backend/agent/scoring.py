"""
Email Scoring Module for Inbox Nuke Agent - Phase 1.

This module implements a multi-signal scoring system to classify emails as KEEP, DELETE, or UNCERTAIN
without using LLM. It combines Gmail category signals, header analysis, user engagement patterns,
keyword detection, and thread context to produce a comprehensive score.

Scoring System:
- Total score range: 0-100 (higher score = more likely to delete)
- KEEP: score < 30 (important email)
- DELETE: score >= 70 (bulk/junk email)
- UNCERTAIN: score 30-69 (needs review or LLM classification)

Signal Weights (configurable):
1. Gmail Category: 30 points max
2. Headers: 25 points max
3. Engagement: 25 points max
4. Keywords: 20 points max
5. Thread Context: 20 points max (bonus/penalty)
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

from gmail_client import GmailClient

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS - Scoring Weights and Thresholds
# ============================================================================

# Gmail Category Signals (30 points max)
CATEGORY_PROMOTIONS_SCORE = 30
CATEGORY_SOCIAL_SCORE = 30
CATEGORY_UPDATES_SCORE = 30
CATEGORY_FORUMS_SCORE = 25
CATEGORY_PRIMARY_SCORE = -30
CATEGORY_IMPORTANT_SCORE = -30

# Header Signals (25 points max)
HEADER_LIST_UNSUBSCRIBE_SCORE = 15
HEADER_PRECEDENCE_BULK_SCORE = 10
HEADER_PRECEDENCE_LIST_SCORE = 10
HEADER_PRECEDENCE_NORMAL_SCORE = -5

# Engagement Signals (25 points max)
ENGAGEMENT_USER_SENT_SCORE = -25  # User participated in thread
ENGAGEMENT_STARRED_SCORE = -15  # User starred the email
ENGAGEMENT_IMPORTANT_SCORE = -10  # Gmail marked as important
ENGAGEMENT_NO_INTERACTION_SCORE = 10  # No user engagement

# Keyword Signals (20 points max)
KEYWORD_IMPORTANT_SCORE = -20  # Contains protected keywords
KEYWORD_COMMERCIAL_SCORE = 15  # Contains commercial/marketing keywords

# Thread Context Signals (20 points max/penalty)
THREAD_CONVERSATION_SCORE = -20  # Multi-participant conversation
THREAD_SINGLE_SENDER_BULK_SCORE = 10  # Single sender, bulk email

# Classification Thresholds
THRESHOLD_KEEP = 30  # Below this = KEEP
THRESHOLD_DELETE = 70  # Above this = DELETE
# Between = UNCERTAIN

# Important Keywords (protective - presence indicates KEEP)
IMPORTANT_KEYWORDS = [
    # Financial
    "receipt", "invoice", "order", "confirmation", "payment", "transaction",
    "bank", "statement", "refund", "charge",

    # Security
    "password", "verification", "verify", "security", "2fa", "otp",
    "two-factor", "authentication", "reset", "code", "access code",

    # Legal/Government
    "tax", "legal", "court", "insurance", "policy", "contract",

    # Healthcare
    "medical", "health", "prescription", "doctor", "appointment",

    # Education/Career
    "diploma", "degree", "transcript", "employment", "offer letter",
    "acceptance", "enrollment",

    # Travel
    "ticket", "booking", "reservation", "itinerary", "boarding pass",
]

# Commercial Keywords (indicates marketing/promotional content)
COMMERCIAL_KEYWORDS = [
    "unsubscribe", "newsletter", "% off", "percent off", "sale", "deal",
    "discount", "coupon", "promo", "promotion", "offer", "limited time",
    "act now", "free shipping", "buy now", "shop now", "exclusive",
    "special offer", "clearance", "save", "ends soon",
]

# Gmail Category Labels (system labels)
GMAIL_CATEGORY_PROMOTIONS = "CATEGORY_PROMOTIONS"
GMAIL_CATEGORY_SOCIAL = "CATEGORY_SOCIAL"
GMAIL_CATEGORY_UPDATES = "CATEGORY_UPDATES"
GMAIL_CATEGORY_FORUMS = "CATEGORY_FORUMS"
GMAIL_CATEGORY_PRIMARY = "CATEGORY_PERSONAL"
GMAIL_LABEL_IMPORTANT = "IMPORTANT"
GMAIL_LABEL_STARRED = "STARRED"
GMAIL_LABEL_SENT = "SENT"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ScoringResult:
    """
    Result of email scoring with detailed breakdown.

    Attributes:
        message_id: Gmail message ID
        sender_email: Sender's email address
        subject: Email subject line
        total_score: Total score (0-100, higher = more likely to delete)
        classification: KEEP, DELETE, or UNCERTAIN
        confidence: Confidence level (0.0-1.0)
        signal_breakdown: Dictionary of signal scores and reasons
        reasoning: Human-readable explanation of the score
    """
    message_id: str
    sender_email: str
    subject: str
    total_score: int
    classification: str
    confidence: float
    signal_breakdown: Dict[str, Tuple[int, str]] = field(default_factory=dict)
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "message_id": self.message_id,
            "sender_email": self.sender_email,
            "subject": self.subject,
            "total_score": self.total_score,
            "classification": self.classification,
            "confidence": self.confidence,
            "signal_breakdown": {
                signal: {"score": score, "reason": reason}
                for signal, (score, reason) in self.signal_breakdown.items()
            },
            "reasoning": self.reasoning,
        }


# ============================================================================
# EmailScorer Class
# ============================================================================

class EmailScorer:
    """
    Multi-signal email scorer for classification without LLM.

    Combines multiple signals to produce a comprehensive score:
    - Gmail category labels (PROMOTIONS, SOCIAL, etc.)
    - Email headers (List-Unsubscribe, Precedence)
    - User engagement (starred, sent, important)
    - Keywords (important vs commercial)
    - Thread context (conversation vs bulk)

    Usage:
        scorer = EmailScorer(gmail_client)
        result = await scorer.score_email(message)
        print(f"Classification: {result.classification}")
    """

    def __init__(self, gmail_client: GmailClient):
        """
        Initialize the email scorer.

        Args:
            gmail_client: Authenticated GmailClient instance
        """
        self.gmail_client = gmail_client
        self.important_keywords = IMPORTANT_KEYWORDS
        self.commercial_keywords = COMMERCIAL_KEYWORDS

        # Cache for thread info to avoid redundant API calls
        self._thread_cache: Dict[str, Dict[str, Any]] = {}

        logger.info("EmailScorer initialized with multi-signal scoring")

    async def score_email(self, message: Dict[str, Any]) -> ScoringResult:
        """
        Score a single email and return detailed scoring breakdown.

        Args:
            message: Gmail message dictionary (should include metadata format)

        Returns:
            ScoringResult with classification and detailed breakdown

        Raises:
            ValueError: If message is missing required fields

        Example:
            >>> message = await gmail_client.get_message("msg123", format="metadata")
            >>> result = await scorer.score_email(message)
            >>> print(result.classification)
            'DELETE'
        """
        try:
            # Extract basic message info
            message_id = message.get("id", "")
            thread_id = message.get("threadId", "")

            if not message_id:
                raise ValueError("Message missing 'id' field")

            # Extract headers and metadata
            payload = message.get("payload", {})
            headers = payload.get("headers", [])
            label_ids = message.get("labelIds", [])
            snippet = message.get("snippet", "")

            # Extract subject and sender
            subject = self._get_header_value(headers, "subject")
            sender_info = self.gmail_client.get_sender_from_headers(headers)
            sender_email = sender_info.get("email", "unknown")

            # Initialize signal breakdown
            signal_breakdown: Dict[str, Tuple[int, str]] = {}

            # 1. Gmail Category Signal
            category_score, category_reason = self._score_gmail_category(label_ids)
            signal_breakdown["gmail_category"] = (category_score, category_reason)

            # 2. Header Signal
            header_score, header_reason = self._score_headers(headers)
            signal_breakdown["headers"] = (header_score, header_reason)

            # 3. Get thread info for engagement and context scoring
            thread_info = await self._get_thread_info(thread_id)

            # 4. Engagement Signal
            engagement_score, engagement_reason = self._score_engagement(
                message, thread_info
            )
            signal_breakdown["engagement"] = (engagement_score, engagement_reason)

            # 5. Keyword Signal
            keyword_score, keyword_reason = self._score_keywords(subject, snippet)
            signal_breakdown["keywords"] = (keyword_score, keyword_reason)

            # 6. Thread Context Signal
            thread_score, thread_reason = self._score_thread_context(thread_info)
            signal_breakdown["thread_context"] = (thread_score, thread_reason)

            # Calculate total score
            total_score = (
                category_score
                + header_score
                + engagement_score
                + keyword_score
                + thread_score
            )

            # Normalize to 0-100 range
            # Maximum possible score: 30+25+10+15+10 = 90 (delete)
            # Minimum possible score: -30-5-25-20-20 = -100 (keep)
            # Map to 0-100 range
            normalized_score = int(((total_score + 100) / 200) * 100)
            normalized_score = max(0, min(100, normalized_score))

            # Classify based on score
            classification = self._classify_from_score(normalized_score)

            # Calculate confidence (how far from uncertain zone)
            confidence = self._calculate_confidence(normalized_score)

            # Generate human-readable reasoning
            reasoning = self._generate_reasoning(
                classification, normalized_score, signal_breakdown
            )

            result = ScoringResult(
                message_id=message_id,
                sender_email=sender_email,
                subject=subject,
                total_score=normalized_score,
                classification=classification,
                confidence=confidence,
                signal_breakdown=signal_breakdown,
                reasoning=reasoning,
            )

            logger.debug(
                f"Scored email {message_id[:12]}... from {sender_email}: "
                f"{classification} (score={normalized_score}, confidence={confidence:.2f})"
            )

            return result

        except Exception as e:
            logger.error(f"Error scoring email {message.get('id', 'unknown')}: {e}")
            # Return UNCERTAIN on error (safe default)
            return ScoringResult(
                message_id=message.get("id", "unknown"),
                sender_email="unknown",
                subject="[Error scoring email]",
                total_score=50,
                classification="UNCERTAIN",
                confidence=0.0,
                signal_breakdown={"error": (0, str(e))},
                reasoning=f"Error during scoring: {str(e)}",
            )

    async def score_emails_batch(
        self, message_ids: List[str]
    ) -> List[ScoringResult]:
        """
        Score multiple emails efficiently using batch operations.

        Args:
            message_ids: List of Gmail message IDs to score

        Returns:
            List of ScoringResult objects

        Example:
            >>> ids = ["msg1", "msg2", "msg3"]
            >>> results = await scorer.score_emails_batch(ids)
            >>> for result in results:
            ...     print(f"{result.sender_email}: {result.classification}")
        """
        if not message_ids:
            return []

        logger.info(f"Scoring batch of {len(message_ids)} emails")

        try:
            # Fetch all messages in batch (efficient)
            messages = await self.gmail_client.batch_get_messages(
                message_ids, format="metadata"
            )

            # Score each message
            results = []
            for message in messages:
                result = await self.score_email(message)
                results.append(result)

            # Log batch statistics
            classifications = {}
            for result in results:
                classifications[result.classification] = (
                    classifications.get(result.classification, 0) + 1
                )

            logger.info(
                f"Batch scoring complete: {len(results)} emails scored - "
                f"KEEP: {classifications.get('KEEP', 0)}, "
                f"DELETE: {classifications.get('DELETE', 0)}, "
                f"UNCERTAIN: {classifications.get('UNCERTAIN', 0)}"
            )

            return results

        except Exception as e:
            logger.error(f"Error in batch scoring: {e}")
            # Return UNCERTAIN for all on error
            return [
                ScoringResult(
                    message_id=msg_id,
                    sender_email="unknown",
                    subject="[Batch scoring error]",
                    total_score=50,
                    classification="UNCERTAIN",
                    confidence=0.0,
                    signal_breakdown={"error": (0, str(e))},
                    reasoning=f"Batch scoring error: {str(e)}",
                )
                for msg_id in message_ids
            ]

    # ========================================================================
    # Signal Scoring Methods
    # ========================================================================

    def _score_gmail_category(self, label_ids: List[str]) -> Tuple[int, str]:
        """
        Score based on Gmail category labels.

        Args:
            label_ids: List of Gmail label IDs from message

        Returns:
            Tuple of (score, reason)
        """
        # Check for promotional/bulk categories (high delete score)
        if GMAIL_CATEGORY_PROMOTIONS in label_ids:
            return (CATEGORY_PROMOTIONS_SCORE, "Gmail categorized as PROMOTIONS")

        if GMAIL_CATEGORY_SOCIAL in label_ids:
            return (CATEGORY_SOCIAL_SCORE, "Gmail categorized as SOCIAL")

        if GMAIL_CATEGORY_UPDATES in label_ids:
            return (CATEGORY_UPDATES_SCORE, "Gmail categorized as UPDATES")

        if GMAIL_CATEGORY_FORUMS in label_ids:
            return (CATEGORY_FORUMS_SCORE, "Gmail categorized as FORUMS")

        # Check for important categories (negative score = keep)
        if GMAIL_CATEGORY_PRIMARY in label_ids:
            return (CATEGORY_PRIMARY_SCORE, "Gmail categorized as PRIMARY/PERSONAL")

        if GMAIL_LABEL_IMPORTANT in label_ids:
            return (CATEGORY_IMPORTANT_SCORE, "Gmail marked as IMPORTANT")

        # No clear category signal
        return (0, "No Gmail category label detected")

    def _score_headers(self, headers: List[Dict[str, str]]) -> Tuple[int, str]:
        """
        Score based on email headers.

        Args:
            headers: List of header dictionaries with 'name' and 'value'

        Returns:
            Tuple of (score, reason)
        """
        score = 0
        reasons = []

        # Check for List-Unsubscribe header
        unsubscribe_info = self.gmail_client.parse_list_unsubscribe_header(headers)
        if unsubscribe_info.get("mailto") or unsubscribe_info.get("url"):
            score += HEADER_LIST_UNSUBSCRIBE_SCORE
            reasons.append("Has List-Unsubscribe header")

        # Check Precedence header
        precedence = self._get_header_value(headers, "precedence").lower()
        if precedence:
            if precedence in ["bulk", "list", "junk"]:
                score += HEADER_PRECEDENCE_BULK_SCORE
                reasons.append(f"Precedence: {precedence}")
            elif precedence == "normal":
                score += HEADER_PRECEDENCE_NORMAL_SCORE
                reasons.append("Precedence: normal")

        if not reasons:
            return (0, "No significant header signals")

        return (score, "; ".join(reasons))

    def _score_engagement(
        self, message: Dict[str, Any], thread_info: Dict[str, Any]
    ) -> Tuple[int, str]:
        """
        Score based on user engagement signals.

        Args:
            message: Gmail message dictionary
            thread_info: Thread information from get_thread_info

        Returns:
            Tuple of (score, reason)
        """
        label_ids = message.get("labelIds", [])
        score = 0
        reasons = []

        # Check if user sent a message in this thread
        if thread_info.get("has_user_replies"):
            score += ENGAGEMENT_USER_SENT_SCORE
            reasons.append("User participated in conversation")

        # Check if starred
        if GMAIL_LABEL_STARRED in label_ids:
            score += ENGAGEMENT_STARRED_SCORE
            reasons.append("User starred this email")

        # Check if marked important
        if GMAIL_LABEL_IMPORTANT in label_ids:
            score += ENGAGEMENT_IMPORTANT_SCORE
            reasons.append("Gmail marked as important")

        # No engagement signals = likely bulk email
        if not reasons:
            score += ENGAGEMENT_NO_INTERACTION_SCORE
            reasons.append("No user engagement detected")

        return (score, "; ".join(reasons))

    def _score_keywords(self, subject: str, snippet: str) -> Tuple[int, str]:
        """
        Score based on keyword analysis.

        Args:
            subject: Email subject line
            snippet: Email snippet/preview text

        Returns:
            Tuple of (score, reason)
        """
        # Combine subject and snippet for analysis
        text = f"{subject} {snippet}".lower()

        # Check for important keywords (protective)
        important_matches = [
            kw for kw in self.important_keywords
            if kw.lower() in text
        ]

        if important_matches:
            # Use the first 3 matches for reason
            matched_keywords = ", ".join(important_matches[:3])
            return (
                KEYWORD_IMPORTANT_SCORE,
                f"Contains important keywords: {matched_keywords}"
            )

        # Check for commercial keywords
        commercial_matches = [
            kw for kw in self.commercial_keywords
            if kw.lower() in text
        ]

        if commercial_matches:
            matched_keywords = ", ".join(commercial_matches[:3])
            return (
                KEYWORD_COMMERCIAL_SCORE,
                f"Contains commercial keywords: {matched_keywords}"
            )

        return (0, "No significant keywords detected")

    def _score_thread_context(self, thread_info: Dict[str, Any]) -> Tuple[int, str]:
        """
        Score based on thread/conversation context.

        Args:
            thread_info: Thread information from get_thread_info

        Returns:
            Tuple of (score, reason)
        """
        message_count = thread_info.get("message_count", 1)
        participant_count = thread_info.get("participant_count", 1)
        has_user_replies = thread_info.get("has_user_replies", False)

        # Check if this is a conversation
        if message_count >= 2 and (has_user_replies or participant_count >= 2):
            return (
                THREAD_CONVERSATION_SCORE,
                f"Conversation thread: {message_count} messages, {participant_count} participants"
            )

        # Single sender, likely bulk email
        if message_count == 1 and participant_count == 1:
            return (
                THREAD_SINGLE_SENDER_BULK_SCORE,
                "Single message from one sender (likely bulk)"
            )

        return (0, "No clear thread context signal")

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _classify_from_score(self, total_score: int) -> str:
        """
        Convert score to KEEP/DELETE/UNCERTAIN classification.

        Args:
            total_score: Total score (0-100)

        Returns:
            Classification string: KEEP, DELETE, or UNCERTAIN
        """
        if total_score < THRESHOLD_KEEP:
            return "KEEP"
        elif total_score >= THRESHOLD_DELETE:
            return "DELETE"
        else:
            return "UNCERTAIN"

    def _calculate_confidence(self, score: int) -> float:
        """
        Calculate confidence level based on how far from uncertain zone.

        Args:
            score: Total score (0-100)

        Returns:
            Confidence value (0.0-1.0)
        """
        # Distance from uncertain zone
        if score < THRESHOLD_KEEP:
            # KEEP zone: confidence based on distance from 30
            distance = THRESHOLD_KEEP - score
            confidence = min(1.0, distance / THRESHOLD_KEEP)
        elif score >= THRESHOLD_DELETE:
            # DELETE zone: confidence based on distance from 70
            distance = score - THRESHOLD_DELETE
            confidence = min(1.0, distance / (100 - THRESHOLD_DELETE))
        else:
            # UNCERTAIN zone: low confidence (inversely proportional to distance from edges)
            distance_to_keep = score - THRESHOLD_KEEP
            distance_to_delete = THRESHOLD_DELETE - score
            min_distance = min(distance_to_keep, distance_to_delete)
            # Confidence decreases as we move toward center of uncertain zone
            confidence = min_distance / ((THRESHOLD_DELETE - THRESHOLD_KEEP) / 2)

        return round(confidence, 2)

    def _generate_reasoning(
        self,
        classification: str,
        score: int,
        signal_breakdown: Dict[str, Tuple[int, str]]
    ) -> str:
        """
        Generate human-readable reasoning for the classification.

        Args:
            classification: KEEP, DELETE, or UNCERTAIN
            score: Total normalized score
            signal_breakdown: Dictionary of signal scores

        Returns:
            Human-readable reasoning string
        """
        # Sort signals by absolute score impact
        sorted_signals = sorted(
            signal_breakdown.items(),
            key=lambda x: abs(x[1][0]),
            reverse=True
        )

        # Build reasoning
        parts = [f"Classification: {classification} (score: {score}/100)"]

        # Add top 3 contributing signals
        top_signals = sorted_signals[:3]
        if top_signals:
            parts.append("Key factors:")
            for signal_name, (signal_score, reason) in top_signals:
                if signal_score != 0:
                    direction = "→ DELETE" if signal_score > 0 else "→ KEEP"
                    parts.append(f"  • {reason} ({signal_score:+d} {direction})")

        return "\n".join(parts)

    async def _get_thread_info(self, thread_id: str) -> Dict[str, Any]:
        """
        Get thread info with caching.

        Args:
            thread_id: Gmail thread ID

        Returns:
            Thread info dictionary
        """
        if not thread_id:
            return {
                "id": "",
                "message_count": 1,
                "participants": set(),
                "participant_count": 1,
                "has_user_replies": False,
                "snippet": "",
            }

        # Check cache
        if thread_id in self._thread_cache:
            return self._thread_cache[thread_id]

        # Fetch from Gmail API
        try:
            thread_info = await self.gmail_client.get_thread_info(thread_id)
            self._thread_cache[thread_id] = thread_info
            return thread_info
        except Exception as e:
            logger.warning(f"Error fetching thread info for {thread_id}: {e}")
            # Return minimal info on error
            return {
                "id": thread_id,
                "message_count": 1,
                "participants": set(),
                "participant_count": 1,
                "has_user_replies": False,
                "snippet": "",
            }

    @staticmethod
    def _get_header_value(headers: List[Dict[str, str]], header_name: str) -> str:
        """
        Extract header value by name (case-insensitive).

        Args:
            headers: List of header dictionaries
            header_name: Header name to search for

        Returns:
            Header value or empty string if not found
        """
        header_name_lower = header_name.lower()
        for header in headers:
            if header.get("name", "").lower() == header_name_lower:
                return header.get("value", "")
        return ""

    async def refine_uncertain_with_llm(
        self,
        uncertain_results: List[ScoringResult],
        llm_classifier: 'LLMClassifier'
    ) -> List[ScoringResult]:
        """
        Refine UNCERTAIN classifications using LLM.
        Groups emails by sender and uses LLM to classify at sender level.

        Args:
            uncertain_results: List of ScoringResult objects classified as UNCERTAIN
            llm_classifier: LLMClassifier instance for sender classification

        Returns:
            List of ScoringResult objects with refined classifications

        Example:
            >>> llm_classifier = LLMClassifier()
            >>> uncertain = [r for r in results if r.classification == "UNCERTAIN"]
            >>> refined = await scorer.refine_uncertain_with_llm(uncertain, llm_classifier)
        """
        if not uncertain_results:
            logger.info("No uncertain results to refine")
            return []

        logger.info(f"Refining {len(uncertain_results)} uncertain emails with LLM")

        # Group by sender
        senders_data = {}
        for result in uncertain_results:
            sender = result.sender_email
            if sender not in senders_data:
                senders_data[sender] = {
                    'email': sender,
                    'name': None,  # Could extract from message if available
                    'subjects': [],
                    'count': 0,
                    'engagement': {
                        'replied_count': 0,
                        'starred_count': 0,
                        'has_unsubscribe': False
                    }
                }
            senders_data[sender]['subjects'].append(result.subject)
            senders_data[sender]['count'] += 1

        logger.info(f"Grouped {len(uncertain_results)} emails into {len(senders_data)} unique senders")

        # Get LLM classifications for senders
        sender_classifications = await llm_classifier.classify_senders_batch(
            list(senders_data.values())
        )

        # Build sender lookup
        sender_lookup = {sc.sender_email: sc for sc in sender_classifications}

        # Update results with LLM classifications
        refined_results = []
        for result in uncertain_results:
            sender_analysis = sender_lookup.get(result.sender_email)
            if sender_analysis:
                # Update classification and confidence
                result.classification = sender_analysis.classification
                result.confidence = sender_analysis.confidence
                result.reasoning = f"LLM: {sender_analysis.reasoning}\n\nOriginal: {result.reasoning}"

                # Add LLM signal to breakdown
                result.signal_breakdown["llm_refinement"] = (
                    0,  # No numeric score for LLM (used as override)
                    f"LLM classified as {sender_analysis.classification} "
                    f"(confidence: {sender_analysis.confidence:.2f})"
                )

            refined_results.append(result)

        # Log refinement statistics
        refined_classifications = {}
        for result in refined_results:
            refined_classifications[result.classification] = (
                refined_classifications.get(result.classification, 0) + 1
            )

        logger.info(
            f"LLM refinement complete: KEEP: {refined_classifications.get('KEEP', 0)}, "
            f"DELETE: {refined_classifications.get('DELETE', 0)}, "
            f"UNCERTAIN: {refined_classifications.get('UNCERTAIN', 0)}"
        )

        return refined_results

    def clear_cache(self):
        """Clear the thread info cache."""
        self._thread_cache.clear()
        logger.debug("Thread cache cleared")
