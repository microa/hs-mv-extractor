#!/usr/bin/env python3
"""
MVO-only test runner - tests only MVO functionality
"""

import os
import sys
import unittest

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set PROJECT_ROOT environment variable
os.environ['PROJECT_ROOT'] = os.path.dirname(os.path.abspath(__file__))

def run_mvo_tests():
    """Run only MVO mode tests"""
    
    print("Running MVO mode tests only...")
    print(f"PROJECT_ROOT: {os.environ['PROJECT_ROOT']}")
    
    # Run MVO end-to-end tests
    print("\n=== Running MVO End-to-End Tests ===")
    try:
        import tests.end_to_end_tests as e2e_tests
        
        # MVO mode tests only
        suite = unittest.TestLoader().loadTestsFromTestCase(e2e_tests.TestMVOEndToEnd)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        print(f"MVO E2E tests: {result.testsRun} tests, {len(result.failures)} failures, {len(result.errors)} errors")
        
        if result.testsRun > 0 and len(result.failures) == 0 and len(result.errors) == 0:
            print("✅ All MVO tests passed!")
            return True
        else:
            print("❌ Some MVO tests failed")
            return False
        
    except Exception as e:
        print(f"MVO tests failed: {e}")
        return False

if __name__ == '__main__':
    success = run_mvo_tests()
    if success:
        print("\n🎉 MVO mode is working correctly!")
    else:
        print("\n❌ MVO mode has issues")
        sys.exit(1)
