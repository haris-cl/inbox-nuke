"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import useSWR from "swr"
import { Trash2, Database, Mail, Filter, BarChart3, Shield, AlertCircle, TrendingUp, Clock, HardDrive, History } from "lucide-react"
import { StatCard } from "@/components/stat-card"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { api, Stats, Run, RunAction, ScoringStats } from "@/lib/api"
import { InboxHealthCard } from "./components/inbox-health-card"
import Link from "next/link"

export default function DashboardPage() {
  const router = useRouter()
  const [actions, setActions] = useState<RunAction[]>([])

  // Fetch current stats
  const { data: stats } = useSWR<Stats>(
    "/api/stats/current",
    () => api.getCurrentStats(),
    { refreshInterval: 0 }
  )

  // Convert bytes to MB for display
  const bytesToMB = (bytes: number): number => {
    return Math.round(bytes / (1024 * 1024))
  }

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return "0 B"
    const k = 1024
    const sizes = ["B", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  const formatDate = (dateStr?: string): string => {
    if (!dateStr) return "Never"
    const date = new Date(dateStr)
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-5xl font-black tracking-tight gradient-text">Dashboard</h1>
        <p className="text-muted-foreground text-lg">
          Your inbox at a glance
        </p>
      </div>

      {/* V2 Inbox Health Card - Primary CTA */}
      <div className="animate-fade-in-up animate-delay-100">
        <InboxHealthCard />
      </div>

      {/* Lifetime Stats */}
      <div className="grid gap-6 md:grid-cols-4 animate-fade-in-up animate-delay-200">
        <StatCard
          icon={Trash2}
          label="Emails Cleaned"
          value={stats?.total_emails_deleted || 0}
          variant="destructive"
        />
        <StatCard
          icon={HardDrive}
          label="Space Freed"
          value={bytesToMB(stats?.total_bytes_freed || 0)}
          suffix=" MB"
          variant="success"
        />
        <StatCard
          icon={Mail}
          label="Senders Analyzed"
          value={stats?.total_senders || 0}
          variant="default"
        />
        <StatCard
          icon={History}
          label="Total Cleanups"
          value={stats?.total_runs || 0}
          variant="default"
        />
      </div>

      {/* Quick Actions */}
      <Card className="animate-fade-in-up animate-delay-300">
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Tools to manage your inbox</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <Link href="/dashboard/space">
              <Card className="cursor-pointer hover:bg-muted/50 transition-colors">
                <CardContent className="p-4 flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-blue-500/10 flex items-center justify-center">
                    <HardDrive className="w-5 h-5 text-blue-500" />
                  </div>
                  <div>
                    <div className="font-medium">Free Up Space</div>
                    <div className="text-xs text-muted-foreground">Delete large emails</div>
                  </div>
                </CardContent>
              </Card>
            </Link>

            <Link href="/dashboard/settings">
              <Card className="cursor-pointer hover:bg-muted/50 transition-colors">
                <CardContent className="p-4 flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-green-500/10 flex items-center justify-center">
                    <Shield className="w-5 h-5 text-green-500" />
                  </div>
                  <div>
                    <div className="font-medium">Protected Senders</div>
                    <div className="text-xs text-muted-foreground">Manage whitelist</div>
                  </div>
                </CardContent>
              </Card>
            </Link>

            <Link href="/dashboard/history">
              <Card className="cursor-pointer hover:bg-muted/50 transition-colors">
                <CardContent className="p-4 flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-purple-500/10 flex items-center justify-center">
                    <Clock className="w-5 h-5 text-purple-500" />
                  </div>
                  <div>
                    <div className="font-medium">History</div>
                    <div className="text-xs text-muted-foreground">View past cleanups</div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Last Cleanup Info */}
      {stats?.last_run && (
        <Card className="animate-fade-in-up animate-delay-400">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
                  <Clock className="w-5 h-5 text-muted-foreground" />
                </div>
                <div>
                  <div className="font-medium">Last Cleanup</div>
                  <div className="text-sm text-muted-foreground">
                    {formatDate(stats.last_run.finished_at || stats.last_run.started_at)} •{" "}
                    {stats.last_run.emails_deleted} emails cleaned
                  </div>
                </div>
              </div>
              <Link href="/dashboard/history">
                <Button variant="ghost" size="sm">
                  View History
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
