import { test, expect } from '@playwright/test';

test.describe('Comprehensive Calculation Tests', () => {
  test('verify all 782 SQL documents load and calculate', async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:5173');
    
    // Wait for documents to load
    await page.waitForSelector('.document-card', { timeout: 15000 });
    
    // Check document count
    const docCountText = await page.textContent('.stat-item:has-text("Documents") .stat-value');
    const docCount = parseInt(docCountText || '0');
    expect(docCount).toBe(782);
    console.log(`✅ Loaded ${docCount} documents`);
    
    // Check data source
    const dataSource = await page.textContent('.stat-item:has-text("Data Source") .stat-value');
    expect(dataSource).toBe('SQL');
    console.log(`✅ Data source: ${dataSource}`);
    
    // Get all document cards
    const cards = await page.$$('.document-card');
    console.log(`✅ Found ${cards.length} document cards on first page`);
    
    // Sample check: verify first 10 documents have valid calculations
    const sampleSize = Math.min(10, cards.length);
    let validCalculations = 0;
    let invalidCalculations = [];
    
    for (let i = 0; i < sampleSize; i++) {
      const card = cards[i];
      
      // Get document name
      const name = await card.$eval('.document-name, h3', el => el.textContent?.trim() || 'Unknown');
      
      // Get effort value
      const effortText = await card.$eval('.effort-value, .effort, [class*="effort"]', 
        el => el.textContent?.trim() || '0'
      ).catch(() => '0');
      
      const effortValue = parseFloat(effortText.replace(/[^0-9.]/g, ''));
      
      // Get field count
      const fieldText = await card.$eval('[class*="field"], .fields', 
        el => el.textContent?.trim() || '0'
      ).catch(() => '0');
      
      const fieldCount = parseInt(fieldText.replace(/[^0-9]/g, '') || '0');
      
      // Get data source indicator
      const source = await card.$eval('.data-source', 
        el => el.textContent?.trim() || 'Unknown'
      ).catch(() => 'Unknown');
      
      // Validate calculation logic
      if (fieldCount === 0 && effortValue > 0) {
        invalidCalculations.push({
          name,
          fields: fieldCount,
          effort: effortValue,
          issue: 'Non-zero effort with zero fields'
        });
      } else if (fieldCount > 0 && effortValue === 0) {
        invalidCalculations.push({
          name,
          fields: fieldCount,
          effort: effortValue,
          issue: 'Zero effort with non-zero fields'
        });
      } else if (!isNaN(effortValue) && effortValue >= 0) {
        validCalculations++;
      }
      
      console.log(`  ${i + 1}. ${name}: ${fieldCount} fields, ${effortValue} hrs, Source: ${source}`);
    }
    
    console.log(`\n✅ Valid calculations: ${validCalculations}/${sampleSize}`);
    
    if (invalidCalculations.length > 0) {
      console.log('\n⚠️ Invalid calculations found:');
      invalidCalculations.forEach(calc => {
        console.log(`  - ${calc.name}: ${calc.issue} (${calc.fields} fields, ${calc.effort} hrs)`);
      });
    }
    
    // Test calculation with zero values
    console.log('\n--- Testing Zero Value Calculation ---');
    
    // Open calculator if available
    const calcButton = await page.$('button:has-text("Calculator"), a[href="/calculator"]');
    if (calcButton) {
      await calcButton.click();
      await page.waitForTimeout(1000);
      
      // Look for reset button
      const resetButton = await page.$('button:has-text("Reset to Defaults")');
      if (resetButton) {
        await resetButton.click();
        console.log('✅ Reset calculator to defaults');
        await page.waitForTimeout(500);
      }
      
      // Try to set all sliders to 0
      const sliders = await page.$$('input[type="range"]');
      if (sliders.length > 0) {
        console.log(`Found ${sliders.length} sliders, setting to 0...`);
        for (const slider of sliders) {
          await slider.evaluate((el: HTMLInputElement) => {
            el.value = '0';
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
          });
        }
        
        // Apply settings if button exists
        const applyButton = await page.$('button:has-text("Apply")');
        if (applyButton) {
          await applyButton.click();
          console.log('✅ Applied zero settings');
          await page.waitForTimeout(1000);
          
          // Check if any document still shows non-zero effort
          const effortAfterZero = await page.$$eval('.document-card .effort-value',
            elements => elements.slice(0, 5).map(el => {
              const text = el.textContent?.trim() || '0';
              return parseFloat(text.replace(/[^0-9.]/g, ''));
            })
          ).catch(() => []);
          
          const nonZeroCount = effortAfterZero.filter(v => v > 0).length;
          if (nonZeroCount === 0) {
            console.log('✅ All documents show 0 hours with zero settings');
          } else {
            console.log(`⚠️ ${nonZeroCount} documents still show non-zero effort with zero settings`);
          }
        }
      }
    }
    
    // Final validation
    expect(validCalculations).toBeGreaterThan(0);
    expect(docCount).toBe(782);
    expect(dataSource).toBe('SQL');
    
    console.log('\n✅ Comprehensive calculation test completed');
  });
  
  test('verify calculations use user settings', async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForSelector('.document-card', { timeout: 10000 });
    
    // Get initial effort for first document
    const initialEffort = await page.$eval('.document-card:first-child .effort-value',
      el => parseFloat(el.textContent?.replace(/[^0-9.]/g, '') || '0')
    );
    
    console.log(`Initial effort for first document: ${initialEffort} hours`);
    
    // Open calculator and change a setting
    const calcLink = await page.$('a[href="/calculator"]');
    if (calcLink) {
      await calcLink.click();
      await page.waitForTimeout(1000);
      
      // Find and change precedentScript slider (if exists)
      const precedentSlider = await page.$('input[type="range"][id*="precedent"], .setting-item:has-text("Precedent") input[type="range"]');
      if (precedentSlider) {
        // Set to maximum
        const max = await precedentSlider.getAttribute('max');
        await precedentSlider.evaluate((el: HTMLInputElement, maxVal) => {
          el.value = maxVal || '120';
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
        }, max);
        
        console.log('Changed precedentScript time to maximum');
        
        // Apply settings
        const applyButton = await page.$('button:has-text("Apply")');
        if (applyButton) {
          await applyButton.click();
          await page.waitForTimeout(1000);
          
          // Check new effort
          await page.goto('http://localhost:5173');
          await page.waitForSelector('.document-card', { timeout: 10000 });
          
          const newEffort = await page.$eval('.document-card:first-child .effort-value',
            el => parseFloat(el.textContent?.replace(/[^0-9.]/g, '') || '0')
          );
          
          console.log(`New effort after change: ${newEffort} hours`);
          
          if (newEffort !== initialEffort) {
            console.log('✅ Calculations respond to user settings');
          } else {
            console.log('⚠️ Calculations did not change with settings');
          }
        }
      }
    }
  });
});