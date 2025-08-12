#!/usr/bin/env node
/**
 * Post-bundle verification ensuring required Python modules are present
 * inside the packaged virtual environments. Fails fast in CI instead of
 * at runtime when the Electron app starts the Python subprocess.
 */
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const distRoot = path.join(root, 'pythondist');

function venvPython(venvDir) {
  return process.platform === 'win32'
    ? path.join(venvDir, 'Scripts', 'python.exe')
    : path.join(venvDir, 'bin', 'python');
}

function checkEnv(name, dir, modules) {
  if (!fs.existsSync(dir)) {
    console.warn(`[verify-python-modules] Skipping ${name}: directory not found (${dir})`);
    return { name, skipped: true };
  }
  const py = venvPython(dir);
  if (!fs.existsSync(py)) {
    console.warn(`[verify-python-modules] Skipping ${name}: python executable not found (${py})`);
    return { name, skipped: true };
  }
  const missing = [];
  for (const m of modules) {
    try {
      // Use -c for cross-platform compatibility instead of heredoc
      const pythonCode = `import importlib, sys; mod = '${m}'; importlib.import_module(mod)`;
      execSync(`"${py}" -c "${pythonCode}"`, { stdio: 'pipe' });
    } catch (e) {
      missing.push(m);
      // For tensorflow specifically, provide more debugging info
      if (m === 'tensorflow') {
        try {
          const debugOutput = execSync(`"${py}" -c "import sys; print('Python path:', sys.path); import tensorflow as tf; print('TF version:', tf.__version__)"`, { stdio: 'pipe', encoding: 'utf-8' });
          console.log(`Tensorflow debug info for ${name}:`, debugOutput);
        } catch (debugError) {
          console.log(`Tensorflow import error for ${name}:`, debugError.stderr ? debugError.stderr.toString() : debugError.message);
        }
      }
    }
  }
  return { name, missing, skipped: false };
}

const report = [];

// Core YOLO environment: importing ultralytics implies its deps are present
report.push(checkEnv('yolo-env', path.join(distRoot, 'yolo-env'), [
  'ultralytics'
]));

// RetinaFace env (optional): On macOS arm64, also import tensorflow to catch plugin/version issues early
const isDarwinArm64 = process.platform === 'darwin' && process.arch === 'arm64';
const retinafaceChecks = isDarwinArm64 ? ['retinaface', 'tensorflow'] : ['retinaface'];
report.push(checkEnv('retinaface-env', path.join(distRoot, 'retinaface-env'), retinafaceChecks));

let hadFailure = false;
for (const r of report) {
  if (r.skipped) continue;
  if (r.missing.length) {
    hadFailure = true;
    console.error(`Environment ${r.name} is missing modules: ${r.missing.join(', ')}`);
  } else {
    console.log(`Environment ${r.name} OK (all required modules importable).`);
  }
}

// On macOS arm64, run a brief TensorFlow sanity check to catch plugin/version issues (e.g., metal plugin)
if (process.platform === 'darwin' && process.arch === 'arm64') {
  const rfPy = venvPython(path.join(distRoot, 'retinaface-env'));
  if (fs.existsSync(rfPy)) {
    try {
      // Use only single quotes inside Python code so we can wrap with double quotes safely
      const code = "import tensorflow as tf; print('TF version:', tf.__version__); print('Devices:', tf.config.list_physical_devices())";
      console.log('[verify-python-modules] TensorFlow sanity check (retinaface-env)...');
      execSync(`"${rfPy}" -c "${code}"`, { stdio: 'inherit' });
    } catch (e) {
      hadFailure = true;
      console.error('[verify-python-modules] TensorFlow sanity check failed in retinaface-env');
    }

    // Optional: RetinaFace smoke test - just verify import works, don't run detection
    // (detection might try to download model weights which requires gdown)
    if (process.env.SMOKE_TEST_RETINAFACE === '1') {
      console.log('\n==================================================');
      console.log('[RETINAFACE SMOKE TEST] Starting smoke test...');
      console.log('==================================================');
      try {
        const smoke = [
          "import os, sys",
          "os.environ['TF_CPP_MIN_LOG_LEVEL']='2'",
          "print('[SMOKE TEST] Testing RetinaFace module import...')",
          "from retinaface import RetinaFace",
          "print('[SMOKE TEST] ✅ RetinaFace module imported successfully')",
          "print('[SMOKE TEST] Testing numpy import...')",
          "import numpy as np",
          "print('[SMOKE TEST] ✅ numpy imported successfully')",
          "print('[SMOKE TEST] Testing cv2 (opencv-python) import...')",
          "import cv2",
          "print('[SMOKE TEST] ✅ cv2 imported successfully')",
          "print('[SMOKE TEST] All required modules are available for RetinaFace')"
        ].join('; ');
        execSync(`"${rfPy}" -c "${smoke}"`, { stdio: 'inherit' });
        console.log('==================================================');
        console.log('[RETINAFACE SMOKE TEST] ✅ PASSED - All checks successful');
        console.log('==================================================\n');
      } catch (e) {
        hadFailure = true;
        console.error('==================================================');
        console.error('[RETINAFACE SMOKE TEST] ❌ FAILED');
        console.error('Error details:', e.message || 'Unknown error');
        console.error('This might indicate missing dependencies like gdown, opencv-python, or numpy');
        console.error('==================================================\n');
      }
    } else {
      console.log('\n[RETINAFACE SMOKE TEST] Skipped (set SMOKE_TEST_RETINAFACE=1 to enable)\n');
    }
  }
}

if (hadFailure) {
  console.error('\nOne or more Python environments are missing required modules.');
  console.error('If cv2 is missing, ensure opencv-python (or opencv-python-headless) is listed in the appropriate requirements file.');
  process.exit(2);
}

console.log('\nPython module verification succeeded.');
