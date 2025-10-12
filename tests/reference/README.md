# Reference Test Data

This directory contains reference test data for validating mv-extractor output.

## Structure

- `h264/` - H.264 test video reference data
- `mpeg4_part2/` - MPEG-4 Part 2 test video reference data  
- `rtsp/` - RTSP stream reference data

## Data Format

Each subdirectory contains:
- `motion_vectors/` - Motion vector .npy files
- `frames/` - Frame image .jpg files
- `frame_types.txt` - Frame type information
- `timestamps.txt` - Timestamp information

## Usage

Reference data is used by the test suite to verify that:
1. Motion vector extraction produces consistent results
2. Frame decoding works correctly
3. Timestamps are accurate
4. Frame types are correctly identified

The test suite compares current output against this reference data to ensure no regressions.
