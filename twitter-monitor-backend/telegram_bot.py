#!/usr/bin/env python3
import logging
import os
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from twitter_monitor import TwitterMonitor

# Configure logging
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create monitor instance
monitor = TwitterMonitor()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "👋 Welcome to the Twitter/X Monitor Bot!\n\n"
        "I can help you monitor Twitter/X for specific content.\n\n"
        "Commands:\n"
        "/status - Check monitoring status\n"
        "/check @user1 @user2 - Check specific users\n"
        "/recent - Show recent matches\n"
        "/start_monitor - Start monitoring\n"
        "/stop_monitor - Stop monitoring\n"
        "/help - Show this help message"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "Twitter/X Monitor Bot Commands:\n\n"
        "/status - Check monitoring status\n"
        "/check @user1 @user2 - Check specific users\n"
        "/recent [number] - Show recent matches (default: 5)\n"
        "/start_monitor - Start monitoring\n"
        "/stop_monitor - Stop monitoring\n"
        "/add_user @user1 @user2 - Add users to monitor\n"
        "/remove_user @user1 @user2 - Remove users from monitoring\n"
        "/list_users - List all monitored users\n"
        "/add_keyword keyword - Add keyword to monitor\n"
        "/list_keywords - List all monitored keywords\n"
        "/add_pattern pattern - Add regex pattern to monitor\n"
        "/list_patterns - List all monitored patterns\n"
        "/help - Show this help message"
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check monitoring status."""
    # Check if process is running
    pid_file = 'twitter_monitor.pid'
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, 0)  # Check if process exists
            status_msg = f"✅ Twitter/X Monitor is running (PID: {pid})\n\n"
            
            # Add configuration info
            usernames = monitor.config["monitoring"]["usernames"]
            patterns = monitor.config["monitoring"]["regex_patterns"]
            keywords = monitor.config["monitoring"]["keywords"]
            interval = monitor.config["monitoring"]["check_interval_minutes"]
            
            status_msg += f"Monitoring {len(usernames)} users\n"
            status_msg += f"Using {len(patterns)} regex patterns\n"
            status_msg += f"Watching for {len(keywords)} keywords\n"
            status_msg += f"Checking every {interval} minutes"
            
            await update.message.reply_text(status_msg)
        except ProcessLookupError:
            await update.message.reply_text("❌ Twitter/X Monitor is not running (stale PID file)")
            os.remove(pid_file)
    else:
        await update.message.reply_text("❌ Twitter/X Monitor is not running")

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check specific users."""
    if not context.args:
        await update.message.reply_text("Please specify at least one username to check. Example: /check @user1 @user2")
        return
    
    await update.message.reply_text(f"🔍 Checking {len(context.args)} users...")
    
    # Clean usernames (remove @ if present)
    usernames = [username.replace('@', '') for username in context.args]
    
    # Temporarily update usernames
    original_usernames = monitor.config["monitoring"]["usernames"]
    monitor.update_usernames(usernames)
    
    # Run check
    monitor.check_tweets()
    
    # Restore original usernames
    monitor.update_usernames(original_usernames)
    
    # Get recent matches
    matches = monitor.get_recent_matches(10)
    
    # Filter matches for the specified users
    user_matches = [m for m in matches if m["username"].replace('@', '') in usernames]
    
    if user_matches:
        await update.message.reply_text(f"✅ Found {len(user_matches)} matches from specified users.")
    else:
        await update.message.reply_text("No matches found for the specified users.")

async def recent_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent matches."""
    limit = 5  # Default
    if context.args and context.args[0].isdigit():
        limit = min(int(context.args[0]), 20)  # Cap at 20 to avoid huge messages
    
    matches = monitor.get_recent_matches(limit)
    
    if not matches:
        await update.message.reply_text("No matches found in the database.")
        return
    
    response = f"📊 Recent {len(matches)} matches:\n\n"
    
    for match in matches:
        response += f"👤 {match['username']}\n"
        response += f"🔍 Matched: {', '.join(match['matched_pattern'])}\n"
        response += f"🔗 {match['tweet_url']}\n"
        response += f"⏰ {match['timestamp']}\n\n"
    
    await update.message.reply_text(response)

async def start_monitor_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start monitoring."""
    # Check if already running
    pid_file = 'twitter_monitor.pid'
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, 0)  # Check if process exists
            await update.message.reply_text("⚠️ Twitter/X Monitor is already running")
            return
        except ProcessLookupError:
            os.remove(pid_file)
    
    # Start in a new process
    try:
        # Fork a child process
        pid = os.fork()
        
        if pid == 0:  # Child process
            # Detach from parent
            os.setsid()
            
            # Close file descriptors
            os.close(0)
            os.close(1)
            os.close(2)
            
            # Start monitoring
            monitor.start_monitoring()
            sys.exit(0)
        else:  # Parent process
            # Write PID file
            with open(pid_file, 'w') as f:
                f.write(str(pid))
            
            await update.message.reply_text(f"✅ Twitter/X Monitor started (PID: {pid})")
    except Exception as e:
        await update.message.reply_text(f"❌ Error starting monitor: {e}")

async def stop_monitor_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop monitoring."""
    pid_file = 'twitter_monitor.pid'
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, 15)  # SIGTERM
            await update.message.reply_text(f"✅ Sent stop signal to process {pid}")
            os.remove(pid_file)
        except ProcessLookupError:
            await update.message.reply_text("❌ No running monitor process found")
            os.remove(pid_file)
    else:
        await update.message.reply_text("❌ No running monitor process found")

async def add_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add users to monitor."""
    if not context.args:
        await update.message.reply_text("Please specify at least one username to add. Example: /add_user @user1 @user2")
        return
    
    # Clean usernames (remove @ if present)
    new_users = [username.replace('@', '') for username in context.args]
    
    # Add to existing users
    current_users = monitor.config["monitoring"]["usernames"]
    updated_users = list(set(current_users + new_users))
    
    # Update config
    monitor.update_usernames(updated_users)
    
    await update.message.reply_text(f"✅ Added {len(new_users)} users. Now monitoring {len(updated_users)} users.")

async def remove_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove users from monitoring."""
    if not context.args:
        await update.message.reply_text("Please specify at least one username to remove. Example: /remove_user @user1 @user2")
        return
    
    # Clean usernames (remove @ if present)
    remove_users = [username.replace('@', '') for username in context.args]
    
    # Remove from existing users
    current_users = monitor.config["monitoring"]["usernames"]
    updated_users = [u for u in current_users if u not in remove_users]
    
    # Update config
    monitor.update_usernames(updated_users)
    
    await update.message.reply_text(f"✅ Removed {len(current_users) - len(updated_users)} users. Now monitoring {len(updated_users)} users.")

async def list_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all monitored users."""
    users = monitor.config["monitoring"]["usernames"]
    
    if not users:
        await update.message.reply_text("No users configured for monitoring.")
        return
    
    response = f"👥 Monitored users ({len(users)}):\n\n"
    for user in users:
        response += f"@{user}\n"
    
    await update.message.reply_text(response)

async def add_keyword_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add keyword to monitor."""
    if not context.args:
        await update.message.reply_text("Please specify a keyword to add. Example: /add_keyword launch")
        return
    
    # Join all args to support multi-word keywords
    keyword = ' '.join(context.args)
    
    # Add to existing keywords
    current_keywords = monitor.config["monitoring"]["keywords"]
    if keyword in current_keywords:
        await update.message.reply_text(f"⚠️ Keyword '{keyword}' is already being monitored.")
        return
    
    current_keywords.append(keyword)
    
    # Update config
    monitor.update_keywords(current_keywords)
    
    await update.message.reply_text(f"✅ Added keyword: '{keyword}'")

async def list_keywords_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all monitored keywords."""
    keywords = monitor.config["monitoring"]["keywords"]
    
    if not keywords:
        await update.message.reply_text("No keywords configured for monitoring.")
        return
    
    response = f"🔑 Monitored keywords ({len(keywords)}):\n\n"
    for keyword in keywords:
        response += f"• {keyword}\n"
    
    await update.message.reply_text(response)

async def add_pattern_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add regex pattern to monitor."""
    if not context.args:
        await update.message.reply_text("Please specify a regex pattern to add. Example: /add_pattern 0x[a-fA-F0-9]{40}")
        return
    
    # Join all args to support complex patterns
    pattern = ' '.join(context.args)
    
    # Add to existing patterns
    current_patterns = monitor.config["monitoring"]["regex_patterns"]
    if pattern in current_patterns:
        await update.message.reply_text(f"⚠️ Pattern '{pattern}' is already being monitored.")
        return
    
    current_patterns.append(pattern)
    
    # Update config
    monitor.update_patterns(current_patterns)
    
    await update.message.reply_text(f"✅ Added pattern: '{pattern}'")

async def list_patterns_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all monitored regex patterns."""
    patterns = monitor.config["monitoring"]["regex_patterns"]
    
    if not patterns:
        await update.message.reply_text("No regex patterns configured for monitoring.")
        return
    
    response = f"📋 Monitored regex patterns ({len(patterns)}):\n\n"
    for pattern in patterns:
        response += f"• {pattern}\n"
    
    await update.message.reply_text(response)

def main():
    """Start the bot."""
    # Get bot token from config
    bot_token = monitor.config["telegram"]["bot_token"]
    
    if not bot_token:
        logger.error("Telegram bot token not configured. Please edit config.json")
        print("Telegram bot token not configured. Please edit config.json")
        return
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("check", check_command))
    application.add_handler(CommandHandler("recent", recent_command))
    application.add_handler(CommandHandler("start_monitor", start_monitor_command))
    application.add_handler(CommandHandler("stop_monitor", stop_monitor_command))
    application.add_handler(CommandHandler("add_user", add_user_command))
    application.add_handler(CommandHandler("remove_user", remove_user_command))
    application.add_handler(CommandHandler("list_users", list_users_command))
    application.add_handler(CommandHandler("add_keyword", add_keyword_command))
    application.add_handler(CommandHandler("list_keywords", list_keywords_command))
    application.add_handler(CommandHandler("add_pattern", add_pattern_command))
    application.add_handler(CommandHandler("list_patterns", list_patterns_command))
    
    # Start the bot
    print("Starting Telegram bot...")
    application.run_polling()

if __name__ == "__main__":
    main()