# Telegram Currency Bot (Драго)

## Overview
A comprehensive Telegram bot that manages a virtual currency system called "Драго" (Drago). Users can earn, transfer, and check their balance of this virtual currency. The bot features complete transfer tracking, detailed statistics, a leaderboard system, and powerful moderation tools including admin hierarchy and ban system.

## Recent Changes
- **October 18, 2025**: Set up Telegram bot with currency system
  - Fixed indentation error in transfer_coins function
  - Fixed timedelta bug (changed `hour=10` to `hours=10`)
  - Installed pyTelegramBotAPI dependency
  - Bot is now running and listening for messages
  - Changed starting balance from 100 to 10 Драго
  - Added owner role for @RYBBKA_MACO with infinite balance
  - Added transfers tracking table to database
  - Added comprehensive statistics system (/stats, /stats_day, /stats_week, /stats_month)
  - Added leaderboard system (/top, /rich)
  - Fixed error message consistency (10 hours instead of 10 minutes)
  - Added input validation and maximum transfer limits
  - **Added complete moderation system:**
    - Ban/unban system with reasons and tracking
    - Admin hierarchy (main admin can appoint other admins)
    - Ban checks on all commands
    - Admin-only commands for moderation
    - Rights management system

## Features

### Economy Commands
- **/start** - Register and get 10 Драго starting balance (owner gets infinite balance)
- **/balance** - Check your current balance (shows ∞ for owner)
- **/checkbalance @username** - Check another user's balance (also works with /userbalance or /balanceof)
- **/earn** - Earn 10 Драго (once every 10 hours, not available for owner)
- **/transfer @username amount** - Transfer Драго to other users (owner can send unlimited amounts without deduction)

### Statistics Commands
- **/stats** - View overall system statistics (total users, total Драго, richest user, total transfers)
- **/stats_day** - View transfer statistics for today
- **/stats_week** - View transfer statistics for the last 7 days
- **/stats_month** - View transfer statistics for the last 30 days
- **/top** or **/rich** - View top 10 richest users leaderboard

### Moderation Commands (Admin Only)
- **/ban @username [reason]** - Ban a user from the bot
- **/unban @username** - Unban a user
- **/banlist** or **/bans** - View list of banned users
- **/adminlist** or **/admins** - View list of administrators
- **/myadmin** or **/myrights** - Check your access rights

### Main Admin Commands (Only @RYBBKA_MACO)
- **/addadmin @username** - Appoint a new administrator
- **/removeadmin @username** - Remove an administrator

### Other
- **/help** - Show available commands (context-aware based on permissions)

## Permission System

### Owner/Main Admin (@RYBBKA_MACO)
- Infinite balance (∞ Драго)
- Can transfer any amount without losing balance
- Cannot use /earn command (already has infinite balance)
- Full admin privileges:
  - Ban/unban any user (including other admins)
  - Appoint and remove administrators
  - View all statistics and lists
  - Access all moderation tools

### Appointed Administrators
- Regular economy features
- Can ban/unban regular users (but not other admins)
- Can view ban list and admin list
- Access all statistics
- Cannot appoint or remove other admins

### Regular Users
- Basic economy commands (earn, transfer, balance)
- View public statistics
- No moderation capabilities

## Project Structure
- `main.py`: Main bot file with all commands and SQLite database logic
- `users.db`: SQLite database storing user data (created automatically)
- `pyproject.toml`: Python project configuration

## Database Schema

### Users Table
- `user_id` (PRIMARY KEY): Telegram user ID
- `username`: Telegram username
- `balance`: User's current balance (default: 10)
- `last_earn`: Timestamp of last earning
- `is_owner`: Owner flag (1 for owner, 0 for regular users)
- `registered_date`: When the user first started the bot

### Transfers Table
- `id` (PRIMARY KEY): Auto-incrementing transfer ID
- `from_user_id`: Sender's user ID
- `from_username`: Sender's username
- `to_user_id`: Recipient's user ID
- `to_username`: Recipient's username
- `amount`: Amount of Драго transferred
- `transfer_date`: Timestamp of the transfer

### Bans Table
- `user_id` (PRIMARY KEY): Banned user's ID
- `username`: Banned user's username
- `banned_by`: Username of admin who issued the ban
- `ban_reason`: Reason for the ban
- `ban_date`: When the ban was issued

### Admins Table
- `user_id` (PRIMARY KEY): Admin's user ID
- `username`: Admin's username
- `appointed_by`: Username of main admin who appointed them
- `appointed_date`: When they were appointed

## How to Run
The bot runs automatically via the "Run Python App" workflow and listens continuously for Telegram messages.

## Moderation Features

### Ban System
- Admins can ban users with optional reason
- Banned users cannot use any bot commands
- Banned users receive notification when banned/unbanned
- Ban list includes: username, banned by, reason, and date
- Admins cannot ban other admins (except main admin can ban anyone)

### Admin Hierarchy
- **Main Admin** (@RYBBKA_MACO): Full control, can appoint/remove admins
- **Appointed Admins**: Can moderate users but cannot manage other admins
- Admins are notified when appointed or removed
- Complete admin list with appointment history

### Protection Features
- Users cannot ban themselves
- Admins cannot ban other admins (unless main admin)
- Cannot transfer Драго to banned users
- All commands check ban status before execution

## Note
The bot API token is currently hardcoded in main.py. For better security, consider moving it to environment variables.
