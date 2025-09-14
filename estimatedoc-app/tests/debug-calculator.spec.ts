import { test, expect } from '@playwright/test';

test.describe('Debug Calculator Rendering', () => {
  test('debug calculator rendering issue', async ({ page }) => {
    // Listen for console logs
    page.on('console', msg => {
      console.log(`Browser console [${msg.type()}]: ${msg.text()}`);
    });
    
    // Listen for page errors
    page.on('pageerror', error => {
      console.log(`Page error: ${error.message}`);
    });
    
    console.log('🔍 Navigating to app...\n');
    await page.goto('http://localhost:5173');
    
    await page.waitForLoadState('networkidle');
    
    // Check initial calculator state in store
    const initialState = await page.evaluate(() => {
      // @ts-ignore
      const store = window.__calculatorStore || window.useCalculatorStore?.getState?.();
      return store ? { isOpen: store.isOpen } : null;
    });
    console.log('Initial calculator state:', initialState);
    
    console.log('\n🔍 Clicking Calculator tab...');
    const calculatorTab = await page.locator('text=Calculator').first();
    await calculatorTab.click();
    
    // Check calculator state after click
    const afterClickState = await page.evaluate(() => {
      // @ts-ignore
      const store = window.__calculatorStore || window.useCalculatorStore?.getState?.();
      return store ? { isOpen: store.isOpen } : null;
    });
    console.log('Calculator state after click:', afterClickState);
    
    // Wait a bit for rendering
    await page.waitForTimeout(2000);
    
    // Check if calculator overlay exists in DOM
    const overlayExists = await page.locator('.calculator-overlay').count();
    console.log(`\nCalculator overlay elements in DOM: ${overlayExists}`);
    
    // Check if calculator panel exists
    const panelExists = await page.locator('.calculator-panel').count();
    console.log(`Calculator panel elements in DOM: ${panelExists}`);
    
    // Get the computed styles of the overlay if it exists
    if (overlayExists > 0) {
      const overlayStyles = await page.locator('.calculator-overlay').first().evaluate(el => {
        const styles = window.getComputedStyle(el);
        return {
          display: styles.display,
          visibility: styles.visibility,
          opacity: styles.opacity,
          position: styles.position,
          width: styles.width,
          height: styles.height,
          right: styles.right
        };
      });
      console.log('\nCalculator overlay styles:', overlayStyles);
    }
    
    // Check if there's any content in the calculator
    if (panelExists > 0) {
      const panelContent = await page.locator('.calculator-panel').first().evaluate(el => {
        return {
          childCount: el.children.length,
          hasContent: el.innerHTML.length > 0,
          firstChildTag: el.children[0]?.tagName,
          innerHTML: el.innerHTML.substring(0, 200) // First 200 chars
        };
      });
      console.log('\nCalculator panel content:', panelContent);
    }
    
    // Try to manually trigger the calculator open through console
    console.log('\n🔍 Manually triggering calculator open...');
    await page.evaluate(() => {
      // @ts-ignore
      if (window.useCalculatorStore) {
        // @ts-ignore
        const store = window.useCalculatorStore.getState();
        store.openCalculator();
        return true;
      }
      return false;
    });
    
    await page.waitForTimeout(2000);
    
    // Check final state
    const finalOverlayCount = await page.locator('.calculator-overlay').count();
    const finalPanelCount = await page.locator('.calculator-panel').count();
    
    console.log('\n📊 Final Summary:');
    console.log('================');
    console.log(`Calculator overlay in DOM: ${finalOverlayCount > 0 ? 'YES' : 'NO'}`);
    console.log(`Calculator panel in DOM: ${finalPanelCount > 0 ? 'YES' : 'NO'}`);
    
    // Take a screenshot
    await page.screenshot({ path: 'debug-calculator.png', fullPage: true });
    console.log('\n📸 Debug screenshot saved as debug-calculator.png');
  });
});