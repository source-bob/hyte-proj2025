# processing.py

import numpy as np
import pandas as pd

from config import MOVESENSE_SAMPLERATE_HZ


# processing.py

def apply_imu_calibration(df: pd.DataFrame, calib_params: dict) -> pd.DataFrame:
    """
    Применяет смещения акселерометра и гироскопа к основному измерению.
    Добавляет колонки:
      - AccX_corr, AccY_corr, AccZ_corr
      - GyroX_corr, GyroY_corr, GyroZ_corr
      - MagnX_corr, MagnY_corr, MagnZ_corr  (пока без калибровки, просто копия)
    """

    acc_bias = calib_params["acc_bias"]
    gyro_bias = calib_params["gyro_bias"]

    df_corr = df.copy()

    # аксель
    df_corr["AccX_corr"] = df_corr["AccX"] - acc_bias[0]
    df_corr["AccY_corr"] = df_corr["AccY"] - acc_bias[1]
    df_corr["AccZ_corr"] = df_corr["AccZ"] - acc_bias[2]

    # гироскоп
    df_corr["GyroX_corr"] = df_corr["GyroX"] - gyro_bias[0]
    df_corr["GyroY_corr"] = df_corr["GyroY"] - gyro_bias[1]
    df_corr["GyroZ_corr"] = df_corr["GyroZ"] - gyro_bias[2]

    # магнитометр — пока без вычитания bias, просто переименуем
    if "MagnX" in df_corr.columns:
        df_corr["MagnX_corr"] = df_corr["MagnX"]
        df_corr["MagnY_corr"] = df_corr["MagnY"]
        df_corr["MagnZ_corr"] = df_corr["MagnZ"]

    return df_corr


def add_vector_magnitudes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Добавляет модули векторов:
      - AccNorm (по скорректированным данным)
      - GyroNorm (по скорректированным данным)
    """

    df = df.copy()

    df["AccNorm"] = np.sqrt(
        df["AccX_corr"]**2 + df["AccY_corr"]**2 + df["AccZ_corr"]**2
    )

    df["GyroNorm"] = np.sqrt(
        df["GyroX_corr"]**2 + df["GyroY_corr"]**2 + df["GyroZ_corr"]**2
    )

    return df


def lowpass_rolling(df: pd.DataFrame, column: str, window_sec: float = 0.2) -> pd.Series:
    """
    Простейший low-pass через скользящее среднее
    window_sec — длительность окна в секундах (например, 0.2 = 200 мс).
    """

    window_samples = max(1, int(window_sec * MOVESENSE_SAMPLERATE_HZ))
    return df[column].rolling(window=window_samples, center=True, min_periods=1).mean()


def preprocess_main_measurement(df_meas: pd.DataFrame, calib_params: dict) -> pd.DataFrame:
    """
    Полный шаг обработки:
      1. применить калибровку
      2. добавить модули векторов
      3. добавить сглаженные версии модулей
    """

    df_corr = apply_imu_calibration(df_meas, calib_params)
    df_feat = add_vector_magnitudes(df_corr)

    # сглаживаем модули векторов
    df_feat["AccNorm_filt"] = lowpass_rolling(df_feat, "AccNorm", window_sec=0.2)
    df_feat["GyroNorm_filt"] = lowpass_rolling(df_feat, "GyroNorm", window_sec=0.2)

    return df_feat
