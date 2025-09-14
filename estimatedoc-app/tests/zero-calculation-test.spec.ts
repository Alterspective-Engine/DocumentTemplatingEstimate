import { test, expect } from '@playwright/test';

test.describe('Zero Calculation Test', () => {
  test('should show 0 hours when all calculator values are set to 0', async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:5173');
    
    // Wait for documents to load
    await page.waitForSelector('.document-card', { timeout: 10000 });
    
    // Open calculator
    await page.click('button:has-text("Effort Calculator")');
    
    // Wait for calculator to open
    await page.waitForSelector('.calculator-panel', { timeout: 5000 });
    
    // Set all field time estimates to 0
    const sliders = await page.$$('.calculator-panel input[type="range"]');
    
    for (const slider of sliders) {
      await slider.evaluate((el: HTMLInputElement) => {
        el.value = '0';
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
      });
    }
    
    // Apply settings
    await page.click('button:has-text("Apply Settings")');
    
    // Wait for recalculation
    await page.waitForTimeout(1000);
    
    // Check that all document cards show 0 hours
    const effortValues = await page.$$eval('.document-card .effort-value', 
      elements => elements.map(el => el.textContent)
    );
    
    // All effort values should be "0.0 hrs" or similar
    for (const value of effortValues) {
      const numericValue = parseFloat(value?.replace(' hrs', '') || '0');
      expect(numericValue).toBe(0);
    }
    
    console.log('✅ Zero calculation test passed - all documents show 0 hours when all values are 0');
  });
  
  test('should use real SQL data', async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:5173');
    
    // Wait for documents to load
    await page.waitForSelector('.document-card', { timeout: 10000 });
    
    // Check data source indicator
    const dataSource = await page.textContent('.stat-item:has-text("Data Source") .stat-value');
    expect(dataSource).toBe('SQL');
    
    // Check document count (should be 782 from SQL data)
    const docCount = await page.textContent('.stat-item:has-text("Documents") .stat-value');
    expect(parseInt(docCount || '0')).toBe(782);
    
    console.log('✅ SQL data test passed - using 782 documents from SQL source');
  });
  
  test('reload data button should work', async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:5173');
    
    // Wait for initial load
    await page.waitForSelector('.document-card', { timeout: 10000 });
    
    // Click reload button
    await page.click('button:has-text("Reload Data")');
    
    // Wait for reload to complete
    await page.waitForTimeout(2000);
    
    // Documents should still be loaded
    const cards = await page.$$('.document-card');
    expect(cards.length).toBeGreaterThan(0);
    
    console.log('✅ Reload data test passed');
  });
});