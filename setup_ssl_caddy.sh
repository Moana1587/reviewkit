#!/bin/bash
# =========================================================================
# SSL Setup Script - Caddy (Easiest Method)
# =========================================================================
# Caddy automatically handles SSL certificates - zero configuration needed!
# Usage: sudo ./setup_ssl_caddy.sh your-domain.com
# =========================================================================

set -e  # Exit on error

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: sudo $0 <domain>"
    echo "Example: sudo $0 api.yourdomain.com"
    exit 1
fi

DOMAIN=$1

echo ""
echo "================================================================"
echo "  ReviewKit SSL Setup - Caddy (Auto SSL)"
echo "================================================================"
echo "  Domain: $DOMAIN"
echo "================================================================"
echo ""

# Step 1: Install dependencies
echo "📦 Step 1/4: Installing dependencies..."
apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
echo "✅ Dependencies installed"
echo ""

# Step 2: Add Caddy repository
echo "📦 Step 2/4: Adding Caddy repository..."
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update
echo "✅ Repository added"
echo ""

# Step 3: Install Caddy
echo "📦 Step 3/4: Installing Caddy..."
apt install caddy -y
echo "✅ Caddy installed"
echo ""

# Step 4: Configure Caddy
echo "⚙️  Step 4/4: Configuring Caddy..."

# Backup original config
cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.backup 2>/dev/null || true

# Create new config
cat > /etc/caddy/Caddyfile << EOF
# ReviewKit API - Caddy Configuration
# Caddy automatically obtains and renews SSL certificates!

$DOMAIN {
    reverse_proxy localhost:8000
    
    # Optional: Enable compression
    encode gzip
    
    # Optional: Add security headers
    header {
        # Enable HSTS
        Strict-Transport-Security "max-age=31536000;"
        # Prevent clickjacking
        X-Frame-Options "SAMEORIGIN"
        # Prevent MIME sniffing
        X-Content-Type-Options "nosniff"
    }
    
    # Optional: Logging
    log {
        output file /var/log/caddy/reviewkit.log
    }
}
EOF

# Create log directory
mkdir -p /var/log/caddy
chown caddy:caddy /var/log/caddy

# Restart Caddy
systemctl restart caddy
systemctl enable caddy

echo "✅ Caddy configured and started"
echo ""

# Configure firewall
echo "🔥 Configuring firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 22/tcp  # Keep SSH open
    echo "✅ UFW firewall configured"
else
    echo "⚠️  UFW not found, skipping firewall configuration"
fi
echo ""

# Wait a moment for Caddy to start
sleep 2

# Check Caddy status
echo "🔍 Checking Caddy status..."
if systemctl is-active --quiet caddy; then
    echo "✅ Caddy is running"
else
    echo "❌ Caddy failed to start. Check logs: sudo journalctl -u caddy"
    exit 1
fi
echo ""

# Print success message
echo ""
echo "================================================================"
echo "  🎉 SSL Setup Complete! (Auto-configured by Caddy)"
echo "================================================================"
echo ""
echo "  ✅ Caddy installed and configured"
echo "  ✅ SSL certificate will be obtained automatically"
echo "  ✅ Auto-renewal configured (Caddy handles this)"
echo "  ✅ HTTP automatically redirects to HTTPS"
echo ""
echo "  Your site will be accessible at:"
echo "  🔒 https://$DOMAIN"
echo ""
echo "  ⏳ Note: First HTTPS request triggers certificate generation"
echo "     (takes 5-10 seconds on first access)"
echo ""
echo "================================================================"
echo ""
echo "📝 Next Steps:"
echo ""
echo "  1. Ensure DNS points to this server:"
echo "     $DOMAIN → $(curl -s ifconfig.me)"
echo ""
echo "  2. Start your Flask app (listening on localhost:8000):"
echo "     cd app"
echo "     python3 app.py --host 127.0.0.1 --port 8000"
echo ""
echo "  3. Test your site (wait 10 seconds for first cert):"
echo "     curl https://$DOMAIN"
echo ""
echo "================================================================"
echo ""
echo "🔧 Useful Commands:"
echo ""
echo "  Check Caddy status:"
echo "    sudo systemctl status caddy"
echo ""
echo "  View Caddy logs:"
echo "    sudo journalctl -u caddy -f"
echo ""
echo "  Restart Caddy:"
echo "    sudo systemctl restart caddy"
echo ""
echo "  Edit Caddy config:"
echo "    sudo nano /etc/caddy/Caddyfile"
echo "    sudo systemctl reload caddy"
echo ""
echo "  View certificate info:"
echo "    sudo caddy list-modules | grep tls"
echo ""
echo "================================================================"
echo ""
echo "💡 Tip: Caddy handles EVERYTHING automatically!"
echo "   - SSL certificates"
echo "   - Renewals"
echo "   - HTTP to HTTPS redirect"
echo "   - Security headers"
echo ""
echo "   No maintenance needed! 🎉"
echo ""

