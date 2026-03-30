# AI Employee Dashboard - Setup & Run Guide

## 🚀 Quick Start

### Option 1: One-Click Start (Windows)
```bash
cd D:\fiinal_hackathon_0\dashboard
start.bat
```

### Option 2: Manual Start
```bash
cd D:\fiinal_hackathon_0\dashboard
pip install -r requirements.txt
python app.py
```

### Step 3: Open in Browser
```
Local:   http://localhost:5000
Network: http://YOUR-VM-IP:5000
```

---

## 🌐 Access from Network (VM)

The server runs on `0.0.0.0:5000` by default, accessible from any device on your network.

**Find your VM IP:**
```bash
# Windows
ipconfig

# Look for IPv4 Address, e.g., 192.168.1.100
```

**Access from other devices:**
```
http://192.168.1.100:5000
```

---

## 🔧 Configuration

Edit `.env` in the project root:

```env
# Dashboard Settings
VAULT_PATH=D:/fiinal_hackathon_0/AI_Employee_Vault
DRY_RUN=true  # Set to false for real actions
```

---

## 📁 Project Structure

```
dashboard/
├── app.py              # Flask backend API
├── package.json        # React dependencies
├── requirements.txt    # Python dependencies
├── public/
│   └── index.html      # HTML template
├── src/
│   ├── App.js          # Main React component
│   ├── index.js        # React entry point
│   └── index.css       # Styles
└── build/              # Built React app (after npm run build)
```

---

## 🎯 Features

| Feature | Description |
|---------|-------------|
| **Vault Status** | Live counts of all folders |
| **Pending Approvals** | View, Approve, Reject items |
| **Needs Action** | View items requiring attention |
| **Watcher Health** | Online/Offline status of all watchers |
| **File Viewer** | View any vault file in modal |
| **Auto Refresh** | Updates every 30 seconds |
| **DRY_RUN Mode** | Safe mode enabled by default |

---

## 🛠️ Troubleshooting

### Port 5000 already in use
```bash
# Change port in app.py
app.run(host='0.0.0.0', port=5001)
```

### React build fails
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### API not responding
```bash
# Check if Flask is running
# Look for: "Starting server..." message

# Check vault path in .env
```

---

## 📝 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Overall system status |
| `/api/vault/status` | GET | Vault folder counts |
| `/api/approvals` | GET | Pending approvals list |
| `/api/needs-action` | GET | Items needing action |
| `/api/watchers` | GET | Watcher health status |
| `/api/approve/<id>` | POST | Approve an item |
| `/api/reject/<id>` | POST | Reject an item |
| `/api/file/<path>` | GET | Get file content |

---

## 🔐 Security Notes

- **DRY_RUN=true** by default - no real actions
- All actions logged to `/Logs/dashboard.md`
- Only vault files accessible (path validation)
- CORS enabled for local development

---

*Built for AI Employee Gold Tier*
