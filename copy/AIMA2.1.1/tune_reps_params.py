import os
import numpy as np
import pandas as pd

from config import MOVESENSE_SAMPLERATE_HZ
import metrics  # будем дергать detect_reps и менять параметры внутри
from processing import preprocess_main_measurement
from angles import compute_quaternions, compute_knee_angles


# === ВХОДНЫЕ ДАННЫЕ ДЛЯ ТЮНИНГА ================================

# Здесь укажи свои PROC-файлы и "правильное" число повторов
FILES_INFO = [
    {
        "path": "data/sessions/proc_LAST_FCKNG_TEST_NORMAL_20251207_070309.csv",
        "true_reps": 17,
        "movement_type": "squat",
    },
    {
        "path": "data/sessions/proc_LAST_FCKNG_TEST_SLOW_20251207_070554.csv",
        "true_reps": 9,
        "movement_type": "squat",
    },
    {
        "path": "data/sessions/proc_bob_squat_segmentation_final_test_20251207_081046.csv",
        "true_reps": 17,
        "movement_type": "squat",
    },
]

# Сетка параметров, по которой будем перебирать
DIST_VALUES = [0.35, 0.40, 0.45, 0.50, 0.60]
HEIGHT_VALUES = [0.18, 0.22, 0.25, 0.30, 0.35]
HP_VALUES = [0.15, 0.20]  # можно оставить один, если не хочешь трогать HP


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===================================

def load_proc_and_angles(csv_path: str):
    """
    Загружает PROC-файл и пересчитывает углы.
    Предполагаем, что в файле уже есть *_corr-колонки.
    """
    df_proc = pd.read_csv(csv_path)
    has_corr = any(col.endswith("_corr") for col in df_proc.columns)
    if not has_corr:
        raise ValueError(
            f"File {csv_path} doesn't look like PROC (no *_corr columns)."
        )

    quats = compute_quaternions(df_proc)
    df_angles = compute_knee_angles(df_proc, quats)

    # Гарантируем Flex_filt для детектора
    if "Flex_filt" not in df_proc.columns:
        df_proc["Flex_filt"] = df_angles["KneeAngle_fused_filt_deg"]

    return df_proc, df_angles


def evaluate_params_for_file(info, dist_sec, rel_height, hp_sec):
    """
    Считает, сколько репов даёт выбранная комбинация параметров
    для одного файла.
    Возвращает (n_reps, error).
    """
    path = info["path"]
    true_reps = info["true_reps"]
    movement_type = info["movement_type"]

    if not os.path.isfile(path):
        print(f"[WARN] File not found, skipping: {path}")
        return None

    df_proc, df_angles = load_proc_and_angles(path)

    # Настраиваем параметры в metrics (dict-объекты шарятся с config)
    metrics.REP_MIN_DIST_SEC[movement_type] = dist_sec
    metrics.REP_REL_HEIGHT[movement_type] = rel_height
    metrics.REP_HP_WINDOW_SEC = hp_sec

    res = metrics.detect_reps(
        df_proc=df_proc,
        movement_type=movement_type,
        samplerate_hz=MOVESENSE_SAMPLERATE_HZ,
    )
    peaks = res.peaks
    n_reps = len(peaks)
    error = abs(n_reps - true_reps)

    return n_reps, error


def grid_search():
    results = []  # сюда сложим все комбинации и их ошибки

    for hp_sec in HP_VALUES:
        for dist_sec in DIST_VALUES:
            for rel_h in HEIGHT_VALUES:
                total_err = 0
                per_file = []

                for info in FILES_INFO:
                    res = evaluate_params_for_file(
                        info,
                        dist_sec=dist_sec,
                        rel_height=rel_h,
                        hp_sec=hp_sec,
                    )
                    if res is None:
                        continue
                    n_reps, err = res
                    total_err += err
                    per_file.append((info["path"], info["true_reps"], n_reps, err))

                if not per_file:
                    continue

                results.append({
                    "hp_sec": hp_sec,
                    "dist_sec": dist_sec,
                    "rel_height": rel_h,
                    "total_err": total_err,
                    "details": per_file,
                })

    # сортируем по суммарной ошибке, затем по dist/height
    results.sort(key=lambda r: (r["total_err"], r["dist_sec"], r["rel_height"]))

    print("\n=== TOP PARAMETER COMBINATIONS ===")
    for r in results[:15]:
        print(
            f"\nHP={r['hp_sec']:.2f}  dist={r['dist_sec']:.2f}  "
            f"height={r['rel_height']:.2f}  --> total_err={r['total_err']}"
        )
        for (path, true_reps, n_reps, err) in r["details"]:
            print(
                f"  {os.path.basename(path)}: true={true_reps}, "
                f"pred={n_reps}, err={err}"
            )


if __name__ == "__main__":
    grid_search()
