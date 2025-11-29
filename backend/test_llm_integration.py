"""
Simple test/demo script for LLM integration.
Tests the LLM classifier without requiring a full database setup.

Usage:
    python test_llm_integration.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agent.llm_classifier import LLMClassifier

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def test_llm_classifier():
    """Test the LLM classifier with sample data."""

    logger.info("=" * 60)
    logger.info("Testing LLM Email Classifier")
    logger.info("=" * 60)

    # Initialize classifier
    classifier = LLMClassifier()

    # Check if available
    if not classifier.is_available():
        logger.warning("LLM classifier not available (OPENAI_API_KEY not set)")
        logger.info("Classifier will default to KEEP for all emails")
        logger.info("\nTo enable LLM classification:")
        logger.info("1. Set OPENAI_API_KEY in backend/.env")
        logger.info("2. Install openai package: pip install openai")
        logger.info("\nContinuing with mock classification...\n")
    else:
        logger.info("LLM classifier is available and ready!")
        logger.info(f"Using model: {classifier.model}\n")

    # Sample senders to classify
    sample_senders = [
        {
            'email': 'newsletter@techcrunch.com',
            'name': 'TechCrunch',
            'subjects': [
                'Daily Crunch: OpenAI launches new model',
                'This Week in Tech: AI breakthroughs',
                'Breaking: Major tech acquisition announced'
            ],
            'count': 45,
            'engagement': {
                'replied_count': 0,
                'starred_count': 1,
                'has_unsubscribe': True
            }
        },
        {
            'email': 'security@bank.com',
            'name': 'Bank Security',
            'subjects': [
                'Security Alert: New device login',
                'Verification code: 123456',
                'Your transaction was approved'
            ],
            'count': 8,
            'engagement': {
                'replied_count': 0,
                'starred_count': 2,
                'has_unsubscribe': False
            }
        },
        {
            'email': 'deals@retailer.com',
            'name': 'Retailer Deals',
            'subjects': [
                '50% OFF Everything - Today Only!',
                'Flash Sale: Limited Time Offer',
                'Your cart is waiting - Complete your purchase'
            ],
            'count': 127,
            'engagement': {
                'replied_count': 0,
                'starred_count': 0,
                'has_unsubscribe': True
            }
        },
        {
            'email': 'john.doe@company.com',
            'name': 'John Doe',
            'subjects': [
                'Re: Project status update',
                'Quick question about the meeting',
                'Fwd: Client feedback'
            ],
            'count': 23,
            'engagement': {
                'replied_count': 15,
                'starred_count': 3,
                'has_unsubscribe': False
            }
        }
    ]

    logger.info(f"Classifying {len(sample_senders)} sample senders...\n")

    # Classify senders
    results = await classifier.classify_senders_batch(sample_senders)

    # Display results
    logger.info("\n" + "=" * 60)
    logger.info("Classification Results")
    logger.info("=" * 60 + "\n")

    for i, (sender, result) in enumerate(zip(sample_senders, results), 1):
        logger.info(f"{i}. {sender['name']} <{sender['email']}>")
        logger.info(f"   Email count: {sender['count']}")
        logger.info(f"   User engagement: replied={sender['engagement']['replied_count']}, "
                   f"starred={sender['engagement']['starred_count']}")
        logger.info(f"   → Classification: {result.classification}")
        logger.info(f"   → Confidence: {result.confidence:.2f}")
        logger.info(f"   → Reasoning: {result.reasoning}")
        if result.email_types:
            logger.info(f"   → Email types: {', '.join(result.email_types)}")
        if result.importance_signals:
            logger.info(f"   → Important signals: {', '.join(result.importance_signals)}")
        logger.info("")

    # Summary statistics
    keep_count = sum(1 for r in results if r.classification == "KEEP")
    delete_count = sum(1 for r in results if r.classification == "DELETE")

    logger.info("=" * 60)
    logger.info("Summary")
    logger.info("=" * 60)
    logger.info(f"Total senders: {len(results)}")
    logger.info(f"KEEP: {keep_count}")
    logger.info(f"DELETE: {delete_count}")

    # Cache test
    logger.info("\n" + "=" * 60)
    logger.info("Testing Cache")
    logger.info("=" * 60)
    logger.info(f"Cache size: {len(classifier.sender_cache)} senders")

    # Re-classify first sender (should use cache)
    logger.info("\nRe-classifying first sender (should use cache)...")
    result2 = await classifier.classify_sender(
        sender_email=sample_senders[0]['email'],
        sender_name=sample_senders[0]['name'],
        sample_subjects=sample_senders[0]['subjects'],
        email_count=sample_senders[0]['count'],
        user_engagement=sample_senders[0]['engagement']
    )
    logger.info(f"Result: {result2.classification} (from cache)")

    # Clear cache
    classifier.clear_cache()
    logger.info("\nCache cleared")
    logger.info(f"Cache size: {len(classifier.sender_cache)} senders")

    logger.info("\n" + "=" * 60)
    logger.info("Test Complete!")
    logger.info("=" * 60)


async def main():
    """Main entry point."""
    try:
        await test_llm_classifier()
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
