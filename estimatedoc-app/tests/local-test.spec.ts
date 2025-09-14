import { test, expect } from '@playwright/test';

test.describe('Local Deployment Test', () => {
  test('test version and search on local deployment', async ({ page }) => {
    // Navigate to local deployment
    await page.goto('http://localhost:8081');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    console.log('🔍 Testing local deployment...');
    
    // Check for version display
    const versionElement = await page.locator('text=/v0\\.0\\.0-/').first();
    const versionExists = await versionElement.count() > 0;
    console.log(`  Version display found: ${versionExists}`);
    
    if (versionExists) {
      const versionText = await versionElement.textContent();
      console.log(`  Version text: ${versionText}`);
    }
    
    // Check search input
    const searchInput = page.locator('input[placeholder*="Search"]').first();
    const searchCount = await searchInput.count();
    console.log(`  Search inputs found: ${searchCount}`);
    
    if (searchCount > 0) {
      const isVisible = await searchInput.isVisible();
      const isEnabled = await searchInput.isEnabled();
      
      console.log(`  - Visible: ${isVisible}`);
      console.log(`  - Enabled: ${isEnabled}`);
      
      // Check for glass-panel class
      const listHeader = await page.locator('.list-header').first();
      const headerClasses = await listHeader.getAttribute('class');
      console.log(`  Header classes: ${headerClasses}`);
      const hasGlassPanel = headerClasses?.includes('glass-panel') || false;
      console.log(`  Has glass-panel class: ${hasGlassPanel}`);
      
      // Try to interact
      console.log('\n  Testing interaction:');
      try {
        await searchInput.click({ timeout: 5000 });
        console.log('    ✓ Click successful');
        
        await searchInput.type('test', { delay: 100 });
        const value = await searchInput.inputValue();
        console.log(`    ✓ Typing successful, value: "${value}"`);
      } catch (error) {
        console.log('    ✗ Interaction failed:', error.message);
      }
    }
    
    // Take screenshot
    await page.screenshot({ path: 'tests/screenshots/local-test.png', fullPage: true });
    
    // Summary
    console.log('\n📊 Local Deployment Summary:');
    console.log('===========================');
    console.log(`Version display: ${versionExists ? 'YES' : 'NO'}`);
    console.log(`Search field present: ${searchCount > 0 ? 'YES' : 'NO'}`);
    
    if (searchCount > 0) {
      const finalValue = await searchInput.inputValue();
      console.log(`Can interact: ${finalValue.length > 0 ? 'YES' : 'NO'}`);
    }
  });
});