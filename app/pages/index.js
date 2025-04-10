import { useState, useEffect } from 'react';
import Head from 'next/head';
import styles from '../styles/Home.module.css';
import { fetchStatus, startMonitoring, stopMonitoring, checkNow, getMatches } from '../lib/api';
import StatusCard from '../components/StatusCard';
import MatchesList from '../components/MatchesList';
import UsernameManager from '../components/UsernameManager';
import ApiSettings from '../components/ApiSettings';
import ThemeToggle from '../components/ThemeToggle';
import { useTheme } from '../context/ThemeContext';

export default function Home() {
  const { isDarkMode } = useTheme();
  const [status, setStatus] = useState(null);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [notification, setNotification] = useState(null);
  const [apiMode, setApiMode] = useState('live');
  const [recentMatches, setRecentMatches] = useState([]);
  const [apiError, setApiError] = useState(null);

  // Fetch status on initial load and periodically
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setApiError(null);
        
        // Get API status
        const statusData = await fetchStatus();
        setStatus(statusData);
        console.log("API data received:", statusData);
        
        // Fetch recent matches for dashboard
        const recentMatchesData = await getMatches(5);
        setRecentMatches(recentMatchesData);
        
        setApiMode('live');
        setLoading(false);
      } catch (error) {
        console.error('Error connecting to API:', error);
        
        // Display detailed error information
        setApiError({
          message: error.message,
          timestamp: new Date().toISOString()
        });
        
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10000); // Refresh every 10 seconds

    return () => clearInterval(interval);
  }, [apiMode]);

  // Handle service control buttons
  const handleStartMonitoring = async () => {
    try {
      setLoading(true);
      setApiError(null);
      await startMonitoring();
      const statusData = await fetchStatus();
      setStatus(statusData);
      setNotification({ type: 'success', message: 'Monitoring started successfully' });
    } catch (error) {
      setNotification({ 
        type: 'error', 
        message: `Failed to start monitoring: ${error.message}` 
      });
      console.error('Error starting monitoring:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStopMonitoring = async () => {
    try {
      setLoading(true);
      setApiError(null);
      await stopMonitoring();
      const statusData = await fetchStatus();
      setStatus(statusData);
      setNotification({ type: 'success', message: 'Monitoring stopped successfully' });
    } catch (error) {
      setNotification({ 
        type: 'error', 
        message: `Failed to stop monitoring: ${error.message}` 
      });
      console.error('Error stopping monitoring:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckNow = async () => {
    try {
      setLoading(true);
      setApiError(null);
      const result = await checkNow();
      const newMatches = result.new_matches || [];
      if (newMatches.length > 0) {
        setRecentMatches(prevMatches => [...newMatches, ...prevMatches].slice(0, 5));
      }
      setNotification({ 
        type: 'success', 
        message: `Check completed: ${newMatches.length} matches found` 
      });
    } catch (error) {
      setNotification({ 
        type: 'error', 
        message: `Failed to perform check: ${error.message}` 
      });
      console.error('Error performing check:', error);
    } finally {
      setLoading(false);
    }
  };

  const dismissNotification = () => {
    setNotification(null);
  };

  const retryConnection = () => {
    setApiError(null);
    setApiMode('live');
  };

  // Format timestamp function
  const formatDate = (timestamp) => {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  return (
    <div className={`${styles.container} ${isDarkMode ? styles.darkMode : ''}`}>
      <Head>
        <title>XCA-Bot Dashboard</title>
        <meta name="description" content="XCA-Bot Cryptocurrency Address Monitor" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className={styles.main}>
        <div className={styles.header}>
          <h1 className={styles.title}>XCA-Bot Dashboard</h1>
          <ThemeToggle />
        </div>
        
        {notification && (
          <div className={`${styles.notification} ${styles[notification.type]}`}>
            <p>{notification.message}</p>
            <button onClick={dismissNotification}>×</button>
          </div>
        )}

        {apiError && (
          <div className={styles.apiErrorBanner}>
            <div className={styles.apiErrorContent}>
              <h3>API Connection Error</h3>
              <p>{apiError.message}</p>
              <p className={styles.apiErrorTime}>
                Error occurred at {formatDate(apiError.timestamp)}
              </p>
            </div>
            <div className={styles.apiErrorActions}>
              <p>Please check that:</p>
              <ul className={styles.apiErrorList}>
                <li>The XCA-Bot backend server is running</li>
                <li>Your API URL is configured correctly (currently: {process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1'})</li>
                <li>You can run the following command in your terminal to start the server:</li>
              </ul>
              <code className={styles.commandCode}>python main.py</code>
              <button 
                onClick={retryConnection} 
                className={styles.retryButton}
              >
                Retry Connection
              </button>
            </div>
          </div>
        )}

        <div className={styles.tabs}>
          <button 
            className={activeTab === 'dashboard' ? styles.activeTab : ''} 
            onClick={() => setActiveTab('dashboard')}
          >
            Dashboard
          </button>
          <button 
            className={activeTab === 'matches' ? styles.activeTab : ''} 
            onClick={() => setActiveTab('matches')}
          >
            Matches
          </button>
          <button 
            className={activeTab === 'settings' ? styles.activeTab : ''} 
            onClick={() => setActiveTab('settings')}
          >
            Settings
          </button>
        </div>

        {activeTab === 'dashboard' && (
          <div className={styles.dashboard}>
            <div className={styles.controls}>
              <button 
                className={`${styles.button} ${styles.startButton}`}
                onClick={handleStartMonitoring}
                disabled={loading || apiError || (status && status.running)}
              >
                Start Monitoring
              </button>
              <button 
                className={`${styles.button} ${styles.stopButton}`}
                onClick={handleStopMonitoring}
                disabled={loading || apiError || (status && !status.running)}
              >
                Stop Monitoring
              </button>
              <button 
                className={`${styles.button} ${styles.checkButton}`}
                onClick={handleCheckNow}
                disabled={loading || apiError}
              >
                Check Now
              </button>
            </div>

            {status ? (
              <StatusCard status={status} />
            ) : loading ? (
              <p>Loading status...</p>
            ) : (
              <p>Status data unavailable</p>
            )}
            
            {/* Recent Matches Section on Dashboard */}
            <div className={styles.recentMatchesSection}>
              <h2>Recent Contract Addresses</h2>
              
              {recentMatches.length === 0 ? (
                <div className={styles.emptyMatches}>
                  <p>No contract addresses detected yet</p>
                  <p>Start monitoring or use "Check Now" to detect addresses</p>
                </div>
              ) : (
                <div className={styles.matchesGrid}>
                  {recentMatches.map((match) => (
                    <div key={match.id || match.tweet_id} className={styles.matchCard}>
                      <div className={styles.matchHeader}>
                        <div className={styles.username}>@{match.username}</div>
                        <div className={styles.timestamp}>{formatDate(match.timestamp)}</div>
                      </div>
                      
                      <div className={styles.tweetText}>
                        {match.tweet_text}
                      </div>
                      
                      <div className={styles.addressesSection}>
                        <h3>Contract Addresses:</h3>
                        {match.contract_addresses.map((address, index) => (
                          <div key={index} className={styles.address}>
                            <code>{address}</code>
                            <button 
                              onClick={() => {
                                navigator.clipboard.writeText(address);
                                setNotification({
                                  type: 'success',
                                  message: 'Address copied to clipboard'
                                });
                                setTimeout(() => setNotification(null), 2000);
                              }}
                              className={styles.copyButton}
                              title="Copy to clipboard"
                            >
                              Copy
                            </button>
                          </div>
                        ))}
                      </div>
                      
                      <div className={styles.matchFooter}>
                        {match.tweet_url && (
                          <a 
                            href={match.tweet_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className={styles.tweetLink}
                          >
                            View Tweet →
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              <div className={styles.viewAllMatches}>
                <button onClick={() => setActiveTab('matches')}>
                  View All Matches →
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'matches' && (
          <MatchesList />
        )}

        {activeTab === 'settings' && (
          <div className={styles.settingsContainer}>
            <UsernameManager />
            <ApiSettings />
          </div>
        )}
      </main>

      <footer className={styles.footer}>
        <p>XCA-Bot - Cryptocurrency Address Monitor</p>
      </footer>
    </div>
  );
} 