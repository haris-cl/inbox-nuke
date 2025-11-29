"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import {
  Check,
  X,
  SkipForward,
  Loader2,
  ChevronRight,
  Mail,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { useCleanup, ReviewItem } from "../cleanup-context"

export default function ReviewPage() {
  const router = useRouter()
  const {
    sessionId,
    mode,
    reviewQueue,
    currentReviewIndex,
    setReviewQueue,
    submitDecision,
    skipAllRemaining,
    nextReviewItem,
  } = useCleanup()
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  // Fetch review queue
  useEffect(() => {
    if (!sessionId) {
      router.push("/dashboard/cleanup/scanning")
      return
    }

    const fetchQueue = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/api/cleanup/review-queue/${sessionId}?mode=${mode || "quick"}`
        )
        const data = await response.json()
        setReviewQueue(data.items)
      } catch (error) {
        console.error("Failed to fetch review queue:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchQueue()
  }, [sessionId, mode, router, setReviewQueue])

  // Check if review is complete
  useEffect(() => {
    if (!loading && currentReviewIndex >= reviewQueue.length && reviewQueue.length > 0) {
      router.push("/dashboard/cleanup/unsubscribe")
    }
  }, [currentReviewIndex, reviewQueue.length, loading, router])

  const handleDecision = async (decision: "keep" | "delete") => {
    const currentItem = reviewQueue[currentReviewIndex]
    if (!currentItem) return

    setSubmitting(true)
    await submitDecision(currentItem.message_id, decision)
    setSubmitting(false)
  }

  const handleSkipAll = async () => {
    setSubmitting(true)
    await skipAllRemaining()
    router.push("/dashboard/cleanup/unsubscribe")
  }

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (submitting || loading) return

      if (e.key === "k" || e.key === "K") {
        handleDecision("keep")
      } else if (e.key === "d" || e.key === "D") {
        handleDecision("delete")
      } else if (e.key === "s" || e.key === "S") {
        handleSkipAll()
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [submitting, loading, currentReviewIndex])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground">Loading review queue...</p>
      </div>
    )
  }

  if (reviewQueue.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center mb-4">
          <Check className="w-8 h-8 text-green-500" />
        </div>
        <h2 className="text-2xl font-bold mb-2">No emails to review!</h2>
        <p className="text-muted-foreground mb-6">
          The AI is confident about all cleanup decisions.
        </p>
        <Button onClick={() => router.push("/dashboard/cleanup/confirm")}>
          Continue to Confirmation
          <ChevronRight className="w-4 h-4 ml-2" />
        </Button>
      </div>
    )
  }

  const currentItem = reviewQueue[currentReviewIndex]
  const progress = Math.round((currentReviewIndex / reviewQueue.length) * 100)
  const remaining = reviewQueue.length - currentReviewIndex

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      {/* Progress Header */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold">Review Emails</h1>
          <Button variant="ghost" size="sm" onClick={handleSkipAll}>
            <SkipForward className="w-4 h-4 mr-2" />
            Skip All & Trust AI
          </Button>
        </div>
        <div className="flex items-center gap-4">
          <Progress value={progress} className="flex-1 h-2" />
          <span className="text-sm text-muted-foreground whitespace-nowrap">
            {currentReviewIndex + 1} of {reviewQueue.length}
          </span>
        </div>
        <p className="text-sm text-muted-foreground">
          {remaining} emails remaining to review
        </p>
      </div>

      {/* Email Card */}
      {currentItem && (
        <Card className="overflow-hidden">
          <CardContent className="p-0">
            {/* Email Header */}
            <div className="p-6 border-b">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
                  <Mail className="w-6 h-6 text-muted-foreground" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold truncate">
                    {currentItem.sender_name || currentItem.sender_email}
                  </div>
                  <div className="text-sm text-muted-foreground truncate">
                    {currentItem.sender_email}
                  </div>
                </div>
              </div>
            </div>

            {/* Subject & Snippet */}
            <div className="p-6 border-b">
              <h3 className="font-medium mb-2 line-clamp-2">{currentItem.subject}</h3>
              <p className="text-sm text-muted-foreground line-clamp-3">
                {currentItem.snippet}
              </p>
            </div>

            {/* AI Reasoning */}
            <div className="p-6 bg-muted/30">
              <div className="flex items-start gap-3">
                <div
                  className={`px-2 py-1 rounded text-xs font-medium ${
                    currentItem.ai_suggestion === "delete"
                      ? "bg-destructive/10 text-destructive"
                      : "bg-green-500/10 text-green-500"
                  }`}
                >
                  AI suggests: {currentItem.ai_suggestion === "delete" ? "Remove" : "Keep"}
                </div>
              </div>
              <p className="text-sm text-muted-foreground mt-2">
                {currentItem.reasoning}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <div className="flex gap-4">
        <Button
          variant="outline"
          size="lg"
          className="flex-1 h-14 text-green-600 border-green-600 hover:bg-green-50 hover:text-green-700"
          onClick={() => handleDecision("keep")}
          disabled={submitting}
        >
          {submitting ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <>
              <Check className="w-5 h-5 mr-2" />
              Keep
              <span className="ml-2 text-xs opacity-60">(K)</span>
            </>
          )}
        </Button>

        <Button
          variant="outline"
          size="lg"
          className="flex-1 h-14 text-destructive border-destructive hover:bg-destructive/10"
          onClick={() => handleDecision("delete")}
          disabled={submitting}
        >
          {submitting ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <>
              <X className="w-5 h-5 mr-2" />
              Remove
              <span className="ml-2 text-xs opacity-60">(D)</span>
            </>
          )}
        </Button>
      </div>

      {/* Keyboard Hints */}
      <p className="text-xs text-center text-muted-foreground">
        Press <kbd className="px-1 py-0.5 rounded bg-muted">K</kbd> to Keep,{" "}
        <kbd className="px-1 py-0.5 rounded bg-muted">D</kbd> to Delete,{" "}
        <kbd className="px-1 py-0.5 rounded bg-muted">S</kbd> to Skip All
      </p>
    </div>
  )
}
