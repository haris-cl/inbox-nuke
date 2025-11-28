"use client"

import { useState } from "react"
import { Play, Pause, RotateCcw, X, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

interface ControlPanelProps {
  status: "idle" | "pending" | "running" | "paused" | "completed" | "failed" | "cancelled"
  onStart: () => void
  onPause: () => void
  onResume: () => void
  onCancel: () => void
  disabled?: boolean
}

export function ControlPanel({
  status,
  onStart,
  onPause,
  onResume,
  onCancel,
  disabled = false,
}: ControlPanelProps) {
  const [showCancelDialog, setShowCancelDialog] = useState(false)

  const handleCancel = () => {
    setShowCancelDialog(false)
    onCancel()
  }

  const statusMessages = {
    idle: "Ready to start cleaning your inbox",
    pending: "Cleanup is starting...",
    running: "Cleanup is in progress",
    paused: "Cleanup is paused",
    completed: "Cleanup completed successfully",
    failed: "Cleanup failed",
    cancelled: "Cleanup was cancelled",
  }

  const statusVariants = {
    idle: "default",
    pending: "default",
    running: "default",
    paused: "warning",
    completed: "success",
    failed: "destructive",
    cancelled: "secondary",
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Control Panel</CardTitle>
          <CardDescription>
            {statusMessages[status]}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 flex-wrap">
            {(status === "idle" || status === "pending") && (
              <Button
                onClick={onStart}
                disabled={disabled || status === "pending"}
                size="lg"
                className="flex-1 min-w-[200px]"
              >
                {status === "pending" ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Starting...
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Start Cleanup
                  </>
                )}
              </Button>
            )}

            {status === "running" && (
              <>
                <Button
                  onClick={onPause}
                  disabled={disabled}
                  variant="secondary"
                  size="lg"
                  className="flex-1"
                >
                  <Pause className="mr-2 h-4 w-4" />
                  Pause
                </Button>
                <Button
                  onClick={() => setShowCancelDialog(true)}
                  disabled={disabled}
                  variant="destructive"
                  size="lg"
                >
                  <X className="mr-2 h-4 w-4" />
                  Cancel
                </Button>
              </>
            )}

            {status === "paused" && (
              <>
                <Button
                  onClick={onResume}
                  disabled={disabled}
                  size="lg"
                  className="flex-1"
                >
                  <RotateCcw className="mr-2 h-4 w-4" />
                  Resume
                </Button>
                <Button
                  onClick={() => setShowCancelDialog(true)}
                  disabled={disabled}
                  variant="destructive"
                  size="lg"
                >
                  <X className="mr-2 h-4 w-4" />
                  Cancel
                </Button>
              </>
            )}

            {(status === "completed" || status === "failed" || status === "cancelled") && (
              <Button
                onClick={onStart}
                disabled={disabled}
                size="lg"
                className="flex-1 min-w-[200px]"
              >
                <Play className="mr-2 h-4 w-4" />
                Start New Cleanup
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <Dialog open={showCancelDialog} onOpenChange={setShowCancelDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Cancel Cleanup?</DialogTitle>
            <DialogDescription>
              Are you sure you want to cancel the current cleanup run? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCancelDialog(false)}
            >
              Keep Running
            </Button>
            <Button
              variant="destructive"
              onClick={handleCancel}
            >
              Cancel Cleanup
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
