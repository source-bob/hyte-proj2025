import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from config import MOVESENSE_SAMPLERATE_HZ
from processing import preprocess_main_measurement
from angles import compute_quaternions, compute_knee_angles
from metrics import detect_reps, compute_rep_metrics, _detrend_moving_average


FLEX_COL_CANDIDATES = [
    "KneeAngle_fused_filt_deg",
    "KneeAngle_filt_deg",
    "KneeAngle_fused_deg",
]

def get_flex_column_name(df_angles: pd.DataFrame) -> str:
    """
    Возвращает имя колонки с углом сгибания колена.
    Поддерживает несколько возможных вариантов имён.
    """
    for name in FLEX_COL_CANDIDATES:
        if name in df_angles.columns:
            return name
    raise KeyError(
        f"No flexion angle column found in df_angles. "
        f"Available columns: {list(df_angles.columns)}"
    )


# === СЮДА ВПИШИ СВОИ ФАЙЛЫ ОДИН РАЗ ===
# Можно миксовать measurement_*.csv и proc_*.csv
FILES = [
    # Примеры – ЗАМЕНИ НА СВОИ:
    "data\sessions\proc_bob_lateral_reps_test_slow_20251207_225157.csv",
    "data\sessions\proc_bob_lateral_reps_test1_20251207_224906.csv",
    "data\sessions\proc_bob_lateral_reps_test3_normal_20251207_231021.csv"
]


LABELS = ["squat", "walk", "lateral"]


def infer_movement_from_name(path: str) -> str:
    name = os.path.basename(path).lower()
    for lbl in LABELS:
        if lbl in name:
            return lbl
    return "squat"  # дефолт, если в имени ничего нет


def load_session_any(csv_path: str):
    """
    Загружаем либо measurement_*.csv (сырые IMU),
    либо proc_*.csv (обработанные).

    Возвращаем:
        df_proc, df_angles
    """
    df = pd.read_csv(csv_path)

    has_corr = any(col.endswith("_corr") for col in df.columns)

    if has_corr:
        # proc_*.csv
        df_proc = df.copy()
        print("  [INFO] Detected PROC file (has *_corr columns).")
        quats = compute_quaternions(df_proc)
        df_angles = compute_knee_angles(df_proc, quats)
    else:
        # measurement_*.csv (RAW)
        print("  [INFO] Detected RAW measurement file (no *_corr columns).")
        df_meas = df.copy()

        # Временная калибровка: нулевые оффсеты
        calib = {}
        for ax in "XYZ":
            calib[f"Acc{ax}_offset"] = 0.0
            calib[f"Gyro{ax}_offset"] = 0.0
            calib[f"Magn{ax}_offset"] = 0.0

        df_proc = preprocess_main_measurement(df_meas, calib)
        quats = compute_quaternions(df_proc)
        df_angles = compute_knee_angles(df_proc, quats)

    flex_col = get_flex_column_name(df_angles)

    if "Flex_filt" not in df_proc.columns:
        df_proc["Flex_filt"] = df_angles[flex_col]

    return df_proc, df_angles



def plot_flex_with_peaks(df_angles: pd.DataFrame,
                         peaks: np.ndarray,
                         title: str):
    from config import MOVESENSE_SAMPLERATE_HZ
    n = len(df_angles)
    t = np.arange(n) / MOVESENSE_SAMPLERATE_HZ
    flex_col = get_flex_column_name(df_angles)
    raw_flex = df_angles[flex_col].to_numpy(dtype=float)

    # 1) Убираем медленный тренд, чтобы остались ритмичные качели
    flex_dt = _detrend_moving_average(
        raw_flex,
        samplerate_hz=MOVESENSE_SAMPLERATE_HZ,
        window_sec=5.0,   # окно побольше, чем для REP_HP_WINDOW_SEC
    )

    # 2) Считаем "стоя" как среднее за первые 2 секунды и сдвигаем в ноль
    n0 = int(2.0 * MOVESENSE_SAMPLERATE_HZ)
    offset = np.mean(flex_dt[:n0])
    flex = flex_dt - offset

    plt.plot(
        t,
        flex,
        label="Flex_filt (detrended)",
        linewidth=2,
    )

    if len(peaks) > 0:
        plt.scatter(
            peaks / MOVESENSE_SAMPLERATE_HZ,
            flex[peaks],
            marker="x",
            s=60,
            label="rep peaks",
        )
        for p in peaks:
            plt.axvline(p / MOVESENSE_SAMPLERATE_HZ, linestyle="--", alpha=0.3)

    plt.title(f"{title} (n_reps={len(peaks)})")
    plt.xlabel("Time (s)")
    plt.ylabel("Angle (deg)")
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.show()



def run_on_file(path: str):
    print(f"\n=== FILE: {path} ===")

    if not os.path.isfile(path):
        print("  [ERROR] file not found, skip.")
        return

    movement_type = infer_movement_from_name(path)
    print(f"  Movement (from name): {movement_type}")

    df_proc, df_angles = load_session_any(path)

    res = detect_reps(
        df_proc=df_proc,
        movement_type=movement_type,
        samplerate_hz=MOVESENSE_SAMPLERATE_HZ,
    )
    peaks = res.peaks

    print(f"  N reps: {len(peaks)}")
    print(f"  Peak indices: {peaks}")

    flex_col = get_flex_column_name(df_angles)

    df_metrics = compute_rep_metrics(
        df_angles,
        peaks,
        samplerate_hz=MOVESENSE_SAMPLERATE_HZ,
        angle_col=flex_col,
    )


    print("\n  REP METRICS:")
    print(df_metrics)

    plot_flex_with_peaks(df_angles, peaks, title=os.path.basename(path))

    # после plot_flex_with_peaks(...) в run_on_file, добавь:

    plt.figure()
    t = np.arange(len(df_proc)) / MOVESENSE_SAMPLERATE_HZ
    plt.plot(t, df_proc["GyroY_corr"], label="GyroY_corr")
    for p in peaks:
        plt.axvline(p / MOVESENSE_SAMPLERATE_HZ, linestyle="--", alpha=0.3)
    plt.legend()
    plt.title("GyroY_corr with rep lines")
    plt.xlabel("Time (s)")
    plt.tight_layout()
    plt.show()


def main():
    if not FILES:
        print("Заполни список FILES в test_reps.py своими CSV-путями.")
        return

    for path in FILES:
        run_on_file(path)


if __name__ == "__main__":
    main()
