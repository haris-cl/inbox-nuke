"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Loader2, Mail, ShoppingBag, Users, Bell, Sparkles } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { useCleanup, CleanupProgress } from "../cleanup-context"

const TRANSPARENCY_MESSAGES = [
  "Checking which senders you reply to...",
  "Identifying promotional emails...",
  "Finding newsletters and mailing lists...",
  "Analyzing your engagement patterns...",
  "Categorizing social notifications...",
  "Looking for large attachments...",
  "Checking for security-sensitive emails...",
  "Building your personalized cleanup plan...",
]

export default function ScanningPage() {
  const router = useRouter()
  const { sessionId, status, progress, startCleanup, updateProgress, setError } = useCleanup()
  const [transparencyIndex, setTransparencyIndex] = useState(0)

  // Start cleanup when page loads
  useEffect(() => {
    if (!sessionId) {
      startCleanup()
    }
  }, [sessionId, startCleanup])

  // Poll for progress
  useEffect(() => {
    if (!sessionId) return

    const pollProgress = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/api/cleanup/progress/${sessionId}`
        )
        const data: CleanupProgress = await response.json()
        updateProgress(data)

        // Navigate when ready
        if (data.status === "ready_for_review") {
          router.push("/dashboard/cleanup/report")
        } else if (data.status === "failed") {
          setError(data.error || "Scan failed")
        }
      } catch (error) {
        console.error("Progress poll error:", error)
      }
    }

    const interval = setInterval(pollProgress, 2000)
    pollProgress() // Initial poll

    return () => clearInterval(interval)
  }, [sessionId, router, updateProgress, setError])

  // Rotate transparency messages
  useEffect(() => {
    const interval = setInterval(() => {
      setTransparencyIndex(prev => (prev + 1) % TRANSPARENCY_MESSAGES.length)
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  const discoveries = progress?.discoveries || {
    promotions: 0,
    newsletters: 0,
    social: 0,
    updates: 0,
    low_value: 0,
  }

  const totalDiscovered = Object.values(discoveries).reduce((a, b) => a + b, 0)
  const progressPercent = progress ? Math.round(progress.progress * 100) : 0

  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center p-8">
      {/* Main scanning animation */}
      <div className="relative mb-8">
        <div className="w-32 h-32 rounded-full bg-primary/10 flex items-center justify-center animate-pulse">
          <Mail className="w-16 h-16 text-primary" />
        </div>
        <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
          <Sparkles className="w-4 h-4 text-primary-foreground" />
        </div>
      </div>

      {/* Progress */}
      <h1 className="text-3xl font-bold mb-2">Scanning your inbox</h1>
      <p className="text-muted-foreground mb-6 h-6 transition-opacity">
        {TRANSPARENCY_MESSAGES[transparencyIndex]}
      </p>

      <div className="w-full max-w-md mb-8">
        <Progress value={progressPercent} className="h-3" />
        <div className="flex justify-between mt-2 text-sm text-muted-foreground">
          <span>{progress?.scanned_emails?.toLocaleString() || 0} emails scanned</span>
          <span>{progressPercent}%</span>
        </div>
      </div>

      {/* Live discoveries */}
      {totalDiscovered > 0 && (
        <Card className="w-full max-w-md">
          <CardContent className="p-6">
            <h3 className="font-semibold mb-4 text-center">Live Discoveries</h3>
            <div className="grid grid-cols-2 gap-4">
              <DiscoveryItem
                icon={<ShoppingBag className="w-5 h-5 text-orange-500" />}
                label="Promotions"
                count={discoveries.promotions}
              />
              <DiscoveryItem
                icon={<Mail className="w-5 h-5 text-blue-500" />}
                label="Newsletters"
                count={discoveries.newsletters}
              />
              <DiscoveryItem
                icon={<Users className="w-5 h-5 text-purple-500" />}
                label="Social"
                count={discoveries.social}
              />
              <DiscoveryItem
                icon={<Bell className="w-5 h-5 text-green-500" />}
                label="Updates"
                count={discoveries.updates}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Loading indicator */}
      <div className="mt-8 flex items-center gap-2 text-muted-foreground">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span className="text-sm">This usually takes 1-3 minutes</span>
      </div>
    </div>
  )
}

function DiscoveryItem({
  icon,
  label,
  count,
}: {
  icon: React.ReactNode
  label: string
  count: number
}) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
      {icon}
      <div>
        <div className="font-medium">{count.toLocaleString()}</div>
        <div className="text-xs text-muted-foreground">{label}</div>
      </div>
    </div>
  )
}
