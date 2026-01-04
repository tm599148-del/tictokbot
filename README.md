# 🤖 TicTac Coupon Miner Telegram Bot

Multi-user Telegram bot for mining TicTac coupon codes with group verification system.

## Features

✅ **Multi-user support** - Multiple users can mine simultaneously  
✅ **Group verification** - Users must join group before using bot  
✅ **Real-time notifications** - Get notified when valid codes are found  
✅ **Admin panel** - Admin can see all valid codes from all users  
✅ **Statistics tracking** - Track checked codes and valid codes found  
✅ **Persistent storage** - All data saved in JSON format

## Bot Commands

- `/start` - Start the bot and verify group membership
- `/setphone 9876543210` - Set your phone number for mining

## User Features

- 🚀 **Start Mining** - Begin scanning codes automatically
- ⏹️ **Stop Mining** - Stop current mining session
- 📊 **My Stats** - View your statistics
- 💎 **My Valid Codes** - View all your valid codes

## Admin Features

- 👑 **Admin Panel** - Access admin dashboard
- 📊 **All Stats** - View all users' statistics
- 💎 **All Valid Codes** - View all valid codes from all users
- 👥 **User List** - List all registered users

## Setup for Render Deployment

### Environment Variables

Set these in Render dashboard:

```
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_admin_user_id
GROUP_LINK=https://t.me/your_group
GROUP_USERNAME=your_group_username
```

### Build Command

```bash
pip install -r requirements.txt
```

### Start Command

```bash
python telegram_bot.py
```

## Local Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables or edit `telegram_bot.py`:
```python
BOT_TOKEN = "your_bot_token"
ADMIN_ID = your_admin_id
GROUP_LINK = "https://t.me/your_group"
GROUP_USERNAME = "your_group_username"
```

3. Run the bot:
```bash
python telegram_bot.py
```

## Configuration

Edit `telegram_bot.py` to customize:

- `NUM_THREADS` - Number of threads per user (default: 10)
- `DELAY_PER_REQUEST` - Delay between requests in seconds (default: 0.5)
- `START_WITH_D` - Generate codes starting with 'D' (default: True)

## Data Storage

- User data stored in `bot_data.json`
- Valid codes saved per user
- Verification status tracked
- Statistics maintained per user

## Requirements

- Python 3.8+
- python-telegram-bot >= 20.0
- requests >= 2.31.0

## License

Private project

## Support

For issues or questions, contact the admin.
