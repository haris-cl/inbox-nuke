"use client"

import { useState } from "react"
import { ChevronDown, ChevronUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface SignalBreakdownProps {
  signals: {
    category_score: number
    header_score: number
    engagement_score: number
    keyword_score: number
    thread_score: number
  }
  signalDetails: Record<string, { score: number; reason: string }>
  reasoning: string
}

export function SignalBreakdown({ signals, signalDetails, reasoning }: SignalBreakdownProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const signalConfig = [
    { key: "category_score", label: "Category", score: signals.category_score },
    { key: "header_score", label: "Headers", score: signals.header_score },
    { key: "engagement_score", label: "Engagement", score: signals.engagement_score },
    { key: "keyword_score", label: "Keywords", score: signals.keyword_score },
    { key: "thread_score", label: "Thread", score: signals.thread_score },
  ]

  const getScoreColor = (score: number) => {
    if (score < 30) return "text-emerald-400 bg-emerald-400/10"
    if (score < 70) return "text-amber-400 bg-amber-400/10"
    return "text-rose-400 bg-rose-400/10"
  }

  return (
    <div className="space-y-2">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full justify-between text-xs font-semibold uppercase tracking-wide text-muted-foreground hover:text-foreground"
      >
        <span>Signal Breakdown</span>
        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </Button>

      {isExpanded && (
        <div className="space-y-3 animate-fade-in-up">
          {/* Signal Scores */}
          <div className="grid grid-cols-5 gap-2">
            {signalConfig.map((signal) => (
              <div
                key={signal.key}
                className={cn(
                  "rounded-lg p-2 text-center transition-all duration-300 hover:scale-105",
                  getScoreColor(signal.score)
                )}
              >
                <div className="text-lg font-black font-mono tabular-nums">{signal.score}</div>
                <div className="text-[10px] font-semibold uppercase tracking-wide opacity-80">
                  {signal.label}
                </div>
              </div>
            ))}
          </div>

          {/* Signal Details */}
          {Object.keys(signalDetails).length > 0 && (
            <div className="space-y-2">
              <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Details
              </div>
              {Object.entries(signalDetails).map(([key, value]) => (
                <div
                  key={key}
                  className="text-xs p-2 rounded-md bg-muted/30 border border-border/30"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold capitalize">{key.replace(/_/g, " ")}</span>
                    <span className={cn("font-mono font-black tabular-nums", getScoreColor(value.score).split(" ")[0])}>
                      {value.score}
                    </span>
                  </div>
                  <div className="text-muted-foreground">{value.reason}</div>
                </div>
              ))}
            </div>
          )}

          {/* Reasoning */}
          {reasoning && (
            <div className="space-y-1">
              <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Reasoning
              </div>
              <div className="text-xs text-muted-foreground leading-relaxed p-2 rounded-md bg-muted/30 border border-border/30">
                {reasoning}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
