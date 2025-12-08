import numpy as np
import pandas as pd
from scipy.signal import find_peaks

from metrics import detect_reps_gyro, detect_reps


# ==========================================================
#  SQUAT SEGMENTATION  (текущая логика — через GyroZ)
# ==========================================================

def segment_squat(df_proc, df_angles, samplerate_hz=104):
    res = detect_reps(
        df_proc=df_proc,
        movement_type="squat",
        samplerate_hz=samplerate_hz
    )
    return res.peaks



# ==========================================================
#  WALK SEGMENTATION (простая версия)
# ==========================================================

# ==========================================================
#  WALK SEGMENTATION через общий detect_reps
# ==========================================================

def segment_walk(df_proc, samplerate_hz=104):
    """
    Сегментация ходьбы: используем тот же универсальный детектор повторений,
    но с movement_type="walk".

    Ось и параметры берутся из config.REP_AXIS / REP_MIN_DIST_SEC / REP_REL_HEIGHT.
    """
    res = detect_reps(
        df_proc=df_proc,
        movement_type="walk",
        samplerate_hz=samplerate_hz,
    )
    return res.peaks


# ==========================================================
#  LATERAL SEGMENTATION через общий detect_reps
# ==========================================================

def segment_lateral(df_proc, samplerate_hz=104):
    """
    Сегментация боковых шагов: тоже через универсальный детектор,
    movement_type="lateral".
    """
    res = detect_reps(
        df_proc=df_proc,
        movement_type="lateral",
        samplerate_hz=samplerate_hz,
    )
    return res.peaks


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
        return segment_squat(df_proc, samplerate_hz)
