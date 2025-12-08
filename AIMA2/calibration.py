# calibration.py

import os
import pandas as pd

from sensor_io import AimaMoveSenseRecorder
from config import CALIB_LENGTH_SEC, MOVESENSE_SAMPLERATE_HZ


def record_calibration_segment() -> pd.DataFrame:
    """
    Запись короткого калибровочного сегмента.
    Сенсор на голени, стоим спокойно, не двигаемся.
    """
    print(f"\n=== КАЛИБРОВКА ({CALIB_LENGTH_SEC} сек, стоять спокойно) ===")
    input("Когда будешь стоять спокойно, нажми ENTER...")

    recorder = AimaMoveSenseRecorder(
        rec_length_sec=CALIB_LENGTH_SEC,
        filename_prefix="calib"
    )
    df_calib = recorder.record_once_to_pandas()

    print("=== CALIB MEASUREMENT (head) ===")
    print(df_calib.head())
    return df_calib


def compute_imu_offsets(df_calib: pd.DataFrame) -> dict:
    """
    Вычисляет смещения (offset) по Acc/Gyro/Magn
    на основе калибровочного сегмента.
    """
    offsets = {}

    for axis in ["X", "Y", "Z"]:
        offsets[f"Acc{axis}_offset"] = df_calib[f"Acc{axis}"].mean()
        offsets[f"Gyro{axis}_offset"] = df_calib[f"Gyro{axis}"].mean()
        offsets[f"Magn{axis}_offset"] = df_calib[f"Magn{axis}"].mean()

    offsets["samplerate_hz"] = MOVESENSE_SAMPLERATE_HZ

    print("\n=== CALIB OFFSETS ===")
    for k, v in offsets.items():
        print(f"{k}: {v:.3f}")

    return offsets
