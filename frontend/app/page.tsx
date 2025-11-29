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
    <div className="min-h-screen gradient-bg grid-pattern noise-texture">
      <div className="absolute top-6 right-6 z-50">
        <ThemeToggle />
      </div>

      <main className="container mx-auto px-6 py-20 relative">
        {/* Hero Section */}
        <div className="text-center mb-24 space-y-8 hero-glow">
          <div className="space-y-4 animate-fade-in-up">
            <h1 className="text-7xl md:text-8xl lg:text-9xl font-black tracking-tight gradient-text leading-none">
              INBOX NUKE
            </h1>
            <p className="text-2xl md:text-3xl lg:text-4xl font-bold text-foreground/90 max-w-3xl mx-auto leading-tight">
              Obliterate inbox chaos with autonomous AI cleanup
            </p>
          </div>

          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed animate-fade-in-up animate-delay-100">
            Fully local agent that intelligently removes unwanted emails while keeping what matters. Zero cloud storage, maximum privacy.
          </p>

          <div className="pt-6 animate-fade-in-up animate-delay-200">
            {isChecking ? (
              <Button
                size="lg"
                disabled
                className="text-lg px-10 py-7 font-bold shadow-lg shadow-primary/20 hover:shadow-xl hover:shadow-primary/30 transition-all duration-300"
              >
                <Loader2 className="mr-2 h-6 w-6 animate-spin" />
                Checking status...
              </Button>
            ) : isAuthenticated ? (
              <Button
                size="lg"
                onClick={handleGoToDashboard}
                className="text-lg px-10 py-7 font-bold shadow-lg shadow-primary/20 hover:shadow-xl hover:shadow-primary/30 hover:scale-105 transition-all duration-300"
              >
                Go to Dashboard
              </Button>
            ) : (
              <Button
                size="lg"
                onClick={handleConnectGmail}
                disabled={isConnecting}
                className="text-lg px-10 py-7 font-bold shadow-lg shadow-primary/20 hover:shadow-xl hover:shadow-primary/30 hover:scale-105 transition-all duration-300"
              >
                {isConnecting && <Loader2 className="mr-2 h-6 w-6 animate-spin" />}
                Connect Gmail
              </Button>
            )}
          </div>

          {error && (
            <p className="mt-4 text-destructive text-sm font-medium animate-fade-in">{error}</p>
          )}
        </div>

        {/* Feature Cards */}
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          <Card className="card-glow border-2 border-border/50 backdrop-blur-sm bg-card/50 animate-scale-in">
            <CardHeader className="space-y-4">
              <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center ring-2 ring-primary/20">
                <Shield className="w-8 h-8 text-primary" />
              </div>
              <CardTitle className="text-2xl font-bold">100% Local</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-base leading-relaxed">
                Your data stays on your machine. We never store or transmit your emails to our servers. Complete privacy guaranteed.
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="card-glow border-2 border-border/50 backdrop-blur-sm bg-card/50 animate-scale-in animate-delay-100">
            <CardHeader className="space-y-4">
              <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-accent/20 to-accent/5 flex items-center justify-center ring-2 ring-accent/20">
                <Zap className="w-8 h-8 text-accent" />
              </div>
              <CardTitle className="text-2xl font-bold">Fully Autonomous</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-base leading-relaxed">
                AI agent makes intelligent decisions about what to keep and delete. Unsubscribes, filters, and cleans automatically.
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="card-glow border-2 border-border/50 backdrop-blur-sm bg-card/50 animate-scale-in animate-delay-200">
            <CardHeader className="space-y-4">
              <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-success/20 to-success/5 flex items-center justify-center ring-2 ring-success/20">
                <BarChart3 className="w-8 h-8 text-success" />
              </div>
              <CardTitle className="text-2xl font-bold">Real-time Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-base leading-relaxed">
                Watch live updates on emails processed, deleted, and space reclaimed. Full transparency in every action taken.
              </CardDescription>
            </CardContent>
          </Card>
        </div>

        {/* Tech Stack Badge */}
        <div className="text-center mt-24 animate-fade-in animate-delay-300">
          <p className="text-sm font-mono text-muted-foreground tracking-wider uppercase">
            Powered by FastAPI + Next.js + OpenAI
          </p>
        </div>
      </main>
    </div>
  )
}
