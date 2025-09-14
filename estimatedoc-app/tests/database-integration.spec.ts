import { test, expect } from '@playwright/test';

test.describe('Database Integration Test', () => {
  test('verify database documents are loaded', async ({ page }) => {
    // Navigate to the application
    await page.goto('http://localhost:5173');
    
    // Wait for documents to load
    await page.waitForSelector('.document-card', { timeout: 10000 });
    
    // Check console for database loading message
    const consoleMessages: string[] = [];
    page.on('console', msg => {
      consoleMessages.push(msg.text());
    });
    
    // Reload to capture console messages
    await page.reload();
    await page.waitForSelector('.document-card', { timeout: 10000 });
    
    // Count document cards
    const documentCards = await page.locator('.document-card').count();
    console.log(`📊 Found ${documentCards} document cards`);
    
    // Check for database loading message in console
    const dbMessage = consoleMessages.find(msg => msg.includes('Loading') && msg.includes('documents'));
    console.log(`💾 Database message: ${dbMessage || 'Not found'}`);
    
    // Verify we have documents from database (should be 547)
    expect(documentCards).toBeGreaterThan(500);
    
    // Check if statistics show correct count
    const statsText = await page.locator('.statistics-card').first().textContent();
    console.log(`📈 Statistics: ${statsText}`);
    
    // Navigate to calculator page
    await page.goto('http://localhost:5173/calculator');
    await page.waitForLoadState('networkidle');
    
    // Check if calculator page has document data
    const hasCalculatorContent = await page.locator('.calculator-page').isVisible();
    expect(hasCalculatorContent).toBeTruthy();
    
    // Take screenshots for evidence
    await page.screenshot({ 
      path: 'tests/screenshots/database-main-page.png',
      fullPage: true 
    });
    
    await page.goto('http://localhost:5173/calculator');
    await page.screenshot({ 
      path: 'tests/screenshots/database-calculator-page.png',
      fullPage: true 
    });
    
    console.log('✅ Database integration test completed');
    console.log(`✅ Total documents loaded: ${documentCards}`);
    
    // Generate summary
    console.log('\n📋 Database Integration Summary:');
    console.log('================================');
    console.log(`Documents loaded: ${documentCards}`);
    console.log(`Source: ${dbMessage?.includes('database') ? 'DATABASE' : 'HARDCODED'}`);
    console.log(`Calculator page: ${hasCalculatorContent ? 'WORKING' : 'NOT WORKING'}`);
    console.log('Screenshots saved to tests/screenshots/');
  });
});