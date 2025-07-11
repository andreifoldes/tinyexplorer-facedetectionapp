#!/usr/bin/env python3
"""
Script to check if all required dependencies for RetinaFace are installed
"""
import sys
import subprocess
import importlib.util

def check_package(package_name, import_name=None):
    """Check if a package is installed and can be imported"""
    if import_name is None:
        import_name = package_name
    
    try:
        spec = importlib.util.find_spec(import_name)
        if spec is not None:
            module = importlib.import_module(import_name)
            version = getattr(module, '__version__', 'Unknown version')
            print(f"✅ {package_name}: {version}")
            return True
        else:
            print(f"❌ {package_name}: Not found")
            return False
    except ImportError as e:
        print(f"❌ {package_name}: Import error - {e}")
        return False
    except Exception as e:
        print(f"⚠️  {package_name}: Error checking - {e}")
        return False

def install_package(package_name):
    """Install a package using pip"""
    try:
        print(f"🔄 Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ {package_name} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package_name}: {e}")
        return False

def main():
    """Main function to check and install dependencies"""
    print("🔍 Checking RetinaFace Dependencies")
    print("=" * 50)
    
    # Required packages for RetinaFace
    required_packages = [
        ("tensorflow", "tensorflow"),
        ("opencv-python", "cv2"),
        ("numpy", "numpy"), 
        ("pillow", "PIL"),
        ("retina-face", "retinaface")
    ]
    
    missing_packages = []
    
    # Check each package
    for package_name, import_name in required_packages:
        if not check_package(package_name, import_name):
            missing_packages.append(package_name)
    
    print("\n" + "=" * 50)
    
    if not missing_packages:
        print("🎉 All required packages are installed!")
        print("\nYou can now run: python test_retinaface.py")
        return True
    else:
        print(f"❌ Missing {len(missing_packages)} package(s):")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        
        print("\n💡 Installation commands:")
        if "retina-face" in missing_packages:
            print("   pip install retina-face")
        if "tensorflow" in missing_packages:
            print("   pip install tensorflow")
        if "opencv-python" in missing_packages:
            print("   pip install opencv-python")
        if "numpy" in missing_packages:
            print("   pip install numpy")
        if "pillow" in missing_packages:
            print("   pip install pillow")
        
        # Ask if user wants to auto-install
        try:
            response = input("\n🤔 Would you like to auto-install missing packages? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                print("\n🚀 Installing missing packages...")
                all_installed = True
                for pkg in missing_packages:
                    if not install_package(pkg):
                        all_installed = False
                
                if all_installed:
                    print("\n🎉 All packages installed successfully!")
                    print("You can now run: python test_retinaface.py")
                    return True
                else:
                    print("\n❌ Some packages failed to install. Please install manually.")
                    return False
            else:
                print("\n📝 Please install the missing packages manually and run this script again.")
                return False
        except KeyboardInterrupt:
            print("\n\n👋 Installation cancelled by user.")
            return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 