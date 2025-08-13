#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const platform = process.platform;
const pythonDistDir = path.join(__dirname, '..', 'pythondist');

console.log('Creating Python bundle with dual environments...');

// Clean previous build
if (fs.existsSync(pythonDistDir)) {
    console.log('Cleaning previous build...');
    execSync(`rm -rf ${pythonDistDir}`);
}

// Create distribution directory
fs.mkdirSync(pythonDistDir, { recursive: true });

// Copy Python source files to python subdirectory
console.log('Copying Python source files...');
const pythonSubDir = path.join(pythonDistDir, 'python');
fs.mkdirSync(pythonSubDir, { recursive: true });
execSync(`cp -r python/ ${pythonSubDir}/`);

// Create YOLO environment
console.log('\n=== Creating YOLO Environment ===');
const yoloEnvDir = path.join(pythonDistDir, 'yolo-env');
fs.mkdirSync(yoloEnvDir, { recursive: true });

// Install YOLO dependencies
const yoloPackages = [
    'ultralytics',
    'opencv-python',
    'pillow',
    'numpy',
    'torch',
    'torchvision',
    'flask',
    'flask-cors',
    'graphene>=3.0',
    'flask-graphql>=2.0'
];

console.log('Installing YOLO environment packages...');
try {
    const yoloInstallCmd = `python3.10 -m pip install --target "${yoloEnvDir}" --no-cache-dir ${yoloPackages.join(' ')}`;
    execSync(yoloInstallCmd, { stdio: 'inherit', env: { ...process.env, PIP_DISABLE_PIP_VERSION_CHECK: '1' } });
} catch (error) {
    console.error('Failed to install YOLO dependencies.');
    process.exit(1);
}

// Create RetinaFace environment
console.log('\n=== Creating RetinaFace Environment ===');
const retinaEnvDir = path.join(pythonDistDir, 'retinaface-env');
fs.mkdirSync(retinaEnvDir, { recursive: true });

// Install RetinaFace dependencies
const retinaPackages = [
    'retina-face',
    'tensorflow',
    'tf-keras',
    'opencv-python',
    'pillow',
    'numpy',
    'flask',
    'flask-cors',
    'graphene>=3.0',
    'flask-graphql>=2.0',
    'ultralytics'  // Include for compatibility
];

console.log('Installing RetinaFace environment packages...');
try {
    const retinaInstallCmd = `python3.10 -m pip install --target "${retinaEnvDir}" --no-cache-dir ${retinaPackages.join(' ')}`;
    execSync(retinaInstallCmd, { stdio: 'inherit', env: { ...process.env, PIP_DISABLE_PIP_VERSION_CHECK: '1' } });
} catch (error) {
    console.error('Failed to install RetinaFace dependencies.');
    process.exit(1);
}

// Also keep the legacy python-deps for backward compatibility
console.log('\n=== Creating legacy python-deps (for compatibility) ===');
const depsDir = path.join(pythonDistDir, 'python-deps');
fs.mkdirSync(depsDir, { recursive: true });

// Use the existing requirements.txt file
const requirementsPath = path.join(pythonDistDir, 'python', 'requirements.txt');
try {
    console.log('Installing legacy dependencies from requirements.txt...');
    const installCmd = `python3 -m pip install --target "${depsDir}" --no-cache-dir -r "${requirementsPath}"`;
    execSync(installCmd, { stdio: 'inherit', env: { ...process.env, PIP_DISABLE_PIP_VERSION_CHECK: '1' } });
} catch (error) {
    console.error('Failed to install legacy dependencies.');
}

console.log('\n=== Python bundle created successfully! ===');
console.log(`YOLO environment size: ${getDirectorySize(yoloEnvDir)} MB`);
console.log(`RetinaFace environment size: ${getDirectorySize(retinaEnvDir)} MB`);
console.log(`Legacy deps size: ${getDirectorySize(depsDir)} MB`);
console.log(`Total bundle size: ${getDirectorySize(pythonDistDir)} MB`);

function getDirectorySize(dir) {
    try {
        const result = execSync(`du -sm ${dir}`).toString().trim();
        return result.split('\t')[0];
    } catch (error) {
        return 'unknown';
    }
}