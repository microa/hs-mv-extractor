#!/usr/bin/env python3
import os, sys, time, json, glob, shutil, importlib
import numpy as np
import cv2

# === 你本地扩展源码路径（确保这里是含有 mvextractor 的 src 目录） ===
# 使用相对路径，更便携
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
LOCAL_SRC = os.path.join(project_root, 'src')

WARMUP_FRAMES = 3  # RAM-only 统计剔除冷启动

def _draw_motion_vectors(frame, motion_vectors):
    """在帧上绘制运动向量（原版 LukasBommes/mv-extractor 功能）"""
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
    """只测内存阶段：包含运动向量可视化，但不保存到文件。"""
    VideoCap, impl_path = _import_videocap(force_local)
    cap = VideoCap()
    if not cap.open(video_path):
        return {"ok": False, "reason": "open_failed", "impl": impl_path}

    api_present = _maybe_set_mvo(cap, want_mvo)

    # 跳过WARMUP帧，与E2E测试保持一致
    for _ in range(WARMUP_FRAMES):
        ret, _, _, _, _ = cap.read()
        if not ret:
            break

    frames = 0
    total_mvs = 0
    nonempty = 0
    t0 = time.perf_counter()  # 开始计时

    while frames < n_frames:
        ret, frame, mvs, ftype, ts = cap.read()
        if not ret:
            break
        
        # 在内存中处理运动向量可视化（包含在计时内）
        # 注意：A模式（MVO）不执行可视化，B模式（Full）执行可视化
        if not want_mvo and getattr(frame, "size", 0) > 0:
            frame_with_vectors = _draw_motion_vectors(frame, mvs)
        
        if getattr(frame, "size", 0) > 0:
            nonempty += 1
        total_mvs += int(np.shape(mvs)[0])
        frames += 1

    t1 = time.perf_counter()  # 结束计时

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
        "ram_median_dt_sec": None,  # 整体计时，无中位数
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

    # 保存帧类型和时间戳（完整模式）
    frame_types = []
    timestamps = []

    VideoCap, impl_path = _import_videocap(force_local)
    cap = VideoCap()
    if not cap.open(video_path):
        return {"ok": False, "reason": "open_failed", "impl": impl_path}

    api_present = _maybe_set_mvo(cap, want_mvo)

    # 跳过WARMUP帧，与RAM测试保持一致
    for _ in range(WARMUP_FRAMES):
        ret, _, _, _, _ = cap.read()
        if not ret:
            break

    frames = 0
    mv_bytes = 0
    frame_bytes = 0
    t0 = time.perf_counter()  # 开始计时

    while frames < n_frames:
        ret, frame, mvs, ftype, ts = cap.read()
        if not ret:
            break

        # 写 MV（每帧一个文件，原版格式）
        mv_path = os.path.join(mv_dir, f"{frames:06d}.npy")
        np.save(mv_path, mvs, allow_pickle=False)
        try:
            mv_bytes += os.path.getsize(mv_path)
        except FileNotFoundError:
            pass

        # 写帧（仅 B）- 包含运动向量可视化
        if write_frames and getattr(frame, "size", 0) > 0:
            # 在帧上绘制运动向量（原版功能）
            frame_with_vectors = _draw_motion_vectors(frame, mvs)
            jpg_path = os.path.join(frames_dir, f"{frames:06d}.jpg")
            cv2.imwrite(jpg_path, frame_with_vectors, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            try:
                frame_bytes += os.path.getsize(jpg_path)
            except FileNotFoundError:
                pass

        # 保存帧类型和时间戳（完整模式）
        if not want_mvo:  # 仅在完整模式下保存
            frame_types.append(ftype)
            timestamps.append(ts)

        frames += 1

    cap.release()
    t1 = time.perf_counter()

    # 保存帧类型和时间戳文件（完整模式）
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
    MVO = 你的本地扩展（强制从 LOCAL_SRC 导入）+ MVO-only
    FULL = PyPI/系统安装版（移除 LOCAL_SRC）+ Full decode（写帧）
    """
    # --- MVO: 本地扩展 + MVO-only ---
    mvo_mem = _bench_mem_only(input_video, test_frames, want_mvo=True,  force_local=True)
    mvo_e2e = _bench_e2e_with_dump(
        input_video, test_frames, os.path.join(output_dir, "MVO"),
        want_mvo=True, force_local=True
    )

    # --- FULL: PyPI 版 + Full decode ---
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
