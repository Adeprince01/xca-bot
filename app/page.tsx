"use client"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Clock, Settings, Twitter, Database, Play, Pause, RefreshCw, Loader2 } from "lucide-react"
import { TagInput } from "./components/TagInput"
import "./styles/tag-input.css"
import { 
  fetchStatus, 
  startMonitoring, 
  stopMonitoring, 
  fetchConfig, 
  updateConfig,
  fetchMatches,
  checkNow,
  exportMatches,
  cleanupDatabase,
  fetchLogs,
  checkApiAvailability,
  StatusResponse,
  FullConfig,
  Match
} from "@/lib/api"
import { formatDateTime } from "@/lib/utils"

export default function TwitterMonitor() {
  const [isRunning, setIsRunning] = useState(false)
  const [activeTab, setActiveTab] = useState("dashboard")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [status, setStatus] = useState<StatusResponse | null>(null)
  const [recentMatches, setRecentMatches] = useState<Match[]>([])
  const [logs, setLogs] = useState<string[]>([])
  const logsEndRef = useRef<HTMLDivElement>(null)

  // Configuration state with nested structure
  const [config, setConfig] = useState<FullConfig>({
    twitter: {
      api_key: "",
      api_secret: "",
      access_token: "",
      access_token_secret: ""
    },
    telegram: {
      bot_token: "",
      channel_id: "",
      enable_direct_messages: false,
      include_tweet_text: true
    },
    monitoring: {
      check_interval_minutes: 15,
      usernames: [],
      regex_patterns: [],
      keywords: []
    }
  })

  // Add loading states
  const [isSavingConfig, setIsSavingConfig] = useState(false)
  const [isCheckingNow, setIsCheckingNow] = useState(false)
  const [isTogglingMonitor, setIsTogglingMonitor] = useState(false)
  const [isExportingMatches, setIsExportingMatches] = useState(false)
  const [isCleaningDatabase, setIsCleaningDatabase] = useState(false)

  // Scroll to bottom of logs when new entries arrive
  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [logs])

  // Fetch initial data and set up SSE connections
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setLoading(true)
        setError(null)
        
        // Check if API is available first
        const isAvailable = await checkApiAvailability()
        if (!isAvailable) {
          throw new Error("API server is not available. Please ensure the backend server is running.")
        }
        
        // Fetch configuration
        const configData = await fetchConfig()
        setConfig(configData)
        
        // Fetch recent matches
        const matchesData = await fetchMatches(10)
        setRecentMatches(matchesData.matches)
        
        // Fetch initial logs
        const logsData = await fetchLogs(100)
        setLogs(logsData)
      } catch (err) {
        console.error("Error fetching initial data:", err)
        setError(`Failed to load initial data: ${err instanceof Error ? err.message : String(err)}`)
      } finally {
        setLoading(false)
      }
    }

    // Set up SSE connections
    const setupSSE = () => {
      // Status updates
      const statusSource = new EventSource(`${process.env.NEXT_PUBLIC_API_URL}/stream/status`)
      statusSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setIsRunning(data.is_running)
          setStatus(prev => ({
            ...prev!,
            is_running: data.is_running,
            uptime: data.uptime,
            last_check: data.next_run
          }))
        } catch (err) {
          console.error("Error parsing status update:", err)
        }
      }
      
      // Match updates
      const matchSource = new EventSource(`${process.env.NEXT_PUBLIC_API_URL}/stream/matches`)
      matchSource.onmessage = (event) => {
        try {
          const match = JSON.parse(event.data)
          setRecentMatches(prev => [match, ...prev].slice(0, 10))
        } catch (err) {
          console.error("Error parsing match update:", err)
        }
      }
      
      // Log updates
      const logSource = new EventSource(`${process.env.NEXT_PUBLIC_API_URL}/stream/logs`)
      logSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setLogs(prev => [...prev, data.log])
        } catch (err) {
          console.error("Error parsing log update:", err)
        }
      }

      // Error handling for SSE connections
      const handleError = (source: EventSource, name: string) => {
        source.onerror = (err) => {
          console.error(`Error in ${name} SSE connection:`, err)
          setError(`Lost connection to server (${name}). Attempting to reconnect...`)
          
          // Try to reconnect after a delay
          setTimeout(() => {
            source.close()
            setupSSE()
          }, 5000)
        }
      }

      handleError(statusSource, "status")
      handleError(matchSource, "matches")
      handleError(logSource, "logs")

      // Cleanup function
      return () => {
        statusSource.close()
        matchSource.close()
        logSource.close()
      }
    }

    fetchInitialData()
    const cleanup = setupSSE()

    return () => {
      cleanup()
    }
  }, [])

  const handleConfigChange = (section: keyof FullConfig, field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    try {
      const value = e.target.type === "checkbox" ? (e.target as HTMLInputElement).checked : e.target.value
      setConfig({
        ...config,
        [section]: {
          ...config[section],
          [field]: value,
        },
      })
    } catch (err) {
      console.error(`Error updating ${field}:`, err)
      setError(`Failed to update ${field}. Please try again.`)
    }
  }

  const toggleMonitoring = async () => {
    try {
      setError(null)
      setIsTogglingMonitor(true)
      
      if (isRunning) {
        await stopMonitoring()
        setIsRunning(false)
      } else {
        await startMonitoring()
        setIsRunning(true)
      }
    } catch (err) {
      console.error("Error toggling monitoring status:", err)
      setError(`Failed to ${isRunning ? 'stop' : 'start'} monitoring: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setIsTogglingMonitor(false)
    }
  }

  const saveConfiguration = async () => {
    try {
      setError(null)
      setIsSavingConfig(true)
      await updateConfig(config)
      alert("Configuration saved successfully!")
    } catch (err) {
      console.error("Error saving configuration:", err)
      setError("Failed to save configuration. Please try again.")
    } finally {
      setIsSavingConfig(false)
    }
  }

  // Add function to calculate today's matches
  const getMatchesToday = () => {
    const today = new Date().toISOString().split('T')[0] // YYYY-MM-DD
    return recentMatches.filter(match => {
      const matchDate = new Date(match.timestamp).toISOString().split('T')[0]
      return matchDate === today
    }).length
  }

  // Add function to run an immediate check
  const performImmediateCheck = async () => {
    try {
      setError(null)
      setIsCheckingNow(true)
      await checkNow()
    } catch (err) {
      console.error("Error performing immediate check:", err)
      setError(`Failed to perform check: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setIsCheckingNow(false)
    }
  }
  
  const refreshData = async () => {
    try {
      setError(null)
      
      // Fetch recent matches
      const matchesData = await fetchMatches(10)
      setRecentMatches(matchesData.matches)
      
      // Fetch status
      const statusData = await fetchStatus()
      setStatus(statusData)
      setIsRunning(statusData.is_running)
      
      alert("Data refreshed successfully!")
    } catch (err) {
      console.error("Error refreshing data:", err)
      setError("Failed to refresh data. Please try again.")
    }
  }

  // Update log management functions
  const clearLogs = async () => {
    try {
      setError(null)
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/logs/clear`, { method: 'POST' })
      setLogs([])
    } catch (err) {
      console.error("Error clearing logs:", err)
      setError("Failed to clear logs. Please try again.")
    }
  }

  const downloadLogs = async () => {
    try {
      setError(null)
      window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/logs/download`
    } catch (err) {
      console.error("Error downloading logs:", err)
      setError("Failed to download logs. Please try again.")
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto p-4 flex justify-center items-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-lg">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-4 max-w-6xl">
      <header className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Twitter/X Monitor</h1>
          <p className="text-muted-foreground">Extract specific content and send to Telegram</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Badge variant={isRunning ? "default" : "outline"} className={isRunning ? "bg-green-500" : ""}>
              {isRunning ? "Running" : "Stopped"}
            </Badge>
          </div>
          <Button 
            onClick={toggleMonitoring} 
            variant={isRunning ? "destructive" : "default"}
            disabled={isTogglingMonitor}
          >
            {isTogglingMonitor ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Processing...
              </>
            ) : isRunning ? (
              <>
                <Pause className="mr-2 h-4 w-4" /> Stop
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" /> Start
              </>
            )}
          </Button>
        </div>
      </header>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4 relative">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
          <button className="absolute top-0 bottom-0 right-0 px-4 py-3" onClick={() => setError(null)}>
            <span className="sr-only">Dismiss</span>
            <span className="text-xl">×</span>
          </button>
        </div>
      )}

      <Tabs defaultValue="dashboard" className="space-y-4" onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="configuration">Configuration</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle>Monitoring Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex justify-between items-center mb-2">
                  <div className="text-2xl font-bold">{isRunning ? "Active" : "Inactive"}</div>
                  <Badge variant={isRunning ? "default" : "outline"} className={isRunning ? "bg-green-500" : ""}>
                    {isRunning ? "Running" : "Stopped"}
                  </Badge>
                </div>
                {status?.last_check ? (
                  <p className="text-muted-foreground">
                    <Clock className="inline mr-1 h-4 w-4" /> Last check: {formatDateTime(status.last_check)}
                  </p>
                ) : (
                  <p className="text-muted-foreground">No checks performed yet</p>
                )}
                {status?.uptime && (
                  <p className="text-muted-foreground mt-1">Uptime: {status.uptime}</p>
                )}
                <Button 
                  className="w-full mt-4" 
                  onClick={performImmediateCheck}
                  disabled={isCheckingNow || !isRunning}
                  variant="outline"
                  size="sm"
                >
                  {isCheckingNow ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Running Check
                    </>
                  ) : (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4" /> Run Check Now
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle>Tracked Users</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{config.monitoring.usernames.length}</div>
                <p className="text-muted-foreground">Checking every {config.monitoring.check_interval_minutes} minutes</p>
                {config.monitoring.usernames.length > 0 ? (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {config.monitoring.usernames.slice(0, 5).map((username, i) => (
                      <Badge key={i} variant="outline">@{username}</Badge>
                    ))}
                    {config.monitoring.usernames.length > 5 && (
                      <Badge variant="outline">+{config.monitoring.usernames.length - 5} more</Badge>
                    )}
                  </div>
                ) : (
                  <div className="mt-2 text-yellow-500">No users configured</div>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle>Matches Today</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{getMatchesToday()}</div>
                <p className="text-muted-foreground">Since midnight {Intl.DateTimeFormat().resolvedOptions().timeZone}</p>
                <div className="flex justify-between mt-4">
                  <Button 
                    size="sm" 
                    variant="outline" 
                    onClick={() => {
                      setIsExportingMatches(true);
                      exportMatches()
                        .then(() => alert("Data exported successfully!"))
                        .catch((err) => {
                          console.error("Error exporting data:", err)
                          setError("Failed to export data. Please try again.")
                        })
                        .finally(() => setIsExportingMatches(false));
                    }}
                    disabled={isExportingMatches || recentMatches.length === 0}
                  >
                    {isExportingMatches ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Database className="h-4 w-4" />
                    )} Export
                  </Button>
                  <Button 
                    size="sm" 
                    variant="outline" 
                    onClick={() => {
                      setIsCleaningDatabase(true);
                      cleanupDatabase()
                        .then(() => alert("Database compacted successfully!"))
                        .catch((err) => {
                          console.error("Error compacting database:", err)
                          setError("Failed to compact database. Please try again.")
                        })
                        .finally(() => setIsCleaningDatabase(false));
                    }}
                    disabled={isCleaningDatabase}
                  >
                    {isCleaningDatabase ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Compacting...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4" /> Compact DB
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Recent Matches</CardTitle>
              <CardDescription>Content matching your patterns</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentMatches.map((match, index) => (
                  <div key={index} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center">
                        <Twitter className="h-4 w-4 mr-2 text-blue-500" />
                        <span className="font-medium">{match.username}</span>
                      </div>
                      <div className="flex items-center text-sm text-muted-foreground">
                        <Clock className="h-3 w-3 mr-1" />
                        {match.timestamp}
                      </div>
                    </div>
                    <p className="mb-2">{match.tweet_text}</p>
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="outline" className="text-xs">
                        {match.matched_pattern.join(", ")}
                      </Badge>
                      <a
                        href={match.tweet_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-500 hover:underline"
                      >
                        View Tweet
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
            <CardFooter>
              <Button variant="outline" className="w-full" onClick={refreshData}>
                <RefreshCw className="mr-2 h-4 w-4" /> Refresh Data
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>

        <TabsContent value="configuration" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Twitter/X Configuration</CardTitle>
                <CardDescription>API settings and monitoring parameters</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="twitter-api-key">Twitter/X API Key</Label>
                  <Input
                    id="twitter-api-key"
                    type="password"
                    value={config.twitter.api_key}
                    onChange={handleConfigChange("twitter", "api_key")}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="twitter-api-secret">Twitter/X API Secret</Label>
                  <Input
                    id="twitter-api-secret"
                    type="password"
                    value={config.twitter.api_secret}
                    onChange={handleConfigChange("twitter", "api_secret")}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="twitter-access-token">Access Token</Label>
                  <Input
                    id="twitter-access-token"
                    type="password"
                    value={config.twitter.access_token}
                    onChange={handleConfigChange("twitter", "access_token")}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="twitter-token-secret">Access Token Secret</Label>
                  <Input
                    id="twitter-token-secret"
                    type="password"
                    value={config.twitter.access_token_secret}
                    onChange={handleConfigChange("twitter", "access_token_secret")}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="check-interval">Check Interval (minutes)</Label>
                  <Input
                    id="check-interval"
                    type="number"
                    value={config.monitoring.check_interval_minutes}
                    onChange={handleConfigChange("monitoring", "check_interval_minutes")}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Telegram Configuration</CardTitle>
                <CardDescription>Bot settings and channel information</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="telegram-bot-token">Telegram Bot Token</Label>
                  <Input
                    id="telegram-bot-token"
                    type="password"
                    value={config.telegram.bot_token}
                    onChange={handleConfigChange("telegram", "bot_token")}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="telegram-channel">Telegram Channel ID</Label>
                  <Input
                    id="telegram-channel"
                    placeholder="@yourchannel or -100123456789"
                    value={config.telegram.channel_id}
                    onChange={handleConfigChange("telegram", "channel_id")}
                  />
                </div>
                <div className="flex items-center space-x-2 pt-4">
                  <Switch
                    id="direct-messages"
                    checked={config.telegram.enable_direct_messages}
                    onCheckedChange={(checked) => setConfig({ 
                      ...config, 
                      telegram: { ...config.telegram, enable_direct_messages: checked }
                    })}
                  />
                  <Label htmlFor="direct-messages">Enable direct messages to bot</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Switch
                    id="include-tweet-text"
                    checked={config.telegram.include_tweet_text}
                    onCheckedChange={(checked) => setConfig({ 
                      ...config, 
                      telegram: { ...config.telegram, include_tweet_text: checked }
                    })}
                  />
                  <Label htmlFor="include-tweet-text">Include tweet text in notifications</Label>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Monitoring Configuration</CardTitle>
              <CardDescription>Users to track and patterns to match</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <TagInput
                label="Twitter/X Usernames to Monitor"
                description="List of Twitter/X usernames to monitor (without @ symbol)"
                value={config.monitoring.usernames}
                onChange={(values: string[]) => setConfig({
                  ...config,
                  monitoring: {
                    ...config.monitoring,
                    usernames: values
                  }
                })}
                placeholder="Add username..."
                className="mb-4"
              />

              <TagInput
                label="Regex Patterns"
                description="Regular expressions to match in tweets"
                value={config.monitoring.regex_patterns}
                onChange={(values: string[]) => setConfig({
                  ...config,
                  monitoring: {
                    ...config.monitoring,
                    regex_patterns: values
                  }
                })}
                placeholder="Add regex pattern..."
                className="mb-4"
              />

              <TagInput
                label="Keywords to Match"
                description="Simple keywords to look for in tweets"
                value={config.monitoring.keywords}
                onChange={(values: string[]) => setConfig({
                  ...config,
                  monitoring: {
                    ...config.monitoring,
                    keywords: values
                  }
                })}
                placeholder="Add keyword..."
                className="mb-4"
              />
            </CardContent>
            <CardFooter>
              <Button 
                className="w-full" 
                onClick={saveConfiguration}
                disabled={isSavingConfig}
              >
                {isSavingConfig ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving Configuration...
                  </>
                ) : (
                  <>
                    <Settings className="mr-2 h-4 w-4" /> 
                    Save Configuration
                  </>
                )}
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>

        <TabsContent value="logs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>System Logs</CardTitle>
              <CardDescription>Recent activity and errors</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="bg-muted p-4 rounded-md font-mono text-sm h-[400px] overflow-y-auto">
                {logs.map((log, index) => (
                  <div
                    key={index}
                    className={
                      log.includes("ERROR") ? "text-red-500" :
                      log.includes("WARNING") ? "text-yellow-500" :
                      log.includes("INFO") ? "text-blue-500" :
                      "text-green-500"
                    }
                  >
                    {log}
                  </div>
                ))}
                <div ref={logsEndRef} />
              </div>
            </CardContent>
            <CardFooter className="flex justify-between">
              <Button variant="outline" onClick={clearLogs}>
                Clear Logs
              </Button>
              <Button variant="outline" onClick={downloadLogs}>
                Download Logs
              </Button>
            </CardFooter>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Database</CardTitle>
              <CardDescription>Stored matches and statistics</CardDescription>
            </CardHeader>
            <CardContent className="flex justify-between items-center">
              <div>
                <p>
                  SQLite database: <code>twitter_monitor.db</code>
                </p>
                <p className="text-sm text-muted-foreground">Size: 2.4 MB • 342 records</p>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={async () => {
                    try {
                      setError(null)
                      setIsExportingMatches(true)
                      await exportMatches()
                      alert("Data exported successfully!")
                    } catch (err) {
                      console.error("Error exporting data:", err)
                      setError("Failed to export data. Please try again.")
                    } finally {
                      setIsExportingMatches(false)
                    }
                  }}
                  disabled={isExportingMatches}
                >
                  {isExportingMatches ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Exporting...
                    </>
                  ) : (
                    <>
                      <Database className="mr-2 h-4 w-4" /> Export CSV
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={async () => {
                    try {
                      setError(null)
                      setIsCleaningDatabase(true)
                      await cleanupDatabase()
                      alert("Database compacted successfully!")
                    } catch (err) {
                      console.error("Error compacting database:", err)
                      setError("Failed to compact database. Please try again.")
                    } finally {
                      setIsCleaningDatabase(false)
                    }
                  }}
                  disabled={isCleaningDatabase}
                >
                  {isCleaningDatabase ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Compacting...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4" /> Compact DB
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}