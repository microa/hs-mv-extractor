#!/usr/bin/env python3
"""
Basic MVO mode test - tests core functionality without external dependencies
"""

import os
import sys
import unittest

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class TestMVOBasic(unittest.TestCase):
    """Basic MVO mode tests that don't require video files"""
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            from mvextractor.videocap import VideoCap
            self.VideoCap = VideoCap
            self.cap = VideoCap()
        except ImportError:
            self.VideoCap = None
            self.cap = None
    
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()
    
    def test_video_cap_creation(self):
        """Test VideoCap object creation"""
        if self.cap is None:
            self.skipTest("VideoCap not available")
        self.assertIsNotNone(self.cap)
    
    def test_mvo_api_availability(self):
        """Test MVO API availability"""
        if self.cap is None:
            self.skipTest("VideoCap not available")
        
        # Check for new API
        has_new_api = hasattr(self.cap, 'set_motion_vectors_only')
        # Check for old API
        has_old_api = hasattr(self.cap, 'setMotionVectorsOnly')
        
        # At least one API should be available
        self.assertTrue(has_new_api or has_old_api, 
                      "At least one MVO API should be available")
    
    def test_mvo_mode_activation(self):
        """Test MVO mode activation without video"""
        if self.cap is None:
            self.skipTest("VideoCap not available")
        
        # Test new API
        if hasattr(self.cap, 'set_motion_vectors_only'):
            # Should not raise an exception
            self.cap.set_motion_vectors_only(True)
            self.cap.set_motion_vectors_only(False)
        
        # Test old API
        if hasattr(self.cap, 'setMotionVectorsOnly'):
            # Should not raise an exception
            self.cap.setMotionVectorsOnly(True)
            self.cap.setMotionVectorsOnly(False)
    
    def test_mvo_mode_consistency(self):
        """Test MVO mode API consistency"""
        if self.cap is None:
            self.skipTest("VideoCap not available")
        
        # Test that both API names work if available
        if hasattr(self.cap, 'set_motion_vectors_only'):
            self.cap.set_motion_vectors_only(True)
            self.cap.set_motion_vectors_only(False)
        
        if hasattr(self.cap, 'setMotionVectorsOnly'):
            self.cap.setMotionVectorsOnly(True)
            self.cap.setMotionVectorsOnly(False)
    
    def test_mvo_mode_with_synthetic_video(self):
        """Test MVO mode with synthetic video (if available)"""
        if self.cap is None:
            self.skipTest("VideoCap not available")
        
        # Try to create a simple test video
        test_video = "test_video.mp4"
        
        # Create a simple test video using ffmpeg if available
        try:
            import subprocess
            result = subprocess.run([
                'ffmpeg', '-f', 'lavfi', '-i', 'testsrc=duration=2:size=320x240:rate=30',
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-y', test_video
            ], capture_output=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(test_video):
                # Test with the synthetic video
                ret = self.cap.open(test_video)
                if ret:
                    # Enable MVO mode
                    if hasattr(self.cap, 'set_motion_vectors_only'):
                        self.cap.set_motion_vectors_only(True)
                    
                    # Read one frame
                    ret, frame, mvs, ftype, ts = self.cap.read()
                    if ret:
                        # In MVO mode, frame should be None or empty
                        if frame is not None:
                            self.assertEqual(frame.size, 0, "Frame should be empty in MVO mode")
                        
                        # Motion vectors should be available
                        self.assertIsNotNone(mvs, "Motion vectors should be available")
                
                # Clean up
                if os.path.exists(test_video):
                    os.remove(test_video)
            else:
                self.skipTest("Could not create test video")
                
        except (subprocess.TimeoutExpired, FileNotFoundError, ImportError):
            self.skipTest("ffmpeg not available for creating test video")

if __name__ == '__main__':
    print("Running basic MVO mode tests...")
    print("These tests don't require external video files or RTSP servers.")
    print()
    
    unittest.main(verbosity=2)
