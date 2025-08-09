#!/usr/bin/env python3
"""
Comprehensive test for all face detection models
"""

import subprocess
import json
import time
import sys
import os

class ModelTester:
    def __init__(self):
        self.yolo_models = [
            "yolov8n-face.pt",
            "yolov8m-face.pt",
            "yolov8l-face.pt",
            "yolov11m-face.pt",
            "yolov11l-face.pt",
            "yolov12l-face.pt"
        ]
        self.retinaface_models = ["RetinaFace"]
        self.results = []

    def test_model(self, model_name, env_type='yolo'):
        """Test a single model"""
        print(f"\n{'='*60}")
        print(f"🔬 Testing {model_name} ({env_type} environment)")
        print(f"{'='*60}")
        
        result = {
            'model': model_name,
            'environment': env_type,
            'load_success': False,
            'load_time': 0,
            'error': None
        }
        
        # Choose Python environment
        if env_type == 'retinaface':
            python_cmd = './retinaface-env/bin/python'
        else:
            python_cmd = './yolo-env/bin/python'
        
        # Set environment
        env = os.environ.copy()
        env['MODEL_TYPE'] = env_type
        
        # Start subprocess
        try:
            proc = subprocess.Popen(
                [python_cmd, 'python/subprocess_api.py'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            
            # Wait for ready
            print("⏳ Waiting for subprocess...")
            if not self.wait_for_ready(proc):
                result['error'] = "Subprocess failed to start"
                print("❌ Subprocess failed to start")
                proc.terminate()
                return result
            
            print("✅ Subprocess ready")
            
            # Load model
            print(f"📦 Loading {model_name}...")
            load_start = time.time()
            
            load_cmd = {
                "type": "load_model",
                "data": {"model_path": model_name},
                "id": 1
            }
            
            proc.stdin.write(json.dumps(load_cmd) + '\n')
            proc.stdin.flush()
            
            # Wait for load response
            response = self.wait_for_response(proc, 1, timeout=60)
            load_time = time.time() - load_start
            result['load_time'] = load_time
            
            if response and response.get('response', {}).get('status') == 'success':
                result['load_success'] = True
                print(f"✅ Model loaded successfully in {load_time:.2f}s")
            else:
                error_msg = response.get('response', {}).get('message', 'Unknown error') if response else 'No response'
                result['error'] = error_msg
                print(f"❌ Failed to load: {error_msg}")
            
            # Gracefully exit
            proc.stdin.write(json.dumps({"type": "exit"}) + '\n')
            proc.stdin.flush()
            time.sleep(0.5)
            proc.terminate()
            
            # Force kill if still running
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                proc.kill()
                
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Exception: {e}")
            
        return result

    def wait_for_ready(self, proc, timeout=15):
        """Wait for subprocess to be ready"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            line = proc.stdout.readline()
            if line:
                try:
                    msg = json.loads(line.strip())
                    if msg.get('type') == 'ready':
                        return True
                except:
                    pass
        return False

    def wait_for_response(self, proc, cmd_id, timeout=30):
        """Wait for specific response"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            line = proc.stdout.readline()
            if line:
                try:
                    msg = json.loads(line.strip())
                    if msg.get('type') == 'response' and msg.get('id') == cmd_id:
                        return msg
                except:
                    pass
        return None

    def run_tests(self):
        """Run all model tests"""
        print("🚀 Starting Comprehensive Face Detection Model Tests")
        print("="*60)
        
        # Test YOLO models
        print("\n📦 Testing YOLO Models")
        for model in self.yolo_models:
            result = self.test_model(model, 'yolo')
            self.results.append(result)
            time.sleep(1)  # Brief pause
        
        # Test RetinaFace
        print("\n📦 Testing RetinaFace Model")
        for model in self.retinaface_models:
            result = self.test_model(model, 'retinaface')
            self.results.append(result)
        
        # Generate report
        self.generate_report()

    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY REPORT")
        print("="*60)
        
        # Count successes
        successful = [r for r in self.results if r['load_success']]
        failed = [r for r in self.results if not r['load_success']]
        
        # YOLO results
        yolo_results = [r for r in self.results if r['environment'] == 'yolo']
        if yolo_results:
            print("\n🔷 YOLO Models:")
            for r in yolo_results:
                status = "✅" if r['load_success'] else "❌"
                time_str = f"({r['load_time']:.2f}s)" if r['load_success'] else f"({r.get('error', 'Unknown')})"
                print(f"  {status} {r['model']:20s} {time_str}")
        
        # RetinaFace results
        retina_results = [r for r in self.results if r['environment'] == 'retinaface']
        if retina_results:
            print("\n🔶 RetinaFace Model:")
            for r in retina_results:
                status = "✅" if r['load_success'] else "❌"
                time_str = f"({r['load_time']:.2f}s)" if r['load_success'] else f"({r.get('error', 'Unknown')})"
                print(f"  {status} {r['model']:20s} {time_str}")
        
        # Overall summary
        print("\n" + "-"*60)
        print(f"✅ Successful: {len(successful)}/{len(self.results)}")
        print(f"❌ Failed: {len(failed)}/{len(self.results)}")
        
        if successful:
            # Performance stats
            load_times = [r['load_time'] for r in successful]
            avg_time = sum(load_times) / len(load_times)
            fastest = min(successful, key=lambda x: x['load_time'])
            slowest = max(successful, key=lambda x: x['load_time'])
            
            print(f"\n⚡ Performance:")
            print(f"  Average load time: {avg_time:.2f}s")
            print(f"  Fastest: {fastest['model']} ({fastest['load_time']:.2f}s)")
            print(f"  Slowest: {slowest['model']} ({slowest['load_time']:.2f}s)")
        
        print("\n🎯 Testing Complete!")
        
        return len(failed) == 0

if __name__ == "__main__":
    tester = ModelTester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)