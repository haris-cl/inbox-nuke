"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Select } from "@/components/ui/select"
import { EmailClassification } from "@/lib/api"
import { cn } from "@/lib/utils"
import { Check, Trash2, AlertCircle, Loader2 } from "lucide-react"

interface ClassificationCardProps {
  classification: EmailClassification
  onOverride?: (messageId: string, newClassification: string) => Promise<void>
}

const classificationConfig = {
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

export function ClassificationCard({ classification, onOverride }: ClassificationCardProps) {
  const [isOverriding, setIsOverriding] = useState(false)
  const displayClassification = classification.user_override || classification.classification
  const config = classificationConfig[displayClassification as keyof typeof classificationConfig]
  const Icon = config.icon

  const handleOverride = async (newClassification: string) => {
    if (!onOverride || newClassification === displayClassification) return

    try {
      setIsOverriding(true)
      await onOverride(classification.message_id, newClassification)
    } catch (error) {
      console.error("Failed to override classification:", error)
    } finally {
      setIsOverriding(false)
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
              <div className="flex items-center gap-2 mb-1">
                <Badge variant={config.variant} className="text-xs">
                  {config.label}
                </Badge>
                <Badge variant="outline" className="text-xs">
                  {classification.category}
                </Badge>
                {classification.user_override && (
                  <Badge variant="secondary" className="text-xs">
                    Overridden
                  </Badge>
                )}
              </div>
              <p className="text-sm font-semibold truncate">
                {classification.sender_email}
              </p>
              <p className="text-xs text-muted-foreground truncate">
                {classification.subject}
              </p>
            </div>
          </div>

          {/* Confidence Bar */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Confidence</span>
              <span className="font-mono">{Math.round(classification.confidence * 100)}%</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className={cn("h-full transition-all duration-500", config.bg)}
                style={{ width: `${classification.confidence * 100}%` }}
              />
            </div>
          </div>

          {/* Reasoning */}
          <p className="text-xs text-muted-foreground leading-relaxed">
            {classification.reasoning}
          </p>

          {/* Override Control */}
          <div className="flex items-center gap-2 pt-2 border-t">
            <span className="text-xs text-muted-foreground">Override:</span>
            <Select
              value={displayClassification}
              onChange={(e) => handleOverride(e.target.value)}
              disabled={isOverriding}
              className="h-8 w-[130px] text-xs"
              options={[
                { value: "KEEP", label: "Keep" },
                { value: "DELETE", label: "Delete" },
                { value: "REVIEW", label: "Review" },
              ]}
            />
            {isOverriding && <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
