import { test, expect } from '@playwright/test';

test.describe('Calculator Page Test', () => {
  test('navigate to calculator page and verify rendering', async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');
    
    // Click on the Calculator link in the navigation
    console.log('Clicking Calculator link in navigation...');
    await page.click('a[href="/calculator"]');
    
    // Wait for navigation to complete
    await page.waitForURL('**/calculator');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Take a screenshot of the calculator page
    await page.screenshot({ path: 'calculator-page-full.png', fullPage: true });
    console.log('✅ Calculator page screenshot saved as calculator-page-full.png');
    
    // Verify key elements are present
    const pageTitle = await page.locator('h1:has-text("Effort Estimation Calculator")').isVisible();
    console.log(`Page title visible: ${pageTitle}`);
    
    // Check for main sections
    const baseConfig = await page.locator('text=/Base Configuration/i').isVisible();
    const fieldEstimates = await page.locator('text=/Field Time Estimates/i').isVisible();
    const resourcePlanning = await page.locator('text=/Resource Planning/i').isVisible();
    const dashboard = await page.locator('text=/Live Impact Dashboard/i').isVisible();
    const timeline = await page.locator('text=/Implementation Timeline/i').isVisible();
    
    console.log('\nSection visibility:');
    console.log(`- Base Configuration: ${baseConfig}`);
    console.log(`- Field Time Estimates: ${fieldEstimates}`);
    console.log(`- Resource Planning: ${resourcePlanning}`);
    console.log(`- Live Impact Dashboard: ${dashboard}`);
    console.log(`- Implementation Timeline: ${timeline}`);
    
    // Test interactivity - adjust base template time
    const baseSlider = await page.locator('input[type="range"]').first();
    if (await baseSlider.isVisible()) {
      await baseSlider.fill('60');
      console.log('✅ Adjusted base template time slider');
    }
    
    // Test resource planning inputs
    const fteInput = await page.locator('input[type="number"]').first();
    if (await fteInput.isVisible()) {
      await fteInput.fill('3');
      console.log('✅ Updated FTE count');
    }
    
    await page.waitForTimeout(1000);
    
    // Take final screenshot with changes
    await page.screenshot({ path: 'calculator-page-with-changes.png', fullPage: true });
    console.log('✅ Updated calculator page screenshot saved');
  });
});