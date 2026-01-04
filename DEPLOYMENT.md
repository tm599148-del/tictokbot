# Render Deployment Guide

## Fix for "ModuleNotFoundError: No module named 'requests'"

### Solution: Set Build Command in Render Dashboard

1. Go to your Render Dashboard
2. Select your service (tictokbot)
3. Go to **Settings** tab
4. Scroll to **Build & Deploy** section
5. Set **Build Command** to:
   ```
   pip install -r requirements.txt
   ```
6. Set **Start Command** to:
   ```
   python telegram_bot.py
   ```
7. Click **Save Changes**
8. Go to **Manual Deploy** and click **Deploy latest commit**

### Alternative: Use render.yaml (Already Added)

The repository includes `render.yaml` which should auto-configure:
- Build Command: `pip install -r requirements.txt`
- Start Command: `python telegram_bot.py`

### Environment Variables

Make sure to set these in Render Dashboard → Environment:

```
BOT_TOKEN=8208170457:AAEznHYzZw6VDSjrK5VDoL88rVwuEUGVi_A
ADMIN_ID=7200333065
GROUP_LINK=https://t.me/shien_help
GROUP_USERNAME=shien_help
```

### Troubleshooting

If dependencies still don't install:

1. Check **Build Logs** in Render Dashboard
2. Make sure `requirements.txt` exists in root directory
3. Try manual build: SSH into container and run `pip install -r requirements.txt`
4. Verify Python version (should be 3.12+)

### Required Files

- ✅ `requirements.txt` - Dependencies list
- ✅ `Procfile` - Process command
- ✅ `render.yaml` - Auto-configuration
- ✅ `telegram_bot.py` - Main bot file
