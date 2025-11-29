"use client"

import { Shield, Trash2, AlertCircle } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

interface ScoreBadgeProps {
  classification: "KEEP" | "DELETE" | "UNCERTAIN"
  className?: string
  showIcon?: boolean
}

export function ScoreBadge({ classification, className, showIcon = true }: ScoreBadgeProps) {
  const config = {
    KEEP: {
      label: "Keep",
      icon: Shield,
      className: "bg-emerald-400/10 text-emerald-400 border-emerald-400/20",
    },
    DELETE: {
      label: "Delete",
      icon: Trash2,
      className: "bg-rose-400/10 text-rose-400 border-rose-400/20",
    },
    UNCERTAIN: {
      label: "Uncertain",
      icon: AlertCircle,
      className: "bg-amber-400/10 text-amber-400 border-amber-400/20",
    },
  }

  const { label, icon: Icon, className: variantClass } = config[classification]

  return (
    <Badge
      variant="outline"
      className={cn("font-semibold text-xs", variantClass, className)}
    >
      {showIcon && <Icon className="w-3 h-3 mr-1" />}
      {label}
    </Badge>
  )
}
