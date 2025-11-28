"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Shield, Zap, BarChart3, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ThemeToggle } from "@/components/theme-toggle"
import { api } from "@/lib/api"

export default function Home() {
  const router = useRouter()
  const [isChecking, setIsChecking] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      setIsChecking(true)
      const status = await api.getAuthStatus()
      setIsAuthenticated(status.connected)
    } catch (err) {
      console.error("Failed to check auth status:", err)
      setIsAuthenticated(false)
    } finally {
      setIsChecking(false)
    }
  }

  const handleConnectGmail = async () => {
    try {
      setIsConnecting(true)
      setError(null)
      const response = await api.startOAuth()
      window.location.href = response.auth_url
    } catch (err) {
      console.error("Failed to start OAuth:", err)
      setError("Failed to connect to Gmail. Please try again.")
      setIsConnecting(false)
    }
  }

  const handleGoToDashboard = () => {
    router.push("/dashboard")
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-secondary/20">
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>

      <main className="container mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16 space-y-6">
          <h1 className="text-5xl md:text-6xl font-bold tracking-tight bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
            Take Back Your Inbox
          </h1>
          <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto">
            Let our autonomous AI agent declutter your Gmail inbox by intelligently removing unwanted emails while keeping what matters.
          </p>
          <div className="pt-4">
            {isChecking ? (
              <Button
                size="lg"
                disabled
                className="text-lg px-8 py-6"
              >
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Checking status...
              </Button>
            ) : isAuthenticated ? (
              <Button
                size="lg"
                onClick={handleGoToDashboard}
                className="text-lg px-8 py-6"
              >
                Go to Dashboard
              </Button>
            ) : (
              <Button
                size="lg"
                onClick={handleConnectGmail}
                disabled={isConnecting}
                className="text-lg px-8 py-6"
              >
                {isConnecting && <Loader2 className="mr-2 h-5 w-5 animate-spin" />}
                Connect Gmail
              </Button>
            )}
          </div>
          {error && (
            <p className="mt-4 text-destructive text-sm">{error}</p>
          )}
        </div>

        {/* Feature Cards */}
        <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          <Card className="border-2 hover:border-primary/50 transition-colors">
            <CardHeader>
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Shield className="w-6 h-6 text-primary" />
              </div>
              <CardTitle>100% Local</CardTitle>
              <CardDescription>
                Your data stays on your machine. We never store or transmit your emails to our servers.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-2 hover:border-primary/50 transition-colors">
            <CardHeader>
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Zap className="w-6 h-6 text-primary" />
              </div>
              <CardTitle>Fully Autonomous</CardTitle>
              <CardDescription>
                Our AI agent makes intelligent decisions about what to keep and what to delete, learning from your preferences.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-2 hover:border-primary/50 transition-colors">
            <CardHeader>
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <BarChart3 className="w-6 h-6 text-primary" />
              </div>
              <CardTitle>Real-time Progress</CardTitle>
              <CardDescription>
                Watch as your inbox gets cleaned with live updates on emails processed, deleted, and space reclaimed.
              </CardDescription>
            </CardHeader>
          </Card>
        </div>

        {/* Additional Info */}
        <div className="text-center mt-16 text-sm text-muted-foreground">
          <p>Powered by advanced AI technology to keep your inbox clean and organized</p>
        </div>
      </main>
    </div>
  )
}
