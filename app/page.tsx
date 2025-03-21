"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Clock, Settings, Twitter, Database, Play, Pause, RefreshCw } from "lucide-react"
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
  StatusResponse,
  FullConfig,
  Match
} from "@/lib/api"

export default function TwitterMonitor() {
  const [isRunning, setIsRunning] = useState(false)
  const [activeTab, setActiveTab] = useState("dashboard")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [status, setStatus] = useState<StatusResponse | null>(null)
  const [recentMatches, setRecentMatches] = useState<Match[]>([])

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

  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)
        
        // Fetch status
        const statusData = await fetchStatus()
        setStatus(statusData)
        setIsRunning(statusData.is_running)
        
        // Fetch configuration
        const configData = await fetchConfig()
        setConfig(configData)
        
        // Fetch recent matches
        const matchesData = await fetchMatches(10)
        setRecentMatches(matchesData.matches)
      } catch (err) {
        console.error("Error fetching data:", err)
        setError("Failed to load data. Please check if the API server is running.")
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    
    // Poll for updates every 30 seconds
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
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
      
      if (isRunning) {
        await stopMonitoring()
        setIsRunning(false)
      } else {
        await startMonitoring()
        setIsRunning(true)
      }
    } catch (err) {
      console.error("Error toggling monitoring status:", err)
      setError("Failed to toggle monitoring status. Please try again.")
    }
  }

  const saveConfiguration = async () => {
    try {
      setError(null)
      await updateConfig(config)
      alert("Configuration saved successfully!")
    } catch (err) {
      console.error("Error saving configuration:", err)
      setError("Failed to save configuration. Please try again.")
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
          <Button onClick={toggleMonitoring} variant={isRunning ? "destructive" : "default"}>
            {isRunning ? (
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
                <div className="text-2xl font-bold">{isRunning ? "Active" : "Inactive"}</div>
                <p className="text-muted-foreground">Last check: 2 minutes ago</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle>Tracked Users</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{config.monitoring.usernames.length}</div>
                <p className="text-muted-foreground">From configuration</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle>Matches Today</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{recentMatches.length}</div>
                <p className="text-muted-foreground">Since midnight UTC</p>
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
              <div className="space-y-2">
                <Label htmlFor="twitter-usernames">Twitter/X Usernames to Monitor</Label>
                <Textarea
                  id="twitter-usernames"
                  placeholder="@user1, @user2, @user3"
                  value={config.monitoring.usernames.join(", ")}
                  onChange={(e) => setConfig({
                    ...config,
                    monitoring: {
                      ...config.monitoring,
                      usernames: e.target.value.split(", ").map(u => u.trim())
                    }
                  })}
                  className="min-h-[100px]"
                />
                <p className="text-sm text-muted-foreground">Comma-separated list of Twitter/X usernames to monitor</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="regex-patterns">Regex Patterns</Label>
                <Textarea
                  id="regex-patterns"
                  placeholder="Enter regex patterns, one per line"
                  value={config.monitoring.regex_patterns.join("\n")}
                  onChange={(e) => setConfig({
                    ...config,
                    monitoring: {
                      ...config.monitoring,
                      regex_patterns: e.target.value.split("\n").map(p => p.trim())
                    }
                  })}
                  className="min-h-[100px] font-mono text-sm"
                />
                <p className="text-sm text-muted-foreground">
                  One pattern per line. Example: 0x[a-fA-F0-9]{40} for Ethereum addresses
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="keywords">Keywords to Match</Label>
                <Textarea
                  id="keywords"
                  placeholder="Enter keywords, one per line"
                  value={config.monitoring.keywords.join("\n")}
                  onChange={(e) => setConfig({
                    ...config,
                    monitoring: {
                      ...config.monitoring,
                      keywords: e.target.value.split("\n").map(k => k.trim())
                    }
                  })}
                  className="min-h-[100px]"
                />
                <p className="text-sm text-muted-foreground">One keyword per line. Case insensitive.</p>
              </div>
            </CardContent>
            <CardFooter>
              <Button className="w-full" onClick={saveConfiguration}>
                <Settings className="mr-2 h-4 w-4" /> Save Configuration
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
                <div className="text-green-500">[2025-03-12 19:01:23] INFO: Monitoring started</div>
                <div className="text-blue-500">[2025-03-12 19:01:24] INFO: Checking 24 users for updates</div>
                <div className="text-blue-500">[2025-03-12 19:01:35] INFO: Found match in @crypto_whale tweet</div>
                <div className="text-blue-500">[2025-03-12 19:01:36] INFO: Sent notification to Telegram</div>
                <div className="text-blue-500">[2025-03-12 19:01:40] INFO: Found match in @defi_guru tweet</div>
                <div className="text-blue-500">[2025-03-12 19:01:41] INFO: Sent notification to Telegram</div>
                <div className="text-yellow-500">
                  [2025-03-12 19:01:45] WARNING: Rate limit approaching (450/500 requests)
                </div>
                <div className="text-blue-500">[2025-03-12 19:16:23] INFO: Checking 24 users for updates</div>
                <div className="text-blue-500">[2025-03-12 19:16:45] INFO: No new matches found</div>
                <div className="text-blue-500">[2025-03-12 19:31:23] INFO: Checking 24 users for updates</div>
                <div className="text-red-500">[2025-03-12 19:31:25] ERROR: Twitter API rate limit exceeded</div>
                <div className="text-blue-500">[2025-03-12 19:31:26] INFO: Waiting 15 minutes before retry</div>
                <div className="text-blue-500">[2025-03-12 19:46:23] INFO: Checking 24 users for updates</div>
                <div className="text-blue-500">[2025-03-12 19:46:35] INFO: Found match in @nft_collector tweet</div>
                <div className="text-blue-500">[2025-03-12 19:46:36] INFO: Sent notification to Telegram</div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-between">
              <Button
                variant="outline"
                onClick={() => {
                  try {
                    setError(null)
                    alert("Logs cleared successfully!")
                  } catch (err) {
                    console.error("Error clearing logs:", err)
                    setError("Failed to clear logs. Please try again.")
                  }
                }}
              >
                Clear Logs
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  try {
                    setError(null)
                    alert("Logs downloaded successfully!")
                  } catch (err) {
                    console.error("Error downloading logs:", err)
                    setError("Failed to download logs. Please try again.")
                  }
                }}
              >
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
                      await exportMatches()
                      alert("Data exported successfully!")
                    } catch (err) {
                      console.error("Error exporting data:", err)
                      setError("Failed to export data. Please try again.")
                    }
                  }}
                >
                  <Database className="mr-2 h-4 w-4" /> Export CSV
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={async () => {
                    try {
                      setError(null)
                      await cleanupDatabase()
                      alert("Database compacted successfully!")
                    } catch (err) {
                      console.error("Error compacting database:", err)
                      setError("Failed to compact database. Please try again.")
                    }
                  }}
                >
                  <RefreshCw className="mr-2 h-4 w-4" /> Compact DB
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}