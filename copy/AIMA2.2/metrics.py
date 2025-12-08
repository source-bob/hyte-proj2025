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

    print(
        f"[DEBUG GYRO REPS] col={gyro_col}, samplerate={samplerate_hz}Hz, "
        f"hp_window={hp_window_sec:.2f}s, rel_height={rel_height:.2f}, "
        f"min_peak_distance={min_peak_distance_sec:.2f}s ({min_dist} näytettä)"
    )

    peaks, _ = find_peaks(
        sig,
        height=height,
        distance=min_dist,
        prominence=0.3 * peak_mag,
    )

    print(
        f"[DEBUG GYRO REPS] polarity={pol}, "
        f"peak_mag={peak_mag:.2f}, height={height:.2f}, peaks={len(peaks)}"
    )

    return peaks


def detect_reps_flexion_angle(
    df_angles: pd.DataFrame,
    samplerate_hz: int = 104,
    angle_col: str = "KneeAngle_fused_filt_deg",
    hp_window_sec: float = 2.0,
    min_peak_distance_sec: float = 1.0,
    rel_height: float = 0.3,
    rel_prom: float = 0.2,
):
    """
    Детекция приседов по surrogate flexion-углу, но с удалением
    медленного тренда (high-pass через скользящее среднее).

    Шаги:
      1) Берём сглаженный угол KneeAngle_fused_filt_deg.
      2) Вычитаем скользящее среднее по окну ~2s -> убираем дрейф.
      3) Берём модуль сигнала и ищем пики по |angle_hp|.
    """

    print("\n=== FLEXION-BASED REP DETECTION (HP) ===")

    if angle_col not in df_angles.columns:
        print(f"[FLEXION DEBUG] Колонка {angle_col} не найдена, возврат пустого списка.")
        return np.array([])

    angle = df_angles[angle_col].to_numpy().astype(float)
    n = len(angle)
    if n == 0:
        print("[FLEXION DEBUG] Пустой сигнал (n=0) — репов нет.")
        return np.array([])

    # --- 1. High-pass через скользящее среднее ---
    win = max(1, int(hp_window_sec * samplerate_hz))
    baseline = pd.Series(angle).rolling(
        window=win, center=True, min_periods=1
    ).mean().to_numpy()
    angle_hp = angle - baseline
    sig = np.abs(angle_hp)

    max_amp = float(np.nanmax(sig))
    if np.isnan(max_amp) or max_amp < 5.0:
        # сигнал слишком слабый, чтобы надёжно детектировать циклы
        print(f"[FLEXION DEBUG] max_amp_hp={max_amp:.2f}° < 5° — репов не ищем.")
        return np.array([])

    height = rel_height * max_amp          # порог по высоте на HP-сигнале
    prominence = rel_prom * max_amp        # порог по "выразительности"
    min_dist = int(min_peak_distance_sec * samplerate_hz)

    print(
        f"[FLEXION DEBUG] samplerate={samplerate_hz}Hz, n={n}, "
        f"hp_window={hp_window_sec:.2f}s (win={win}), "
        f"max_amp_hp={max_amp:.2f}°, height>={height:.2f}°, "
        f"prominence>={prominence:.2f}°, "
        f"min_peak_distance={min_peak_distance_sec:.2f}s ({min_dist} näytettä)"
    )

    peaks, props = find_peaks(
        sig,
        height=height,
        distance=min_dist,
        prominence=prominence,
    )

    print(f"[FLEXION DEBUG] Найдено пиков по flexion-HP: {len(peaks)}")
    if len(peaks) > 0:
        print(f"[FLEXION DEBUG] Первые пики (до 15): {peaks[:15]}")

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
        print("\n[METRICS] Повторов не найдено (m=0) — возвращаем пустую таблицу.")
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

    df = pd.DataFrame(rows)

    # --- DEBUG-БЛОК ---
    print("\n[METRICS DEBUG] ===== REP METRICS SUMMARY =====")
    print(f"Всего повторов (rows): {len(df)}")
    print(f"Длина углового сигнала: {n} näytettä")
    if len(df) > 0:
        first = df.iloc[0]
        last = df.iloc[-1]
        print(
            f"  Первый реп: id={first['rep_id']}, "
            f"start={first['rep_start_idx']}, end={first['rep_end_idx']}, "
            f"dur={first['duration_sec']:.2f}s, max_angle={first['max_angle_deg']:.1f}°"
        )
        if len(df) > 1:
            print(
                f"  Последний реп: id={last['rep_id']}, "
                f"start={last['rep_start_idx']}, end={last['rep_end_idx']}, "
                f"dur={last['duration_sec']:.2f}s, max_angle={last['max_angle_deg']:.1f}°"
            )
    print("[METRICS DEBUG] ================================\n")

    return df


def filter_squat_reps(
    df_metrics: pd.DataFrame,
    min_angle_deg: float = 20.0,
    min_dur_sec: float = 1.0,
) -> pd.DataFrame:
    """
    Фильтрация 'полноценных' приседаний:
      - по минимальной глубине сгибания (max_angle_deg),
      - по минимальной длительности повтора (duration_sec).

    Всё, что меньше порогов, считаем мелкими колебаниями / полуприседами
    и не учитываем как отдельные повторы.
    """

    if df_metrics is None or df_metrics.empty:
        print("\n[METRICS FILTER] Пустая таблица df_metrics — фильтровать нечего.")
        return df_metrics

    mask = (
        (df_metrics["max_angle_deg"] >= min_angle_deg) &
        (df_metrics["duration_sec"] >= min_dur_sec)
    )

    df_valid = df_metrics[mask].reset_index(drop=True).copy()

    print("\n[METRICS FILTER] Фильтрация 'полноценных' приседаний:")
    print(f"  Всего сегментов до фильтрации: {len(df_metrics)}")
    print(f"  Осталось после фильтрации: {len(df_valid)}")
    print(f"  Порог глубины: max_angle >= {min_angle_deg}°")
    print(f"  Порог длительности: duration >= {min_dur_sec:.2f} s")

    # Перенумеруем rep_id, чтобы шли от 1 до N подряд
    if not df_valid.empty:
        df_valid["rep_id"] = np.arange(1, len(df_valid) + 1, dtype=int)

    return df_valid
