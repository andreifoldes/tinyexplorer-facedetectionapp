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

// Copy Python source files to python subdirectory
console.log('Copying Python source files...');
const pythonSubDir = path.join(pythonDistDir, 'python');
fs.mkdirSync(pythonSubDir, { recursive: true });
execSync(`cp -r python/ ${pythonSubDir}/`);

// Install dependencies to a local directory
console.log('Installing Python dependencies...');
const depsDir = path.join(pythonDistDir, 'python-deps');
fs.mkdirSync(depsDir, { recursive: true });

// Use the existing requirements.txt file which has more flexible version requirements
const requirementsPath = path.join(pythonDistDir, 'python', 'requirements.txt');

try {
    console.log('Installing Python packages from requirements.txt...');
    const installCmd = `python3 -m pip install --target "${depsDir}" --no-cache-dir -r "${requirementsPath}"`;
    execSync(installCmd, { stdio: 'inherit', env: { ...process.env, PIP_DISABLE_PIP_VERSION_CHECK: '1' } });
} catch (error) {
    console.error('Failed to install Python dependencies.');
    process.exit(1);
}

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