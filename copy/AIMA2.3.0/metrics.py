# metrics.py

import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from dataclasses import dataclass

from config import (
    REP_AXIS,
    REP_POLARITY,
    REP_HP_WINDOW_SEC,
    REP_MIN_DIST_SEC,
    REP_REL_HEIGHT,
)


def _highpass_moving_average(
    signal: np.ndarray,
    samplerate_hz: float,
    window_sec: float,
) -> np.ndarray:
    """
    Простейший high-pass через скользящее среднее:
        hp = signal - moving_average(signal, window_sec)
    """
    n = signal.size
    if n == 0:
        return signal

    win = max(1, int(round(window_sec * samplerate_hz)))
    baseline = (
        pd.Series(signal)
        .rolling(window=win, center=True, min_periods=1)
        .mean()
        .to_numpy()
    )
    return signal - baseline


def detect_reps_gyro(
    df_proc: pd.DataFrame,
    gyro_col: str = "GyroY_corr",
    samplerate_hz: int = 104,
    hp_window_sec: float = 0.3,
    rel_height: float = 0.4,
    min_peak_distance_sec: float = 0.7,
) -> np.ndarray:
    """
    Вспомогательный детектор повторений по одному gyro-каналу.

    Используется только в test_reps.py как отдельный стенд.
    Основной пайплайн должен использовать detect_reps().
    """

    if gyro_col not in df_proc.columns:
        print(f"[detect_reps_gyro] column '{gyro_col}' not in df_proc")
        return np.array([], dtype=int)

    gyro = df_proc[gyro_col].to_numpy(dtype=float)

    # High-pass
    win = max(1, int(hp_window_sec * samplerate_hz))
    baseline = (
        pd.Series(gyro)
        .rolling(window=win, center=True, min_periods=1)
        .mean()
        .to_numpy()
    )
    gyro_hp = gyro - baseline

    max_pos = float(np.nanmax(gyro_hp))
    max_neg = float(-np.nanmin(gyro_hp))

    if np.isnan(max_pos) or np.isnan(max_neg):
        print("[DEBUG] Gyro has NaN -> reps=0")
        return np.array([], dtype=int)

    # Выбираем доминирующую полярность
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
        return np.array([], dtype=int)

    height = rel_height * peak_mag
    min_dist = int(round(min_peak_distance_sec * samplerate_hz))

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

    return peaks.astype(int)


def _detrend_moving_average(
    signal: np.ndarray,
    samplerate_hz: float,
    window_sec: float = 5.0,
) -> np.ndarray:
    """
    Убираем медленный тренд через скользящее среднее.
    Это НЕ high-pass для быстрого шума, а именно снятие
    очень медленного «ползания» базовой линии.
    """
    n = signal.size
    if n == 0:
        return signal

    win = max(1, int(round(window_sec * samplerate_hz)))
    baseline = (
        pd.Series(signal)
        .rolling(window=win, center=True, min_periods=1)
        .mean()
        .to_numpy()
    )
    return signal - baseline



def compute_rep_metrics(
    df_angles: pd.DataFrame,
    peaks: np.ndarray,
    samplerate_hz: int = 104,
    angle_col: str = "KneeAngle_filt_deg",
) -> pd.DataFrame:
    """
    Считает метрики по каждому повторению на основе угла flexion
    + (новое) per-rep фронтальный индекс (valgus_rms_rep_deg), если доступен.

    df_angles — DataFrame с колонкой angle_col (обычно KneeAngle_filt_deg).
    """

    base_cols = [
        "rep_id", "peak_index", "t_peak_sec",
        "max_angle_deg", "rep_start_idx", "rep_end_idx",
        "duration_sec",
    ]

    # если хотим, чтобы колонка существовала даже в пустом df:
    all_cols = base_cols + ["valgus_rms_rep_deg"]

    if angle_col not in df_angles.columns:
        print(f"[compute_rep_metrics] column '{angle_col}' not in df_angles")
        return pd.DataFrame(columns=all_cols)

    raw_angle = df_angles[angle_col].to_numpy(dtype=float)

    # Для flex-indeksi берём уже фильтрованный угол как есть, без доп. детренда
    angle = raw_angle


    n = len(angle)
    peaks = np.asarray(peaks, dtype=int)
    m = len(peaks)

    if m == 0:
        return pd.DataFrame(columns=all_cols)

    # --- Границы репов: середины между соседними пиками (как было раньше) ---
    boundaries = np.zeros(m + 1, dtype=int)
    boundaries[0] = 0
    boundaries[-1] = n - 1
    for i in range(1, m):
        boundaries[i] = (peaks[i - 1] + peaks[i]) // 2

    rows = []

    # Подготовим фронтальный сигнал, если он есть
    if "KneeValgus_filt_deg" in df_angles.columns:
        valgus_full = df_angles["KneeValgus_filt_deg"].to_numpy(dtype=float)
    else:
        valgus_full = None

    for i, p_idx in enumerate(peaks):
        start = int(boundaries[i])
        end = int(boundaries[i + 1])

        # --- Flex-часть (как было) ---
        seg = angle[start:end + 1]
        max_angle = float(np.max(np.abs(seg)))
        t_peak = p_idx / samplerate_hz
        dur = (end - start) / samplerate_hz

        row = {
            "rep_id": i + 1,
            "peak_index": int(p_idx),
            "t_peak_sec": round(t_peak, 3),
            "max_angle_deg": round(max_angle, 2),
            "rep_start_idx": start,
            "rep_end_idx": end,
            "duration_sec": round(dur, 3),
        }

        # --- Новое: фронтальное отклонение по репу ---
        if valgus_full is not None:
            valgus_seg = valgus_full[start:end + 1]

            # отсеиваем откровенные артефакты
            mask = np.isfinite(valgus_seg) & (np.abs(valgus_seg) <= 35.0)
            if np.any(mask):
                clean = valgus_seg[mask]
                valgus_rms_rep = float(np.sqrt(np.mean(clean ** 2)))
            else:
                valgus_rms_rep = np.nan  # весь реп – артефакт

            row["valgus_rms_rep_deg"] = (
                round(valgus_rms_rep, 2) if np.isfinite(valgus_rms_rep) else np.nan
            )

        rows.append(row)

    return pd.DataFrame(rows, columns=all_cols)



@dataclass
class RepDetectionResult:
    peaks: np.ndarray
    boundaries: np.ndarray


def detect_reps(
    df_proc: pd.DataFrame,
    movement_type: str,
    samplerate_hz: float = 104,
) -> RepDetectionResult:
    """
    Унифицированный детектор повторений для squat / walk / lateral.

    Для каждого movement_type используется ось из REP_AXIS[movement_type].
    Для squat ось должна быть GyroNorm_filt (настраивается в config.py).

    Алгоритм:
      1) Берём сигнал по оси REP_AXIS.
      2) High-pass через скользящее среднее (REP_HP_WINDOW_SEC).
      3) Учитываем полярность REP_POLARITY.
      4) Первый проход: мягкий поиск кандидатов-пиков.
      5) Считаем median(|peak_heights|) → адаптивный порог.
      6) Второй проход: финальные пики с height и distance.
      7) Границы репов — середины между соседними пиками.
    """

    if movement_type not in REP_AXIS:
        raise ValueError(f"Unknown movement_type '{movement_type}'")

    axis = REP_AXIS[movement_type]
    if axis not in df_proc.columns:
        print(f"[ERROR] REP_AXIS '{axis}' отсутствует в df_proc")
        return RepDetectionResult(
            peaks=np.array([], dtype=int),
            boundaries=np.array([0, max(len(df_proc) - 1, 0)], dtype=int),
        )

    signal = df_proc[axis].to_numpy(dtype=float)
    n = signal.size
    if n == 0:
        return RepDetectionResult(
            peaks=np.array([], dtype=int),
            boundaries=np.array([0], dtype=int),
        )

    # --- 1. High-pass ---
    hp = _highpass_moving_average(
        signal,
        samplerate_hz=samplerate_hz,
        window_sec=REP_HP_WINDOW_SEC,
    )

    # --- 2. Учёт полярности ---
    polarity = float(REP_POLARITY.get(movement_type, 1.0))
    work = hp * polarity

    max_amp = float(np.nanmax(np.abs(work)))
    if not np.isfinite(max_amp) or max_amp < 1e-6:
        return RepDetectionResult(
            peaks=np.array([], dtype=int),
            boundaries=np.array([0, n - 1], dtype=int),
        )

    base_min_dist_sec = float(REP_MIN_DIST_SEC.get(movement_type, 0.7))
    base_rel_height = float(REP_REL_HEIGHT.get(movement_type, 0.25))

    # --- 3. Первый мягкий проход: кандидаты ---
    cand_height = 0.10 * max_amp           # 10% от максимума
    cand_dist = int(round(0.25 * samplerate_hz))  # 0.25 s

    cand_peaks, cand_props = find_peaks(
        work,
        height=cand_height,
        distance=max(1, cand_dist),
    )

    if cand_peaks.size == 0:
        return RepDetectionResult(
            peaks=np.array([], dtype=int),
            boundaries=np.array([0, n - 1], dtype=int),
        )

    cand_heights = np.asarray(cand_props["peak_heights"], dtype=float)
    median_h = float(np.median(np.abs(cand_heights)))

    # --- 4. Адаптивный порог ---
    thr_dyn = 0.7 * median_h
    thr_floor = base_rel_height * max_amp
    height_threshold = max(thr_dyn, thr_floor)

    # --- 5. Финальный поиск пиков ---
    min_dist_samples = int(round(base_min_dist_sec * samplerate_hz))
    peaks, props = find_peaks(
        work,
        height=height_threshold,
        distance=max(1, min_dist_samples),
    )
    peaks = peaks.astype(int)

    if peaks.size == 0:
        return RepDetectionResult(
            peaks=np.array([], dtype=int),
            boundaries=np.array([0, n - 1], dtype=int),
        )

    # --- 6. Границы репов ---
    boundaries = np.zeros(peaks.size + 1, dtype=int)
    boundaries[0] = 0
    boundaries[-1] = n - 1
    for i in range(1, peaks.size):
        boundaries[i] = (peaks[i - 1] + peaks[i]) // 2

    print(
        f"[REPS] movement={movement_type}, n_peaks={len(peaks)}, "
        f"max_amp={max_amp:.2f}, median_h={median_h:.2f}, "
        f"thr={height_threshold:.2f}"
    )

    return RepDetectionResult(peaks=peaks, boundaries=boundaries)
