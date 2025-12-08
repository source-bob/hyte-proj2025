# angles.py

import numpy as np
import pandas as pd

from madgwick import MadgwickAHRS
from processing import lowpass_rolling
from config import MOVESENSE_SAMPLERATE_HZ, MADGWICK_BETA


def compute_quaternions(df_proc: pd.DataFrame) -> np.ndarray:
    """
    Считает кватернионы ориентации сенсора из Acc/Gyro/Magn (_corr) через Madgwick.
    Возвращает массив (N, 4): [w, x, y, z].
    """
    dt = 1.0 / MOVESENSE_SAMPLERATE_HZ
    ahrs = MadgwickAHRS(sample_period=dt, beta=MADGWICK_BETA)

    quats = np.zeros((len(df_proc), 4), dtype=float)

    for i, row in enumerate(df_proc.itertuples(index=False)):
        gx = getattr(row, "GyroX_corr")
        gy = getattr(row, "GyroY_corr")
        gz = getattr(row, "GyroZ_corr")
        ax = getattr(row, "AccX_corr")
        ay = getattr(row, "AccY_corr")
        az = getattr(row, "AccZ_corr")
        mx = getattr(row, "MagnX_corr")
        my = getattr(row, "MagnY_corr")
        mz = getattr(row, "MagnZ_corr")

        ahrs.update(gx, gy, gz, ax, ay, az, mx, my, mz)
        quats[i] = ahrs.quaternion

    return quats


def quaternions_to_euler_wxyz(q: np.ndarray):
    """
    Преобразует массив кватернионов (w,x,y,z) в yaw/pitch/roll (deg).
    Возвращает три массива той же длины.
    """
    w, x, y, z = q.T

    # yaw (psi)
    yaw = np.degrees(np.arctan2(
        2.0 * (w * z + x * y),
        1.0 - 2.0 * (y * y + z * z),
    ))

    # pitch (theta)
    sinp = 2.0 * (w * y - z * x)
    sinp = np.clip(sinp, -1.0, 1.0)
    pitch = np.degrees(np.arcsin(sinp))

    # roll (phi)
    roll = np.degrees(np.arctan2(
        2.0 * (w * x + y * z),
        1.0 - 2.0 * (x * x + y * y),
    ))

    return yaw, pitch, roll


def compute_knee_angles(
    df_proc: pd.DataFrame,
    quats: np.ndarray,
) -> pd.DataFrame:
    """
    На основе кватернионов считает:
      - KneeAngle_fused_deg / _filt_deg (flexion/extension)
      - KneeValgus_fused_deg / _filt_deg (varus/valgus)

    Сенсор на передней поверхности голени.
    Используем:
      - flexion ≈ наклон сегмента в сагиттальной плоскости (pitch)
      - varus/valgus ≈ наклон в фронтальной плоскости (roll)
    """

    df = df_proc.copy()

    # --- 1. Euler из кватернионов ---
    yaw, pitch, roll = quaternions_to_euler_wxyz(quats)

    # Для отладки сохраняем в таблицу
    df["Yaw_deg"] = yaw
    df["Pitch_deg"] = pitch
    df["Roll_deg"] = roll

    n = len(df)
    if n == 0:
        # Пустой датафрейм – возвращаем как есть
        return df

    # --- 2. Базовая "нейтраль" (человек стоит) ---
    # Берём первую секунду измерения как опорную позу
    n0 = int(MOVESENSE_SAMPLERATE_HZ * 1.0)
    n0 = max(1, min(n0, n))  # на всякий случай

    # Flexion: используем pitch. Обычно при приседе голень наклоняется вперёд,
    # и pitch уходит в минус -> берём -pitch, чтобы flexion рос при сгибании.
    raw_flex = -pitch
    neutral_flex = float(np.mean(raw_flex[:n0]))
    flex = raw_flex - neutral_flex

    df["KneeAngle_fused_deg"] = flex
    df["KneeAngle_filt_deg"] = lowpass_rolling(
        df,
        "KneeAngle_fused_deg",
        window_sec=0.25,
    )

    # Varus/valgus: используем roll, тоже нормируем к нейтрали
    raw_valgus = roll
    neutral_valgus = float(np.mean(raw_valgus[:n0]))
    valgus = raw_valgus - neutral_valgus

    df["KneeValgus_fused_deg"] = valgus
    df["KneeValgus_filt_deg"] = lowpass_rolling(
        df,
        "KneeValgus_fused_deg",
        window_sec=0.25,
    )

    return df
