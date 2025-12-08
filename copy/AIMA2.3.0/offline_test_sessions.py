import os
import pandas as pd

from config import MOVESENSE_SAMPLERATE_HZ
from angles import compute_quaternions, compute_knee_angles
from metrics import detect_reps, compute_rep_metrics
from features import session_features_from_metrics


# === УКАЖИ ЗДЕСЬ ФАЙЛЫ, КОТОРЫЕ ХОЧЕШЬ ПРОГНАТЬ ========================

FILES = [
    {
        "path": "data/sessions/proc_bob_squat_reps_test2_20251207_210939.csv",
        "movement_type": "squat",
    },
    {
        "path": "data/sessions/proc_bob_squat_reps_test3_20251207_211149.csv",
        "movement_type": "squat",
    },
    {
        "path": "data/sessions/proc_bob_walk_reps_test1_normal_20251207_235815.csv",
        "movement_type": "walk",
    },
    {
        "path": "data/sessions/proc_bob_walk_reps_test1_slow_20251208_000107.csv",
        "movement_type": "walk",
    },
    {
        "path": "data/sessions/proc_bob_walk_reps_test1_veryslow_20251208_000350.csv",
        "movement_type": "walk",
    },
    {
        "path": "data/sessions/proc_bob_walk_reps_test1_fast_20251208_000621.csv",
        "movement_type": "walk",
    },
    {
        "path": "data/sessions/proc_bob_lateral_reps_test4_normal_20251207_235348.csv",
        "movement_type": "lateral",
    },
    {
        "path": "data/sessions/proc_bob_lateral_reps_test3_normal_20251207_231021.csv",
        "movement_type": "lateral",
    },
    {
        "path": "data/sessions/proc_bob_lateral_reps_test1_20251207_224906.csv",
        "movement_type": "lateral",
    },
    {
        "path": "data/sessions/proc_bob_lateral_reps_test_slow_20251207_225157.csv",
        "movement_type": "lateral",
    },
]


# === ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ОДНОГО ФАЙЛА =========================

def process_file(info: dict):
    path = info["path"]
    movement_type = info["movement_type"]

    if not os.path.isfile(path):
        print(f"[WARN] file not found, skip: {path}")
        return

    print("\n" + "=" * 72)
    print(f"FILE: {os.path.basename(path)}   (movement={movement_type})")

    # 1) Загружаем PROC
    df_proc = pd.read_csv(path)

    # 2) Считаем кватернионы и углы (как в основном пайплайне)
    quats = compute_quaternions(df_proc)
    df_angles = compute_knee_angles(df_proc, quats)

    # 3) Детект репов
    res = detect_reps(
        df_proc=df_proc,
        movement_type=movement_type,
        samplerate_hz=MOVESENSE_SAMPLERATE_HZ,
    )
    peaks = res.peaks
    boundaries = res.boundaries

    print(f"Detected reps: {len(peaks)}")
    print(f"Peaks indices: {peaks.tolist()}")

    if len(peaks) == 0:
        print("[INFO] no reps -> skip metrics")
        return

    # 4) Per-rep метрики (flex + наш новый valgus_rms_rep_deg)
    df_metrics = compute_rep_metrics(
        df_angles=df_angles,
        peaks=peaks,
        samplerate_hz=MOVESENSE_SAMPLERATE_HZ,
        # если в compute_rep_metrics стоит нужный angle_col по умолчанию,
        # этот аргумент можно опустить
        # angle_col="KneeAngle_fused_filt_deg",
    )

    # Покажем ключевые столбцы по репам
    cols_to_show = [c for c in [
        "rep_id",
        "max_angle_deg",
        "valgus_rms_rep_deg",
        "duration_sec",
    ] if c in df_metrics.columns]

    print("\nPer-rep metrics:")
    if len(df_metrics) == 0:
        print("  <empty df_metrics>")
    else:
        print(df_metrics[cols_to_show].to_string(index=False))

    # 5) Сессионные фичи (как в main.py перед печатью “Polven maksimi fleksio”)
    session_feats = session_features_from_metrics(
        df_angles=df_angles,
        df_metrics=df_metrics,
        samplerate_hz=MOVESENSE_SAMPLERATE_HZ,
    )

    # 6) Красиво напечатаем основные индексы
    print("\nSession-level indices:")

    def p(name, key):
        if key in session_feats:
            print(f"  {name}: {session_feats[key]:.2f}")

    p("Flex max (sääriluun kallistuskulma, deg)", "flex_max_deg")
    p("Flex mean (deg)", "flex_mean_deg")
    p("Frontal deviation mean (deg)", "valgus_mean_deg")
    p("Frontal deviation RMS (deg)", "valgus_rms_deg")
    p("Rep count", "n_reps")
    p("Tempo (reps/min)", "tempo_reps_per_min")
    p("Mean rep duration (s)", "rep_mean_duration_sec")


# === MAIN ========================================================

if __name__ == "__main__":
    for info in FILES:
        process_file(info)
