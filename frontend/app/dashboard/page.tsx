"use client"

import { useState, useEffect } from "react"
import useSWR from "swr"
import { Trash2, Database, Mail, Filter } from "lucide-react"
import { StatCard } from "@/components/stat-card"
import { ControlPanel } from "@/components/control-panel"
import { ProgressSection } from "@/components/progress-section"
import { ActivityFeed } from "@/components/activity-feed"
import { api, Stats, Run, RunAction } from "@/lib/api"

export default function DashboardPage() {
  const [currentRun, setCurrentRun] = useState<Run | null>(null)
  const [actions, setActions] = useState<RunAction[]>([])
  const [isOperating, setIsOperating] = useState(false)

  // Fetch current stats
  const { data: stats, mutate: mutateStats } = useSWR<Stats>(
    "/api/stats/current",
    () => api.getCurrentStats(),
    {
      refreshInterval: currentRun?.status === "running" ? 2000 : 0,
    }
  )

  // Fetch run actions when a run is active
  useEffect(() => {
    if (currentRun?.id) {
      loadActions()
      const interval = setInterval(loadActions, 2000)
      return () => clearInterval(interval)
    }
  }, [currentRun?.id])

  const loadActions = async () => {
    if (!currentRun?.id) return
    try {
      const fetchedActions = await api.getRunActions(currentRun.id, { limit: 20, offset: 0 })
      setActions(fetchedActions)
    } catch (error) {
      console.error("Failed to load actions:", error)
    }
  }

  const handleStart = async () => {
    try {
      setIsOperating(true)
      const run = await api.startRun()
      setCurrentRun(run)
      mutateStats()
    } catch (error) {
      console.error("Failed to start run:", error)
      alert("Failed to start cleanup. Please try again.")
    } finally {
      setIsOperating(false)
    }
  }

  const handlePause = async () => {
    if (!currentRun?.id) return
    try {
      setIsOperating(true)
      const run = await api.pauseRun(currentRun.id)
      setCurrentRun(run)
      mutateStats()
    } catch (error) {
      console.error("Failed to pause run:", error)
      alert("Failed to pause cleanup. Please try again.")
    } finally {
      setIsOperating(false)
    }
  }

  const handleResume = async () => {
    if (!currentRun?.id) return
    try {
      setIsOperating(true)
      const run = await api.resumeRun(currentRun.id)
      setCurrentRun(run)
      mutateStats()
    } catch (error) {
      console.error("Failed to resume run:", error)
      alert("Failed to resume cleanup. Please try again.")
    } finally {
      setIsOperating(false)
    }
  }

  const handleCancel = async () => {
    if (!currentRun?.id) return
    try {
      setIsOperating(true)
      const run = await api.cancelRun(currentRun.id)
      setCurrentRun(run)
      mutateStats()
    } catch (error) {
      console.error("Failed to cancel run:", error)
      alert("Failed to cancel cleanup. Please try again.")
    } finally {
      setIsOperating(false)
    }
  }

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return "0 B"
    const k = 1024
    const sizes = ["B", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  // Use active_run from stats if no currentRun is set
  const activeRun = currentRun || stats?.active_run
  const runStatus = (activeRun?.status || "idle") as "idle" | "pending" | "running" | "paused" | "completed" | "failed" | "cancelled"
  const isRunActive = runStatus === "running" || runStatus === "paused"

  // Calculate progress from active_run if available
  const progress = stats?.active_run?.senders_total
    ? Math.round((stats.active_run.senders_processed / stats.active_run.senders_total) * 100)
    : 0

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Monitor your inbox cleanup progress and statistics
        </p>
      </div>

      {/* Control Panel */}
      <ControlPanel
        status={runStatus}
        onStart={handleStart}
        onPause={handlePause}
        onResume={handleResume}
        onCancel={handleCancel}
        disabled={isOperating}
      />

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={Trash2}
          label="Emails Deleted"
          value={stats?.active_run?.emails_deleted || stats?.total_emails_deleted || 0}
          variant="destructive"
        />
        <StatCard
          icon={Database}
          label="Storage Freed"
          value={stats?.active_run?.bytes_freed_estimate || stats?.total_bytes_freed || 0}
          variant="success"
          suffix={` ${formatBytes(stats?.active_run?.bytes_freed_estimate || stats?.total_bytes_freed || 0)}`}
          decimals={0}
        />
        <StatCard
          icon={Mail}
          label="Senders Processed"
          value={stats?.active_run?.senders_processed || 0}
          variant="default"
        />
        <StatCard
          icon={Filter}
          label="Total Senders"
          value={stats?.active_run?.senders_total || stats?.total_senders || 0}
          variant="default"
        />
      </div>

      {/* Progress Section - Only shown when run is active */}
      {isRunActive && stats?.active_run && (
        <ProgressSection
          percent={progress}
          phase={runStatus === "paused" ? "Paused" : "Processing"}
          current={stats.active_run.senders_processed}
          total={stats.active_run.senders_total}
        />
      )}

      {/* Activity Feed */}
      <ActivityFeed actions={actions} />
    </div>
  )
}
