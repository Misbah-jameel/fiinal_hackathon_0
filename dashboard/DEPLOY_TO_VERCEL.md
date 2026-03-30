# 🚀 Deploy Dashboard to Vercel - Step by Step

## 📋 Pre-requisites

- Node.js installed (already have ✅)
- GitHub account (already have ✅)
- Vercel account (free - sign up at vercel.com)

---

## 🎯 Method 1: Deploy from GitHub (Easiest!)

### Step 1: Push Dashboard to GitHub

```bash
# Already done! Your repo is at:
https://github.com/Misbah-jameel/fiinal_hackathon_0
```

### Step 2: Deploy on Vercel

1. **Go to** [vercel.com](https://vercel.com)
2. **Sign up/Login** with GitHub
3. **Click "Add New Project"**
4. **Import Git Repository**
   - Select: `Misbah-jameel/fiinal_hackathon_0`
   - Framework Preset: `Other`
   - Root Directory: `dashboard`
5. **Click "Deploy"**

### Step 3: Get Your URL

```
✅ Live at: https://fiinal-hackathon-0.vercel.app
```

---

## 🎯 Method 2: Deploy with CLI

### Step 1: Login to Vercel

```bash
vercel login
```

This will open browser - complete authentication.

### Step 2: Deploy

```bash
cd D:\fiinal_hackathon_0\dashboard
vercel --prod
```

### Step 3: Confirm Deployment

```
✅ Production: https://your-project.vercel.app
```

---

## ⚙️ Configuration

### Update API Connection

After deployment, the dashboard needs to connect to your backend.

**Option A: Connect to VM Backend**

Edit `dashboard/public/index.html` line ~150:

```javascript
const API_BASE = 'http://YOUR-VM-IP:5000';  // Your VM public IP
```

**Option B: Use Environment Variable**

```bash
vercel env add API_BASE http://YOUR-VM-IP:5000
vercel --prod
```

---

## 🔐 CORS Setup (Important!)

If you get CORS errors, update `dashboard/app.py`:

```python
from flask_cors import CORS

# Allow Vercel domain
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://*.vercel.app"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allowed_headers": ["Content-Type"]
    }
})
```

Then push to GitHub:

```bash
git add .
git commit -m "Enable CORS for Vercel"
git push origin main
```

Vercel will auto-deploy!

---

## 🌐 Access URLs

After deployment:

| Component | URL |
|-----------|-----|
| **Frontend (Vercel)** | `https://fiinal-hackathon-0.vercel.app` |
| **Backend (VM)** | `http://YOUR-VM-IP:5000` |

---

## 📊 Auto-Deploy on Git Push

Vercel automatically deploys when you push to GitHub!

```bash
# Make changes
git add .
git commit -m "Update dashboard"
git push origin main

# Vercel will auto-deploy in ~30 seconds
```

---

## 🎨 Custom Domain (Optional)

1. Go to Vercel Dashboard
2. Select your project
3. Settings → Domains
4. Add your domain: `dashboard.yourdomain.com`

---

## 🆘 Troubleshooting

### Build Failed

```
Error: Missing vercel.json
```

**Fix:** Make sure `vercel.json` is in `dashboard/` folder

### API Not Working

```
Failed to fetch from /api/status
```

**Fix:** 
- Check API_BASE URL
- Ensure backend is running
- Check CORS settings

### Blank Page

**Fix:**
- Open browser console (F12)
- Check for errors
- Verify `index.html` path in vercel.json

---

## ✅ Success Checklist

- [ ] Vercel account created
- [ ] Project deployed
- [ ] Dashboard loads at vercel.app URL
- [ ] API connection working
- [ ] No CORS errors in console

---

## 🎉 Done!

Your dashboard is now:

- ✅ Hosted on global CDN
- ✅ Auto-deploys on git push
- ✅ HTTPS enabled
- ✅ Accessible from anywhere

**Share your dashboard URL with your team!**

---

*For AI Employee Gold Tier*
