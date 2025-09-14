import { test, expect } from '@playwright/test';

test.describe('Azure Deployment Search Test', () => {
  test('test search on Azure deployment', async ({ page }) => {
    // Navigate to the Azure deployment
    await page.goto('https://estimatedoc-app.mangosand-2b84247d.eastus.azurecontainerapps.io');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Take a screenshot for visual analysis
    await page.screenshot({ path: 'tests/screenshots/azure-initial.png', fullPage: true });
    
    console.log('🔍 Testing search on Azure deployment...');
    
    // Try to find and interact with search input
    const searchInput = page.locator('input[placeholder*="Search"]').first();
    
    // Check if element exists
    const count = await searchInput.count();
    console.log(`  Search inputs found: ${count}`);
    
    if (count > 0) {
      // Get element properties
      const isVisible = await searchInput.isVisible();
      const isEnabled = await searchInput.isEnabled();
      const isEditable = await searchInput.isEditable();
      
      console.log(`  - Visible: ${isVisible}`);
      console.log(`  - Enabled: ${isEnabled}`);
      console.log(`  - Editable: ${isEditable}`);
      
      // Check computed styles
      const styles = await searchInput.evaluate((el) => {
        const computed = window.getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        return {
          display: computed.display,
          visibility: computed.visibility,
          pointerEvents: computed.pointerEvents,
          position: computed.position,
          zIndex: computed.zIndex,
          opacity: computed.opacity,
          userSelect: computed.userSelect,
          cursor: computed.cursor,
          disabled: (el as HTMLInputElement).disabled,
          readOnly: (el as HTMLInputElement).readOnly,
          width: rect.width,
          height: rect.height,
          top: rect.top,
          left: rect.left
        };
      });
      
      console.log('  Computed styles:', JSON.stringify(styles, null, 2));
      
      // Check parent elements for potential issues
      const parentStyles = await searchInput.evaluate((el) => {
        const parents = [];
        let currentElement = el.parentElement;
        
        while (currentElement && currentElement !== document.body) {
          const computed = window.getComputedStyle(currentElement);
          parents.push({
            tagName: currentElement.tagName,
            className: currentElement.className,
            pointerEvents: computed.pointerEvents,
            position: computed.position,
            zIndex: computed.zIndex,
            overflow: computed.overflow,
            display: computed.display
          });
          currentElement = currentElement.parentElement;
        }
        
        return parents;
      });
      
      console.log('\n  Parent element styles:');
      parentStyles.forEach((parent, index) => {
        console.log(`    ${index + 1}. ${parent.tagName}.${parent.className}`);
        console.log(`       pointer-events: ${parent.pointerEvents}, position: ${parent.position}, z-index: ${parent.zIndex}`);
      });
      
      // Try to interact
      console.log('\n  Testing interaction:');
      
      try {
        await searchInput.click({ timeout: 5000 });
        console.log('    ✓ Click successful');
      } catch (error) {
        console.log('    ✗ Click failed:', error.message);
        
        // Try force click
        try {
          await searchInput.click({ force: true });
          console.log('    ✓ Force click successful');
        } catch (error2) {
          console.log('    ✗ Force click also failed');
        }
      }
      
      // Try typing
      try {
        await searchInput.type('test', { delay: 100 });
        const value = await searchInput.inputValue();
        console.log(`    ✓ Typing successful, value: "${value}"`);
      } catch (error) {
        console.log('    ✗ Typing failed:', error.message);
        
        // Try fill
        try {
          await searchInput.fill('test');
          const value = await searchInput.inputValue();
          console.log(`    ✓ Fill successful, value: "${value}"`);
        } catch (error2) {
          console.log('    ✗ Fill also failed');
        }
      }
      
      // Take screenshot after interaction
      await page.screenshot({ path: 'tests/screenshots/azure-after-interaction.png', fullPage: true });
    } else {
      console.log('  ✗ No search input found on Azure deployment');
      
      // Try to find any input elements
      const allInputs = await page.locator('input').all();
      console.log(`  Total input elements on page: ${allInputs.length}`);
      
      for (let i = 0; i < allInputs.length; i++) {
        const input = allInputs[i];
        const placeholder = await input.getAttribute('placeholder');
        const type = await input.getAttribute('type');
        console.log(`    Input ${i + 1}: type="${type}", placeholder="${placeholder}"`);
      }
    }
    
    // Check for any JavaScript errors
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    
    if (errors.length > 0) {
      console.log('\n  JavaScript errors detected:');
      errors.forEach(err => console.log(`    - ${err}`));
    }
    
    // Final summary
    console.log('\n📊 Azure Deployment Summary:');
    console.log('===========================');
    console.log(`Search field present: ${count > 0 ? 'YES' : 'NO'}`);
    
    if (count > 0) {
      const finalValue = await searchInput.inputValue();
      console.log(`Can interact: ${finalValue.length > 0 ? 'YES' : 'NO'}`);
      console.log(`Final value: "${finalValue}"`);
    }
  });
});