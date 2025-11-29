"use client"

import { createContext, useContext, useState, useCallback, ReactNode } from "react"

// Types for V2 Cleanup Flow
export interface CleanupDiscoveries {
  promotions: number
  newsletters: number
  social: number
  updates: number
  low_value: number
}

export interface CleanupProgress {
  session_id: string
  status: string
  progress: number
  total_emails: number
  scanned_emails: number
  discoveries: CleanupDiscoveries
  error?: string
}

export interface SenderRecommendation {
  email: string
  display_name?: string
  count: number
  reason: string
}

export interface RecommendationSummary {
  session_id: string
  total_to_cleanup: number
  total_protected: number
  space_savings: number
  category_breakdown: Record<string, number>
  protected_reasons: string[]
  top_delete_senders: SenderRecommendation[]
  top_keep_senders: SenderRecommendation[]
}

export interface ReviewItem {
  message_id: string
  sender_email: string
  sender_name?: string
  subject: string
  date: string
  snippet: string
  ai_suggestion: string
  reasoning: string
  confidence: number
  category: string
}

export interface ConfirmationSummary {
  session_id: string
  emails_to_delete: number
  senders_to_unsubscribe: number
  space_to_be_freed: number
  protected_count: number
  safety_info: {
    trash_recovery_days: number
    auto_protected_categories: string[]
  }
}

export interface CleanupResults {
  session_id: string
  status: string
  emails_deleted: number
  space_freed: number
  senders_unsubscribed: number
  filters_created: number
  errors: string[]
  completed_at?: string
}

// Context state
interface CleanupState {
  sessionId: string | null
  status: "idle" | "scanning" | "ready_for_review" | "reviewing" | "confirming" | "executing" | "completed" | "failed"
  mode: "quick" | "full" | null
  progress: CleanupProgress | null
  recommendations: RecommendationSummary | null
  reviewQueue: ReviewItem[]
  currentReviewIndex: number
  confirmation: ConfirmationSummary | null
  results: CleanupResults | null
  error: string | null
}

// Active session info for resuming
export interface ActiveSession {
  has_active_session: boolean
  session_id?: string
  status?: string
  mode?: string
  progress: number
  total_emails: number
  scanned_emails: number
  total_to_cleanup: number
  total_protected: number
  created_at?: string
  resume_step?: string
}

interface CleanupContextType extends CleanupState {
  startCleanup: () => Promise<void>
  resumeSession: (sessionId: string, status: string, mode?: string | null) => void
  setMode: (mode: "quick" | "full") => Promise<void>
  submitDecision: (messageId: string, decision: "keep" | "delete") => Promise<void>
  skipAllRemaining: () => Promise<void>
  confirmCleanup: () => Promise<void>
  reset: () => void
  updateProgress: (progress: CleanupProgress) => void
  setRecommendations: (recs: RecommendationSummary) => void
  setReviewQueue: (items: ReviewItem[]) => void
  setConfirmation: (conf: ConfirmationSummary) => void
  setResults: (results: CleanupResults) => void
  setError: (error: string) => void
  nextReviewItem: () => void
}

const CleanupContext = createContext<CleanupContextType | null>(null)

export function CleanupProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<CleanupState>({
    sessionId: null,
    status: "idle",
    mode: null,
    progress: null,
    recommendations: null,
    reviewQueue: [],
    currentReviewIndex: 0,
    confirmation: null,
    results: null,
    error: null,
  })

  const startCleanup = useCallback(async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/api/cleanup/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ max_emails: 10000 }),
      })
      const data = await response.json()
      setState(prev => ({
        ...prev,
        sessionId: data.session_id,
        status: "scanning",
        error: null,
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        status: "failed",
        error: "Failed to start cleanup",
      }))
    }
  }, [])

  const resumeSession = useCallback((sessionId: string, status: string, mode?: string | null) => {
    // Map backend status to frontend status
    const statusMap: Record<string, CleanupState["status"]> = {
      scanning: "scanning",
      ready_for_review: "ready_for_review",
      reviewing: "reviewing",
      confirming: "confirming",
      executing: "executing",
      completed: "completed",
      failed: "failed",
    }

    setState(prev => ({
      ...prev,
      sessionId,
      status: statusMap[status] || "idle",
      mode: mode as "quick" | "full" | null,
      error: null,
    }))
  }, [])

  const setMode = useCallback(async (mode: "quick" | "full") => {
    if (!state.sessionId) return
    try {
      await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/api/cleanup/mode/${state.sessionId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode }),
      })
      setState(prev => ({
        ...prev,
        mode,
        status: "reviewing",
      }))
    } catch (error) {
      setState(prev => ({ ...prev, error: "Failed to set mode" }))
    }
  }, [state.sessionId])

  const submitDecision = useCallback(async (messageId: string, decision: "keep" | "delete") => {
    if (!state.sessionId) return
    try {
      await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/api/cleanup/review-decision/${state.sessionId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message_id: messageId, decision }),
      })
      setState(prev => ({
        ...prev,
        currentReviewIndex: prev.currentReviewIndex + 1,
      }))
    } catch (error) {
      setState(prev => ({ ...prev, error: "Failed to submit decision" }))
    }
  }, [state.sessionId])

  const skipAllRemaining = useCallback(async () => {
    if (!state.sessionId) return
    try {
      await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/api/cleanup/skip-all/${state.sessionId}`, {
        method: "POST",
      })
      setState(prev => ({
        ...prev,
        status: "confirming",
        currentReviewIndex: prev.reviewQueue.length,
      }))
    } catch (error) {
      setState(prev => ({ ...prev, error: "Failed to skip remaining" }))
    }
  }, [state.sessionId])

  const confirmCleanup = useCallback(async () => {
    if (!state.sessionId) return
    try {
      await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/api/cleanup/execute/${state.sessionId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirmed: true }),
      })
      setState(prev => ({
        ...prev,
        status: "executing",
      }))
    } catch (error) {
      setState(prev => ({ ...prev, error: "Failed to execute cleanup" }))
    }
  }, [state.sessionId])

  const reset = useCallback(() => {
    setState({
      sessionId: null,
      status: "idle",
      mode: null,
      progress: null,
      recommendations: null,
      reviewQueue: [],
      currentReviewIndex: 0,
      confirmation: null,
      results: null,
      error: null,
    })
  }, [])

  const updateProgress = useCallback((progress: CleanupProgress) => {
    setState(prev => ({
      ...prev,
      progress,
      status: progress.status as CleanupState["status"],
    }))
  }, [])

  const setRecommendations = useCallback((recs: RecommendationSummary) => {
    setState(prev => ({ ...prev, recommendations: recs }))
  }, [])

  const setReviewQueue = useCallback((items: ReviewItem[]) => {
    setState(prev => ({
      ...prev,
      reviewQueue: items,
      currentReviewIndex: 0,
    }))
  }, [])

  const setConfirmation = useCallback((conf: ConfirmationSummary) => {
    setState(prev => ({ ...prev, confirmation: conf }))
  }, [])

  const setResults = useCallback((results: CleanupResults) => {
    setState(prev => ({
      ...prev,
      results,
      status: results.status === "completed" ? "completed" : prev.status,
    }))
  }, [])

  const setError = useCallback((error: string) => {
    setState(prev => ({ ...prev, error, status: "failed" }))
  }, [])

  const nextReviewItem = useCallback(() => {
    setState(prev => ({
      ...prev,
      currentReviewIndex: Math.min(prev.currentReviewIndex + 1, prev.reviewQueue.length),
    }))
  }, [])

  return (
    <CleanupContext.Provider
      value={{
        ...state,
        startCleanup,
        resumeSession,
        setMode,
        submitDecision,
        skipAllRemaining,
        confirmCleanup,
        reset,
        updateProgress,
        setRecommendations,
        setReviewQueue,
        setConfirmation,
        setResults,
        setError,
        nextReviewItem,
      }}
    >
      {children}
    </CleanupContext.Provider>
  )
}

export function useCleanup() {
  const context = useContext(CleanupContext)
  if (!context) {
    throw new Error("useCleanup must be used within a CleanupProvider")
  }
  return context
}
