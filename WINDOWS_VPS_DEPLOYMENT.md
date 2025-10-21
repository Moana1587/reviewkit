# 🪟 Windows VPS Deployment Guide

Complete guide to deploy ReviewKit on a Windows Server VPS.

---

## 🚀 Quick Start (3 Steps)

### Step 1: Setup (One Time)
On your Windows VPS, run:
```batch
setup_windows_vps.bat
```

### Step 2: Configure
Edit `.env` file with your credentials

### Step 3: Start Server
Double-click:
```batch
start_server.bat
```

**Done!** Your app is now accessible at `http://YOUR_VPS_IP:8000`

---

## 📋 Detailed Setup Instructions

### Prerequisites

**On Windows VPS:**
1. **Python 3.8+** installed
   - Download from: https://www.python.org/downloads/
   - ✅ Check "Add Python to PATH" during installation
2. **Git** installed (optional, for cloning)
   - Download from: https://git-scm.com/download/win
3. **Admin access** (for firewall configuration)

---

### Method 1: Clone from GitHub (Recommended)

1. **Connect to your Windows VPS**
   - Use Remote Desktop (RDP)
   - Address: Your VPS IP
   - Username/Password: From your VPS provider

2. **Open PowerShell or Command Prompt**

3. **Clone the repository:**
   ```batch
   cd C:\
   git clone https://github.com/Moana1587/reviewkit.git
   cd reviewkit
   ```

4. **Run setup script:**
   ```batch
   setup_windows_vps.bat
   ```

5. **Edit .env file:**
   - Open: `C:\reviewkit\.env`
   - Update `DB_PASSWORD` and `OPEN_AI_KEY`
   - Save and close

6. **Start the server:**
   ```batch
   start_server.bat
   ```

7. **Access from browser:**
   ```
   http://YOUR_VPS_IP:8000
   ```

---

### Method 2: Upload Files Manually

1. **Connect to VPS via RDP**

2. **Create project folder:**
   ```batch
   mkdir C:\reviewkit
   ```

3. **Upload your project files:**
   - Use File Explorer to copy files
   - Or use FTP client (FileZilla)
   - Copy all files to `C:\reviewkit`

4. **Run setup:**
   ```batch
   cd C:\reviewkit
   setup_windows_vps.bat
   ```

5. **Configure and start** (same as Method 1 steps 5-7)

---

## 🎯 What Each Script Does

### `setup_windows_vps.bat` (Run Once)
- ✅ Checks Python installation
- ✅ Creates virtual environment
- ✅ Installs all dependencies
- ✅ Creates .env template
- ✅ Opens Windows Firewall port 8000
- ✅ Creates desktop shortcut

### `start_server.bat` (Run Every Time)
- ✅ Activates virtual environment
- ✅ Updates dependencies if needed
- ✅ Starts Flask server on 0.0.0.0:8000
- ✅ Makes app publicly accessible

### `start_server_public.bat` (Quick Start)
- Simplified startup script
- Use after initial setup

---

## 🔧 Configuration

### Edit .env File

Location: `C:\reviewkit\.env`

```env
# MySQL Database
HOST=35.214.36.137
DB_PORT=3306
DB_USER=ursajda4eqbre
DB_PASSWORD=YOUR_ACTUAL_MYSQL_PASSWORD
DB_NAME=dbhvo6177kzjng

# OpenAI API Key
OPEN_AI_KEY=YOUR_ACTUAL_OPENAI_API_KEY

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=CHANGE_THIS_TO_RANDOM_STRING
```

⚠️ **Replace the placeholder values with your actual credentials!**

---

## 🔥 Windows Firewall Configuration

### Automatic (Recommended)
The setup script automatically configures the firewall.

### Manual Configuration
If needed, open port 8000 manually:

1. **Open Windows Firewall:**
   - Start → Windows Defender Firewall with Advanced Security

2. **Add Inbound Rule:**
   - Inbound Rules → New Rule
   - Rule Type: Port
   - Protocol: TCP
   - Port: 8000
   - Action: Allow the connection
   - Profile: All (Domain, Private, Public)
   - Name: ReviewKit Flask App

3. **Click Finish**

---

## 🌐 Making Your App Accessible

### Find Your VPS IP Address

**Method 1: PowerShell**
```powershell
(Invoke-WebRequest -Uri "https://api.ipify.org").Content
```

**Method 2: Command Prompt**
```batch
ipconfig
```
Look for "IPv4 Address"

### Access URLs

**From anywhere:**
```
http://YOUR_VPS_IP:8000
```

**From VPS itself:**
```
http://localhost:8000
http://127.0.0.1:8000
```

---

## 🔄 Running as a Windows Service (Optional)

To keep the app running even when you log out:

### Using NSSM (Non-Sucking Service Manager)

1. **Download NSSM:**
   - https://nssm.cc/download

2. **Install as service:**
   ```batch
   nssm install ReviewKit "C:\reviewkit\venv\Scripts\python.exe" "C:\reviewkit\app\app.py --host 0.0.0.0 --port 8000"
   ```

3. **Set working directory:**
   ```batch
   nssm set ReviewKit AppDirectory "C:\reviewkit"
   ```

4. **Start service:**
   ```batch
   nssm start ReviewKit
   ```

5. **Configure auto-start:**
   - Services → ReviewKit → Properties
   - Startup type: Automatic

### Service Commands
```batch
# Start
nssm start ReviewKit

# Stop
nssm stop ReviewKit

# Restart
nssm restart ReviewKit

# Remove
nssm remove ReviewKit
```

---

## 📊 Monitoring & Management

### View Running Status

**Check if server is running:**
```batch
netstat -ano | findstr :8000
```

### View Logs

Logs are shown in the console window where you ran `start_server.bat`

### Restart Server

1. Press `Ctrl+C` in server window
2. Run `start_server.bat` again

---

## 🐛 Troubleshooting

### Error: "Python is not installed"

**Solution:**
1. Download Python: https://www.python.org/downloads/
2. Run installer
3. ✅ Check "Add Python to PATH"
4. Restart Command Prompt
5. Verify: `python --version`

---

### Error: "Port 8000 is already in use"

**Solution:**
Find and kill the process:
```batch
netstat -ano | findstr :8000
taskkill /PID [PID_NUMBER] /F
```

---

### Error: "Cannot connect from browser"

**Possible causes:**

1. **Firewall blocking:**
   - Run `setup_windows_vps.bat` as Administrator
   - Or manually configure firewall (see above)

2. **Cloud provider firewall:**
   - Check your VPS provider's security groups
   - Add inbound rule for port 8000
   - Examples:
     - **AWS**: Security Groups → Edit Inbound Rules
     - **Azure**: Network Security Groups → Add rule
     - **Google Cloud**: VPC Firewall Rules

3. **Server not running:**
   - Make sure `start_server.bat` is running
   - Check for errors in console

---

### Error: "Database connection failed"

**Solutions:**

1. **Check .env file:**
   - Verify DB_PASSWORD is correct
   - Ensure no extra spaces

2. **Whitelist VPS IP in MySQL:**
   - Get your VPS public IP
   - Add it to MySQL allowed hosts

3. **Test connection:**
   - Create `test_connection.bat`:
     ```batch
     @echo off
     call venv\Scripts\activate.bat
     python -c "import pymysql; print('Testing...'); conn = pymysql.connect(host='35.214.36.137', user='ursajda4eqbre', password='YOUR_PASSWORD', database='dbhvo6177kzjng'); print('SUCCESS!'); conn.close()"
     pause
     ```

---

### Error: "Module not found"

**Solution:**
```batch
call venv\Scripts\activate.bat
pip install -r requirements.txt
```

---

## 🔐 Security Best Practices

### 1. Use Strong Passwords
- Don't use default passwords
- Use password manager

### 2. Restrict RDP Access
- Change default RDP port (3389)
- Use VPN or firewall rules
- Only allow trusted IPs

### 3. Keep Windows Updated
- Enable Windows Update
- Install security patches regularly

### 4. Use HTTPS (Production)
For production, use IIS with SSL:
- Install IIS
- Configure reverse proxy
- Install SSL certificate

### 5. Don't Expose .env
- Never share .env file
- Don't commit to git
- Use environment variables

---

## 📁 File Structure on Windows VPS

```
C:\reviewkit\
├── app\
│   ├── app.py                 # Main Flask application
│   ├── tools.py               # Helper functions
│   ├── pdf.py                 # PDF generation
│   ├── templates\             # HTML templates
│   ├── storage\               # File uploads
│   └── instance\              # SQLite database
├── venv\                      # Virtual environment
├── .env                       # Configuration (KEEP SECRET!)
├── requirements.txt           # Python dependencies
├── setup_windows_vps.bat      # Initial setup
├── start_server.bat           # Start server
└── start_server_public.bat    # Quick start
```

---

## 💰 Windows VPS Providers

| Provider | Price/Month | Features |
|----------|-------------|----------|
| **AWS EC2** | $10-30 | Windows Server, Free tier available |
| **Azure** | $15-40 | Windows Server, Student credits |
| **Google Cloud** | $20-50 | Windows Server, $300 credit |
| **Vultr** | $10-20 | Windows Server 2019/2022 |
| **DigitalOcean** | N/A | Linux only |

---

## ✅ Deployment Checklist

- [ ] Windows VPS created
- [ ] Connected via RDP
- [ ] Python installed (with PATH)
- [ ] Project files uploaded/cloned
- [ ] Ran `setup_windows_vps.bat`
- [ ] Edited `.env` with real credentials
- [ ] Windows Firewall port 8000 open
- [ ] Cloud firewall configured (if applicable)
- [ ] Started server with `start_server.bat`
- [ ] Tested access from browser
- [ ] (Optional) Configured as Windows Service
- [ ] (Optional) Setup custom domain

---

## 🎉 Success!

Once deployed, your ReviewKit app will be accessible at:

```
http://YOUR_VPS_IP:8000
```

Anyone on the internet can now access your application!

---

## 📞 Need Help?

**Check logs in console window**

**Test individual components:**
```batch
# Test Python
python --version

# Test virtual environment
venv\Scripts\activate.bat

# Test app directly
cd app
python app.py
```

**Common issues:**
- Firewall blocking → Configure Windows Firewall
- Port in use → Kill process on port 8000
- Module errors → Reinstall dependencies
- Database errors → Check .env credentials

---

**Happy Deploying! 🚀**

