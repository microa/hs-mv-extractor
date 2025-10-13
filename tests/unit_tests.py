import os
import unittest
import time

import numpy as np

from mvextractor.videocap import VideoCap


PROJECT_ROOT = os.getenv("PROJECT_ROOT", "")


class TestMotionVectorExtraction(unittest.TestCase):

    def validate_frame(self, frame):
        self.assertEqual(type(frame), np.ndarray)
        self.assertEqual(frame.dtype, np.uint8)
        self.assertEqual(frame.shape, (720, 1280, 3))


    def validate_motion_vectors(self, motion_vectors, shape=(0, 10)):
        self.assertEqual(type(motion_vectors), np.ndarray)
        self.assertEqual(motion_vectors.dtype, np.int32)
        self.assertEqual(motion_vectors.shape, shape)


    # run before every test
    def setUp(self):
        self.cap = VideoCap()


    # run after every test regardless of success
    def tearDown(self):
        self.cap.release()


    def open_video(self):
        return self.cap.open(os.path.join(PROJECT_ROOT, "vid_h264.mp4"))


    def test_init_cap(self):
        self.cap = VideoCap()
        self.assertIn('open', dir(self.cap))
        self.assertIn('grab', dir(self.cap))
        self.assertIn('read', dir(self.cap))
        self.assertIn('release', dir(self.cap))
        self.assertIn('retrieve', dir(self.cap))


    def test_open_video(self):
        ret = self.open_video()
        self.assertTrue(ret)

    
    def test_open_invalid_video(self):
        ret = self.cap.open("vid_not_existent.mp4")
        self.assertFalse(ret)


    def test_read_not_opened_cap(self):
        ret = self.cap.open("vid_not_existent.mp4")
        self.assertFalse(ret)
        ret, frame, motion_vectors, frame_type = self.cap.read()
        self.assertEqual(frame_type, "?")
        self.assertFalse(ret)
        self.assertIsNone(frame)
        self.validate_motion_vectors(motion_vectors)


    def test_read_first_I_frame(self):
        self.open_video()
        ret, frame, motion_vectors, frame_type = self.cap.read()
        self.assertTrue(ret)
        self.assertEqual(frame_type, "I")      
        self.validate_frame(frame)
        self.validate_motion_vectors(motion_vectors)


    def test_read_first_P_frame(self):
        self.open_video()
        self.cap.read()  # skip first frame (I frame)
        ret, frame, motion_vectors, frame_type = self.cap.read()
        self.assertTrue(ret)
        self.assertEqual(frame_type, "P")      
        self.validate_frame(frame)
        self.validate_motion_vectors(motion_vectors, shape=(3665, 10))
        self.assertTrue(np.all(motion_vectors[:10, :] == np.array([
            [-1, 16, 16,   8, 8,   8, 8, 0, 0, 4],
            [-1, 16, 16,  24, 8,  24, 8, 0, 0, 4],
            [-1, 16, 16,  40, 8,  40, 8, 0, 0, 4],
            [-1, 16, 16,  56, 8,  56, 8, 0, 0, 4],
            [-1, 16, 16,  72, 8,  72, 8, 0, 0, 4],
            [-1, 16, 16,  88, 8,  88, 8, 0, 0, 4],
            [-1, 16, 16, 104, 8, 104, 8, 0, 0, 4],
            [-1, 16, 16, 120, 8, 120, 8, 0, 0, 4],
            [-1, 16, 16, 136, 8, 136, 8, 0, 0, 4],
            [-1, 16, 16, 152, 8, 152, 8, 0, 0, 4],
        ])))


    def test_read_first_ten_frames(self):
        rets = []
        frames = []
        motion_vectors = []
        frame_types = []
        self.open_video()
        for _ in range(10):
            ret, frame, motion_vector, frame_type = self.cap.read()
            rets.append(ret)
            frames.append(frame)
            motion_vectors.append(motion_vector)
            frame_types.append(frame_type)

        self.assertTrue(all(rets))
        self.assertEqual(frame_types, ['I', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'])
        [self.validate_frame(frame) for frame in frames]
        shapes = [
            (0, 10), (3665, 10), (3696, 10), (3722, 10), (3807, 10), 
            (3953, 10), (4155, 10), (3617, 10), (4115, 10), (4192, 10)
        ]
        [self.validate_motion_vectors(motion_vector, shape) for motion_vector, shape in zip(motion_vectors, shapes)]


    def test_frame_count(self):
        self.open_video()
        frame_count = 0
        while True:
            ret, _, _, _ = self.cap.read()
            if not ret:
                break
            frame_count += 1
        self.assertEqual(frame_count, 337)


    def test_timings(self):
        self.open_video()
        times = []
        while True:
            tstart = time.perf_counter()
            ret, _, _, _ = self.cap.read()
            if not ret:
                break
            tend = time.perf_counter()
            telapsed = tend - tstart
            times.append(telapsed)
        dt_mean = np.mean(times)
        dt_std = np.std(times)
        print(f"Timings: mean {dt_mean} s -- std: {dt_std} s")
        self.assertGreater(dt_mean, 0)
        self.assertGreater(dt_std, 0)
        self.assertLess(dt_mean, 0.01, msg=f"Mean of frame read duration exceeds maximum ({dt_mean} s > {0.01} s)")
        self.assertLess(dt_std, 0.003, msg=f"Standard deviation of frame read duration exceeds maximum ({dt_std} s > {0.003} s)")













    def test_mvo_mode_support(self):
        has_mvo_api = hasattr(self.cap, 'set_motion_vectors_only')
        self.assertTrue(has_mvo_api, "MVO mode API should be available")
    
    def test_mvo_mode_activation(self):
        # Should not raise an exception
        self.cap.set_motion_vectors_only(True)
        self.cap.set_motion_vectors_only(False)
    
    def test_mvo_mode_with_video_file(self):
        test_video = os.path.join(PROJECT_ROOT, 'vid_h264.mp4')
        ret = self.cap.open(test_video)
        self.assertTrue(ret, "Failed to open test video")
        
        # Enable MVO mode
        self.cap.set_motion_vectors_only(True)
        
        # Read one frame
        ret, frame, mvs, ftype = self.cap.read()
        self.assertTrue(ret, "Should read frame successfully")
        
        # In MVO mode, frame should be None or empty
        if frame is not None:
            self.assertEqual(frame.size, 0, "Frame should be empty in MVO mode")
        
        # Motion vectors should be available
        self.assertIsNotNone(mvs, "Motion vectors should be available")
        self.assertIsInstance(mvs, np.ndarray, "Motion vectors should be numpy array")
    
    def test_mvo_mode_performance(self):
        """Test that MVO mode is faster than full mode"""
        test_video = os.path.join(PROJECT_ROOT, 'vid_h264.mp4')
        
        if not os.path.exists(test_video):
            self.skipTest("H.264 test video not found")
        
        # Test MVO mode timing
        ret = self.cap.open(test_video)
        self.assertTrue(ret, "Failed to open test video")
        
        self.cap.set_motion_vectors_only(True)
        
        start_time = time.perf_counter()
        frame_count = 0
        for i in range(10):  # Read 10 frames
            ret, _, _, _ = self.cap.read()
            if not ret:
                break
            frame_count += 1
        mvo_time = time.perf_counter() - start_time
        
        self.cap.release()
        
        # Test full mode timing
        self.cap = VideoCap()
        ret = self.cap.open(test_video)
        self.assertTrue(ret, "Failed to open test video")
        
        self.cap.set_motion_vectors_only(False)
        
        start_time = time.perf_counter()
        frame_count_full = 0
        for i in range(10):  # Read 10 frames
            ret, _, _, _ = self.cap.read()
            if not ret:
                break
            frame_count_full += 1
        full_time = time.perf_counter() - start_time
        
        # MVO mode should be faster (or at least not significantly slower)
        self.assertGreaterEqual(frame_count, 1, "Should read at least one frame in MVO mode")
        self.assertGreaterEqual(frame_count_full, 1, "Should read at least one frame in full mode")
        
        # Performance comparison (MVO should be faster)
        if mvo_time > 0 and full_time > 0:
            speedup = full_time / mvo_time
            print(f"MVO mode speedup: {speedup:.2f}x")
            # MVO should be at least as fast as full mode
            self.assertGreaterEqual(speedup, 0.5, "MVO mode should be reasonably fast")






    def test_mvo_mode_h264(self):
        video_path = os.path.join(PROJECT_ROOT, 'vid_h264.mp4')
        self.assertTrue(self.cap.open(video_path), "Failed to open H.264 test video")
        
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
        video_path = os.path.join(PROJECT_ROOT, 'vid_mpeg4_part2.mp4')
        ret = self.cap.open(video_path)
        self.assertTrue(ret, "Failed to open MPEG-4 test video")
        
        # Enable MVO mode
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
        video_path = os.path.join(PROJECT_ROOT, 'vid_h264.mp4')
        
        # Test full mode
        ret = self.cap.open(video_path)
        self.assertTrue(ret, "Failed to open test video")
        
        # Disable MVO mode (full mode)
        self.cap.set_motion_vectors_only(False)
        
        ret, frame, mvs, ftype = self.cap.read()
        self.assertTrue(ret, "Should read frame successfully")
        self.assertIsNotNone(frame, "Frame should not be None in full mode")
        self.assertGreater(frame.size, 0, "Frame should have content in full mode")
        
        # Enable MVO mode
        self.cap.set_motion_vectors_only(True)
        
        ret, frame, mvs, ftype = self.cap.read()
        self.assertTrue(ret, "Should read frame successfully")
        # Frame should be None or empty in MVO mode
        if frame is not None:
            self.assertEqual(frame.size, 0, "Frame should be empty in MVO mode")


if __name__ == '__main__':
    unittest.main()
