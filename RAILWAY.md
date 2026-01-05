## Railway Deployment Guide

1. Push latest code (already done). Repo: `tm599148-del/tictokbot`.
2. Create new Railway project → Deploy from GitHub → select repo.
3. Railway will detect `Dockerfile` automatically.
4. Environment variables (Project → Variables):
   ```
   BOT_TOKEN=8208170457:AAEznHYzZw6VDSjrK5VDoL88rVwuEUGVi_A
   ADMIN_ID=7200333065
   GROUP_LINK=https://t.me/+w7VwgotOFrRkNTM1
   GROUP_USERNAME=w7VwgotOFrRkNTM1
   START_PREFIXES=T,D
   ```
5. Deploy. Logs should show “Bot is running! Press Ctrl+C to stop.”

### Manual command override (optional)
If Railway asks for start command, set `python telegram_bot.py`.
