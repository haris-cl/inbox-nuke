"use client"

import { useEffect, useState } from "react"
import { useRouter, usePathname } from "next/navigation"
import Link from "next/link"
import {
  LayoutDashboard,
  Mail,
  History,
  Settings,
  LogOut,
  Menu,
  X,
  Loader2,
  Paperclip,
  BarChart3,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/theme-toggle"
import { api } from "@/lib/api"
import { cn } from "@/lib/utils"

interface NavItem {
  href: string
  label: string
  icon: React.ComponentType<{ className?: string }>
}

// V2 Primary navigation - simplified 4 items
const primaryNavItems: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/space", label: "Free Up Space", icon: Paperclip },
  { href: "/dashboard/history", label: "History", icon: History },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
]

// Legacy navigation - kept for backwards compatibility but hidden from nav
// Access via direct URL only: /dashboard/score, /dashboard/senders, /dashboard/attachments
const secondaryNavItems: NavItem[] = [
  // Empty in V2 - all tools accessible via Dashboard quick actions
]

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const [userEmail, setUserEmail] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [isDisconnecting, setIsDisconnecting] = useState(false)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const status = await api.getAuthStatus()
      if (!status.connected) {
        router.push("/")
      } else {
        setUserEmail(status.email || null)
      }
    } catch (error) {
      console.error("Auth check failed:", error)
      router.push("/")
    } finally {
      setIsLoading(false)
    }
  }

  const handleDisconnect = async () => {
    if (!confirm("Are you sure you want to disconnect your Gmail account?")) {
      return
    }

    try {
      setIsDisconnecting(true)
      await api.disconnect()
      router.push("/")
    } catch (error) {
      console.error("Disconnect failed:", error)
      alert("Failed to disconnect. Please try again.")
    } finally {
      setIsDisconnecting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="min-h-screen gradient-bg noise-texture">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-border/50 bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto flex h-20 items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            >
              {isSidebarOpen ? (
                <X className="h-5 w-5" />
              ) : (
                <Menu className="h-5 w-5" />
              )}
            </Button>
            <h1 className="text-2xl font-black tracking-tight gradient-text">INBOX NUKE</h1>
          </div>

          <div className="flex items-center gap-4">
            {userEmail && (
              <span className="text-sm font-mono text-muted-foreground hidden sm:inline bg-muted/50 px-3 py-1 rounded-md">
                {userEmail}
              </span>
            )}
            <ThemeToggle />
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDisconnect}
              disabled={isDisconnecting}
              className="font-semibold"
            >
              {isDisconnecting ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <LogOut className="mr-2 h-4 w-4" />
              )}
              Disconnect
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto flex gap-8 px-6 py-8">
        {/* Sidebar */}
        <aside
          className={cn(
            "fixed inset-y-0 left-0 z-30 w-64 transform border-r border-border/50 bg-background/95 backdrop-blur-xl pt-20 transition-transform md:relative md:inset-auto md:pt-0 md:translate-x-0",
            isSidebarOpen ? "translate-x-0" : "-translate-x-full"
          )}
        >
          <nav className="space-y-6 p-4">
            {/* Primary Navigation */}
            <div className="space-y-2">
              {primaryNavItems.map((item) => {
                const Icon = item.icon
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setIsSidebarOpen(false)}
                    className={cn(
                      "flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold transition-all duration-300",
                      isActive
                        ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20 scale-105"
                        : "text-muted-foreground hover:bg-muted/50 hover:text-foreground hover:scale-102"
                    )}
                  >
                    <Icon className="h-5 w-5" />
                    {item.label}
                  </Link>
                )
              })}
            </div>

            {/* Secondary Navigation - Tools (empty in V2) */}
            {secondaryNavItems.length > 0 && (
              <div className="space-y-2">
                <div className="px-4 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Tools
                </div>
                {secondaryNavItems.map((item) => {
                  const Icon = item.icon
                  const isActive = pathname === item.href
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setIsSidebarOpen(false)}
                      className={cn(
                        "flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold transition-all duration-300",
                        isActive
                          ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20 scale-105"
                          : "text-muted-foreground hover:bg-muted/50 hover:text-foreground hover:scale-102"
                      )}
                    >
                      <Icon className="h-5 w-5" />
                      {item.label}
                    </Link>
                  )
                })}
              </div>
            )}
          </nav>
        </aside>

        {/* Mobile overlay */}
        {isSidebarOpen && (
          <div
            className="fixed inset-0 z-20 bg-background/80 backdrop-blur-sm md:hidden"
            onClick={() => setIsSidebarOpen(false)}
          />
        )}

        {/* Main content */}
        <main className="flex-1 min-w-0">{children}</main>
      </div>
    </div>
  )
}
