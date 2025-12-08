# recompute_proc_from_raw.py

import pandas as pd
from pathlib import Path

from calibration import compute_imu_offsets
from processing import preprocess_main_measurement
from angles import compute_quaternions, compute_knee_angles

# === НАСТРОЙКИ ===

# Путь к калибровочному файлу (там, где ты стоял спокойно)
# !!! ВАЖНО: подставь СВОЙ файл калибровки !!!
CALIB_PATH = Path("data") / "calib_imu9_2025-12-07_08-09-18.csv"

# Список измерений, которые хотим пересчитать
MEASUREMENT_FILES = [
    Path("data") / "measurement_imu9_2025-12-07_07-02-14.csv",
    Path("data") / "measurement_imu9_2025-12-07_07-05-33.csv",
    Path("data") / "measurement_imu9_2025-12-07_08-10-41.csv",
]

OUT_DIR = Path("data") / "sessions"   # туда же, где лежат proc_*.csv


def main():
    # 1. Грузим калибровку и считаем offsets
    df_calib = pd.read_csv(CALIB_PATH)
    calib = compute_imu_offsets(df_calib)

    for meas_path in MEASUREMENT_FILES:
        print(f"\n=== REPROCESS {meas_path.name} ===")
        df_raw = pd.read_csv(meas_path)

        # 2. Базовая обработка (offsets, нормы, фильтры)
        df_proc = preprocess_main_measurement(df_raw, calib)

        # 3. Ориентация по Madgwick
        quats = compute_quaternions(df_proc)

        # 4. Коленные углы из кватернионов
        df_angles = compute_knee_angles(df_proc, quats)

        # 5. Сохраняем новый proc_* файл
        out_name = meas_path.stem.replace("measurement_imu9_", "proc_REGEN_")
        out_path = OUT_DIR / f"{out_name}.csv"
        df_angles.to_csv(out_path, index=False)
        print(f"  -> saved {out_path}")

if __name__ == "__main__":
    main()
