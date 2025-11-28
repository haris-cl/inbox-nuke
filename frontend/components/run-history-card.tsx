"use client"

import * as React from "react"
import Link from "next/link"
import { ChevronDown, ChevronUp, Clock, Trash2, Database, Mail } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Run } from "@/lib/api"
import { formatBytes, formatRelativeTime } from "@/lib/utils"

interface RunHistoryCardProps {
  run: Run
}

function getStatusVariant(status: Run["status"]) {
  switch (status) {
    case "completed":
      return "success"
    case "failed":
      return "destructive"
    case "running":
      return "default"
    case "paused":
      return "warning"
    case "cancelled":
      return "secondary"
    default:
      return "secondary"
  }
}

function calculateDuration(startedAt: string, completedAt?: string): string {
  const start = new Date(startedAt).getTime()
  const end = completedAt ? new Date(completedAt).getTime() : Date.now()
  const durationMs = end - start

  const seconds = Math.floor(durationMs / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)

  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`
  } else {
    return `${seconds}s`
  }
}

export function RunHistoryCard({ run }: RunHistoryCardProps) {
  const [expanded, setExpanded] = React.useState(false)

  const duration = calculateDuration(run.started_at, run.finished_at)
  const statusVariant = getStatusVariant(run.status)

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-1 flex-1">
            <div className="flex items-center gap-2">
              <CardTitle className="text-lg">Run #{run.id}</CardTitle>
              <Badge variant={statusVariant}>
                {run.status.charAt(0).toUpperCase() + run.status.slice(1)}
              </Badge>
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-3 w-3" />
              <span>{formatRelativeTime(run.started_at)}</span>
              <span>•</span>
              <span>{duration}</span>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="ml-2"
          >
            {expanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Mini Stats Grid */}
        <div className="grid grid-cols-3 gap-3">
          <div className="flex items-center gap-2 text-sm">
            <Trash2 className="h-4 w-4 text-destructive" />
            <div>
              <p className="font-medium">{run.emails_deleted.toLocaleString()}</p>
              <p className="text-xs text-muted-foreground">Deleted</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Database className="h-4 w-4 text-success" />
            <div>
              <p className="font-medium">{formatBytes(run.bytes_freed_estimate)}</p>
              <p className="text-xs text-muted-foreground">Freed</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Mail className="h-4 w-4 text-primary" />
            <div>
              <p className="font-medium">{run.senders_processed.toLocaleString()}</p>
              <p className="text-xs text-muted-foreground">Processed</p>
            </div>
          </div>
        </div>

        {/* Expanded Details */}
        {expanded && (
          <div className="pt-3 border-t space-y-3">
            {run.error_message && (
              <div className="text-sm text-destructive bg-destructive/10 rounded-md p-2">
                <p className="font-medium">Error:</p>
                <p className="text-xs">{run.error_message}</p>
              </div>
            )}

            <div className="flex gap-2">
              <Button asChild variant="default" size="sm" className="flex-1">
                <Link href={`/dashboard/history/${run.id}`}>
                  View Details
                </Link>
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
