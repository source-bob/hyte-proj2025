# metrics.py

import numpy as np
import pandas as pd
from scipy.signal import find_peaks


def detect_reps_gyro(
    df_proc: pd.DataFrame,
    gyro_col: str = "GyroY_corr",
    samplerate_hz: int = 104,
    hp_window_sec: float = 0.3,
    rel_height: float = 0.4,
    min_peak_distance_sec: float = 0.7,
):
    """
    Детекция приседов по GyroY_corr.

    1) High-pass (скользящее среднее) -> убираем дрейф
    2) Определяем доминирующий знак (вверх/вниз)
    3) Ищем пики только этого знака
    """

    gyro = df_proc[gyro_col].to_numpy().astype(float)

    win = max(1, int(hp_window_sec * samplerate_hz))
    baseline = pd.Series(gyro).rolling(
        window=win, center=True, min_periods=1
    ).mean().to_numpy()
    gyro_hp = gyro - baseline

    max_pos = float(np.nanmax(gyro_hp))
    max_neg = float(-np.nanmin(gyro_hp))

    if np.isnan(max_pos) or np.isnan(max_neg):
        print("[DEBUG] Gyro has NaN -> reps=0")
        return np.array([])

    if max_pos >= max_neg:
        sig = gyro_hp
        peak_mag = max_pos
        pol = "pos"
    else:
        sig = -gyro_hp
        peak_mag = max_neg
        pol = "neg"

    if peak_mag < 1.0:
        print(f"[DEBUG] peak_mag={peak_mag:.2f} < 1 dps -> reps=0")
        return np.array([])

    height = rel_height * peak_mag
    min_dist = int(min_peak_distance_sec * samplerate_hz)

    peaks, _ = find_peaks(
        sig,
        height=height,
        distance=min_dist,
        prominence=0.3 * peak_mag,
    )

    print(
        f"[DEBUG] gyro reps: polarity={pol}, "
        f"peak_mag={peak_mag:.2f}, height={height:.2f}, peaks={len(peaks)}"
    )

    return peaks


def compute_rep_metrics(
    df_angles: pd.DataFrame,
    peaks: np.ndarray,
    samplerate_hz: int = 104,
    angle_col: str = "KneeAngle_fused_filt_deg",
) -> pd.DataFrame:
    """
    Считает метрики по каждому повторению на основе угла flexion.
    """

    angle = df_angles[angle_col].to_numpy()
    n = len(angle)
    peaks = np.asarray(peaks, dtype=int)
    m = len(peaks)

    if m == 0:
        return pd.DataFrame(columns=[
            "rep_id", "peak_index", "t_peak_sec",
            "max_angle_deg", "rep_start_idx", "rep_end_idx",
            "duration_sec",
        ])

    boundaries = np.zeros(m + 1, dtype=int)
    boundaries[0] = 0
    boundaries[-1] = n - 1
    for i in range(1, m):
        boundaries[i] = (peaks[i - 1] + peaks[i]) // 2

    rows = []
    for i, p_idx in enumerate(peaks):
        start = boundaries[i]
        end = boundaries[i + 1]

        seg = angle[start:end + 1]
        max_angle = float(np.max(np.abs(seg)))
        t_peak = p_idx / samplerate_hz
        dur = (end - start) / samplerate_hz

        rows.append({
            "rep_id": i + 1,
            "peak_index": int(p_idx),
            "t_peak_sec": round(t_peak, 3),
            "max_angle_deg": round(max_angle, 2),
            "rep_start_idx": int(start),
            "rep_end_idx": int(end),
            "duration_sec": round(dur, 3),
        })

    return pd.DataFrame(rows)
