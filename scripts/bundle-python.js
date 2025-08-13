#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const platform = process.platform;
const pythonDistDir = path.join(__dirname, '..', 'pythondist');

console.log('Creating Python bundle...');

// --- Bundled Python 3.10 support (macOS) ---
const PY_VERSION = process.env.PYTHON_310_VERSION || '3.10.14';
const bundledPythonRoot = path.join(pythonDistDir, 'base-python-3.10');

function hasExecutable(file) {
    try { fs.accessSync(file, fs.constants.X_OK); return true; } catch { return false; }
}

function findExecutableRecursively(dir, namePattern) {
    if (!fs.existsSync(dir)) return null;
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) {
            const nested = findExecutableRecursively(full, namePattern);
            if (nested) return nested;
        } else if (entry.isFile() && namePattern.test(entry.name) && hasExecutable(full)) {
            return full;
        }
    }
    return null;
}

function ensureBundledPython310() {
    // 1. Direct override path
    const override = process.env.BUNDLED_PYTHON_310;
    if (override) {
        try { execSync(`"${override}" --version`, { stdio: 'ignore' }); console.log(`Using BUNDLED_PYTHON_310: ${override}`); return override; } catch { console.warn('Override invalid, continuing.'); }
    }
    // 2. Forced system usage
    if (process.env.USE_SYSTEM_PYTHON === '1') return 'python3.10';
    // 2.5 Homebrew detection & auto-install (preferred fast path on macOS)
    if (process.platform === 'darwin') {
        let brewAvailable = false;
        try { execSync('brew --version', { stdio: 'ignore' }); brewAvailable = true; } catch (_) {}
        if (brewAvailable) {
            const brewPy = ['/opt/homebrew/opt/python@3.10/bin/python3.10','/usr/local/opt/python@3.10/bin/python3.10'];
            let found = brewPy.find(p => hasExecutable(p));
            if (!found) {
                try {
                    console.log('Homebrew python@3.10 not found, installing via brew (this may take a minute)...');
                    execSync('brew install python@3.10', { stdio: 'inherit' });
                    found = brewPy.find(p => hasExecutable(p));
                } catch (e) {
                    console.warn('brew install python@3.10 failed:', e.message);
                }
            }
            if (found) {
                console.log(`Using Homebrew python3.10 at ${found}`);
                return found;
            }
        } else {
            console.log('Homebrew not available; skipping brew-based installation.');
        }
    }
    // 3. pyenv detection
    let pyenvAvailable = false;
    let pyenvCmd = 'pyenv';
    try { execSync('pyenv --version', { stdio: 'ignore' }); pyenvAvailable = true; } catch (_) {}
    if (!pyenvAvailable) {
        // Attempt lightweight embedded pyenv clone (no shell integration) under pythondist/tools/pyenv
        const toolsDir = path.join(pythonDistDir, 'tools');
        const embeddedPyenvRoot = path.join(toolsDir, 'pyenv');
        try {
            if (!fs.existsSync(embeddedPyenvRoot)) {
                console.log('Installing embedded pyenv...');
                fs.mkdirSync(toolsDir, { recursive: true });
                execSync(`git clone --depth 1 https://github.com/pyenv/pyenv.git "${embeddedPyenvRoot}"`, { stdio: 'inherit' });
            } else {
                console.log('Embedded pyenv already present.');
            }
            // Provide a shim command using PYENV_ROOT override
            pyenvCmd = `PYENV_ROOT="${embeddedPyenvRoot}" ${embeddedPyenvRoot}/bin/pyenv`;
            execSync(`${pyenvCmd} --version`, { stdio: 'ignore', env: { ...process.env, PYENV_ROOT: embeddedPyenvRoot } });
            pyenvAvailable = true;
            console.log(`Using embedded pyenv at ${embeddedPyenvRoot}`);
        } catch (e) {
            console.warn('Embedded pyenv bootstrap failed:', e.message);
        }
    }
    if (pyenvAvailable) {
        try {
            const versionsRaw = execSync(`${pyenvCmd} versions --bare`, { env: { ...process.env, PYENV_ROOT: pyenvCmd.includes('PYENV_ROOT') ? pyenvCmd.split(' ')[1].replace(/"/g,'') : process.env.PYENV_ROOT } }).toString().split(/\n+/).map(v=>v.trim()).filter(Boolean);
            let chosen = versionsRaw.filter(v => v.startsWith('3.10.')).sort().pop();
            if (!chosen) {
                chosen = PY_VERSION; // default 3.10.14
                console.log(`pyenv: auto-installing ${chosen} (no 3.10.x found)...`);
                execSync(`${pyenvCmd} install -s ${chosen}`, { stdio: 'inherit', env: { ...process.env } });
            }
            const pyPath = execSync(`PYENV_VERSION=${chosen} ${pyenvCmd} which python`, { env: { ...process.env } }).toString().trim();
            console.log(`Using pyenv Python ${chosen} at ${pyPath}`);
            return pyPath;
        } catch (e) {
            console.warn('pyenv provisioning failed:', e.message);
        }
    }
    // 4. Homebrew paths
    const brewCandidates = [
        '/opt/homebrew/opt/python@3.10/bin/python3.10',
        '/usr/local/opt/python@3.10/bin/python3.10'
    ];
    for (const c of brewCandidates) { if (hasExecutable(c)) { console.log(`Found Homebrew python3.10 at ${c}`); return c; } }
    // 5. PATH probe
    try { execSync('python3.10 --version', { stdio: 'ignore' }); return 'python3.10'; } catch(_) {}
    console.error('No python3.10 found. Options:');
    console.error('  a) brew install python@3.10');
    console.error('  b) pyenv install 3.10.14   (pyenv auto-install failed or not present)');
    console.error('  c) export BUNDLED_PYTHON_310=/abs/path/to/python3.10');
    process.exit(1);
}

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

// Helper for RetinaFace: use forced variable or bundled interpreter
function findPythonForRetinaFace() {
    const forced = process.env.RETINAFACE_PYTHON || process.env.PYTHON_FOR_RETINAFACE;
    if (forced) {
        try {
            execSync(`"${forced}" --version`, { stdio: 'ignore' });
            console.log(`Using forced RetinaFace Python from env: ${forced}`);
            return forced;
        } catch (e) {
            console.warn(`Warning: forced RetinaFace Python not usable: ${forced}. Falling back to bundled 3.10.`);
        }
    }
    return ensureBundledPython310();
}

try {
    console.log('Creating virtual environments for better package isolation...');
    
    // Create YOLO virtual environment
    console.log('Creating YOLO virtual environment...');
    const pyForYolo = ensureBundledPython310();
    console.log(`Using ${pyForYolo} to create YOLO virtual environment...`);
    execSync(`"${pyForYolo}" -m venv "${yoloEnvDir}"`, { stdio: 'inherit' });
    
    // Install YOLO packages in virtual environment
    console.log('Installing YOLO packages...');
    const yoloPython = process.platform === 'win32'
        ? path.join(yoloEnvDir, 'Scripts', 'python.exe')
        : path.join(yoloEnvDir, 'bin', 'python');

    // Always upgrade tooling first
    execSync(`"${yoloPython}" -m pip install --no-cache-dir --upgrade pip setuptools wheel`, {
        stdio: 'inherit',
        env: { ...process.env, PIP_DISABLE_PIP_VERSION_CHECK: '1' }
    });

    // On Linux runners, prefer CPU-only PyTorch wheels to avoid CUDA resolution issues
    const isLinux = process.platform === 'linux';
    let installCmd = `"${yoloPython}" -m pip install --no-cache-dir --upgrade -r "${yoloRequirementsPath}"`;
    if (isLinux) {
        installCmd = `"${yoloPython}" -m pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple --upgrade -r "${yoloRequirementsPath}"`;
    }

    try {
        execSync(installCmd, { stdio: 'inherit', env: { ...process.env, PIP_DISABLE_PIP_VERSION_CHECK: '1' } });
    } catch (primaryInstallError) {
        console.warn('Primary YOLO dependency install failed. Attempting fallback with pinned CPU torch/torchvision...');
        try {
            // Install pinned torch/torchvision CPU wheels first, then the rest of the requirements
            if (isLinux) {
                execSync(`"${yoloPython}" -m pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple torch==2.2.2 torchvision==0.17.2`, {
                    stdio: 'inherit',
                    env: { ...process.env, PIP_DISABLE_PIP_VERSION_CHECK: '1' }
                });
            } else {
                execSync(`"${yoloPython}" -m pip install --no-cache-dir torch==2.2.2 torchvision==0.17.2`, {
                    stdio: 'inherit',
                    env: { ...process.env, PIP_DISABLE_PIP_VERSION_CHECK: '1' }
                });
            }

            // Install remaining requirements; already-installed pins will be kept if compatible
            execSync(`"${yoloPython}" -m pip install --no-cache-dir --upgrade -r "${yoloRequirementsPath}"`, {
                stdio: 'inherit',
                env: { ...process.env, PIP_DISABLE_PIP_VERSION_CHECK: '1' }
            });
        } catch (fallbackError) {
            console.error('Fallback YOLO dependency install also failed.');
            throw fallbackError;
        }
    }
    
    // Create RetinaFace virtual environment
    console.log('Creating RetinaFace virtual environment...');
    try {
        const retinafacePythonSystem = findPythonForRetinaFace();
        console.log(`Selected system Python for RetinaFace venv: ${retinafacePythonSystem}`);
        execSync(`${retinafacePythonSystem} -m venv "${retinafaceEnvDir}"`, { stdio: 'inherit' });

        console.log('Installing RetinaFace packages...');
        const retinafacePython = process.platform === 'win32'
            ? path.join(retinafaceEnvDir, 'Scripts', 'python.exe')
            : path.join(retinafaceEnvDir, 'bin', 'python');

        // Verify Python version compatibility for TensorFlow (2.15 supports up to 3.11)
        try {
            const verOut = execSync(`"${retinafacePython}" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"`).toString().trim();
            const [maj, min] = verOut.split('.').map(Number);
            if (maj !== 3 || min > 11) {
                throw new Error(`Unsupported Python ${verOut} for TensorFlow; install Python 3.10 or 3.11 and set RETINAFACE_PYTHON`);
            }
            console.log(`RetinaFace Python version: ${verOut}`);
        } catch (verErr) {
            console.error('RetinaFace Python version check failed:', verErr.message);
            throw verErr;
        }

        // Always upgrade pip tooling first
        execSync(`"${retinafacePython}" -m pip install --no-cache-dir --upgrade pip setuptools wheel`, { stdio: 'inherit', env: { ...process.env, PIP_DISABLE_PIP_VERSION_CHECK: '1' } });

        const isDarwin = process.platform === 'darwin';
        const isArm64 = process.arch === 'arm64';
        const isX64 = process.arch === 'x64';
        let retinafaceOk = false;

        function installList(pkgs, note) {
            console.log(`Installing RetinaFace package set (${note})...`);
            const quoted = pkgs.map(p => `"${p}"`).join(' ');
            execSync(`"${retinafacePython}" -m pip install --no-cache-dir ${quoted}`, { stdio: 'inherit', env: { ...process.env, PIP_DISABLE_PIP_VERSION_CHECK: '1' } });
            retinafaceOk = true;
        }

        try {
            if (isDarwin && isArm64) {
                // Apple Silicon path
                installList([
                    'flask', 'flask-cors', 'graphene>=3.0', 'flask-graphql>=2.0',
                    'opencv-python', 'pillow', 'numpy<2.0.0',
                    'tensorflow-macos==2.15.0', 'tensorflow-metal==1.1.0', 'tf-keras==2.15.0',
                    'retina-face>=0.0.14'
                ], 'macOS arm64 TF 2.15 + metal');
            } else if (isDarwin && isX64) {
                // Intel mac: use standard tensorflow 2.15 (CPU) which supports py3.10
                installList([
                    'flask', 'flask-cors', 'graphene>=3.0', 'flask-graphql>=2.0',
                    'opencv-python', 'pillow', 'numpy<2.0.0',
                    'tensorflow==2.15.0', 'tf-keras==2.15.0',
                    'retina-face>=0.0.14'
                ], 'macOS x64 TF 2.15 CPU');
            } else {
                // Other platforms: first try requirements file (may specify newer TF)
                console.log('Installing RetinaFace requirements from file...');
                execSync(`"${retinafacePython}" -m pip install --no-cache-dir --upgrade -r "${retinafaceRequirementsPath}"`, { stdio: 'inherit', env: { ...process.env, PIP_DISABLE_PIP_VERSION_CHECK: '1' } });
                retinafaceOk = true;
            }
        } catch (primaryRfError) {
            console.warn('Primary RetinaFace install attempt failed:', primaryRfError.message);
            console.warn('Attempting fallback with conservative TF 2.15 CPU set...');
            try {
                installList([
                    'flask', 'flask-cors', 'graphene>=3.0', 'flask-graphql>=2.0',
                    'opencv-python', 'pillow', 'numpy<2.0.0',
                    'tensorflow==2.15.0', 'tf-keras==2.15.0',
                    'retina-face>=0.0.14'
                ], 'fallback TF 2.15 CPU');
            } catch (fallbackRfError) {
                console.warn('Fallback RetinaFace install failed:', fallbackRfError.message);
                console.warn('RetinaFace env will be incomplete (optional feature).');
            }
        }

        if (retinafaceOk) {
            console.log('RetinaFace environment created successfully!');
        } else {
            console.error('RetinaFace environment failed to install required packages (fatal).');
            throw new Error('RetinaFace environment incomplete');
        }
    } catch (retinafaceError) {
        console.error('Failed to create RetinaFace environment (fatal)');
        console.error('Error:', retinafaceError.message);
        process.exit(1);
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