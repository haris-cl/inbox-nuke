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
    default: "text-primary bg-primary/10",
    success: "text-success bg-success/10",
    warning: "text-warning bg-warning/10",
    destructive: "text-destructive bg-destructive/10",
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {label}
        </CardTitle>
        <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center", variantColors[variant])}>
          <Icon className="w-5 h-5" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          <CountUp
            end={value}
            decimals={decimals}
            duration={1}
            separator=","
            suffix={suffix}
          />
        </div>
        {trend && (
          <p className={cn(
            "text-xs mt-1",
            trend.isPositive ? "text-success" : "text-destructive"
          )}>
            {trend.isPositive ? "+" : "-"}{Math.abs(trend.value)}% from last run
          </p>
        )}
      </CardContent>
    </Card>
  )
}
