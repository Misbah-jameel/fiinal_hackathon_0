# 🚀 Deploy Dashboard to Vercel - Complete Guide

## ✅ Ready to Deploy!

Your code is now on GitHub at:
**https://github.com/Misbah-jameel/fiinal_hackathon_0**

The `dashboard/` folder is ready for Vercel deployment.

---

## 📋 Step-by-Step Deployment

### Step 1: Go to Vercel

1. Open browser: **[vercel.com](https://vercel.com)**
2. Click **"Sign Up"** or **"Login"**
3. Choose **"Continue with GitHub"**
4. Authorize Vercel

### Step 2: Import Your Repository

1. Click **"Add New Project"**
2. Click **"Import Git Repository"**
3. Find: `Misbah-jameel/fiinal_hackathon_0`
4. Click **"Import"**

### Step 3: Configure Project

```
Framework Preset: Other
Root Directory: dashboard
Build Command: (leave empty)
Output Directory: public
Install Command: (leave empty)
```

### Step 4: Deploy!

1. Click **"Deploy"**
2. Wait ~30 seconds
3. ✅ **Success!**

### Step 5: Get Your URL

```
🎉 Your dashboard is live at:
https://fiinal-hackathon-0.vercel.app
```

---

## 🎯 What You Get

### ✅ Features:

- **Global CDN** - Fast loading worldwide
- **Auto HTTPS** - Secure by default
- **Auto Deploy** - Push to GitHub = auto deploy
- **Free Hosting** - No credit card needed
- **Custom Domain** - Add your own domain

### 📊 Dashboard Preview:

The deployed dashboard will show:
- ✅ Vault status cards
- ✅ Watcher health monitoring
- ✅ Pending approvals list
- ✅ Demo data (until backend connected)

---

## 🔗 Connect to Backend (Optional)

The Vercel deployment uses **demo data** by default. To connect to your VM backend:

### Option 1: Edit index.html

Find line ~150 in `dashboard/public/index.html`:

```javascript
const API_BASE = window.location.hostname === 'localhost' 
    ? 'http://localhost:5000' 
    : 'http://YOUR-VM-IP:5000';  // ← Replace this
```

Change to:
```javascript
const API_BASE = 'http://YOUR-VM-PUBLIC-IP:5000';
```

Then push to GitHub:
```bash
git add .
git commit -m "Update API base URL"
git push origin main
```

Vercel will auto-deploy in ~30 seconds!

### Option 2: Use Environment Variables

In Vercel dashboard:
1. Settings → Environment Variables
2. Add: `API_BASE` = `http://YOUR-VM-IP:5000`
3. Redeploy

---

## ⚙️ VM Backend Requirements

For the dashboard to connect to your backend:

### 1. Public IP Address

Your VM needs a public IP or:
- Port forwarding on router
- Ngrok tunnel
- Cloudflare tunnel

### 2. Open Port 5000

Windows Firewall:
```
New Inbound Rule → Port 5000 → Allow
```

### 3. CORS Configuration

Update `dashboard/app.py`:

```python
from flask_cors import CORS

# Allow Vercel
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://*.vercel.app"],
        "methods": ["GET", "POST", "OPTIONS"]
    }
})
```

---

## 🎨 Customization

### Change Dashboard Title

Edit `dashboard/public/index.html` line 8:

```html
<title>My AI Employee Dashboard</title>
```

### Change Colors

Edit CSS in `dashboard/public/index.html`:

```css
body {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    /* Change these colors! */
}
```

### Add Logo

Add logo image to `dashboard/public/` and update header.

---

## 📱 Access from Anywhere

After deployment:

| Device | URL |
|--------|-----|
| Desktop | https://fiinal-hackathon-0.vercel.app |
| Mobile | Same URL (responsive!) |
| Tablet | Same URL (responsive!) |

---

## 🔄 Auto-Deploy on Git Push

Every time you push to GitHub:

```bash
git add .
git commit -m "Update dashboard"
git push origin main
```

Vercel will:
1. Detect push
2. Build dashboard
3. Deploy automatically
4. Update live URL

**No manual deployment needed!**

---

## 🆘 Troubleshooting

### Dashboard Shows "Loading..." Forever

**Fix:** Check browser console (F12)
- If CORS error → Enable CORS in backend
- If network error → Check VM is accessible

### Blank Page

**Fix:** 
- Check Vercel build logs
- Verify `public/` folder exists
- Check `index.html` path

### API Not Working

**Fix:**
- Verify API_BASE URL
- Check backend is running
- Test: `curl http://YOUR-VM-IP:5000/api/status`

---

## 🎉 Success Checklist

- [ ] Vercel account created
- [ ] Project deployed
- [ ] Dashboard loads at vercel.app URL
- [ ] Can see stats cards
- [ ] Can see watcher health
- [ ] (Optional) Backend connected

---

## 📞 Need Help?

### Vercel Documentation
- [Deploy Guide](https://vercel.com/docs/deployments)
- [Environment Variables](https://vercel.com/docs/environment-variables)
- [Custom Domains](https://vercel.com/docs/custom-domains)

### Your Project
- Backend: Running on VM at `http://localhost:5000`
- Frontend: Deployed at `https://fiinal-hackathon-0.vercel.app`
- GitHub: `https://github.com/Misbah-jameel/fiinal_hackathon_0`

---

## 🎊 Congratulations!

Your AI Employee Dashboard is now:

✅ **Live on Vercel**
✅ **Accessible worldwide**
✅ **Auto-deploying**
✅ **Free hosting**
✅ **HTTPS secured**

**Share your dashboard URL with your team!**

---

*Built with ❤️ for AI Employee Gold Tier*

**Dashboard Version:** 1.0.0  
**Deployed:** 2026-03-30  
**Status:** ✅ Production Ready on Vercel
