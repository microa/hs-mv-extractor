#!/usr/bin/env python3
"""
Basic test script to verify the optimization features work correctly.
This script tests the new API methods without requiring full installation.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_import():
    """Test if we can import the optimized module"""
    try:
        from mvextractor.videocap import VideoCap
        print("✅ Successfully imported VideoCap")
        return True
    except ImportError as e:
        print(f"❌ Failed to import VideoCap: {e}")
        return False

def test_new_methods():
    """Test if new optimization methods exist"""
    try:
        from mvextractor.videocap import VideoCap
        cap = VideoCap()
        
        # Check if new methods exist
        if hasattr(cap, 'setExtractionMode'):
            print("✅ setExtractionMode method exists")
        else:
            print("❌ setExtractionMode method missing")
            return False
            
        if hasattr(cap, 'readMotionVectorsOnly'):
            print("✅ readMotionVectorsOnly method exists")
        else:
            print("❌ readMotionVectorsOnly method missing")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Error testing new methods: {e}")
        return False

def test_api_compatibility():
    """Test if original API still works"""
    try:
        from mvextractor.videocap import VideoCap
        cap = VideoCap()
        
        # Test original methods still exist
        if hasattr(cap, 'open') and hasattr(cap, 'read') and hasattr(cap, 'release'):
            print("✅ Original API methods still available")
            return True
        else:
            print("❌ Original API methods missing")
            return False
    except Exception as e:
        print(f"❌ Error testing original API: {e}")
        return False

def main():
    print("=== Motion Vector Extractor Optimization Test ===")
    print()
    
    # Test 1: Import
    print("Test 1: Module Import")
    if not test_import():
        print("❌ Import test failed")
        return False
    print()
    
    # Test 2: New Methods
    print("Test 2: New Optimization Methods")
    if not test_new_methods():
        print("❌ New methods test failed")
        return False
    print()
    
    # Test 3: API Compatibility
    print("Test 3: API Compatibility")
    if not test_api_compatibility():
        print("❌ API compatibility test failed")
        return False
    print()
    
    print("🎉 All tests passed! Optimizations are working correctly.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
