#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const platform = process.platform;
const pythonDistDir = path.join(__dirname, '..', 'pythondist');

console.log('Creating Python bundle...');

// Clean previous build
if (fs.existsSync(pythonDistDir)) {
    execSync(`rm -rf ${pythonDistDir}`);
}

// Create distribution directory
fs.mkdirSync(pythonDistDir, { recursive: true });

// Copy Python source files
console.log('Copying Python source files...');
execSync(`cp -r python/ ${pythonDistDir}/`);

// Install dependencies to a local directory
console.log('Installing Python dependencies...');
const depsDir = path.join(pythonDistDir, 'python-deps');
fs.mkdirSync(depsDir, { recursive: true });

// Install only the essential packages to reduce size
const essentialPackages = [
    'opencv-python-headless',  // Smaller than opencv-python
    'pillow',
    'numpy'
];

// Install packages one by one to handle failures gracefully
essentialPackages.forEach(pkg => {
    try {
        console.log(`Installing ${pkg}...`);
        execSync(`pip install ${pkg} --target ${depsDir} --no-deps`, { stdio: 'inherit' });
    } catch (error) {
        console.warn(`Failed to install ${pkg}, continuing...`);
    }
});

// Install dependencies for essential packages
try {
    console.log('Installing package dependencies...');
    execSync(`pip install --target ${depsDir} --no-warn-script-location python-dateutil typing-extensions`, { stdio: 'inherit' });
} catch (error) {
    console.warn('Some dependencies failed to install, continuing...');
}

// Create a requirements file for the essential packages
const essentialRequirements = essentialPackages.join('\n');
fs.writeFileSync(path.join(pythonDistDir, 'requirements-essential.txt'), essentialRequirements);

console.log('Python bundle created successfully!');
console.log(`Bundle size: ${getDirectorySize(pythonDistDir)} MB`);

function getDirectorySize(dir) {
    try {
        const result = execSync(`du -sm ${dir}`).toString().trim();
        return result.split('\t')[0];
    } catch (error) {
        return 'unknown';
    }
}