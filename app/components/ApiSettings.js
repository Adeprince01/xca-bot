import React, { useState, useEffect } from 'react';
import { getConfig, testTelegramDestination } from '../lib/api';
import styles from '../styles/ApiSettings.module.css';

/**
 * Component to display and manage API configuration settings
 */
export default function ApiSettings() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [notification, setNotification] = useState(null);
  
  // Input states for API settings
  const [twitterApiKey, setTwitterApiKey] = useState('');
  const [twitterApiSecret, setTwitterApiSecret] = useState('');
  const [twitterAccessToken, setTwitterAccessToken] = useState('');
  const [twitterAccessTokenSecret, setTwitterAccessTokenSecret] = useState('');
  
  const [telegramBotToken, setTelegramBotToken] = useState('');
  const [telegramChannelId, setTelegramChannelId] = useState('');
  const [newDestChatId, setNewDestChatId] = useState('');
  const [newDestDescription, setNewDestDescription] = useState('');

  useEffect(() => {
    async function fetchConfig() {
      try {
        setLoading(true);
        const configData = await getConfig();
        setConfig(configData);
        
        // Set form values from config (note: sensitive values may be masked)
        if (configData.twitter) {
          // We might only get masked values like "abcd...wxyz"
          // So we don't set fields that appear to be masked
          if (configData.twitter.api_key && !configData.twitter.api_key.includes('...')) {
            setTwitterApiKey(configData.twitter.api_key);
          }
          if (configData.twitter.api_secret && !configData.twitter.api_secret.includes('...')) {
            setTwitterApiSecret(configData.twitter.api_secret);
          }
          if (configData.twitter.access_token && !configData.twitter.access_token.includes('...')) {
            setTwitterAccessToken(configData.twitter.access_token);
          }
          if (configData.twitter.access_token_secret && !configData.twitter.access_token_secret.includes('...')) {
            setTwitterAccessTokenSecret(configData.twitter.access_token_secret);
          }
        }
        
        if (configData.telegram) {
          if (configData.telegram.bot_token && !configData.telegram.bot_token.includes('...')) {
            setTelegramBotToken(configData.telegram.bot_token);
          }
          if (configData.telegram.primary_channel_id) {
            setTelegramChannelId(configData.telegram.primary_channel_id);
          }
        }
        
        setError(null);
      } catch (err) {
        console.error('Error fetching configuration:', err);
        setError('Failed to load API configuration.');
      } finally {
        setLoading(false);
      }
    }

    fetchConfig();
  }, []);

  const handleSaveTwitterSettings = async (e) => {
    e.preventDefault();
    
    try {
      setSaving(true);
      
      // Note: This is a placeholder. You need to implement the API endpoint
      // to update Twitter API settings on the backend
      
      // This could be implemented by writing to the .env file or updating a database
      
      setNotification({
        type: 'success',
        message: 'Twitter API settings saved successfully.'
      });
      
      setTimeout(() => setNotification(null), 3000);
      
    } catch (err) {
      console.error('Error saving Twitter settings:', err);
      setError('Failed to save Twitter API settings.');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveTelegramSettings = async (e) => {
    e.preventDefault();
    
    try {
      setSaving(true);
      
      // Note: This is a placeholder. You need to implement the API endpoint
      // to update Telegram settings on the backend
      
      setNotification({
        type: 'success',
        message: 'Telegram settings saved successfully.'
      });
      
      setTimeout(() => setNotification(null), 3000);
      
    } catch (err) {
      console.error('Error saving Telegram settings:', err);
      setError('Failed to save Telegram settings.');
    } finally {
      setSaving(false);
    }
  };

  const handleTestTelegramChannel = async () => {
    try {
      setSaving(true);
      
      const result = await testTelegramDestination(telegramChannelId);
      
      if (result.success) {
        setNotification({
          type: 'success',
          message: 'Test message sent successfully!'
        });
      } else {
        setError('Failed to send test message: ' + result.message);
      }
      
    } catch (err) {
      console.error('Error testing Telegram channel:', err);
      setError('Failed to send test message to Telegram channel.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className={styles.apiSettings}>
      <h2>API Configuration</h2>
      
      {notification && (
        <div className={`${styles.notification} ${styles[notification.type]}`}>
          {notification.message}
        </div>
      )}
      
      {error && <div className={styles.error}>{error}</div>}
      
      {loading ? (
        <div className={styles.loading}>Loading configuration...</div>
      ) : (
        <div className={styles.settingsForms}>
          <form onSubmit={handleSaveTwitterSettings} className={styles.settingsForm}>
            <h3>Twitter API Settings</h3>
            
            <div className={styles.formGroup}>
              <label>API Key</label>
              <input
                type="text"
                value={twitterApiKey}
                onChange={(e) => setTwitterApiKey(e.target.value)}
                placeholder="Enter Twitter API Key"
                className={styles.formInput}
              />
            </div>
            
            <div className={styles.formGroup}>
              <label>API Secret</label>
              <input
                type="password"
                value={twitterApiSecret}
                onChange={(e) => setTwitterApiSecret(e.target.value)}
                placeholder="Enter Twitter API Secret"
                className={styles.formInput}
              />
            </div>
            
            <div className={styles.formGroup}>
              <label>Access Token</label>
              <input
                type="text"
                value={twitterAccessToken}
                onChange={(e) => setTwitterAccessToken(e.target.value)}
                placeholder="Enter Twitter Access Token"
                className={styles.formInput}
              />
            </div>
            
            <div className={styles.formGroup}>
              <label>Access Token Secret</label>
              <input
                type="password"
                value={twitterAccessTokenSecret}
                onChange={(e) => setTwitterAccessTokenSecret(e.target.value)}
                placeholder="Enter Twitter Access Token Secret"
                className={styles.formInput}
              />
            </div>
            
            <button 
              type="submit" 
              className={styles.saveButton}
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save Twitter Settings'}
            </button>
          </form>
          
          <form onSubmit={handleSaveTelegramSettings} className={styles.settingsForm}>
            <h3>Telegram Settings</h3>
            
            <div className={styles.formGroup}>
              <label>Bot Token</label>
              <input
                type="text"
                value={telegramBotToken}
                onChange={(e) => setTelegramBotToken(e.target.value)}
                placeholder="Enter Telegram Bot Token"
                className={styles.formInput}
              />
            </div>
            
            <div className={styles.formGroup}>
              <label>Primary Channel ID</label>
              <div className={styles.inputWithButton}>
                <input
                  type="text"
                  value={telegramChannelId}
                  onChange={(e) => setTelegramChannelId(e.target.value)}
                  placeholder="Enter Telegram Channel ID"
                  className={styles.formInput}
                />
                <button 
                  type="button" 
                  onClick={handleTestTelegramChannel}
                  className={styles.testButton}
                  disabled={!telegramChannelId || saving}
                >
                  Test
                </button>
              </div>
            </div>
            
            <h4>Forwarding Destinations</h4>
            
            {config && config.telegram && config.telegram.forwarding_destinations && (
              <div className={styles.destinations}>
                {config.telegram.forwarding_destinations.map((dest, index) => (
                  <div key={index} className={styles.destination}>
                    <div className={styles.destinationDetails}>
                      <div className={styles.chatId}>{dest.chat_id}</div>
                      {dest.description && (
                        <div className={styles.description}>{dest.description}</div>
                      )}
                    </div>
                    <div className={styles.destinationActions}>
                      <button 
                        type="button" 
                        className={styles.testButton}
                        onClick={() => testTelegramDestination(dest.chat_id)}
                      >
                        Test
                      </button>
                      <button 
                        type="button" 
                        className={styles.removeButton}
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            <div className={styles.addDestination}>
              <h5>Add Destination</h5>
              <div className={styles.formGroup}>
                <label>Chat ID</label>
                <input
                  type="text"
                  value={newDestChatId}
                  onChange={(e) => setNewDestChatId(e.target.value)}
                  placeholder="Enter Chat ID"
                  className={styles.formInput}
                />
              </div>
              <div className={styles.formGroup}>
                <label>Description (optional)</label>
                <input
                  type="text"
                  value={newDestDescription}
                  onChange={(e) => setNewDestDescription(e.target.value)}
                  placeholder="Enter Description"
                  className={styles.formInput}
                />
              </div>
              <button 
                type="button" 
                className={styles.addButton}
                disabled={!newDestChatId}
              >
                Add Destination
              </button>
            </div>
            
            <button 
              type="submit" 
              className={styles.saveButton}
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save Telegram Settings'}
            </button>
          </form>
        </div>
      )}
    </div>
  );
} 