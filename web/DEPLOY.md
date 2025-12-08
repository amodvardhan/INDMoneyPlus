# Web Application Deployment Guide

This guide covers multiple ways to deploy only the web application (Next.js frontend).

## Prerequisites

- Node.js 20+ installed
- Environment variables configured
- Backend API accessible

## Quick Start

### Option 1: Vercel (Recommended - Easiest)

Vercel is the easiest way to deploy Next.js applications:

1. **Install Vercel CLI** (optional):
   ```bash
   npm i -g vercel
   ```

2. **Deploy from web directory**:
   ```bash
   cd web
   vercel
   ```

3. **Or connect via GitHub**:
   - Go to [vercel.com](https://vercel.com)
   - Import your repository
   - Set root directory to `web`
   - Configure environment variables:
     - `NEXT_PUBLIC_API_URL` - Your backend API URL
     - `NEXT_PUBLIC_APP_NAME` - Application name

4. **Automatic deployments**:
   - Vercel automatically deploys on push to main branch
   - Preview deployments for PRs

### Option 2: Docker Deployment

#### Build and Run Locally

```bash
cd web

# Build the Docker image
docker build -t portfolio-web:latest -f Dockerfile .

# Run the container
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=https://api.yourdomain.com \
  -e NEXT_PUBLIC_APP_NAME="Portfolio Superapp" \
  portfolio-web:latest
```

#### Deploy to Cloud (Docker)

**AWS ECS / Fargate:**
```bash
# Tag and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag portfolio-web:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/portfolio-web:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/portfolio-web:latest
```

**Google Cloud Run:**
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/<project-id>/portfolio-web
gcloud run deploy portfolio-web \
  --image gcr.io/<project-id>/portfolio-web \
  --platform managed \
  --region us-central1 \
  --set-env-vars NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

**Azure Container Instances:**
```bash
# Build and push to ACR
az acr build --registry <registry-name> --image portfolio-web:latest .
az container create \
  --resource-group <resource-group> \
  --name portfolio-web \
  --image <registry-name>.azurecr.io/portfolio-web:latest \
  --dns-name-label portfolio-web \
  --ports 3000 \
  --environment-variables NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### Option 3: Railway

1. Go to [railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Select repository and set root directory to `web`
4. Add environment variables
5. Deploy automatically

### Option 4: Netlify

1. Go to [netlify.com](https://netlify.com)
2. Add new site → Import from Git
3. Build settings:
   - Base directory: `web`
   - Build command: `npm run build`
   - Publish directory: `web/.next`
4. Add environment variables
5. Deploy

### Option 5: Manual Server Deployment

#### On a VPS/Server:

```bash
# SSH into your server
ssh user@your-server.com

# Clone repository
git clone <your-repo-url>
cd INDMoneyPlus/web

# Install dependencies
npm ci --production

# Build the application
npm run build

# Install PM2 for process management
npm install -g pm2

# Start the application
pm2 start npm --name "portfolio-web" -- start

# Save PM2 configuration
pm2 save
pm2 startup

# Set up Nginx reverse proxy (optional)
sudo nano /etc/nginx/sites-available/portfolio-web
```

Nginx configuration:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## Environment Variables

Create a `.env.production` file in the `web` directory:

```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_APP_NAME=Portfolio Superapp
NODE_ENV=production
```

**Important:** Only variables prefixed with `NEXT_PUBLIC_` are exposed to the browser.

## Build Commands

```bash
# Development
npm run dev

# Production build
npm run build

# Start production server
npm run start

# Type check
npm run type-check

# Lint
npm run lint
```

## Troubleshooting

### Module Resolution Issues

If you encounter module resolution errors (like `lightweight-charts`):

1. **Ensure symlink exists**:
   ```bash
   cd web
   mkdir -p node_modules
   ln -sf ../../node_modules/lightweight-charts node_modules/lightweight-charts
   ```

2. **Or install locally**:
   ```bash
   cd web
   npm install lightweight-charts
   ```

### Build Errors

1. **Clear Next.js cache**:
   ```bash
   rm -rf .next
   npm run build
   ```

2. **Check environment variables**:
   ```bash
   echo $NEXT_PUBLIC_API_URL
   ```

3. **Verify Node version**:
   ```bash
   node --version  # Should be 20+
   ```

### Docker Build Issues

If Docker build fails:

1. **Check Dockerfile context**:
   - Ensure you're building from the `web` directory
   - Or adjust COPY paths in Dockerfile

2. **Workspace dependencies**:
   - The Dockerfile should handle workspace dependencies
   - Consider installing root dependencies if needed

## CI/CD Integration

### GitHub Actions

The existing workflow (`.github/workflows/frontend-ci.yml`) runs:
- Linting
- Type checking
- Tests
- Build verification

To add deployment:

```yaml
# Add to frontend-ci.yml
deploy:
  needs: build
  runs-on: ubuntu-latest
  if: github.ref == 'refs/heads/main'
  steps:
    - uses: actions/checkout@v4
    - uses: amondnet/vercel-action@v25
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
        vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
        working-directory: ./web
```

## Performance Optimization

1. **Enable caching**:
   - Static assets are automatically cached
   - API responses cached with React Query

2. **Image optimization**:
   - Next.js Image component automatically optimizes images
   - Configure image domains in `next.config.js`

3. **Code splitting**:
   - Automatic code splitting enabled
   - Dynamic imports for heavy components

## Security Checklist

- [ ] Environment variables set securely
- [ ] HTTPS enabled
- [ ] CORS configured correctly
- [ ] API endpoints secured
- [ ] No sensitive data in client-side code
- [ ] Content Security Policy headers set
- [ ] Rate limiting on API endpoints

## Monitoring

Set up monitoring for:
- Error tracking (Sentry, LogRocket)
- Performance monitoring (Vercel Analytics, Google Analytics)
- Uptime monitoring (UptimeRobot, Pingdom)
- API response times

## Support

For issues:
1. Check build logs
2. Verify environment variables
3. Check backend API connectivity
4. Review Next.js documentation
