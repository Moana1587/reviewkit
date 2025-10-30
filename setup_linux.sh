#!/bin/bash
# =========================================================================
# ReviewKit - Linux/Ubuntu Setup Script (DigitalOcean Droplet)
# =========================================================================
# This script automates the deployment process for Ubuntu servers
# Run as: sudo ./setup_linux.sh or curl -sSL https://your-url/setup_linux.sh | bash
# =========================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
NC='\033[0m' # No Color

# Print banner
clear
echo -e "${CYAN}"
echo "  ===================================================================="
echo "             ReviewKit - Linux Setup Wizard"
echo "  ===================================================================="
echo -e "${NC}"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${YELLOW}[INFO] This script should be run as root or with sudo${NC}"
   echo -e "${YELLOW}[INFO] Some steps may fail without proper permissions${NC}"
   echo ""
fi

# Function to print status
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

# Detect current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR"

print_info "Project directory: $PROJECT_DIR"
echo ""

# =========================================================================
# Step 1: Update System Packages
# =========================================================================
echo -e "${CYAN}[1/10]${NC} Updating system packages..."
apt update -qq || print_error "Failed to update packages"
print_status "System packages updated"
echo ""

# =========================================================================
# Step 2: Install Dependencies
# =========================================================================
echo -e "${CYAN}[2/10]${NC} Installing required dependencies..."

# Install Python
if ! command -v python3 &> /dev/null; then
    apt install python3 python3-pip python3-venv -y
    print_status "Python installed"
else
    print_status "Python already installed ($(python3 --version))"
fi

# Install Nginx
if ! command -v nginx &> /dev/null; then
    apt install nginx -y
    print_status "Nginx installed"
else
    print_status "Nginx already installed"
fi

# Install Git
if ! command -v git &> /dev/null; then
    apt install git -y
    print_status "Git installed"
else
    print_status "Git already installed"
fi

# Install build tools
apt install build-essential libssl-dev libffi-dev python3-dev -y -qq
print_status "Build tools installed"
echo ""

# =========================================================================
# Step 3: Create Virtual Environment
# =========================================================================
echo -e "${CYAN}[3/10]${NC} Creating Python virtual environment..."

cd "$PROJECT_DIR"

if [ -d "venv" ]; then
    print_info "Virtual environment already exists, recreating..."
    rm -rf venv
fi

python3 -m venv venv
print_status "Virtual environment created"
echo ""

# =========================================================================
# Step 4: Install Python Dependencies
# =========================================================================
echo -e "${CYAN}[4/10]${NC} Installing Python packages..."

source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
print_status "Python packages installed"
echo ""

# =========================================================================
# Step 5: Create .env File (if not exists)
# =========================================================================
echo -e "${CYAN}[5/10]${NC} Configuring environment variables..."

if [ ! -f ".env" ]; then
    cat > .env << 'EOL'
# MySQL Database Configuration (Optional - uses SQLite by default)
HOST=your_mysql_host
DB_PORT=3306
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=your_database_name

# OpenAI API Key (REQUIRED)
OPEN_AI_KEY=your_openai_api_key_here

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=change-this-to-random-string
EOL
    chmod 600 .env
    print_status ".env file created"
    echo -e "${YELLOW}[!] IMPORTANT: Edit .env file with your actual credentials!${NC}"
else
    print_status ".env file already exists"
fi
echo ""

# =========================================================================
# Step 6: Create Required Directories
# =========================================================================
echo -e "${CYAN}[6/10]${NC} Creating application directories..."

mkdir -p app/storage
mkdir -p app/instance
mkdir -p app/logs
chmod 755 app/storage app/instance app/logs
print_status "Application directories created"
echo ""

# =========================================================================
# Step 7: Create Systemd Service
# =========================================================================
echo -e "${CYAN}[7/10]${NC} Creating systemd service..."

cat > /etc/systemd/system/reviewkit.service << EOL
[Unit]
Description=ReviewKit Flask Application
After=network.target

[Service]
User=root
WorkingDirectory=$PROJECT_DIR/app
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 app:app --timeout 120
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOL

systemctl daemon-reload
print_status "Systemd service created"
echo ""

# =========================================================================
# Step 8: Configure Nginx
# =========================================================================
echo -e "${CYAN}[8/10]${NC} Configuring Nginx..."

# Get server IP or use placeholder
SERVER_IP=$(curl -s ifconfig.me || echo "YOUR_SERVER_IP")

cat > /etc/nginx/sites-available/reviewkit << EOL
server {
    listen 80;
    server_name $SERVER_IP _;

    # Max upload size
    client_max_body_size 50M;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Increase timeout for long operations
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files (if needed)
    location /static {
        alias $PROJECT_DIR/app/static;
        expires 30d;
    }
}
EOL

# Enable site
if [ -f /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi

ln -sf /etc/nginx/sites-available/reviewkit /etc/nginx/sites-enabled/

# Test Nginx configuration
nginx -t &> /dev/null && print_status "Nginx configured successfully" || print_error "Nginx configuration error"
echo ""

# =========================================================================
# Step 9: Configure Firewall (UFW)
# =========================================================================
echo -e "${CYAN}[9/10]${NC} Configuring firewall..."

# Check if UFW is installed
if command -v ufw &> /dev/null; then
    # Allow SSH (important!)
    ufw allow 22/tcp &> /dev/null
    # Allow HTTP
    ufw allow 80/tcp &> /dev/null
    # Allow HTTPS
    ufw allow 443/tcp &> /dev/null
    # Enable firewall (non-interactive)
    echo "y" | ufw enable &> /dev/null || true
    print_status "Firewall configured (ports 22, 80, 443 open)"
else
    print_info "UFW not installed, skipping firewall configuration"
fi
echo ""

# =========================================================================
# Step 10: Start Services
# =========================================================================
echo -e "${CYAN}[10/10]${NC} Starting services..."

# Enable and start ReviewKit service
systemctl enable reviewkit &> /dev/null
systemctl start reviewkit

# Wait a moment for service to start
sleep 2

# Check if service is running
if systemctl is-active --quiet reviewkit; then
    print_status "ReviewKit service started"
else
    print_error "ReviewKit service failed to start"
    echo -e "${YELLOW}Check logs with: sudo journalctl -u reviewkit -n 50${NC}"
fi

# Restart Nginx
systemctl restart nginx
print_status "Nginx started"
echo ""

# =========================================================================
# Installation Complete
# =========================================================================
echo -e "${GREEN}"
echo "  ===================================================================="
echo "             ✅ Installation Complete!"
echo "  ===================================================================="
echo -e "${NC}"
echo ""

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me || hostname -I | awk '{print $1}')

echo -e "${CYAN}📋 Next Steps:${NC}"
echo ""
echo -e "  1️⃣  Edit configuration file:"
echo -e "     ${YELLOW}nano $PROJECT_DIR/.env${NC}"
echo ""
echo -e "  2️⃣  Add your OpenAI API key and database credentials"
echo ""
echo -e "  3️⃣  Restart the service:"
echo -e "     ${YELLOW}sudo systemctl restart reviewkit${NC}"
echo ""
echo -e "  4️⃣  Access your application at:"
echo -e "     ${GREEN}http://$PUBLIC_IP${NC}"
echo ""
echo -e "${CYAN}📊 Useful Commands:${NC}"
echo ""
echo -e "  • View logs:      ${YELLOW}sudo journalctl -u reviewkit -f${NC}"
echo -e "  • Restart app:    ${YELLOW}sudo systemctl restart reviewkit${NC}"
echo -e "  • Check status:   ${YELLOW}sudo systemctl status reviewkit${NC}"
echo -e "  • Stop app:       ${YELLOW}sudo systemctl stop reviewkit${NC}"
echo ""
echo -e "${CYAN}🔒 Optional - Enable HTTPS:${NC}"
echo ""
echo -e "  1. Point your domain to: ${GREEN}$PUBLIC_IP${NC}"
echo -e "  2. Install certbot: ${YELLOW}sudo apt install certbot python3-certbot-nginx -y${NC}"
echo -e "  3. Get certificate: ${YELLOW}sudo certbot --nginx -d yourdomain.com${NC}"
echo ""
echo -e "${GREEN}🎉 Happy deploying!${NC}"
echo ""

