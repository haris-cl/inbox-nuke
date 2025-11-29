"use client"

import { Mail, Star, Reply, TrendingUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScoreBadge } from "@/components/score-badge"
import { ScoreBar } from "@/components/score-bar"
import { SenderProfile } from "@/lib/api"
import { cn } from "@/lib/utils"

interface SenderRowProps {
  sender: SenderProfile
  onViewEmails?: (email: string) => void
  onOverride?: (email: string, classification: string) => void
}

export function SenderRow({ sender, onViewEmails, onOverride }: SenderRowProps) {
  // Get initials for avatar
  const getInitials = (email: string, name?: string) => {
    if (name) {
      return name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    }
    return email.slice(0, 2).toUpperCase()
  }

  const initials = getInitials(sender.sender_email, sender.display_name)

  return (
    <div className="card-glow border-2 border-border/50 backdrop-blur-sm bg-card/50 rounded-xl p-4 hover:scale-[1.01] transition-all duration-300">
      <div className="flex items-start gap-4">
        {/* Avatar */}
        <div className="flex-shrink-0">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 ring-2 ring-primary/20 flex items-center justify-center">
            <span className="text-sm font-black text-primary">{initials}</span>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 space-y-3">
          {/* Header */}
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0 flex-1">
              {sender.display_name && (
                <div className="font-semibold text-sm truncate">{sender.display_name}</div>
              )}
              <div className="text-xs text-muted-foreground font-mono truncate">
                {sender.sender_email}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                {sender.sender_domain}
              </div>
            </div>
            <ScoreBadge classification={sender.classification} />
          </div>

          {/* Score Bar */}
          <ScoreBar score={sender.avg_score} animated={false} />

          {/* Stats */}
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <Mail className="w-3 h-3" />
              <span className="font-mono tabular-nums">{sender.email_count}</span>
              <span>emails</span>
            </div>
            {sender.user_replied_count > 0 && (
              <div className="flex items-center gap-1 text-emerald-400">
                <Reply className="w-3 h-3" />
                <span className="font-mono tabular-nums">{sender.user_replied_count}</span>
              </div>
            )}
            {sender.starred_count > 0 && (
              <div className="flex items-center gap-1 text-amber-400">
                <Star className="w-3 h-3" />
                <span className="font-mono tabular-nums">{sender.starred_count}</span>
              </div>
            )}
            {sender.primary_count > 0 && (
              <div className="flex items-center gap-1">
                <TrendingUp className="w-3 h-3" />
                <span className="font-mono tabular-nums">{sender.primary_count}</span>
                <span>primary</span>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {onViewEmails && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onViewEmails(sender.sender_email)}
                className="text-xs"
              >
                View Emails
              </Button>
            )}
            {onOverride && sender.classification !== "KEEP" && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onOverride(sender.sender_email, "KEEP")}
                className="text-xs text-emerald-400 hover:text-emerald-400"
              >
                Mark Keep
              </Button>
            )}
            {onOverride && sender.classification !== "DELETE" && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onOverride(sender.sender_email, "DELETE")}
                className="text-xs text-rose-400 hover:text-rose-400"
              >
                Mark Delete
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
