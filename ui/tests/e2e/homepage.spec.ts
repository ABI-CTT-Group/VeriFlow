import { test, expect } from '@playwright/test';

test.describe('Homepage', () => {
    test('should load with correct title', async ({ page }) => {
        await page.goto('/');

        // Check page title
        await expect(page).toHaveTitle('VeriFlow');
    });

    test('should display VeriFlow logo text', async ({ page }) => {
        await page.goto('/');

        // Check logo text is visible
        const logoText = page.locator('text=VeriFlow');
        await expect(logoText.first()).toBeVisible();
    });

    test('should display sidebar navigation', async ({ page }) => {
        await page.goto('/');

        // Check navigation items exist
        await expect(page.locator('text=Upload')).toBeVisible();
        await expect(page.locator('text=Study Design')).toBeVisible();
        await expect(page.locator('text=Workflow')).toBeVisible();
        await expect(page.locator('text=Console')).toBeVisible();
    });

    test('should display upload zone', async ({ page }) => {
        await page.goto('/');

        // Check upload zone is visible
        await expect(page.locator('text=Drop your PDF here')).toBeVisible();
    });
});
