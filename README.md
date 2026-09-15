# Gmail Creator Bot - Railway Ready

Telegram bot for automated Gmail account creation.

## 🚀 Deploy to Railway

### Method 1: One-Click Deploy
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

### Method 2: Manual Deploy

1. **Fork/Upload this repo to GitHub**

2. **Connect to Railway:**
   - Go to [Railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repo

3. **Add Environment Variables:**
   ```
   BOT_TOKEN=your_telegram_bot_token
   OWNER_ID=your_telegram_id
   ```

4. **Deploy!**
   - Railway will auto-build and deploy
   - Bot will start automatically

## 📁 Files

```
gmail-creator/
├── bot.py              # Main bot
├── config.py           # Configuration
├── database.py         # SQLite database
├── proxy_manager.py    # Proxy handling
├── gmail_engine.py     # Gmail automation
├── requirements.txt    # Python dependencies
├── Procfile           # Railway worker
├── runtime.txt        # Python version
├── nixpacks.toml      # Build config
├── railway.toml       # Railway config
└── .env.example       # Environment template
```

## 🎯 Features

- ✅ Auto-generate Gmail accounts (1-10 batch)
- ✅ Custom account creation
- ✅ Proxy manager (add, validate, rotate)
- ✅ Stop/Resume/Pause controls
- ✅ Google blocking detection
- ✅ Phone verification handling
- ✅ Debug screenshots
- ✅ Access key system

## 🌐 Proxy Setup

Add residential proxies in format:
```
host:port:username:password
```

## 📱 Usage

1. Send `/start` to bot
2. Choose Auto-Generate or Custom
3. Add proxies (residential recommended)
4. Start creating accounts!

## ⚠️ Important

- Use **residential proxies** (datacenter blocked by Google)
- Phone verification is **normal** for new accounts
- Wait 24h between batches

## 🛠️ Troubleshooting

**Bot not starting?**
- Check BOT_TOKEN is correct
- Check OWNER_ID is correct
- View logs: `railway logs`

**Google blocking?**
- Add residential proxies
- Rotate proxies

---

**Ready to deploy on Railway!**
