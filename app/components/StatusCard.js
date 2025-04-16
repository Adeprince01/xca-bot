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

  // Helper to get display info based on status string
  const getStatusInfo = (statusType, statusValue) => {
    switch (statusType) {
      case 'twitter':
        switch (statusValue) {
          case 'connected': return { text: 'Connected', className: styles.active };
          case 'permission_error': return { text: 'Limited Access', className: styles.warning };
          case 'config_error': return { text: 'Config Error', className: styles.error };
          case 'disconnected': return { text: 'Disconnected', className: styles.inactive };
          default: return { text: statusValue || 'Unknown', className: styles.inactive }; // Display unknown status if received
        }
      case 'telegram':
        switch (statusValue) {
          case 'connected': return { text: 'Connected', className: styles.active };
          case 'token_missing': return { text: 'Token Missing', className: styles.error };
          case 'send_error': return { text: 'Send Error', className: styles.warning };
          case 'disconnected': return { text: 'Disconnected', className: styles.inactive };
          default: return { text: statusValue || 'Unknown', className: styles.inactive }; // Display unknown status if received
        }
      default:
        return { text: 'N/A', className: styles.inactive };
    }
  };

  // Get status display info
  const twitterStatusInfo = getStatusInfo('twitter', status?.twitter_status); // Use new status?.twitter_status
  const telegramStatusInfo = getStatusInfo('telegram', status?.telegram_status); // Use new status?.telegram_status

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
          <div className={`${styles.value} ${twitterStatusInfo.className}`}>
            {twitterStatusInfo.text}
          </div>
        </div>

        <div className={styles.item}>
          <div className={styles.label}>Telegram Bot</div>
          <div className={`${styles.value} ${telegramStatusInfo.className}`}>
            {telegramStatusInfo.text}
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
            {status.monitoring?.usernames_count ?? 'N/A'} usernames
          </div>
        </div>

        <div className={styles.item}>
          <div className={styles.label}>Check Interval</div>
          <div className={styles.value}>
            {status.monitoring?.check_interval_minutes ?? 'N/A'} minutes
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