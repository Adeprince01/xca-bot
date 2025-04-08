#!/usr/bin/env python3
import argparse
import json
import os
import sys
import re
from twitter_monitor import TwitterMonitor

def main():
    parser = argparse.ArgumentParser(description='Twitter/X Monitor CLI')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start monitoring')
    
    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop monitoring')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check monitoring status')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check specific users immediately')
    check_parser.add_argument('usernames', nargs='+', help='Usernames to check (without @)')
    check_parser.add_argument('--limit', type=int, default=10, help='Number of tweets to check per user')
    
    # Configure command
    config_parser = subparsers.add_parser('config', help='Configure the monitor')
    config_parser.add_argument('--twitter-api-key', help='Twitter API Key')
    config_parser.add_argument('--twitter-api-secret', help='Twitter API Secret')
    config_parser.add_argument('--twitter-access-token', help='Twitter Access Token')
    config_parser.add_argument('--twitter-token-secret', help='Twitter Access Token Secret')
    config_parser.add_argument('--telegram-bot-token', help='Telegram Bot Token')
    config_parser.add_argument('--telegram-channel', help='Telegram Channel ID')
    config_parser.add_argument('--check-interval', type=int, help='Check interval in minutes')
    
    # Users command
    users_parser = subparsers.add_parser('users', help='Manage monitored users')
    users_parser.add_argument('--add', help='Add users (comma-separated)')
    users_parser.add_argument('--remove', help='Remove users (comma-separated)')
    users_parser.add_argument('--list', action='store_true', help='List all monitored users')
    users_parser.add_argument('--file', help='Load users from file (one per line)')
    
    # Patterns command
    patterns_parser = subparsers.add_parser('patterns', help='Manage regex patterns')
    patterns_parser.add_argument('--add', help='Add regex pattern')
    patterns_parser.add_argument('--remove', help='Remove regex pattern')
    patterns_parser.add_argument('--list', action='store_true', help='List all regex patterns')
    patterns_parser.add_argument('--file', help='Load patterns from file (one per line)')
    
    # Keywords command
    keywords_parser = subparsers.add_parser('keywords', help='Manage keywords')
    keywords_parser.add_argument('--add', help='Add keyword')
    keywords_parser.add_argument('--remove', help='Remove keyword')
    keywords_parser.add_argument('--list', action='store_true', help='List all keywords')
    keywords_parser.add_argument('--file', help='Load keywords from file (one per line)')
    
    # Telegram destinations command
    telegram_parser = subparsers.add_parser('telegram', help='Manage Telegram forwarding destinations')
    telegram_parser.add_argument('--add', help='Add a Telegram destination chat ID')
    telegram_parser.add_argument('--remove', help='Remove a Telegram destination by chat ID')
    telegram_parser.add_argument('--list', action='store_true', help='List all Telegram destinations')
    telegram_parser.add_argument('--clear', action='store_true', help='Clear all Telegram destinations')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export matches to CSV')
    export_parser.add_argument('--file', default='matches_export.csv', help='Output file name')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create monitor instance
    monitor = TwitterMonitor()
    
    # Process commands
    if args.command == 'start':
        print("Starting Twitter/X Monitor...")
        try:
            monitor.start_monitoring()
        except KeyboardInterrupt:
            print("\nStopping monitoring...")
            monitor.stop_monitoring()
        finally:
            monitor.close()
    
    elif args.command == 'stop':
        # This is a bit tricky since we need to signal the running process
        pid_file = 'twitter_monitor.pid'
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, 15)  # SIGTERM
                print(f"Sent stop signal to process {pid}")
            except ProcessLookupError:
                print("No running monitor process found")
                os.remove(pid_file)
        else:
            print("No running monitor process found")
    
    elif args.command == 'status':
        # Check if process is running
        pid_file = 'twitter_monitor.pid'
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, 0)  # Check if process exists
                print(f"Twitter/X Monitor is running (PID: {pid}")
                
                # Show some stats
                matches = monitor.get_recent_matches(5)
                print(f"\nRecent matches: {len(matches)}")
                for match in matches:
                    print(f"- @{match['username']} matched '{', '.join(match['matched_pattern'])}' at {match['timestamp']}")
                
            except ProcessLookupError:
                print("Twitter/X Monitor is not running (stale PID file)")
                os.remove(pid_file)
        else:
            print("Twitter/X Monitor is not running")
    
    elif args.command == 'check':
        usernames = args.usernames
        # Clean usernames (remove @ if present)
        usernames = [username.replace('@', '') for username in usernames]
        
        print(f"🔍 Checking {len(usernames)} users for contract addresses...")
        
        # Temporarily update usernames
        original_usernames = monitor.config["monitoring"]["usernames"]
        monitor.update_usernames(usernames)
        
        # Run check
        try:
            monitor.check_tweets()
            
            # Get recent matches
            matches = monitor.get_recent_matches(10)
            
            # Filter matches for the specified users
            user_matches = [m for m in matches if m["username"].replace('@', '') in usernames]
            
            if user_matches:
                print(f"✅ Found {len(user_matches)} matches:")
                for match in user_matches:
                    # Extract contract addresses
                    contract_addresses = []
                    for pattern in match["matched_pattern"]:
                        if pattern == "0x[a-fA-F0-9]{40}":  # Ethereum address pattern
                            addresses = re.findall(r"0x[a-fA-F0-9]{40}", match["tweet_text"])
                            contract_addresses.extend(addresses)
                    
                    addresses_str = ', '.join(contract_addresses) if contract_addresses else "No CA found"
                    print(f"Username: {match['username']} | Contract: {addresses_str} | Link: {match['tweet_url']} | Time: {match['timestamp']}")
            else:
                print("No contract addresses found for the specified users.")
        except Exception as e:
            print(f"Error checking users: {e}")
        finally:
            # Restore original usernames
            monitor.update_usernames(original_usernames)
    
    elif args.command == 'config':
        # Update configuration
        changed = False
        
        if args.twitter_api_key:
            monitor.config["twitter"]["api_key"] = args.twitter_api_key
            changed = True
        
        if args.twitter_api_secret:
            monitor.config["twitter"]["api_secret"] = args.twitter_api_secret
            changed = True
        
        if args.twitter_access_token:
            monitor.config["twitter"]["access_token"] = args.twitter_access_token
            changed = True
        
        if args.twitter_token_secret:
            monitor.config["twitter"]["access_token_secret"] = args.twitter_token_secret
            changed = True
        
        if args.telegram_bot_token:
            monitor.config["telegram"]["bot_token"] = args.telegram_bot_token
            changed = True
        
        if args.telegram_channel:
            monitor.config["telegram"]["channel_id"] = args.telegram_channel
            changed = True
        
        if args.check_interval:
            monitor.config["monitoring"]["check_interval_minutes"] = args.check_interval
            changed = True
        
        if changed:
            monitor.save_config()
            print("Configuration updated successfully")
        else:
            # Display current configuration
            print("Current configuration:")
            print(json.dumps(monitor.config, indent=2))
    
    elif args.command == 'users':
        if args.list:
            users = monitor.config["monitoring"]["usernames"]
            print(f"Monitored users ({len(users)}):")
            for user in users:
                print(f"- {user}")
        
        elif args.add:
            new_users = [u.strip() for u in args.add.split(',')]
            current_users = monitor.config["monitoring"]["usernames"]
            updated_users = list(set(current_users + new_users))
            monitor.update_usernames(updated_users)
            print(f"Added {len(new_users)} users. Now monitoring {len(updated_users)} users.")
        
        elif args.remove:
            remove_users = [u.strip() for u in args.remove.split(',')]
            current_users = monitor.config["monitoring"]["usernames"]
            updated_users = [u for u in current_users if u not in remove_users]
            monitor.update_usernames(updated_users)
            print(f"Removed {len(current_users) - len(updated_users)} users. Now monitoring {len(updated_users)} users.")
        
        elif args.file:
            try:
                with open(args.file, 'r') as f:
                    new_users = [line.strip() for line in f if line.strip()]
                monitor.update_usernames(new_users)
                print(f"Loaded {len(new_users)} users from {args.file}")
            except Exception as e:
                print(f"Error loading users from file: {e}")
    
    elif args.command == 'patterns':
        if args.list:
            patterns = monitor.config["monitoring"]["regex_patterns"]
            print(f"Regex patterns ({len(patterns)}):")
            for pattern in patterns:
                print(f"- {pattern}")
        
        elif args.add:
            current_patterns = monitor.config["monitoring"]["regex_patterns"]
            current_patterns.append(args.add)
            monitor.update_patterns(current_patterns)
            print(f"Added pattern: {args.add}")
        
        elif args.remove:
            current_patterns = monitor.config["monitoring"]["regex_patterns"]
            if args.remove in current_patterns:
                current_patterns.remove(args.remove)
                monitor.update_patterns(current_patterns)
                print(f"Removed pattern: {args.remove}")
            else:
                print(f"Pattern not found: {args.remove}")
        
        elif args.file:
            try:
                with open(args.file, 'r') as f:
                    new_patterns = [line.strip() for line in f if line.strip()]
                monitor.update_patterns(new_patterns)
                print(f"Loaded {len(new_patterns)} patterns from {args.file}")
            except Exception as e:
                print(f"Error loading patterns from file: {e}")
    
    elif args.command == 'keywords':
        if args.list:
            keywords = monitor.config["monitoring"]["keywords"]
            print(f"Keywords ({len(keywords)}):")
            for keyword in keywords:
                print(f"- {keyword}")
        
        elif args.add:
            current_keywords = monitor.config["monitoring"]["keywords"]
            current_keywords.append(args.add)
            monitor.update_keywords(current_keywords)
            print(f"Added keyword: {args.add}")
        
        elif args.remove:
            current_keywords = monitor.config["monitoring"]["keywords"]
            if args.remove in current_keywords:
                current_keywords.remove(args.remove)
                monitor.update_keywords(current_keywords)
                print(f"Removed keyword: {args.remove}")
            else:
                print(f"Keyword not found: {args.remove}")
        
        elif args.file:
            try:
                with open(args.file, 'r') as f:
                    new_keywords = [line.strip() for line in f if line.strip()]
                monitor.update_keywords(new_keywords)
                print(f"Loaded {len(new_keywords)} keywords from {args.file}")
            except Exception as e:
                print(f"Error loading keywords from file: {e}")
        
        elif args.command == 'telegram':
            # Get current destinations or initialize empty list
            if 'forwarding_destinations' not in monitor.config['telegram']:
                monitor.config['telegram']['forwarding_destinations'] = []
            
            current_destinations = monitor.config['telegram']['forwarding_destinations']
            
            if args.list:
                print(f"Telegram forwarding destinations ({len(current_destinations)}):")
                for idx, dest in enumerate(current_destinations):
                    print(f"{idx+1}. Chat ID: {dest['chat_id']}")
                
                # Also show the primary channel
                primary_channel = monitor.config['telegram']['channel_id']
                if primary_channel:
                    print(f"\nPrimary channel ID: {primary_channel}")
            
            elif args.add:
                new_chat_id = args.add.strip()
                
                # Check if already exists
                exists = False
                for dest in current_destinations:
                    if dest['chat_id'] == new_chat_id:
                        exists = True
                        break
                
                if exists:
                    print(f"Destination {new_chat_id} already exists")
                else:
                    current_destinations.append({'chat_id': new_chat_id})
                    monitor.config['telegram']['forwarding_destinations'] = current_destinations
                    try:
                        monitor.save_config()
                        print(f"Added Telegram destination: {new_chat_id}")
                        print(f"Updated config: {json.dumps(monitor.config['telegram'], indent=2)}")
                    except Exception as e:
                        print(f"Error saving configuration: {e}")
                        print("Adding destination manually...")
                        # Fallback to manually writing the config
                        try:
                            with open('config.json', 'r') as f:
                                config = json.load(f)
                            
                            if 'telegram' not in config:
                                config['telegram'] = {}
                            
                            if 'forwarding_destinations' not in config['telegram']:
                                config['telegram']['forwarding_destinations'] = []
                            
                            config['telegram']['forwarding_destinations'].append({'chat_id': new_chat_id})
                            
                            with open('config.json', 'w') as f:
                                json.dump(config, f, indent=4)
                            
                            print(f"Successfully added destination {new_chat_id} to config.json")
                        except Exception as e:
                            print(f"Failed to manually update config.json: {e}")
            
            elif args.remove:
                remove_id = args.remove.strip()
                initial_count = len(current_destinations)
                
                # Filter out the destination to remove
                updated_destinations = [dest for dest in current_destinations if dest['chat_id'] != remove_id]
                
                if len(updated_destinations) < initial_count:
                    monitor.config['telegram']['forwarding_destinations'] = updated_destinations
                    monitor.save_config()
                    print(f"Removed Telegram destination: {remove_id}")
                else:
                    print(f"Destination {remove_id} not found")
            
            elif args.clear:
                monitor.config['telegram']['forwarding_destinations'] = []
                monitor.save_config()
                print("Cleared all Telegram forwarding destinations")
    
    elif args.command == 'export':
        filename = args.file
        result = monitor.export_matches_csv(filename)
        if result:
            print(f"Exported matches to {filename}")
        else:
            print("Error exporting matches")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()