# Custom Domain Configuration Guide

This guide describes how to connect and configure a production custom domain (for example, `nexus.yourdomain.com` or `agentops.yourcompany.org`) to the AgentOps Nexus platform.

---

## 1. DNS Records Setup

Point your custom domain or subdomain to your server's public IP address or reverse proxy gateway.

| Record Type | Host / Name | Target / Value | TTL |
| :--- | :--- | :--- | :--- |
| **A Record** | `@` (or `nexus`) | `YOUR_SERVER_PUBLIC_IPV4` | `300` (5 min) |
| **AAAA Record** (Optional) | `@` (or `nexus`) | `YOUR_SERVER_PUBLIC_IPV6` | `300` (5 min) |
| **CNAME** (Alternative) | `nexus` | `cname.yourhostingprovider.com` | `300` (5 min) |

---

## 2. Environment Variables

Define your custom domain and API origin in `apps/dashboard/.env.production`:

```bash
# Domain configuration
VITE_CUSTOM_DOMAIN="nexus.yourdomain.com"
VITE_API_BASE_URL="https://nexus.yourdomain.com"
```

---

## 3. Production Nginx Reverse Proxy with SSL (Let's Encrypt)

Below is the standard production configuration template for `/etc/nginx/sites-available/agentops-nexus.conf`:

```nginx
# HTTP - Redirect all traffic to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name nexus.yourdomain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS - Terminate TLS and proxy to AgentOps Nexus
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name nexus.yourdomain.com;

    # SSL Certificates (managed via certbot)
    ssl_certificate /etc/letsencrypt/live/nexus.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/nexus.yourdomain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Frontend Dashboard (SPA)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API & WebSocket streams
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}
```

---

## 4. Issuing SSL/TLS Certificate

Use Certbot to provision free, auto-renewing certificates:

```bash
sudo certbot --nginx -d nexus.yourdomain.com
```

---

## 5. Verification Checklist

1. **DNS Propagation**: Run `dig +short nexus.yourdomain.com` or `nslookup nexus.yourdomain.com`.
2. **TLS Validity**: Run `curl -Iv https://nexus.yourdomain.com` to verify certificate issuer and HTTP/2 handshake.
3. **API Proxy**: Verify that `https://nexus.yourdomain.com/api/tools` returns HTTP 200 with JSON payload.
4. **Favicon**: Confirm `https://nexus.yourdomain.com/favicon.svg` renders cleanly in the browser tab.
