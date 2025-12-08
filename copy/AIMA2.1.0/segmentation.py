import numpy as np
import pandas as pd
from scipy.signal import find_peaks

from metrics import detect_reps_gyro


# ==========================================================
#  SQUAT SEGMENTATION  (текущая логика — через GyroZ)
# ==========================================================

def segment_squat(df_proc, samplerate_hz=104):
    """
    Выделение приседаний — просто обёртка над detect_reps_gyro.
    Возвращает peaks (индексы повторов).
    """
    peaks = detect_reps_gyro(
        df_proc,
        gyro_col="GyroZ_corr",
        samplerate_hz=samplerate_hz,
    )
    return peaks


# ==========================================================
#  WALK SEGMENTATION (простая версия)
# ==========================================================

def segment_walk(df_proc, samplerate_hz=104):
    """
    Выделение шаговых циклов для ходьбы.
    Используем пики по |GyroZ_corr| (обычно хорошо отражает мах ноги/корпуса).
    """

    # Берём канал с наибольшей динамикой при ходьбе
    if "GyroZ_corr" in df_proc.columns:
        sig = df_proc["GyroZ_corr"].to_numpy()
    elif "GyroZ" in df_proc.columns:
        sig = df_proc["GyroZ"].to_numpy()
    else:
        # Фоллбек: нормаль гиро
        sig = df_proc["GyroNorm_filt"].to_numpy()

    sig_abs = np.abs(sig)

    # Порог по амплитуде: чуть выше среднего
    mean = np.mean(sig_abs)
    std = np.std(sig_abs)
    height = mean + 0.5 * std  # можно подправить при необходимости

    # Шаги обычно ~1–2 в секунду → мин. расстояние между шагами ~0.35–0.5 s
    min_dist = int(0.35 * samplerate_hz)

    peaks, _ = find_peaks(sig_abs, height=height, distance=min_dist)

    return peaks



# ==========================================================
#  LATERAL SEGMENTATION (side steps)
# ==========================================================

def segment_lateral(df_proc, samplerate_hz=104):
    """
    Выделение боковых шагов.
    Используем AccY_corr — при боковом переносе массы пики хорошо видны.
    """

    acc_y = df_proc["AccY_corr"].to_numpy()

    # Ищем пики по Y-ускорению
    peaks, _ = find_peaks(
        np.abs(acc_y),
        height=np.mean(np.abs(acc_y)) * 1.5,
        distance=int(0.4 * samplerate_hz),
    )

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
        return segment_squat(df_proc, samplerate_hz)

    elif movement_class == "walk":
        return segment_walk(df_proc, samplerate_hz)

    elif movement_class == "lateral":
        return segment_lateral(df_proc, samplerate_hz)

    else:
        print(f"[WARN] Неизвестный тип движения '{movement_class}', fallback → squat")
        return segment_squat(df_proc, samplerate_hz)
