"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import {
  Shield,
  Trash2,
  HardDrive,
  ChevronRight,
  Loader2,
  ShoppingBag,
  Mail,
  Users,
  Bell,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useCleanup, RecommendationSummary } from "../cleanup-context"

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B"
  const k = 1024
  const sizes = ["B", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i]
}

export default function ReportPage() {
  const router = useRouter()
  const { sessionId, recommendations, setRecommendations, setMode } = useCleanup()
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  // Fetch recommendations
  useEffect(() => {
    if (!sessionId) {
      router.push("/dashboard/cleanup/scanning")
      return
    }

    const fetchRecommendations = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/api/cleanup/recommendations/${sessionId}`
        )
        const data: RecommendationSummary = await response.json()
        setRecommendations(data)
      } catch (error) {
        console.error("Failed to fetch recommendations:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchRecommendations()
  }, [sessionId, router, setRecommendations])

  const handleModeSelect = async (mode: "quick" | "full") => {
    setSubmitting(true)
    await setMode(mode)
    router.push("/dashboard/cleanup/review")
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground">Preparing your inbox report...</p>
      </div>
    )
  }

  const recs = recommendations

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold">
          We found{" "}
          <span className="text-primary">
            {recs?.total_to_cleanup.toLocaleString() || 0}
          </span>{" "}
          emails to clean up
        </h1>
        <p className="text-xl text-muted-foreground">
          Free up to{" "}
          <span className="font-semibold text-foreground">
            {formatBytes(recs?.space_savings || 0)}
          </span>{" "}
          of storage space
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-6 flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-destructive/10 flex items-center justify-center">
              <Trash2 className="w-6 h-6 text-destructive" />
            </div>
            <div>
              <div className="text-2xl font-bold">
                {recs?.total_to_cleanup.toLocaleString() || 0}
              </div>
              <div className="text-sm text-muted-foreground">To clean up</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-green-500/10 flex items-center justify-center">
              <Shield className="w-6 h-6 text-green-500" />
            </div>
            <div>
              <div className="text-2xl font-bold">
                {recs?.total_protected.toLocaleString() || 0}
              </div>
              <div className="text-sm text-muted-foreground">Protected</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-blue-500/10 flex items-center justify-center">
              <HardDrive className="w-6 h-6 text-blue-500" />
            </div>
            <div>
              <div className="text-2xl font-bold">
                {formatBytes(recs?.space_savings || 0)}
              </div>
              <div className="text-sm text-muted-foreground">Space to free</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Category Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>What we found</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <CategoryItem
              icon={<ShoppingBag className="w-5 h-5 text-orange-500" />}
              label="Promotions"
              count={recs?.category_breakdown?.promotions || 0}
            />
            <CategoryItem
              icon={<Mail className="w-5 h-5 text-blue-500" />}
              label="Newsletters"
              count={recs?.category_breakdown?.newsletters || 0}
            />
            <CategoryItem
              icon={<Users className="w-5 h-5 text-purple-500" />}
              label="Social"
              count={recs?.category_breakdown?.social || 0}
            />
            <CategoryItem
              icon={<Bell className="w-5 h-5 text-green-500" />}
              label="Updates"
              count={recs?.category_breakdown?.updates || 0}
            />
          </div>
        </CardContent>
      </Card>

      {/* Protected Section */}
      <Card className="border-green-500/30 bg-green-500/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-green-500" />
            What's Protected
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {recs?.protected_reasons.map((reason, i) => (
              <li key={i} className="flex items-center gap-2 text-muted-foreground">
                <div className="w-2 h-2 rounded-full bg-green-500" />
                {reason}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Mode Selection */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-center">Choose how to proceed</h2>
        <div className="grid md:grid-cols-2 gap-4">
          {/* Quick Clean */}
          <Card
            className="cursor-pointer transition-all hover:border-primary hover:shadow-lg"
            onClick={() => !submitting && handleModeSelect("quick")}
          >
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                  <Trash2 className="w-6 h-6 text-primary" />
                </div>
                <span className="text-xs font-medium px-2 py-1 rounded-full bg-primary/10 text-primary">
                  Recommended
                </span>
              </div>
              <h3 className="text-lg font-semibold mb-2">Quick Clean</h3>
              <p className="text-muted-foreground text-sm mb-4">
                Let AI handle most decisions. You'll only review uncertain emails.
              </p>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">
                  ~{Math.min(50, Math.round((recs?.total_to_cleanup || 0) * 0.05))} emails
                  to review
                </span>
                <ChevronRight className="w-5 h-5 text-primary" />
              </div>
            </CardContent>
          </Card>

          {/* Review All */}
          <Card
            className="cursor-pointer transition-all hover:border-primary hover:shadow-lg"
            onClick={() => !submitting && handleModeSelect("full")}
          >
            <CardContent className="p-6">
              <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-4">
                <Mail className="w-6 h-6 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Review All</h3>
              <p className="text-muted-foreground text-sm mb-4">
                Review every email before deletion. Takes longer but gives full control.
              </p>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">
                  {recs?.total_to_cleanup.toLocaleString() || 0} emails to review
                </span>
                <ChevronRight className="w-5 h-5 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {submitting && (
        <div className="flex justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      )}
    </div>
  )
}

function CategoryItem({
  icon,
  label,
  count,
}: {
  icon: React.ReactNode
  label: string
  count: number
}) {
  return (
    <div className="flex items-center gap-3 p-4 rounded-lg bg-muted/50">
      {icon}
      <div>
        <div className="font-semibold">{count.toLocaleString()}</div>
        <div className="text-xs text-muted-foreground">{label}</div>
      </div>
    </div>
  )
}
