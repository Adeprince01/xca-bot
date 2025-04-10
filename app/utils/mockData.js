// Mock data for development when API is not available

export const getMockStatus = () => {
  return {
    status: "running",
    uptime: "2h 15m",
    version: "1.0.0",
    monitoring: {
      active: true,
      usernames: ["cryptoTracker", "ethUpdates", "defiAlert"],
      last_check: new Date().toISOString(),
    },
    stats: {
      total_matches: 15,
      matches_today: 3,
    }
  };
};

export const getMockMatches = () => {
  return {
    matches: [
      {
        id: "mock-1",
        username: "cryptoTracker",
        tweet_id: "1234567890",
        tweet_text: "Just found this new contract: 0x1234567890abcdef1234567890abcdef12345678 looks promising! #ETH",
        contract_address: "0x1234567890abcdef1234567890abcdef12345678",
        timestamp: new Date(Date.now() - 25 * 60000).toISOString(),
        chain: "ETH",
        notification_sent: true,
      },
      {
        id: "mock-2",
        username: "defiAlert",
        tweet_id: "2345678901",
        tweet_text: "New BSC gem: 0xabcdef1234567890abcdef1234567890abcdef12 launching today! #BNB #BSC",
        contract_address: "0xabcdef1234567890abcdef1234567890abcdef12",
        timestamp: new Date(Date.now() - 2 * 3600000).toISOString(),
        chain: "BSC",
        notification_sent: true,
      },
      {
        id: "mock-3",
        username: "ethUpdates",
        tweet_id: "3456789012",
        tweet_text: "Just launched our token 0x7890abcdef1234567890abcdef1234567890abcd check it out! #Ethereum",
        contract_address: "0x7890abcdef1234567890abcdef1234567890abcd",
        timestamp: new Date(Date.now() - 8 * 3600000).toISOString(),
        chain: "ETH",
        notification_sent: true,
      },
      {
        id: "mock-4",
        username: "cryptoNews",
        tweet_id: "4567890123",
        tweet_text: "Bullish on $ETH and $BTC this week! Market is looking strong.",
        contract_address: "$ETH,$BTC",
        timestamp: new Date(Date.now() - 5 * 3600000).toISOString(),
        chain: "TICKER",
        notification_sent: true,
      }
    ],
    pagination: {
      total: 15,
      page: 1,
      per_page: 10,
      total_pages: 2
    }
  };
};

export const getMockConfig = () => {
  return {
    twitter: {
      usernames: ["cryptoTracker", "ethUpdates", "defiAlert", "cryptoNews"],
      check_interval: 120,
    },
    telegram: {
      enabled: true,
      primary_channel: "-100123456789",
      forwarding_destinations: ["-100987654321"],
    },
    matching: {
      keywords: ["contract", "token", "launch", "bullish"],
      regex_patterns: [
        "0x[a-fA-F0-9]{40}",
        "$[A-Za-z][A-Za-z0-9]+"
      ]
    }
  };
}; 