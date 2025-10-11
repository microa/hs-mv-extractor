#!/usr/bin/env python3
import os, sys, time, json, glob, shutil, importlib
import numpy as np

# === 你本地扩展源码路径（确保这里是含有 mvextractor 的 src 目录） ===
# 使用相对路径，更便携
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
LOCAL_SRC = os.path.join(project_root, 'src')

WARMUP_FRAMES = 3  # RAM-only 统计剔除冷启动

def _ensure_dir_clean(d):
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d, exist_ok=True)

def _zap_mv_modules():
    """从 sys.modules 清理 mvextractor 相关项，保证下一次 import 用新的后端。"""
    for k in list(sys.modules.keys()):
        if k == 'mvextractor' or k.startswith('mvextractor.'):
            del sys.modules[k]
    importlib.invalidate_caches()

def _import_videocap(force_local: bool):
    """
    force_local=True  -> A：强制本地扩展（把 LOCAL_SRC 放到 sys.path 最前）
    force_local=False -> B：强制 PyPI/系统安装的包（从 sys.path 移除 LOCAL_SRC）
    """
    # 准备 sys.path
    abs_local = os.path.abspath(LOCAL_SRC)
    sys.path = [p for p in sys.path if os.path.abspath(p) != abs_local]
    if force_local:
        sys.path.insert(0, abs_local)

    _zap_mv_modules()  # 清理已加载模块再导入
    from mvextractor.videocap import VideoCap
    import mvextractor as _mv
    return VideoCap, _mv.__file__

def _maybe_set_mvo(cap, on: bool) -> bool:
    """尝试启用/关闭 MVO-only；返回是否存在该 API。"""
    for name in ("set_motion_vectors_only", "setMotionVectorsOnly"):
        fn = getattr(cap, name, None)
        if callable(fn):
            fn(bool(on))
            return True
    return False

def _bench_mem_only(video_path, n_frames, want_mvo: bool, force_local: bool):
    """只测内存阶段：sum(read() 时长)，不落盘。"""
    VideoCap, impl_path = _import_videocap(force_local)
    cap = VideoCap()
    if not cap.open(video_path):
        return {"ok": False, "reason": "open_failed", "impl": impl_path}

    api_present = _maybe_set_mvo(cap, want_mvo)

    times, nonempty, frames, total_mvs = [], 0, 0, 0
    target = WARMUP_FRAMES + n_frames
    while frames < target:
        t0 = time.perf_counter()
        ret, frame, mvs, ftype, ts = cap.read()
        t1 = time.perf_counter()
        if not ret:
            break
        if frames >= WARMUP_FRAMES:
            times.append(t1 - t0)
            if getattr(frame, "size", 0) > 0:
                nonempty += 1
            total_mvs += int(np.shape(mvs)[0])
        frames += 1

    cap.release()
    counted = max(0, frames - WARMUP_FRAMES)
    nonempty_ratio = (nonempty / counted) if counted else 0.0
    mvo_effective = bool(api_present and want_mvo and nonempty_ratio < 0.1)

    return {
        "ok": True,
        "impl": impl_path,
        "api_present": api_present,
        "mvo_requested": want_mvo,
        "mvo_effective": mvo_effective,
        "counted_frames": counted,
        "ram_only_time_sec": float(sum(times)) if times else 0.0,
        "ram_avg_dt_sec": float(np.mean(times)) if times else None,
        "ram_median_dt_sec": float(np.median(times)) if times else None,
        "ram_nonempty_frame_ratio": nonempty_ratio,
        "ram_avg_mvs_per_frame": (total_mvs / counted) if counted else 0.0,
    }

def _bench_e2e_with_dump(video_path, n_frames, out_dir, want_mvo: bool, force_local: bool):
    """
    端到端：从建目录 + open 到全部写完 + release。
    - A (want_mvo=True, force_local=True)：只写 MV（.npy） -> out_dir/MotionVectors
    - B (want_mvo=False, force_local=False)：写 MV（.npy） + 写帧（.jpg） -> out_dir/MotionVectors, out_dir/Frames
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
            write_frames = False  # 没有 cv2 时仅写 MV

    VideoCap, impl_path = _import_videocap(force_local)
    t0 = time.perf_counter()

    cap = VideoCap()
    if not cap.open(video_path):
        return {"ok": False, "reason": "open_failed", "impl": impl_path}

    api_present = _maybe_set_mvo(cap, want_mvo)

    frames = 0
    mv_bytes = 0
    frame_bytes = 0

    while frames < n_frames:
        ret, frame, mvs, ftype, ts = cap.read()
        if not ret:
            break

        # 写 MV
        mv_path = os.path.join(mv_dir, f"{frames:06d}.npy")
        np.save(mv_path, mvs, allow_pickle=False)
        try:
            mv_bytes += os.path.getsize(mv_path)
        except FileNotFoundError:
            pass

        # 写帧（仅 B）
        if write_frames and getattr(frame, "size", 0) > 0:
            jpg_path = os.path.join(frames_dir, f"{frames:06d}.jpg")
            cv2.imwrite(jpg_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            try:
                frame_bytes += os.path.getsize(jpg_path)
            except FileNotFoundError:
                pass

        frames += 1

    cap.release()
    t1 = time.perf_counter()

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
    A = 你的本地扩展（强制从 LOCAL_SRC 导入）+ MVO-only
    B = PyPI/系统安装版（移除 LOCAL_SRC）+ Full decode（写帧）
    """
    # --- A: 本地扩展 + MVO-only ---
    a_mem = _bench_mem_only(input_video, test_frames, want_mvo=True,  force_local=True)
    a_e2e = _bench_e2e_with_dump(
        input_video, test_frames, os.path.join(output_dir, "A_mvo_only"),
        want_mvo=True, force_local=True
    )

    # --- B: PyPI 版 + Full decode ---
    b_mem = _bench_mem_only(input_video, test_frames, want_mvo=False, force_local=False)
    b_e2e = _bench_e2e_with_dump(
        input_video, test_frames, os.path.join(output_dir, "B_full_decode"),
        want_mvo=False, force_local=False
    )

    report = {
        "video": input_video,
        "frames_target": test_frames,
        "A_mvo_only": {
            "impl": a_mem.get("impl"),
            "api_present": a_mem.get("api_present"),
            "mvo_effective": a_mem.get("mvo_effective"),
            "ram_only_time_sec": a_mem.get("ram_only_time_sec"),
            "ram_avg_dt_sec": a_mem.get("ram_avg_dt_sec"),
            "ram_median_dt_sec": a_mem.get("ram_median_dt_sec"),
            "ram_nonempty_frame_ratio": a_mem.get("ram_nonempty_frame_ratio"),
            "ram_avg_mvs_per_frame": a_mem.get("ram_avg_mvs_per_frame"),
            "e2e_time_sec": a_e2e.get("e2e_time_sec"),
            "mv_files_written": a_e2e.get("mv_files_written"),
            "frame_files_written": a_e2e.get("frame_files_written"),
            "e2e_mv_bytes": a_e2e.get("e2e_mv_bytes"),
            "e2e_frame_bytes": a_e2e.get("e2e_frame_bytes"),
        },
        "B_full_decode": {
            "impl": b_mem.get("impl"),
            "api_present": b_mem.get("api_present"),
            "mvo_effective": b_mem.get("mvo_effective"),
            "ram_only_time_sec": b_mem.get("ram_only_time_sec"),
            "ram_avg_dt_sec": b_mem.get("ram_avg_dt_sec"),
            "ram_median_dt_sec": b_mem.get("ram_median_dt_sec"),
            "ram_nonempty_frame_ratio": b_mem.get("ram_nonempty_frame_ratio"),
            "ram_avg_mvs_per_frame": b_mem.get("ram_avg_mvs_per_frame"),
            "e2e_time_sec": b_e2e.get("e2e_time_sec"),
            "mv_files_written": b_e2e.get("mv_files_written"),
            "frame_files_written": b_e2e.get("frame_files_written"),
            "e2e_mv_bytes": b_e2e.get("e2e_mv_bytes"),
            "e2e_frame_bytes": b_e2e.get("e2e_frame_bytes"),
        },
        "speedup_ram_only_x": (
            (b_mem.get("ram_only_time_sec") / a_mem.get("ram_only_time_sec"))
            if (a_mem.get("ok") and b_mem.get("ok") and a_mem.get("ram_only_time_sec") and b_mem.get("ram_only_time_sec"))
            else None
        ),
        "speedup_e2e_x": (
            (b_e2e.get("e2e_time_sec") / a_e2e.get("e2e_time_sec"))
            if (a_e2e.get("ok") and b_e2e.get("ok") and a_e2e.get("e2e_time_sec") and b_e2e.get("e2e_time_sec"))
            else None
        ),
    }

    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    input_video = "/home/mbin/hsextract-mvs/data/vid_h264.mp4"
    output_dir = "/home/mbin/hsextract-mvs/data"
    real_test(input_video, output_dir, 300)
