"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import {
  MailX,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Zap,
  Mail,
  Globe,
  CheckCircle,
  Info,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { useCleanup } from "../cleanup-context"
import { v2 } from "@/lib/api"

interface UnsubscribableSender {
  email: string
  display_name?: string
  email_count: number
  has_one_click: boolean
  unsubscribe_method: string
  selected: boolean
}

export default function UnsubscribePage() {
  const router = useRouter()
  const { sessionId } = useCleanup()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [senders, setSenders] = useState<UnsubscribableSender[]>([])
  const [selectedEmails, setSelectedEmails] = useState<Set<string>>(new Set())

  // Fetch unsubscribable senders
  useEffect(() => {
    if (!sessionId) {
      router.push("/dashboard/cleanup/scanning")
      return
    }

    const fetchSenders = async () => {
      try {
        const response = await v2.getUnsubscribeSenders(sessionId)
        setSenders(response.senders)
        // Initialize selected set with pre-selected senders
        const preSelected = new Set(
          response.senders.filter((s) => s.selected).map((s) => s.email)
        )
        setSelectedEmails(preSelected)
      } catch (error) {
        console.error("Failed to fetch senders:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchSenders()
  }, [sessionId, router])

  const toggleSender = (email: string) => {
    setSelectedEmails((prev) => {
      const next = new Set(prev)
      if (next.has(email)) {
        next.delete(email)
      } else {
        next.add(email)
      }
      return next
    })
  }

  const selectAll = () => {
    setSelectedEmails(new Set(senders.map((s) => s.email)))
  }

  const selectNone = () => {
    setSelectedEmails(new Set())
  }

  const handleContinue = async () => {
    setSaving(true)
    try {
      await v2.updateUnsubscribeSelections(sessionId!, Array.from(selectedEmails))
      router.push("/dashboard/cleanup/confirm")
    } catch (error) {
      console.error("Failed to save selections:", error)
    } finally {
      setSaving(false)
    }
  }

  const getMethodIcon = (method: string) => {
    switch (method) {
      case "one_click":
        return <Zap className="w-4 h-4 text-green-500" />
      case "mailto":
        return <Mail className="w-4 h-4 text-blue-500" />
      case "http":
        return <Globe className="w-4 h-4 text-orange-500" />
      default:
        return <Mail className="w-4 h-4 text-muted-foreground" />
    }
  }

  const getMethodLabel = (method: string) => {
    switch (method) {
      case "one_click":
        return "One-Click"
      case "mailto":
        return "Email"
      case "http":
        return "Web"
      default:
        return "Unknown"
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground">Finding senders to unsubscribe from...</p>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="w-16 h-16 rounded-full bg-purple-500/10 flex items-center justify-center mx-auto mb-4">
          <MailX className="w-8 h-8 text-purple-500" />
        </div>
        <h1 className="text-3xl font-bold">Unsubscribe from Mailing Lists</h1>
        <p className="text-muted-foreground">
          Select senders you want to unsubscribe from to stop receiving future emails
        </p>
      </div>

      {/* Info Card */}
      <Card className="border-purple-500/30 bg-purple-500/5">
        <CardContent className="p-4 flex items-start gap-3">
          <Info className="w-5 h-5 text-purple-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <span className="font-medium text-purple-600">How it works:</span>
            <span className="text-muted-foreground">
              {" "}We'll automatically unsubscribe you using modern RFC 8058 one-click
              unsubscribe when available, or send an unsubscribe email for older systems.
            </span>
          </div>
        </CardContent>
      </Card>

      {senders.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <CheckCircle className="w-12 h-12 mx-auto text-green-500 mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Mailing Lists Found</h3>
            <p className="text-muted-foreground">
              None of the emails marked for deletion have unsubscribe options.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Selection Controls */}
          <div className="flex items-center justify-between">
            <div className="text-sm text-muted-foreground">
              {selectedEmails.size} of {senders.length} selected
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={selectAll}>
                Select All
              </Button>
              <Button variant="outline" size="sm" onClick={selectNone}>
                Select None
              </Button>
            </div>
          </div>

          {/* Senders List */}
          <div className="space-y-2">
            {senders.map((sender) => (
              <Card
                key={sender.email}
                className={`cursor-pointer transition-all ${
                  selectedEmails.has(sender.email)
                    ? "ring-2 ring-primary bg-primary/5"
                    : "hover:bg-muted/50"
                }`}
                onClick={() => toggleSender(sender.email)}
              >
                <CardContent className="p-4 flex items-center gap-4">
                  {/* Checkbox */}
                  <div
                    className={`w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 ${
                      selectedEmails.has(sender.email)
                        ? "bg-primary border-primary"
                        : "border-muted-foreground/30"
                    }`}
                  >
                    {selectedEmails.has(sender.email) && (
                      <CheckCircle className="w-4 h-4 text-primary-foreground" />
                    )}
                  </div>

                  {/* Sender Info */}
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">
                      {sender.display_name || sender.email}
                    </div>
                    {sender.display_name && (
                      <div className="text-sm text-muted-foreground truncate">
                        {sender.email}
                      </div>
                    )}
                  </div>

                  {/* Email Count */}
                  <div className="text-sm text-muted-foreground">
                    {sender.email_count} emails
                  </div>

                  {/* Unsubscribe Method */}
                  <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-muted text-xs font-medium">
                    {getMethodIcon(sender.unsubscribe_method)}
                    <span>{getMethodLabel(sender.unsubscribe_method)}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}

      {/* Action Buttons */}
      <div className="flex gap-4 pt-4">
        <Button
          variant="outline"
          size="lg"
          className="flex-1"
          onClick={() => router.push("/dashboard/cleanup/review")}
        >
          <ChevronLeft className="w-4 h-4 mr-2" />
          Back
        </Button>

        <Button
          size="lg"
          className="flex-1"
          onClick={handleContinue}
          disabled={saving}
        >
          {saving ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              Continue
              <ChevronRight className="w-4 h-4 ml-2" />
            </>
          )}
        </Button>
      </div>

      {/* Skip Option */}
      <p className="text-xs text-center text-muted-foreground">
        You can skip this step by clicking Continue without selecting any senders.
      </p>
    </div>
  )
}
