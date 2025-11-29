"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import {
  Sparkles,
  HardDrive,
  Trash2,
  Loader2,
  ChevronRight,
  CheckCircle,
  AlertTriangle,
  AlertCircle,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { v2, InboxHealth } from "@/lib/api"

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B"
  const k = 1024
  const sizes = ["B", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i]
}

interface InboxHealthCardProps {
  onStartCleanup?: () => void
}

export function InboxHealthCard({ onStartCleanup }: InboxHealthCardProps) {
  const router = useRouter()
  const [health, setHealth] = useState<InboxHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await v2.getInboxHealth()
        setHealth(data)
      } catch (err) {
        setError("Could not check inbox health")
        console.error("Inbox health error:", err)
      } finally {
        setLoading(false)
      }
    }

    fetchHealth()
  }, [])

  const handleStartCleanup = () => {
    if (onStartCleanup) {
      onStartCleanup()
    } else {
      router.push("/dashboard/cleanup")
    }
  }

  if (loading) {
    return (
      <Card className="bg-gradient-to-br from-primary/5 to-primary/10 border-primary/20">
        <CardContent className="p-8 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  if (error || !health) {
    return (
      <Card className="bg-gradient-to-br from-muted/50 to-muted border-muted">
        <CardContent className="p-8">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-full bg-muted-foreground/10 flex items-center justify-center">
              <AlertCircle className="w-7 h-7 text-muted-foreground" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold">Connect Gmail to check inbox health</h3>
              <p className="text-sm text-muted-foreground">
                {error || "Unable to analyze your inbox"}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const statusConfig = {
    healthy: {
      icon: CheckCircle,
      color: "text-green-500",
      bg: "bg-green-500/10",
      borderColor: "border-green-500/20",
      gradient: "from-green-500/5 to-green-500/10",
      label: "Inbox is Healthy",
      message: "Your inbox is clean. Keep up the good work!",
    },
    needs_attention: {
      icon: AlertTriangle,
      color: "text-yellow-500",
      bg: "bg-yellow-500/10",
      borderColor: "border-yellow-500/20",
      gradient: "from-yellow-500/5 to-yellow-500/10",
      label: "Needs Attention",
      message: "Some cleanup recommended to keep your inbox tidy.",
    },
    critical: {
      icon: AlertCircle,
      color: "text-destructive",
      bg: "bg-destructive/10",
      borderColor: "border-destructive/20",
      gradient: "from-destructive/5 to-destructive/10",
      label: "Cleanup Needed",
      message: "Your inbox has accumulated a lot of clutter.",
    },
    unknown: {
      icon: Sparkles,
      color: "text-primary",
      bg: "bg-primary/10",
      borderColor: "border-primary/20",
      gradient: "from-primary/5 to-primary/10",
      label: "Ready to Scan",
      message: "Run a cleanup to analyze your inbox.",
    },
    error: {
      icon: AlertCircle,
      color: "text-muted-foreground",
      bg: "bg-muted",
      borderColor: "border-muted",
      gradient: "from-muted/50 to-muted",
      label: "Status Unknown",
      message: "Could not determine inbox status.",
    },
  }

  const config = statusConfig[health.status] || statusConfig.unknown
  const StatusIcon = config.icon

  return (
    <Card className={`bg-gradient-to-br ${config.gradient} ${config.borderColor}`}>
      <CardContent className="p-8">
        <div className="flex flex-col md:flex-row md:items-center gap-6">
          {/* Status Icon & Label */}
          <div className="flex items-center gap-4 flex-1">
            <div className={`w-16 h-16 rounded-full ${config.bg} flex items-center justify-center`}>
              <StatusIcon className={`w-8 h-8 ${config.color}`} />
            </div>
            <div>
              <h2 className="text-2xl font-bold">{config.label}</h2>
              <p className="text-muted-foreground">{config.message}</p>
            </div>
          </div>

          {/* Stats */}
          {health.potential_cleanup_count > 0 && (
            <div className="flex gap-6 md:gap-8">
              <div className="text-center">
                <div className="flex items-center justify-center gap-1 text-2xl font-bold">
                  <Trash2 className="w-5 h-5 text-muted-foreground" />
                  {health.potential_cleanup_count.toLocaleString()}
                </div>
                <div className="text-xs text-muted-foreground">to clean</div>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center gap-1 text-2xl font-bold">
                  <HardDrive className="w-5 h-5 text-muted-foreground" />
                  {formatBytes(health.potential_space_savings)}
                </div>
                <div className="text-xs text-muted-foreground">to free</div>
              </div>
            </div>
          )}

          {/* Action Button */}
          <Button size="lg" onClick={handleStartCleanup} className="md:ml-4">
            <Sparkles className="w-4 h-4 mr-2" />
            Start Cleanup
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
