import { test, expect } from '@playwright/test';

test.describe('Calculator Verification', () => {
  test('verify calculator is rendering correctly', async ({ page }) => {
    console.log('🔍 Verifying calculator rendering...\n');
    
    await page.goto('http://localhost:5173');
    
    // Wait for the page to fully load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000); // Give extra time for React to render
    
    // Click on the Calculator tab
    const calculatorTab = await page.locator('text=Calculator').first();
    await expect(calculatorTab).toBeVisible({ timeout: 10000 });
    console.log('✅ Calculator tab is visible');
    
    await calculatorTab.click();
    console.log('✅ Clicked on Calculator tab');
    
    // Wait longer for the calculator to fully load and render
    await page.waitForTimeout(5000); // Give calculator plenty of time to load
    
    // Take a screenshot to see what's rendered
    await page.screenshot({ path: 'calculator-state.png', fullPage: true });
    console.log('📸 Screenshot saved as calculator-state.png');
    
    // Wait for the calculator panel to be visible
    const calculatorPanel = await page.locator('[class*="calculator"], [class*="Calculator"], .panel').first();
    const isPanelVisible = await calculatorPanel.isVisible().catch(() => false);
    console.log(`Calculator panel visible: ${isPanelVisible}`);
    
    // Check for any calculator-related content
    const calculatorTitle = await page.locator('text=/effort calculator|calculator settings/i').first();
    const isTitleVisible = await calculatorTitle.isVisible().catch(() => false);
    console.log(`Calculator title visible: ${isTitleVisible}`);
    
    // Look for input fields
    const inputs = await page.locator('input').all();
    console.log(`Found ${inputs.length} input fields on page`);
    
    // Look for any buttons
    const buttons = await page.locator('button').all();
    console.log(`Found ${buttons.length} buttons on page`);
    for (let i = 0; i < Math.min(5, buttons.length); i++) {
      const text = await buttons[i].textContent().catch(() => 'N/A');
      console.log(`  Button ${i + 1}: "${text}"`);
    }
    
    // Check for any error messages
    const errors = await page.locator('.error, [class*="error"]').all();
    if (errors.length > 0) {
      console.log(`⚠️ Found ${errors.length} error elements`);
      for (const error of errors) {
        const errorText = await error.textContent().catch(() => '');
        if (errorText) console.log(`  Error: ${errorText}`);
      }
    }
    
    // Check console for any errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`❌ Console error: ${msg.text()}`);
      }
    });
    
    // Wait a bit more to catch any delayed errors
    await page.waitForTimeout(2000);
    
    console.log('\n📊 Calculator Verification Summary:');
    console.log('===================================');
    console.log(`Calculator tab accessible: ${await calculatorTab.isVisible()}`);
    console.log(`Calculator panel found: ${isPanelVisible}`);
    console.log(`Input fields present: ${inputs.length > 0}`);
    console.log(`Buttons present: ${buttons.length > 0}`);
    
    // Final screenshot
    await page.screenshot({ path: 'calculator-final-state.png', fullPage: true });
    console.log('📸 Final screenshot saved as calculator-final-state.png');
  });
});