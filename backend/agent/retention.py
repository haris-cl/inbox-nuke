"""
Smart retention rules engine.

Applies user-defined and default rules to determine email fate.
Rules are evaluated in priority order to decide whether emails should be kept, deleted, or reviewed.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Sender

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================


class RuleType(Enum):
    """Types of retention rules."""
    SENDER_EMAIL = "sender_email"  # Exact sender match
    SENDER_DOMAIN = "sender_domain"  # Domain match
    SUBJECT_CONTAINS = "subject_contains"  # Subject keyword
    LABEL = "label"  # Gmail label
    HAS_ATTACHMENT = "has_attachment"
    IS_CONVERSATION = "is_conversation"
    OLDER_THAN_DAYS = "older_than_days"
    CATEGORY = "category"  # Gmail category (promotions, social, etc.)


class Action(Enum):
    """Actions that can be taken on emails."""
    KEEP = "KEEP"
    DELETE = "DELETE"
    REVIEW = "REVIEW"


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class RetentionRule:
    """
    A retention rule that determines email fate.

    Attributes:
        rule_type: Type of rule to apply
        pattern: Pattern to match (domain, keyword, etc.)
        action: Action to take (KEEP, DELETE, REVIEW)
        priority: Higher priority rules applied first (default: 0)
        enabled: Whether rule is active (default: True)
        description: Human-readable description
    """
    rule_type: RuleType
    pattern: str
    action: Action
    priority: int = 0
    enabled: bool = True
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary for serialization."""
        return {
            "rule_type": self.rule_type.value,
            "pattern": self.pattern,
            "action": self.action.value,
            "priority": self.priority,
            "enabled": self.enabled,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetentionRule":
        """Create rule from dictionary."""
        return cls(
            rule_type=RuleType(data["rule_type"]),
            pattern=data["pattern"],
            action=Action(data["action"]),
            priority=data.get("priority", 0),
            enabled=data.get("enabled", True),
            description=data.get("description", ""),
        )


@dataclass
class EvaluationResult:
    """
    Result of evaluating an email against retention rules.

    Attributes:
        action: Action to take (KEEP, DELETE, REVIEW)
        matching_rule: Description of the rule that matched
        priority: Priority of the matching rule
        confidence: Confidence score (0-100)
    """
    action: Action
    matching_rule: str
    priority: int
    confidence: int = 100


# ============================================================================
# Retention Engine
# ============================================================================


class RetentionEngine:
    """
    Smart retention rules engine.

    Manages and evaluates retention rules to determine what to do with emails.
    Combines default safety rules with user-defined custom rules.
    """

    def __init__(self):
        """Initialize the retention engine with default rules."""
        self.rules: List[RetentionRule] = []
        self._load_default_rules()

    def _load_default_rules(self):
        """Load default retention rules."""
        # ALWAYS KEEP rules (highest priority: 90-100)
        self.rules.extend([
            # Conversations (highest priority)
            RetentionRule(
                RuleType.IS_CONVERSATION,
                "true",
                Action.KEEP,
                priority=100,
                description="Always keep conversation threads where user participated",
            ),

            # Financial - Critical
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "receipt",
                Action.KEEP,
                priority=95,
                description="Financial receipts and purchase confirmations",
            ),
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "invoice",
                Action.KEEP,
                priority=95,
                description="Invoices and billing statements",
            ),
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "order confirmation",
                Action.KEEP,
                priority=95,
                description="Order confirmations",
            ),
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "e-transfer",
                Action.KEEP,
                priority=95,
                description="E-transfer notifications",
            ),
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "payment",
                Action.KEEP,
                priority=95,
                description="Payment confirmations and notifications",
            ),
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "transaction",
                Action.KEEP,
                priority=95,
                description="Transaction records",
            ),

            # Security - Critical
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "verification code",
                Action.KEEP,
                priority=98,
                description="Verification codes and OTP",
            ),
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "2fa",
                Action.KEEP,
                priority=98,
                description="Two-factor authentication",
            ),
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "two-factor",
                Action.KEEP,
                priority=98,
                description="Two-factor authentication",
            ),
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "password reset",
                Action.KEEP,
                priority=98,
                description="Password reset emails",
            ),
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "security alert",
                Action.KEEP,
                priority=98,
                description="Security alerts and warnings",
            ),
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "sign-in",
                Action.KEEP,
                priority=92,
                description="Sign-in notifications",
            ),

            # Documents - Important
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "diploma",
                Action.KEEP,
                priority=95,
                description="Educational documents",
            ),
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "certificate",
                Action.KEEP,
                priority=95,
                description="Certificates and credentials",
            ),
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "appointment",
                Action.KEEP,
                priority=90,
                description="Appointments and reservations",
            ),
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "reservation",
                Action.KEEP,
                priority=90,
                description="Travel and restaurant reservations",
            ),
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "booking",
                Action.KEEP,
                priority=90,
                description="Booking confirmations",
            ),

            # Medical - Important
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "prescription",
                Action.KEEP,
                priority=95,
                description="Medical prescriptions",
            ),
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "lab results",
                Action.KEEP,
                priority=95,
                description="Medical lab results",
            ),
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "medical",
                Action.KEEP,
                priority=90,
                description="Medical-related emails",
            ),
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "doctor",
                Action.KEEP,
                priority=90,
                description="Doctor communications",
            ),

            # Important domains (Canadian e-transfer, government)
            RetentionRule(
                RuleType.SENDER_DOMAIN,
                "interac.ca",
                Action.KEEP,
                priority=98,
                description="Interac e-transfer notifications",
            ),
            RetentionRule(
                RuleType.SENDER_DOMAIN,
                ".gov",
                Action.KEEP,
                priority=95,
                description="Government emails",
            ),

            # DELETE rules (lower priority: 20-40)
            RetentionRule(
                RuleType.CATEGORY,
                "promotions",
                Action.DELETE,
                priority=30,
                description="Gmail promotions category",
            ),
            RetentionRule(
                RuleType.CATEGORY,
                "social",
                Action.REVIEW,
                priority=25,
                description="Social media notifications",
            ),
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "% off",
                Action.DELETE,
                priority=25,
                description="Discount offers",
            ),
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "sale ends",
                Action.DELETE,
                priority=25,
                description="Sale announcements",
            ),
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "limited time",
                Action.DELETE,
                priority=25,
                description="Limited time offers",
            ),
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "refer a friend",
                Action.DELETE,
                priority=20,
                description="Referral emails",
            ),
            RetentionRule(
                RuleType.SUBJECT_CONTAINS,
                "earn rewards",
                Action.DELETE,
                priority=20,
                description="Rewards program emails",
            ),
        ])

    def evaluate(self, email: Dict[str, Any]) -> EvaluationResult:
        """
        Evaluate an email against all rules.

        Args:
            email: Email dictionary with fields:
                - sender_email: Sender email address
                - sender_domain: Sender domain
                - subject: Email subject
                - labels: List of Gmail labels
                - has_attachment: Whether email has attachments
                - is_conversation: Whether email is part of conversation
                - category: Gmail category (if any)
                - date: Email date

        Returns:
            EvaluationResult with action, matching rule, and priority
        """
        # Sort rules by priority (highest first)
        sorted_rules = sorted(
            [r for r in self.rules if r.enabled],
            key=lambda r: r.priority,
            reverse=True,
        )

        for rule in sorted_rules:
            if self._matches_rule(email, rule):
                return EvaluationResult(
                    action=rule.action,
                    matching_rule=f"{rule.rule_type.value}: {rule.pattern}",
                    priority=rule.priority,
                    confidence=100,
                )

        # No matching rule found - default to REVIEW
        return EvaluationResult(
            action=Action.REVIEW,
            matching_rule="No matching rule (default)",
            priority=0,
            confidence=50,
        )

    def _matches_rule(self, email: Dict[str, Any], rule: RetentionRule) -> bool:
        """
        Check if an email matches a rule.

        Args:
            email: Email dictionary
            rule: Retention rule to check

        Returns:
            True if email matches rule, False otherwise
        """
        try:
            if rule.rule_type == RuleType.SENDER_EMAIL:
                sender_email = email.get("sender_email", "").lower()
                return sender_email == rule.pattern.lower()

            elif rule.rule_type == RuleType.SENDER_DOMAIN:
                sender_domain = email.get("sender_domain", "").lower()
                pattern = rule.pattern.lower()

                # Check for exact match or subdomain match
                if pattern.startswith("."):
                    # Pattern like ".gov" matches all .gov domains
                    return sender_domain.endswith(pattern) or sender_domain == pattern[1:]
                else:
                    # Exact domain match or subdomain
                    return sender_domain == pattern or sender_domain.endswith("." + pattern)

            elif rule.rule_type == RuleType.SUBJECT_CONTAINS:
                subject = email.get("subject", "").lower()
                return rule.pattern.lower() in subject

            elif rule.rule_type == RuleType.LABEL:
                labels = [label.lower() for label in email.get("labels", [])]
                return rule.pattern.lower() in labels

            elif rule.rule_type == RuleType.HAS_ATTACHMENT:
                has_attachment = email.get("has_attachment", False)
                return has_attachment == (rule.pattern.lower() == "true")

            elif rule.rule_type == RuleType.IS_CONVERSATION:
                is_conversation = email.get("is_conversation", False)
                return is_conversation == (rule.pattern.lower() == "true")

            elif rule.rule_type == RuleType.OLDER_THAN_DAYS:
                email_date = email.get("date")
                if email_date:
                    try:
                        days_threshold = int(rule.pattern)
                        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
                        return email_date < cutoff_date
                    except ValueError:
                        logger.warning(f"Invalid days pattern in rule: {rule.pattern}")
                        return False
                return False

            elif rule.rule_type == RuleType.CATEGORY:
                category = email.get("category", "").lower()
                return category == rule.pattern.lower()

            return False

        except Exception as e:
            logger.warning(f"Error matching rule {rule.rule_type}: {e}")
            return False

    def add_rule(self, rule: RetentionRule) -> None:
        """
        Add a custom rule to the engine.

        Args:
            rule: RetentionRule to add
        """
        self.rules.append(rule)
        logger.info(f"Added rule: {rule.description or rule.pattern}")

    def remove_rule(self, rule_index: int) -> bool:
        """
        Remove a rule by its index.

        Args:
            rule_index: Index of rule to remove

        Returns:
            True if rule was removed, False if index invalid
        """
        try:
            if 0 <= rule_index < len(self.rules):
                removed_rule = self.rules.pop(rule_index)
                logger.info(f"Removed rule: {removed_rule.description or removed_rule.pattern}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing rule at index {rule_index}: {e}")
            return False

    def get_rules(self) -> List[Dict[str, Any]]:
        """
        Get all rules as dictionaries.

        Returns:
            List of rule dictionaries
        """
        return [
            {
                **rule.to_dict(),
                "index": idx,
            }
            for idx, rule in enumerate(self.rules)
        ]

    def get_rules_by_priority(self) -> List[Dict[str, Any]]:
        """
        Get all rules sorted by priority.

        Returns:
            List of rule dictionaries sorted by priority (highest first)
        """
        sorted_rules = sorted(
            self.rules,
            key=lambda r: r.priority,
            reverse=True,
        )
        return [rule.to_dict() for rule in sorted_rules]

    def enable_rule(self, rule_index: int) -> bool:
        """
        Enable a rule by index.

        Args:
            rule_index: Index of rule to enable

        Returns:
            True if rule was enabled, False if index invalid
        """
        try:
            if 0 <= rule_index < len(self.rules):
                self.rules[rule_index].enabled = True
                return True
            return False
        except Exception as e:
            logger.error(f"Error enabling rule at index {rule_index}: {e}")
            return False

    def disable_rule(self, rule_index: int) -> bool:
        """
        Disable a rule by index.

        Args:
            rule_index: Index of rule to disable

        Returns:
            True if rule was disabled, False if index invalid
        """
        try:
            if 0 <= rule_index < len(self.rules):
                self.rules[rule_index].enabled = False
                return True
            return False
        except Exception as e:
            logger.error(f"Error disabling rule at index {rule_index}: {e}")
            return False


# ============================================================================
# Helper Functions
# ============================================================================


async def evaluate_sender_emails(
    sender: Sender,
    gmail_client,
    retention_engine: RetentionEngine,
    max_emails: int = 100,
) -> Dict[str, Any]:
    """
    Evaluate emails from a sender using retention rules.

    Args:
        sender: Sender instance
        gmail_client: GmailClient instance
        retention_engine: RetentionEngine instance
        max_emails: Maximum number of emails to evaluate

    Returns:
        Dictionary with evaluation results:
            - total_emails: Total emails evaluated
            - keep_count: Number of emails to keep
            - delete_count: Number of emails to delete
            - review_count: Number of emails to review
            - breakdown: Detailed breakdown by rule
    """
    try:
        # Get emails from this sender with thread info
        query = f"from:{sender.email}"
        emails_with_thread = await gmail_client.get_emails_with_thread_info(
            query=query,
            max_results=max_emails,
        )

        # Evaluate each email
        keep_count = 0
        delete_count = 0
        review_count = 0
        rule_breakdown: Dict[str, int] = {}

        for email_msg in emails_with_thread:
            # Get message details
            message = await gmail_client.get_message(email_msg["id"], format="metadata")

            # Extract subject
            subject = ""
            headers = message.get("payload", {}).get("headers", [])
            for header in headers:
                if header.get("name", "").lower() == "subject":
                    subject = header.get("value", "")
                    break

            # Build email dict for evaluation
            email_data = {
                "sender_email": sender.email,
                "sender_domain": sender.domain,
                "subject": subject,
                "labels": message.get("labelIds", []),
                "has_attachment": len(message.get("payload", {}).get("parts", [])) > 1,
                "is_conversation": email_msg.get("is_conversation", False),
                "category": "",  # TODO: Extract category from labels
                "date": datetime.utcnow(),  # TODO: Parse actual date
            }

            # Evaluate
            result = retention_engine.evaluate(email_data)

            # Count by action
            if result.action == Action.KEEP:
                keep_count += 1
            elif result.action == Action.DELETE:
                delete_count += 1
            else:
                review_count += 1

            # Track rule breakdown
            rule_key = result.matching_rule
            rule_breakdown[rule_key] = rule_breakdown.get(rule_key, 0) + 1

        return {
            "sender_email": sender.email,
            "total_emails": len(emails_with_thread),
            "keep_count": keep_count,
            "delete_count": delete_count,
            "review_count": review_count,
            "breakdown": rule_breakdown,
        }

    except Exception as e:
        logger.error(f"Error evaluating emails for sender {sender.email}: {e}")
        return {
            "sender_email": sender.email,
            "total_emails": 0,
            "keep_count": 0,
            "delete_count": 0,
            "review_count": 0,
            "breakdown": {},
            "error": str(e),
        }
