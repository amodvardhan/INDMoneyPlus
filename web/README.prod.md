# Portfolio Superapp - Production Deployment Guide

## Building for Production

```bash
npm run build
npm run start
```

## Docker Production Build

```bash
# Build image
docker build -t portfolio-superapp-web .

# Run container
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=https://api.example.com \
  portfolio-superapp-web
```

## Environment Variables

Required environment variables for production:

- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_APP_NAME` - Application name

Optional:
- `NODE_ENV` - Set to `production`

## Deployment Options

### Vercel (Recommended)

1. Connect your repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push to main

### Docker

See Dockerfile for production build. The Dockerfile uses Next.js standalone output for optimal size.

### Static Export

For static hosting (if no server-side features needed):

```bash
# In next.config.js, add:
output: 'export'

# Then build:
npm run build
```

## Performance Optimization

- Images are automatically optimized
- Code splitting is enabled
- Static assets are cached
- API responses are cached with React Query

## Security

- Never commit `.env.local` or `.env.production`
- Use HTTPS in production
- Set secure cookie flags for authentication
- Enable CSP headers
- Use environment variables for all secrets

## Monitoring

- Set up error tracking (Sentry, etc.)
- Monitor API response times
- Track Core Web Vitals
- Set up uptime monitoring

## CI/CD

The GitHub Actions workflow (`.github/workflows/frontend-ci.yml`) runs:
- Linting
- Type checking
- Unit tests
- Build verification
- Storybook build

