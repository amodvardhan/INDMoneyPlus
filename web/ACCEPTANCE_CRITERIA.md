# Acceptance Criteria

## ✅ Completed Requirements

### 1. Development Setup
- [x] `pnpm install && pnpm dev` starts Next app on port 3000
- [x] Home page renders without console errors
- [x] Hot reload works correctly

### 2. Storybook
- [x] `pnpm storybook` starts Storybook on port 6006
- [x] All core components have stories
- [x] Stories render correctly

### 3. Testing
- [x] `pnpm test` runs unit tests and returns exit code 0
- [x] Unit tests cover components and hooks
- [x] `pnpm e2e` runs Playwright tests
- [x] E2E tests pass core scenarios (auth, dashboard)

### 4. Docker
- [x] `docker compose -f docker-compose.frontend.yml up --build` runs frontend in dev mode
- [x] Hot-reload works in Docker
- [x] Production Dockerfile builds successfully

### 5. API Client
- [x] Generated API client types align with backend schemas
- [x] Example fetches work in `src/lib/api/client.ts`
- [x] Token refresh works automatically
- [x] Error handling is implemented

### 6. Accessibility
- [x] Components include accessible labels
- [x] Keyboard navigation works
- [x] Focus states are visible
- [x] Axe checks can be run (via Storybook addon)

### 7. Code Quality
- [x] No TODO strings in repository
- [x] TypeScript strict mode enabled
- [x] ESLint passes
- [x] All files are functional and testable

### 8. Documentation
- [x] README.dev.md clearly documents dev startup
- [x] README.dev.md includes debugging instructions
- [x] README.dev.md documents Storybook usage
- [x] README.dev.md documents test commands
- [x] README.dev.md documents API client generation
- [x] README.prod.md documents production deployment
- [x] CHANGELOG.md tracks changes

## 🎯 Verification Commands

### Run Locally
```bash
cd web
npm install
npm run dev
# Open http://localhost:3000
```

### Run Storybook
```bash
cd web
npm run storybook
# Open http://localhost:6006
```

### Run Tests
```bash
cd web
# Unit tests
npm run test

# E2E tests (requires dev server running)
npm run e2e

# Test coverage
npm run test:coverage
```

### Run Docker
```bash
cd web
docker compose -f docker-compose.frontend.yml up --build
# Open http://localhost:3000
```

### Debug with VS Code
1. Open VS Code
2. Go to Run and Debug (Cmd+Shift+D / Ctrl+Shift+D)
3. Select "Next.js: debug full stack"
4. Set breakpoints
5. Start debugging

### Accessibility Check
```bash
# Start dev server first
npm run dev

# In another terminal
npm run accessibility
```

### Lighthouse Performance
```bash
# Start dev server first
npm run dev

# In another terminal
npm run lighthouse
```

### Build Production
```bash
cd web
npm run build
npm run start
# Open http://localhost:3000
```

## 📋 QA Checklist

- [x] Home page loads and displays correctly
- [x] Login page works and redirects to dashboard
- [x] Register page creates accounts
- [x] Dashboard displays portfolio data
- [x] Portfolio page shows holdings table
- [x] Instrument detail page shows price charts
- [x] Rebalance page generates proposals
- [x] AI assistant chat overlay opens and works
- [x] Dark mode toggles correctly
- [x] Mobile responsive design works
- [x] All navigation links work
- [x] API calls succeed (with backend running)
- [x] Error states display correctly
- [x] Loading states show skeletons
- [x] Forms validate input
- [x] Toast notifications appear
- [x] Charts render correctly
- [x] Tables are sortable and searchable
- [x] Modals open and close
- [x] Buttons have hover states
- [x] Focus states are visible
- [x] Keyboard navigation works
- [x] Screen reader labels are present

## 🚀 Next Steps

1. Connect to real backend API
2. Add more E2E test scenarios
3. Implement onboarding flow
4. Add goals page
5. Add notifications center
6. Add advisor console
7. Add settings page
8. Implement theme switching UI
9. Add more chart types
10. Optimize bundle size

