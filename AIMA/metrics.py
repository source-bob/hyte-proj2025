# metrics.py
import numpy as np
import pandas as pd
from scipy.signal import find_peaks


def detect_reps_from_angle(
    df: pd.DataFrame,
    column: str = "KneeAngle_fused_filt_deg",
    samplerate_hz: int = 104,
    rel_height: float = 0.3,       # 30% от глубины приседа
    min_peak_distance_sec: float = 0.9,  # около длительности 1 приседа
):
    """
    Детекция приседаний по основному минимуму угла (самая глубокая точка).
    """

    angle = df[column].to_numpy()

    # 1) Инверсия — ищем "пики вниз" как "пики вверх"
    sig = -angle

    # 2) Находим max амплитуду в инвертированном сигнале
    peak_mag = np.nanmax(sig)

    # 3) Динамический порог (отсекает маленькие "мини-ямы")
    height = rel_height * peak_mag

    # 4) Минимальное расстояние между приседами
    min_dist_samples = int(min_peak_distance_sec * samplerate_hz)

    # 5) Поиск пиков (нижних точек)
    peaks, props = find_peaks(
        sig,
        height=height,
        distance=min_dist_samples,
    )

    print(f"[DEBUG] peak_mag={peak_mag:.3f}, height={height:.3f}, peaks={len(peaks)}")

    return peaks



def compute_rep_metrics(df, peaks, samplerate_hz=104,
                        column="KneeAngle_fused_filt_deg"):
    angle = df[column].to_numpy()
    angle_abs = np.abs(angle)
    n = len(angle)

    peaks = np.asarray(peaks)
    m = len(peaks)

    # границы между пиками
    boundaries = np.zeros(m + 1, dtype=int)
    boundaries[0] = 0
    boundaries[-1] = n - 1
    for i in range(1, m):
        boundaries[i] = (peaks[i-1] + peaks[i]) // 2

    metrics = []
    for i, peak_idx in enumerate(peaks):
        start = boundaries[i]
        end = boundaries[i+1]

        seg = angle_abs[start:end+1]
        peak_mag = float(seg.max())
        t_peak = peak_idx / samplerate_hz
        duration = (end - start) / samplerate_hz

        metrics.append({
            "rep_id": i + 1,
            "peak_index": int(peak_idx),
            "t_peak_sec": round(t_peak, 3),
            "max_angle_deg": round(peak_mag, 2),
            "rep_start_idx": int(start),
            "rep_end_idx": int(end),
            "duration_sec": round(duration, 3),
        })

    return pd.DataFrame(metrics)

