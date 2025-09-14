import { test, expect } from '@playwright/test';

test.describe('Debug Calculator Heights', () => {
  test('debug calculator element heights', async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');
    
    // Click Calculator tab
    await page.locator('text=Calculator').first().click();
    await page.waitForTimeout(3000);
    
    // Get detailed height information
    const heights = await page.evaluate(() => {
      const getElementInfo = (selector: string) => {
        const el = document.querySelector(selector);
        if (!el) return null;
        const rect = el.getBoundingClientRect();
        const computed = window.getComputedStyle(el);
        return {
          selector,
          height: rect.height,
          scrollHeight: (el as HTMLElement).scrollHeight,
          clientHeight: (el as HTMLElement).clientHeight,
          offsetHeight: (el as HTMLElement).offsetHeight,
          display: computed.display,
          overflow: computed.overflow,
          overflowY: computed.overflowY,
          position: computed.position,
          flexGrow: computed.flexGrow,
          flexShrink: computed.flexShrink,
          minHeight: computed.minHeight,
          maxHeight: computed.maxHeight,
          padding: computed.padding,
          hasChildren: el.children.length > 0,
          childrenCount: el.children.length
        };
      };
      
      return {
        overlay: getElementInfo('.calculator-overlay'),
        panel: getElementInfo('.calculator-panel'),
        header: getElementInfo('.calculator-header'),
        toolbar: getElementInfo('.calculator-toolbar'),
        preview: getElementInfo('.preview-impact-panel'),
        content: getElementInfo('.calculator-content'),
        footer: getElementInfo('.calculator-footer'),
        sections: Array.from(document.querySelectorAll('.calculator-section')).map((el, i) => ({
          index: i,
          height: el.getBoundingClientRect().height,
          display: window.getComputedStyle(el).display,
          visibility: window.getComputedStyle(el).visibility
        }))
      };
    });
    
    console.log('Element Heights:', JSON.stringify(heights, null, 2));
    
    // Try to manually set height on calculator-content
    await page.evaluate(() => {
      const content = document.querySelector('.calculator-content') as HTMLElement;
      if (content) {
        content.style.height = '400px';
        content.style.minHeight = '400px';
        return true;
      }
      return false;
    });
    
    await page.waitForTimeout(1000);
    
    // Check heights again after manual adjustment
    const afterHeights = await page.evaluate(() => {
      const content = document.querySelector('.calculator-content');
      const panel = document.querySelector('.calculator-panel');
      return {
        content: content ? {
          height: (content as HTMLElement).getBoundingClientRect().height,
          scrollHeight: (content as HTMLElement).scrollHeight,
          style: (content as HTMLElement).style.cssText
        } : null,
        panel: panel ? {
          height: (panel as HTMLElement).getBoundingClientRect().height,
          scrollHeight: (panel as HTMLElement).scrollHeight
        } : null
      };
    });
    
    console.log('\nAfter manual height adjustment:', afterHeights);
    
    await page.screenshot({ path: 'calculator-height-debug.png', fullPage: false });
  });
});