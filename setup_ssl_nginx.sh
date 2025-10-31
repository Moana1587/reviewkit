#!/bin/bash
# =========================================================================
# SSL Setup Script - Nginx + Let's Encrypt
# =========================================================================
# This script automates SSL certificate setup for ReviewKit
# Usage: sudo ./setup_ssl_nginx.sh your-domain.com your-email@example.com
# =========================================================================

set -e  # Exit on error

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: sudo $0 <domain> <email>"
    echo "Example: sudo $0 api.yourdomain.com admin@yourdomain.com"
    exit 1
fi

DOMAIN=$1
EMAIL=$2

echo ""
echo "================================================================"
echo "  ReviewKit SSL Setup - Nginx + Let's Encrypt"
echo "================================================================"
echo "  Domain: $DOMAIN"
echo "  Email:  $EMAIL"
echo "================================================================"
echo ""

# Step 1: Install Nginx
echo "📦 Step 1/6: Installing Nginx..."
apt update
apt install nginx -y
echo "✅ Nginx installed"
echo ""

# Step 2: Install Certbot
echo "🔐 Step 2/6: Installing Certbot..."
apt install certbot python3-certbot-nginx -y
echo "✅ Certbot installed"
echo ""

# Step 3: Create Nginx config
echo "⚙️  Step 3/6: Configuring Nginx..."

cat > /etc/nginx/sites-available/reviewkit << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/reviewkit /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test config
nginx -t
systemctl restart nginx

echo "✅ Nginx configured"
echo ""

# Step 4: Configure firewall
echo "🔥 Step 4/6: Configuring firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 'Nginx Full'
    ufw allow 22  # Keep SSH open
    echo "✅ UFW firewall configured"
else
    echo "⚠️  UFW not found, skipping firewall configuration"
fi
echo ""

# Step 5: Get SSL certificate
echo "🔒 Step 5/6: Getting SSL certificate from Let's Encrypt..."
echo ""
echo "Please follow the certbot prompts below:"
echo ""

certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL --redirect

echo ""
echo "✅ SSL certificate obtained"
echo ""

# Step 6: Test auto-renewal
echo "🔄 Step 6/6: Setting up auto-renewal..."
certbot renew --dry-run
echo "✅ Auto-renewal configured"
echo ""

# Print success message
echo ""
echo "================================================================"
echo "  🎉 SSL Setup Complete!"
echo "================================================================"
echo ""
echo "  ✅ Nginx installed and configured"
echo "  ✅ SSL certificate obtained"
echo "  ✅ Auto-renewal configured (runs twice daily)"
echo "  ✅ HTTP automatically redirects to HTTPS"
echo ""
echo "  Your site is now accessible at:"
echo "  🔒 https://$DOMAIN"
echo ""
echo "================================================================"
echo ""
echo "📝 Next Steps:"
echo ""
echo "  1. Start your Flask app (listening on localhost:8000):"
echo "     cd app"
echo "     python3 app.py --host 127.0.0.1 --port 8000"
echo ""
echo "  2. Test your site:"
echo "     curl https://$DOMAIN"
echo ""
echo "  3. Check SSL rating:"
echo "     https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
echo ""
echo "================================================================"
echo ""
echo "🔧 Useful Commands:"
echo ""
echo "  Check certificate status:"
echo "    sudo certbot certificates"
echo ""
echo "  Renew certificate manually:"
echo "    sudo certbot renew"
echo ""
echo "  Check Nginx status:"
echo "    sudo systemctl status nginx"
echo ""
echo "  Reload Nginx config:"
echo "    sudo nginx -t && sudo systemctl reload nginx"
echo ""
echo "================================================================"
echo ""

