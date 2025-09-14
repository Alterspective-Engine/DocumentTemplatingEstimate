import { test, expect } from '@playwright/test';

test.describe('Check Calculation Values', () => {
  test('verify calculation for test doc.docx', async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:5173');
    
    // Wait for documents to load
    await page.waitForSelector('.document-card', { timeout: 10000 });
    
    // Get the calculator settings from localStorage
    const settings = await page.evaluate(() => {
      const stored = localStorage.getItem('calculator-settings');
      if (stored) {
        const parsed = JSON.parse(stored);
        return parsed?.state?.settings || null;
      }
      return null;
    });
    
    console.log('Current calculator settings:');
    if (settings) {
      console.log('- Base template time:', settings.baseTemplateTime, 'minutes');
      console.log('- Precedent Script time:', settings.fieldTimeEstimates?.precedentScript?.current, 'minutes');
      console.log('- Complexity multipliers:', {
        simple: settings.complexityMultipliers?.simple?.current,
        moderate: settings.complexityMultipliers?.moderate?.current,
        complex: settings.complexityMultipliers?.complex?.current
      });
      console.log('- Optimization:', {
        reuse: settings.optimization?.reuseEfficiency?.current,
        learning: settings.optimization?.learningCurve?.current,
        automation: settings.optimization?.automationPotential?.current
      });
    }
    
    // Click on test doc.docx
    await page.click('.document-card:has-text("test doc.docx")');
    
    // Wait for detail modal
    await page.waitForSelector('.document-detail-modal', { timeout: 5000 });
    
    // Click on Calculation Details tab
    await page.click('button:has-text("Calculation Details")');
    
    // Get calculation values
    const calcValues = await page.evaluate(() => {
      const rows = document.querySelectorAll('.calculation-steps .step-row, .calculation-section tr');
      const values: any = {};
      
      rows.forEach(row => {
        const label = row.querySelector('.step-label, td:first-child')?.textContent?.trim();
        const value = row.querySelector('.step-value, td:last-child')?.textContent?.trim();
        if (label && value) {
          values[label] = value;
        }
      });
      
      // Also get the final result
      const finalResult = document.querySelector('.final-result-value, [class*="final"] [class*="value"], .effort-result')?.textContent?.trim();
      if (finalResult) {
        values['Final Result'] = finalResult;
      }
      
      return values;
    });
    
    console.log('\nCalculation values from UI:');
    Object.entries(calcValues).forEach(([key, value]) => {
      console.log(`- ${key}: ${value}`);
    });
    
    // Manual calculation check
    console.log('\n--- Manual Calculation Check ---');
    console.log('Document: test doc.docx');
    console.log('Field Types: 4 Precedent Scripts');
    
    const baseTime = settings?.baseTemplateTime || 0;
    const precedentTime = settings?.fieldTimeEstimates?.precedentScript?.current || 30;
    const moderateMultiplier = settings?.complexityMultipliers?.moderate?.current || 1.5;
    
    const fieldTimeMinutes = 4 * precedentTime;
    const totalBaseMinutes = baseTime + fieldTimeMinutes;
    const totalBaseHours = totalBaseMinutes / 60;
    const withComplexity = totalBaseHours * moderateMultiplier;
    
    console.log(`\nExpected calculation:`);
    console.log(`1. Base template: ${baseTime} minutes = ${baseTime/60} hours`);
    console.log(`2. Field time: 4 × ${precedentTime} minutes = ${fieldTimeMinutes} minutes = ${fieldTimeMinutes/60} hours`);
    console.log(`3. Total base: ${totalBaseMinutes} minutes = ${totalBaseHours} hours`);
    console.log(`4. With Moderate complexity (×${moderateMultiplier}): ${withComplexity} hours`);
    
    // Check if base hours matches expectation
    const baseHoursText = calcValues['Base Hours:'] || calcValues['Base Hours'] || '';
    const baseHoursValue = parseFloat(baseHoursText);
    
    console.log(`\n✓ Base hours from UI: ${baseHoursValue}`);
    console.log(`✓ Expected base hours: ${withComplexity}`);
    
    if (Math.abs(baseHoursValue - withComplexity) > 0.1) {
      console.error(`❌ MISMATCH: Base hours should be ${withComplexity} but showing ${baseHoursValue}`);
    } else {
      console.log('✅ Base hours calculation is correct');
    }
  });
});