"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Subscription } from "@/lib/api"
import { cn } from "@/lib/utils"
import { Mail, Trash2, CheckCircle, Loader2 } from "lucide-react"

interface SubscriptionCardProps {
  subscription: Subscription
  onUnsubscribe?: (id: number) => Promise<void>
  onCleanup?: (id: number) => Promise<void>
  isSelected?: boolean
  onToggleSelect?: (id: number) => void
}

export function SubscriptionCard({
  subscription,
  onUnsubscribe,
  onCleanup,
  isSelected,
  onToggleSelect,
}: SubscriptionCardProps) {
  const [isUnsubscribing, setIsUnsubscribing] = useState(false)
  const [isCleaning, setIsCleaning] = useState(false)

  const handleUnsubscribe = async () => {
    if (!onUnsubscribe) return
    try {
      setIsUnsubscribing(true)
      await onUnsubscribe(subscription.id)
    } catch (error) {
      console.error("Failed to unsubscribe:", error)
    } finally {
      setIsUnsubscribing(false)
    }
  }

  const handleCleanup = async () => {
    if (!onCleanup) return
    if (!confirm(`Delete all emails from ${subscription.sender_email}?`)) return

    try {
      setIsCleaning(true)
      await onCleanup(subscription.id)
    } catch (error) {
      console.error("Failed to cleanup:", error)
    } finally {
      setIsCleaning(false)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (days === 0) return "Today"
    if (days === 1) return "Yesterday"
    if (days < 7) return `${days} days ago`
    if (days < 30) return `${Math.floor(days / 7)} weeks ago`
    return date.toLocaleDateString()
  }

  return (
    <Card
      className={cn(
        "card-glow hover:scale-[1.01] transition-all duration-300",
        isSelected && "ring-2 ring-primary"
      )}
    >
      <CardContent className="p-4">
        <div className="space-y-3">
          {/* Header */}
          <div className="flex items-start gap-3">
            {onToggleSelect && (
              <input
                type="checkbox"
                checked={isSelected}
                onChange={() => onToggleSelect(subscription.id)}
                className="mt-1 w-4 h-4 rounded border-border text-primary focus:ring-primary"
              />
            )}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <Mail className="w-4 h-4 text-primary" />
                {subscription.is_unsubscribed && (
                  <Badge variant="success" className="text-xs gap-1">
                    <CheckCircle className="w-3 h-3" />
                    Unsubscribed
                  </Badge>
                )}
              </div>
              <p className="text-sm font-semibold">
                {subscription.sender_name || subscription.sender_email}
              </p>
              {subscription.sender_name && (
                <p className="text-xs text-muted-foreground truncate">
                  {subscription.sender_email}
                </p>
              )}
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-2">
            <div className="p-2 rounded-lg bg-muted/50">
              <p className="text-xs text-muted-foreground">Emails</p>
              <p className="text-lg font-black font-mono">{subscription.email_count}</p>
            </div>
            <div className="p-2 rounded-lg bg-muted/50">
              <p className="text-xs text-muted-foreground">Last Email</p>
              <p className="text-xs font-semibold mt-1">
                {formatDate(subscription.last_email_date)}
              </p>
            </div>
          </div>

          {subscription.unsubscribed_at && (
            <p className="text-xs text-muted-foreground">
              Unsubscribed {formatDate(subscription.unsubscribed_at)}
            </p>
          )}

          {/* Actions */}
          <div className="flex gap-2 pt-2 border-t">
            {!subscription.is_unsubscribed && onUnsubscribe && (
              <Button
                variant="secondary"
                size="sm"
                onClick={handleUnsubscribe}
                disabled={isUnsubscribing || isCleaning}
                className="flex-1"
              >
                {isUnsubscribing ? (
                  <>
                    <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                    Unsubscribing...
                  </>
                ) : (
                  <>
                    <Mail className="mr-2 h-3 w-3" />
                    Unsubscribe
                  </>
                )}
              </Button>
            )}
            {onCleanup && (
              <Button
                variant="destructive"
                size="sm"
                onClick={handleCleanup}
                disabled={isUnsubscribing || isCleaning}
                className="flex-1"
              >
                {isCleaning ? (
                  <>
                    <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                    Cleaning...
                  </>
                ) : (
                  <>
                    <Trash2 className="mr-2 h-3 w-3" />
                    Clean Up
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
