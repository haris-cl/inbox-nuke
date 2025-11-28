"""
Safety guardrails module for the Inbox Nuke Agent.

This module implements safety checks to prevent deletion of important emails.
All checks are conservative - when in doubt, protect the email.
"""

import re
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from email.utils import parseaddr

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import WhitelistDomain


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS - Protected Keywords, Domains, and Sender Patterns
# ============================================================================

PROTECTED_KEYWORDS = [
    # Financial
    "invoice",
    "receipt",
    "confirmation",
    "order",
    "bank",
    "payment",
    "statement",
    "transaction",

    # Tax and Legal
    "tax",
    "irs",
    "w2",
    "w-2",
    "1099",

    # Security and Authentication
    "verification",
    "verification code",
    "verify your",
    "security",
    "security alert",
    "unusual activity",
    "suspicious activity",
    "alert",
    "password",
    "password reset",
    "reset password",
    "change password",
    "2fa",
    "two-factor",
    "two factor",
    "otp",
    "one-time password",
    "verify",
    "authenticate",
    "authentication",
    "sign-in",
    "sign in",
    "login",
    "log in",
    "access code",
    "confirmation code",
    "credential",
    "credentials",

    # Healthcare
    "insurance",
    "healthcare",
    "medical",
    "prescription",
    "doctor",
    "hospital",

    # Legal
    "legal",
    "court",
    "subpoena",
    "lawsuit",
    "attorney",
    "lawyer",

    # Government
    "government",
    "dmv",
    "passport",
    "visa",
    "immigration",
]


PROTECTED_DOMAINS = [
    # Major US Banks
    "chase.com",
    "bankofamerica.com",
    "wellsfargo.com",
    "citibank.com",
    "usbank.com",
    "pnc.com",
    "capitalone.com",
    "tdbank.com",
    "schwab.com",
    "ally.com",

    # Payment Processors
    "paypal.com",
    "venmo.com",
    "stripe.com",
    "square.com",
    "zelle.com",
    "applepay.com",

    # Investment/Financial Services
    "fidelity.com",
    "vanguard.com",
    "etrade.com",
    "robinhood.com",
    "coinbase.com",
    "betterment.com",
    "wealthfront.com",

    # Tax Services
    "turbotax.com",
    "hrblock.com",
    "taxact.com",
    "freetaxusa.com",

    # Healthcare/Insurance
    "anthem.com",
    "uhc.com",
    "aetna.com",
    "cigna.com",
    "bluecross.com",
    "blueshield.com",
    "humana.com",
    "kaiserpermanente.org",

    # Credit Bureaus
    "experian.com",
    "equifax.com",
    "transunion.com",

    # Utilities
    "att.com",
    "verizon.com",
    "tmobile.com",
    "sprint.com",
    "comcast.com",
    "spectrum.com",

    # Government (handled separately via .gov TLD)
    "irs.gov",
    "usps.com",
    "usps.gov",
    "ssa.gov",
    "state.gov",
]


PROTECTED_SENDER_PATTERNS = [
    r"noreply@.*bank.*\.com",
    r"security@.*\.com",
    r"alert@.*\.com",
    r"alerts@.*\.com",
    r"verification@.*\.com",
    r"verify@.*\.com",
    r"no-?reply@.*bank.*",
    r"notifications?@.*bank.*",
    r"fraud@.*",
    r"disputes?@.*",
]


# Compile patterns for performance
_compiled_sender_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in PROTECTED_SENDER_PATTERNS]
_compiled_keyword_pattern = re.compile(
    r'\b(' + '|'.join(re.escape(kw) for kw in PROTECTED_KEYWORDS) + r')\b',
    re.IGNORECASE
)


# ============================================================================
# JUNK/SPAM DETECTION PATTERNS
# ============================================================================

# Keywords that indicate promotional/spam emails (subject line patterns)
JUNK_SUBJECT_PATTERNS = [
    # Discounts and offers
    r'\d+%\s*off',
    r'percent\s*off',
    r'\bsale\b',
    r'\bdeal\b',
    r'\bdeals\b',
    r'\boffer\b',
    r'\boffers\b',
    r'\bdiscount\b',
    r'\bcoupon\b',
    r'\bpromo\b',
    r'\bpromotion\b',
    r'\bsave\s*\$',
    r'\bfree\s*shipping\b',
    r'\blimited\s*time\b',

    # Newsletter patterns
    r'\bnewsletter\b',
    r'\bweekly\s*digest\b',
    r'\bdaily\s*update\b',
    r'\bmonthly\s*roundup\b',
    r'\bthis\s*week\b',

    # Unsubscribe mentions (ironically)
    r'\bunsubscribe\b',
]

# Email address patterns that indicate spam/marketing
JUNK_SENDER_PATTERNS = [
    r'^noreply@',
    r'^no-reply@',
    r'^no\.reply@',
    r'^donotreply@',
    r'^do-not-reply@',
    r'^newsletter@',
    r'^newsletters@',
    r'^marketing@',
    r'^promo@',
    r'^promotions@',
    r'^offers@',
    r'^deals@',
    r'^sales@',
    r'^updates@',
    r'^notifications@',
    r'^news@',
    r'^info@',
    r'^hello@.*\.(com|net|org)',
    r'^hi@.*\.(com|net|org)',
]

# Compile junk patterns for performance
_compiled_junk_subject_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in JUNK_SUBJECT_PATTERNS]
_compiled_junk_sender_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in JUNK_SENDER_PATTERNS]


# ============================================================================
# JUNK DETECTION FUNCTIONS
# ============================================================================

def is_junk_sender(sender_email: str) -> bool:
    """
    Check if sender email matches junk/spam patterns.

    Args:
        sender_email: Email address to check

    Returns:
        True if sender matches junk patterns, False otherwise
    """
    if not sender_email:
        return False

    for pattern in _compiled_junk_sender_patterns:
        if pattern.search(sender_email):
            return True

    return False


def is_junk_subject(subject: str) -> bool:
    """
    Check if subject line matches junk/promotional patterns.

    Args:
        subject: Email subject to check

    Returns:
        True if subject matches junk patterns, False otherwise
    """
    if not subject:
        return False

    for pattern in _compiled_junk_subject_patterns:
        if pattern.search(subject):
            return True

    return False


def calculate_junk_score(sender_email: str, subject: str, has_unsubscribe: bool) -> int:
    """
    Calculate a junk score for an email (0-100, higher = more likely junk).

    Args:
        sender_email: Sender email address
        subject: Email subject line
        has_unsubscribe: Whether email has List-Unsubscribe header

    Returns:
        Junk score (0-100)
    """
    score = 0

    # Check sender patterns (40 points)
    if is_junk_sender(sender_email):
        score += 40

    # Check subject patterns (30 points)
    if is_junk_subject(subject):
        score += 30

    # Has List-Unsubscribe header (30 points)
    if has_unsubscribe:
        score += 30

    return min(score, 100)


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class SafetyCheck(Enum):
    """Enum representing the result of a safety check."""
    SAFE = "safe"
    PROTECTED_KEYWORD = "protected_keyword"
    PROTECTED_DOMAIN = "protected_domain"
    WHITELISTED = "whitelisted"
    IMPORTANT_SENDER = "important_sender"


@dataclass
class SafetyResult:
    """Result of a safety check operation."""
    is_safe: bool
    check: SafetyCheck
    reason: str


# ============================================================================
# CORE SAFETY FUNCTIONS
# ============================================================================

def contains_protected_keyword(text: str) -> Optional[str]:
    """
    Check if text contains any protected keywords.

    Args:
        text: Text to check (subject, snippet, etc.)

    Returns:
        The matched keyword if found, None otherwise
    """
    if not text:
        return None

    match = _compiled_keyword_pattern.search(text)
    if match:
        return match.group(1).lower()

    return None


def is_protected_domain(domain: str) -> bool:
    """
    Check if domain matches protected domain patterns.

    Handles:
    - .gov and other special TLDs
    - Common domain variations
    - Case-insensitive matching

    Args:
        domain: Domain to check

    Returns:
        True if domain is protected, False otherwise
    """
    if not domain:
        return False

    domain_lower = domain.lower().strip()

    # Check for .gov TLD (all government domains are protected)
    if domain_lower.endswith('.gov'):
        return True

    # Check for .mil TLD (military domains are protected)
    if domain_lower.endswith('.mil'):
        return True

    # Check exact match in protected domains
    if domain_lower in PROTECTED_DOMAINS:
        return True

    # Check if domain is a subdomain of any protected domain
    for protected in PROTECTED_DOMAINS:
        if domain_lower.endswith('.' + protected):
            return True

    return False


def matches_protected_sender_pattern(sender_email: str) -> bool:
    """
    Check if sender email matches any protected sender patterns.

    Args:
        sender_email: Email address to check

    Returns:
        True if email matches protected pattern, False otherwise
    """
    if not sender_email:
        return False

    for pattern in _compiled_sender_patterns:
        if pattern.search(sender_email):
            return True

    return False


async def is_whitelisted(domain: str, db: AsyncSession) -> bool:
    """
    Check if domain is in the user's whitelist.

    Args:
        domain: Domain to check
        db: Database session

    Returns:
        True if domain is whitelisted, False otherwise
    """
    if not domain:
        return False

    domain_lower = domain.lower().strip()

    try:
        result = await db.execute(
            select(WhitelistDomain).where(
                WhitelistDomain.domain == domain_lower
            )
        )
        whitelist_entry = result.scalar_one_or_none()
        return whitelist_entry is not None
    except Exception as e:
        logger.error(f"Error checking whitelist for domain {domain}: {e}")
        return False


def get_domain_category(domain: str) -> str:
    """
    Categorize domain for reporting purposes.

    Args:
        domain: Domain to categorize

    Returns:
        Category: financial, government, healthcare, or unknown
    """
    if not domain:
        return "unknown"

    domain_lower = domain.lower()

    # Government
    if domain_lower.endswith('.gov') or domain_lower.endswith('.mil'):
        return "government"

    # Financial institutions
    financial_keywords = ['bank', 'fidelity', 'vanguard', 'schwab', 'etrade',
                         'robinhood', 'coinbase', 'paypal', 'venmo', 'stripe',
                         'square', 'capitalone', 'chase', 'wellsfargo', 'citi']
    if any(keyword in domain_lower for keyword in financial_keywords):
        return "financial"

    # Healthcare
    healthcare_keywords = ['health', 'medical', 'hospital', 'insurance', 'anthem',
                          'aetna', 'cigna', 'kaiser', 'bluecross', 'blueshield',
                          'humana', 'uhc']
    if any(keyword in domain_lower for keyword in healthcare_keywords):
        return "healthcare"

    # Tax services
    tax_keywords = ['tax', 'irs']
    if any(keyword in domain_lower for keyword in tax_keywords):
        return "financial"

    return "unknown"


def extract_sender_email(message: dict) -> Optional[str]:
    """
    Extract sender email from message headers.

    Args:
        message: Gmail message dict with headers

    Returns:
        Sender email address or None
    """
    try:
        headers = message.get('payload', {}).get('headers', [])
        for header in headers:
            if header['name'].lower() == 'from':
                # Parse "Display Name <email@domain.com>" format
                _, email = parseaddr(header['value'])
                return email.lower() if email else None
        return None
    except Exception as e:
        logger.error(f"Error extracting sender email: {e}")
        return None


def extract_domain(email: str) -> Optional[str]:
    """
    Extract domain from email address.

    Args:
        email: Email address

    Returns:
        Domain portion or None
    """
    if not email or '@' not in email:
        return None

    try:
        return email.split('@')[1].lower()
    except Exception:
        return None


async def check_sender_safety(sender_email: str, db: AsyncSession) -> SafetyResult:
    """
    Check if sender email is safe to process.

    Checks (in priority order):
    1. User whitelist (highest priority - user explicitly trusts this)
    2. Protected sender patterns (security-related senders)
    3. Protected domains (banks, government, etc.)

    Args:
        sender_email: Email address to check
        db: Database session

    Returns:
        SafetyResult with check result and reason
    """
    if not sender_email:
        return SafetyResult(
            is_safe=True,
            check=SafetyCheck.SAFE,
            reason="No sender email provided"
        )

    sender_email = sender_email.lower().strip()
    domain = extract_domain(sender_email)

    # Check 1: User whitelist (highest priority)
    if domain and await is_whitelisted(domain, db):
        category = get_domain_category(domain)
        return SafetyResult(
            is_safe=False,
            check=SafetyCheck.WHITELISTED,
            reason=f"Domain {domain} is in user whitelist ({category})"
        )

    # Check 2: Protected sender patterns
    if matches_protected_sender_pattern(sender_email):
        return SafetyResult(
            is_safe=False,
            check=SafetyCheck.IMPORTANT_SENDER,
            reason=f"Sender {sender_email} matches protected pattern (security/verification)"
        )

    # Check 3: Protected domains
    if domain and is_protected_domain(domain):
        category = get_domain_category(domain)
        return SafetyResult(
            is_safe=False,
            check=SafetyCheck.PROTECTED_DOMAIN,
            reason=f"Domain {domain} is protected ({category})"
        )

    return SafetyResult(
        is_safe=True,
        check=SafetyCheck.SAFE,
        reason="No safety concerns detected"
    )


async def check_message_safety(message: dict, db: AsyncSession) -> SafetyResult:
    """
    Comprehensive safety check for an email message.

    Checks (in priority order):
    1. Sender safety (whitelist, protected domains, patterns)
    2. Subject for protected keywords
    3. Snippet/preview for protected keywords

    Args:
        message: Gmail message dict
        db: Database session

    Returns:
        SafetyResult with the most important safety concern found
    """
    # Check 1: Sender safety (highest priority)
    sender_email = extract_sender_email(message)
    if sender_email:
        sender_result = await check_sender_safety(sender_email, db)
        if not sender_result.is_safe:
            return sender_result

    # Check 2: Subject for protected keywords
    subject = None
    headers = message.get('payload', {}).get('headers', [])
    for header in headers:
        if header['name'].lower() == 'subject':
            subject = header['value']
            break

    if subject:
        keyword = contains_protected_keyword(subject)
        if keyword:
            return SafetyResult(
                is_safe=False,
                check=SafetyCheck.PROTECTED_KEYWORD,
                reason=f"Subject contains protected keyword: '{keyword}'"
            )

    # Check 3: Snippet for protected keywords
    snippet = message.get('snippet', '')
    if snippet:
        keyword = contains_protected_keyword(snippet)
        if keyword:
            return SafetyResult(
                is_safe=False,
                check=SafetyCheck.PROTECTED_KEYWORD,
                reason=f"Message snippet contains protected keyword: '{keyword}'"
            )

    return SafetyResult(
        is_safe=True,
        check=SafetyCheck.SAFE,
        reason="No safety concerns detected"
    )


# ============================================================================
# STATISTICS AND REPORTING
# ============================================================================

async def get_safety_stats(db: AsyncSession) -> dict:
    """
    Return safety statistics for monitoring and reporting.

    Args:
        db: Database session

    Returns:
        Dict with counts: protected_keywords, protected_domains, whitelisted, safe
    """
    try:
        # Get whitelist count
        result = await db.execute(select(WhitelistDomain))
        whitelisted_count = len(result.scalars().all())

        return {
            "protected_keywords_count": len(PROTECTED_KEYWORDS),
            "protected_domains_count": len(PROTECTED_DOMAINS),
            "protected_patterns_count": len(PROTECTED_SENDER_PATTERNS),
            "whitelisted_domains_count": whitelisted_count,
            "categories": {
                "financial": len([d for d in PROTECTED_DOMAINS if 'bank' in d or 'pay' in d or 'fidelity' in d or 'vanguard' in d or 'schwab' in d]),
                "government": "all .gov and .mil domains",
                "healthcare": len([d for d in PROTECTED_DOMAINS if any(kw in d for kw in ['health', 'medical', 'anthem', 'aetna', 'cigna', 'kaiser', 'blue'])]),
            }
        }
    except Exception as e:
        logger.error(f"Error getting safety stats: {e}")
        return {
            "protected_keywords_count": len(PROTECTED_KEYWORDS),
            "protected_domains_count": len(PROTECTED_DOMAINS),
            "protected_patterns_count": len(PROTECTED_SENDER_PATTERNS),
            "whitelisted_domains_count": 0,
            "error": str(e)
        }
