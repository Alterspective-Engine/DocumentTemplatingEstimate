import { test, expect } from '@playwright/test';

test.describe('Calculation Engine Test', () => {
  test('verify calculations work with database data', async ({ page }) => {
    console.log('🧮 Testing calculation engine with database data...\n');
    
    // Enable console logging to see what's happening
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log('❌ Console error:', msg.text());
      }
    });
    
    // Navigate to main page
    await page.goto('http://localhost:5173');
    
    // Wait a moment for app to initialize
    await page.waitForTimeout(2000);
    
    // Check if we have any document cards
    const hasCards = await page.locator('.document-card').count();
    console.log(`📊 Document cards found: ${hasCards}`);
    
    if (hasCards === 0) {
      // Try to find error messages
      const bodyText = await page.locator('body').textContent();
      console.log('Page content:', bodyText?.substring(0, 500));
      
      // Check if there's a loading state stuck
      const loading = await page.locator('text=/loading/i').count();
      console.log(`Loading indicators: ${loading}`);
    } else {
      // Get first 3 documents to check calculations
      const cards = await page.locator('.document-card').all();
      
      for (let i = 0; i < Math.min(3, cards.length); i++) {
        const card = cards[i];
        const title = await card.locator('h3').textContent();
        const complexity = await card.locator('.complexity-badge').textContent();
        const effortElement = await card.locator('.metric:has-text("Effort")');
        const effortText = await effortElement.textContent();
        
        console.log(`\n📄 Document ${i + 1}: ${title}`);
        console.log(`  Complexity: ${complexity}`);
        console.log(`  Effort: ${effortText}`);
        
        // Check if effort has a calculated value
        if (effortText && (effortText.includes('h') || effortText.includes('m'))) {
          console.log(`  ✅ Has calculated effort`);
        } else {
          console.log(`  ❌ Missing effort calculation`);
        }
      }
    }
    
    // Now navigate to calculator
    console.log('\n🔧 Navigating to calculator page...');
    await page.goto('http://localhost:5173/calculator');
    await page.waitForTimeout(1000);
    
    // Check base template time
    const baseSlider = await page.locator('input.base-slider').first();
    if (await baseSlider.isVisible()) {
      const value = await baseSlider.inputValue();
      console.log(`\n⏱️ Base Template Time: ${value} minutes`);
      
      // Try to change it using a different method
      await baseSlider.click();
      await baseSlider.press('End'); // Move to max
      await page.waitForTimeout(500);
      
      const newValue = await baseSlider.inputValue();
      console.log(`  After pressing End: ${newValue} minutes`);
      
      if (newValue === value) {
        console.log('  ❌ Slider not responding to keyboard input');
        
        // Try setting via JavaScript
        await page.evaluate(() => {
          const slider = document.querySelector('input.base-slider') as HTMLInputElement;
          if (slider) {
            slider.value = '80';
            slider.dispatchEvent(new Event('change', { bubbles: true }));
            slider.dispatchEvent(new Event('input', { bubbles: true }));
          }
        });
        
        await page.waitForTimeout(500);
        const jsValue = await baseSlider.inputValue();
        console.log(`  After JS update: ${jsValue} minutes`);
      }
    }
    
    // Check if settings object exists
    const hasSettings = await page.evaluate(() => {
      return typeof (window as any).useCalculatorStore !== 'undefined';
    });
    console.log(`\n🔧 Calculator store available: ${hasSettings ? 'YES' : 'NO'}`);
    
    // Get current settings from store
    if (hasSettings) {
      const settings = await page.evaluate(() => {
        const store = (window as any).useCalculatorStore?.getState?.();
        return store?.settings;
      });
      
      if (settings) {
        console.log('\n📋 Current Settings:');
        console.log(`  Base Template Time: ${settings.baseTemplateTime || 'NOT SET'}`);
        console.log(`  Field Estimates: ${Object.keys(settings.fieldTimeEstimates || {}).length} types`);
      }
    }
    
    // Final summary
    console.log('\n' + '='.repeat(50));
    console.log('📋 CALCULATION ENGINE SUMMARY');
    console.log('='.repeat(50));
    console.log(`Documents loaded: ${hasCards}`);
    console.log(`Calculator page: ${await page.locator('.calculator-page').isVisible() ? 'VISIBLE' : 'NOT VISIBLE'}`);
    console.log(`Base template slider: ${await baseSlider.isVisible() ? 'VISIBLE' : 'NOT VISIBLE'}`);
    console.log('='.repeat(50));
    
    // Take a screenshot
    await page.screenshot({ 
      path: 'tests/screenshots/calculation-test.png',
      fullPage: true 
    });
  });
});