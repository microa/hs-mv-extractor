#!/usr/bin/env python3
"""
Basic usage example for hs-mv-extractor
Demonstrates how to extract motion vectors from a video

Performance: 13-15x faster than original implementation
- RAM processing: 13.2x speedup
- End-to-end: 15.0x speedup
- Memory usage: 50%+ reduction
- Storage: 43% reduction (motion vectors only)
"""

import os
import sys
import numpy as np

from mvextractor.videocap import VideoCap



def extract_motion_vectors(video_path, output_dir="output"):
    """
    Extract motion vectors from a video file
    
    Args:
        video_path (str): Path to the video file
        output_dir (str): Directory to save results
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize video capture
    cap = VideoCap()
    
    # Open video file
    if not cap.open(video_path):
        print(f"Error: Could not open video file {video_path}")
        return False
    
    print(f"Processing video: {video_path}")
    print(f"Output directory: {output_dir}")
    
    frame_count = 0
    motion_vectors_dir = os.path.join(output_dir, "motion_vectors")
    frames_dir = os.path.join(output_dir, "frames")
    
    os.makedirs(motion_vectors_dir, exist_ok=True)
    os.makedirs(frames_dir, exist_ok=True)
    
    # Extract motion vectors
    while True:
        ret, frame, motion_vectors, frame_type = cap.read()
        
        if not ret:
            break
        
        # Save motion vectors
        if motion_vectors is not None and len(motion_vectors) > 0:
            mv_path = os.path.join(motion_vectors_dir, f"frame_{frame_count:06d}.npy")
            np.save(mv_path, motion_vectors)
        
        # Save frame (if available)
        if frame is not None and hasattr(frame, 'shape') and len(frame.shape) > 0:
            try:
                import cv2
                frame_path = os.path.join(frames_dir, f"frame_{frame_count:06d}.jpg")
                cv2.imwrite(frame_path, frame)
            except ImportError:
                pass  # OpenCV not available
        
        print(f"Frame {frame_count}: Type={frame_type}, MVs={len(motion_vectors) if motion_vectors is not None else 0}")
        frame_count += 1
    
    cap.release()
    print(f"\nExtraction complete! Processed {frame_count} frames")
    print(f"Motion vectors saved to: {motion_vectors_dir}")
    print(f"Frames saved to: {frames_dir}")
    
    return True

def extract_motion_vectors_only(video_path, output_dir="output"):
    """
    Extract only motion vectors (high-speed mode)
    
    Args:
        video_path (str): Path to the video file
        output_dir (str): Directory to save results
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize video capture
    cap = VideoCap()
    
    # Enable motion vectors only mode for maximum performance
    try:
        cap.set_motion_vectors_only(True)
        print("Motion vectors only mode enabled")
    except AttributeError:
        print("Motion vectors only mode not available")
    
    # Open video file
    if not cap.open(video_path):
        print(f"Error: Could not open video file {video_path}")
        return False
    
    print(f"Processing video (MVO mode): {video_path}")
    print(f"Output directory: {output_dir}")
    
    frame_count = 0
    motion_vectors_dir = os.path.join(output_dir, "motion_vectors")
    os.makedirs(motion_vectors_dir, exist_ok=True)
    
    # Extract motion vectors
    while True:
        ret, frame, motion_vectors, frame_type = cap.read()
        
        if not ret:
            break
        
        # Save motion vectors
        if motion_vectors is not None and len(motion_vectors) > 0:
            mv_path = os.path.join(motion_vectors_dir, f"frame_{frame_count:06d}.npy")
            np.save(mv_path, motion_vectors)
        
        print(f"Frame {frame_count}: Type={frame_type}, MVs={len(motion_vectors) if motion_vectors is not None else 0}")
        frame_count += 1
    
    cap.release()
    print(f"\nExtraction complete! Processed {frame_count} frames")
    print(f"Motion vectors saved to: {motion_vectors_dir}")
    
    return True

if __name__ == "__main__":
    # Example usage
    video_path = "vid_h264.mp4"  # Adjust path as needed
    
    if not os.path.exists(video_path):
        print(f"Video file not found: {video_path}")
        print("Please ensure a test video is available in the data/ directory")
        sys.exit(1)
    
    print("=== Basic Motion Vector Extraction ===")
    extract_motion_vectors(video_path, "output_basic")
    
    print("\n=== High-Speed Motion Vector Extraction ===")
    extract_motion_vectors_only(video_path, "output_mvo")