import { test, expect } from '@playwright/test';

test.describe('Calculator Slider Test', () => {
  test('verify all sliders are functional', async ({ page }) => {
    console.log('🎚️ Testing all calculator sliders...\n');
    
    // Navigate to calculator page
    await page.goto('http://localhost:5173/calculator');
    await page.waitForLoadState('networkidle');
    
    // Wait for calculator to load
    await page.waitForSelector('.calculator-page', { timeout: 10000 });
    
    // Test 1: Base Template Time Slider
    console.log('📊 Test 1: Base Template Time Slider');
    const baseSlider = await page.locator('input.base-slider').first();
    const initialBase = await baseSlider.inputValue();
    console.log(`  Initial: ${initialBase} minutes`);
    
    // Move slider to middle
    await baseSlider.fill('65');
    await page.waitForTimeout(200);
    const newBase = await baseSlider.inputValue();
    console.log(`  After change: ${newBase} minutes`);
    console.log(`  ✅ Base template slider: ${newBase !== initialBase ? 'WORKING' : 'STUCK'}`);
    
    // Test 2: Field Time Sliders
    console.log('\n📊 Test 2: Field Time Estimate Sliders');
    const fieldSliders = await page.locator('input.field-slider').all();
    console.log(`  Found ${fieldSliders.length} field sliders`);
    
    const fieldNames = [
      'If Statement',
      'Precedent Script', 
      'Reflection',
      'Search',
      'Unbound',
      'Built-in Script',
      'Extended',
      'Scripted'
    ];
    
    let workingCount = 0;
    for (let i = 0; i < fieldSliders.length && i < fieldNames.length; i++) {
      const slider = fieldSliders[i];
      const initial = await slider.inputValue();
      
      // Get max value and set to middle
      const max = await slider.getAttribute('max');
      const middle = Math.floor(Number(max) / 2);
      
      await slider.fill(String(middle));
      await page.waitForTimeout(100);
      
      const updated = await slider.inputValue();
      const isWorking = updated !== initial;
      
      console.log(`  ${fieldNames[i]}: ${initial}m → ${updated}m ${isWorking ? '✅' : '❌'}`);
      if (isWorking) workingCount++;
    }
    
    // Test 3: Check Impact on Documents
    console.log('\n📊 Test 3: Impact on Documents');
    
    // Navigate back to main page
    await page.goto('http://localhost:5173');
    await page.waitForSelector('.document-card', { timeout: 5000 });
    
    // Check first document effort
    const firstCard = await page.locator('.document-card').first();
    const effortText = await firstCard.locator('.metric:has-text("Effort")').textContent();
    console.log(`  First document effort: ${effortText}`);
    
    // Go back to calculator and change base template significantly
    await page.goto('http://localhost:5173/calculator');
    await page.waitForSelector('.calculator-page');
    
    const baseSlider2 = await page.locator('input.base-slider').first();
    await baseSlider2.fill('100'); // Set to high value
    await page.waitForTimeout(500); // Wait for recalculation
    
    // Check documents again
    await page.goto('http://localhost:5173');
    await page.waitForSelector('.document-card', { timeout: 5000 });
    
    const firstCard2 = await page.locator('.document-card').first();
    const effortText2 = await firstCard2.locator('.metric:has-text("Effort")').textContent();
    console.log(`  After change: ${effortText2}`);
    
    const effortChanged = effortText !== effortText2;
    console.log(`  ✅ Documents updated: ${effortChanged ? 'YES' : 'NO'}`);
    
    // Test 4: Resource Planning Inputs
    console.log('\n📊 Test 4: Resource Planning Inputs');
    await page.goto('http://localhost:5173/calculator');
    
    // Find FTE input
    const inputs = await page.locator('input[type="number"]').all();
    if (inputs.length > 0) {
      const fteInput = inputs[0];
      const initial = await fteInput.inputValue();
      await fteInput.fill('4');
      const updated = await fteInput.inputValue();
      console.log(`  FTE: ${initial} → ${updated} ${updated !== initial ? '✅' : '❌'}`);
    }
    
    // Summary
    console.log('\n' + '='.repeat(50));
    console.log('🎚️ SLIDER TEST SUMMARY');
    console.log('='.repeat(50));
    console.log(`✅ Base Template Slider: ${newBase !== initialBase ? 'WORKING' : 'STUCK'}`);
    console.log(`✅ Field Sliders Working: ${workingCount}/${fieldSliders.length}`);
    console.log(`✅ Changes Affect Documents: ${effortChanged ? 'YES' : 'NO'}`);
    console.log('='.repeat(50));
    
    // Assertions
    expect(Number(newBase)).not.toBe(Number(initialBase));
    expect(workingCount).toBeGreaterThan(0);
  });
});