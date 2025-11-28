"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import useSWR from "swr"
import { Trash2, Plus, Loader2, CheckCircle2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { api, WhitelistEntry, AuthStatus } from "@/lib/api"

export default function SettingsPage() {
  const router = useRouter()
  const [newDomain, setNewDomain] = useState("")
  const [isAdding, setIsAdding] = useState(false)
  const [removingDomain, setRemovingDomain] = useState<string | null>(null)
  const [isDisconnecting, setIsDisconnecting] = useState(false)

  const { data: whitelist, mutate: mutateWhitelist } = useSWR<WhitelistEntry[]>(
    "/api/whitelist",
    () => api.getWhitelist()
  )

  const { data: authStatus } = useSWR<AuthStatus>(
    "/api/auth/status",
    () => api.getAuthStatus()
  )

  const handleAddDomain = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newDomain.trim()) return

    try {
      setIsAdding(true)
      await api.addToWhitelist(newDomain.trim())
      setNewDomain("")
      mutateWhitelist()
    } catch (error) {
      console.error("Failed to add domain:", error)
      alert("Failed to add domain to whitelist. Please try again.")
    } finally {
      setIsAdding(false)
    }
  }

  const handleRemoveDomain = async (email: string) => {
    if (!confirm(`Are you sure you want to remove ${email} from the whitelist?`)) {
      return
    }

    try {
      setRemovingDomain(email)
      await api.removeFromWhitelist(email)
      mutateWhitelist()
    } catch (error) {
      console.error("Failed to remove domain:", error)
      alert("Failed to remove domain from whitelist. Please try again.")
    } finally {
      setRemovingDomain(null)
    }
  }

  const handleDisconnect = async () => {
    if (!confirm("Are you sure you want to disconnect your Gmail account? This will log you out.")) {
      return
    }

    try {
      setIsDisconnecting(true)
      await api.disconnect()
      router.push("/")
    } catch (error) {
      console.error("Failed to disconnect:", error)
      alert("Failed to disconnect. Please try again.")
    } finally {
      setIsDisconnecting(false)
    }
  }

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Manage your whitelist and Gmail connection
        </p>
      </div>

      {/* Whitelist Management */}
      <Card>
        <CardHeader>
          <CardTitle>Whitelist Management</CardTitle>
          <CardDescription>
            Emails from these domains will never be deleted or filtered
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Add Domain Form */}
          <form onSubmit={handleAddDomain} className="flex gap-2">
            <input
              type="text"
              placeholder="Enter email or domain (e.g., important@example.com)"
              value={newDomain}
              onChange={(e) => setNewDomain(e.target.value)}
              className="flex-1 px-4 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <Button type="submit" disabled={isAdding || !newDomain.trim()}>
              {isAdding ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Plus className="h-4 w-4 mr-2" />
              )}
              Add
            </Button>
          </form>

          {/* Whitelist Items */}
          <div className="space-y-2">
            {!whitelist ? (
              <div className="flex justify-center py-4">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : whitelist.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                No domains in whitelist. Add domains above to protect them from cleanup.
              </p>
            ) : (
              whitelist.map((entry) => (
                <div
                  key={entry.email}
                  className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">{entry.email}</span>
                      {entry.name && (
                        <span className="text-xs text-muted-foreground">({entry.name})</span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Added {formatDate(entry.added_at)}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemoveDomain(entry.email)}
                    disabled={removingDomain === entry.email}
                  >
                    {removingDomain === entry.email ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="h-4 w-4 text-destructive" />
                    )}
                  </Button>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Gmail Connection */}
      <Card>
        <CardHeader>
          <CardTitle>Gmail Connection</CardTitle>
          <CardDescription>
            Manage your Gmail account connection
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {authStatus?.connected && (
            <div className="flex items-center gap-3 p-4 rounded-lg border bg-success/10">
              <CheckCircle2 className="h-5 w-5 text-success" />
              <div className="flex-1">
                <p className="font-medium text-sm">Connected</p>
                <p className="text-sm text-muted-foreground">{authStatus.email}</p>
              </div>
            </div>
          )}

          <Button
            variant="destructive"
            onClick={handleDisconnect}
            disabled={isDisconnecting}
            className="w-full sm:w-auto"
          >
            {isDisconnecting ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Trash2 className="h-4 w-4 mr-2" />
            )}
            Disconnect Gmail
          </Button>
          <p className="text-xs text-muted-foreground">
            Disconnecting will revoke access to your Gmail account and log you out.
          </p>
        </CardContent>
      </Card>

      {/* Aggressiveness Setting (Placeholder) */}
      <Card>
        <CardHeader>
          <CardTitle>Cleanup Aggressiveness</CardTitle>
          <CardDescription>
            Control how aggressive the AI agent should be when cleaning (Coming Soon)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground">Conservative</span>
              <input
                type="range"
                min="1"
                max="5"
                defaultValue="3"
                disabled
                className="flex-1 opacity-50"
              />
              <span className="text-sm text-muted-foreground">Aggressive</span>
            </div>
            <Badge variant="secondary">Coming Soon</Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
