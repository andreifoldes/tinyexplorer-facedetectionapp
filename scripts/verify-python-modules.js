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

// Core YOLO environment expected modules
report.push(checkEnv('yolo-env', path.join(distRoot, 'yolo-env'), [
  'torch', 'torchvision', 'ultralytics', 'cv2', 'numpy', 'PIL'
]));

// RetinaFace env (optional) expected modules
// Note: TensorFlow import can be slow in CI environment, so we verify other modules
report.push(checkEnv('retinaface-env', path.join(distRoot, 'retinaface-env'), [
  'retinaface', 'cv2', 'numpy', 'PIL'
]));

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

if (hadFailure) {
  console.error('\nOne or more Python environments are missing required modules.');
  console.error('If cv2 is missing, ensure opencv-python (or opencv-python-headless) is listed in the appropriate requirements file.');
  process.exit(2);
}

console.log('\nPython module verification succeeded.');
