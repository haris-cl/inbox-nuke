"""
Tests for the safety module.
Tests protected keywords, domains, whitelist functionality, and message safety checks.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from agent.safety import (
    SafetyCheck,
    SafetyResult,
    contains_protected_keyword,
    is_protected_domain,
    matches_protected_sender_pattern,
    is_whitelisted,
    get_domain_category,
    extract_sender_email,
    extract_domain,
    check_sender_safety,
    check_message_safety,
    get_safety_stats,
)
from models import WhitelistDomain


# ============================================================================
# Protected Keywords Tests
# ============================================================================


class TestProtectedKeywords:
    """Tests for protected keyword detection."""

    def test_contains_protected_keyword_invoice(self):
        """Test detection of 'invoice' keyword."""
        assert contains_protected_keyword("Your invoice is ready") == "invoice"
        assert contains_protected_keyword("INVOICE #12345") == "invoice"

    def test_contains_protected_keyword_receipt(self):
        """Test detection of 'receipt' keyword."""
        assert contains_protected_keyword("Receipt for your purchase") == "receipt"
        assert contains_protected_keyword("ORDER RECEIPT") == "receipt"

    def test_contains_protected_keyword_security(self):
        """Test detection of security-related keywords."""
        assert contains_protected_keyword("Security Alert: New Login") == "security"
        assert contains_protected_keyword("Password reset verification") == "verification"
        assert contains_protected_keyword("Your OTP code is 123456") == "otp"

    def test_contains_protected_keyword_financial(self):
        """Test detection of financial keywords."""
        assert contains_protected_keyword("Bank statement available") == "bank"
        assert contains_protected_keyword("Payment confirmation") == "payment"
        assert contains_protected_keyword("Transaction declined") == "transaction"

    def test_contains_protected_keyword_case_insensitive(self):
        """Test that keyword detection is case-insensitive."""
        assert contains_protected_keyword("INVOICE") == "invoice"
        assert contains_protected_keyword("Invoice") == "invoice"
        assert contains_protected_keyword("invoice") == "invoice"

    def test_no_protected_keyword(self):
        """Test that non-protected text returns None."""
        assert contains_protected_keyword("Hello, how are you?") is None
        assert contains_protected_keyword("Weekly newsletter") is None
        assert contains_protected_keyword("Special offer inside!") is None

    def test_protected_keyword_word_boundary(self):
        """Test that keywords must match word boundaries."""
        # "invoice" should match
        assert contains_protected_keyword("invoice123") is None  # No word boundary
        assert contains_protected_keyword("invoice ") == "invoice"  # Word boundary
        assert contains_protected_keyword(" invoice") == "invoice"  # Word boundary


# ============================================================================
# Protected Domains Tests
# ============================================================================


class TestProtectedDomains:
    """Tests for protected domain detection."""

    def test_protected_domain_bank(self):
        """Test detection of bank domains."""
        assert is_protected_domain("chase.com") is True
        assert is_protected_domain("bankofamerica.com") is True
        assert is_protected_domain("wellsfargo.com") is True

    def test_protected_domain_payment(self):
        """Test detection of payment processor domains."""
        assert is_protected_domain("paypal.com") is True
        assert is_protected_domain("stripe.com") is True
        assert is_protected_domain("venmo.com") is True

    def test_protected_domain_government(self):
        """Test detection of .gov domains."""
        assert is_protected_domain("irs.gov") is True
        assert is_protected_domain("ssa.gov") is True
        assert is_protected_domain("state.gov") is True
        assert is_protected_domain("anydomain.gov") is True  # All .gov protected

    def test_protected_domain_military(self):
        """Test detection of .mil domains."""
        assert is_protected_domain("army.mil") is True
        assert is_protected_domain("navy.mil") is True
        assert is_protected_domain("anydomain.mil") is True  # All .mil protected

    def test_protected_domain_subdomain(self):
        """Test detection of subdomains of protected domains."""
        assert is_protected_domain("alerts.chase.com") is True
        assert is_protected_domain("noreply.paypal.com") is True
        assert is_protected_domain("secure.bankofamerica.com") is True

    def test_protected_domain_case_insensitive(self):
        """Test that domain matching is case-insensitive."""
        assert is_protected_domain("CHASE.COM") is True
        assert is_protected_domain("Chase.Com") is True
        assert is_protected_domain("IRS.GOV") is True

    def test_not_protected_domain(self):
        """Test that non-protected domains return False."""
        assert is_protected_domain("example.com") is False
        assert is_protected_domain("newsletter.com") is False
        assert is_protected_domain("marketing.org") is False

    def test_protected_domain_empty_input(self):
        """Test handling of empty input."""
        assert is_protected_domain("") is False
        assert is_protected_domain(None) is False


# ============================================================================
# Protected Sender Patterns Tests
# ============================================================================


class TestProtectedSenderPatterns:
    """Tests for protected sender pattern matching."""

    def test_matches_noreply_bank(self):
        """Test matching of noreply@*bank* patterns."""
        assert matches_protected_sender_pattern("noreply@chase.com") is True
        assert matches_protected_sender_pattern("noreply@mybank.com") is True
        assert matches_protected_sender_pattern("no-reply@bank.com") is True

    def test_matches_security_sender(self):
        """Test matching of security@ patterns."""
        assert matches_protected_sender_pattern("security@example.com") is True
        assert matches_protected_sender_pattern("alert@company.com") is True
        assert matches_protected_sender_pattern("alerts@service.com") is True

    def test_matches_verification_sender(self):
        """Test matching of verification@ patterns."""
        assert matches_protected_sender_pattern("verification@example.com") is True
        assert matches_protected_sender_pattern("verify@service.com") is True

    def test_matches_fraud_sender(self):
        """Test matching of fraud@ patterns."""
        assert matches_protected_sender_pattern("fraud@bank.com") is True
        assert matches_protected_sender_pattern("disputes@company.com") is True

    def test_not_matches_regular_sender(self):
        """Test that regular senders don't match."""
        assert matches_protected_sender_pattern("newsletter@example.com") is False
        assert matches_protected_sender_pattern("marketing@company.com") is False
        assert matches_protected_sender_pattern("hello@service.com") is False


# ============================================================================
# Whitelist Tests
# ============================================================================


class TestWhitelist:
    """Tests for whitelist functionality."""

    @pytest.mark.asyncio
    async def test_is_whitelisted_found(self, test_db: AsyncSession):
        """Test detection of whitelisted domain."""
        # Add domain to whitelist
        domain = WhitelistDomain(domain="important.com", reason="Test")
        test_db.add(domain)
        await test_db.commit()

        assert await is_whitelisted("important.com", test_db) is True

    @pytest.mark.asyncio
    async def test_is_whitelisted_not_found(self, test_db: AsyncSession):
        """Test that non-whitelisted domain returns False."""
        assert await is_whitelisted("example.com", test_db) is False

    @pytest.mark.asyncio
    async def test_is_whitelisted_case_insensitive(self, test_db: AsyncSession):
        """Test that whitelist check is case-insensitive."""
        domain = WhitelistDomain(domain="important.com", reason="Test")
        test_db.add(domain)
        await test_db.commit()

        assert await is_whitelisted("IMPORTANT.COM", test_db) is True
        assert await is_whitelisted("Important.Com", test_db) is True

    @pytest.mark.asyncio
    async def test_is_whitelisted_empty_input(self, test_db: AsyncSession):
        """Test handling of empty input."""
        assert await is_whitelisted("", test_db) is False
        assert await is_whitelisted(None, test_db) is False


# ============================================================================
# Domain Category Tests
# ============================================================================


class TestDomainCategory:
    """Tests for domain categorization."""

    def test_category_government(self):
        """Test government domain categorization."""
        assert get_domain_category("irs.gov") == "government"
        assert get_domain_category("state.gov") == "government"
        assert get_domain_category("army.mil") == "government"

    def test_category_financial(self):
        """Test financial domain categorization."""
        assert get_domain_category("chase.com") == "financial"
        assert get_domain_category("bankofamerica.com") == "financial"
        assert get_domain_category("paypal.com") == "financial"
        assert get_domain_category("turbotax.com") == "financial"

    def test_category_healthcare(self):
        """Test healthcare domain categorization."""
        assert get_domain_category("anthem.com") == "healthcare"
        assert get_domain_category("aetna.com") == "healthcare"
        assert get_domain_category("bluecross.com") == "healthcare"
        assert get_domain_category("kaiser.com") == "healthcare"

    def test_category_unknown(self):
        """Test unknown domain categorization."""
        assert get_domain_category("example.com") == "unknown"
        assert get_domain_category("newsletter.com") == "unknown"


# ============================================================================
# Extraction Tests
# ============================================================================


class TestExtraction:
    """Tests for email and domain extraction."""

    def test_extract_sender_email(self, sample_gmail_message):
        """Test extraction of sender email from message."""
        email = extract_sender_email(sample_gmail_message)
        assert email == "test@example.com"

    def test_extract_sender_email_protected(self, sample_protected_message):
        """Test extraction from protected message."""
        email = extract_sender_email(sample_protected_message)
        assert email == "noreply@chase.com"

    def test_extract_sender_email_no_from_header(self):
        """Test handling of message without From header."""
        message = {
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test"},
                ]
            }
        }
        assert extract_sender_email(message) is None

    def test_extract_domain_valid_email(self):
        """Test domain extraction from valid email."""
        assert extract_domain("user@example.com") == "example.com"
        assert extract_domain("test@subdomain.example.com") == "subdomain.example.com"

    def test_extract_domain_invalid_email(self):
        """Test handling of invalid email."""
        assert extract_domain("invalid") is None
        assert extract_domain("no-at-sign.com") is None
        assert extract_domain("") is None


# ============================================================================
# Sender Safety Tests
# ============================================================================


class TestCheckSenderSafety:
    """Tests for sender safety checks."""

    @pytest.mark.asyncio
    async def test_safe_sender(self, test_db: AsyncSession):
        """Test that regular sender is marked safe."""
        result = await check_sender_safety("newsletter@example.com", test_db)
        assert result.is_safe is True
        assert result.check == SafetyCheck.SAFE

    @pytest.mark.asyncio
    async def test_whitelisted_sender(self, test_db: AsyncSession):
        """Test that whitelisted sender is protected."""
        domain = WhitelistDomain(domain="important.com", reason="Test")
        test_db.add(domain)
        await test_db.commit()

        result = await check_sender_safety("user@important.com", test_db)
        assert result.is_safe is False
        assert result.check == SafetyCheck.WHITELISTED

    @pytest.mark.asyncio
    async def test_protected_domain_sender(self, test_db: AsyncSession):
        """Test that sender from protected domain is protected."""
        result = await check_sender_safety("noreply@chase.com", test_db)
        assert result.is_safe is False
        assert result.check == SafetyCheck.PROTECTED_DOMAIN

    @pytest.mark.asyncio
    async def test_protected_pattern_sender(self, test_db: AsyncSession):
        """Test that sender matching protected pattern is protected."""
        result = await check_sender_safety("security@example.com", test_db)
        assert result.is_safe is False
        assert result.check == SafetyCheck.IMPORTANT_SENDER


# ============================================================================
# Message Safety Tests
# ============================================================================


class TestCheckMessageSafety:
    """Tests for comprehensive message safety checks."""

    @pytest.mark.asyncio
    async def test_safe_message(self, test_db: AsyncSession):
        """Test that regular message is marked safe."""
        message = {
            "payload": {
                "headers": [
                    {"name": "From", "value": "newsletter@example.com"},
                    {"name": "Subject", "value": "Weekly Updates"},
                ]
            },
            "snippet": "Here are this week's top stories",
        }
        result = await check_message_safety(message, test_db)
        assert result.is_safe is True
        assert result.check == SafetyCheck.SAFE

    @pytest.mark.asyncio
    async def test_protected_by_subject_keyword(self, test_db: AsyncSession):
        """Test that message with protected keyword in subject is protected."""
        message = {
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Subject", "value": "Your Invoice is Ready"},
                ]
            },
            "snippet": "Thank you for your purchase",
        }
        result = await check_message_safety(message, test_db)
        assert result.is_safe is False
        assert result.check == SafetyCheck.PROTECTED_KEYWORD
        assert "invoice" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_protected_by_snippet_keyword(self, test_db: AsyncSession):
        """Test that message with protected keyword in snippet is protected."""
        message = {
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Subject", "value": "Important Notice"},
                ]
            },
            "snippet": "Your bank statement is ready for review",
        }
        result = await check_message_safety(message, test_db)
        assert result.is_safe is False
        assert result.check == SafetyCheck.PROTECTED_KEYWORD

    @pytest.mark.asyncio
    async def test_protected_by_sender(self, test_db: AsyncSession, sample_protected_message):
        """Test that message from protected sender is protected."""
        result = await check_message_safety(sample_protected_message, test_db)
        assert result.is_safe is False
        assert result.check == SafetyCheck.PROTECTED_DOMAIN


# ============================================================================
# Safety Stats Tests
# ============================================================================


class TestSafetyStats:
    """Tests for safety statistics."""

    @pytest.mark.asyncio
    async def test_get_safety_stats(self, test_db_with_data: AsyncSession):
        """Test retrieval of safety statistics."""
        stats = await get_safety_stats(test_db_with_data)

        assert "protected_keywords_count" in stats
        assert "protected_domains_count" in stats
        assert "protected_patterns_count" in stats
        assert "whitelisted_domains_count" in stats

        # Check that counts are positive
        assert stats["protected_keywords_count"] > 0
        assert stats["protected_domains_count"] > 0
        assert stats["protected_patterns_count"] > 0

        # We added 2 whitelist domains in test_db_with_data
        assert stats["whitelisted_domains_count"] == 2
