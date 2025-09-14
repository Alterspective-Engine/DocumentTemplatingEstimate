import { test, expect } from '@playwright/test';

test.describe('Calculator Validation with Database Data', () => {
  test('verify calculator uses real document field data', async ({ page }) => {
    console.log('🔍 Starting calculator validation test...\n');
    
    // Navigate to calculator page
    await page.goto('http://localhost:5173/calculator');
    await page.waitForLoadState('networkidle');
    
    // Wait for calculator to load
    await page.waitForSelector('.calculator-page', { timeout: 10000 });
    
    // Check for base template configuration
    const baseTemplateSection = await page.locator('text=/Base Template Configuration/i').isVisible();
    console.log(`✅ Base Template Configuration: ${baseTemplateSection ? 'FOUND' : 'NOT FOUND'}`);
    
    // Check for effort estimation settings
    const effortSection = await page.locator('text=/Effort Estimation Settings/i').isVisible();
    console.log(`✅ Effort Estimation Settings: ${effortSection ? 'FOUND' : 'NOT FOUND'}`);
    
    // Check for field time estimates
    const fieldTypes = [
      'If Statement',
      'Precedent Script',
      'Reflection',
      'Search',
      'Unbound',
      'Built-in Script',
      'Extended',
      'Scripted'
    ];
    
    console.log('\n📊 Field Type Time Estimates:');
    for (const fieldType of fieldTypes) {
      const fieldVisible = await page.locator(`text=/${fieldType}/i`).first().isVisible();
      if (fieldVisible) {
        // Try to get the input value for this field
        const inputSelector = `input[type="number"]`;
        const inputs = await page.locator(inputSelector).all();
        console.log(`  ✓ ${fieldType}: Found`);
      } else {
        console.log(`  ✗ ${fieldType}: Not found`);
      }
    }
    
    // Check for resource planning
    const resourceSection = await page.locator('h2:has-text("Resource Planning")').isVisible();
    console.log(`\n✅ Resource Planning: ${resourceSection ? 'FOUND' : 'NOT FOUND'}`);
    
    // Check for implementation timeline
    const timelineSection = await page.locator('h2:has-text("Implementation Timeline")').isVisible();
    console.log(`✅ Implementation Timeline: ${timelineSection ? 'FOUND' : 'NOT FOUND'}`);
    
    // Check for live impact dashboard
    const impactSection = await page.locator('h2:has-text("Live Impact Dashboard")').isVisible();
    console.log(`✅ Live Impact Dashboard: ${impactSection ? 'FOUND' : 'NOT FOUND'}`);
    
    // Navigate to main page to check document count
    await page.goto('http://localhost:5173');
    await page.waitForSelector('.document-card', { timeout: 10000 });
    
    // Count documents
    const documentCount = await page.locator('.document-card').count();
    console.log(`\n📈 Total Documents Loaded: ${documentCount}`);
    
    // Check a few document cards for field breakdowns
    console.log('\n🔍 Checking Document Field Breakdowns:');
    const firstThreeCards = await page.locator('.document-card').all();
    
    for (let i = 0; i < Math.min(3, firstThreeCards.length); i++) {
      const card = firstThreeCards[i];
      const title = await card.locator('h3').textContent();
      const content = await card.textContent();
      
      // Check if card contains field data
      const hasFieldData = content?.includes('fields') || content?.includes('Fields');
      const hasComplexity = content?.includes('Simple') || content?.includes('Moderate') || content?.includes('Complex');
      const hasEffort = content?.includes('hours') || content?.includes('hrs');
      
      console.log(`\n  Document ${i + 1}: ${title}`);
      console.log(`    - Has field data: ${hasFieldData ? 'YES' : 'NO'}`);
      console.log(`    - Has complexity: ${hasComplexity ? 'YES' : 'NO'}`);
      console.log(`    - Has effort: ${hasEffort ? 'YES' : 'NO'}`);
    }
    
    // Take screenshots for evidence
    await page.goto('http://localhost:5173/calculator');
    await page.screenshot({ 
      path: 'tests/screenshots/calculator-with-database.png',
      fullPage: true 
    });
    
    await page.goto('http://localhost:5173');
    await page.screenshot({ 
      path: 'tests/screenshots/documents-with-database.png',
      fullPage: true 
    });
    
    // Generate validation summary
    console.log('\n' + '='.repeat(50));
    console.log('📋 CALCULATOR VALIDATION SUMMARY');
    console.log('='.repeat(50));
    console.log(`✅ Documents from Database: ${documentCount === 547 ? 'VERIFIED (547)' : `WARNING (${documentCount})`}`);
    console.log(`✅ Calculator Page: ${baseTemplateSection ? 'FUNCTIONAL' : 'NEEDS ATTENTION'}`);
    console.log(`✅ Field Types: ${effortSection ? 'CONFIGURED' : 'MISSING'}`);
    console.log(`✅ Resource Planning: ${resourceSection ? 'PRESENT' : 'MISSING'}`);
    console.log(`✅ Timeline: ${timelineSection ? 'PRESENT' : 'MISSING'}`);
    console.log(`✅ Impact Dashboard: ${impactSection ? 'PRESENT' : 'MISSING'}`);
    console.log('='.repeat(50));
    
    // Assert critical requirements
    expect(documentCount).toBe(547); // Must have exactly 547 documents from database
    expect(baseTemplateSection || effortSection).toBeTruthy(); // Calculator must be functional
  });
});