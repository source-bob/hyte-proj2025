import numpy as np
import pandas as pd
from scipy.signal import find_peaks

from metrics import detect_reps_gyro, detect_reps_flexion_angle


# ==========================================================
#  SQUAT SEGMENTATION  (текущая логика — через GyroZ)
# ==========================================================

def segment_squat(df_proc, df_angles, samplerate_hz=104):
    """
    Выделение приседаний.

    1) Пытаемся детектировать репы по flexion-углу (HP-обработанному),
       ожидая 1 пик ≈ 1 присед.
    2) Если пиков слишком мало (например, <= 3), делаем fallback
       на старый вариант по гироскопу (GyroZ_corr).
    """
    print("\n=== SEGMENTATION: SQUAT ===")

    # --- 1. Основной способ: по flexion-HP ---
    peaks_flex = detect_reps_flexion_angle(
        df_angles,
        samplerate_hz=samplerate_hz,
        angle_col="KneeAngle_fused_filt_deg",
        hp_window_sec=2.0,
        min_peak_distance_sec=1.0,
        rel_height=0.3,
        rel_prom=0.2,
    )

    if len(peaks_flex) >= 4:
        print(f"[SQUAT] Используем flexion-based HP пики, всего: {len(peaks_flex)}")
        print(f"[SQUAT] Первые пики (до 15): {peaks_flex[:15]}")
        return peaks_flex

    print(
        f"[SQUAT] Flexion-based HP детекция дала мало пиков ({len(peaks_flex)}), "
        f"fallback на GyroZ_corr."
    )

    # --- 2. Запасной вариант: по гироскопу ---
    peaks_gyro = detect_reps_gyro(
        df_proc,
        gyro_col="GyroZ_corr",
        samplerate_hz=samplerate_hz,
        hp_window_sec=0.3,
        rel_height=0.4,
        min_peak_distance_sec=1.5,
    )
    print(f"[SQUAT] Количество пиков по Gyro: {len(peaks_gyro)}")
    if len(peaks_gyro) > 0:
        print(f"[SQUAT] Первые пики (до 15): {peaks_gyro[:15]}")
    return peaks_gyro


# ==========================================================
#  WALK SEGMENTATION (простая версия)
# ==========================================================

def segment_walk(df_proc, samplerate_hz=104):
    """
    Выделение шаговых циклов для ходьбы.
    Используем пики по |GyroZ_corr| (обычно хорошо отражает мах ноги/корпуса).
    """

    print("\n=== SEGMENTATION: WALK ===")

    # Берём канал с наибольшей динамикой при ходьбе
    if "GyroZ_corr" in df_proc.columns:
        sig = df_proc["GyroZ_corr"].to_numpy()
        sig_name = "GyroZ_corr"
    elif "GyroZ" in df_proc.columns:
        sig = df_proc["GyroZ"].to_numpy()
        sig_name = "GyroZ"
    else:
        # Фоллбек: нормаль гиро
        sig = df_proc["GyroNorm_filt"].to_numpy()
        sig_name = "GyroNorm_filt"

    sig_abs = np.abs(sig)

    mean = np.mean(sig_abs)
    std = np.std(sig_abs)
    height = mean + 0.5 * std  # можно будет подправить при необходимости

    # Шаги обычно ~1–2 в секунду → мин. расстояние между шагами ~0.35–0.5 s
    min_dist = int(0.35 * samplerate_hz)

    print(
        f"[WALK DEBUG] signal={sig_name}, mean={mean:.3f}, std={std:.3f}, "
        f"height={height:.3f}, min_dist={min_dist} näytettä "
        f"({min_dist/samplerate_hz:.2f}s)"
    )

    peaks, _ = find_peaks(sig_abs, height=height, distance=min_dist)

    print(f"[WALK DEBUG] Найдено шагов (пиков): {len(peaks)}")
    if len(peaks) > 0:
        print(f"[WALK DEBUG] Первые пики (до 20): {peaks[:20]}")

    return peaks



# ==========================================================
#  LATERAL SEGMENTATION (side steps)
# ==========================================================

def segment_lateral(df_proc, samplerate_hz=104):
    """
    Выделение боковых шагов.
    Используем AccY_corr — при боковом переносе массы пики хорошо видны.
    """

    print("\n=== SEGMENTATION: LATERAL ===")

    if "AccY_corr" in df_proc.columns:
        acc_y = df_proc["AccY_corr"].to_numpy()
        sig_name = "AccY_corr"
    else:
        acc_y = df_proc["AccY"].to_numpy()
        sig_name = "AccY"

    acc_abs = np.abs(acc_y)

    mean = np.mean(acc_abs)
    std = np.std(acc_abs)
    height = mean + 0.5 * std
    min_dist = int(0.4 * samplerate_hz)

    print(
        f"[LATERAL DEBUG] signal={sig_name}, mean={mean:.3f}, std={std:.3f}, "
        f"height={height:.3f}, min_dist={min_dist} näytettä "
        f"({min_dist/samplerate_hz:.2f}s)"
    )

    peaks, _ = find_peaks(
        acc_abs,
        height=height,
        distance=min_dist,
    )

    print(f"[LATERAL DEBUG] Найдено боковых шагов (пиков): {len(peaks)}")
    if len(peaks) > 0:
        print(f"[LATERAL DEBUG] Первые пики (до 20): {peaks[:20]}")

    return peaks


# ==========================================================
#  MAIN DISPATCHER — ВЫБОР СЕГМЕНТОРА
# ==========================================================

def segment_movement(df_proc, df_angles, movement_class, samplerate_hz=104):
    """
    Вызывает корректный сегментатор для данного типа движения.
    Возвращает peaks[] — индексы повторов/шагов.
    """

    if movement_class == "squat":
        return segment_squat(df_proc, df_angles, samplerate_hz)

    elif movement_class == "walk":
        return segment_walk(df_proc, samplerate_hz)

    elif movement_class == "lateral":
        return segment_lateral(df_proc, samplerate_hz)

    else:
        print(f"[WARN] Неизвестный тип движения '{movement_class}', fallback → squat")
        return segment_squat(df_proc, df_angles, samplerate_hz)
