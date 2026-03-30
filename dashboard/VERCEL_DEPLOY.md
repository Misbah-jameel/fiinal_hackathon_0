# 🚀 Vercel Deployment Guide - AI Employee Dashboard

## ⚡ Quick Deploy

### Option 1: Deploy to Vercel (Recommended)

**Step 1: Install Vercel CLI**
```bash
npm install -g vercel
```

**Step 2: Login to Vercel**
```bash
vercel login
```

**Step 3: Deploy Dashboard**
```bash
cd dashboard
vercel --prod
```

**Step 4: Get Your URL**
```
https://your-dashboard.vercel.app
```

---

## 🔧 Configuration

### Update API Base URL

After deployment, update the dashboard to connect to your VM backend:

**Edit `index.html` line ~150:**
```javascript
const API_BASE = 'https://your-vm-ip:5000';  // Your VM public IP
```

Or use environment variable:
```bash
vercel env add API_BASE https://your-vm-ip:5000
```

---

## 🌐 Access Options

### Option A: Vercel Frontend + VM Backend
```
Frontend: https://your-dashboard.vercel.app
Backend:  http://your-vm-ip:5000
```

**Pros:**
- ✅ Fast global CDN (Vercel)
- ✅ Always online frontend
- ✅ Your backend stays private

**Cons:**
- ⚠️ Need public IP for backend
- ⚠️ CORS configuration needed

---

### Option B: Local Deployment (Current)
```
Frontend: http://localhost:5000
Backend:  http://localhost:5000
```

**Pros:**
- ✅ Everything local
- ✅ No configuration needed
- ✅ Fast development

**Cons:**
- ⚠️ Only accessible on VM
- ⚠️ Need to keep terminal open

---

## 🔐 CORS Setup (For Option A)

If deploying frontend to Vercel, update `dashboard/app.py`:

```python
from flask_cors import CORS

# Allow your Vercel domain
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://your-dashboard.vercel.app"],
        "methods": ["GET", "POST"]
    }
})
```

---

## 📝 Environment Variables

Create `.env` in dashboard folder:
```env
VITE_API_BASE=http://localhost:5000
```

For production:
```env
VITE_API_BASE=https://your-vm-public-ip:5000
```

---

## 🚨 Important Notes

### VM Backend Requirements

For Vercel frontend to connect to your VM:

1. **Public IP or Port Forwarding**
   - Your VM needs a public IP
   - Or setup port forwarding for port 5000

2. **Firewall Rules**
   - Allow inbound traffic on port 5000
   - Windows Firewall: Add inbound rule

3. **Static IP (Recommended)**
   - Dynamic IP changes = broken dashboard
   - Use static IP or DNS service

---

## 🎯 Recommended Setup

**For Production:**
```
1. Deploy Backend to Cloud (Render/Railway/AWS)
2. Deploy Frontend to Vercel
3. Both accessible via HTTPS
```

**For Development:**
```
Keep everything local on VM:
python dashboard/app.py
http://localhost:5000
```

---

## 📊 Alternative: Deploy Both to Vercel

Vercel supports Python backends! 

**Structure:**
```
dashboard/
├── api/
│   └── status.py      # API endpoints
├── public/
│   └── index.html     # Frontend
├── vercel.json
└── package.json
```

**Deploy:**
```bash
vercel --prod
```

---

## 🆘 Troubleshooting

### CORS Error
```
Access to fetch at 'http://vm-ip:5000' from origin 'https://vercel.app' has been blocked by CORS policy
```

**Fix:** Add CORS headers in `app.py` (see above)

### Connection Timeout
```
Failed to fetch
```

**Fix:** 
- Check VM is accessible from internet
- Port 5000 is open
- Use HTTPS in production

### API Not Found
```
404 Not Found
```

**Fix:** Check API_BASE URL is correct

---

## 🎉 Success!

After deployment, you'll have:

```
✅ Global CDN for frontend
✅ Fast loading worldwide
✅ Auto HTTPS
✅ Auto deployments on git push
```

**Dashboard URL:** `https://your-project.vercel.app`

---

*For AI Employee Gold Tier*
