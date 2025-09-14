import { test, expect } from '@playwright/test';

test.describe('Inspect Calculator Styles', () => {
  test('inspect calculator panel computed styles', async ({ page }) => {
    console.log('🔍 Navigating to app...\n');
    await page.goto('http://localhost:5173');
    
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    console.log('🔍 Clicking Calculator tab...');
    const calculatorTab = await page.locator('text=Calculator').first();
    await calculatorTab.click();
    
    await page.waitForTimeout(3000);
    
    // Get all elements inside calculator panel
    const panelElements = await page.evaluate(() => {
      const panel = document.querySelector('.calculator-panel');
      if (!panel) return null;
      
      const getAllElements = (el: Element, depth = 0): any => {
        if (depth > 3) return null; // Limit depth
        
        const styles = window.getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        
        return {
          tag: el.tagName,
          className: el.className,
          visible: rect.width > 0 && rect.height > 0,
          dimensions: {
            width: rect.width,
            height: rect.height,
            top: rect.top,
            left: rect.left
          },
          styles: {
            display: styles.display,
            visibility: styles.visibility,
            opacity: styles.opacity,
            background: styles.background?.substring(0, 100),
            color: styles.color,
            overflow: styles.overflow,
            position: styles.position,
            zIndex: styles.zIndex
          },
          textContent: el.textContent?.substring(0, 50),
          childCount: el.children.length,
          children: depth < 2 ? Array.from(el.children).slice(0, 3).map(child => getAllElements(child, depth + 1)) : []
        };
      };
      
      return getAllElements(panel);
    });
    
    console.log('\nCalculator Panel Structure:');
    console.log(JSON.stringify(panelElements, null, 2));
    
    // Check if content is actually visible
    const isContentVisible = await page.evaluate(() => {
      const headers = document.querySelectorAll('.calculator-header h2, .calculator-header h3');
      const buttons = document.querySelectorAll('.calculator-panel button');
      const inputs = document.querySelectorAll('.calculator-panel input');
      
      return {
        headerCount: headers.length,
        headerTexts: Array.from(headers).map(h => h.textContent),
        buttonCount: buttons.length,
        inputCount: inputs.length,
        firstButtonText: buttons[0]?.textContent,
        panelHeight: document.querySelector('.calculator-panel')?.getBoundingClientRect().height,
        overlayHeight: document.querySelector('.calculator-overlay')?.getBoundingClientRect().height
      };
    });
    
    console.log('\nContent Visibility Check:');
    console.log(isContentVisible);
    
    // Take screenshot with specific viewport
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.screenshot({ path: 'calculator-inspect.png', fullPage: false });
    console.log('\n📸 Screenshot saved as calculator-inspect.png');
  });
});