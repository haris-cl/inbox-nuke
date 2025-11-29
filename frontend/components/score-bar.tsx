"use client"

import { useEffect, useState } from "react"
import { cn } from "@/lib/utils"

interface ScoreBarProps {
  score: number
  className?: string
  showLabel?: boolean
  animated?: boolean
}

export function ScoreBar({ score, className, showLabel = true, animated = true }: ScoreBarProps) {
  const [displayScore, setDisplayScore] = useState(animated ? 0 : score)

  useEffect(() => {
    if (animated) {
      const timer = setTimeout(() => setDisplayScore(score), 100)
      return () => clearTimeout(timer)
    }
  }, [score, animated])

  // Determine color based on score
  const getScoreColor = (s: number) => {
    if (s < 30) return "text-emerald-400"
    if (s < 70) return "text-amber-400"
    return "text-rose-400"
  }

  // Calculate gradient position
  const gradientPosition = `${displayScore}%`

  return (
    <div className={cn("space-y-2", className)}>
      {showLabel && (
        <div className="flex justify-between items-center">
          <span className="text-xs text-muted-foreground font-semibold uppercase tracking-wide">
            Score
          </span>
          <span className={cn("text-sm font-mono font-black tabular-nums", getScoreColor(score))}>
            {score}
          </span>
        </div>
      )}
      <div className="relative h-3 bg-muted rounded-full overflow-hidden">
        <div
          className="absolute inset-0 transition-all duration-1000 ease-out"
          style={{
            width: gradientPosition,
            background: "linear-gradient(to right, hsl(142 76% 36%), hsl(45 93% 47%), hsl(0 84% 60%))",
            backgroundSize: `${100 / (displayScore / 100)}% 100%`,
          }}
        />
      </div>
    </div>
  )
}
