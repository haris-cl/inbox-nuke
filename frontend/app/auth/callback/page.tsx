"use client"

import { useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { CheckCircle2, XCircle, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function AuthCallback() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [countdown, setCountdown] = useState(2)

  const success = searchParams.get("success") === "true"
  const email = searchParams.get("email")
  const error = searchParams.get("error")

  useEffect(() => {
    if (success) {
      const timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(timer)
            router.push("/dashboard")
            return 0
          }
          return prev - 1
        })
      }, 1000)

      return () => clearInterval(timer)
    }
  }, [success, router])

  const handleGoToDashboard = () => {
    router.push("/dashboard")
  }

  const handleTryAgain = () => {
    router.push("/")
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-secondary/20 flex items-center justify-center p-4">
      <Card className="max-w-md w-full">
        <CardHeader className="text-center">
          {success ? (
            <>
              <div className="mx-auto mb-4 w-16 h-16 rounded-full bg-success/10 flex items-center justify-center">
                <CheckCircle2 className="w-8 h-8 text-success" />
              </div>
              <CardTitle className="text-2xl">Successfully Connected!</CardTitle>
              <CardDescription className="text-base mt-2">
                Your Gmail account has been connected successfully.
                {email && (
                  <span className="block mt-1 font-medium text-foreground">
                    {email}
                  </span>
                )}
              </CardDescription>
            </>
          ) : (
            <>
              <div className="mx-auto mb-4 w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center">
                <XCircle className="w-8 h-8 text-destructive" />
              </div>
              <CardTitle className="text-2xl">Connection Failed</CardTitle>
              <CardDescription className="text-base mt-2">
                {error || "An error occurred while connecting your Gmail account. Please try again."}
              </CardDescription>
            </>
          )}
        </CardHeader>
        <CardContent className="space-y-4">
          {success ? (
            <>
              <p className="text-sm text-muted-foreground text-center">
                Redirecting to dashboard in {countdown} seconds...
              </p>
              <Button
                onClick={handleGoToDashboard}
                className="w-full"
                size="lg"
              >
                Go to Dashboard Now
              </Button>
            </>
          ) : (
            <Button
              onClick={handleTryAgain}
              className="w-full"
              size="lg"
            >
              Try Again
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
