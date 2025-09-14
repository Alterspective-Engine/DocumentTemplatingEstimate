import { test, expect } from '@playwright/test';

test.describe('Debug Calculator Width', () => {
  test('debug calculator width issues', async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');
    
    // Click Calculator tab
    await page.locator('text=Calculator').first().click();
    await page.waitForTimeout(3000);
    
    // Get width information for all elements
    const widths = await page.evaluate(() => {
      const getWidth = (selector: string) => {
        const el = document.querySelector(selector);
        if (!el) return null;
        const rect = el.getBoundingClientRect();
        const computed = window.getComputedStyle(el);
        return {
          selector,
          width: rect.width,
          clientWidth: (el as HTMLElement).clientWidth,
          scrollWidth: (el as HTMLElement).scrollWidth,
          padding: computed.padding,
          paddingLeft: computed.paddingLeft,
          paddingRight: computed.paddingRight,
          overflow: computed.overflow,
          overflowX: computed.overflowX,
          boxSizing: computed.boxSizing
        };
      };
      
      // Get first slider info
      const firstSlider = document.querySelector('.slider-container');
      const sliderInfo = firstSlider ? {
        width: firstSlider.getBoundingClientRect().width,
        parentWidth: firstSlider.parentElement?.getBoundingClientRect().width,
        display: window.getComputedStyle(firstSlider).display
      } : null;
      
      // Get settings grid info
      const settingsGrid = document.querySelector('.settings-grid');
      const gridInfo = settingsGrid ? {
        width: settingsGrid.getBoundingClientRect().width,
        display: window.getComputedStyle(settingsGrid).display,
        gridTemplateColumns: window.getComputedStyle(settingsGrid).gridTemplateColumns
      } : null;
      
      return {
        overlay: getWidth('.calculator-overlay'),
        panel: getWidth('.calculator-panel'),
        content: getWidth('.calculator-content'),
        section: getWidth('.calculator-section'),
        firstSlider: sliderInfo,
        settingsGrid: gridInfo,
        footer: getWidth('.calculator-footer')
      };
    });
    
    console.log('Width Debug Info:', JSON.stringify(widths, null, 2));
    
    // Check if content is being clipped
    const isClipped = await page.evaluate(() => {
      const content = document.querySelector('.calculator-content');
      if (!content) return false;
      return (content as HTMLElement).scrollWidth > (content as HTMLElement).clientWidth;
    });
    
    console.log('\nContent is horizontally clipped:', isClipped);
    
    // Get all input elements to see if they're visible
    const inputs = await page.evaluate(() => {
      const inputs = document.querySelectorAll('.calculator-content input');
      return Array.from(inputs).slice(0, 3).map(input => {
        const rect = input.getBoundingClientRect();
        return {
          type: input.getAttribute('type'),
          visible: rect.width > 0 && rect.height > 0,
          width: rect.width,
          left: rect.left,
          right: rect.right
        };
      });
    });
    
    console.log('\nInput visibility:', inputs);
    
    await page.screenshot({ path: 'calculator-width-debug.png', fullPage: false });
  });
});