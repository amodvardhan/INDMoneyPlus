import { test, expect } from '@playwright/test'

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication - in real app, you'd set up auth state
    await page.goto('/dashboard')
  })

  test('should display dashboard when authenticated', async ({ page }) => {
    // Wait for dashboard to load
    await expect(page.locator('h1')).toContainText('Dashboard')
  })

  test('should show net worth card', async ({ page }) => {
    await expect(page.locator('text=Net Worth')).toBeVisible()
  })

  test('should navigate to portfolio', async ({ page }) => {
    await page.click('text=View Portfolio')
    await expect(page).toHaveURL(/.*portfolio/)
  })
})

