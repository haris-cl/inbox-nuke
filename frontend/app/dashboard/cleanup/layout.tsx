"use client"

import { CleanupProvider } from "./cleanup-context"

export default function CleanupLayout({ children }: { children: React.ReactNode }) {
  return <CleanupProvider>{children}</CleanupProvider>
}
