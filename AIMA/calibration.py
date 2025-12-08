# calibration.py

import numpy as np
import pandas as pd

from sensor_io import AimaMoveSenseRecorder
from config import (
    MOVESENSE_SAMPLERATE_HZ,
    CALIB_REC_LENGTH_SEC,
)


def record_calibration_segment() -> pd.DataFrame:
    """
    Записать короткий статичный отрезок для калибровки.
    Предполагаем, что в этот момент сенсор закреплён на колене,
    нога в «нулевой» позе и максимально неподвижна.
    """
    print(f"\n=== CALIBRATION ===")
    print(f"Пожалуйста, займи калибровочную позу и не двигайся {CALIB_REC_LENGTH_SEC} секунд.")
    input("Нажми ENTER, когда будешь готов начать калибровку...")

    # создаём рекордер ТОЛЬКО для калибровки с другой длительностью
    recorder = AimaMoveSenseRecorder(
        rec_length_sec=CALIB_REC_LENGTH_SEC,
        filename_prefix="calib"
    )

    df_calib = recorder.record_once_to_pandas()

    print("Калибровочный отрезок записан. Форма:", df_calib.shape)
    return df_calib


def compute_imu_offsets(df_calib: pd.DataFrame) -> dict:
    """
    Считает смещения (bias) акселерометра и гироскопа по калибровочному отрезку.
    Возвращает словарь с параметрами калибровки.
    """

    # На всякий случай отфильтруем строки, где все NaN в Timestamp, но это не критично
    # Для Acc/Gyro значения и так есть.
    acc_cols = ["AccX", "AccY", "AccZ"]
    gyro_cols = ["GyroX", "GyroY", "GyroZ"]

    acc_bias = df_calib[acc_cols].mean().to_numpy()
    gyro_bias = df_calib[gyro_cols].mean().to_numpy()

    # Вектор гравитации по акселерометру (в статике он указывает примерно вниз)
    gravity_vec = acc_bias.copy()
    g_norm = np.linalg.norm(gravity_vec)
    if g_norm > 0:
        gravity_dir = gravity_vec / g_norm
    else:
        gravity_dir = np.array([0.0, 0.0, 1.0])

    calib_params = {
        "acc_bias": acc_bias,          # средние значения акселя
        "gyro_bias": gyro_bias,        # средние значения гиро
        "gravity_dir": gravity_dir,    # нормированный вектор g в системе сенсора
        "samplerate_hz": MOVESENSE_SAMPLERATE_HZ,
    }

    print("\n=== Calibration parameters ===")
    print("Acc bias:", acc_bias)
    print("Gyro bias:", gyro_bias)
    print("Gravity direction (sensor frame):", gravity_dir)

    return calib_params
