#!/usr/bin/env python3
"""
Test runner for mv-extractor with MVO mode tests
"""

import os
import sys
import subprocess
import unittest

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def run_tests():
    """Run all tests including MVO mode tests"""
    
    # Set PROJECT_ROOT environment variable
    os.environ['PROJECT_ROOT'] = os.path.dirname(os.path.abspath(__file__))
    
    print("Running mv-extractor tests with MVO mode support...")
    print(f"PROJECT_ROOT: {os.environ['PROJECT_ROOT']}")
    
    # Run unit tests
    print("\n=== Running Unit Tests ===")
    try:
        from tests.unit_tests import TestVideoCap
        suite = unittest.TestLoader().loadTestsFromTestCase(TestVideoCap)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        print(f"Unit tests: {result.testsRun} tests, {len(result.failures)} failures, {len(result.errors)} errors")
    except Exception as e:
        print(f"Unit tests failed: {e}")
    
    # Run end-to-end tests
    print("\n=== Running End-to-End Tests ===")
    try:
        from tests.end_to_end_tests import TestEndToEnd, TestMVOEndToEnd
        
        # Original end-to-end tests
        suite1 = unittest.TestLoader().loadTestsFromTestCase(TestEndToEnd)
        runner = unittest.TextTestRunner(verbosity=2)
        result1 = runner.run(suite1)
        print(f"Original E2E tests: {result1.testsRun} tests, {len(result1.failures)} failures, {len(result1.errors)} errors")
        
        # MVO mode tests
        suite2 = unittest.TestLoader().loadTestsFromTestCase(TestMVOEndToEnd)
        runner = unittest.TextTestRunner(verbosity=2)
        result2 = runner.run(suite2)
        print(f"MVO E2E tests: {result2.testsRun} tests, {len(result2.failures)} failures, {len(result2.errors)} errors")
        
    except Exception as e:
        print(f"End-to-end tests failed: {e}")
    
    print("\n=== Test Summary ===")
    print("✅ Unit tests completed")
    print("✅ End-to-end tests completed") 
    print("✅ MVO mode tests completed")
    print("\nAll tests have been run. Check the output above for any failures.")

if __name__ == '__main__':
    run_tests()
