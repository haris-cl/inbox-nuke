"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import {
  CheckCircle,
  HardDrive,
  Trash2,
  MailX,
  Loader2,
  Home,
  Settings,
  Sparkles,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { useCleanup, CleanupResults } from "../cleanup-context"

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B"
  const k = 1024
  const sizes = ["B", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i]
}

export default function SuccessPage() {
  const router = useRouter()
  const { sessionId, results, setResults, reset } = useCleanup()
  const [loading, setLoading] = useState(true)

  // Fetch results
  useEffect(() => {
    if (!sessionId) {
      router.push("/dashboard")
      return
    }

    const fetchResults = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/api/cleanup/results/${sessionId}`
        )
        const data: CleanupResults = await response.json()
        setResults(data)

        // Check if still executing
        if (data.status === "executing") {
          // Poll until complete
          const pollInterval = setInterval(async () => {
            const pollResponse = await fetch(
              `${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/api/cleanup/results/${sessionId}`
            )
            const pollData: CleanupResults = await pollResponse.json()
            setResults(pollData)

            if (pollData.status === "completed" || pollData.status === "failed") {
              clearInterval(pollInterval)
              setLoading(false)
            }
          }, 2000)

          return () => clearInterval(pollInterval)
        } else {
          setLoading(false)
        }
      } catch (error) {
        console.error("Failed to fetch results:", error)
        setLoading(false)
      }
    }

    fetchResults()
  }, [sessionId, router, setResults])

  const handleBackToDashboard = () => {
    reset()
    router.push("/dashboard")
  }

  if (loading || results?.status === "executing") {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="relative mb-8">
          <div className="w-24 h-24 rounded-full bg-primary/10 flex items-center justify-center animate-pulse">
            <Trash2 className="w-12 h-12 text-primary" />
          </div>
        </div>
        <h1 className="text-2xl font-bold mb-2">Cleaning your inbox...</h1>
        <p className="text-muted-foreground mb-6">
          Moving emails to trash and unsubscribing from mailing lists
        </p>
        <div className="flex items-center gap-2 text-primary">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>This may take a minute</span>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-8">
      {/* Success Header */}
      <div className="text-center space-y-4">
        <div className="w-20 h-20 rounded-full bg-green-500/10 flex items-center justify-center mx-auto">
          <CheckCircle className="w-10 h-10 text-green-500" />
        </div>
        <h1 className="text-3xl font-bold">
          <Sparkles className="w-8 h-8 inline-block text-yellow-500 mr-2" />
          Inbox Cleaned!
        </h1>
        <p className="text-muted-foreground">
          Your inbox is now cleaner and more organized
        </p>
      </div>

      {/* Results Stats */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardContent className="p-6 text-center">
            <div className="w-12 h-12 rounded-full bg-destructive/10 flex items-center justify-center mx-auto mb-3">
              <Trash2 className="w-6 h-6 text-destructive" />
            </div>
            <div className="text-3xl font-bold">
              {results?.emails_deleted.toLocaleString() || 0}
            </div>
            <div className="text-sm text-muted-foreground">Emails cleaned</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 text-center">
            <div className="w-12 h-12 rounded-full bg-blue-500/10 flex items-center justify-center mx-auto mb-3">
              <HardDrive className="w-6 h-6 text-blue-500" />
            </div>
            <div className="text-3xl font-bold">
              {formatBytes(results?.space_freed || 0)}
            </div>
            <div className="text-sm text-muted-foreground">Space freed</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 text-center">
            <div className="w-12 h-12 rounded-full bg-purple-500/10 flex items-center justify-center mx-auto mb-3">
              <MailX className="w-6 h-6 text-purple-500" />
            </div>
            <div className="text-3xl font-bold">
              {results?.senders_unsubscribed || 0}
            </div>
            <div className="text-sm text-muted-foreground">Unsubscribed</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 text-center">
            <div className="w-12 h-12 rounded-full bg-green-500/10 flex items-center justify-center mx-auto mb-3">
              <CheckCircle className="w-6 h-6 text-green-500" />
            </div>
            <div className="text-3xl font-bold">
              {results?.filters_created || 0}
            </div>
            <div className="text-sm text-muted-foreground">Filters created</div>
          </CardContent>
        </Card>
      </div>

      {/* Recovery Note */}
      <Card className="border-blue-500/30 bg-blue-500/5">
        <CardContent className="p-4 flex items-start gap-3">
          <div className="w-8 h-8 rounded-full bg-blue-500/10 flex items-center justify-center flex-shrink-0">
            <CheckCircle className="w-4 h-4 text-blue-500" />
          </div>
          <div>
            <div className="font-medium text-blue-600">
              Changed your mind?
            </div>
            <p className="text-sm text-muted-foreground">
              All deleted emails are in your Gmail Trash. You can recover them
              within 30 days.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Next Steps */}
      <div className="space-y-3">
        <h3 className="font-semibold text-center">What's next?</h3>

        <div className="grid gap-3">
          <Button
            size="lg"
            className="w-full"
            onClick={handleBackToDashboard}
          >
            <Home className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>

          <Button
            variant="outline"
            size="lg"
            className="w-full"
            onClick={() => router.push("/dashboard/settings")}
          >
            <Settings className="w-4 h-4 mr-2" />
            Protect More Senders
          </Button>
        </div>
      </div>
    </div>
  )
}
