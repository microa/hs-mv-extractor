#!/usr/bin/env python3
import os, sys, time, json, glob, shutil, importlib
import numpy as np
import cv2

# === Local extension source path (ensure this contains mvextractor src directory) ===
# Using relative paths for better portability
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
LOCAL_SRC = os.path.join(project_root, 'src')

WARMUP_FRAMES = 3  # Remove cold start frames from RAM-only statistics

def _draw_motion_vectors(frame, motion_vectors):
    """Draw motion vectors on frame (original LukasBommes/mv-extractor functionality)"""
    if len(motion_vectors) > 0:
        num_mvs = np.shape(motion_vectors)[0]
        shift = 2
        factor = (1 << shift)
        for mv in np.split(motion_vectors, num_mvs):
            start_pt = (int((mv[0, 5] + mv[0, 7] / mv[0, 9]) * factor + 0.5), int((mv[0, 6] + mv[0, 8] / mv[0, 9]) * factor + 0.5))
            end_pt = (mv[0, 5] * factor, mv[0, 6] * factor)
            cv2.arrowedLine(frame, start_pt, end_pt, (0, 0, 255), 1, cv2.LINE_AA, shift, 0.1)
    return frame

def _ensure_dir_clean(d):
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d, exist_ok=True)

def _zap_mv_modules():
    """Clean mvextractor related items from sys.modules to ensure next import uses new backend."""
    for k in list(sys.modules.keys()):
        if k == 'mvextractor' or k.startswith('mvextractor.'):
            del sys.modules[k]
    importlib.invalidate_caches()

def _import_videocap(force_local: bool):
    """
    force_local=True  -> A: Force local extension (put LOCAL_SRC at front of sys.path)
    force_local=False -> B: Force PyPI/system installed package (remove LOCAL_SRC from sys.path)
    """
    # Prepare sys.path
    abs_local = os.path.abspath(LOCAL_SRC)
    sys.path = [p for p in sys.path if os.path.abspath(p) != abs_local]
    if force_local:
        sys.path.insert(0, abs_local)

    _zap_mv_modules()  # Clean loaded modules before importing
    from mvextractor.videocap import VideoCap
    import mvextractor as _mv
    return VideoCap, _mv.__file__

def _maybe_set_mvo(cap, on: bool) -> bool:
    """Try to enable/disable MVO-only; returns whether the API exists."""
    for name in ("set_motion_vectors_only", "setMotionVectorsOnly"):
        fn = getattr(cap, name, None)
        if callable(fn):
            fn(bool(on))
            return True
    return False

def _bench_mem_only(video_path, n_frames, want_mvo: bool, force_local: bool):
    """Test memory-only phase: includes motion vector visualization but doesn't save to files."""
    VideoCap, impl_path = _import_videocap(force_local)
    cap = VideoCap()
    if not cap.open(video_path):
        return {"ok": False, "reason": "open_failed", "impl": impl_path}

    api_present = _maybe_set_mvo(cap, want_mvo)

    # Skip WARMUP frames to match E2E test
    for _ in range(WARMUP_FRAMES):
        ret, _, _, _, _ = cap.read()
        if not ret:
            break

    frames = 0
    total_mvs = 0
    nonempty = 0
    t0 = time.perf_counter()  # Start timing

    while frames < n_frames:
        ret, frame, mvs, ftype, ts = cap.read()
        if not ret:
            break
        
        # Process motion vector visualization in memory (included in timing)
        # Note: A mode (MVO) doesn't execute visualization, B mode (Full) executes visualization
        if not want_mvo and getattr(frame, "size", 0) > 0:
            frame_with_vectors = _draw_motion_vectors(frame, mvs)
        
        if getattr(frame, "size", 0) > 0:
            nonempty += 1
        total_mvs += int(np.shape(mvs)[0])
        frames += 1

    t1 = time.perf_counter()  # End timing

    cap.release()
    counted = frames
    nonempty_ratio = (nonempty / counted) if counted else 0.0
    mvo_effective = bool(api_present and want_mvo and nonempty_ratio < 0.1)

    return {
        "ok": True,
        "impl": impl_path,
        "api_present": api_present,
        "mvo_requested": want_mvo,
        "mvo_effective": mvo_effective,
        "counted_frames": counted,
        "ram_only_time_sec": float(t1 - t0),
        "ram_avg_dt_sec": float((t1 - t0) / counted) if counted else None,
        "ram_median_dt_sec": None,  # Overall timing, no median
        "ram_nonempty_frame_ratio": nonempty_ratio,
        "ram_avg_mvs_per_frame": (total_mvs / counted) if counted else 0.0,
    }

def _bench_e2e_with_dump(video_path, n_frames, out_dir, want_mvo: bool, force_local: bool):
    """
    End-to-end: from directory creation + open to all files written + release.
    - A (want_mvo=True, force_local=True): Only write MV (.npy) -> out_dir/MotionVectors
    - B (want_mvo=False, force_local=False): Write MV (.npy) + write frames (.jpg) -> out_dir/MotionVectors, out_dir/Frames
    """
    _ensure_dir_clean(out_dir)
    mv_dir = os.path.join(out_dir, "MotionVectors")
    os.makedirs(mv_dir, exist_ok=True)

    write_frames = not want_mvo
    frames_dir = os.path.join(out_dir, "Frames")
    cv2 = None
    if write_frames:
        try:
            import cv2 as _cv2
            cv2 = _cv2
            os.makedirs(frames_dir, exist_ok=True)
        except Exception:
            write_frames = False  # Only write MV when cv2 is not available

    # Save frame types and timestamps (full mode)
    frame_types = []
    timestamps = []

    VideoCap, impl_path = _import_videocap(force_local)
    cap = VideoCap()
    if not cap.open(video_path):
        return {"ok": False, "reason": "open_failed", "impl": impl_path}

    api_present = _maybe_set_mvo(cap, want_mvo)

    # Skip WARMUP frames to match RAM test
    for _ in range(WARMUP_FRAMES):
        ret, _, _, _, _ = cap.read()
        if not ret:
            break

    frames = 0
    mv_bytes = 0
    frame_bytes = 0
    t0 = time.perf_counter()  # Start timing

    while frames < n_frames:
        ret, frame, mvs, ftype, ts = cap.read()
        if not ret:
            break

        # Write MV (one file per frame, original format)
        mv_path = os.path.join(mv_dir, f"{frames:06d}.npy")
        np.save(mv_path, mvs, allow_pickle=False)
        try:
            mv_bytes += os.path.getsize(mv_path)
        except FileNotFoundError:
            pass

        # Write frames (only B) - includes motion vector visualization
        if write_frames and getattr(frame, "size", 0) > 0:
            # Draw motion vectors on frame (original functionality)
            frame_with_vectors = _draw_motion_vectors(frame, mvs)
            jpg_path = os.path.join(frames_dir, f"{frames:06d}.jpg")
            cv2.imwrite(jpg_path, frame_with_vectors, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            try:
                frame_bytes += os.path.getsize(jpg_path)
            except FileNotFoundError:
                pass

        # Save frame types and timestamps (full mode)
        if not want_mvo:  # Only save in full mode
            frame_types.append(ftype)
            timestamps.append(ts)

        frames += 1

    cap.release()
    t1 = time.perf_counter()

    # Save frame types and timestamps files (full mode)
    if not want_mvo and frame_types and timestamps:
        frame_types_path = os.path.join(out_dir, "frame_types.txt")
        timestamps_path = os.path.join(out_dir, "timestamps.txt")
        
        with open(frame_types_path, 'w') as f:
            for ftype in frame_types:
                f.write(f"{ftype}\n")
        
        with open(timestamps_path, 'w') as f:
            for ts in timestamps:
                f.write(f"{ts:.6f}\n")

    written_mv = len(glob.glob(os.path.join(mv_dir, "*.npy")))
    written_frames = len(glob.glob(os.path.join(frames_dir, "*.jpg"))) if os.path.isdir(frames_dir) else 0

    return {
        "ok": True,
        "impl": impl_path,
        "api_present": api_present,
        "mvo_requested": want_mvo,
        "e2e_time_sec": float(t1 - t0),
        "frames_processed": frames,
        "mv_files_written": written_mv,
        "frame_files_written": written_frames,
        "e2e_mv_bytes": int(mv_bytes),
        "e2e_frame_bytes": int(frame_bytes),
    }

def real_test(input_video: str, output_dir: str, test_frames: int):
    """
    MVO = Your local extension (forced import from LOCAL_SRC) + MVO-only
    FULL = PyPI/system installed version (remove LOCAL_SRC) + Full decode (write frames)
    """
    # --- MVO: Local extension + MVO-only ---
    mvo_mem = _bench_mem_only(input_video, test_frames, want_mvo=True,  force_local=True)
    mvo_e2e = _bench_e2e_with_dump(
        input_video, test_frames, os.path.join(output_dir, "MVO"),
        want_mvo=True, force_local=True
    )

    # --- FULL: PyPI version + Full decode ---
    full_mem = _bench_mem_only(input_video, test_frames, want_mvo=False, force_local=False)
    full_e2e = _bench_e2e_with_dump(
        input_video, test_frames, os.path.join(output_dir, "FULL"),
        want_mvo=False, force_local=False
    )

    report = {
        "video": input_video,
        "frames_target": test_frames,
        "MVO": {
            "impl": mvo_mem.get("impl"),
            "api_present": mvo_mem.get("api_present"),
            "mvo_effective": mvo_mem.get("mvo_effective"),
            "ram_only_time_sec": mvo_mem.get("ram_only_time_sec"),
            "ram_avg_dt_sec": mvo_mem.get("ram_avg_dt_sec"),
            "ram_median_dt_sec": mvo_mem.get("ram_median_dt_sec"),
            "ram_nonempty_frame_ratio": mvo_mem.get("ram_nonempty_frame_ratio"),
            "ram_avg_mvs_per_frame": mvo_mem.get("ram_avg_mvs_per_frame"),
            "e2e_time_sec": mvo_e2e.get("e2e_time_sec"),
            "mv_files_written": mvo_e2e.get("mv_files_written"),
            "frame_files_written": mvo_e2e.get("frame_files_written"),
            "e2e_mv_bytes": mvo_e2e.get("e2e_mv_bytes"),
            "e2e_frame_bytes": mvo_e2e.get("e2e_frame_bytes"),
        },
        "FULL": {
            "impl": full_mem.get("impl"),
            "api_present": full_mem.get("api_present"),
            "mvo_effective": full_mem.get("mvo_effective"),
            "ram_only_time_sec": full_mem.get("ram_only_time_sec"),
            "ram_avg_dt_sec": full_mem.get("ram_avg_dt_sec"),
            "ram_median_dt_sec": full_mem.get("ram_median_dt_sec"),
            "ram_nonempty_frame_ratio": full_mem.get("ram_nonempty_frame_ratio"),
            "ram_avg_mvs_per_frame": full_mem.get("ram_avg_mvs_per_frame"),
            "e2e_time_sec": full_e2e.get("e2e_time_sec"),
            "mv_files_written": full_e2e.get("mv_files_written"),
            "frame_files_written": full_e2e.get("frame_files_written"),
            "e2e_mv_bytes": full_e2e.get("e2e_mv_bytes"),
            "e2e_frame_bytes": full_e2e.get("e2e_frame_bytes"),
        },
        "speedup_ram_only_x": (
            (full_mem.get("ram_only_time_sec") / mvo_mem.get("ram_only_time_sec"))
            if (mvo_mem.get("ok") and full_mem.get("ok") and mvo_mem.get("ram_only_time_sec") and full_mem.get("ram_only_time_sec"))
            else None
        ),
        "speedup_e2e_x": (
            (full_e2e.get("e2e_time_sec") / mvo_e2e.get("e2e_time_sec"))
            if (mvo_e2e.get("ok") and full_e2e.get("ok") and mvo_e2e.get("e2e_time_sec") and full_e2e.get("e2e_time_sec"))
            else None
        ),
    }

    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    input_video = "/home/mbin/hsextract-mvs/data/vid_mpeg4_part2.mp4"
    output_dir = "/home/mbin/hsextract-mvs/data"
    real_test(input_video, output_dir, 300)
