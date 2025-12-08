# angles.py

import numpy as np
import pandas as pd

from madgwick import MadgwickAHRS
from processing import lowpass_rolling
from config import MOVESENSE_SAMPLERATE_HZ, MADGWICK_BETA
from sklearn.decomposition import PCA


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


def estimate_motion_axes_pca(df_proc):
    """
    Определяет функциональные оси движения (flexion и valgus)
    по данным ускорения/гироскопа. Используется PCA, чтобы 
    получить главную плоскость движения, не зависящую от ориентации сенсора.
    """

    # --- 1. Соберём матрицу сигналов, отражающих движение ---
    # Можно использовать AccCorr или GyroCorr — Gyro лучше при активных движениях
    axes = []
    for col in ["GyroX_corr", "GyroY_corr", "GyroZ_corr"]:
        if col in df_proc.columns:
            axes.append(df_proc[col].to_numpy())
    X = np.vstack(axes).T  # форма (N, 3)

    # Центрируем
    X = X - np.mean(X, axis=0, keepdims=True)

    # --- 2. PCA: три главные компоненты ---
    pca = PCA(n_components=3)
    pca.fit(X)

    pc1 = pca.components_[0]  # главная ось движения (flexion)
    pc2 = pca.components_[1]  # вторая ось (valgus)
    pc3 = pca.components_[2]  # ортогональная (не нужна)

    # Нормируем
    pc1 /= np.linalg.norm(pc1)
    pc2 /= np.linalg.norm(pc2)

    return pc1, pc2


def compute_knee_angles_pca(df_proc, quats):
    """
    Вычисляет flexion и valgus углы, используя функциональные 
    PCA-оси, а не pitch/roll. Дает реалистичные значения движения.
    """

    # --- 1. Получаем PCA-оси движения ---
    pc_flex, pc_valgus = estimate_motion_axes_pca(df_proc)

    # --- 2. Берём матрицы поворота сенсора во времени ---
    # quats — массив [N, 4]
    N = len(quats)
    flex_angles = np.zeros(N)
    valgus_angles = np.zeros(N)

    # Нулевая ориентация — эталон
    # Применяем PCA-оси к начальному положению
    for t in range(N):
        q = quats[t]
        # Матрица поворота из quaternion
        qw, qx, qy, qz = q
        R = np.array([
            [1 - 2*(qy*qy + qz*qz),     2*(qx*qy - qz*qw),     2*(qx*qz + qy*qw)],
            [    2*(qx*qy + qz*qw), 1 - 2*(qx*qx + qz*qz),     2*(qy*qz - qx*qw)],
            [    2*(qx*qz - qy*qw),     2*(qy*qz + qx*qw), 1 - 2*(qx*qx + qy*qy)]
        ])

        # --- 3. Применяем ориентацию сенсора к PCA-осям ---
        flex_vec = R @ pc_flex
        valgus_vec = R @ pc_valgus

        # --- 4. Flexion = угол отклонения flex_vec от начальной оси flex ---
        if t == 0:
            flex_ref = flex_vec.copy()
            valgus_ref = valgus_vec.copy()

        # Угол между векторами
        cos_f = np.dot(flex_vec, flex_ref) / (np.linalg.norm(flex_vec)*np.linalg.norm(flex_ref))
        cos_f = np.clip(cos_f, -1.0, 1.0)
        flex_angle = np.degrees(np.arccos(cos_f))

        cos_v = np.dot(valgus_vec, valgus_ref) / (np.linalg.norm(valgus_vec)*np.linalg.norm(valgus_ref))
        cos_v = np.clip(cos_v, -1.0, 1.0)
        valgus_angle = np.degrees(np.arccos(cos_v))

        flex_angles[t] = flex_angle
        valgus_angles[t] = valgus_angle

    # --- 5. Сглаживаем углы (как раньше) ---
    flex_filt = pd.Series(flex_angles).rolling(5, min_periods=1, center=True).mean().to_numpy()
    valgus_filt = pd.Series(valgus_angles).rolling(5, min_periods=1, center=True).mean().to_numpy()

    return pd.DataFrame({
        "KneeAngle_fused_deg": flex_angles,
        "KneeAngle_fused_filt_deg": flex_filt,
        "KneeValgus_fused_deg": valgus_angles,
        "KneeValgus_filt_deg": valgus_filt,
    })


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
