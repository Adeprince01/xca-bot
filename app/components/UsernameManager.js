import React, { useState, useEffect } from 'react';
import { getConfig, updateConfig } from '../lib/api';
import styles from '../styles/UsernameManager.module.css';

/**
 * Component to manage the list of Twitter/X usernames to monitor
 */
export default function UsernameManager() {
  const [usernames, setUsernames] = useState([]);
  const [newUsername, setNewUsername] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    async function fetchConfig() {
      try {
        setLoading(true);
        const config = await getConfig();
        
        if (config && config.monitoring && config.monitoring.usernames) {
          setUsernames(config.monitoring.usernames);
        }
        
        setError(null);
      } catch (err) {
        console.error('Error fetching configuration:', err);
        setError('Failed to load username configuration.');
      } finally {
        setLoading(false);
      }
    }

    fetchConfig();
  }, []);

  const handleAddUsername = () => {
    // Clean up username (remove @ if present)
    const cleanUsername = newUsername.trim().replace(/^@/, '');
    
    if (!cleanUsername) {
      setError('Please enter a valid username');
      return;
    }
    
    if (usernames.includes(cleanUsername)) {
      setError('This username is already in the list');
      return;
    }
    
    setUsernames([...usernames, cleanUsername]);
    setNewUsername('');
    setError(null);
  };

  const handleRemoveUsername = (index) => {
    const updatedUsernames = [...usernames];
    updatedUsernames.splice(index, 1);
    setUsernames(updatedUsernames);
  };

  const handleSaveChanges = async () => {
    try {
      setSaving(true);
      
      // Note: This is a placeholder. The updateConfig endpoint 
      // needs to be implemented on the backend.
      await updateConfig({
        monitoring: {
          usernames: usernames
        }
      });
      
      setNotification({
        type: 'success',
        message: 'Usernames saved successfully'
      });
      
      setTimeout(() => {
        setNotification(null);
      }, 3000);
      
    } catch (err) {
      console.error('Error saving usernames:', err);
      setError('Failed to save username configuration.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className={styles.usernameManager}>
      <h2>Manage Twitter/X Usernames</h2>
      
      {notification && (
        <div className={`${styles.notification} ${styles[notification.type]}`}>
          {notification.message}
        </div>
      )}
      
      {error && <div className={styles.error}>{error}</div>}
      
      <div className={styles.addUserForm}>
        <input
          type="text"
          placeholder="Enter Twitter/X username"
          value={newUsername}
          onChange={(e) => setNewUsername(e.target.value)}
          className={styles.usernameInput}
        />
        <button 
          onClick={handleAddUsername}
          className={styles.addButton}
          disabled={!newUsername.trim()}
        >
          Add Username
        </button>
      </div>
      
      {loading ? (
        <div className={styles.loading}>Loading usernames...</div>
      ) : (
        <>
          {usernames.length === 0 ? (
            <div className={styles.emptyState}>
              <p>No usernames configured</p>
              <p>Add Twitter/X usernames to monitor for cryptocurrency addresses</p>
            </div>
          ) : (
            <div className={styles.usernameList}>
              {usernames.map((username, index) => (
                <div key={index} className={styles.usernameItem}>
                  <div className={styles.username}>@{username}</div>
                  <button 
                    onClick={() => handleRemoveUsername(index)}
                    className={styles.removeButton}
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
          
          <div className={styles.actionButtons}>
            <button 
              onClick={handleSaveChanges} 
              disabled={saving}
              className={styles.saveButton}
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </>
      )}
    </div>
  );
} 