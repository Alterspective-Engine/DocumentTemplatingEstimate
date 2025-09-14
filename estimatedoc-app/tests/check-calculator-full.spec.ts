import { test, expect } from '@playwright/test';

test.describe('Check Full Calculator', () => {
  test('check if calculator content is fully rendered', async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');
    
    // Click Calculator tab
    await page.locator('text=Calculator').first().click();
    await page.waitForTimeout(5000); // Long wait to ensure everything loads
    
    // Scroll the calculator panel to see if content exists below
    const scrollInfo = await page.evaluate(() => {
      const panel = document.querySelector('.calculator-content');
      const overlay = document.querySelector('.calculator-overlay');
      const calculatorPanel = document.querySelector('.calculator-panel');
      
      if (panel) {
        // Try to scroll the panel
        panel.scrollTop = panel.scrollHeight;
      }
      
      return {
        contentExists: !!panel,
        contentScrollHeight: panel?.scrollHeight || 0,
        contentClientHeight: panel?.clientHeight || 0,
        contentChildren: panel?.children.length || 0,
        overlayHeight: overlay?.getBoundingClientRect().height || 0,
        panelHeight: calculatorPanel?.getBoundingClientRect().height || 0,
        panelScrollHeight: calculatorPanel?.scrollHeight || 0,
        sections: Array.from(document.querySelectorAll('.calculator-section')).map(s => ({
          className: s.className,
          height: s.getBoundingClientRect().height,
          visible: s.getBoundingClientRect().height > 0
        }))
      };
    });
    
    console.log('Calculator Content Info:', scrollInfo);
    
    // Check for the main calculator sections
    const sections = await page.evaluate(() => {
      return {
        fieldTimeEstimates: !!document.querySelector('.calculator-section h3[class*="Field Time"]'),
        complexityThresholds: !!document.querySelector('.calculator-section h3[class*="Complexity Thresholds"]'),
        complexityMultipliers: !!document.querySelector('.calculator-section h3[class*="Complexity Multipliers"]'),
        optimization: !!document.querySelector('.calculator-section h3[class*="Optimization"]'),
        footer: !!document.querySelector('.calculator-footer'),
        applyButton: !!document.querySelector('.calculator-footer button[class*="primary"]')
      };
    });
    
    console.log('Calculator Sections Present:', sections);
    
    // Take a full page screenshot
    await page.screenshot({ path: 'calculator-full-check.png', fullPage: true });
    
    // Try scrolling inside the calculator panel if it has scrollable content
    await page.evaluate(() => {
      const content = document.querySelector('.calculator-content');
      if (content) {
        content.scrollTop = 0; // Scroll to top
        return content.scrollHeight;
      }
      return 0;
    });
    
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'calculator-scrolled-top.png', fullPage: false });
    
    // Try to scroll to bottom
    await page.evaluate(() => {
      const content = document.querySelector('.calculator-content');
      if (content) {
        content.scrollTop = content.scrollHeight;
        return content.scrollTop;
      }
      return 0;
    });
    
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'calculator-scrolled-bottom.png', fullPage: false });
  });
});