# ReviewKit Backend 🚀

A Flask-based backend application for managing and analyzing customer reviews using AI (OpenAI GPT).

## ✨ Features

- 📝 Review management and storage
- 🤖 AI-powered review analysis using OpenAI
- 💾 Dual database support (SQLite for dev, MySQL for production)
- 📄 PDF report generation
- 🔒 Secure environment variable management
- 🌐 Production-ready for both Windows and Linux servers

---

## 🚀 Quick Start - Local Development

### Prerequisites
- Python 3.8+
- MySQL database (optional, uses SQLite by default)
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Moana1587/reviewkit.git
   cd reviewkit
   ```

2. **Create virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create .env file**
   ```env
   # MySQL Database
   HOST=your_mysql_host
   DB_PORT=3306
   DB_USER=your_mysql_user
   DB_PASSWORD=your_mysql_password
   DB_NAME=your_database_name
   
   # OpenAI
   OPEN_AI_KEY=your_openai_api_key
   ```

5. **Run the application**
   ```bash
   cd app
   python app.py
   ```

6. **Open in browser**
   ```
   http://localhost:8000
   ```

---

## 🌐 Production Deployment

### 🪟 Windows VPS Deployment (Recommended for Windows Server)

**On your Windows VPS, run ONE command:**

```batch
setup_windows_vps.bat
```

Then double-click:
```batch
start_server.bat
```

**Your app is now live at:** `http://YOUR_VPS_IP:8000`

📖 **Full guide:** [WINDOWS_VPS_DEPLOYMENT.md](WINDOWS_VPS_DEPLOYMENT.md)

#### Quick Windows Deployment Steps:
1. ✅ Connect to Windows VPS via RDP
2. ✅ Clone or upload project files
3. ✅ Run `setup_windows_vps.bat`
4. ✅ Edit `.env` with your credentials
5. ✅ Run `start_server.bat`
6. ✅ Access at `http://YOUR_VPS_IP:8000`

---

### 🐧 Linux VPS Deployment (Ubuntu/Debian)

**Coming soon** - For Linux servers, use traditional Flask deployment with Nginx + Gunicorn.

---

## 📁 Project Structure

```
reviewkit(backend)/
├── app/
│   ├── app.py                  # Main Flask application
│   ├── tools.py                # Utility functions
│   ├── pdf.py                  # PDF generation
│   ├── aifunction.py           # OpenAI integration
│   ├── templates/              # HTML templates
│   ├── storage/                # File storage (PDFs, reviews)
│   └── instance/               # SQLite database
│
├── venv/                       # Virtual environment (created by setup)
├── .env                        # Environment variables (not in git)
├── .gitignore                  # Git ignore rules
│
├── requirements.txt            # Python dependencies
│
├── setup_windows_vps.bat       # Windows VPS setup (ONE-TIME)
├── start_server.bat            # Start server (EVERY TIME)
├── start_server_public.bat     # Quick start alternative
│
├── WINDOWS_VPS_DEPLOYMENT.md   # Windows deployment guide
└── README.md                   # This file
```

---

## 🔌 API Endpoints

- `GET /` - Main interface
- `POST /chat` - AI chat endpoint for review analysis
- `POST /generate-pdf` - Generate PDF report for location
- Additional endpoints in `app/app.py`

---

## 🎯 Deployment Options Comparison

| Feature | Windows VPS | Linux VPS |
|---------|-------------|-----------|
| **Setup Complexity** | ⭐ Very Easy | ⭐⭐⭐ Moderate |
| **Setup Time** | 5 minutes | 15-30 minutes |
| **Best For** | Windows Server | Ubuntu/Debian |
| **Auto-start** | Optional (NSSM) | Systemd |
| **Web Server** | Direct Flask | Nginx + Gunicorn |
| **Cost** | $10-30/mo | $5-12/mo |
| **Performance** | Good | Excellent |

---

## 🔐 Environment Variables

Create a `.env` file:

```env
# MySQL Database Configuration
HOST=your_mysql_host
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=your_database

# OpenAI API Key
OPEN_AI_KEY=sk-your-openai-api-key

# Flask Configuration (optional)
FLASK_ENV=production
SECRET_KEY=your-random-secret-key
```

⚠️ **Never commit `.env` to git!** (already in `.gitignore`)

---

## 🛠️ Windows VPS - Batch Files

### `setup_windows_vps.bat` (Run Once)
Sets up everything automatically:
- ✅ Creates virtual environment
- ✅ Installs dependencies
- ✅ Configures Windows Firewall
- ✅ Creates .env template
- ✅ Creates desktop shortcut

### `start_server.bat` (Run Every Time)
Starts your server publicly:
- ✅ Activates virtual environment
- ✅ Starts Flask on 0.0.0.0:8000
- ✅ Makes app accessible to anyone

### `start_server_public.bat` (Alternative)
Quick start script for rapid deployment

---

## 📊 Making Your App Public

### Windows VPS:
```batch
# Just run this:
start_server.bat

# Access at:
http://YOUR_VPS_IP:8000
```

### From Local Machine:
```bash
# Run with public host
cd app
python app.py --host 0.0.0.0 --port 8000
```

⚠️ **Note:** Make sure your firewall allows port 8000!

---

## 🔥 Windows Firewall Configuration

### Automatic (Recommended):
The `setup_windows_vps.bat` script handles this automatically.

### Manual:
```batch
netsh advfirewall firewall add rule name="ReviewKit Flask App" dir=in action=allow protocol=TCP localport=8000
```

### For Cloud Providers:
Also configure cloud firewall (Security Groups):
- **AWS**: EC2 → Security Groups → Add Inbound Rule (TCP 8000)
- **Azure**: Network Security Group → Add Rule (TCP 8000)
- **Google Cloud**: VPC Firewall → Create Rule (TCP 8000)

---

## 🐛 Troubleshooting

### Can't access from browser?
1. Check if server is running
2. Verify Windows Firewall allows port 8000
3. Check cloud provider security groups
4. Confirm you're using VPS public IP

### Database connection fails?
1. Check `.env` credentials
2. Whitelist VPS IP in MySQL
3. Test connection manually

### Module not found?
```batch
venv\Scripts\activate.bat
pip install -r requirements.txt
```

---

## 💻 Development vs Production

### Development (Local):
```bash
cd app
python app.py
# Runs on http://localhost:8000
```

### Production (Windows VPS):
```batch
start_server.bat
# Runs on http://0.0.0.0:8000 (publicly accessible)
```

---

## 🔐 Security Best Practices

1. **Never commit `.env`** - Already in `.gitignore`
2. **Use strong passwords** - For database and API keys
3. **Keep dependencies updated** - Run `pip install -r requirements.txt --upgrade`
4. **Use HTTPS in production** - Configure IIS with SSL for Windows
5. **Whitelist IPs** - Restrict database access to VPS IP only
6. **Regular backups** - Backup database and storage folder

---

## 📦 VPS Requirements

**Minimum Specs:**
- 1GB RAM
- 1 CPU core
- 25GB storage
- Windows Server 2016+ or Ubuntu 20.04+

**Recommended Providers:**

**Windows VPS:**
- AWS EC2 ($10-30/mo)
- Azure ($15-40/mo)
- Vultr ($10-20/mo)

**Linux VPS:**
- DigitalOcean ($6/mo)
- Linode ($5/mo)

---

## ✅ Windows VPS Deployment Checklist

- [ ] Windows VPS created (AWS/Azure/Vultr)
- [ ] Connected via Remote Desktop (RDP)
- [ ] Python installed (with PATH)
- [ ] Git installed (optional)
- [ ] Project files uploaded/cloned
- [ ] Ran `setup_windows_vps.bat`
- [ ] Edited `.env` with real credentials
- [ ] Windows Firewall configured (auto by script)
- [ ] Cloud firewall configured (Security Groups)
- [ ] Started with `start_server.bat`
- [ ] Tested access: `http://VPS_IP:8000`
- [ ] (Optional) Setup as Windows Service
- [ ] (Optional) Configure custom domain

---

## 📚 Documentation

- **[WINDOWS_VPS_DEPLOYMENT.md](WINDOWS_VPS_DEPLOYMENT.md)** - Complete Windows deployment guide
- [Flask Documentation](https://flask.palletsprojects.com/)
- [OpenAI API Docs](https://platform.openai.com/docs/)

---

## 🎉 Success!

### After deployment, your app will be accessible at:

**Windows VPS:**
```
http://YOUR_VPS_IP:8000
```

**Anyone on the internet can now use your app!** 🌍

---

## 🆘 Need Help?

**For Windows deployment:**
- Check [WINDOWS_VPS_DEPLOYMENT.md](WINDOWS_VPS_DEPLOYMENT.md)
- Look at server console for errors

**For database issues:**
- Verify .env credentials
- Check MySQL allows remote connections
- Whitelist VPS IP in database

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Made with ❤️ for Windows and Linux servers**

🚀 **Ready to deploy? Run `setup_windows_vps.bat` on your Windows VPS!**
