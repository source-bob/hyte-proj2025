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

    Ориентация сенсора:
      X+ вниз, Y+ вправо, Z+ вперёд.
    """

    df = df_proc.copy()

    yaw, pitch, roll = quaternions_to_euler_wxyz(quats)

    # Flexion: используем pitch, нормируем к 0 в начале
    flex = pitch - pitch[0]
    df["KneeAngle_fused_deg"] = flex
    df["KneeAngle_fused_filt_deg"] = lowpass_rolling(
        df,
        "KneeAngle_fused_deg",
        window_sec=0.25,
    )

    # Varus/valgus: используем roll, тоже нормируем к 0
    valgus = roll - roll[0]
    df["KneeValgus_fused_deg"] = valgus
    df["KneeValgus_filt_deg"] = lowpass_rolling(
        df,
        "KneeValgus_fused_deg",
        window_sec=0.25,
    )

    return df
