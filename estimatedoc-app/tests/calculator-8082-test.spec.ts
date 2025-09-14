import { test, expect } from '@playwright/test';

test.describe('Calculator on Port 8082 Test', () => {
  test('test calculator appearance and functionality on port 8082', async ({ page }) => {
    console.log('🔍 Testing calculator on port 8082...\n');
    
    // Navigate to port 8082
    await page.goto('http://localhost:8082');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Take initial screenshot
    await page.screenshot({ 
      path: 'tests/screenshots/calculator-8082-initial.png', 
      fullPage: true 
    });
    console.log('📸 Initial screenshot saved\n');
    
    // Check if calculator button exists and click it
    const calcButton = page.locator('button').filter({ hasText: /calculator/i }).first();
    const calcButtonExists = await calcButton.count() > 0;
    
    if (calcButtonExists) {
      console.log('✓ Calculator button found, clicking...');
      await calcButton.click();
      await page.waitForTimeout(1000);
      
      // Take screenshot after opening calculator
      await page.screenshot({ 
        path: 'tests/screenshots/calculator-8082-opened.png', 
        fullPage: true 
      });
      console.log('📸 Calculator opened screenshot saved\n');
      
      // Check calculator modal/panel
      const calculatorPanel = page.locator('.calculator-panel, .calculator-modal, [class*="calculator"]').first();
      const calcPanelVisible = await calculatorPanel.isVisible().catch(() => false);
      
      console.log(`Calculator panel visible: ${calcPanelVisible}`);
      
      if (calcPanelVisible) {
        // Check for input fields
        const inputs = await page.locator('.calculator-panel input, .calculator-modal input, [class*="calculator"] input').all();
        console.log(`\nFound ${inputs.length} input fields in calculator`);
        
        // Try to interact with first few inputs
        for (let i = 0; i < Math.min(3, inputs.length); i++) {
          const input = inputs[i];
          const placeholder = await input.getAttribute('placeholder').catch(() => 'unknown');
          const currentValue = await input.inputValue().catch(() => '');
          
          console.log(`\nInput ${i + 1}:`);
          console.log(`  Placeholder: ${placeholder}`);
          console.log(`  Current value: ${currentValue}`);
          
          try {
            await input.click();
            await input.fill('100');
            const newValue = await input.inputValue();
            console.log(`  ✓ Successfully changed value to: ${newValue}`);
          } catch (error) {
            console.log(`  ✗ Could not interact with input: ${error.message}`);
          }
        }
        
        // Take screenshot after interaction
        await page.screenshot({ 
          path: 'tests/screenshots/calculator-8082-interacted.png', 
          fullPage: true 
        });
        console.log('\n📸 Calculator after interaction screenshot saved');
        
        // Check for any visual issues
        const calculatorElement = await calculatorPanel.boundingBox();
        if (calculatorElement) {
          console.log('\nCalculator dimensions:');
          console.log(`  Width: ${calculatorElement.width}px`);
          console.log(`  Height: ${calculatorElement.height}px`);
          console.log(`  Position: (${calculatorElement.x}, ${calculatorElement.y})`);
        }
        
        // Check for overlapping or broken layout
        const allTexts = await page.locator('.calculator-panel *, .calculator-modal *, [class*="calculator"] *').evaluateAll(elements => {
          return elements.slice(0, 10).map(el => {
            const styles = window.getComputedStyle(el);
            return {
              text: el.textContent?.trim().substring(0, 50),
              display: styles.display,
              position: styles.position,
              zIndex: styles.zIndex,
              overflow: styles.overflow
            };
          });
        });
        
        console.log('\nFirst 10 calculator elements styles:');
        allTexts.forEach((item, i) => {
          if (item.text) {
            console.log(`  ${i + 1}. "${item.text}" - display: ${item.display}, position: ${item.position}`);
          }
        });
      }
    } else {
      console.log('✗ Calculator button not found');
      
      // Check if calculator is already visible
      const calculatorVisible = await page.locator('.calculator-panel, .calculator-modal, [class*="calculator"]').first().isVisible().catch(() => false);
      console.log(`Calculator already visible: ${calculatorVisible}`);
      
      if (calculatorVisible) {
        await page.screenshot({ 
          path: 'tests/screenshots/calculator-8082-already-visible.png', 
          fullPage: true 
        });
        console.log('📸 Calculator already visible screenshot saved');
      }
    }
    
    // Final summary
    console.log('\n📊 Calculator Test Summary:');
    console.log('===========================');
    console.log(`Calculator button found: ${calcButtonExists ? 'YES' : 'NO'}`);
    console.log(`Screenshots saved in tests/screenshots/`);
  });
});