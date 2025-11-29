/**
 * Mock data for Playwright tests
 * Provides consistent test data across all test files
 */

// Auth Status Responses
export const mockAuthConnected = {
  connected: true,
  email: "test@gmail.com",
};

export const mockAuthDisconnected = {
  connected: false,
  email: null,
};

// Dashboard Stats
export const mockStats = {
  total_emails_processed: 5432,
  total_deleted: 1234,
  total_unsubscribed: 89,
  total_filters_created: 45,
  storage_freed_bytes: 524288000, // 500MB
  active_run: null,
};

export const mockStatsWithActiveRun = {
  ...mockStats,
  active_run: {
    id: "run-123",
    status: "running",
    progress: 45,
    senders_processed: 23,
    senders_total: 50,
  },
};

// Inbox Health
export const mockInboxHealthHealthy = {
  status: "healthy",
  potential_cleanup_count: 250,
  potential_space_savings: 52428800, // 50MB
  last_scan_at: new Date().toISOString(),
  categories: {
    promotions: 150,
    social: 50,
    updates: 50,
  },
};

export const mockInboxHealthNeedsAttention = {
  status: "needs_attention",
  potential_cleanup_count: 2500,
  potential_space_savings: 524288000, // 500MB
  last_scan_at: new Date().toISOString(),
  categories: {
    promotions: 1500,
    social: 500,
    updates: 500,
  },
};

export const mockInboxHealthCritical = {
  status: "critical",
  potential_cleanup_count: 8500,
  potential_space_savings: 1073741824, // 1GB
  last_scan_at: new Date().toISOString(),
  categories: {
    promotions: 5000,
    social: 2000,
    updates: 1500,
  },
};

// Auto Protected Categories
export const mockAutoProtected = {
  categories: [
    {
      name: "People you email with",
      description: "Emails from people you've replied to or sent emails to",
      icon: "users",
    },
    {
      name: "Your contacts",
      description: "Emails from senders in your Google Contacts",
      icon: "contact",
    },
    {
      name: "Financial institutions",
      description: "Banks, credit cards, payment services, and investments",
      icon: "building-bank",
    },
    {
      name: "Security emails",
      description: "Password resets, verification codes, and security alerts",
      icon: "shield-check",
    },
    {
      name: "Government",
      description: "Emails from .gov and .mil domains",
      icon: "landmark",
    },
  ],
};

// V2 Cleanup Session
export const mockCleanupSession = {
  session_id: "session-abc-123",
  status: "scanning",
};

export const mockCleanupProgressScanning = {
  session_id: "session-abc-123",
  status: "scanning",
  progress: 0.45,
  total_emails: 500,
  scanned_emails: 225,
  discoveries: {
    promotions: 45,
    newsletters: 12,
    social: 23,
    updates: 18,
    low_value: 8,
  },
  error: null,
};

export const mockCleanupProgressComplete = {
  session_id: "session-abc-123",
  status: "ready_for_review",
  progress: 1.0,
  total_emails: 500,
  scanned_emails: 500,
  discoveries: {
    promotions: 120,
    newsletters: 35,
    social: 65,
    updates: 45,
    low_value: 22,
  },
  error: null,
};

export const mockRecommendationSummary = {
  session_id: "session-abc-123",
  total_scanned: 500,
  total_to_cleanup: 287,
  total_protected: 213,
  space_savings: 157286400, // 150MB
  categories: {
    promotions: { count: 120, recommended_delete: 115 },
    newsletters: { count: 35, recommended_delete: 30 },
    social: { count: 65, recommended_delete: 60 },
    updates: { count: 45, recommended_delete: 40 },
    low_value: { count: 22, recommended_delete: 22 },
    protected: { count: 213, recommended_delete: 0 },
  },
  top_senders: [
    { email: "newsletter@company.com", count: 45, category: "newsletters" },
    { email: "promo@store.com", count: 38, category: "promotions" },
    { email: "updates@social.com", count: 32, category: "social" },
  ],
};

export const mockReviewQueue = {
  session_id: "session-abc-123",
  mode: "quick",
  items: [
    {
      message_id: "msg-1",
      sender_email: "newsletter@example.com",
      sender_name: "Example Newsletter",
      subject: "Weekly Updates - Issue #42",
      snippet: "Here are this week's top stories...",
      ai_suggestion: "delete",
      confidence: 0.92,
      reasoning: "High-volume newsletter sender with unsubscribe link",
      category: "newsletters",
      received_date: new Date(Date.now() - 86400000).toISOString(),
    },
    {
      message_id: "msg-2",
      sender_email: "promo@store.com",
      sender_name: "Online Store",
      subject: "50% Off Everything Today!",
      snippet: "Don't miss our biggest sale of the year...",
      ai_suggestion: "delete",
      confidence: 0.88,
      reasoning: "Promotional email with sale keywords",
      category: "promotions",
      received_date: new Date(Date.now() - 172800000).toISOString(),
    },
    {
      message_id: "msg-3",
      sender_email: "support@service.com",
      sender_name: "Service Support",
      subject: "Your account summary",
      snippet: "Here is your monthly account summary...",
      ai_suggestion: "keep",
      confidence: 0.75,
      reasoning: "Account-related email, may contain important info",
      category: "updates",
      received_date: new Date(Date.now() - 259200000).toISOString(),
    },
  ],
  total_items: 50,
  reviewed_count: 0,
};

export const mockConfirmationSummary = {
  session_id: "session-abc-123",
  total_to_delete: 245,
  total_to_keep: 255,
  space_to_free: 125829120, // 120MB
  by_category: {
    promotions: 115,
    newsletters: 30,
    social: 58,
    updates: 32,
    low_value: 10,
  },
  user_overrides: {
    kept: 5,
    deleted: 3,
  },
};

export const mockCleanupResults = {
  session_id: "session-abc-123",
  status: "completed",
  emails_deleted: 245,
  space_freed: 125829120,
  senders_unsubscribed: 12,
  filters_created: 8,
  duration_seconds: 45,
  errors: [],
};

// Senders
export const mockSenders = {
  senders: [
    {
      id: 1,
      email: "newsletter@company.com",
      name: "Company Newsletter",
      domain: "company.com",
      message_count: 156,
      first_seen: new Date(Date.now() - 30 * 86400000).toISOString(),
      last_seen: new Date().toISOString(),
      unsubscribe_method: "mailto",
      unsubscribed: false,
      has_filter: false,
    },
    {
      id: 2,
      email: "promo@store.com",
      name: "Online Store",
      domain: "store.com",
      message_count: 89,
      first_seen: new Date(Date.now() - 60 * 86400000).toISOString(),
      last_seen: new Date(Date.now() - 2 * 86400000).toISOString(),
      unsubscribe_method: "http",
      unsubscribed: true,
      has_filter: true,
    },
    {
      id: 3,
      email: "updates@social.com",
      name: "Social Network",
      domain: "social.com",
      message_count: 234,
      first_seen: new Date(Date.now() - 90 * 86400000).toISOString(),
      last_seen: new Date(Date.now() - 1 * 86400000).toISOString(),
      unsubscribe_method: null,
      unsubscribed: false,
      has_filter: false,
    },
  ],
  total: 3,
  limit: 50,
  offset: 0,
};

// Run History
export const mockRuns = {
  runs: [
    {
      id: "run-1",
      status: "completed",
      started_at: new Date(Date.now() - 2 * 86400000).toISOString(),
      finished_at: new Date(Date.now() - 2 * 86400000 + 3600000).toISOString(),
      senders_total: 150,
      senders_processed: 150,
      emails_deleted: 1234,
      storage_freed: 524288000,
      unsubscribed_count: 45,
      filters_created: 30,
    },
    {
      id: "run-2",
      status: "completed",
      started_at: new Date(Date.now() - 7 * 86400000).toISOString(),
      finished_at: new Date(Date.now() - 7 * 86400000 + 1800000).toISOString(),
      senders_total: 80,
      senders_processed: 80,
      emails_deleted: 567,
      storage_freed: 209715200,
      unsubscribed_count: 22,
      filters_created: 15,
    },
    {
      id: "run-3",
      status: "cancelled",
      started_at: new Date(Date.now() - 14 * 86400000).toISOString(),
      finished_at: new Date(Date.now() - 14 * 86400000 + 600000).toISOString(),
      senders_total: 100,
      senders_processed: 35,
      emails_deleted: 123,
      storage_freed: 52428800,
      unsubscribed_count: 8,
      filters_created: 5,
    },
  ],
  total: 3,
  limit: 20,
  offset: 0,
};

export const mockRunDetail = {
  id: "run-1",
  status: "completed",
  started_at: new Date(Date.now() - 2 * 86400000).toISOString(),
  finished_at: new Date(Date.now() - 2 * 86400000 + 3600000).toISOString(),
  senders_total: 150,
  senders_processed: 150,
  emails_deleted: 1234,
  storage_freed: 524288000,
  unsubscribed_count: 45,
  filters_created: 30,
  error_message: null,
};

export const mockRunActions = {
  actions: [
    {
      id: 1,
      run_id: "run-1",
      action_type: "delete",
      sender_email: "newsletter@company.com",
      email_count: 45,
      created_at: new Date(Date.now() - 2 * 86400000 + 1000).toISOString(),
    },
    {
      id: 2,
      run_id: "run-1",
      action_type: "unsubscribe",
      sender_email: "newsletter@company.com",
      email_count: 0,
      created_at: new Date(Date.now() - 2 * 86400000 + 2000).toISOString(),
    },
    {
      id: 3,
      run_id: "run-1",
      action_type: "filter",
      sender_email: "newsletter@company.com",
      email_count: 0,
      created_at: new Date(Date.now() - 2 * 86400000 + 3000).toISOString(),
    },
  ],
  total: 150,
  limit: 50,
  offset: 0,
};

// Whitelist
export const mockWhitelist = {
  entries: [
    { email: "important@work.com", name: "Work Contact", added_at: new Date().toISOString() },
    { email: "@family.com", name: "Family Domain", added_at: new Date().toISOString() },
    { email: "friend@personal.com", name: "Friend", added_at: new Date().toISOString() },
  ],
};

// Large Attachments
export const mockLargeAttachments = {
  emails: [
    {
      message_id: "att-1",
      subject: "Project Files - Final Version",
      from_email: "colleague@work.com",
      from_name: "Work Colleague",
      size: 15728640, // 15MB
      size_mb: 15,
      date: new Date(Date.now() - 30 * 86400000).toISOString(),
    },
    {
      message_id: "att-2",
      subject: "Vacation Photos",
      from_email: "friend@gmail.com",
      from_name: "Friend",
      size: 8388608, // 8MB
      size_mb: 8,
      date: new Date(Date.now() - 60 * 86400000).toISOString(),
    },
    {
      message_id: "att-3",
      subject: "Design Mockups v2",
      from_email: "designer@agency.com",
      from_name: "Designer",
      size: 25165824, // 24MB
      size_mb: 24,
      date: new Date(Date.now() - 45 * 86400000).toISOString(),
    },
  ],
  total_size_bytes: 49283072, // ~47MB
};

// Subscriptions
export const mockSubscriptions = {
  subscriptions: [
    {
      id: "sub-1",
      email: "newsletter@tech.com",
      name: "Tech Newsletter",
      frequency: "weekly",
      message_count: 52,
      last_received: new Date(Date.now() - 86400000).toISOString(),
      unsubscribed: false,
    },
    {
      id: "sub-2",
      email: "deals@shopping.com",
      name: "Shopping Deals",
      frequency: "daily",
      message_count: 180,
      last_received: new Date().toISOString(),
      unsubscribed: false,
    },
    {
      id: "sub-3",
      email: "updates@social.com",
      name: "Social Updates",
      frequency: "daily",
      message_count: 365,
      last_received: new Date().toISOString(),
      unsubscribed: true,
    },
  ],
  total: 3,
};

// Retention Rules
export const mockRetentionRules = {
  rules: [
    {
      index: 0,
      sender_pattern: "*@promotions.com",
      max_age_days: 7,
      action: "delete",
      created_at: new Date().toISOString(),
    },
    {
      index: 1,
      sender_pattern: "newsletter@*",
      max_age_days: 30,
      action: "archive",
      created_at: new Date().toISOString(),
    },
  ],
};

// Email Scoring
export const mockScoringProgress = {
  status: "completed",
  progress: 100,
  total_emails: 500,
  scored_emails: 500,
  started_at: new Date(Date.now() - 300000).toISOString(),
  completed_at: new Date().toISOString(),
};

export const mockScoringStats = {
  total_scored: 500,
  by_classification: {
    keep: 250,
    review: 150,
    delete: 100,
  },
  avg_score: 65,
};

export const mockScoredEmails = {
  emails: [
    {
      message_id: "score-1",
      subject: "Important: Account Security Update",
      from_email: "security@bank.com",
      from_name: "Bank Security",
      score: 95,
      classification: "keep",
      signals: {
        sender_reputation: 90,
        content_importance: 95,
        user_engagement: 85,
      },
      date: new Date().toISOString(),
    },
    {
      message_id: "score-2",
      subject: "Weekly Newsletter #42",
      from_email: "newsletter@news.com",
      from_name: "News Site",
      score: 45,
      classification: "review",
      signals: {
        sender_reputation: 60,
        content_importance: 40,
        user_engagement: 35,
      },
      date: new Date(Date.now() - 86400000).toISOString(),
    },
    {
      message_id: "score-3",
      subject: "50% Off Everything!",
      from_email: "promo@store.com",
      from_name: "Store",
      score: 15,
      classification: "delete",
      signals: {
        sender_reputation: 30,
        content_importance: 10,
        user_engagement: 5,
      },
      date: new Date(Date.now() - 172800000).toISOString(),
    },
  ],
  total: 500,
  limit: 50,
  offset: 0,
};

// Classifications
export const mockClassificationSummary = {
  total_scanned: 1000,
  promotional: 400,
  social: 200,
  updates: 150,
  forums: 50,
  primary: 200,
};

export const mockClassifications = {
  classifications: [
    {
      message_id: "class-1",
      subject: "Sale ends tonight!",
      from_email: "promo@store.com",
      classification: "promotional",
      confidence: 0.95,
      date: new Date().toISOString(),
    },
    {
      message_id: "class-2",
      subject: "John commented on your post",
      from_email: "notifications@social.com",
      classification: "social",
      confidence: 0.88,
      date: new Date().toISOString(),
    },
  ],
  total: 1000,
  limit: 50,
  offset: 0,
};
