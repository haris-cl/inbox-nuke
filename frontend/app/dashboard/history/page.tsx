"use client"

import * as React from "react"
import useSWR from "swr"
import { History, Inbox } from "lucide-react"
import { RunHistoryCard } from "@/components/run-history-card"
import { Button } from "@/components/ui/button"
import { Select, SelectOption } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { api, RunListResponse } from "@/lib/api"

const ITEMS_PER_PAGE = 10

const statusOptions: SelectOption[] = [
  { value: "all", label: "All Status" },
  { value: "completed", label: "Completed" },
  { value: "failed", label: "Failed" },
  { value: "running", label: "Running" },
  { value: "paused", label: "Paused" },
]

export default function HistoryPage() {
  const [page, setPage] = React.useState(0)
  const [statusFilter, setStatusFilter] = React.useState("all")

  const offset = page * ITEMS_PER_PAGE

  // Fetch runs with filters
  const { data, error, isLoading } = useSWR<RunListResponse>(
    ["/api/runs", offset, statusFilter],
    () => api.getRuns({
      limit: ITEMS_PER_PAGE,
      offset,
      status: statusFilter === "all" ? undefined : statusFilter,
    }),
    {
      refreshInterval: 5000, // Refresh every 5 seconds
    }
  )

  const runs = data?.runs || []
  const total = data?.total || 0
  const totalPages = Math.ceil(total / ITEMS_PER_PAGE)
  const hasNextPage = page < totalPages - 1
  const hasPrevPage = page > 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Run History</h1>
        <p className="text-muted-foreground mt-1">
          View all cleanup runs and their results
        </p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <label htmlFor="status-filter" className="text-sm font-medium">
            Status:
          </label>
          <Select
            id="status-filter"
            options={statusOptions}
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value)
              setPage(0) // Reset to first page when filter changes
            }}
            className="w-[180px]"
          />
        </div>
        {total > 0 && (
          <p className="text-sm text-muted-foreground">
            Showing {offset + 1}-{Math.min(offset + ITEMS_PER_PAGE, total)} of {total} runs
          </p>
        )}
      </div>

      {/* Error State */}
      {error && (
        <Alert variant="destructive">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>
            Failed to load run history. Please try again later.
          </AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-48 w-full" />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && runs.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="rounded-full bg-muted p-6 mb-4">
            <Inbox className="h-12 w-12 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold mb-2">No runs found</h3>
          <p className="text-sm text-muted-foreground max-w-sm">
            {statusFilter === "all"
              ? "You haven't started any cleanup runs yet. Go to the dashboard to start your first run."
              : `No ${statusFilter} runs found. Try changing the filter.`}
          </p>
        </div>
      )}

      {/* Runs List */}
      {!isLoading && !error && runs.length > 0 && (
        <div className="space-y-4">
          {runs.map((run) => (
            <RunHistoryCard key={run.id} run={run} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {!isLoading && !error && totalPages > 1 && (
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            onClick={() => setPage(page - 1)}
            disabled={!hasPrevPage}
          >
            Previous
          </Button>
          <div className="text-sm text-muted-foreground">
            Page {page + 1} of {totalPages}
          </div>
          <Button
            variant="outline"
            onClick={() => setPage(page + 1)}
            disabled={!hasNextPage}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  )
}
