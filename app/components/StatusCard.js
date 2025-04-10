import React from 'react';
import styles from '../styles/StatusCard.module.css';

/**
 * Component to display system status information
 */
export default function StatusCard({ status }) {
  // Format timestamp neatly
  const formatDate = (timestamp) => {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  return (
    <div className={styles.statusCard}>
      <h2>System Status</h2>
      
      <div className={styles.grid}>
        <div className={styles.item}>
          <div className={styles.label}>Status</div>
          <div className={`${styles.value} ${status.running ? styles.active : styles.inactive}`}>
            {status.running ? 'RUNNING' : 'STOPPED'}
          </div>
        </div>

        <div className={styles.item}>
          <div className={styles.label}>Twitter API</div>
          <div className={`${styles.value} ${status.twitter_api_ok ? styles.active : styles.inactive}`}>
            {status.twitter_api_ok ? 'CONNECTED' : 'DISCONNECTED'}
          </div>
        </div>

        <div className={styles.item}>
          <div className={styles.label}>Telegram Bot</div>
          <div className={`${styles.value} ${status.telegram_bot_ok ? styles.active : styles.inactive}`}>
            {status.telegram_bot_ok ? 'CONNECTED' : 'DISCONNECTED'}
          </div>
        </div>

        {status.uptime && (
          <div className={styles.item}>
            <div className={styles.label}>Uptime</div>
            <div className={styles.value}>{status.uptime}</div>
          </div>
        )}

        <div className={styles.item}>
          <div className={styles.label}>Monitoring</div>
          <div className={styles.value}>
            {status.monitoring.usernames_count} usernames
          </div>
        </div>

        <div className={styles.item}>
          <div className={styles.label}>Check Interval</div>
          <div className={styles.value}>
            {status.monitoring.check_interval_minutes} minutes
          </div>
        </div>

        {status.matches && (
          <div className={styles.item}>
            <div className={styles.label}>Total Matches</div>
            <div className={styles.value}>{status.matches.total}</div>
          </div>
        )}

        {status.matches && (
          <div className={styles.item}>
            <div className={styles.label}>Today's Matches</div>
            <div className={styles.value}>{status.matches.today}</div>
          </div>
        )}
      </div>
    </div>
  );
} 