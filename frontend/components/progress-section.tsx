"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"

interface ProgressSectionProps {
  percent: number
  phase: string
  current: number
  total: number
  className?: string
}

const phaseDescriptions: Record<string, string> = {
  initializing: "Setting up the cleanup process...",
  discovering: "Discovering email senders...",
  analyzing: "Analyzing email patterns...",
  processing: "Processing cleanup actions...",
  unsubscribing: "Unsubscribing from mailing lists...",
  filtering: "Creating filters...",
  deleting: "Removing unwanted emails...",
  finalizing: "Finishing up...",
}

export function ProgressSection({
  percent,
  phase,
  current,
  total,
  className,
}: ProgressSectionProps) {
  const description = phaseDescriptions[phase.toLowerCase()] || "Processing..."

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Progress</CardTitle>
          <Badge variant="default" className="capitalize">
            {phase}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">{description}</span>
            <span className="font-medium">{Math.round(percent)}%</span>
          </div>
          <Progress value={percent} className="h-3" />
        </div>
        <div className="flex justify-between items-center pt-2 border-t">
          <span className="text-sm text-muted-foreground">Items Processed</span>
          <span className="text-lg font-semibold">
            {current.toLocaleString()} / {total.toLocaleString()}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}
