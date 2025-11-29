"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Select } from "@/components/ui/select"
import { ScoreBadge } from "@/components/score-badge"
import { ScoreBar } from "@/components/score-bar"
import { SignalBreakdown } from "@/components/signal-breakdown"
import { EmailScore } from "@/lib/api"
import { Loader2 } from "lucide-react"

// Simple time ago formatter
function timeAgo(date: Date): string {
  const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000)

  let interval = seconds / 31536000
  if (interval > 1) return Math.floor(interval) + " years ago"

  interval = seconds / 2592000
  if (interval > 1) return Math.floor(interval) + " months ago"

  interval = seconds / 86400
  if (interval > 1) return Math.floor(interval) + " days ago"

  interval = seconds / 3600
  if (interval > 1) return Math.floor(interval) + " hours ago"

  interval = seconds / 60
  if (interval > 1) return Math.floor(interval) + " minutes ago"

  return Math.floor(seconds) + " seconds ago"
}

interface EmailScoreCardProps {
  email: EmailScore
  onOverride?: (messageId: string, classification: string) => Promise<void>
}

export function EmailScoreCard({ email, onOverride }: EmailScoreCardProps) {
  const [isOverriding, setIsOverriding] = useState(false)
  const displayClassification = email.user_override || email.classification

  const handleOverride = async (newClassification: string) => {
    if (!onOverride || newClassification === displayClassification) return

    try {
      setIsOverriding(true)
      await onOverride(email.message_id, newClassification)
    } catch (error) {
      console.error("Failed to override classification:", error)
    } finally {
      setIsOverriding(false)
    }
  }

  return (
    <Card className="card-glow border-2 border-border/50 backdrop-blur-sm bg-card/50">
      <CardContent className="p-4 space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <ScoreBadge classification={displayClassification as "KEEP" | "DELETE" | "UNCERTAIN"} />
              {email.user_override && (
                <Badge variant="secondary" className="text-xs">
                  Overridden
                </Badge>
              )}
              <Badge variant="outline" className="text-xs">
                {Math.round(email.confidence * 100)}% confident
              </Badge>
            </div>
            <div className="text-sm font-semibold line-clamp-1">{email.subject}</div>
            <div className="text-xs text-muted-foreground font-mono mt-1">{email.sender_email}</div>
            <div className="text-xs text-muted-foreground mt-1">
              {timeAgo(new Date(email.scored_at))}
            </div>
          </div>
        </div>

        {/* Score Bar */}
        <ScoreBar score={email.total_score} />

        {/* Labels */}
        {email.gmail_labels.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            {email.gmail_labels.slice(0, 3).map((label) => (
              <Badge key={label} variant="outline" className="text-xs">
                {label}
              </Badge>
            ))}
            {email.gmail_labels.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{email.gmail_labels.length - 3} more
              </Badge>
            )}
          </div>
        )}

        {/* Signal Breakdown */}
        <SignalBreakdown
          signals={{
            category_score: email.category_score,
            header_score: email.header_score,
            engagement_score: email.engagement_score,
            keyword_score: email.keyword_score,
            thread_score: email.thread_score,
          }}
          signalDetails={email.signal_details}
          reasoning={email.reasoning}
        />

        {/* Override Control */}
        {onOverride && (
          <div className="flex items-center gap-2 pt-2 border-t border-border/50">
            <span className="text-xs text-muted-foreground font-semibold uppercase tracking-wide">
              Override:
            </span>
            <Select
              value={displayClassification}
              onChange={(e) => handleOverride(e.target.value)}
              disabled={isOverriding}
              className="h-8 w-[130px] text-xs"
              options={[
                { value: "KEEP", label: "Keep" },
                { value: "DELETE", label: "Delete" },
                { value: "UNCERTAIN", label: "Uncertain" },
              ]}
            />
            {isOverriding && <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
