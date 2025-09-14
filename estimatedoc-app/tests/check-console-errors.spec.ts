import { test, expect } from '@playwright/test';

test.describe('Check Console Errors', () => {
  test('capture console errors when opening calculator', async ({ page }) => {
    const consoleErrors: string[] = [];
    
    // Listen for console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
        console.log(`❌ Console error: ${msg.text()}`);
      }
    });
    
    // Listen for page errors
    page.on('pageerror', error => {
      consoleErrors.push(error.message);
      console.log(`❌ Page error: ${error.message}`);
    });
    
    console.log('🔍 Navigating to app...\n');
    await page.goto('http://localhost:5173');
    
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    console.log('🔍 Clicking Calculator tab...\n');
    const calculatorTab = await page.locator('text=Calculator').first();
    await calculatorTab.click();
    
    await page.waitForTimeout(3000);
    
    if (consoleErrors.length > 0) {
      console.log('\n❌ Found console errors:');
      consoleErrors.forEach((error, index) => {
        console.log(`${index + 1}. ${error}`);
      });
    } else {
      console.log('\n✅ No console errors found');
    }
    
    // Check if calculator content is actually rendered
    const calculatorContent = await page.locator('.calculator-container, [class*="Calculator"]').first();
    const html = await calculatorContent.innerHTML().catch(() => 'Could not get HTML');
    
    if (html === '' || html === 'Could not get HTML') {
      console.log('\n⚠️ Calculator container is empty or not found');
    } else {
      console.log('\n✅ Calculator container has content');
      console.log(`Content length: ${html.length} characters`);
    }
    
    // Take screenshot
    await page.screenshot({ path: 'console-errors-check.png', fullPage: true });
    console.log('\n📸 Screenshot saved as console-errors-check.png');
  });
});