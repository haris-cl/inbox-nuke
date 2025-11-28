"use client"

import { useState } from "react"
import useSWR from "swr"
import { Trash2, Loader2, Download, AlertCircle, CheckCircle2, HardDrive } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
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

interface LargeEmailsResponse {
  emails: LargeEmail[]
  total_count: number
  total_size_bytes: number
  total_size_mb: number
}

export default function AttachmentsPage() {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [isDeleting, setIsDeleting] = useState(false)
  const [minSizeMb, setMinSizeMb] = useState(5)
  const [olderThanDays, setOlderThanDays] = useState(365)

  const { data, error, isLoading, mutate } = useSWR<LargeEmailsResponse>(
    `/api/attachments/large?min_size_mb=${minSizeMb}&older_than_days=${olderThanDays}`,
    () => api.getLargeAttachments({ min_size_mb: minSizeMb, older_than_days: olderThanDays })
  )

  const handleSelectAll = () => {
    if (data && selectedIds.size === data.emails.length) {
      setSelectedIds(new Set())
    } else if (data) {
      setSelectedIds(new Set(data.emails.map((e) => e.message_id)))
    }
  }

  const handleToggleSelect = (messageId: string) => {
    const newSelected = new Set(selectedIds)
    if (newSelected.has(messageId)) {
      newSelected.delete(messageId)
    } else {
      newSelected.add(messageId)
    }
    setSelectedIds(newSelected)
  }

  const handleDeleteSelected = async () => {
    if (selectedIds.size === 0) return

    const selectedEmails = data?.emails.filter((e) => selectedIds.has(e.message_id)) || []
    const totalSizeMb = selectedEmails.reduce((sum, e) => sum + e.size_mb, 0)

    if (
      !confirm(
        `Are you sure you want to delete ${selectedIds.size} email(s)? This will free up approximately ${totalSizeMb.toFixed(2)} MB. Emails will be moved to trash and can be recovered for 30 days.`
      )
    ) {
      return
    }

    try {
      setIsDeleting(true)
      await api.cleanupAttachments(Array.from(selectedIds))
      setSelectedIds(new Set())
      mutate()
    } catch (error) {
      console.error("Failed to delete emails:", error)
      alert("Failed to delete emails. Please try again.")
    } finally {
      setIsDeleting(false)
    }
  }

  const formatBytes = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
  }

  const formatDate = (dateString: string): string => {
    try {
      return new Date(dateString).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    } catch {
      return dateString
    }
  }

  const selectedSizeMb = data?.emails
    .filter((e) => selectedIds.has(e.message_id))
    .reduce((sum, e) => sum + e.size_mb, 0) || 0

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Large Attachments</h1>
        <p className="text-muted-foreground mt-1">
          Find and remove large emails to free up storage space
        </p>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Search Filters</CardTitle>
          <CardDescription>
            Customize search criteria to find large emails
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                Minimum Size (MB)
              </label>
              <input
                type="number"
                min="1"
                max="100"
                value={minSizeMb}
                onChange={(e) => setMinSizeMb(Number(e.target.value))}
                className="w-full px-4 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">
                Older Than (Days)
              </label>
              <input
                type="number"
                min="0"
                max="3650"
                value={olderThanDays}
                onChange={(e) => setOlderThanDays(Number(e.target.value))}
                className="w-full px-4 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
          </div>
          <Button onClick={() => mutate()} size="sm">
            Apply Filters
          </Button>
        </CardContent>
      </Card>

      {/* Summary Stats */}
      {data && data.emails.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <HardDrive className="h-8 w-8 text-primary" />
                <div>
                  <p className="text-2xl font-bold">{data.total_count}</p>
                  <p className="text-xs text-muted-foreground">Large Emails</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <Download className="h-8 w-8 text-primary" />
                <div>
                  <p className="text-2xl font-bold">{data.total_size_mb.toFixed(1)} MB</p>
                  <p className="text-xs text-muted-foreground">Total Size</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-8 w-8 text-primary" />
                <div>
                  <p className="text-2xl font-bold">{selectedIds.size}</p>
                  <p className="text-xs text-muted-foreground">
                    Selected ({selectedSizeMb.toFixed(1)} MB)
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Email List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Large Emails</CardTitle>
              <CardDescription>
                Select emails to delete and free up space
              </CardDescription>
            </div>
            {data && data.emails.length > 0 && (
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSelectAll}
                >
                  {selectedIds.size === data.emails.length ? "Deselect All" : "Select All"}
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleDeleteSelected}
                  disabled={selectedIds.size === 0 || isDeleting}
                >
                  {isDeleting ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <Trash2 className="h-4 w-4 mr-2" />
                  )}
                  Delete Selected
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          )}

          {error && (
            <div className="flex items-center gap-3 p-4 rounded-lg border border-destructive/50 bg-destructive/10">
              <AlertCircle className="h-5 w-5 text-destructive" />
              <p className="text-sm text-destructive">
                Failed to load large emails. Please try again.
              </p>
            </div>
          )}

          {data && data.emails.length === 0 && (
            <div className="text-center py-8">
              <HardDrive className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">
                No large emails found matching your criteria.
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                Try adjusting the filters above.
              </p>
            </div>
          )}

          {data && data.emails.length > 0 && (
            <div className="space-y-2">
              {data.emails.map((email) => (
                <div
                  key={email.message_id}
                  className={`flex items-start gap-3 p-4 rounded-lg border transition-colors ${
                    selectedIds.has(email.message_id)
                      ? "bg-accent border-primary"
                      : "bg-card hover:bg-accent/50"
                  }`}
                >
                  <Checkbox
                    checked={selectedIds.has(email.message_id)}
                    onCheckedChange={() => handleToggleSelect(email.message_id)}
                    className="mt-1"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-sm truncate">
                          {email.subject}
                        </h3>
                        <p className="text-xs text-muted-foreground mt-1">
                          From: {email.from_name || email.from_email}
                        </p>
                      </div>
                      <Badge variant="secondary" className="shrink-0">
                        {email.size_mb.toFixed(1)} MB
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">
                      {formatDate(email.date)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
