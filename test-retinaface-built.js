const { _electron: electron } = require('@playwright/test');
const path = require('path');

async function testRetinaFaceInBuiltApp() {
  let electronApp;
  let page;
  
  try {
    console.log('=== TESTING RETINAFACE IN BUILT ELECTRON APP ===\n');
    
    // Path to the built Electron app
    const electronPath = path.join(__dirname, 'dist', 'mac-arm64', 'TinyExplorer FaceDetectionApp.app', 'Contents', 'MacOS', 'TinyExplorer FaceDetectionApp');
    
    console.log('1. Launching Electron app from:', electronPath);
    
    // Launch the Electron app
    electronApp = await electron.launch({
      executablePath: electronPath,
      args: [],
      env: {
        NODE_ENV: 'production'
      }
    });

    // Get the first page (main window)
    page = await electronApp.firstWindow();
    
    console.log('2. App launched successfully, waiting for UI to load...');
    await page.waitForTimeout(5000);
    
    // Capture console messages
    const consoleMessages = [];
    page.on('console', msg => {
      consoleMessages.push({
        type: msg.type(),
        text: msg.text(),
        timestamp: new Date().toISOString()
      });
      console.log(`[CONSOLE-${msg.type().toUpperCase()}] ${msg.text()}`);
    });
    
    // Take initial screenshot
    await page.screenshot({ path: 'test-results/initial-app-state.png', fullPage: true });
    console.log('3. Initial screenshot saved');
    
    // Check if app loaded successfully
    console.log('4. Checking if app UI loaded...');
    const bodyVisible = await page.isVisible('body');
    console.log(`   - Body visible: ${bodyVisible}`);
    
    // Get page content to understand the structure
    const pageContent = await page.content();
    console.log(`   - Page content length: ${pageContent.length} characters`);
    
    // Look for any model selector or dropdown
    console.log('5. Looking for model selector elements...');
    const possibleSelectors = [
      'select',
      'select[name="model"]',
      'select[id*="model"]',
      '.model-selector',
      '[data-testid*="model"]',
      'dropdown',
      '.dropdown'
    ];
    
    let modelSelector = null;
    for (const selector of possibleSelectors) {
      try {
        const element = page.locator(selector);
        const isVisible = await element.isVisible({ timeout: 2000 }).catch(() => false);
        if (isVisible) {
          modelSelector = element;
          console.log(`   - Found model selector: ${selector}`);
          break;
        }
      } catch (e) {
        // Continue to next selector
      }
    }
    
    if (modelSelector) {
      console.log('6. Testing model selector...');
      
      // Get all options
      try {
        const options = await modelSelector.locator('option').allTextContents();
        console.log(`   - Available options: ${JSON.stringify(options)}`);
        
        // Look for RetinaFace option
        const retinaFaceOption = options.find(option => 
          option.toLowerCase().includes('retinaface') || 
          option.toLowerCase().includes('retina')
        );
        
        if (retinaFaceOption) {
          console.log(`   - Found RetinaFace option: ${retinaFaceOption}`);
          
          // Try to select RetinaFace
          console.log('7. Selecting RetinaFace model...');
          const optionElement = modelSelector.locator(`option:has-text("${retinaFaceOption}")`);
          const optionValue = await optionElement.getAttribute('value');
          
          await modelSelector.selectOption(optionValue);
          console.log(`   - Selected RetinaFace (value: ${optionValue})`);
          
          // Wait for potential environment switching
          console.log('8. Waiting for environment switching...');
          await page.waitForTimeout(10000); // Wait 10 seconds for environment switching
          
          // Take screenshot after selection
          await page.screenshot({ path: 'test-results/after-retinaface-selection.png', fullPage: true });
          
        } else {
          console.log('   - RetinaFace option not found in dropdown');
          console.log(`   - Available options were: ${options.join(', ')}`);
        }
        
      } catch (error) {
        console.log(`   - Error accessing options: ${error.message}`);
      }
      
    } else {
      console.log('6. No model selector found, checking page structure...');
      
      // Get all interactive elements
      const buttons = await page.locator('button').allTextContents().catch(() => []);
      console.log(`   - Buttons found: ${JSON.stringify(buttons)}`);
      
      const inputs = await page.locator('input').count().catch(() => 0);
      console.log(`   - Input elements found: ${inputs}`);
      
      const selects = await page.locator('select').count().catch(() => 0);
      console.log(`   - Select elements found: ${selects}`);
      
      // Try to find any text that mentions models
      const bodyText = await page.locator('body').textContent().catch(() => '');
      const modelMentions = bodyText.toLowerCase().includes('model') || 
                           bodyText.toLowerCase().includes('yolo') || 
                           bodyText.toLowerCase().includes('retinaface');
      console.log(`   - Page mentions models: ${modelMentions}`);
      
      if (modelMentions) {
        console.log(`   - Sample text: ${bodyText.substring(0, 300)}...`);
      }
    }
    
    // Look for any Load Model or similar buttons
    console.log('9. Looking for Load Model button...');
    const possibleLoadButtons = [
      'button:has-text("Load Model")',
      'button:has-text("Load")',
      'button:has-text("Start")',
      'button[id*="load"]',
      'button[class*="load"]'
    ];
    
    let loadButton = null;
    for (const selector of possibleLoadButtons) {
      try {
        const element = page.locator(selector);
        const isVisible = await element.isVisible({ timeout: 2000 }).catch(() => false);
        if (isVisible) {
          loadButton = element;
          console.log(`   - Found load button: ${selector}`);
          break;
        }
      } catch (e) {
        // Continue
      }
    }
    
    if (loadButton) {
      console.log('10. Clicking Load Model button...');
      await loadButton.click();
      
      // Wait for Python subprocess communication
      await page.waitForTimeout(8000);
      
      // Take screenshot after load attempt
      await page.screenshot({ path: 'test-results/after-load-attempt.png', fullPage: true });
    }
    
    // Final analysis of console messages
    console.log('\n=== CONSOLE MESSAGE ANALYSIS ===');
    
    const environmentMessages = consoleMessages.filter(msg => 
      msg.text.toLowerCase().includes('environment') ||
      msg.text.toLowerCase().includes('conda') ||
      msg.text.toLowerCase().includes('retinaface-env') ||
      msg.text.toLowerCase().includes('yolo-env') ||
      msg.text.toLowerCase().includes('model type change')
    );
    
    const pythonMessages = consoleMessages.filter(msg =>
      msg.text.toLowerCase().includes('python') ||
      msg.text.toLowerCase().includes('subprocess') ||
      msg.text.toLowerCase().includes('flask')
    );
    
    const retinaFaceMessages = consoleMessages.filter(msg =>
      msg.text.toLowerCase().includes('retinaface') ||
      msg.text.toLowerCase().includes('retina')
    );
    
    const errorMessages = consoleMessages.filter(msg => msg.type === 'error');
    
    console.log(`Environment switching messages: ${environmentMessages.length}`);
    environmentMessages.forEach(msg => {
      console.log(`   [${msg.timestamp}] ${msg.text}`);
    });
    
    console.log(`\nPython-related messages: ${pythonMessages.length}`);
    pythonMessages.forEach(msg => {
      console.log(`   [${msg.timestamp}] ${msg.text}`);
    });
    
    console.log(`\nRetinaFace-related messages: ${retinaFaceMessages.length}`);
    retinaFaceMessages.forEach(msg => {
      console.log(`   [${msg.timestamp}] ${msg.text}`);
    });
    
    console.log(`\nError messages: ${errorMessages.length}`);
    errorMessages.forEach(msg => {
      console.log(`   [${msg.timestamp}] ERROR: ${msg.text}`);
    });
    
    // Summary
    console.log('\n=== TEST SUMMARY ===');
    console.log(`✓ App launched successfully: ${electronApp !== null}`);
    console.log(`✓ UI loaded: ${bodyVisible}`);
    console.log(`✓ Model selector found: ${modelSelector !== null}`);
    console.log(`✓ Load button found: ${loadButton !== null}`);
    console.log(`✓ Environment switching detected: ${environmentMessages.length > 0}`);
    console.log(`✓ RetinaFace functionality detected: ${retinaFaceMessages.length > 0}`);
    console.log(`✗ Errors encountered: ${errorMessages.length}`);
    console.log(`Total console messages: ${consoleMessages.length}`);
    
    // Wait a bit more to catch any delayed messages
    await page.waitForTimeout(5000);
    
  } catch (error) {
    console.error('Test failed with error:', error);
  } finally {
    if (electronApp) {
      console.log('\nClosing Electron app...');
      await electronApp.close();
    }
  }
}

// Run the test
testRetinaFaceInBuiltApp().then(() => {
  console.log('\nTest completed.');
}).catch(error => {
  console.error('Test failed:', error);
});