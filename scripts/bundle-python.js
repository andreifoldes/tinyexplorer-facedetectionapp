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

// Install dependencies to both yolo-env and retinaface-env directories
console.log('Installing Python dependencies to dual environments...');

// Create both environment directories
const yoloEnvDir = path.join(pythonDistDir, 'yolo-env');
const retinafaceEnvDir = path.join(pythonDistDir, 'retinaface-env');
fs.mkdirSync(yoloEnvDir, { recursive: true });
fs.mkdirSync(retinafaceEnvDir, { recursive: true });

// Use requirements from source tree to avoid relying on copy timing
const yoloRequirementsPath = path.join(__dirname, '..', 'python', 'requirements.txt');
const retinafaceRequirementsPath = path.join(__dirname, '..', 'python', 'requirements-retinaface.txt');

// Helper to find a preferred Python for retinaface (prefer 3.10 for TF compatibility)
function findPythonForRetinaFace() {
    // Allow CI to force a specific interpreter
    const forced = process.env.RETINAFACE_PYTHON || process.env.PYTHON_FOR_RETINAFACE;
    if (forced) {
        try {
            execSync(`"${forced}" --version`, { stdio: 'ignore' });
            console.log(`Using forced RetinaFace Python from env: ${forced}`);
            return forced;
        } catch (e) {
            console.warn(`Warning: RETINAFACE_PYTHON not usable: ${forced}. Falling back to candidates.`);
        }
    }
    const candidates = ['python3.10', 'python3.11', 'python3.12', 'python3'];
    for (const c of candidates) {
        try {
            execSync(`${c} --version`, { stdio: 'ignore' });
            return c;
        } catch (_) {}
    }
    return 'python3';
}

try {
    console.log('Creating virtual environments for better package isolation...');
    
    // Create YOLO virtual environment
    console.log('Creating YOLO virtual environment...');
    execSync(`python3 -m venv "${yoloEnvDir}"`, { stdio: 'inherit' });
    
    // Install YOLO packages in virtual environment
    console.log('Installing YOLO packages...');
    const yoloPython = path.join(yoloEnvDir, 'bin', 'python');
    const yoloInstallCmd = `"${yoloPython}" -m pip install --no-cache-dir --upgrade pip setuptools wheel && "${yoloPython}" -m pip install --no-cache-dir --upgrade -r "${yoloRequirementsPath}"`;
    execSync(yoloInstallCmd, { stdio: 'inherit', env: { ...process.env, PIP_DISABLE_PIP_VERSION_CHECK: '1' } });
    
    // Create RetinaFace virtual environment
    console.log('Creating RetinaFace virtual environment...');
    try {
        const retinafacePythonSystem = findPythonForRetinaFace();
        console.log(`Selected system Python for RetinaFace venv: ${retinafacePythonSystem}`);
        execSync(`${retinafacePythonSystem} -m venv "${retinafaceEnvDir}"`, { stdio: 'inherit' });

        console.log('Installing RetinaFace packages...');
        const retinafacePython = path.join(retinafaceEnvDir, 'bin', 'python');

        // Always upgrade pip tooling first
        execSync(`"${retinafacePython}" -m pip install --no-cache-dir --upgrade pip setuptools wheel`, { stdio: 'inherit', env: { ...process.env, PIP_DISABLE_PIP_VERSION_CHECK: '1' } });

        // On Apple Silicon macOS, prefer tensorflow-macos + tensorflow-metal pinned to 2.15 line with python 3.10
        if (process.platform === 'darwin' && process.arch === 'arm64') {
            console.log('Detected macOS arm64 - installing tensorflow-macos + tensorflow-metal for RetinaFace');
            const pkgs = [
                'flask',
                'flask-cors',
                'graphene>=3.0',
                'flask-graphql>=2.0',
                'opencv-python',
                'pillow',
                'numpy<2.0.0',
                'tensorflow-macos==2.15.0',
                'tensorflow-metal==1.1.0',
                'tf-keras==2.15.0',
                'retina-face>=0.0.14'
            ];
            const quoted = pkgs.map(p => `"${p}"`).join(' ');
            execSync(`"${retinafacePython}" -m pip install --no-cache-dir ${quoted}`, { stdio: 'inherit', env: { ...process.env, PIP_DISABLE_PIP_VERSION_CHECK: '1' } });
        } else {
            // Default path: install from requirements file
            const retinafaceInstallCmd = `"${retinafacePython}" -m pip install --no-cache-dir --upgrade -r "${retinafaceRequirementsPath}"`;
            execSync(retinafaceInstallCmd, { stdio: 'inherit', env: { ...process.env, PIP_DISABLE_PIP_VERSION_CHECK: '1' } });
        }

        console.log('RetinaFace environment created successfully!');
    } catch (retinafaceError) {
        console.warn('Warning: Failed to create RetinaFace environment. RetinaFace models will not be available in packaged app.');
        console.warn('This is likely due to TensorFlow compatibility with the current Python version.');
        console.warn('Error:', retinafaceError.message);
    }
} catch (error) {
    console.error('Failed to create YOLO environment (critical).');
    console.error('Error:', error.message);
    process.exit(1);
}

// Also create python-deps for backwards compatibility
const depsDir = path.join(pythonDistDir, 'python-deps');
console.log('Creating python-deps symlink for backwards compatibility...');
try {
    execSync(`rm -f "${depsDir}"`);
} catch (_) {}
execSync(`ln -sf yolo-env "${depsDir}"`);

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