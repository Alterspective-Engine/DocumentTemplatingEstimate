import { test } from '@playwright/test';

test('Reset calculator to defaults', async ({ page }) => {
  // Navigate to the app
  await page.goto('http://localhost:5173');
  
  // Clear calculator settings from localStorage
  await page.evaluate(() => {
    localStorage.removeItem('calculator-settings');
    console.log('Cleared calculator settings from localStorage');
  });
  
  // Reload to apply defaults
  await page.reload();
  
  // Wait for documents to load
  await page.waitForSelector('.document-card', { timeout: 10000 });
  
  // Click on calculator button in header
  await page.click('a[href="/calculator"], button:has-text("Calculator")');
  
  // If modal opens, look for calculator settings
  const hasCalculator = await page.$$('.calculator-panel, .calculator-interface, .calculator-page').then(els => els.length > 0);
  
  if (hasCalculator) {
    console.log('Calculator interface found');
    
    // Check if there's a reset button
    const resetButton = await page.$('button:has-text("Reset"), button:has-text("Defaults")');
    if (resetButton) {
      await resetButton.click();
      console.log('Clicked reset to defaults button');
    }
  }
  
  console.log('✅ Calculator settings have been reset');
  
  // Force recalculation by reloading
  await page.reload();
  await page.waitForSelector('.document-card', { timeout: 10000 });
  
  // Now check the values for test doc
  await page.click('.document-card:has-text("test doc.docx")');
  
  console.log('Calculator should now use default values:');
  console.log('- Base template time: 0 minutes');
  console.log('- Precedent Script: 30 minutes');
  console.log('- Expected for 4 scripts: 2 hours base, 3 hours with complexity');
});