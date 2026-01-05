# 🤖 TicTac Coupon Miner Telegram Bot

Multi-user Telegram bot for mining TicTac coupon codes.

## Features

✅ **Multi-user support** - Multiple users can mine simultaneously  
✅ **User accounts** - Each user has their own valid codes  
✅ **Real-time notifications** - Get notified when valid codes are found  
✅ **Admin panel** - Admin can see all valid codes from all users  
✅ **Statistics** - Track checked codes and valid codes found  

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the bot:
```bash
python telegram_bot.py
```

## Bot Commands

- `/start` - Start the bot and see main menu
- `/setphone 9876543210` - Set your phone number for mining

## User Features

### Start Mining
- Click "🚀 Start Mining" to begin scanning codes
- Bot will notify you when valid codes are found
- Progress updates every 100 codes checked

### My Stats
- View your total checked codes
- View your valid codes count
- See current mining session stats

### My Valid Codes
- View all valid codes you've found
- Shows last 20 codes
- Codes are automatically saved

### Stop Mining
- Click "⏹️ Stop Mining" to stop current session
- Final stats will be sent when stopped

## Admin Features (Admin ID: 7200333065)

### Admin Panel
- View total users and total valid codes
- Access admin-only features

### All Stats
- View statistics from all users
- See each user's valid codes count
- See each user's total checked codes

### All Valid Codes
- View all valid codes from all users
- Shows which user found each code
- Last 30 codes displayed

### User List
- List all registered users
- See user IDs and code counts

## Configuration

Edit `telegram_bot.py` to change:
- `BOT_TOKEN` - Your Telegram bot token
- `ADMIN_ID` - Admin user ID
- `NUM_THREADS` - Number of threads per user (default: 10)
- `DELAY_PER_REQUEST` - Delay between requests (default: 0.5s)
- `START_PREFIXES` - Comma-separated letters to force coupon prefixes (default: `T,M`; leave empty for random)

## Data Storage

User data is stored in `bot_data.json`:
- Valid codes per user
- Total checked codes
- Phone numbers
- Usernames
- Creation timestamps

## Notes

- Each user needs to set their phone number using `/setphone`
- Valid codes are automatically saved to user's account
- Mining runs continuously until stopped
- Multiple users can mine simultaneously
- Each mining session shows a live status message with last checked code
- Live status includes a 0‑100 progress bar (with remaining checks) for current batch
- Users receive a summary message for every 10 valid codes they find
- Admin can access all users' data

## Support

If you encounter any issues, check:
1. Bot token is correct
2. Dependencies are installed
3. Internet connection is working
4. Bot has proper permissions
