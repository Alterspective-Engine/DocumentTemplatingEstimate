import { test, expect } from '@playwright/test';

test.describe('Search Field Diagnosis', () => {
  test('diagnose search field interaction issues', async ({ page }) => {
    // Navigate to the application
    await page.goto('http://localhost:5173');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Take a screenshot for visual analysis
    await page.screenshot({ path: 'tests/screenshots/initial-page.png', fullPage: true });
    
    // Try to locate the search input field with multiple strategies
    const searchSelectors = [
      'input[placeholder*="Search"]',
      'input[type="text"]',
      '.search-input',
      '.search-bar input',
      'input'
    ];
    
    let searchInput = null;
    let workingSelector = null;
    
    console.log('🔍 Attempting to find search input...');
    
    for (const selector of searchSelectors) {
      try {
        const element = await page.locator(selector).first();
        const count = await element.count();
        console.log(`  Selector "${selector}": Found ${count} element(s)`);
        
        if (count > 0) {
          searchInput = element;
          workingSelector = selector;
          
          // Get detailed information about the element
          const boundingBox = await element.boundingBox();
          const isVisible = await element.isVisible();
          const isEnabled = await element.isEnabled();
          const isEditable = await element.isEditable();
          
          console.log(`  ✓ Found search input with selector: ${selector}`);
          console.log(`    - Visible: ${isVisible}`);
          console.log(`    - Enabled: ${isEnabled}`);
          console.log(`    - Editable: ${isEditable}`);
          console.log(`    - Position: ${JSON.stringify(boundingBox)}`);
          
          // Check computed styles
          const styles = await element.evaluate((el) => {
            const computed = window.getComputedStyle(el);
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
              readOnly: (el as HTMLInputElement).readOnly
            };
          });
          
          console.log('    - Computed styles:', JSON.stringify(styles, null, 2));
          
          // Check for overlapping elements
          const overlappingElements = await page.evaluate((selector) => {
            const input = document.querySelector(selector);
            if (!input) return null;
            
            const rect = input.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            
            // Get element at center point
            const elementAtPoint = document.elementFromPoint(centerX, centerY);
            
            // Check if there's an overlay
            const hasOverlay = elementAtPoint !== input;
            
            return {
              hasOverlay,
              overlayElement: hasOverlay ? {
                tagName: elementAtPoint?.tagName,
                className: elementAtPoint?.className,
                id: elementAtPoint?.id
              } : null
            };
          }, workingSelector);
          
          console.log('    - Overlay check:', JSON.stringify(overlappingElements, null, 2));
          
          break;
        }
      } catch (error) {
        console.log(`  ✗ Selector "${selector}" failed:`, error.message);
      }
    }
    
    if (!searchInput) {
      throw new Error('Could not find search input field');
    }
    
    // Try different interaction methods
    console.log('\n🖱️ Testing interaction methods...');
    
    // Method 1: Standard click
    try {
      await searchInput.click({ timeout: 5000 });
      console.log('  ✓ Standard click successful');
    } catch (error) {
      console.log('  ✗ Standard click failed:', error.message);
      
      // Method 2: Force click
      try {
        await searchInput.click({ force: true });
        console.log('  ✓ Force click successful');
      } catch (error2) {
        console.log('  ✗ Force click failed:', error2.message);
        
        // Method 3: JavaScript click
        try {
          await searchInput.evaluate((el) => (el as HTMLElement).click());
          console.log('  ✓ JavaScript click successful');
        } catch (error3) {
          console.log('  ✗ JavaScript click failed:', error3.message);
        }
      }
    }
    
    // Try to focus the element
    console.log('\n🎯 Testing focus methods...');
    
    try {
      await searchInput.focus();
      console.log('  ✓ Focus successful');
      
      // Check if actually focused
      const isFocused = await searchInput.evaluate((el) => el === document.activeElement);
      console.log(`  - Element is focused: ${isFocused}`);
    } catch (error) {
      console.log('  ✗ Focus failed:', error.message);
      
      // Try JavaScript focus
      try {
        await searchInput.evaluate((el) => (el as HTMLElement).focus());
        console.log('  ✓ JavaScript focus successful');
      } catch (error2) {
        console.log('  ✗ JavaScript focus failed:', error2.message);
      }
    }
    
    // Try to type in the field
    console.log('\n⌨️ Testing typing...');
    
    try {
      await searchInput.type('test search', { delay: 100 });
      console.log('  ✓ Typing successful');
      
      // Get the value
      const value = await searchInput.inputValue();
      console.log(`  - Input value: "${value}"`);
    } catch (error) {
      console.log('  ✗ Typing failed:', error.message);
      
      // Try fill method
      try {
        await searchInput.fill('test search');
        console.log('  ✓ Fill successful');
        
        const value = await searchInput.inputValue();
        console.log(`  - Input value: "${value}"`);
      } catch (error2) {
        console.log('  ✗ Fill failed:', error2.message);
      }
    }
    
    // Take screenshot after interaction attempts
    await page.screenshot({ path: 'tests/screenshots/after-interaction.png', fullPage: true });
    
    // Check for any error messages in console
    const consoleLogs: string[] = [];
    page.on('console', msg => consoleLogs.push(`${msg.type()}: ${msg.text()}`));
    
    // Final diagnosis
    console.log('\n📊 Diagnosis Summary:');
    console.log('====================');
    
    if (searchInput) {
      const finalValue = await searchInput.inputValue();
      const isFocused = await searchInput.evaluate((el) => el === document.activeElement);
      
      console.log(`Search input found: YES`);
      console.log(`Can interact: ${finalValue.length > 0 ? 'YES' : 'PARTIAL/NO'}`);
      console.log(`Final value: "${finalValue}"`);
      console.log(`Is focused: ${isFocused}`);
      
      if (finalValue.length === 0) {
        console.log('\n⚠️ ISSUE DETECTED: Search input exists but cannot accept input');
        console.log('Possible causes:');
        console.log('  1. Element is disabled or readonly');
        console.log('  2. Another element is overlaying the input');
        console.log('  3. CSS pointer-events is set to none');
        console.log('  4. JavaScript event handlers are preventing input');
      }
    }
    
    // Return diagnostic data
    return {
      searchInputFound: !!searchInput,
      selector: workingSelector,
      consoleLogs
    };
  });
});