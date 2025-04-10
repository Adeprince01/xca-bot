import React, { useState, useEffect } from 'react';
import { getMatches } from '../lib/api';
import styles from '../styles/MatchesList.module.css';

/**
 * Component to display the list of matched cryptocurrency addresses
 */
export default function MatchesList() {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [limit, setLimit] = useState(20);

  useEffect(() => {
    async function fetchMatches() {
      try {
        setLoading(true);
        const data = await getMatches(limit);
        setMatches(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching matches:', err);
        setError('Failed to load matches. Please try again later.');
      } finally {
        setLoading(false);
      }
    }

    fetchMatches();
  }, [limit]);

  const formatDate = (timestamp) => {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const handleRefresh = async () => {
    try {
      setLoading(true);
      const data = await getMatches(limit);
      setMatches(data);
      setError(null);
    } catch (err) {
      console.error('Error refreshing matches:', err);
      setError('Failed to refresh matches. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.matchesContainer}>
      <div className={styles.header}>
        <h2>Detected Contract Addresses</h2>
        
        <div className={styles.controls}>
          <select 
            value={limit} 
            onChange={(e) => setLimit(Number(e.target.value))}
            className={styles.limitSelect}
          >
            <option value={10}>Last 10</option>
            <option value={20}>Last 20</option>
            <option value={50}>Last 50</option>
            <option value={100}>Last 100</option>
          </select>
          
          <button 
            onClick={handleRefresh} 
            disabled={loading}
            className={styles.refreshButton}
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {loading ? (
        <div className={styles.loading}>Loading matches...</div>
      ) : matches.length === 0 ? (
        <div className={styles.emptyState}>
          <p>No matches found yet</p>
          <p>Contract addresses detected in tweets will appear here</p>
        </div>
      ) : (
        <div className={styles.matchesList}>
          {matches.map((match) => (
            <div key={match.id || match.tweet_id} className={styles.matchCard}>
              <div className={styles.matchHeader}>
                <div className={styles.username}>@{match.username}</div>
                <div className={styles.timestamp}>{formatDate(match.timestamp)}</div>
              </div>
              
              <div className={styles.addresses}>
                {match.contract_addresses.map((address, index) => (
                  <div key={index} className={styles.address}>
                    <code>{address}</code>
                    <button 
                      onClick={() => navigator.clipboard.writeText(address)}
                      className={styles.copyButton}
                      title="Copy to clipboard"
                    >
                      Copy
                    </button>
                  </div>
                ))}
              </div>
              
              {match.tweet_text && (
                <div className={styles.tweetText}>
                  {match.tweet_text}
                </div>
              )}
              
              <div className={styles.matchFooter}>
                <div className={styles.patterns}>
                  {match.matched_patterns.map((pattern, index) => (
                    <span key={index} className={styles.pattern}>
                      {pattern}
                    </span>
                  ))}
                </div>
                
                <a 
                  href={match.tweet_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className={styles.tweetLink}
                >
                  View Tweet →
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
} 