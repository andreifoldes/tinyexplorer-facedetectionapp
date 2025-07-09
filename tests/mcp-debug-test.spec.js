const { test, expect } = require('@playwright/test');

test.describe('MCP Debug Test - Live App', () => {
  test('should check what is actually rendering at localhost:3001', async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:3001');
    await page.waitForLoadState('networkidle');
    
    // Wait for JavaScript to initialize
    await page.waitForTimeout(3000);
    
    // Take a screenshot
    await page.screenshot({ path: 'current-state.png', fullPage: true });
    
    // Get the full page content
    const pageContent = await page.evaluate(() => {
      return {
        title: document.title,
        htmlContent: document.documentElement.innerHTML,
        bodyText: document.body.innerText || document.body.textContent || '',
        rootElement: document.getElementById('root') ? document.getElementById('root').innerHTML : 'NO ROOT',
        statusElement: document.getElementById('status') ? document.getElementById('status').textContent : 'NO STATUS',
        mainContent: document.getElementById('main-content') ? document.getElementById('main-content').style.display : 'NO MAIN CONTENT',
        consoleErrors: []
      };
    });
    
    console.log('=== PAGE DEBUG INFO ===');
    console.log('Title:', pageContent.title);
    console.log('Body text:', pageContent.bodyText);
    console.log('Status element:', pageContent.statusElement);
    console.log('Main content display:', pageContent.mainContent);
    console.log('Root element length:', pageContent.rootElement.length);
    
    // Check for network errors
    const networkErrors = [];
    page.on('response', response => {
      if (response.status() >= 400) {
        networkErrors.push(`${response.status()} ${response.url()}`);
      }
    });
    
    // Check for console errors
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Wait a bit more to catch any async operations
    await page.waitForTimeout(2000);
    
    console.log('Network errors:', networkErrors);
    console.log('Console errors:', consoleErrors);
    
    // Test backend connectivity from browser
    const backendTest = await page.evaluate(async () => {
      try {
        const response = await fetch('http://127.0.0.1:5000/graphql/?query={awake}');
        const data = await response.json();
        return { success: true, data: data };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });
    
    console.log('Backend connectivity test:', backendTest);
    
    // Check if the JavaScript initialization worked
    const jsInitialization = await page.evaluate(() => {
      return {
        hasInitFunction: typeof init === 'function',
        hasAPIBase: typeof API_BASE !== 'undefined',
        hasSigningKey: typeof SIGNING_KEY !== 'undefined',
        windowLoadFired: true
      };
    });
    
    console.log('JavaScript initialization:', jsInitialization);
    
    // Test passes if we successfully inspected the app
    expect(pageContent.title).toBe('Face Recognition App Demo');
  });
  
  test('should check if CORS is blocking the requests', async ({ page }) => {
    await page.goto('http://localhost:3001');
    await page.waitForLoadState('networkidle');
    
    // Monitor network requests
    const requests = [];
    page.on('request', request => {
      requests.push({
        url: request.url(),
        method: request.method()
      });
    });
    
    const responses = [];
    page.on('response', response => {
      responses.push({
        url: response.url(),
        status: response.status(),
        headers: response.headers()
      });
    });
    
    await page.waitForTimeout(5000);
    
    console.log('=== NETWORK REQUESTS ===');
    requests.forEach(req => console.log(`${req.method} ${req.url}`));
    
    console.log('=== NETWORK RESPONSES ===');
    responses.forEach(resp => console.log(`${resp.status} ${resp.url}`));
    
    // Check specifically for GraphQL requests
    const graphqlRequests = requests.filter(req => req.url.includes('graphql'));
    const graphqlResponses = responses.filter(resp => resp.url.includes('graphql'));
    
    console.log('GraphQL requests:', graphqlRequests);
    console.log('GraphQL responses:', graphqlResponses);
    
    expect(true).toBe(true); // This test is for debugging
  });
});