#!/usr/bin/env python3
import argparse
import json
import os
import sys
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