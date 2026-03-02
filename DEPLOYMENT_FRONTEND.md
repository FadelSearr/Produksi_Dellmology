# Deployment Guide - Dellmology Pro

## 🚀 Quick Deployment Options

Choose your preferred deployment method:

1. **Vercel** (Recommended) - Easiest, free tier available
2. **Docker** (Local/VPS) - Full control, self-hosted
3. **Netlify** - Alternative cloud option
4. **Railway.app** - Budget-friendly cloud

---

## Option 1: Vercel Deployment (Easiest - 5 minutes)

### Prerequisites
- Vercel account (free at vercel.com)
- GitHub account with this repo pushed

### Steps

#### 1. Push Code to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/dellmology.git
git push -u origin main
```

#### 2. Connect to Vercel
- Go to [vercel.com](https://vercel.com)
- Click "New Project"
- Import your GitHub repo
- Select `apps/web` as the root directory
- Click "Deploy"

#### 3. Set Environment Variables in Vercel
In Vercel Dashboard → Settings → Environment Variables:

```
NEXT_PUBLIC_STREAMER_URL=https://your-local-worker.com
NEXT_PUBLIC_API_URL=https://your-app.vercel.app
GEMINI_API_KEY=your_gemini_key
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
```

#### 4. Configure Local Worker
Since the Go/Python worker runs locally, use **Cloudflare Tunnel** to expose it:

```bash
# Install cloudflared
# https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-setup/

cloudflared tunnel login
cloudflared tunnel create dellmology
cloudflared tunnel route dns dellmology api.dellmology-idx.com

# Edit ~/.cloudflare/config.yml
configure:
  id: <your-tunnel-id>
  credentials-file: ~/.cloudflare/credentials-<tunnel-id>.json

ingress:
  - hostname: api.dellmology-idx.com
    service: http://localhost:8080
  - service: http_status:404
```

Start tunnel:
```bash
cloudflared tunnel run dellmology
```

Then set in Vercel:
```
NEXT_PUBLIC_STREAMER_URL=https://api.dellmology-idx.com
```

**Done!** Your dashboard is live at `https://your-app.vercel.app`

---

## Option 2: Docker Deployment (Full Control)

### Dockerfile

```dockerfile
# apps/web/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Build Next.js app
COPY . .
RUN npm run build

# Production image
FROM node:18-alpine

WORKDIR /app

# Copy only necessary files
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./

EXPOSE 3000

CMD ["npm", "start"]
```

### Docker Compose

```yaml
# docker-compose.yml (update existing)
version: '3.8'

services:
  # Frontend
  web:
    build:
      context: apps/web
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      NODE_ENV: production
      NEXT_PUBLIC_STREAMER_URL: http://localhost:8080
      NEXT_PUBLIC_API_URL: http://localhost:3000
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      SUPABASE_URL: ${SUPABASE_URL}
      SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY}
    depends_on:
      - timescaledb
    networks:
      - dellmology

  # Database (TimescaleDB)
  timescaledb:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: dellmology
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./db/init:/docker-entrypoint-initdb.d
    ports:
      - "5433:5432"
    networks:
      - dellmology

networks:
  dellmology:
    driver: bridge

volumes:
  pgdata:
```

### Deploy to VPS

```bash
# 1. SSH into your VPS
ssh user@your-vps-ip

# 2. Clone repository
git clone https://github.com/yourusername/dellmology.git
cd dellmology

# 3. Create .env file
cat > .env << EOF
POSTGRES_PASSWORD=secure_password_here
GEMINI_API_KEY=your_key
SUPABASE_URL=your_url
SUPABASE_ANON_KEY=your_key
EOF

# 4. Build and run
docker-compose up -d

# 5. Check status
docker-compose ps
docker-compose logs web
```

### Reverse Proxy (Nginx)

```nginx
# /etc/nginx/sites-available/dellmology
server {
    listen 80;
    server_name dellmology.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name dellmology.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/dellmology.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dellmology.yourdomain.com/privkey.pem;

    # CORS headers
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;

    # Proxy to Next.js
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;

        # WebSocket support
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Stream endpoint
    location /stream {
        proxy_pass http://localhost:8080/stream;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400;
        chunked_transfer_encoding off;
    }
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/dellmology /etc/nginx/sites-enabled/
sudo certbot certonly --standalone -d dellmology.yourdomain.com
sudo systemctl reload nginx
```

---

## Option 3: Netlify Deployment

### 1. Connect GitHub
- Go to [netlify.com](https://netlify.com)
- Click "New site from Git"
- Connect GitHub, select your repo

### 2. Build Settings
- **Base directory**: `apps/web`
- **Build command**: `npm run build`
- **Publish directory**: `.next`

### 3. Environment Variables
In Netlify Dashboard → Site settings → Build & deploy → Environment:

```
NEXT_PUBLIC_STREAMER_URL=https://your-tunnel.example.com
NEXT_PUBLIC_API_URL=https://your-site.netlify.app
GEMINI_API_KEY=your_key
```

### 4. Redirects (_redirects file)

```
# apps/web/public/_redirects
/api/* http://localhost:8080 200
/* /index.html 200
```

---

## Option 4: Railway.app (Budget Friendly)

### 1. Create Account
- Go to [railway.app](https://railway.app)
- Sign up (GitHub auth recommended)

### 2. Deploy
- Create new project
- Select "Deploy from GitHub"
- Select your repository
- Set `apps/web` as the root

### 3. Configure
Add to Railway environment:

```
NODE_ENV=production
NEXT_PUBLIC_STREAMER_URL=https://your-worker.railway.app
NEXT_PUBLIC_API_URL=https://dellmology.railway.app
GEMINI_API_KEY=your_key
SUPABASE_URL=your_url
SUPABASE_ANON_KEY=your_key
```

### 4. Connect Database
- Create PostgreSQL service in Railway
- Connect to your app

---

## Monitoring & Maintenance

### Health Checks
```bash
# Monitor Vercel deployment
# Dashboard → Analytics

# Monitor Docker containers
docker-compose logs -f web
docker-compose stats

# Monitor system
htop
```

### Logs
```bash
# Vercel (in Vercel Dashboard)
Settings → Functions → Logs

# Docker
docker-compose logs web --tail=100 -f

# VPS System Logs
journalctl -xe
tail -f /var/log/nginx/error.log
```

### Auto-scaling (Docker)
```bash
# Use Docker Swarm or Kubernetes
docker swarm init
docker service create --name dellmology \
  --replicas 3 \
  -p 3000:3000 \
  dellmology:latest
```

---

## Production Checklist

- [ ] Environment variables configured securely
- [ ] Database backups configured
- [ ] SSL/TLS certificates installed
- [ ] CORS headers configured
- [ ] Rate limiting enabled
- [ ] Error logging setup
- [ ] Monitoring/alerting configured
- [ ] Load balancer configured (if multiple instances)
- [ ] CDN setup for static assets
- [ ] Database migrations run
- [ ] Backup strategy documented
- [ ] Disaster recovery plan ready

---

## Troubleshooting

### Build fails on Vercel
```
Error: Cannot find module
✓ Check package.json versions match
✓ Run npm ci instead of npm install locally
✓ Check .vercelignore is not excluding needed files
```

### WebSocket connection fails
```
Error: 404 /stream
✓ Ensure Go worker is running and accessible
✓ Check firewall rules
✓ Check Nginx proxy_buffering is off
```

### High memory usage
```
Memory limit exceeded
✓ Optimize bundle size (npm analyze)
✓ Enable caching strategy
✓ Use serverless functions instead of server
```

---

## Cost Estimates

| Platform | Monthly Cost | Notes |
|----------|-------------|-------|
| **Vercel** | $0-20 | Free tier, pay-as-you-go |
| **Netlify** | $0-19 | Free tier sufficient |
| **Railway.app** | $5-50 | $5 starter, pay-as-you-go |
| **VPS (DigitalOcean)** | $5-40 | Fixed cost, full control |
| **AWS** | $10-100+ | Pay-as-you-go, complex |
| **Google Cloud** | $10-100+ | Pay-as-you-go, complex |

---

## Scaling Strategy

### Phase 1: Launch (Single Instance)
- Single Vercel deployment
- Shared database
- Local Go worker

### Phase 2: Growth (Multiple Instances)
- Multiple Vercel deployments (automatic)
- Database read replicas
- Multiple Go workers behind load balancer

### Phase 3: Scale (Full Infrastructure)
- Kubernetes cluster
- Database sharding
- Caching layer (Redis)
- CDN for static content

---

**Need help?** Check the troubleshooting section above or open an issue on GitHub.
