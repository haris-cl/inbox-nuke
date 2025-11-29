"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import {
  Loader2,
  RefreshCw,
  Play,
  Clock,
  Trash2,
  MailCheck,
  ArrowRight,
  History,
  Sparkles,
  CheckCircle,
  HardDrive,
  MailX,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { v2 } from "@/lib/api"
import { useCleanup, ActiveSession } from "./cleanup-context"

interface PastSession {
  session_id: string
  status: string
  mode?: string
  total_emails: number
  scanned_emails: number
  total_to_cleanup: number
  total_protected: number
  emails_deleted: number
  space_freed: number
  senders_unsubscribed: number
  created_at: string
  completed_at?: string
  can_take_action: boolean
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return "just now"
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  return `${diffDays}d ago`
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B"
  const k = 1024
  const sizes = ["B", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i]
}

function getStatusLabel(status: string): string {
  switch (status) {
    case "scanning":
      return "Scanning"
    case "ready_for_review":
      return "Ready for Review"
    case "reviewing":
      return "In Review"
    case "confirming":
      return "Ready to Confirm"
    case "executing":
      return "Executing"
    case "completed":
      return "Completed"
    case "failed":
      return "Failed"
    default:
      return status
  }
}

function getStatusColor(status: string): string {
  switch (status) {
    case "completed":
      return "text-green-500"
    case "failed":
      return "text-destructive"
    case "scanning":
      return "text-blue-500"
    default:
      return "text-primary"
  }
}

/**
 * V2 Cleanup Entry Page
 * Shows active session, past sessions with actions available, and option to start new
 */
export default function CleanupPage() {
  const router = useRouter()
  const { resumeSession, startCleanup } = useCleanup()
  const [loading, setLoading] = useState(true)
  const [activeSession, setActiveSession] = useState<ActiveSession | null>(null)
  const [pastSessions, setPastSessions] = useState<PastSession[]>([])
  const [abandoning, setAbandoning] = useState(false)
  const [starting, setStarting] = useState(false)
  const [reopening, setReopening] = useState<string | null>(null)

  // Fetch active session and past sessions
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [activeData, sessionsData] = await Promise.all([
          v2.getActiveSession(),
          v2.listSessions(10, true),
        ])

        if (activeData.has_active_session) {
          setActiveSession(activeData)
        }

        // Filter to show sessions that can have actions taken
        // and exclude the active session
        const actionableSessions = sessionsData.sessions.filter(
          (s) =>
            s.can_take_action &&
            s.session_id !== activeData.session_id
        )
        setPastSessions(actionableSessions)

        // If no active session and no past actionable sessions, just start new
        if (!activeData.has_active_session && actionableSessions.length === 0) {
          router.push("/dashboard/cleanup/scanning")
        }
      } catch (error) {
        console.error("Failed to fetch sessions:", error)
        router.push("/dashboard/cleanup/scanning")
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [router])

  const handleResume = () => {
    if (!activeSession?.session_id || !activeSession?.status) return

    resumeSession(
      activeSession.session_id,
      activeSession.status,
      activeSession.mode
    )

    // Navigate based on status
    const routeMap: Record<string, string> = {
      scanning: "/dashboard/cleanup/scanning",
      ready_for_review: "/dashboard/cleanup/report",
      reviewing: "/dashboard/cleanup/review",
      confirming: "/dashboard/cleanup/confirm",
    }
    router.push(routeMap[activeSession.status] || "/dashboard/cleanup/report")
  }

  const handleStartNew = async () => {
    if (activeSession?.session_id) {
      setAbandoning(true)
      try {
        await v2.abandonSession(activeSession.session_id)
      } catch (error) {
        console.error("Failed to abandon session:", error)
      }
    }

    setStarting(true)
    await startCleanup()
    router.push("/dashboard/cleanup/scanning")
  }

  const handleReopenSession = async (sessionId: string) => {
    setReopening(sessionId)
    try {
      await v2.reopenSession(sessionId)
      resumeSession(sessionId, "ready_for_review", null)
      router.push("/dashboard/cleanup/report")
    } catch (error) {
      console.error("Failed to reopen session:", error)
      setReopening(null)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground">Loading cleanup sessions...</p>
      </div>
    )
  }

  const hasContent = activeSession || pastSessions.length > 0

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
          <Sparkles className="w-8 h-8 text-primary" />
        </div>
        <h1 className="text-2xl font-bold">Inbox Cleanup</h1>
        <p className="text-muted-foreground">
          {hasContent
            ? "Continue a previous scan or start fresh"
            : "Clean up your inbox with AI-powered recommendations"}
        </p>
      </div>

      {/* Active Session */}
      {activeSession && (
        <Card className="border-primary/30 bg-primary/5">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                <CardTitle className="text-base">Active Session</CardTitle>
              </div>
              {activeSession.created_at && (
                <span className="text-xs text-muted-foreground flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {formatTimeAgo(activeSession.created_at)}
                </span>
              )}
            </div>
            <CardDescription>
              {getStatusLabel(activeSession.status || "")}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-lg font-bold">
                  {activeSession.scanned_emails.toLocaleString()}
                </div>
                <div className="text-xs text-muted-foreground">Scanned</div>
              </div>
              <div>
                <div className="text-lg font-bold text-destructive">
                  {activeSession.total_to_cleanup.toLocaleString()}
                </div>
                <div className="text-xs text-muted-foreground">To Clean</div>
              </div>
              <div>
                <div className="text-lg font-bold text-green-500">
                  {activeSession.total_protected.toLocaleString()}
                </div>
                <div className="text-xs text-muted-foreground">Protected</div>
              </div>
            </div>

            <Button className="w-full" onClick={handleResume}>
              <Play className="w-4 h-4 mr-2" />
              Continue Session
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Past Sessions with Actions Available */}
      {pastSessions.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-muted-foreground" />
            <h2 className="font-semibold">Previous Scans</h2>
            <span className="text-xs text-muted-foreground">
              (actions available)
            </span>
          </div>

          <div className="space-y-3">
            {pastSessions.map((session) => (
              <Card key={session.session_id} className="hover:bg-muted/50 transition-colors">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className={`text-sm font-medium ${getStatusColor(session.status)}`}>
                          {getStatusLabel(session.status)}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {formatTimeAgo(session.created_at)}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <MailCheck className="w-3 h-3" />
                          {session.scanned_emails.toLocaleString()} scanned
                        </span>
                        {session.total_to_cleanup > 0 && (
                          <span className="flex items-center gap-1 text-destructive">
                            <Trash2 className="w-3 h-3" />
                            {session.total_to_cleanup.toLocaleString()} to clean
                          </span>
                        )}
                        {session.emails_deleted > 0 && (
                          <span className="flex items-center gap-1 text-green-500">
                            <CheckCircle className="w-3 h-3" />
                            {session.emails_deleted.toLocaleString()} deleted
                          </span>
                        )}
                      </div>
                    </div>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleReopenSession(session.session_id)}
                      disabled={reopening === session.session_id}
                    >
                      {reopening === session.session_id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <>
                          <Play className="w-4 h-4 mr-1" />
                          Take Action
                        </>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Start New Button */}
      <div className="pt-4">
        <Button
          variant={hasContent ? "outline" : "default"}
          size="lg"
          className="w-full"
          onClick={handleStartNew}
          disabled={abandoning || starting}
        >
          {abandoning || starting ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              {abandoning ? "Preparing..." : "Starting scan..."}
            </>
          ) : (
            <>
              <RefreshCw className="w-4 h-4 mr-2" />
              {hasContent ? "Start Fresh Scan" : "Start Cleanup"}
            </>
          )}
        </Button>

        {hasContent && (
          <p className="text-xs text-center text-muted-foreground mt-2">
            Starting a fresh scan will scan your inbox again for new recommendations
          </p>
        )}
      </div>
    </div>
  )
}
