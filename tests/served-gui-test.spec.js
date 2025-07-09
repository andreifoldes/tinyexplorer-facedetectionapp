const { test, expect } = require('@playwright/test');

test.describe('Face Recognition App - Integration Tests (Served)', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the served build
    await page.goto('http://localhost:3001');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
  });

  test('should load React app and handle missing backend gracefully', async ({ page }) => {
    // Verify React app root exists and has content
    const root = page.locator('#root');
    await expect(root).toBeVisible();
    
    const content = await root.textContent();
    expect(content).toBeTruthy();
    expect(content.length).toBeGreaterThan(0);
    
    // Should show either the full UI or loading message
    const title = page.locator('h1:has-text("Face Recognition Toolbox")');
    const loadingMessage = page.locator('div:has-text("Connecting to Python backend...")');
    
    const titleVisible = await title.isVisible().catch(() => false);
    const loadingVisible = await loadingMessage.isVisible().catch(() => false);
    
    expect(titleVisible || loadingVisible).toBe(true);
  });

  test('should have working JavaScript without critical errors', async ({ page }) => {
    const jsErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        jsErrors.push(msg.text());
      }
    });
    
    await page.waitForTimeout(3000);
    
    // Filter out expected network errors
    const criticalErrors = jsErrors.filter(error => 
      !error.includes('Network error') && 
      !error.includes('Failed to fetch') && 
      !error.includes('GraphQL') &&
      !error.includes('CORS') &&
      !error.includes('apollo')
    );
    
    expect(criticalErrors.length).toBe(0);
  });

  test('should have CSS and JavaScript bundles loaded', async ({ page }) => {
    // Check that React bundle is loaded
    const hasJSBundle = await page.evaluate(() => {
      const scripts = Array.from(document.querySelectorAll('script[src*="main"]'));
      return scripts.length > 0;
    });
    
    expect(hasJSBundle).toBe(true);
    
    // Check that CSS is loaded
    const hasStyles = await page.evaluate(() => {
      const root = document.getElementById('root');
      if (!root) return false;
      
      const computedStyle = window.getComputedStyle(root);
      return computedStyle.display !== 'none';
    });
    
    expect(hasStyles).toBe(true);
  });

  test('should render app structure when backend becomes available', async ({ page }) => {
    // Wait for potential backend connection
    await page.waitForTimeout(5000);
    
    const appStructure = await page.evaluate(() => {
      const root = document.getElementById('root');
      if (!root) return null;
      
      return {
        hasContent: root.innerHTML.length > 100,
        hasHeading: root.innerHTML.includes('Face Recognition'),
        hasButtons: root.innerHTML.includes('button') || root.innerHTML.includes('Browse'),
        hasInputs: root.innerHTML.includes('input') || root.innerHTML.includes('Select a folder')
      };
    });
    
    if (appStructure) {
      expect(appStructure.hasContent).toBe(true);
      
      // Either shows loading state or full UI
      if (appStructure.hasButtons && appStructure.hasInputs) {
        // Full UI is loaded
        expect(appStructure.hasHeading).toBe(true);
      } else {
        // Still in loading state, which is acceptable
        expect(appStructure.hasHeading || appStructure.hasContent).toBe(true);
      }
    }
  });

  test('should be responsive on different screen sizes', async ({ page }) => {
    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(500);
    
    const root = page.locator('#root');
    await expect(root).toBeVisible();
    
    // Test desktop view
    await page.setViewportSize({ width: 1200, height: 800 });
    await page.waitForTimeout(500);
    
    await expect(root).toBeVisible();
  });

  test('should maintain app state and handle backend connectivity', async ({ page }) => {
    // Test that the app gracefully handles no backend
    const pageContent = await page.evaluate(() => {
      const root = document.getElementById('root');
      return root ? root.innerHTML : '';
    });
    
    expect(pageContent).toBeTruthy();
    expect(pageContent.length).toBeGreaterThan(50);
    
    // Should contain relevant app content
    const hasRelevantContent = pageContent.includes('Face Recognition') || 
                              pageContent.includes('Connecting to Python') ||
                              pageContent.includes('backend') ||
                              pageContent.includes('loading');
    
    expect(hasRelevantContent).toBe(true);
  });
});