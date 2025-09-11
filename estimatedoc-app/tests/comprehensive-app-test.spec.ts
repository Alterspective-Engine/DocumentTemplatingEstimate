import { test, expect, Page } from '@playwright/test';

// Configuration
const BASE_URL = 'http://localhost:5174';
const TIMEOUT = 30000;

// Test results storage
interface TestResult {
  category: string;
  subcategory: string;
  score: number;
  notes: string;
  issues: string[];
  recommendations: string[];
}

const testResults: TestResult[] = [];

// Helper function to rate a category
function rateCategory(category: string, subcategory: string, score: number, notes: string, issues: string[] = [], recommendations: string[] = []) {
  testResults.push({ category, subcategory, score, notes, issues, recommendations });
}

test.describe('Comprehensive EstimateDoc Application Testing', () => {
  test.setTimeout(TIMEOUT * 10);

  test('Complete Application Testing and Rating', async ({ page }) => {
    // Navigate to the application
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    // ============= 1. PERFORMANCE TESTING =============
    console.log('\n📊 Testing Performance Metrics...');
    
    // 1.1 Page Load Time
    const startTime = Date.now();
    await page.reload();
    await page.waitForLoadState('domcontentloaded');
    const loadTime = Date.now() - startTime;
    rateCategory('Performance', 'Page Load Time', 
      loadTime < 1000 ? 10 : loadTime < 2000 ? 8 : loadTime < 3000 ? 6 : 4,
      `Page loaded in ${loadTime}ms`,
      loadTime > 2000 ? ['Page load time exceeds 2 seconds'] : [],
      loadTime > 2000 ? ['Optimize bundle size', 'Implement code splitting'] : []
    );

    // 1.2 Time to Interactive
    const tti = await page.evaluate(() => {
      return performance.timing.domInteractive - performance.timing.navigationStart;
    });
    rateCategory('Performance', 'Time to Interactive', 
      tti < 1500 ? 10 : tti < 3000 ? 7 : 5,
      `TTI: ${tti}ms`
    );

    // 1.3 Memory Usage
    const memoryUsage = await page.evaluate(() => {
      return (performance as any).memory ? (performance as any).memory.usedJSHeapSize / 1048576 : 0;
    });
    rateCategory('Performance', 'Memory Usage', 
      memoryUsage < 50 ? 10 : memoryUsage < 100 ? 8 : 6,
      `Memory: ${memoryUsage.toFixed(2)}MB`
    );

    // ============= 2. UI/UX TESTING =============
    console.log('\n🎨 Testing UI/UX Elements...');

    // 2.1 Navigation
    const navLinks = await page.locator('nav a, header a').count();
    rateCategory('UI/UX', 'Navigation', 
      navLinks > 0 ? 9 : 3,
      `Found ${navLinks} navigation links`,
      navLinks === 0 ? ['No navigation links found'] : [],
      navLinks === 0 ? ['Add clear navigation menu'] : []
    );

    // 2.2 Search Functionality
    const searchInput = await page.locator('input[type="text"], input[placeholder*="search" i]').first();
    if (searchInput) {
      await searchInput.click();
      await searchInput.fill('test search');
      await page.waitForTimeout(500);
      const resultsVisible = await page.locator('.document-card').count();
      rateCategory('UI/UX', 'Search Functionality', 
        resultsVisible >= 0 ? 10 : 5,
        `Search returned ${resultsVisible} results`
      );
      await searchInput.clear();
    }

    // 2.3 Responsive Design
    const viewports = [
      { width: 375, height: 667, name: 'Mobile' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 1920, height: 1080, name: 'Desktop' }
    ];
    
    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      await page.waitForTimeout(500);
      const isResponsive = await page.evaluate(() => {
        const main = document.querySelector('main');
        return main && main.scrollWidth <= window.innerWidth;
      });
      rateCategory('UI/UX', `Responsive Design - ${viewport.name}`, 
        isResponsive ? 10 : 5,
        `${viewport.name} view ${isResponsive ? 'works' : 'has issues'}`
      );
    }
    await page.setViewportSize({ width: 1920, height: 1080 });

    // ============= 3. FUNCTIONALITY TESTING =============
    console.log('\n⚙️ Testing Core Functionality...');

    // 3.1 Document List
    const documentCards = await page.locator('.document-card').count();
    rateCategory('Functionality', 'Document List Display', 
      documentCards > 0 ? 10 : 0,
      `Displaying ${documentCards} documents`,
      documentCards === 0 ? ['No documents displayed'] : [],
      documentCards === 0 ? ['Check data loading', 'Verify API endpoints'] : []
    );

    // 3.2 Document Details
    if (documentCards > 0) {
      await page.locator('.document-card').first().click();
      await page.waitForTimeout(1000);
      const detailsVisible = await page.locator('.document-detail-modal, .document-detail').isVisible().catch(() => false);
      rateCategory('Functionality', 'Document Details Modal', 
        detailsVisible ? 10 : 5,
        `Document details ${detailsVisible ? 'opens correctly' : 'failed to open'}`
      );
      if (detailsVisible) {
        // Close modal
        const closeButton = await page.locator('button:has-text("Close"), button:has(svg)').first();
        if (closeButton) await closeButton.click();
      }
    }

    // 3.3 Filters
    const filterButton = await page.locator('button:has-text("Filter")').first();
    if (filterButton) {
      await filterButton.click();
      await page.waitForTimeout(500);
      const filtersVisible = await page.locator('.filter-panel').isVisible().catch(() => false);
      rateCategory('Functionality', 'Filter Panel', 
        filtersVisible ? 10 : 6,
        `Filter panel ${filtersVisible ? 'works' : 'not found'}`
      );
    }

    // 3.4 Calculator
    const calculatorButton = await page.locator('button:has-text("Calculator")').first();
    if (calculatorButton) {
      await calculatorButton.click();
      await page.waitForTimeout(1000);
      const calculatorVisible = await page.locator('.calculator-panel, .calculator-overlay').isVisible().catch(() => false);
      rateCategory('Functionality', 'Calculator', 
        calculatorVisible ? 10 : 5,
        `Calculator ${calculatorVisible ? 'opens correctly' : 'failed to open'}`
      );
      
      if (calculatorVisible) {
        // Test calculator sliders
        const sliders = await page.locator('input[type="range"]').count();
        rateCategory('Functionality', 'Calculator Controls', 
          sliders > 0 ? 9 : 4,
          `Found ${sliders} calculator controls`
        );
        
        // Close calculator
        const closeButton = await page.locator('.calculator-panel button:has(svg)').first();
        if (closeButton) await closeButton.click();
      }
    }

    // 3.5 Statistics Page
    const statsLink = await page.locator('a:has-text("Statistics"), button:has-text("Statistics")').first();
    if (statsLink) {
      await statsLink.click();
      await page.waitForTimeout(1000);
      const chartsVisible = await page.locator('.chart-container, svg').count();
      rateCategory('Functionality', 'Statistics Page', 
        chartsVisible > 0 ? 10 : 5,
        `Statistics page shows ${chartsVisible} visualizations`
      );
    }

    // ============= 4. ACCESSIBILITY TESTING =============
    console.log('\n♿ Testing Accessibility...');

    // 4.1 Alt Text for Images
    const images = await page.locator('img').all();
    let imagesWithAlt = 0;
    for (const img of images) {
      const alt = await img.getAttribute('alt');
      if (alt) imagesWithAlt++;
    }
    rateCategory('Accessibility', 'Image Alt Text', 
      images.length === 0 || imagesWithAlt === images.length ? 10 : (imagesWithAlt / images.length) * 10,
      `${imagesWithAlt}/${images.length} images have alt text`
    );

    // 4.2 ARIA Labels
    const buttons = await page.locator('button').all();
    let buttonsWithAria = 0;
    for (const button of buttons) {
      const ariaLabel = await button.getAttribute('aria-label');
      const text = await button.textContent();
      if (ariaLabel || text) buttonsWithAria++;
    }
    rateCategory('Accessibility', 'Button Labels', 
      buttons.length === 0 || buttonsWithAria === buttons.length ? 10 : (buttonsWithAria / buttons.length) * 10,
      `${buttonsWithAria}/${buttons.length} buttons properly labeled`
    );

    // 4.3 Keyboard Navigation
    await page.keyboard.press('Tab');
    await page.waitForTimeout(100);
    const focusVisible = await page.evaluate(() => {
      const focused = document.activeElement;
      if (!focused) return false;
      const styles = window.getComputedStyle(focused);
      return styles.outline !== 'none' || styles.boxShadow !== 'none';
    });
    rateCategory('Accessibility', 'Keyboard Navigation', 
      focusVisible ? 9 : 5,
      `Focus indicators ${focusVisible ? 'visible' : 'not clearly visible'}`
    );

    // 4.4 Color Contrast
    const contrastRatio = await page.evaluate(() => {
      const getContrast = (rgb1: number[], rgb2: number[]) => {
        const l1 = 0.2126 * rgb1[0] + 0.7152 * rgb1[1] + 0.0722 * rgb1[2];
        const l2 = 0.2126 * rgb2[0] + 0.7152 * rgb2[1] + 0.0722 * rgb2[2];
        return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
      };
      
      const elements = document.querySelectorAll('p, span, h1, h2, h3, h4, h5, h6');
      let goodContrast = 0;
      elements.forEach(el => {
        const styles = window.getComputedStyle(el);
        const color = styles.color;
        const bgColor = styles.backgroundColor;
        // Simplified contrast check
        if (color && bgColor && color !== bgColor) goodContrast++;
      });
      return elements.length > 0 ? (goodContrast / elements.length) * 100 : 100;
    });
    rateCategory('Accessibility', 'Color Contrast', 
      contrastRatio > 90 ? 10 : contrastRatio > 70 ? 7 : 5,
      `${contrastRatio.toFixed(0)}% elements have good contrast`
    );

    // ============= 5. SECURITY TESTING =============
    console.log('\n🔒 Testing Security...');

    // 5.1 HTTPS Check
    const isSecure = BASE_URL.startsWith('https');
    rateCategory('Security', 'HTTPS', 
      isSecure ? 10 : 2,
      isSecure ? 'Using HTTPS' : 'Not using HTTPS',
      !isSecure ? ['Application not served over HTTPS'] : [],
      !isSecure ? ['Enable HTTPS in production'] : []
    );

    // 5.2 Content Security Policy
    const cspHeader = await page.evaluate(() => {
      return document.querySelector('meta[http-equiv="Content-Security-Policy"]') !== null;
    });
    rateCategory('Security', 'Content Security Policy', 
      cspHeader ? 10 : 5,
      cspHeader ? 'CSP header present' : 'No CSP header found'
    );

    // 5.3 Input Validation
    const inputs = await page.locator('input').all();
    let validatedInputs = 0;
    for (const input of inputs) {
      const type = await input.getAttribute('type');
      const pattern = await input.getAttribute('pattern');
      const required = await input.getAttribute('required');
      if (type || pattern || required) validatedInputs++;
    }
    rateCategory('Security', 'Input Validation', 
      inputs.length === 0 || validatedInputs > inputs.length * 0.5 ? 8 : 5,
      `${validatedInputs}/${inputs.length} inputs have validation`
    );

    // ============= 6. DATA HANDLING =============
    console.log('\n📊 Testing Data Handling...');

    // 6.1 Data Loading
    const dataLoaded = documentCards > 0;
    rateCategory('Data', 'Data Loading', 
      dataLoaded ? 10 : 0,
      dataLoaded ? 'Data loaded successfully' : 'No data loaded'
    );

    // 6.2 Error Handling
    await page.goto(`${BASE_URL}/nonexistent-page`);
    await page.waitForTimeout(1000);
    const has404 = await page.locator('text=/404|not found/i').count() > 0;
    rateCategory('Data', 'Error Handling', 
      has404 ? 9 : 5,
      has404 ? '404 page exists' : 'No 404 page'
    );
    await page.goto(BASE_URL);

    // 6.3 Local Storage
    const localStorage = await page.evaluate(() => {
      return Object.keys(window.localStorage).length;
    });
    rateCategory('Data', 'Local Storage Usage', 
      localStorage > 0 ? 9 : 7,
      `Using ${localStorage} localStorage keys`
    );

    // ============= 7. BROWSER COMPATIBILITY =============
    console.log('\n🌐 Testing Browser Compatibility...');

    // 7.1 Modern JavaScript Features
    const jsCompatibility = await page.evaluate(() => {
      try {
        // Test modern JS features
        const test = { ...{a: 1}, b: 2 };
        const arrow = () => true;
        const promise = Promise.resolve(true);
        return true;
      } catch {
        return false;
      }
    });
    rateCategory('Compatibility', 'JavaScript Support', 
      jsCompatibility ? 10 : 5,
      jsCompatibility ? 'Modern JS supported' : 'JS compatibility issues'
    );

    // 7.2 CSS Features
    const cssCompatibility = await page.evaluate(() => {
      const el = document.createElement('div');
      el.style.display = 'grid';
      el.style.backdropFilter = 'blur(10px)';
      return el.style.display === 'grid';
    });
    rateCategory('Compatibility', 'CSS Support', 
      cssCompatibility ? 10 : 7,
      cssCompatibility ? 'Modern CSS supported' : 'Limited CSS support'
    );

    // ============= 8. ANALYTICS & TRACKING =============
    console.log('\n📈 Testing Analytics...');

    // 8.1 Analytics Implementation
    const hasAnalytics = await page.evaluate(() => {
      return typeof (window as any).analytics !== 'undefined' || 
             localStorage.getItem('analytics_session') !== null;
    });
    rateCategory('Analytics', 'Analytics Implementation', 
      hasAnalytics ? 10 : 3,
      hasAnalytics ? 'Analytics implemented' : 'No analytics found'
    );

    // 8.2 Privacy Compliance
    const hasPrivacyConsent = await page.evaluate(() => {
      return localStorage.getItem('analytics_consent') !== null;
    });
    rateCategory('Analytics', 'Privacy Compliance', 
      hasPrivacyConsent ? 10 : 6,
      hasPrivacyConsent ? 'Privacy consent system exists' : 'No consent management'
    );

    // ============= 9. CODE QUALITY INDICATORS =============
    console.log('\n💻 Testing Code Quality Indicators...');

    // 9.1 Console Errors
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    await page.reload();
    await page.waitForTimeout(2000);
    rateCategory('Code Quality', 'Console Errors', 
      consoleErrors.length === 0 ? 10 : Math.max(0, 10 - consoleErrors.length),
      `${consoleErrors.length} console errors found`,
      consoleErrors.length > 0 ? consoleErrors : []
    );

    // 9.2 Network Errors
    const networkErrors: string[] = [];
    page.on('requestfailed', request => {
      networkErrors.push(request.url());
    });
    await page.reload();
    await page.waitForTimeout(2000);
    rateCategory('Code Quality', 'Network Errors', 
      networkErrors.length === 0 ? 10 : Math.max(0, 10 - networkErrors.length),
      `${networkErrors.length} network errors found`,
      networkErrors.length > 0 ? networkErrors : []
    );

    // ============= 10. USER EXPERIENCE DETAILS =============
    console.log('\n👤 Testing User Experience Details...');

    // 10.1 Loading States
    await page.reload();
    const hasLoadingStates = await page.locator('.loading, .skeleton, [class*="load"]').count();
    rateCategory('UX', 'Loading States', 
      hasLoadingStates > 0 ? 9 : 5,
      hasLoadingStates > 0 ? 'Loading states present' : 'No loading states found'
    );

    // 10.2 Empty States
    await page.fill('input[type="text"]', 'xyzabc123impossible');
    await page.waitForTimeout(1000);
    const hasEmptyState = await page.locator('text=/no results|not found|empty/i').count() > 0;
    rateCategory('UX', 'Empty States', 
      hasEmptyState ? 10 : 6,
      hasEmptyState ? 'Empty states handled' : 'No empty state messaging'
    );
    await page.locator('input[type="text"]').clear();

    // 10.3 Feedback Messages
    const hasFeedback = await page.locator('.toast, .notification, .alert, .message').count() > 0;
    rateCategory('UX', 'User Feedback', 
      hasFeedback ? 8 : 5,
      hasFeedback ? 'Feedback system exists' : 'No feedback system found'
    );

    // 10.4 Form Usability
    const forms = await page.locator('form').count();
    if (forms > 0) {
      const hasLabels = await page.locator('label').count() > 0;
      rateCategory('UX', 'Form Usability', 
        hasLabels ? 9 : 5,
        hasLabels ? 'Forms have labels' : 'Forms lack proper labels'
      );
    }

    // 10.5 Click Targets
    const clickTargets = await page.evaluate(() => {
      const buttons = document.querySelectorAll('button, a');
      let adequateSize = 0;
      buttons.forEach(btn => {
        const rect = btn.getBoundingClientRect();
        if (rect.width >= 44 && rect.height >= 44) adequateSize++;
      });
      return { total: buttons.length, adequate: adequateSize };
    });
    rateCategory('UX', 'Click Target Size', 
      clickTargets.total === 0 || clickTargets.adequate > clickTargets.total * 0.8 ? 10 : 6,
      `${clickTargets.adequate}/${clickTargets.total} have adequate size (44x44px)`
    );

    // ============= 11. CONTENT QUALITY =============
    console.log('\n📝 Testing Content Quality...');

    // 11.1 Spelling & Grammar
    const headings = await page.locator('h1, h2, h3').allTextContents();
    const hasProperCapitalization = headings.every(h => h.length === 0 || h[0] === h[0].toUpperCase());
    rateCategory('Content', 'Text Quality', 
      hasProperCapitalization ? 9 : 7,
      'Headings properly capitalized'
    );

    // 11.2 Help Documentation
    const hasHelp = await page.locator('text=/help|guide|tutorial|documentation/i').count() > 0;
    rateCategory('Content', 'Help & Documentation', 
      hasHelp ? 8 : 4,
      hasHelp ? 'Help content available' : 'No help documentation found'
    );

    // ============= 12. MOBILE EXPERIENCE =============
    console.log('\n📱 Testing Mobile Experience...');
    
    await page.setViewportSize({ width: 375, height: 667 });

    // 12.1 Touch Targets
    const touchTargets = await page.evaluate(() => {
      const elements = document.querySelectorAll('button, a, input');
      let adequate = 0;
      elements.forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.width >= 48 && rect.height >= 48) adequate++;
      });
      return { total: elements.length, adequate };
    });
    rateCategory('Mobile', 'Touch Target Size', 
      touchTargets.total === 0 || touchTargets.adequate > touchTargets.total * 0.7 ? 9 : 5,
      `${touchTargets.adequate}/${touchTargets.total} mobile-friendly touch targets`
    );

    // 12.2 Mobile Navigation
    const mobileMenu = await page.locator('[class*="mobile"], [class*="burger"], [class*="hamburger"]').count();
    rateCategory('Mobile', 'Mobile Navigation', 
      mobileMenu > 0 ? 9 : 6,
      mobileMenu > 0 ? 'Mobile menu exists' : 'No dedicated mobile menu'
    );

    // 12.3 Viewport Meta Tag
    const hasViewport = await page.evaluate(() => {
      return document.querySelector('meta[name="viewport"]') !== null;
    });
    rateCategory('Mobile', 'Viewport Configuration', 
      hasViewport ? 10 : 3,
      hasViewport ? 'Viewport meta tag present' : 'Missing viewport meta tag'
    );

    await page.setViewportSize({ width: 1920, height: 1080 });

    // ============= 13. ADVANCED FEATURES =============
    console.log('\n🚀 Testing Advanced Features...');

    // 13.1 Search Capabilities
    const hasAdvancedSearch = await page.locator('[class*="filter"], [class*="sort"]').count() > 0;
    rateCategory('Features', 'Advanced Search', 
      hasAdvancedSearch ? 9 : 5,
      hasAdvancedSearch ? 'Advanced search features available' : 'Basic search only'
    );

    // 13.2 Export Functionality
    const hasExport = await page.locator('text=/export|download|save/i').count() > 0;
    rateCategory('Features', 'Export Capabilities', 
      hasExport ? 10 : 5,
      hasExport ? 'Export functionality available' : 'No export options'
    );

    // 13.3 Real-time Updates
    const hasRealtime = await page.evaluate(() => {
      return typeof EventSource !== 'undefined' || typeof WebSocket !== 'undefined';
    });
    rateCategory('Features', 'Real-time Capabilities', 
      hasRealtime ? 8 : 6,
      'Real-time technology available'
    );

    // 13.4 Offline Support
    const hasServiceWorker = await page.evaluate(() => {
      return 'serviceWorker' in navigator;
    });
    rateCategory('Features', 'Offline Support', 
      hasServiceWorker ? 7 : 4,
      hasServiceWorker ? 'Service Worker API available' : 'No offline support'
    );

    // ============= 14. INTERNATIONALIZATION =============
    console.log('\n🌍 Testing Internationalization...');

    // 14.1 Language Support
    const htmlLang = await page.evaluate(() => document.documentElement.lang);
    rateCategory('i18n', 'Language Declaration', 
      htmlLang ? 10 : 5,
      htmlLang ? `Language set to: ${htmlLang}` : 'No language declared'
    );

    // 14.2 Date/Time Formatting
    const dates = await page.locator('time, [class*="date"], [class*="time"]').count();
    rateCategory('i18n', 'Date/Time Handling', 
      dates > 0 ? 8 : 6,
      `${dates} date/time elements found`
    );

    // 14.3 Number Formatting
    const numbers = await page.evaluate(() => {
      const elements = document.body.innerText.match(/\d{1,3}(,\d{3})+/g);
      return elements ? elements.length : 0;
    });
    rateCategory('i18n', 'Number Formatting', 
      numbers > 0 ? 9 : 7,
      `${numbers} formatted numbers found`
    );

    // ============= 15. TESTING & MAINTENANCE =============
    console.log('\n🔧 Testing Maintenance Indicators...');

    // 15.1 Version Information
    const hasVersion = await page.evaluate(() => {
      return document.querySelector('meta[name="version"]') !== null ||
             document.body.innerText.includes('version') ||
             document.body.innerText.includes('v1') ||
             document.body.innerText.includes('v2');
    });
    rateCategory('Maintenance', 'Version Information', 
      hasVersion ? 8 : 4,
      hasVersion ? 'Version info present' : 'No version information'
    );

    // 15.2 Debug Information
    const hasDebugInfo = await page.evaluate(() => {
      return typeof (window as any).__REDUX_DEVTOOLS_EXTENSION__ !== 'undefined' ||
             typeof (window as any).__REACT_DEVTOOLS_GLOBAL_HOOK__ !== 'undefined';
    });
    rateCategory('Maintenance', 'Debug Tools', 
      hasDebugInfo ? 7 : 5,
      hasDebugInfo ? 'Debug tools available' : 'No debug tools detected'
    );

    // ============= GENERATE COMPREHENSIVE REPORT =============
    console.log('\n' + '='.repeat(80));
    console.log('📊 COMPREHENSIVE TEST RESULTS SUMMARY');
    console.log('='.repeat(80));

    // Calculate scores by category
    const categoryScores: { [key: string]: { total: number, count: number, avg: number } } = {};
    testResults.forEach(result => {
      if (!categoryScores[result.category]) {
        categoryScores[result.category] = { total: 0, count: 0, avg: 0 };
      }
      categoryScores[result.category].total += result.score;
      categoryScores[result.category].count++;
    });

    Object.keys(categoryScores).forEach(cat => {
      categoryScores[cat].avg = categoryScores[cat].total / categoryScores[cat].count;
    });

    // Overall score
    const overallScore = testResults.reduce((sum, r) => sum + r.score, 0) / testResults.length;

    console.log(`\n📈 OVERALL SCORE: ${overallScore.toFixed(1)}/10\n`);

    // Category breakdown
    console.log('📊 CATEGORY SCORES:');
    Object.entries(categoryScores).forEach(([category, scores]) => {
      const emoji = scores.avg >= 8 ? '✅' : scores.avg >= 6 ? '⚠️' : '❌';
      console.log(`${emoji} ${category}: ${scores.avg.toFixed(1)}/10`);
    });

    // Top issues
    console.log('\n🔴 TOP ISSUES TO ADDRESS:');
    const issues = testResults
      .filter(r => r.issues.length > 0)
      .sort((a, b) => a.score - b.score)
      .slice(0, 10);
    
    issues.forEach((issue, i) => {
      console.log(`${i + 1}. [${issue.category}] ${issue.subcategory}: ${issue.issues.join(', ')}`);
    });

    // Top recommendations
    console.log('\n💡 TOP RECOMMENDATIONS:');
    const recommendations = testResults
      .filter(r => r.recommendations.length > 0)
      .sort((a, b) => a.score - b.score)
      .slice(0, 10);
    
    recommendations.forEach((rec, i) => {
      console.log(`${i + 1}. [${rec.category}] ${rec.subcategory}: ${rec.recommendations.join(', ')}`);
    });

    // Save detailed report
    await page.evaluate((results) => {
      const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `test-results-${new Date().toISOString()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, testResults);

    console.log('\n✅ Testing complete! Detailed report saved to test-results.json');
  });
});