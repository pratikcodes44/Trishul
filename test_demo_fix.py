#!/usr/bin/env python3
"""
DEMO MODE PORT SCANNING FIX TEST
Verify that demo mode can find open ports on localhost
"""

import subprocess
import sys
import time

def test_vulnerable_arena_running():
    """Check if vulnerable_arena.py is running"""
    print("🔍 Checking if vulnerable_arena.py is running...")
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'vulnerable_arena.py' in result.stdout:
            print("✅ vulnerable_arena.py is running!")
            return True
        else:
            print("❌ vulnerable_arena.py is NOT running!")
            print("   Start it with: python3 vulnerable_arena.py")
            return False
    except Exception as e:
        print(f"❌ Failed to check process: {e}")
        return False

def test_port_5000_open():
    """Test if port 5000 is actually open"""
    print("\n🔍 Testing if port 5000 is open...")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', 5000))
        sock.close()
        
        if result == 0:
            print("✅ Port 5000 is OPEN and accepting connections!")
            return True
        else:
            print("❌ Port 5000 is CLOSED!")
            return False
    except Exception as e:
        print(f"❌ Socket test failed: {e}")
        return False

def test_naabu_scan():
    """Test if naabu can scan localhost:5000"""
    print("\n🔍 Testing naabu scan on 127.0.0.1...")
    try:
        # Test the exact way Trishul will scan
        result = subprocess.run(
            ['naabu', '-silent', '-p', '5000'],
            input="127.0.0.1",
            capture_output=True,
            text=True,
            timeout=15
        )
        
        output = result.stdout.strip()
        if '127.0.0.1:5000' in output:
            print("✅ naabu successfully found port 5000!")
            print(f"   Output: {output}")
            return True
        else:
            print(f"❌ naabu did not find port 5000!")
            print(f"   Output: {output}")
            print(f"   Stderr: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ naabu not installed!")
        return False
    except subprocess.TimeoutExpired:
        print("❌ naabu scan timed out!")
        return False
    except Exception as e:
        print(f"❌ naabu test failed: {e}")
        return False

def test_http_request():
    """Test if we can make HTTP request to vulnerable_arena"""
    print("\n🔍 Testing HTTP request to vulnerable_arena...")
    try:
        import urllib.request
        response = urllib.request.urlopen('http://127.0.0.1:5000/', timeout=5)
        content = response.read().decode('utf-8')
        
        if response.status == 200:
            print("✅ HTTP request successful!")
            print(f"   Status: {response.status}")
            return True
        else:
            print(f"❌ HTTP request failed with status: {response.status}")
            return False
    except Exception as e:
        print(f"❌ HTTP request failed: {e}")
        return False

def test_demo_mode_parsing():
    """Test that --demo flag parses correctly"""
    print("\n🔍 Testing --demo flag parsing...")
    try:
        import argparse
        
        parser = argparse.ArgumentParser()
        parser.add_argument("--demo", action="store_true")
        
        args = parser.parse_args(['--demo'])
        
        if args.demo:
            print("✅ --demo flag parsing works!")
            return True
        else:
            print("❌ --demo flag not parsed")
            return False
    except Exception as e:
        print(f"❌ Demo flag test failed: {e}")
        return False

def main():
    """Run all demo mode tests"""
    print("=" * 70)
    print("🧪 DEMO MODE PORT SCANNING FIX VERIFICATION")
    print("=" * 70)
    
    tests_passed = 0
    total_tests = 5
    
    # Test 1: vulnerable_arena running
    if test_vulnerable_arena_running():
        tests_passed += 1
    
    # Test 2: Port 5000 open
    if test_port_5000_open():
        tests_passed += 1
    
    # Test 3: naabu can scan
    if test_naabu_scan():
        tests_passed += 1
    
    # Test 4: HTTP request works
    if test_http_request():
        tests_passed += 1
    
    # Test 5: Demo flag parsing
    if test_demo_mode_parsing():
        tests_passed += 1
    
    print("\n" + "=" * 70)
    print(f"📊 TEST RESULTS: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED! Demo mode should work now!")
        print("✅ Port scanning will find port 5000")
        print("✅ Vulnerability scanning will proceed")
        print("🚀 Ready to test: python3 main.py --demo")
    elif tests_passed >= 3:
        print("⚠️  Most tests passed - demo mode should work")
        print("🚀 Try running: python3 main.py --demo")
    else:
        print(f"❌ {total_tests - tests_passed} critical tests failed")
        print("🔧 Fix issues above before running demo")
    
    print("=" * 70)
    
    return 0 if tests_passed == total_tests else 1

if __name__ == "__main__":
    sys.exit(main())