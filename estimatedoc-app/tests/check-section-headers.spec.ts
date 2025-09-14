import { test, expect } from '@playwright/test';

test.describe('Check Section Headers', () => {
  test('check calculator section headers', async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');
    
    // Click Calculator tab
    await page.locator('text=Calculator').first().click();
    await page.waitForTimeout(3000);
    
    // Check for all h3 elements in calculator
    const headers = await page.evaluate(() => {
      const allH3 = document.querySelectorAll('.calculator-content h3');
      return Array.from(allH3).map(h => ({
        text: h.textContent,
        className: h.className,
        visible: (h as HTMLElement).offsetHeight > 0,
        parent: h.parentElement?.className
      }));
    });
    
    console.log('H3 Headers found:', headers);
    
    // Check for all text content in sections
    const sectionContent = await page.evaluate(() => {
      const sections = document.querySelectorAll('.calculator-section');
      return Array.from(sections).map((section, i) => {
        const firstChild = section.firstElementChild;
        return {
          index: i,
          firstChildTag: firstChild?.tagName,
          firstChildClass: firstChild?.className,
          firstChildText: firstChild?.textContent?.substring(0, 50),
          innerHTML: section.innerHTML.substring(0, 200)
        };
      });
    });
    
    console.log('\nSection Content:', sectionContent);
    
    // Check for specific text
    const hasFieldTimeText = await page.locator('text=/Field Time Estimates/i').count();
    const hasComplexityText = await page.locator('text=/Complexity/i').count();
    const hasOptimizationText = await page.locator('text=/Optimization/i').count();
    
    console.log('\nText presence:');
    console.log('Field Time Estimates:', hasFieldTimeText);
    console.log('Complexity:', hasComplexityText);
    console.log('Optimization:', hasOptimizationText);
    
    // Scroll the content area to see if headers appear
    await page.evaluate(() => {
      const content = document.querySelector('.calculator-content');
      if (content) {
        content.scrollTop = 0;
      }
    });
    
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'calculator-section-check.png', fullPage: false });
  });
});