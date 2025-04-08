"use client"

import { useEffect, useState } from "react"
import { ThemeProvider as NextThemesProvider } from "next-themes"
import { type ThemeProviderProps } from "next-themes"

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  // This ensures hydration doesn't cause issues by rendering nothing on the server
  // and only showing the content once we're on the client
  const [mounted, setMounted] = useState(false)
  
  useEffect(() => {
    setMounted(true)
  }, [])
  
  if (!mounted) {
    // Return a placeholder with the same structure but no theme classes
    return <>{children}</>
  }

  return <NextThemesProvider {...props}>{children}</NextThemesProvider>
} 