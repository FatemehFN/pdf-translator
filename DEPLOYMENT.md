# Deployment Guide - PDF to Farsi Translator

## 🚀 Deploy to Render (Free & Easy)

Follow these steps to deploy your app and get a public URL:

### Step 1: Prepare Your Code

1. **Create a GitHub account** (if you don't have one):
   - Go to https://github.com and sign up

2. **Create a new repository**:
   - Click the "+" icon → "New repository"
   - Name it: `pdf-translator` (or any name you like)
   - Set it to **Public** or **Private** (both work)
   - Click "Create repository"

3. **Upload your code to GitHub**:
   
   Open Terminal and run these commands in your project folder:
   
   ```bash
   cd /Users/fsfatemi/Translate_chat_bot
   
   # Initialize git (if not already done)
   git init
   
   # Add all files
   git add .
   
   # Commit the files
   git commit -m "Initial commit - PDF translator app"
   
   # Connect to your GitHub repository (replace YOUR_USERNAME and YOUR_REPO)
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   
   # Push to GitHub
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy to Render

1. **Create a Render account**:
   - Go to https://render.com
   - Click "Get Started for Free"
   - Sign up with your GitHub account (easier!)

2. **Create a new Web Service**:
   - Click "New +" button
   - Select "Web Service"
   - Connect your GitHub repository (`pdf-translator`)
   - Click "Connect"

3. **Configure the service**:
   - **Name**: `pdf-translator` (or your choice)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Instance Type**: Select "Free"

4. **Click "Create Web Service"**

5. **Wait for deployment** (5-10 minutes):
   - Render will build and deploy your app
   - You'll see logs showing the progress
   - When done, you'll get a URL like: `https://pdf-translator-xxxx.onrender.com`

### Step 3: Share Your URL

✅ That's it! Share your Render URL with anyone:
- `https://your-app-name.onrender.com`

They can:
- Visit the URL
- Upload their PDF
- Get translated HTML files
- Your API key is used automatically (it's in the code)

---

## 🎯 Alternative: Deploy to Railway (Also Free)

If you prefer Railway:

1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway auto-detects Python and deploys
6. Get your URL: `https://your-app.railway.app`

---

## 🎯 Alternative: Deploy to PythonAnywhere (Free Tier)

1. Go to https://www.pythonanywhere.com
2. Sign up for free account
3. Go to "Web" tab → "Add a new web app"
4. Choose "Flask" and Python 3.10
5. Upload your files via "Files" tab
6. Configure to point to your `app.py`
7. Get URL: `https://yourusername.pythonanywhere.com`

---

## ⚠️ Important Notes

### API Key Security
Your Gemini API key is currently hardcoded in `app.py`. For better security:

1. **Option 1 - Keep as is** (easiest):
   - The key stays in your code
   - Only you can see the code on GitHub if it's private
   - Works fine for personal use

2. **Option 2 - Use environment variables** (more secure):
   - On Render, go to "Environment" tab
   - Add: `GEMINI_API_KEY` = `your-key-here`
   - Update `app.py` to use: `API_KEY = os.environ.get('GEMINI_API_KEY', 'fallback-key')`

### Free Tier Limitations

**Render Free Tier:**
- ✅ Free forever
- ⚠️ App "sleeps" after 15 minutes of inactivity
- ⚠️ Takes ~30 seconds to wake up on first request
- ✅ 750 hours/month of runtime

**Railway Free Tier:**
- ✅ $5 credit per month (usually enough)
- ✅ No sleep mode
- ⚠️ Billing required after trial

### Keeping Your App Awake

If you're using Render and don't want the sleep delay:

1. Use a service like **UptimeRobot** (free):
   - Go to https://uptimerobot.com
   - Add your Render URL
   - It pings every 5 minutes
   - Keeps app awake 24/7

2. Or upgrade to Render's paid plan ($7/month) for no sleep

---

## 📱 Testing Your Deployment

After deployment, test it:

1. Visit your URL
2. Upload a test PDF
3. Check if translation works
4. Download the HTML file
5. Share the URL with others!

---

## 🔧 Troubleshooting

**App won't start:**
- Check Render logs for errors
- Verify all files are pushed to GitHub
- Make sure `requirements.txt` is present

**Upload fails:**
- Check file size (under 16MB)
- Verify PDF is valid
- Check API key is correct

**Slow first load:**
- Normal on Render free tier (app sleeping)
- Wait 30 seconds and refresh
- Consider using UptimeRobot

---

## 🎉 You're Done!

Your app is now live on the internet! Share your URL with anyone who needs PDF translations.

**Example URL to share:**
```
https://pdf-translator-xxxx.onrender.com
```

Anyone with this link can:
- Upload their PDF
- Get Farsi translation
- Download HTML file
- All using YOUR Gemini API key automatically
