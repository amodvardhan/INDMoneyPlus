# Quick Deploy Guide - Web Only

## 🚀 Fastest Options

### 1. Vercel (30 seconds)
```bash
cd web
npx vercel
```
Or connect GitHub repo at [vercel.com](https://vercel.com)

### 2. Railway (1 minute)
1. Go to [railway.app](https://railway.app)
2. New Project → GitHub
3. Select repo, set root: `web`
4. Add env vars → Deploy

### 3. Docker (2 minutes)
```bash
cd web
docker build -t portfolio-web .
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=https://api.yourdomain.com \
  portfolio-web
```

### 4. Manual Build
```bash
cd web
./deploy.sh
npm run start
```

## 📋 Required Environment Variables

```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_APP_NAME=Portfolio Superapp
```

## 🔧 Build Commands

```bash
npm run build    # Build for production
npm run start    # Start production server
npm run dev      # Development mode
```

## 📚 Full Documentation

See [DEPLOY.md](./DEPLOY.md) for detailed instructions.
