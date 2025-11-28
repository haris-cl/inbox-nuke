"""
Inbox Nuke Agent Module

This module contains the AI agent logic and safety guardrails
for intelligent email cleanup operations.
"""

from agent.safety import (
    SafetyCheck,
    SafetyResult,
    check_sender_safety,
    check_message_safety,
    contains_protected_keyword,
    is_protected_domain,
    is_whitelisted,
    get_domain_category,
    get_safety_stats,
    PROTECTED_KEYWORDS,
    PROTECTED_DOMAINS,
    PROTECTED_SENDER_PATTERNS,
)

from agent.unsubscribe import (
    UnsubscribeResult,
    unsubscribe_via_mailto,
    unsubscribe_via_http,
    unsubscribe,
)

from agent.filters import (
    create_mute_filter,
    check_filter_exists,
    get_muted_label_id,
    get_or_create_domain_label,
    create_filters_for_senders,
    delete_filter_for_sender,
    clear_label_cache,
)

from agent.cleanup import (
    CleanupResult,
    delete_emails_from_sender,
    cleanup_large_attachments,
    cleanup_category,
    cleanup_multiple_senders,
)

from agent.discovery import (
    discover_senders,
    discover_new_senders,
    get_sender_stats,
)

from agent.runner import (
    CleanupAgent,
    ActionResult,
)

from agent.scheduler import (
    init_scheduler,
    shutdown_scheduler,
    get_scheduler,
    schedule_cleanup_run,
    get_running_jobs,
    cancel_job,
    pause_job,
    resume_job,
    get_scheduler_status,
)

__all__ = [
    # Safety
    "SafetyCheck",
    "SafetyResult",
    "check_sender_safety",
    "check_message_safety",
    "contains_protected_keyword",
    "is_protected_domain",
    "is_whitelisted",
    "get_domain_category",
    "get_safety_stats",
    "PROTECTED_KEYWORDS",
    "PROTECTED_DOMAINS",
    "PROTECTED_SENDER_PATTERNS",
    # Unsubscribe
    "UnsubscribeResult",
    "unsubscribe_via_mailto",
    "unsubscribe_via_http",
    "unsubscribe",
    # Filters
    "create_mute_filter",
    "check_filter_exists",
    "get_muted_label_id",
    "get_or_create_domain_label",
    "create_filters_for_senders",
    "delete_filter_for_sender",
    "clear_label_cache",
    # Cleanup
    "CleanupResult",
    "delete_emails_from_sender",
    "cleanup_large_attachments",
    "cleanup_category",
    "cleanup_multiple_senders",
    # Discovery
    "discover_senders",
    "discover_new_senders",
    "get_sender_stats",
    # Runner
    "CleanupAgent",
    "ActionResult",
    # Scheduler
    "init_scheduler",
    "shutdown_scheduler",
    "get_scheduler",
    "schedule_cleanup_run",
    "get_running_jobs",
    "cancel_job",
    "pause_job",
    "resume_job",
    "get_scheduler_status",
]
