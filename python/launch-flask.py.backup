#!/usr/bin/env python3
"""
Python launcher that adds bundled dependencies to sys.path before importing the main API
"""
import sys
import os
import argparse

# Add bundled dependencies to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
deps_dir = os.path.join(current_dir, 'python-deps')
if os.path.exists(deps_dir):
    sys.path.insert(0, deps_dir)

# Import and run the main API
from api import app, apiSigningKey

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apiport", type=int, default=5000)
    parser.add_argument("--signingkey", type=str, default="")
    args = parser.parse_args()
    
    # Update global signing key
    import api
    api.apiSigningKey = args.signingkey
    
    app.run(port=args.apiport)