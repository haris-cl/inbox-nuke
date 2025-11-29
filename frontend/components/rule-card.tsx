"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { RetentionRule } from "@/lib/api"
import { cn } from "@/lib/utils"
import { Shield, Trash2, AlertCircle, Check, Loader2 } from "lucide-react"

interface RuleCardProps {
  rule: RetentionRule
  onDelete?: (index: number) => Promise<void>
}

const actionConfig = {
  KEEP: {
    label: "Keep",
    icon: Check,
    variant: "default" as const,
    color: "text-success",
    bg: "bg-success/10",
  },
  DELETE: {
    label: "Delete",
    icon: Trash2,
    variant: "destructive" as const,
    color: "text-destructive",
    bg: "bg-destructive/10",
  },
  REVIEW: {
    label: "Review",
    icon: AlertCircle,
    variant: "warning" as const,
    color: "text-warning",
    bg: "bg-warning/10",
  },
}

const ruleTypeLabels: Record<string, string> = {
  sender_domain: "Sender Domain",
  sender_pattern: "Sender Pattern",
  subject_pattern: "Subject Pattern",
  keyword: "Keyword",
  category: "Category",
}

export function RuleCard({ rule, onDelete }: RuleCardProps) {
  const [isDeleting, setIsDeleting] = useState(false)
  const config = actionConfig[rule.action as keyof typeof actionConfig]
  const Icon = config.icon

  const handleDelete = async () => {
    if (!onDelete || rule.enabled) return
    if (!confirm("Delete this rule? This action cannot be undone.")) return

    try {
      setIsDeleting(true)
      await onDelete(rule.index)
    } catch (error) {
      console.error("Failed to delete rule:", error)
      alert("Failed to delete rule. Please try again.")
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <Card className="card-glow hover:scale-[1.01] transition-all duration-300">
      <CardContent className="p-4">
        <div className="space-y-3">
          {/* Header */}
          <div className="flex items-start gap-3">
            <div className={cn("mt-1 p-2 rounded-lg", config.bg)}>
              <Icon className={cn("w-4 h-4", config.color)} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <Badge variant={config.variant} className="text-xs">
                  {config.label}
                </Badge>
                <Badge variant="outline" className="text-xs">
                  {ruleTypeLabels[rule.rule_type] || rule.rule_type}
                </Badge>
                {rule.enabled && (
                  <Badge variant="secondary" className="text-xs gap-1">
                    <Shield className="w-3 h-3" />
                    Default
                  </Badge>
                )}
              </div>
              <p className="text-sm font-semibold font-mono break-all">
                {rule.pattern}
              </p>
              {rule.description && (
                <p className="text-xs text-muted-foreground mt-1">
                  {rule.description}
                </p>
              )}
            </div>
          </div>

          {/* Priority */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Priority:</span>
            <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary transition-all duration-500"
                style={{ width: `${Math.min(rule.priority * 10, 100)}%` }}
              />
            </div>
            <span className="text-xs font-mono text-muted-foreground">{rule.priority}</span>
          </div>

          {/* Delete Button (for custom rules only) */}
          {!rule.enabled && onDelete && (
            <div className="pt-2 border-t">
              <Button
                variant="destructive"
                size="sm"
                onClick={handleDelete}
                disabled={isDeleting}
                className="w-full"
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="mr-2 h-3 w-3" />
                    Delete Rule
                  </>
                )}
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
