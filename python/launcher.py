#!/usr/bin/env python3
"""
Launcher script for packaged Python subprocess.
Sets up the Python path to include bundled dependencies before running the main script.
"""
import sys
import os
import json

def setup_python_path():
    """Add bundled dependencies to Python path"""
    # Get the directory where this launcher script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # The python-deps directory should be at the same level as the python directory
    parent_dir = os.path.dirname(script_dir)
    deps_dir = os.path.join(parent_dir, 'python-deps')
    
    # Sanitize environment to avoid leaking user site-packages or PYTHONPATH
    os.environ.pop('PYTHONPATH', None)
    os.environ['PYTHONNOUSERSITE'] = '1'

    # Add dependencies directory to Python path if it exists (prepend)
    if os.path.exists(deps_dir):
        # Add the deps directory itself
        if deps_dir not in sys.path:
            sys.path.insert(0, deps_dir)
        
        print(f"Added bundled dependencies from: {deps_dir}", file=sys.stderr)
    else:
        print(f"Warning: Bundled dependencies not found at: {deps_dir}", file=sys.stderr)
    
    # Also add the script directory itself to path (prepend)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    
    # Log Python path for debugging
    print(f"Python path setup complete. Script dir: {script_dir}", file=sys.stderr)
    print(f"Python version: {sys.version}", file=sys.stderr)
    print(f"Python executable: {sys.executable}", file=sys.stderr)

def main():
    """Main entry point - setup path and run subprocess API"""
    try:
        # Setup Python path for bundled dependencies
        setup_python_path()
        
        # Now import and run the subprocess API
        # Import here after path is set up
        import subprocess_api
        
        # Create and run the API
        api = subprocess_api.SubprocessAPI()
        api.run()
        
    except ImportError as e:
        error_msg = {
            "type": "error",
            "message": f"Failed to import subprocess_api: {str(e)}"
        }
        print(json.dumps(error_msg))
        sys.stderr.write(f"Import error: {e}\n")
        sys.stderr.write(f"Python path: {sys.path}\n")
        sys.exit(1)
    except Exception as e:
        error_msg = {
            "type": "error", 
            "message": f"Launcher error: {str(e)}"
        }
        print(json.dumps(error_msg))
        sys.stderr.write(f"Launcher error: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()