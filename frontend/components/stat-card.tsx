"use client"

import { LucideIcon } from "lucide-react"
import CountUp from "react-countup"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface StatCardProps {
  icon: LucideIcon
  label: string
  value: number
  trend?: {
    value: number
    isPositive: boolean
  }
  variant?: "default" | "success" | "warning" | "destructive"
  suffix?: string
  decimals?: number
}

export function StatCard({
  icon: Icon,
  label,
  value,
  trend,
  variant = "default",
  suffix = "",
  decimals = 0,
}: StatCardProps) {
  const variantColors = {
    default: "text-primary bg-gradient-to-br from-primary/20 to-primary/5 ring-primary/20",
    success: "text-success bg-gradient-to-br from-success/20 to-success/5 ring-success/20",
    warning: "text-warning bg-gradient-to-br from-warning/20 to-warning/5 ring-warning/20",
    destructive: "text-destructive bg-gradient-to-br from-destructive/20 to-destructive/5 ring-destructive/20",
  }

  const variantGlow = {
    default: "hover:shadow-primary/20",
    success: "hover:shadow-success/20",
    warning: "hover:shadow-warning/20",
    destructive: "hover:shadow-destructive/20",
  }

  return (
    <Card className={cn(
      "stat-card-glow border-2 border-border/50 backdrop-blur-sm bg-card/50 transition-all duration-300 hover:scale-[1.02]",
      variantGlow[variant]
    )}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          {label}
        </CardTitle>
        <div className={cn(
          "w-12 h-12 rounded-xl flex items-center justify-center ring-2 transition-transform duration-300 group-hover:scale-110",
          variantColors[variant]
        )}>
          <Icon className="w-6 h-6" />
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="text-4xl font-black tabular-nums font-mono tracking-tight">
          <CountUp
            end={value}
            decimals={decimals}
            duration={1.2}
            separator=","
            suffix={suffix}
          />
        </div>
        {trend && (
          <p className={cn(
            "text-xs font-semibold uppercase tracking-wide",
            trend.isPositive ? "text-success" : "text-destructive"
          )}>
            {trend.isPositive ? "↑" : "↓"} {Math.abs(trend.value)}% from last run
          </p>
        )}
      </CardContent>
    </Card>
  )
}
