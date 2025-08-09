const { _electron: electron } = require('@playwright/test');
const path = require('path');

async function testRetinaFaceInDevelopment() {
  let electronApp;
  let page;
  
  try {
    console.log('=== TESTING RETINAFACE IN DEVELOPMENT MODE ===\n');
    
    // Launch in development mode from main directory
    console.log('1. Launching Electron app in development mode...');
    
    electronApp = await electron.launch({
      executablePath: require('electron'),
      args: [path.join(__dirname, 'main')],
      env: {
        NODE_ENV: 'development'
      }
    });

    page = await electronApp.firstWindow();
    
    console.log('2. App launched successfully, waiting for UI to load...');
    await page.waitForTimeout(10000); // Wait longer for Python startup
    
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
    await page.screenshot({ path: 'test-results/dev-initial.png', fullPage: true });
    console.log('3. Initial screenshot saved');
    
    // Check if app loaded successfully
    console.log('4. Checking if app UI loaded...');
    const bodyVisible = await page.isVisible('body');
    console.log(`   - Body visible: ${bodyVisible}`);
    
    // Look for model selector
    console.log('5. Looking for model selector...');
    const modelSelector = page.locator('select');
    const selectorVisible = await modelSelector.isVisible({ timeout: 15000 }).catch(() => false);
    
    if (selectorVisible) {
      console.log('   - Model selector found!');
      
      // Get all options
      const options = await modelSelector.locator('option').allTextContents();
      console.log(`   - Available options: ${JSON.stringify(options)}`);
      
      // Look for RetinaFace option
      const retinaFaceOption = options.find(option => 
        option.toLowerCase().includes('retinaface') || 
        option.toLowerCase().includes('retina')
      );
      
      if (retinaFaceOption) {
        console.log(`6. Found RetinaFace option: ${retinaFaceOption}`);
        
        // Select RetinaFace
        const optionElement = modelSelector.locator(`option:has-text("${retinaFaceOption}")`);
        const optionValue = await optionElement.getAttribute('value');
        
        console.log('7. Selecting RetinaFace model...');
        await modelSelector.selectOption(optionValue);
        
        // Wait for environment switching
        console.log('8. Waiting for environment switching (20 seconds)...');
        await page.waitForTimeout(20000);
        
        // Take screenshot after selection
        await page.screenshot({ path: 'test-results/dev-after-retinaface.png', fullPage: true });
        
        // Check for Load Model button and try it
        console.log('9. Looking for Load Model button...');
        const loadButton = page.locator('button:has-text("Load Model")');
        const loadButtonVisible = await loadButton.isVisible({ timeout: 5000 }).catch(() => false);
        
        if (loadButtonVisible) {
          console.log('   - Load Model button found, clicking...');
          await loadButton.click();
          
          // Wait for model loading
          await page.waitForTimeout(15000);
          
          // Take final screenshot
          await page.screenshot({ path: 'test-results/dev-after-load.png', fullPage: true });
        }
        
      } else {
        console.log('6. RetinaFace option not found in dropdown');
        console.log(`   - Available options were: ${options.join(', ')}`);
      }
      
    } else {
      console.log('   - No model selector found after waiting');
      
      // Check what's on the page
      const bodyText = await page.locator('body').textContent().catch(() => '');
      console.log(`   - Page content sample: ${bodyText.substring(0, 300)}...`);
    }
    
    // Final analysis
    console.log('\n=== DEVELOPMENT MODE CONSOLE MESSAGE ANALYSIS ===');
    
    const environmentMessages = consoleMessages.filter(msg => 
      msg.text.toLowerCase().includes('environment') ||
      msg.text.toLowerCase().includes('conda') ||
      msg.text.toLowerCase().includes('retinaface-env') ||
      msg.text.toLowerCase().includes('yolo-env') ||
      msg.text.toLowerCase().includes('model type change')
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
    
    console.log(`\nRetinaFace-related messages: ${retinaFaceMessages.length}`);
    retinaFaceMessages.forEach(msg => {
      console.log(`   [${msg.timestamp}] ${msg.text}`);
    });
    
    console.log(`\nError messages: ${errorMessages.length}`);
    errorMessages.forEach(msg => {
      console.log(`   [${msg.timestamp}] ERROR: ${msg.text}`);
    });
    
    // Summary
    console.log('\n=== DEVELOPMENT MODE TEST SUMMARY ===');
    console.log(`✓ App launched successfully: ${electronApp !== null}`);
    console.log(`✓ UI loaded: ${bodyVisible}`);
    console.log(`✓ Model selector found: ${selectorVisible}`);
    console.log(`✓ Environment switching detected: ${environmentMessages.length > 0}`);
    console.log(`✓ RetinaFace functionality detected: ${retinaFaceMessages.length > 0}`);
    console.log(`✗ Errors encountered: ${errorMessages.length}`);
    console.log(`Total console messages: ${consoleMessages.length}`);
    
    // Let it run a bit more to catch delayed messages
    await page.waitForTimeout(5000);
    
  } catch (error) {
    console.error('Development test failed with error:', error);
  } finally {
    if (electronApp) {
      console.log('\nClosing Electron app...');
      await electronApp.close();
    }
  }
}

// Run the test
testRetinaFaceInDevelopment().then(() => {
  console.log('\nDevelopment test completed.');
}).catch(error => {
  console.error('Development test failed:', error);
});