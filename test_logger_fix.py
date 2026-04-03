#!/usr/bin/env python3
"""
LOGGER FIX TEST SCRIPT
Test to verify logger import fix works properly
Run this to confirm the fix before running full attack
"""

import sys
import traceback

def test_main_imports():
    """Test that main.py imports work without logger errors"""
    print("🔍 Testing main.py imports...")
    try:
        import main
        print("✅ main.py imported successfully - logger error FIXED!")
        return True
    except NameError as e:
        if "'logger' is not defined" in str(e):
            print(f"❌ Logger error still exists: {e}")
            return False
        else:
            print(f"❌ Different NameError: {e}")
            return False
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_logger_functionality():
    """Test basic logger functionality"""
    print("\n🔍 Testing logger functionality...")
    try:
        import logging
        
        # Test standard logger
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.INFO)
        
        # Create a simple handler to capture output
        import io
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger.addHandler(handler)
        
        # Test logging
        logger.info("Test info message")
        logger.error("Test error message")
        logger.warning("Test warning message")
        
        # Check if messages were logged
        output = stream.getvalue()
        if "Test info message" in output or "Test error message" in output:
            print("✅ Standard logging works correctly!")
            return True
        else:
            print("❌ Standard logging failed - no output captured")
            return False
            
    except Exception as e:
        print(f"❌ Logger functionality test failed: {e}")
        return False

def test_audit_logger():
    """Test audit logger integration"""
    print("\n🔍 Testing audit logger...")
    try:
        from audit_logger import init_audit_logger, get_audit_logger
        
        # Initialize audit logger
        audit_logger = init_audit_logger("test_audit_fix.jsonl", enabled=True)
        
        if audit_logger:
            print("✅ Audit logger initialized successfully!")
            
            # Test basic audit logging
            audit_logger.log_scan_start("test.com", "hackathon", {"test": True})
            print("✅ Audit logging test successful!")
            
            # Clean up test file
            import os
            if os.path.exists("test_audit_fix.jsonl"):
                os.remove("test_audit_fix.jsonl")
            
            return True
        else:
            print("❌ Audit logger failed to initialize")
            return False
            
    except Exception as e:
        print(f"❌ Audit logger test failed: {e}")
        return False

def test_quick_attack_simulation():
    """Test a quick attack simulation to verify no logger errors"""
    print("\n🔍 Testing quick attack simulation...")
    try:
        # Import required modules
        from scope_checker import ScopeChecker
        from audit_logger import init_audit_logger
        
        # Initialize audit logger
        init_audit_logger("test_quick_audit.jsonl", enabled=True)
        
        # Test scope checking (minimal operation)
        scope_checker = ScopeChecker("hackathon_test.txt")
        is_valid = scope_checker.check("test.com")
        
        print(f"✅ Quick scope check completed (result: {is_valid})")
        
        # Clean up
        import os
        if os.path.exists("test_quick_audit.jsonl"):
            os.remove("test_quick_audit.jsonl")
        if os.path.exists("hackathon_test.txt"):
            os.remove("hackathon_test.txt")
            
        return True
        
    except Exception as e:
        print(f"❌ Quick attack simulation failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all logger tests"""
    print("=" * 60)
    print("🧪 TRISHUL LOGGER FIX VERIFICATION TEST")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Main imports
    if test_main_imports():
        tests_passed += 1
    
    # Test 2: Logger functionality  
    if test_logger_functionality():
        tests_passed += 1
        
    # Test 3: Audit logger
    if test_audit_logger():
        tests_passed += 1
        
    # Test 4: Quick attack simulation
    if test_quick_attack_simulation():
        tests_passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED! Logger fix is successful!")
        print("✅ Your attack should no longer show logger errors")
        print("🚀 Safe to run full attack or continue current one")
    else:
        print(f"⚠️  {total_tests - tests_passed} tests failed - logger issues may persist")
        print("🔧 Check the error messages above for details")
    
    print("=" * 60)

if __name__ == "__main__":
    main()