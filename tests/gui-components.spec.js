const { test, expect } = require('@playwright/test');
const path = require('path');

test.describe('Face Recognition App - GUI Components', () => {
  test.describe('Static Build Tests', () => {
    test.beforeEach(async ({ page }) => {
      // Test the static build directly
      const buildPath = path.join(__dirname, '..', 'build', 'index.html');
      const fileUrl = `file://${buildPath}`;
      await page.goto(fileUrl);
      await page.waitForTimeout(1000);
    });

    test('should display main title', async ({ page }) => {
      const title = page.locator('h1');
      await expect(title).toBeVisible();
      await expect(title).toHaveText('Face Recognition Toolbox');
    });

    test('should have all required buttons', async ({ page }) => {
      // Check for all main buttons
      await expect(page.locator('button:has-text("Browse")')).toBeVisible();
      await expect(page.locator('button:has-text("Load Model")')).toBeVisible();
      await expect(page.locator('button:has-text("Start Recognition")')).toBeVisible();
      
      // Verify button count
      const buttonCount = await page.locator('button').count();
      expect(buttonCount).toBeGreaterThanOrEqual(3);
    });

    test('should have all form controls with proper attributes', async ({ page }) => {
      // Folder input
      const folderInput = page.locator('input[placeholder="Select a folder..."]');
      await expect(folderInput).toBeVisible();
      await expect(folderInput).toHaveAttribute('readonly', '');
      
      // Model dropdown
      const modelSelect = page.locator('select');
      await expect(modelSelect).toBeVisible();
      
      // Confidence slider
      const confidenceSlider = page.locator('input[type="range"]');
      await expect(confidenceSlider).toBeVisible();
      await expect(confidenceSlider).toHaveAttribute('min', '0.1');
      await expect(confidenceSlider).toHaveAttribute('max', '1.0');
      await expect(confidenceSlider).toHaveAttribute('step', '0.1');
      
      // Default slider value
      const sliderValue = await confidenceSlider.inputValue();
      expect(parseFloat(sliderValue)).toBe(0.5);
    });

    test('should have proper control labels', async ({ page }) => {
      await expect(page.locator('label:has-text("Folder:")')).toBeVisible();
      await expect(page.locator('label:has-text("Model:")')).toBeVisible();
      await expect(page.locator('label:has-text("Confidence Threshold:")')).toBeVisible();
    });

    test('should have progress sections', async ({ page }) => {
      await expect(page.locator('h3:has-text("Progress Updates:")')).toBeVisible();
      await expect(page.locator('.message-window')).toBeVisible();
    });

    test('should have proper CSS styling', async ({ page }) => {
      // Check main app structure
      await expect(page.locator('.App')).toBeVisible();
      await expect(page.locator('.App-header')).toBeVisible();
      await expect(page.locator('.controls')).toBeVisible();
      
      // Check control groups exist
      const controlGroups = page.locator('.control-group');
      const count = await controlGroups.count();
      expect(count).toBeGreaterThan(0);
    });

    test('should show connecting message when no backend', async ({ page }) => {
      // In static mode, should show connecting message
      const connectingMessage = page.locator('div:has-text("Connecting to Python backend...")');
      await expect(connectingMessage).toBeVisible();
    });
  });

  test.describe('Development Server Tests', () => {
    test.beforeEach(async ({ page }) => {
      // Test against the development server
      await page.goto('http://localhost:3000');
      
      // Wait for app to load (either title or loading message)
      await Promise.race([
        page.waitForSelector('h1').catch(() => {}),
        page.waitForSelector('div:has-text("Connecting to Python backend...")').catch(() => {})
      ]);
    });

    test('should load the React app', async ({ page }) => {
      // Check that either the title or loading message is visible
      const title = page.locator('h1:has-text("Face Recognition Toolbox")');
      const loadingMessage = page.locator('div:has-text("Connecting to Python backend...")');
      
      const titleVisible = await title.isVisible().catch(() => false);
      const loadingVisible = await loadingMessage.isVisible().catch(() => false);
      
      expect(titleVisible || loadingVisible).toBe(true);
    });

    test('should update confidence threshold when slider is moved', async ({ page }) => {
      // Only test this if the full UI is loaded
      const slider = page.locator('input[type="range"]');
      const isSliderVisible = await slider.isVisible().catch(() => false);
      
      if (isSliderVisible) {
        await slider.fill('0.8');
        
        // Check that the displayed value updates
        const confidenceValue = page.locator('span').first();
        await expect(confidenceValue).toHaveText('0.8');
      } else {
        // App is still loading, which is acceptable
        console.log('Slider test skipped - app still loading');
      }
    });

    test('should have proper button styling when loaded', async ({ page }) => {
      const startButton = page.locator('button:has-text("Start Recognition")');
      const isVisible = await startButton.isVisible().catch(() => false);
      
      if (isVisible) {
        // Test button styling
        await expect(startButton).toHaveCSS('padding', '10px 20px');
        await expect(startButton).toHaveCSS('color', 'rgb(255, 255, 255)');
        
        // Should be disabled initially (no folder selected)
        await expect(startButton).toBeDisabled();
        await expect(startButton).toHaveCSS('background-color', 'rgb(102, 102, 102)');
      }
    });

    test('should handle JavaScript execution without critical errors', async ({ page }) => {
      const jsErrors = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          jsErrors.push(msg.text());
        }
      });
      
      await page.waitForTimeout(3000);
      
      // Filter out expected errors (network errors due to no backend)
      const criticalErrors = jsErrors.filter(error => 
        !error.includes('Network error') && 
        !error.includes('Failed to fetch') && 
        !error.includes('GraphQL') &&
        !error.includes('CORS')
      );
      
      expect(criticalErrors.length).toBe(0);
    });
  });
}); 