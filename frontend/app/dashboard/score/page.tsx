"use client"

import { useState, useEffect } from "react"
import useSWR from "swr"
import { Play, Loader2, Trash2, Shield, AlertCircle, BarChart3, TrendingDown, TrendingUp, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { StatCard } from "@/components/stat-card"
import { SenderRow } from "@/components/sender-row"
import { EmailScoreCard } from "@/components/email-score-card"
import { api, ScoringProgress, ScoringStats, SenderProfile, EmailScore } from "@/lib/api"
import { cn } from "@/lib/utils"

export default function ScorePage() {
  const [isScanning, setIsScanning] = useState(false)
  const [selectedSender, setSelectedSender] = useState<string | undefined>()
  const [selectedClassification, setSelectedClassification] = useState<string | undefined>()
  const [activeTab, setActiveTab] = useState("senders")

  // Fetch progress
  const { data: progress, mutate: mutateProgress } = useSWR<ScoringProgress>(
    "/api/scoring/progress",
    () => api.getScoringProgress(),
    {
      refreshInterval: isScanning ? 2000 : 0,
    }
  )

  // Fetch stats
  const { data: stats, mutate: mutateStats } = useSWR<ScoringStats>(
    "/api/scoring/stats",
    () => api.getScoringStats()
  )

  // Fetch senders
  const { data: sendersData, mutate: mutateSenders } = useSWR<{ senders: SenderProfile[]; total: number }>(
    selectedClassification ? `/api/scoring/senders?classification=${selectedClassification}` : "/api/scoring/senders",
    () => api.getSenderProfiles({ classification: selectedClassification, limit: 50 })
  )

  // Fetch emails
  const { data: emailsData, mutate: mutateEmails } = useSWR<{ emails: EmailScore[]; total: number }>(
    selectedSender || selectedClassification
      ? `/api/scoring/emails?sender=${selectedSender || ""}&classification=${selectedClassification || ""}`
      : "/api/scoring/emails",
    () => api.getScoredEmails({ sender: selectedSender, classification: selectedClassification, limit: 50 })
  )

  // Update scanning state based on progress
  useEffect(() => {
    if (progress?.status === "running") {
      setIsScanning(true)
    } else if (progress?.status === "completed" || progress?.status === "failed") {
      setIsScanning(false)
      mutateStats()
      mutateSenders()
      mutateEmails()
    }
  }, [progress?.status])

  const handleStartScan = async (rescan: boolean = false) => {
    try {
      setIsScanning(true)
      // Scan up to 50,000 emails for full inbox cleanup
      await api.startScoring(50000, rescan)
      mutateProgress()
    } catch (error) {
      console.error("Failed to start scoring:", error)
      alert("Failed to start scoring. Please try again.")
      setIsScanning(false)
    }
  }

  const handleViewEmails = (senderEmail: string) => {
    setSelectedSender(senderEmail)
    setActiveTab("emails")
  }

  const handleOverrideEmail = async (messageId: string, classification: string) => {
    // First, get the current email to know the original classification
    const email = emailsData?.emails.find(e => e.message_id === messageId)
    const originalClassification = email?.classification || "UNCERTAIN"

    // Override the score
    await api.overrideEmailScore(messageId, classification)

    // Submit feedback to trigger learning (only if classification changed)
    if (originalClassification !== classification) {
      try {
        await api.submitFeedback("email", messageId, classification)
      } catch (error) {
        console.error("Failed to submit feedback for learning:", error)
        // Don't fail the override if feedback fails
      }
    }

    mutateEmails()
    mutateStats()
  }

  const handleBulkDelete = async (classification: string) => {
    if (!confirm(`Are you sure you want to delete all emails marked as ${classification}?`)) {
      return
    }

    try {
      const result = await api.executeScoreCleanup(classification)
      alert(`Successfully deleted ${result.deleted_count} emails`)
      mutateStats()
      mutateEmails()
    } catch (error) {
      console.error("Failed to execute cleanup:", error)
      alert("Failed to delete emails. Please try again.")
    }
  }

  const progressPercent = progress?.total_emails
    ? Math.round((progress.scored_emails / progress.total_emails) * 100)
    : 0

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-5xl font-black tracking-tight gradient-text">Review & Score</h1>
        <p className="text-muted-foreground text-lg">
          Scan your inbox, review email scores, and decide what to clean up
        </p>
      </div>

      {/* Workflow Guide */}
      <Card className="border-2 border-primary/20 bg-primary/5 animate-fade-in-up">
        <CardContent className="py-4">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">1</div>
            <div className="flex-1 space-y-1">
              <p className="font-semibold">Scan your inbox</p>
              <p className="text-sm text-muted-foreground">We&apos;ll analyze up to 50,000 emails and score each one based on multiple signals</p>
            </div>
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">2</div>
            <div className="flex-1 space-y-1">
              <p className="font-semibold">Review classifications</p>
              <p className="text-sm text-muted-foreground">Each email is marked KEEP, DELETE, or UNCERTAIN. Override any you disagree with.</p>
            </div>
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">3</div>
            <div className="flex-1 space-y-1">
              <p className="font-semibold">Clean up</p>
              <p className="text-sm text-muted-foreground">Bulk delete emails marked DELETE, or manage senders individually</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Scan Control Panel */}
      <Card className="card-glow border-2 border-border/50 backdrop-blur-sm bg-card/50 animate-fade-in-up animate-delay-100">
        <CardHeader>
          <CardTitle>Scan Control</CardTitle>
          <CardDescription>
            {progress?.status === "running"
              ? `Scanning emails... ${progress.current_sender || ""}`
              : progress?.status === "completed"
              ? `Scan completed - ${stats?.total_scored || 0} emails scored`
              : "Start a new scan to score your emails (up to 50,000)"}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isScanning && progress && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Progress</span>
                <span className="font-mono font-bold tabular-nums">
                  {progress.scored_emails.toLocaleString()} / {progress.total_emails.toLocaleString()}
                </span>
              </div>
              <Progress value={progressPercent} className="h-3" />
            </div>
          )}

          <div className="flex gap-2">
            <Button
              onClick={() => handleStartScan(false)}
              disabled={isScanning}
              size="lg"
              className="flex-1"
            >
              {isScanning ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Scanning...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  {stats?.total_scored ? "Scan New Emails" : "Start Full Scan"}
                </>
              )}
            </Button>
            {stats?.total_scored ? (
              <Button
                onClick={() => handleStartScan(true)}
                disabled={isScanning}
                size="lg"
                variant="outline"
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Rescan All
              </Button>
            ) : null}
          </div>
        </CardContent>
      </Card>

      {/* Stats Overview */}
      {stats && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 animate-fade-in-up animate-delay-200">
          <StatCard
            icon={Shield}
            label="Keep"
            value={stats.keep_count}
            variant="success"
          />
          <StatCard
            icon={Trash2}
            label="Delete"
            value={stats.delete_count}
            variant="destructive"
          />
          <StatCard
            icon={AlertCircle}
            label="Uncertain"
            value={stats.uncertain_count}
            variant="warning"
          />
          <StatCard
            icon={BarChart3}
            label="Total Scored"
            value={stats.total_scored}
            variant="default"
          />
        </div>
      )}

      {/* Score Distribution */}
      {stats && stats.score_distribution && (
        <Card className="card-glow border-2 border-border/50 backdrop-blur-sm bg-card/50 animate-fade-in-up animate-delay-300">
          <CardHeader>
            <CardTitle>Score Distribution</CardTitle>
            <CardDescription>Distribution of scores across your emails</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(stats.score_distribution).map(([range, count]) => {
                const total = stats.total_scored
                const percentage = total > 0 ? Math.round((count / total) * 100) : 0
                const isLow = range.includes("0-") || range.includes("10-") || range.includes("20-")
                const isHigh = range.includes("70-") || range.includes("80-") || range.includes("90-")

                return (
                  <div key={range} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="font-mono font-semibold">{range}</span>
                      <span className="font-mono tabular-nums text-muted-foreground">
                        {count} ({percentage}%)
                      </span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className={cn(
                          "h-full transition-all duration-500",
                          isLow && "bg-emerald-400/50",
                          !isLow && !isHigh && "bg-amber-400/50",
                          isHigh && "bg-rose-400/50"
                        )}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Top Senders Insight */}
      {stats && ((stats.top_delete_senders?.length ?? 0) > 0 || (stats.top_keep_senders?.length ?? 0) > 0) && (
        <div className="grid gap-6 md:grid-cols-2 animate-fade-in-up animate-delay-400">
          {/* Top Delete Senders */}
          {(stats.top_delete_senders?.length ?? 0) > 0 && (
            <Card className="card-glow border-2 border-rose-400/20 backdrop-blur-sm bg-card/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-rose-400">
                  <TrendingDown className="w-5 h-5" />
                  Top Delete Candidates
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {(stats.top_delete_senders || []).slice(0, 5).map((sender) => (
                  <div
                    key={sender.email}
                    className="flex items-center justify-between p-2 rounded-lg bg-rose-400/5 border border-rose-400/10"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-semibold truncate">{sender.email}</div>
                      <div className="text-xs text-muted-foreground">
                        {sender.count} emails
                      </div>
                    </div>
                    <div className="text-lg font-black font-mono text-rose-400 ml-2">
                      {sender.score}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Top Keep Senders */}
          {(stats.top_keep_senders?.length ?? 0) > 0 && (
            <Card className="card-glow border-2 border-emerald-400/20 backdrop-blur-sm bg-card/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-emerald-400">
                  <TrendingUp className="w-5 h-5" />
                  Top Keep Senders
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {(stats.top_keep_senders || []).slice(0, 5).map((sender) => (
                  <div
                    key={sender.email}
                    className="flex items-center justify-between p-2 rounded-lg bg-emerald-400/5 border border-emerald-400/10"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-semibold truncate">{sender.email}</div>
                      <div className="text-xs text-muted-foreground">
                        {sender.count} emails
                      </div>
                    </div>
                    <div className="text-lg font-black font-mono text-emerald-400 ml-2">
                      {sender.score}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Tabs for Senders and Emails */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6 animate-fade-in-up animate-delay-500">
        <TabsList className="grid w-full grid-cols-2 max-w-md">
          <TabsTrigger value="senders">By Sender</TabsTrigger>
          <TabsTrigger value="emails">By Email</TabsTrigger>
        </TabsList>

        {/* Senders Tab */}
        <TabsContent value="senders" className="space-y-4">
          {/* Filter Buttons */}
          <div className="flex gap-2 flex-wrap">
            <Button
              variant={!selectedClassification ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedClassification(undefined)}
            >
              All
            </Button>
            <Button
              variant={selectedClassification === "KEEP" ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedClassification("KEEP")}
              className={selectedClassification === "KEEP" ? "bg-emerald-400 hover:bg-emerald-400/90" : ""}
            >
              Keep
            </Button>
            <Button
              variant={selectedClassification === "DELETE" ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedClassification("DELETE")}
              className={selectedClassification === "DELETE" ? "bg-rose-400 hover:bg-rose-400/90" : ""}
            >
              Delete
            </Button>
            <Button
              variant={selectedClassification === "UNCERTAIN" ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedClassification("UNCERTAIN")}
              className={selectedClassification === "UNCERTAIN" ? "bg-amber-400 hover:bg-amber-400/90" : ""}
            >
              Uncertain
            </Button>
          </div>

          {/* Sender List */}
          <div className="space-y-4">
            {(sendersData?.senders || []).map((sender) => (
              <SenderRow
                key={sender.id}
                sender={sender}
                onViewEmails={handleViewEmails}
              />
            ))}
            {(sendersData?.senders?.length ?? 0) === 0 && (
              <Card className="border-2 border-dashed border-border/50">
                <CardContent className="flex items-center justify-center py-12">
                  <p className="text-muted-foreground">No senders found. Start a scan to see results.</p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Emails Tab */}
        <TabsContent value="emails" className="space-y-4">
          {/* Filter Buttons */}
          <div className="flex gap-2 flex-wrap">
            <Button
              variant={!selectedClassification ? "default" : "outline"}
              size="sm"
              onClick={() => {
                setSelectedClassification(undefined)
                setSelectedSender(undefined)
              }}
            >
              All
            </Button>
            <Button
              variant={selectedClassification === "KEEP" ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedClassification("KEEP")}
              className={selectedClassification === "KEEP" ? "bg-emerald-400 hover:bg-emerald-400/90" : ""}
            >
              Keep
            </Button>
            <Button
              variant={selectedClassification === "DELETE" ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedClassification("DELETE")}
              className={selectedClassification === "DELETE" ? "bg-rose-400 hover:bg-rose-400/90" : ""}
            >
              Delete
            </Button>
            <Button
              variant={selectedClassification === "UNCERTAIN" ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedClassification("UNCERTAIN")}
              className={selectedClassification === "UNCERTAIN" ? "bg-amber-400 hover:bg-amber-400/90" : ""}
            >
              Uncertain
            </Button>
          </div>

          {/* Bulk Actions */}
          {selectedClassification === "DELETE" && emailsData && emailsData.emails.length > 0 && (
            <Card className="border-2 border-rose-400/20 bg-rose-400/5">
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-sm">Bulk Delete</div>
                    <div className="text-xs text-muted-foreground">
                      Delete all {emailsData.total} emails marked for deletion
                    </div>
                  </div>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleBulkDelete("DELETE")}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete All
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Email List */}
          <div className="grid gap-4 md:grid-cols-2">
            {(emailsData?.emails || []).map((email) => (
              <EmailScoreCard
                key={email.id}
                email={email}
                onOverride={handleOverrideEmail}
              />
            ))}
          </div>
          {(emailsData?.emails?.length ?? 0) === 0 && (
            <Card className="border-2 border-dashed border-border/50">
              <CardContent className="flex items-center justify-center py-12">
                <p className="text-muted-foreground">No emails found. Start a scan to see results.</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
