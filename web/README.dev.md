# Portfolio Superapp - Frontend Development Guide

## Prerequisites

- Node.js 20+ and npm
- Docker and Docker Compose (optional, for containerized development)

## Quick Start

1. **Install dependencies:**
   ```bash
   npm install
   # or
   pnpm install
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your API URL
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```
   The app will be available at http://localhost:3000

## Available Scripts

- `npm run dev` - Start Next.js development server with hot reload
- `npm run build` - Build production bundle
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking
- `npm run test` - Run unit tests
- `npm run test:watch` - Run tests in watch mode
- `npm run test:coverage` - Generate test coverage report
- `npm run e2e` - Run Playwright E2E tests
- `npm run e2e:ui` - Run Playwright with UI mode
- `npm run storybook` - Start Storybook on port 6006
- `npm run build-storybook` - Build static Storybook
- `npm run accessibility` - Run axe accessibility checks (requires server running)
- `npm run lighthouse` - Run Lighthouse performance audit

## Development with Docker

```bash
# Start frontend in dev mode with hot reload
docker compose -f docker-compose.frontend.yml up --build

# Or using docker-compose directly
docker-compose -f docker-compose.frontend.yml up
```

## Project Structure

```
web/
├── src/
│   ├── app/              # Next.js App Router pages
│   ├── components/        # React components
│   │   ├── ui/           # Design system primitives
│   │   ├── charts/       # Chart components
│   │   └── ai-assistant/ # AI chat components
│   ├── hooks/            # Custom React hooks
│   ├── lib/              # Utilities and API client
│   ├── styles/           # Global styles
│   └── design-system/    # Design tokens
├── e2e/                  # Playwright E2E tests
├── public/               # Static assets
└── .storybook/           # Storybook configuration
```

## API Client

The API client is located in `src/lib/api/client.ts` and uses axios with automatic token refresh. It's typed with TypeScript interfaces in `src/lib/api/types.ts`.

### Mock API Responses

For development, you can mock API responses by:
1. Using MSW (Mock Service Worker) - see `src/mocks/` (if implemented)
2. Modifying the API client to return mock data in development mode
3. Using Next.js API routes as mocks

## Debugging

### VS Code Debugger

1. Open VS Code
2. Go to Run and Debug (Cmd+Shift+D / Ctrl+Shift+D)
3. Select "Next.js: debug full stack"
4. Set breakpoints in your code
5. Start debugging

### Browser DevTools

- React DevTools: Install browser extension
- React Query DevTools: Available in development mode (bottom left corner)

## Testing

### Unit Tests

Tests are written with Jest and React Testing Library:

```bash
npm run test
```

### E2E Tests

E2E tests use Playwright:

```bash
# Run tests
npm run e2e

# Run with UI
npm run e2e:ui
```

### Storybook

View and test components in isolation:

```bash
npm run storybook
```

## Design System

The design system is located in:
- `src/design-system/tokens.ts` - TypeScript tokens
- `src/styles/globals.css` - CSS variables
- `src/components/ui/` - Component primitives

## Accessibility

- All components follow WCAG AA standards
- Run accessibility checks: `npm run accessibility`
- Use Storybook's a11y addon to test components

## Performance

- Use `npm run lighthouse` to audit performance
- Images are optimized with Next.js Image component
- Code splitting is automatic with Next.js
- Heavy components (charts) are dynamically imported

## Environment Variables

- `NEXT_PUBLIC_API_URL` - Backend API URL (default: http://localhost:8000)
- `NEXT_PUBLIC_APP_NAME` - App name (default: Portfolio Superapp)

## Troubleshooting

### Port already in use
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### Module not found errors
```bash
# Clear .next cache
rm -rf .next
npm install
```

### Type errors
```bash
# Regenerate types
npm run type-check
```

## Next Steps

- Read [Next.js Documentation](https://nextjs.org/docs)
- Check [React Query Docs](https://tanstack.com/query/latest)
- Review [Tailwind CSS Docs](https://tailwindcss.com/docs)

