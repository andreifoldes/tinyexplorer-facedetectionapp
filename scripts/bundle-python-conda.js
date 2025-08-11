#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const platform = process.platform;
const pythonDistDir = path.join(__dirname, '..', 'pythondist');
const condaEnv = 'electron-python-sample';
const condaPath = '/home/tamas.foldes/miniconda3';

console.log('Creating Python bundle from conda environment...');

// Clean previous build
if (fs.existsSync(pythonDistDir)) {
    console.log('Cleaning previous build...');
    execSync(`rm -rf ${pythonDistDir}`);
}

// Create distribution directory
fs.mkdirSync(pythonDistDir, { recursive: true });

// Copy Python source files
console.log('Copying Python source files...');
execSync(`cp -r python/ ${pythonDistDir}/`);

// Create python-deps directory
const depsDir = path.join(pythonDistDir, 'python-deps');
fs.mkdirSync(depsDir, { recursive: true });

// Export site-packages from conda environment
console.log(`Exporting packages from conda environment: ${condaEnv}...`);
const sitePackagesPath = path.join(condaPath, 'envs', condaEnv, 'lib', 'python3.10', 'site-packages');

if (!fs.existsSync(sitePackagesPath)) {
    console.error(`Site-packages not found at: ${sitePackagesPath}`);
    process.exit(1);
}

// List of packages to copy from conda environment
const packagesToCopy = [
    // Core packages
    'numpy',
    'numpy.libs',
    'cv2',
    'PIL',
    'pillow.libs',
    
    // Deep learning
    'torch',
    'torchvision',
    'ultralytics',
    'tensorflow',
    'tensorboard',
    'tensorboard_data_server',
    'keras',
    'retinaface',
    
    // Web/API packages
    'flask',
    'flask_cors',
    'flask_graphql',
    'flask_socketio',
    'graphene',
    'graphql',
    
    // Dependencies
    'werkzeug',
    'jinja2',
    'markupsafe',
    'click',
    'itsdangerous',
    'six.py',
    'typing_extensions.py',
    'dateutil',
    'yaml',
    'tqdm',
    'requests',
    'urllib3',
    'certifi',
    'charset_normalizer',
    'idna',
    'packaging',
    'pyparsing',
    
    // Additional ML dependencies
    'scipy',
    'scipy.libs',
    'matplotlib',
    'seaborn',
    'pandas',
    'sklearn',
    'h5py',
    'gdown',
    'beautifulsoup4',
    'bs4',
    
    // YOLO dependencies
    'ultralytics.egg-info',
    'yolo',
    
    // Additional required packages
    'psutil',
    'py_cpuinfo',
    'thop',
    
    // Dist-info directories for package metadata
    '*.dist-info',
    '*.egg-info'
];

console.log('Copying packages from conda environment...');
packagesToCopy.forEach(pkg => {
    const sourcePath = path.join(sitePackagesPath, pkg);
    const destPath = path.join(depsDir, pkg);
    
    // Check if it's a wildcard pattern
    if (pkg.includes('*')) {
        try {
            const pattern = pkg.replace('*', '');
            const files = fs.readdirSync(sitePackagesPath).filter(f => f.includes(pattern));
            files.forEach(file => {
                const src = path.join(sitePackagesPath, file);
                const dst = path.join(depsDir, file);
                if (fs.existsSync(src)) {
                    execSync(`cp -r "${src}" "${dst}"`);
                    console.log(`  ✓ Copied ${file}`);
                }
            });
        } catch (error) {
            console.warn(`  ⚠ Pattern ${pkg} not found`);
        }
    } else if (fs.existsSync(sourcePath)) {
        try {
            execSync(`cp -r "${sourcePath}" "${destPath}"`);
            console.log(`  ✓ Copied ${pkg}`);
        } catch (error) {
            console.warn(`  ⚠ Failed to copy ${pkg}: ${error.message}`);
        }
    } else {
        // Try to find the package with glob pattern
        try {
            const results = execSync(`ls -d ${sitePackagesPath}/${pkg}* 2>/dev/null || true`).toString().trim();
            if (results) {
                const paths = results.split('\n');
                paths.forEach(p => {
                    if (p) {
                        const basename = path.basename(p);
                        execSync(`cp -r "${p}" "${path.join(depsDir, basename)}"`);
                        console.log(`  ✓ Copied ${basename}`);
                    }
                });
            } else {
                console.log(`  ⚠ Package ${pkg} not found`);
            }
        } catch (error) {
            console.log(`  ⚠ Package ${pkg} not found`);
        }
    }
});

// Create a simple launcher script that sets up PYTHONPATH
const launcherScript = `#!/usr/bin/env python3
import sys
import os

# Add bundled dependencies to path
deps_dir = os.path.join(os.path.dirname(__file__), 'python-deps')
if os.path.exists(deps_dir):
    sys.path.insert(0, deps_dir)

# Import and run the subprocess API
from subprocess_api import SubprocessAPI

if __name__ == "__main__":
    api = SubprocessAPI()
    api.run()
`;

fs.writeFileSync(path.join(pythonDistDir, 'python', 'launcher.py'), launcherScript);
console.log('Created launcher script');

// Create requirements file listing what was bundled
const requirementsContent = `# Bundled from conda environment: ${condaEnv}
opencv-python-headless
pillow
numpy
torch
torchvision
ultralytics
tensorflow
retina-face
flask
flask-cors
flask-graphql
flask-socketio
graphene
`;

fs.writeFileSync(path.join(pythonDistDir, 'requirements-bundled.txt'), requirementsContent);

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