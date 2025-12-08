# processing.py

import numpy as np
import pandas as pd

from config import MOVESENSE_SAMPLERATE_HZ


def lowpass_rolling(
    df: pd.DataFrame,
    col: str,
    window_sec: float,
    samplerate_hz: int = MOVESENSE_SAMPLERATE_HZ,
) -> pd.Series:
    """
    Простой "low-pass" на основе скользящего среднего.
    """
    win = max(1, int(window_sec * samplerate_hz))
    return (
        df[col]
        .rolling(window=win, center=True, min_periods=1)
        .mean()
    )


def preprocess_main_measurement(
    df_raw: pd.DataFrame,
    calib: dict,
) -> pd.DataFrame:
    """
    Базовая обработка основного измерения:
      - вычитание offsets из калибровки
      - расчёт норм векторов
      - сглаживание норм (для диагностики)
    """
    df = df_raw.copy()

    for axis in ["X", "Y", "Z"]:
        df[f"Acc{axis}_corr"] = df[f"Acc{axis}"] - calib.get(f"Acc{axis}_offset", 0.0)
        df[f"Gyro{axis}_corr"] = df[f"Gyro{axis}"] - calib.get(f"Gyro{axis}_offset", 0.0)
        df[f"Magn{axis}_corr"] = df[f"Magn{axis}"] - calib.get(f"Magn{axis}_offset", 0.0)

    df["AccNorm"] = np.sqrt(
        df["AccX_corr"] ** 2 + df["AccY_corr"] ** 2 + df["AccZ_corr"] ** 2
    )
    df["GyroNorm"] = np.sqrt(
        df["GyroX_corr"] ** 2 + df["GyroY_corr"] ** 2 + df["GyroZ_corr"] ** 2
    )

    df["AccNorm_filt"] = lowpass_rolling(df, "AccNorm", window_sec=0.25)
    df["GyroNorm_filt"] = lowpass_rolling(df, "GyroNorm", window_sec=0.25)

    return df
