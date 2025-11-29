"use client"

import { useState, useEffect } from "react"
import {
  HardDrive,
  Trash2,
  Loader2,
  CheckCircle,
  Filter,
  Mail,
  Calendar,
  AlertTriangle,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { api } from "@/lib/api"

interface LargeEmail {
  message_id: string
  subject: string
  from_email: string
  from_name?: string
  size: number
  size_mb: number
  date: string
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B"
  const k = 1024
  const sizes = ["B", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i]
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}

export default function SpacePage() {
  const [emails, setEmails] = useState<LargeEmail[]>([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(false)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [minSize, setMinSize] = useState("1")
  const [olderThan, setOlderThan] = useState("30")
  const [totalSize, setTotalSize] = useState(0)
  const [showConfirm, setShowConfirm] = useState(false)
  const [deleteResult, setDeleteResult] = useState<{
    deleted: number
    freed: number
  } | null>(null)

  const fetchEmails = async () => {
    setLoading(true)
    try {
      const result = await api.getLargeAttachments({
        min_size_mb: parseInt(minSize),
        older_than_days: parseInt(olderThan),
        max_results: 100,
      })
      setEmails(result.emails)
      setTotalSize(result.total_size_bytes)
      setSelected(new Set())
    } catch (error) {
      console.error("Failed to fetch large emails:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchEmails()
  }, [])

  const handleSelectAll = () => {
    if (selected.size === emails.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(emails.map((e) => e.message_id)))
    }
  }

  const handleSelect = (messageId: string) => {
    const newSelected = new Set(selected)
    if (newSelected.has(messageId)) {
      newSelected.delete(messageId)
    } else {
      newSelected.add(messageId)
    }
    setSelected(newSelected)
  }

  const selectedSize = emails
    .filter((e) => selected.has(e.message_id))
    .reduce((acc, e) => acc + e.size, 0)

  const handleDelete = async () => {
    setShowConfirm(false)
    setDeleting(true)
    try {
      const result = await api.cleanupAttachments(Array.from(selected))
      setDeleteResult({
        deleted: result.deleted_count,
        freed: result.bytes_freed,
      })
      // Refresh the list
      await fetchEmails()
    } catch (error) {
      console.error("Failed to delete emails:", error)
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-5xl font-black tracking-tight gradient-text">
          Free Up Space
        </h1>
        <p className="text-muted-foreground text-lg">
          Find and delete large emails to reclaim storage
        </p>
      </div>

      {/* Storage Overview */}
      <Card className="bg-gradient-to-br from-blue-500/5 to-blue-500/10 border-blue-500/20">
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-full bg-blue-500/10 flex items-center justify-center">
              <HardDrive className="w-7 h-7 text-blue-500" />
            </div>
            <div className="flex-1">
              <div className="text-sm text-muted-foreground">
                Found {emails.length} large emails totaling
              </div>
              <div className="text-3xl font-bold">{formatBytes(totalSize)}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-wrap gap-4 items-end">
            <div className="space-y-2">
              <label className="text-sm font-medium">Minimum Size</label>
              <select
                value={minSize}
                onChange={(e) => setMinSize(e.target.value)}
                className="flex h-10 w-[140px] items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <option value="1">1 MB+</option>
                <option value="5">5 MB+</option>
                <option value="10">10 MB+</option>
                <option value="25">25 MB+</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Older Than</label>
              <select
                value={olderThan}
                onChange={(e) => setOlderThan(e.target.value)}
                className="flex h-10 w-[140px] items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <option value="7">7 days</option>
                <option value="30">30 days</option>
                <option value="90">90 days</option>
                <option value="180">6 months</option>
                <option value="365">1 year</option>
              </select>
            </div>

            <Button onClick={fetchEmails} disabled={loading}>
              {loading ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Filter className="w-4 h-4 mr-2" />
              )}
              Apply Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Success Message */}
      {deleteResult && (
        <Card className="bg-green-500/10 border-green-500/20">
          <CardContent className="p-6 flex items-center gap-4">
            <CheckCircle className="w-6 h-6 text-green-500" />
            <div>
              <div className="font-medium">
                Successfully deleted {deleteResult.deleted} emails
              </div>
              <div className="text-sm text-muted-foreground">
                Freed {formatBytes(deleteResult.freed)} of storage
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="ml-auto"
              onClick={() => setDeleteResult(null)}
            >
              Dismiss
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Email List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Large Emails</CardTitle>
              <CardDescription>
                {selected.size > 0
                  ? `${selected.size} selected = ${formatBytes(selectedSize)}`
                  : "Select emails to delete"}
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleSelectAll}
                disabled={emails.length === 0}
              >
                {selected.size === emails.length ? "Deselect All" : "Select All"}
              </Button>
              <Button
                variant="destructive"
                size="sm"
                onClick={() => setShowConfirm(true)}
                disabled={selected.size === 0 || deleting}
              >
                {deleting ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Trash2 className="w-4 h-4 mr-2" />
                )}
                Delete Selected
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : emails.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <HardDrive className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <div className="font-medium">No large emails found</div>
              <div className="text-sm">
                Try adjusting your filters to find more emails
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              {emails.map((email) => (
                <div
                  key={email.message_id}
                  className={`flex items-center gap-4 p-4 rounded-lg border transition-colors cursor-pointer ${
                    selected.has(email.message_id)
                      ? "bg-primary/5 border-primary/30"
                      : "hover:bg-muted/50"
                  }`}
                  onClick={() => handleSelect(email.message_id)}
                >
                  <Checkbox
                    checked={selected.has(email.message_id)}
                    onCheckedChange={() => handleSelect(email.message_id)}
                    onClick={(e) => e.stopPropagation()}
                  />

                  <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
                    <Mail className="w-5 h-5 text-muted-foreground" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{email.subject}</div>
                    <div className="text-sm text-muted-foreground truncate">
                      {email.from_name || email.from_email}
                    </div>
                  </div>

                  <div className="flex items-center gap-6 text-sm">
                    <div className="flex items-center gap-1 text-muted-foreground">
                      <Calendar className="w-4 h-4" />
                      {formatDate(email.date)}
                    </div>
                    <div className="font-mono font-medium text-right w-20">
                      {email.size_mb.toFixed(1)} MB
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Confirmation Dialog */}
      <AlertDialog open={showConfirm} onOpenChange={setShowConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-destructive" />
              Delete {selected.size} emails?
            </AlertDialogTitle>
            <AlertDialogDescription>
              This will move {selected.size} emails ({formatBytes(selectedSize)})
              to your Gmail Trash. You can recover them within 30 days.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete Emails
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
