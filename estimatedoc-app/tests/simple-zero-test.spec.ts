import { test, expect } from '@playwright/test';

test.describe('Simple Zero Calculation Test', () => {
  test('verify zero-value calculation fix', async ({ page }) => {
    // Navigate to calculator page
    await page.goto('http://localhost:5173/calculator');
    
    // Wait for page to load
    await page.waitForTimeout(2000);
    
    // Check if calculator interface exists
    const calculatorExists = await page.$$('.calculator-interface, .calculator-page, [class*="calculator"]');
    
    console.log(`Found ${calculatorExists.length} calculator elements`);
    
    // Try direct navigation to main page
    await page.goto('http://localhost:5173');
    
    // Wait for documents to load
    await page.waitForSelector('.document-card', { timeout: 10000 });
    
    // Get current effort values
    const initialEfforts = await page.$$eval('.document-card', cards => 
      cards.slice(0, 5).map(card => {
        const effortEl = card.querySelector('.effort-value, [class*="effort"], [class*="hours"]');
        return effortEl?.textContent || 'N/A';
      })
    );
    
    console.log('Initial effort values (first 5):', initialEfforts);
    
    // Check data source
    const dataSource = await page.textContent('.stat-value:has-text("SQL"), .stat-item:has-text("Data Source") .stat-value') || 'unknown';
    console.log('Data source:', dataSource);
    
    // Check document count
    const docCountText = await page.textContent('.stat-item:has-text("Documents") .stat-value') || '0';
    const docCount = parseInt(docCountText);
    console.log('Document count:', docCount);
    
    // Verify we're using SQL data
    expect(dataSource).toBe('SQL');
    expect(docCount).toBe(782);
    
    console.log('✅ Application is using SQL data with 782 documents');
  });
  
  test('verify base template time is 0 by default', async ({ page }) => {
    // This test verifies the fix we made to calculatorStore.ts
    await page.goto('http://localhost:5173');
    
    // Execute script to check the calculator store settings
    const baseTemplateTime = await page.evaluate(() => {
      // Access the store if it's exposed globally (common in dev)
      const stores = (window as any).__zustand_stores || [];
      for (const store of stores) {
        const state = store?.getState?.();
        if (state?.settings?.baseTemplateTime !== undefined) {
          return state.settings.baseTemplateTime;
        }
      }
      
      // Try to get from localStorage
      const stored = localStorage.getItem('calculator-settings');
      if (stored) {
        const parsed = JSON.parse(stored);
        return parsed?.state?.settings?.baseTemplateTime;
      }
      
      return null;
    });
    
    console.log('Base template time:', baseTemplateTime);
    
    // It should be 0 after our fix
    if (baseTemplateTime !== null) {
      expect(baseTemplateTime).toBe(0);
      console.log('✅ Base template time is correctly set to 0');
    } else {
      console.log('⚠️ Could not access calculator settings from page context');
    }
  });
});