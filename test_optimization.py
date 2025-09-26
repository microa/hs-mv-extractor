#!/usr/bin/env python3
"""
Test script to demonstrate the performance improvements of the optimized mv-extractor.
This script compares the performance between standard extraction and optimized motion-vector-only extraction.
"""

import time
import numpy as np
from mvextractor.videocap import VideoCap

def test_standard_extraction(video_path, num_frames=100):
    """Test standard extraction (with frame decoding)"""
    print("Testing standard extraction...")
    
    cap = VideoCap()
    if not cap.open(video_path):
        print(f"Failed to open {video_path}")
        return None
    
    start_time = time.time()
    frame_count = 0
    
    while frame_count < num_frames:
        ret, frame, motion_vectors, frame_type, timestamp = cap.read()
        if not ret:
            break
        frame_count += 1
    
    end_time = time.time()
    cap.release()
    
    elapsed = end_time - start_time
    fps = frame_count / elapsed if elapsed > 0 else 0
    
    print(f"Standard extraction: {frame_count} frames in {elapsed:.2f}s ({fps:.2f} FPS)")
    return elapsed, fps

def test_optimized_extraction(video_path, num_frames=100):
    """Test optimized extraction (motion vectors only)"""
    print("Testing optimized extraction...")
    
    cap = VideoCap()
    cap.setExtractionMode(extract_frames=False, lightweight_mode=True)
    
    if not cap.open(video_path):
        print(f"Failed to open {video_path}")
        return None
    
    start_time = time.time()
    frame_count = 0
    
    while frame_count < num_frames:
        ret, frame, motion_vectors, frame_type, timestamp = cap.readMotionVectorsOnly()
        if not ret:
            break
        frame_count += 1
    
    end_time = time.time()
    cap.release()
    
    elapsed = end_time - start_time
    fps = frame_count / elapsed if elapsed > 0 else 0
    
    print(f"Optimized extraction: {frame_count} frames in {elapsed:.2f}s ({fps:.2f} FPS)")
    return elapsed, fps

def main():
    video_path = "vid_h264.mp4"  # Use the test video
    
    print("=== Motion Vector Extractor Performance Test ===")
    print(f"Testing with video: {video_path}")
    print(f"Processing 100 frames for comparison")
    print()
    
    # Test standard extraction
    standard_result = test_standard_extraction(video_path, 100)
    print()
    
    # Test optimized extraction
    optimized_result = test_optimized_extraction(video_path, 100)
    print()
    
    # Compare results
    if standard_result and optimized_result:
        std_time, std_fps = standard_result
        opt_time, opt_fps = optimized_result
        
        speedup = std_time / opt_time if opt_time > 0 else 0
        fps_improvement = (opt_fps - std_fps) / std_fps * 100 if std_fps > 0 else 0
        
        print("=== Performance Comparison ===")
        print(f"Standard extraction:  {std_time:.2f}s ({std_fps:.2f} FPS)")
        print(f"Optimized extraction: {opt_time:.2f}s ({opt_fps:.2f} FPS)")
        print(f"Speed improvement:    {speedup:.2f}x faster")
        print(f"FPS improvement:      {fps_improvement:.1f}%")
        print()
        
        if speedup > 1.5:
            print("✅ Significant performance improvement achieved!")
        else:
            print("⚠️  Performance improvement is minimal")

if __name__ == "__main__":
    main()
