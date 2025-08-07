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

// Install ALL packages needed for face detection (single transaction to avoid conflicts)
// Pin numpy to a version compatible with tensorflow 2.19 (<2.2.0) to avoid resolver conflicts
// Keep TensorFlow CPU default (tensorflow is CPU-only by default; GPU is an extra),
// and pin PyTorch CPU-only wheels to avoid NVIDIA deps.
const essentialPackages = [
    'tensorflow==2.19.0',
    // TensorFlow 2.19 requires tf-keras to be installed separately
    'tf-keras',
    'numpy==1.26.4',
    'opencv-python-headless',
    'pillow==10.3.0',
    'torch==2.5.0',
    'torchvision==0.20.0',
    'ultralytics',
    'retina-face==0.0.17',
    'flask',
    'flask-cors',
    'flask-graphql',
    'flask-socketio',
    'graphene'
];

// Create a requirements file for the essential packages
const essentialRequirements = essentialPackages.join('\n');
const requirementsPath = path.join(pythonDistDir, 'requirements-essential.txt');
fs.writeFileSync(requirementsPath, essentialRequirements);

try {
    console.log('Installing all Python packages (CPU-only Torch) in a single operation...');
    const installCmd = `python3 -m pip install --target "${depsDir}" --upgrade-strategy only-if-needed --no-cache-dir --index-url https://pypi.org/simple --extra-index-url https://download.pytorch.org/whl/cpu -r "${requirementsPath}"`;
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