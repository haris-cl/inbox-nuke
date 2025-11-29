"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import {
  Shield,
  Trash2,
  HardDrive,
  AlertTriangle,
  ChevronLeft,
  Loader2,
  Clock,
  CheckCircle,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useCleanup, ConfirmationSummary } from "../cleanup-context"

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B"
  const k = 1024
  const sizes = ["B", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i]
}

export default function ConfirmPage() {
  const router = useRouter()
  const { sessionId, confirmation, setConfirmation, confirmCleanup } = useCleanup()
  const [loading, setLoading] = useState(true)
  const [confirming, setConfirming] = useState(false)

  // Fetch confirmation summary
  useEffect(() => {
    if (!sessionId) {
      router.push("/dashboard/cleanup/scanning")
      return
    }

    const fetchConfirmation = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/api/cleanup/confirmation/${sessionId}`
        )
        const data: ConfirmationSummary = await response.json()
        setConfirmation(data)
      } catch (error) {
        console.error("Failed to fetch confirmation:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchConfirmation()
  }, [sessionId, router, setConfirmation])

  const handleConfirm = async () => {
    setConfirming(true)
    await confirmCleanup()
    router.push("/dashboard/cleanup/success")
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground">Preparing confirmation...</p>
      </div>
    )
  }

  const conf = confirmation

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">Ready to Clean Up?</h1>
        <p className="text-muted-foreground">
          Review what will happen before confirming
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="w-10 h-10 rounded-full bg-destructive/10 flex items-center justify-center mx-auto mb-2">
              <Trash2 className="w-5 h-5 text-destructive" />
            </div>
            <div className="text-2xl font-bold">
              {conf?.emails_to_delete.toLocaleString() || 0}
            </div>
            <div className="text-xs text-muted-foreground">Emails to remove</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4 text-center">
            <div className="w-10 h-10 rounded-full bg-blue-500/10 flex items-center justify-center mx-auto mb-2">
              <HardDrive className="w-5 h-5 text-blue-500" />
            </div>
            <div className="text-2xl font-bold">
              {formatBytes(conf?.space_to_be_freed || 0)}
            </div>
            <div className="text-xs text-muted-foreground">Space to free</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4 text-center">
            <div className="w-10 h-10 rounded-full bg-green-500/10 flex items-center justify-center mx-auto mb-2">
              <Shield className="w-5 h-5 text-green-500" />
            </div>
            <div className="text-2xl font-bold">
              {conf?.protected_count.toLocaleString() || 0}
            </div>
            <div className="text-xs text-muted-foreground">Protected</div>
          </CardContent>
        </Card>
      </div>

      {/* Safety Assurance */}
      <Card className="border-blue-500/30 bg-blue-500/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-blue-600">
            <Shield className="w-5 h-5" />
            Safety First
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-start gap-3">
            <Clock className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-medium">30-Day Recovery Window</div>
              <p className="text-sm text-muted-foreground">
                All emails go to Trash, not permanent deletion. You can recover
                anything for 30 days.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-medium">Auto-Protected Categories</div>
              <ul className="text-sm text-muted-foreground mt-1 space-y-1">
                {conf?.safety_info.auto_protected_categories.map((cat, i) => (
                  <li key={i}>• {cat}</li>
                ))}
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <Button
          variant="outline"
          size="lg"
          className="flex-1"
          onClick={() => router.push("/dashboard/cleanup/unsubscribe")}
        >
          <ChevronLeft className="w-4 h-4 mr-2" />
          Go Back
        </Button>

        <Button
          size="lg"
          className="flex-1 bg-primary hover:bg-primary/90"
          onClick={handleConfirm}
          disabled={confirming}
        >
          {confirming ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Starting cleanup...
            </>
          ) : (
            <>
              <Trash2 className="w-4 h-4 mr-2" />
              Confirm Cleanup
            </>
          )}
        </Button>
      </div>

      {/* Fine Print */}
      <p className="text-xs text-center text-muted-foreground">
        By clicking "Confirm Cleanup", you agree to move the selected emails to
        Trash. This action can be undone within 30 days.
      </p>
    </div>
  )
}
