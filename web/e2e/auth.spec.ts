import { test, expect } from '@playwright/test'

test.describe('Authentication', () => {
  test('should display login page', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('h1, h2')).toContainText(/welcome|sign in/i)
  })

  test('should display register page', async ({ page }) => {
    await page.goto('/register')
    await expect(page.locator('h1, h2')).toContainText(/create|sign up/i)
  })

  test('should navigate between login and register', async ({ page }) => {
    await page.goto('/login')
    await page.click('text=Sign up')
    await expect(page).toHaveURL(/.*register/)
    
    await page.click('text=Sign in')
    await expect(page).toHaveURL(/.*login/)
  })
})

