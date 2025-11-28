"use client"

import * as React from "react"
import { useParams, useRouter } from "next/navigation"
import useSWR from "swr"
import {
  ArrowLeft,
  Download,
  Clock,
  Trash2,
  Database,
  Mail,
  Filter,
  CheckCircle2,
  XCircle,
  Loader2,
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { api, Run, RunAction } from "@/lib/api"
import { formatBytes, formatRelativeTime, formatNumber } from "@/lib/utils"

const ACTIONS_PER_PAGE = 20

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

function getActionIcon(actionType: RunAction["action_type"]) {
  switch (actionType) {
    case "delete":
      return <Trash2 className="h-4 w-4 text-destructive" />
    case "filter":
      return <Filter className="h-4 w-4 text-primary" />
    case "unsubscribe":
      return <Mail className="h-4 w-4 text-warning" />
    case "skip":
      return <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
    default:
      return null
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
    return `${hours}h ${minutes % 60}m ${seconds % 3600 % 60}s`
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`
  } else {
    return `${seconds}s`
  }
}

export default function RunDetailPage() {
  const params = useParams()
  const router = useRouter()
  const runId = params.runId as string

  const [actionsPage, setActionsPage] = React.useState(0)
  const actionsOffset = actionsPage * ACTIONS_PER_PAGE

  // Fetch run details
  const { data: run, error: runError, isLoading: runLoading } = useSWR<Run>(
    runId ? `/api/runs/${runId}` : null,
    () => api.getRun(runId),
    {
      refreshInterval: (data) => {
        // Refresh every 2 seconds if running, otherwise don't refresh
        return data?.status === "running" ? 2000 : 0
      },
    }
  )

  // Fetch run actions
  const { data: actions, error: actionsError, isLoading: actionsLoading } = useSWR<RunAction[]>(
    runId ? [`/api/runs/${runId}/actions`, actionsOffset] : null,
    () => api.getRunActions(runId, { limit: ACTIONS_PER_PAGE, offset: actionsOffset }),
    {
      refreshInterval: (data) => {
        // Refresh every 3 seconds if run is active
        return run?.status === "running" ? 3000 : 0
      },
    }
  )

  const handleExport = () => {
    api.exportRunCSV(runId)
  }

  const handleBack = () => {
    router.push("/dashboard/history")
  }

  if (runLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-32 w-full" />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  if (runError || !run) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={handleBack}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to History
        </Button>
        <Alert variant="destructive">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>
            Failed to load run details. The run may not exist or there was a server error.
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  const duration = calculateDuration(run.started_at, run.finished_at)
  const statusVariant = getStatusVariant(run.status)
  const isRunning = run.status === "running"
  const progress = run.senders_total > 0
    ? Math.round((run.senders_processed / run.senders_total) * 100)
    : 0

  // Calculate stats
  const emailsDeleted = run.emails_deleted
  const bytesFreed = run.bytes_freed_estimate
  const sendersProcessed = run.senders_processed
  const filtersCreated = actions?.filter(a => a.action_type === "filter").length || 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <Button variant="ghost" onClick={handleBack} className="mb-2 -ml-2">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to History
          </Button>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight">Run #{runId.slice(0, 8)}</h1>
            <Badge variant={statusVariant}>
              {run.status.charAt(0).toUpperCase() + run.status.slice(1)}
            </Badge>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span>Started {formatRelativeTime(run.started_at)}</span>
            <span>•</span>
            <span>Duration: {duration}</span>
          </div>
        </div>
        <Button onClick={handleExport} variant="outline">
          <Download className="mr-2 h-4 w-4" />
          Export CSV
        </Button>
      </div>

      {/* Progress (if running) */}
      {isRunning && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Loader2 className="h-5 w-5 animate-spin" />
              Run in Progress
            </CardTitle>
            <CardDescription>
              Cleaning up your inbox...
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Progress value={progress} className="h-2" />
            <p className="text-sm text-muted-foreground mt-2">
              {progress}% complete
            </p>
          </CardContent>
        </Card>
      )}

      {/* Error Alert */}
      {run.error_message && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertTitle>Run Failed</AlertTitle>
          <AlertDescription>{run.error_message}</AlertDescription>
        </Alert>
      )}

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Emails Deleted</CardTitle>
            <Trash2 className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(emailsDeleted)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Storage Freed</CardTitle>
            <Database className="h-4 w-4 text-success" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatBytes(bytesFreed)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Senders Processed</CardTitle>
            <Mail className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(sendersProcessed)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Filters Created</CardTitle>
            <Filter className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{filtersCreated}</div>
          </CardContent>
        </Card>
      </div>

      {/* Activity Log */}
      <Card>
        <CardHeader>
          <CardTitle>Activity Log</CardTitle>
          <CardDescription>
            Detailed list of all actions performed during this run
          </CardDescription>
        </CardHeader>
        <CardContent>
          {actionsLoading && (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          )}

          {actionsError && (
            <Alert variant="destructive">
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>
                Failed to load activity log.
              </AlertDescription>
            </Alert>
          )}

          {!actionsLoading && !actionsError && (!actions || actions.length === 0) && (
            <div className="text-center py-8 text-muted-foreground">
              No actions recorded yet.
            </div>
          )}

          {!actionsLoading && !actionsError && actions && actions.length > 0 && (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Action</TableHead>
                    <TableHead>Sender</TableHead>
                    <TableHead>Emails</TableHead>
                    <TableHead>Time</TableHead>
                    <TableHead>Details</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {actions.map((action) => (
                    <TableRow key={action.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getActionIcon(action.action_type)}
                          <span className="capitalize">{action.action_type}</span>
                        </div>
                      </TableCell>
                      <TableCell className="font-medium">
                        {action.sender_email}
                      </TableCell>
                      <TableCell>{formatNumber(action.email_count)}</TableCell>
                      <TableCell className="text-muted-foreground text-sm">
                        {formatRelativeTime(action.timestamp)}
                      </TableCell>
                      <TableCell className="text-muted-foreground text-sm">
                        {action.notes || "-"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination for actions */}
              {actions.length === ACTIONS_PER_PAGE && (
                <div className="flex items-center justify-between mt-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setActionsPage(actionsPage - 1)}
                    disabled={actionsPage === 0}
                  >
                    Previous
                  </Button>
                  <span className="text-sm text-muted-foreground">
                    Page {actionsPage + 1}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setActionsPage(actionsPage + 1)}
                    disabled={actions.length < ACTIONS_PER_PAGE}
                  >
                    Next
                  </Button>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
