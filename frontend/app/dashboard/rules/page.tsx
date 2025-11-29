"use client"

import { useState } from "react"
import useSWR from "swr"
import { ListFilter, Plus, Loader2, Shield, AlertCircle, Eye } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { StatCard } from "@/components/stat-card"
import { RuleCard } from "@/components/rule-card"
import { api, RetentionRule, ClassificationSummary } from "@/lib/api"

export default function RulesPage() {
  const [showAddDialog, setShowAddDialog] = useState(false)
  const [showPreviewDialog, setShowPreviewDialog] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [isPreviewing, setIsPreviewing] = useState(false)
  const [previewData, setPreviewData] = useState<ClassificationSummary | null>(null)

  // Form state
  const [ruleType, setRuleType] = useState("sender_domain")
  const [pattern, setPattern] = useState("")
  const [action, setAction] = useState<"KEEP" | "DELETE" | "REVIEW">("KEEP")
  const [priority, setPriority] = useState("5")

  // Fetch rules
  const { data: rules, mutate } = useSWR<RetentionRule[]>(
    "/api/retention/rules",
    () => api.getRetentionRules()
  )

  const handleCreate = async () => {
    if (!pattern.trim()) {
      alert("Please enter a pattern.")
      return
    }

    try {
      setIsCreating(true)
      await api.createRetentionRule({
        rule_type: ruleType,
        pattern: pattern.trim(),
        action,
        priority: parseInt(priority),
      })
      setShowAddDialog(false)
      setPattern("")
      setRuleType("sender_domain")
      setAction("KEEP")
      setPriority("5")
      mutate()
    } catch (error) {
      console.error("Failed to create rule:", error)
      alert("Failed to create rule. Please try again.")
    } finally {
      setIsCreating(false)
    }
  }

  const handleDelete = async (index: number) => {
    await api.deleteRetentionRule(index)
    mutate()
  }

  const handlePreview = async () => {
    try {
      setIsPreviewing(true)
      const data = await api.previewCleanup()
      setPreviewData(data)
      setShowPreviewDialog(true)
    } catch (error) {
      console.error("Failed to preview cleanup:", error)
      alert("Failed to preview cleanup. Please try again.")
    } finally {
      setIsPreviewing(false)
    }
  }

  // Separate default and custom rules
  const defaultRules = rules?.filter(r => r.enabled) || []
  const customRules = rules?.filter(r => !r.enabled) || []

  // Calculate stats
  const totalRules = rules?.length || 0
  const defaultCount = defaultRules.length
  const customCount = customRules.length
  const keepRules = rules?.filter(r => r.action === "KEEP").length || 0

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="space-y-2">
        <h1 className="text-5xl font-black tracking-tight gradient-text">Retention Rules</h1>
        <p className="text-muted-foreground text-lg">
          Define rules to control which emails are kept or deleted
        </p>
      </div>

      {/* Stats */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 animate-fade-in-up animate-delay-100">
        <StatCard
          icon={ListFilter}
          label="Total Rules"
          value={totalRules}
          variant="default"
        />
        <StatCard
          icon={Shield}
          label="Default Rules"
          value={defaultCount}
          variant="success"
        />
        <StatCard
          icon={Plus}
          label="Custom Rules"
          value={customCount}
          variant="warning"
        />
        <StatCard
          icon={AlertCircle}
          label="Keep Rules"
          value={keepRules}
          variant="default"
        />
      </div>

      {/* Actions */}
      <Card className="animate-fade-in-up animate-delay-200">
        <CardHeader>
          <CardTitle>Rule Management</CardTitle>
          <CardDescription>
            Create custom rules and preview their impact before applying
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 flex-wrap">
            <Button
              onClick={() => setShowAddDialog(true)}
              size="lg"
              className="flex-1 min-w-[200px]"
            >
              <Plus className="mr-2 h-4 w-4" />
              Add Custom Rule
            </Button>
            <Button
              onClick={handlePreview}
              disabled={isPreviewing}
              variant="secondary"
              size="lg"
            >
              {isPreviewing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Previewing...
                </>
              ) : (
                <>
                  <Eye className="mr-2 h-4 w-4" />
                  Preview Cleanup Impact
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Default Rules */}
      {defaultRules.length > 0 && (
        <div className="space-y-4 animate-fade-in-up animate-delay-300">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-success" />
            <h2 className="text-2xl font-black">Default Rules</h2>
            <span className="text-sm text-muted-foreground">
              (Protected - Cannot be deleted)
            </span>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {defaultRules.map((rule) => (
              <RuleCard key={rule.index} rule={rule} />
            ))}
          </div>
        </div>
      )}

      {/* Custom Rules */}
      {customRules.length > 0 && (
        <div className="space-y-4 animate-fade-in-up animate-delay-400">
          <div className="flex items-center gap-2">
            <Plus className="w-5 h-5 text-primary" />
            <h2 className="text-2xl font-black">Custom Rules</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {customRules.map((rule) => (
              <RuleCard key={rule.index} rule={rule} onDelete={handleDelete} />
            ))}
          </div>
        </div>
      )}

      {customRules.length === 0 && (
        <Card className="animate-fade-in-up animate-delay-400">
          <CardContent className="p-8 text-center space-y-4">
            <Plus className="w-12 h-12 mx-auto text-muted-foreground" />
            <div>
              <p className="text-lg font-semibold">No Custom Rules</p>
              <p className="text-muted-foreground">
                Create custom rules to fine-tune your email retention policy
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Add Rule Dialog */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Custom Rule</DialogTitle>
            <DialogDescription>
              Create a new retention rule to control email cleanup behavior
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-semibold">Rule Type</label>
              <Select
                value={ruleType}
                onChange={(e) => setRuleType(e.target.value)}
                options={[
                  { value: "sender_domain", label: "Sender Domain" },
                  { value: "sender_pattern", label: "Sender Pattern" },
                  { value: "subject_pattern", label: "Subject Pattern" },
                  { value: "keyword", label: "Keyword" },
                  { value: "category", label: "Category" },
                ]}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold">Pattern</label>
              <Input
                placeholder="e.g., @example.com or *newsletter*"
                value={pattern}
                onChange={(e) => setPattern(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold">Action</label>
              <Select
                value={action}
                onChange={(e) => setAction(e.target.value as any)}
                options={[
                  { value: "KEEP", label: "Keep" },
                  { value: "DELETE", label: "Delete" },
                  { value: "REVIEW", label: "Review" },
                ]}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold">Priority (1-10)</label>
              <Input
                type="number"
                min="1"
                max="10"
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowAddDialog(false)}
              disabled={isCreating}
            >
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={isCreating}>
              {isCreating ? (
                <>
                  <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                  Creating...
                </>
              ) : (
                "Create Rule"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Preview Dialog */}
      <Dialog open={showPreviewDialog} onOpenChange={setShowPreviewDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Cleanup Preview</DialogTitle>
            <DialogDescription>
              Estimated impact of current retention rules
            </DialogDescription>
          </DialogHeader>
          {previewData && (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 rounded-lg bg-success/10 text-center">
                  <p className="text-2xl font-black font-mono text-success">
                    {previewData.keep_count}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">Keep</p>
                </div>
                <div className="p-4 rounded-lg bg-destructive/10 text-center">
                  <p className="text-2xl font-black font-mono text-destructive">
                    {previewData.delete_count}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">Delete</p>
                </div>
                <div className="p-4 rounded-lg bg-warning/10 text-center">
                  <p className="text-2xl font-black font-mono text-warning">
                    {previewData.review_count}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">Review</p>
                </div>
              </div>
              <div className="space-y-2">
                <p className="text-sm font-semibold">Categories</p>
                <div className="space-y-1">
                  {Object.entries(previewData.by_category).map(([cat, count]) => (
                    <div key={cat} className="flex justify-between text-sm">
                      <span className="text-muted-foreground">{cat}</span>
                      <span className="font-mono font-semibold">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button onClick={() => setShowPreviewDialog(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
