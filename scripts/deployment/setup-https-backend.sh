#!/bin/bash
# Setup HTTPS for Backend on Google Cloud VM
# This script sets up nginx reverse proxy with Let's Encrypt SSL

set -e

echo "🔒 Setting up HTTPS for CryptoOrchestrator Backend"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  Warning: Backend not responding on localhost:8000"
    echo "   Make sure your FastAPI backend is running before continuing"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install nginx
echo "📦 Installing nginx..."
apt-get update
apt-get install -y nginx

# Install certbot via snap (recommended method for 2026)
echo "📦 Installing certbot via snap (recommended method)..."
if ! command -v snap &> /dev/null; then
    echo "Installing snapd..."
    apt-get install -y snapd
    systemctl enable --now snapd
    systemctl enable --now snapd.socket
    ln -sf /snap/core/current/usr/lib/snapd/snapd /usr/lib/snapd/snapd
fi

# Install certbot via snap (ensures latest version)
snap install core; snap refresh core
snap install --classic certbot
ln -sf /snap/bin/certbot /usr/bin/certbot || true

# Get domain name (or use IP)
read -p "Enter your domain name (or press Enter to use IP): " DOMAIN
if [ -z "$DOMAIN" ]; then
    echo "⚠️  Using IP address. For production, use a domain name."
    DOMAIN="34.16.15.56"
    USE_IP=true
else
    USE_IP=false
fi

# Create nginx configuration
echo "📝 Creating nginx configuration..."

if [ "$USE_IP" = true ]; then
    # HTTP only configuration (for IP address)
    cat > /etc/nginx/sites-available/cryptoorchestrator <<EOF
server {
    listen 80;
    server_name ${DOMAIN};

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # CORS headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type, X-Requested-With' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        
        if (\$request_method = 'OPTIONS') {
            return 204;
        }
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
else
    # HTTP and HTTPS configuration (for domain)
    cat > /etc/nginx/sites-available/cryptoorchestrator <<EOF
# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name ${DOMAIN};
    return 301 https://\$server_name\$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name ${DOMAIN};

    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # CORS headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type, X-Requested-With' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        
        if (\$request_method = 'OPTIONS') {
            return 204;
        }
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
fi

# Enable site
ln -sf /etc/nginx/sites-available/cryptoorchestrator /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Start nginx
systemctl enable nginx
systemctl restart nginx

if [ "$USE_IP" = false ]; then
    echo "🔐 Setting up SSL certificate with Let's Encrypt..."
    echo "   Note: Certbot installed via snap includes automatic renewal"
    
    # Get email for Let's Encrypt notifications
    read -p "Enter email for Let's Encrypt notifications (optional, press Enter for admin@${DOMAIN}): " EMAIL
    if [ -z "$EMAIL" ]; then
        EMAIL="admin@${DOMAIN}"
    fi
    
    certbot --nginx -d ${DOMAIN} --non-interactive --agree-tos --email ${EMAIL} --redirect || {
        echo ""
        echo "⚠️  SSL certificate setup failed. You can run manually:"
        echo "   certbot --nginx -d ${DOMAIN}"
        echo ""
        echo "Common issues:"
        echo "  - Domain DNS not pointing to this server's IP"
        echo "  - Port 80 not accessible from internet"
        echo "  - Firewall blocking HTTP traffic"
        echo "  - Domain already has a certificate (may need to use --force-renewal)"
    }
    
    # Verify auto-renewal (certbot via snap handles this automatically with systemd timer)
    if [ $? -eq 0 ]; then
        echo "✅ Verifying certificate auto-renewal..."
        certbot renew --dry-run 2>&1 | grep -q "Congratulations" && {
            echo "✅ Auto-renewal configured successfully"
        } || {
            echo "⚠️  Auto-renewal test had issues, but certificate is installed"
            echo "   Certbot via snap should handle renewals automatically"
        }
    fi
fi

echo ""
echo "✅ HTTPS setup complete!"
if [ "$USE_IP" = true ]; then
    echo "⚠️  Using HTTP proxy (no SSL). For production, use a domain name."
    echo "   Backend accessible at: http://${DOMAIN}"
else
    echo "✅ Backend accessible at: https://${DOMAIN}"
fi
echo ""
echo "📝 Update Vercel environment variable:"
echo "   VITE_API_URL=https://${DOMAIN}/api"
echo ""
