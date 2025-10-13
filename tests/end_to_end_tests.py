import os
import time
import tempfile
import unittest
import subprocess

import cv2
import numpy as np


PROJECT_ROOT = os.getenv("PROJECT_ROOT", "")


class TestEndToEnd(unittest.TestCase):

    def motions_vectors_valid(self, outdir, refdir):
        equal = []
        num_mvs = len(os.listdir(os.path.join(refdir, "motion_vectors")))
        for i in range(num_mvs):
            mvs = np.load(os.path.join(outdir, "motion_vectors", f"mvs-{i}.npy"))
            mvs_ref = np.load(os.path.join(refdir, "motion_vectors", f"mvs-{i}.npy"))
            equal.append(np.all(mvs == mvs_ref))
        return all(equal)


    def frame_types_valid(self, outdir, refdir):
        with open(os.path.join(outdir, "frame_types.txt"), "r") as file:
            frame_types = [line.strip() for line in file]
        with open(os.path.join(refdir, "frame_types.txt"), "r") as file:
            frame_types_ref = [line.strip() for line in file]
        return frame_types == frame_types_ref


    def frames_valid(self, outdir, refdir):
        equal = []
        num_frames = len(os.listdir(os.path.join(refdir, "frames")))
        for i in range(num_frames):
            frame = cv2.imread(os.path.join(outdir, "frames", f"frame-{i}.jpg"))
            frame_ref = cv2.imread(os.path.join(refdir, "frames", f"frame-{i}.jpg"))
            equal.append(np.all(frame == frame_ref))
        return all(equal)


    def test_end_to_end_h264(self):
        with tempfile.TemporaryDirectory() as outdir:
            print("Running extraction for H.264")
            subprocess.run(f"extract_mvs {os.path.join(PROJECT_ROOT, 'vid_h264.mp4')} --dump {outdir}", shell=True, check=True)
            refdir = os.path.join(PROJECT_ROOT, "tests/reference/h264")

            self.assertTrue(self.motions_vectors_valid(outdir, refdir), msg="motion vectors are invalid")
            self.assertTrue(self.frame_types_valid(outdir, refdir), msg="frame types are invalid")
            self.assertTrue(self.frames_valid(outdir, refdir), msg="frames are invalid")


    def test_end_to_end_mpeg4_part2(self):
        with tempfile.TemporaryDirectory() as outdir:
            print("Running extraction for MPEG-4 Part 2")
            subprocess.run(f"extract_mvs {os.path.join(PROJECT_ROOT, 'vid_mpeg4_part2.mp4')} --dump {outdir}", shell=True, check=True)
            refdir = os.path.join(PROJECT_ROOT, "tests/reference/mpeg4_part2")

            self.assertTrue(self.motions_vectors_valid(outdir, refdir), msg="motion vectors are invalid")
            self.assertTrue(self.frame_types_valid(outdir, refdir), msg="frame types are invalid")
            self.assertTrue(self.frames_valid(outdir, refdir), msg="frames are invalid")


    def test_end_to_end_rtsp(self):
        with tempfile.TemporaryDirectory() as outdir:
            print("Setting up end to end test for RTSP")
            media_server_binary = os.path.abspath(os.path.join(PROJECT_ROOT, "tests/tools/live555MediaServer"))
            rtsp_server = subprocess.Popen(media_server_binary, cwd=PROJECT_ROOT if PROJECT_ROOT else None)
            try:
                time.sleep(1)
                print("Running extraction for RTSP stream")
                rtsp_url = "rtsp://localhost:554/vid_h264.264"
                subprocess.run(f"extract_mvs {rtsp_url} --dump {outdir}", shell=True, check=True)
                refdir = os.path.join(PROJECT_ROOT, "tests/reference/rtsp")

                self.assertTrue(self.motions_vectors_valid(outdir, refdir), msg="motion vectors are invalid")
                self.assertTrue(self.frame_types_valid(outdir, refdir), msg="frame types are invalid")
                self.assertTrue(self.frames_valid(outdir, refdir), msg="frames are invalid")
            finally:
                rtsp_server.terminate()


class TestMVOEndToEnd(unittest.TestCase):

    def setUp(self):
        from mvextractor.videocap import VideoCap
        self.VideoCap = VideoCap
        self.cap = VideoCap() if VideoCap else None
        self.test_video_h264 = os.path.join(PROJECT_ROOT, 'vid_h264.mp4')
        self.test_video_mpeg4 = os.path.join(PROJECT_ROOT, 'vid_mpeg4_part2.mp4')
    
    def tearDown(self):
        self.cap.release()
    
    def test_mvo_mode_h264(self):
        self.assertTrue(self.cap.open(self.test_video_h264), "Failed to open H.264 test video")
        
        self.cap.set_motion_vectors_only(True)
        
        frame_count = 0
        motion_vectors_count = 0
        
        # Read first 10 frames
        for i in range(10):
            ret, frame, mvs, ftype = self.cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # In MVO mode, frame should be None or empty
            if frame is not None:
                self.assertEqual(frame.size, 0, "Frame should be empty in MVO mode")
            
            # Motion vectors should be available
            if mvs is not None and len(mvs) > 0:
                motion_vectors_count += 1
        
        self.assertGreater(frame_count, 0, "Should read at least one frame")
        self.assertGreater(motion_vectors_count, 0, "Should extract motion vectors")
    
    def test_mvo_mode_mpeg4(self):
        """Test MVO mode with MPEG-4 Part 2 video"""
        if self.cap is None:
            self.skipTest("VideoCap not available")
        if not os.path.exists(self.test_video_mpeg4):
            self.skipTest("MPEG-4 test video not found")
        
        ret = self.cap.open(self.test_video_mpeg4)
        self.assertTrue(ret, "Failed to open MPEG-4 test video")
        
        # Enable MVO mode
        if hasattr(self.cap, 'set_motion_vectors_only'):
            self.cap.set_motion_vectors_only(True)
        
        frame_count = 0
        motion_vectors_count = 0
        
        # Read first 10 frames
        for i in range(10):
            ret, frame, mvs, ftype = self.cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # In MVO mode, frame should be None or empty
            if frame is not None:
                self.assertEqual(frame.size, 0, "Frame should be empty in MVO mode")
            
            # Motion vectors should be available
            if mvs is not None and len(mvs) > 0:
                motion_vectors_count += 1
        
        self.assertGreater(frame_count, 0, "Should read at least one frame")
        self.assertGreater(motion_vectors_count, 0, "Should extract motion vectors")
    
    def test_mvo_vs_full_mode_comparison(self):
        """Test that MVO mode produces no frames while full mode produces frames"""
        if self.cap is None:
            self.skipTest("VideoCap not available")
        if not os.path.exists(self.test_video_h264):
            self.skipTest("H.264 test video not found")
        
        # Test full mode
        ret = self.cap.open(self.test_video_h264)
        self.assertTrue(ret, "Failed to open test video")
        
        # Disable MVO mode (full mode)
        if hasattr(self.cap, 'set_motion_vectors_only'):
            self.cap.set_motion_vectors_only(False)
        
        ret, frame, mvs, ftype = self.cap.read()
        self.assertTrue(ret, "Should read frame successfully")
        self.assertIsNotNone(frame, "Frame should not be None in full mode")
        self.assertGreater(frame.size, 0, "Frame should have content in full mode")
        
        self.cap.release()
        
        # Test MVO mode
        if self.VideoCap is None:
            self.skipTest("VideoCap not available")
        self.cap = self.VideoCap()
        ret = self.cap.open(self.test_video_h264)
        self.assertTrue(ret, "Failed to open test video")
        
        # Enable MVO mode
        if hasattr(self.cap, 'set_motion_vectors_only'):
            self.cap.set_motion_vectors_only(True)
        
        ret, frame, mvs, ftype = self.cap.read()
        self.assertTrue(ret, "Should read frame successfully")
        # Frame should be None or empty in MVO mode
        if frame is not None:
            self.assertEqual(frame.size, 0, "Frame should be empty in MVO mode")


if __name__ == '__main__':
    unittest.main()
            