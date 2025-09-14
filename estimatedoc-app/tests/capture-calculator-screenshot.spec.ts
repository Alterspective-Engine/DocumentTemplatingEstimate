import { test, expect } from '@playwright/test';

test.describe('Capture Calculator Screenshot', () => {
  test('capture full calculator rendering', async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Click Calculator tab
    console.log('Opening calculator...');
    await page.locator('text=Calculator').first().click();
    await page.waitForTimeout(3000); // Give time for animations
    
    // Take screenshot of the full calculator
    await page.screenshot({ path: 'calculator-full-render.png', fullPage: false });
    console.log('✅ Screenshot saved as calculator-full-render.png');
    
    // Scroll down in the calculator content to show more sections
    await page.evaluate(() => {
      const content = document.querySelector('.calculator-content');
      if (content) {
        content.scrollTop = 500;
      }
    });
    
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'calculator-scrolled-render.png', fullPage: false });
    console.log('✅ Screenshot saved as calculator-scrolled-render.png');
    
    // Scroll to bottom
    await page.evaluate(() => {
      const content = document.querySelector('.calculator-content');
      if (content) {
        content.scrollTop = content.scrollHeight;
      }
    });
    
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'calculator-bottom-render.png', fullPage: false });
    console.log('✅ Screenshot saved as calculator-bottom-render.png');
  });
});