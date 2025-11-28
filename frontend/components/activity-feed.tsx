"use client"

import { useEffect, useRef } from "react"
import { Trash2, Mail, Filter, Check } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

import { RunAction } from "@/lib/api"

interface ActivityFeedProps {
  actions: RunAction[]
  className?: string
}

const actionConfig: Record<string, {
  icon: any,
  label: string,
  variant: "destructive" | "warning" | "default" | "secondary",
  color: string,
}> = {
  delete: {
    icon: Trash2,
    label: "Deleted",
    variant: "destructive",
    color: "text-destructive",
  },
  unsubscribe: {
    icon: Mail,
    label: "Unsubscribed",
    variant: "warning",
    color: "text-warning",
  },
  filter: {
    icon: Filter,
    label: "Filtered",
    variant: "default",
    color: "text-primary",
  },
  skip: {
    icon: Check,
    label: "Skipped",
    variant: "secondary",
    color: "text-muted-foreground",
  },
  error: {
    icon: Trash2,
    label: "Error",
    variant: "destructive",
    color: "text-destructive",
  },
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)

  if (seconds < 60) return "just now"
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  return date.toLocaleDateString()
}

export function ActivityFeed({ actions, className }: ActivityFeedProps) {
  const feedRef = useRef<HTMLDivElement>(null)
  const prevActionsLength = useRef(actions.length)

  useEffect(() => {
    if (actions.length > prevActionsLength.current && feedRef.current) {
      feedRef.current.scrollTop = 0
    }
    prevActionsLength.current = actions.length
  }, [actions.length])

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <div
          ref={feedRef}
          className="space-y-3 max-h-96 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-muted scrollbar-track-transparent"
        >
          {actions.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              No activity yet. Start a cleanup run to see actions here.
            </p>
          ) : (
            actions.map((action) => {
              const config = actionConfig[action.action_type] || actionConfig.skip
              const Icon = config.icon

              return (
                <div
                  key={action.id}
                  className="flex items-start gap-3 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                >
                  <div className={cn("mt-0.5", config.color)}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge variant={config.variant} className="text-xs">
                        {config.label}
                      </Badge>
                      <span className="text-sm font-medium truncate">
                        {action.sender_email}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {action.email_count} email{action.email_count !== 1 ? "s" : ""}
                      {action.notes && ` • ${action.notes}`}
                    </p>
                  </div>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {formatTimestamp(action.timestamp)}
                  </span>
                </div>
              )
            })
          )}
        </div>
      </CardContent>
    </Card>
  )
}
