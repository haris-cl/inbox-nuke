"use client"

import { useState } from "react"
import useSWR from "swr"
import { Newspaper, Mail, Loader2, CheckCircle, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { StatCard } from "@/components/stat-card"
import { SubscriptionCard } from "@/components/subscription-card"
import { api, Subscription } from "@/lib/api"

export default function SubscriptionsPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [isBulkUnsubscribing, setIsBulkUnsubscribing] = useState(false)

  // Fetch subscriptions
  const { data: subscriptions, mutate } = useSWR<Subscription[]>(
    "/api/subscriptions",
    () => api.getSubscriptions()
  )

  const handleUnsubscribe = async (id: number) => {
    await api.unsubscribe(id)
    mutate()
  }

  const handleCleanup = async (id: number) => {
    await api.cleanupSubscription(id)
    mutate()
  }

  const handleBulkUnsubscribe = async () => {
    if (selectedIds.length === 0) {
      alert("Please select subscriptions to unsubscribe from.")
      return
    }

    if (!confirm(`Unsubscribe from ${selectedIds.length} subscriptions?`)) {
      return
    }

    try {
      setIsBulkUnsubscribing(true)
      const result = await api.bulkUnsubscribe(selectedIds)
      alert(`Successfully unsubscribed from ${result.success_count} subscriptions!`)
      setSelectedIds([])
      mutate()
    } catch (error) {
      console.error("Failed to bulk unsubscribe:", error)
      alert("Failed to unsubscribe. Please try again.")
    } finally {
      setIsBulkUnsubscribing(false)
    }
  }

  const handleToggleSelect = (id: number) => {
    setSelectedIds(prev =>
      prev.includes(id)
        ? prev.filter(i => i !== id)
        : [...prev, id]
    )
  }

  const handleSelectAll = () => {
    if (!filteredSubscriptions) return
    const activeIds = filteredSubscriptions
      .filter(s => !s.is_unsubscribed)
      .map(s => s.id)
    setSelectedIds(activeIds)
  }

  const handleClearSelection = () => {
    setSelectedIds([])
  }

  // Filter subscriptions by search query
  const filteredSubscriptions = subscriptions?.filter(s =>
    s.sender_email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.sender_name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Calculate stats
  const totalSubscriptions = subscriptions?.length || 0
  const unsubscribedCount = subscriptions?.filter(s => s.is_unsubscribed).length || 0
  const activeCount = totalSubscriptions - unsubscribedCount
  const totalEmails = subscriptions?.reduce((sum, s) => sum + s.email_count, 0) || 0

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="space-y-2">
        <h1 className="text-5xl font-black tracking-tight gradient-text">Subscriptions</h1>
        <p className="text-muted-foreground text-lg">
          Manage your email subscriptions and bulk unsubscribe
        </p>
      </div>

      {/* Stats */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 animate-fade-in-up animate-delay-100">
        <StatCard
          icon={Newspaper}
          label="Total Subscriptions"
          value={totalSubscriptions}
          variant="default"
        />
        <StatCard
          icon={Mail}
          label="Active"
          value={activeCount}
          variant="warning"
        />
        <StatCard
          icon={CheckCircle}
          label="Unsubscribed"
          value={unsubscribedCount}
          variant="success"
        />
        <StatCard
          icon={Trash2}
          label="Total Emails"
          value={totalEmails}
          variant="destructive"
        />
      </div>

      {/* Bulk Actions */}
      {subscriptions && subscriptions.length > 0 && (
        <Card className="animate-fade-in-up animate-delay-200">
          <CardHeader>
            <CardTitle>Bulk Actions</CardTitle>
            <CardDescription>
              Select multiple subscriptions to unsubscribe at once
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2 flex-wrap">
              <Button
                variant="outline"
                onClick={handleSelectAll}
                disabled={isBulkUnsubscribing}
              >
                Select All Active
              </Button>
              <Button
                variant="outline"
                onClick={handleClearSelection}
                disabled={isBulkUnsubscribing || selectedIds.length === 0}
              >
                Clear Selection ({selectedIds.length})
              </Button>
              <Button
                onClick={handleBulkUnsubscribe}
                disabled={isBulkUnsubscribing || selectedIds.length === 0}
                className="flex-1 min-w-[200px]"
              >
                {isBulkUnsubscribing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Unsubscribing...
                  </>
                ) : (
                  <>
                    <Mail className="mr-2 h-4 w-4" />
                    Unsubscribe Selected ({selectedIds.length})
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search */}
      {subscriptions && subscriptions.length > 0 && (
        <Card className="animate-fade-in-up animate-delay-300">
          <CardContent className="p-4">
            <Input
              placeholder="Search subscriptions by sender..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </CardContent>
        </Card>
      )}

      {/* Subscriptions Grid */}
      {filteredSubscriptions && filteredSubscriptions.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 animate-fade-in-up animate-delay-400">
          {filteredSubscriptions.map((subscription) => (
            <SubscriptionCard
              key={subscription.id}
              subscription={subscription}
              onUnsubscribe={handleUnsubscribe}
              onCleanup={handleCleanup}
              isSelected={selectedIds.includes(subscription.id)}
              onToggleSelect={!subscription.is_unsubscribed ? handleToggleSelect : undefined}
            />
          ))}
        </div>
      ) : subscriptions && subscriptions.length > 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <p className="text-muted-foreground">
              No results match your search. Try a different query.
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card className="animate-fade-in-up animate-delay-300">
          <CardContent className="p-8 text-center space-y-4">
            <Newspaper className="w-12 h-12 mx-auto text-muted-foreground" />
            <div>
              <p className="text-lg font-semibold">No Subscriptions Found</p>
              <p className="text-muted-foreground">
                Run a cleanup to discover your email subscriptions
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
