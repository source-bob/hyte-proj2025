# main.py

import os
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from config import (
    MOVESENSE_SAMPLERATE_HZ,
    REC_LENGTH_SEC,
    SESSIONS_DIR,
    METRICS_DIR,
    FEATURES_DIR,
)
from sensor_io import AimaMoveSenseRecorder
from calibration import record_calibration_segment, compute_imu_offsets
from processing import preprocess_main_measurement
from angles import compute_quaternions, compute_knee_angles
from metrics import detect_reps_gyro, compute_rep_metrics
from features import session_features_from_metrics
from ai_model import (
    evaluate_technique,
    load_cnn_model,
    classify_reps_cnn,
)


def plot_all(df_meas, df_angles, title_prefix="Main measurement"):
    n = len(df_meas)
    t = np.arange(n) / MOVESENSE_SAMPLERATE_HZ

    fig, axes = plt.subplots(5, 1, figsize=(10, 14), sharex=True)

    ax = axes[0]
    ax.plot(t, df_meas["AccX"], label="AccX")
    ax.plot(t, df_meas["AccY"], label="AccY")
    ax.plot(t, df_meas["AccZ"], label="AccZ")
    ax.set_title(f"{title_prefix} Accelerometer")
    ax.set_ylabel("Acceleration (g)")
    ax.legend(loc="upper right")

    ax = axes[1]
    ax.plot(t, df_meas["GyroX"], label="GyroX")
    ax.plot(t, df_meas["GyroY"], label="GyroY")
    ax.plot(t, df_meas["GyroZ"], label="GyroZ")
    ax.set_title(f"{title_prefix} Gyroscope")
    ax.set_ylabel("Angular velocity (dps)")
    ax.legend(loc="upper right")

    ax = axes[2]
    ax.plot(t, df_meas["MagnX"], label="MagnX")
    ax.plot(t, df_meas["MagnY"], label="MagnY")
    ax.plot(t, df_meas["MagnZ"], label="MagnZ")
    ax.set_title(f"{title_prefix} Magnetometer")
    ax.set_ylabel("Magnetic field")
    ax.legend(loc="upper right")

    ax = axes[3]
    ax.plot(t, df_angles["KneeAngle_fused_filt_deg"], label="Fused flex (filt)", linewidth=2)
    ax.plot(t, df_angles["KneeAngle_fused_deg"], label="Flex raw", alpha=0.3)
    ax.set_title("Knee flexion angle")
    ax.set_ylabel("Angle (deg)")
    ax.legend(loc="upper right")

    ax = axes[4]
    ax.plot(t, df_angles["KneeValgus_filt_deg"], label="Valgus/varus (filt)", linewidth=2)
    ax.axhline(0.0, linestyle="--", alpha=0.3, label="Neutral")
    ax.set_title("Knee valgus/varus angle")
    ax.set_ylabel("Angle (deg)")
    ax.set_xlabel("Time (s)")
    ax.legend(loc="upper right")

    fig.tight_layout()
    plt.show()


def main():
    print("=== AIMA 2 (flat) pipeline ===")

    os.makedirs(SESSIONS_DIR, exist_ok=True)
    os.makedirs(METRICS_DIR, exist_ok=True)
    os.makedirs(FEATURES_DIR, exist_ok=True)

    session_label = input("Метка этой сессии (good / valgus / fast / ...): ").strip() or "unlabeled"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{session_label}_{timestamp}"

    # --- 1. Калибровка ---
    df_calib = record_calibration_segment()
    calib = compute_imu_offsets(df_calib)

    # --- 2. Основное измерение ---
    print(f"\nТеперь запишем основное измерение (~{REC_LENGTH_SEC} секунд).")
    input("Когда будешь готов выполнять движение, нажми ENTER...")

    recorder = AimaMoveSenseRecorder(
        rec_length_sec=REC_LENGTH_SEC,
        filename_prefix="measurement"
    )
    df_meas = recorder.record_once_to_pandas()

    print("\n=== MAIN MEASUREMENT ===")
    print("Shape:", df_meas.shape)
    print(df_meas.head())

    # --- 3. Обработка ---
    df_proc = preprocess_main_measurement(df_meas, calib)
    print("\n=== After processing (df_proc) ===")
    print(df_proc.head())

    # --- 4. Кватернионы и углы ---
    quats = compute_quaternions(df_proc)
    df_angles = compute_knee_angles(df_proc, quats)

    print("\n=== Knee angles computed ===")
    print(df_angles[[
        "KneeAngle_fused_deg",
        "KneeAngle_fused_filt_deg",
        "KneeValgus_fused_deg",
        "KneeValgus_filt_deg",
    ]].head())

    # --- 5. Поиск повторов по гиро ---
    peaks = detect_reps_gyro(
        df_proc,
        gyro_col="GyroZ_corr",
        samplerate_hz=MOVESENSE_SAMPLERATE_HZ,
    )

    if len(peaks) == 0:
        print("\n❗ Повторов не найдено — попробуй сделать более выраженные сгибания.")
        plot_all(df_meas, df_angles)
        return

    print(f"\nНайдено повторений: {len(peaks)}")
    print("Индексы пиков:", peaks)

    # --- 6. Метрики по репам ---
    df_metrics = compute_rep_metrics(
        df_angles,
        peaks,
        samplerate_hz=MOVESENSE_SAMPLERATE_HZ,
    )

    print("\n=== METRICS ===")
    print(df_metrics)

    # --- 7. Фичи сессии ---
    session_feats = session_features_from_metrics(
        df_metrics,
        df_angles,
        samplerate_hz=MOVESENSE_SAMPLERATE_HZ,
    )

    print("\n=== SESSION FEATURES (for AI) ===")
    for k, v in session_feats.items():
        print(f"{k}: {v:.3f}")

    # --- 8. Сохранения CSV ---
    feats_path = os.path.join(FEATURES_DIR, f"features_{base_name}.csv")
    pd.DataFrame([session_feats]).to_csv(feats_path, index=False)
    print(f"\nФичи сохранены в {feats_path}")

    metrics_path = os.path.join(METRICS_DIR, f"metrics_{base_name}.csv")
    df_metrics.to_csv(metrics_path, index=False)
    print(f"Метрики сохранены в {metrics_path}")

    angles_path = os.path.join(SESSIONS_DIR, f"angles_{base_name}.csv")
    df_angles.to_csv(angles_path, index=False)
    print(f"Углы сохранены в {angles_path}")

    # --- 9. Rule-based оценка ---
    ai_result = evaluate_technique(session_feats)
    print("\n=== AI EVALUATION (rule-based) ===")
    print(f"Сводный балл: {ai_result['score']} / 100")
    print(f"Класс: {ai_result['label']}")
    print("Комментарии:")
    for c in ai_result["comments"]:
        print(" -", c)

    # --- 10. 1D-CNN оценка ---
    try:
        model, device = load_cnn_model()
        cnn_res = classify_reps_cnn(df_angles, df_metrics, model, device)

        print("\n=== AI EVALUATION (1D-CNN) ===")
        counts = cnn_res["counts"]
        per_rep = cnn_res["per_rep"]
        dominant = cnn_res["dominant_class"]

        print("Распределение классов по повторам:")
        for name in ["good", "valgus", "fast"]:
            if name in counts:
                print(f"  {name}: {counts[name]} rep")

        if dominant is not None:
            print(f"\nДоминирующий класс по CNN: {dominant}")

        print("\nПервые 5 повторов (предсказания CNN):")
        for r in per_rep[:5]:
            print(
                f"  rep {r['rep_id']:>2}: {r['pred_class']}"
                f"  (P_good={r['prob_good']:.2f},"
                f" P_valgus={r['prob_valgus']:.2f},"
                f" P_fast={r['prob_fast']:.2f})"
            )
    except Exception as e:
        print("\n[WARN] Не удалось выполнить 1D-CNN оценку:", e)

    plot_all(df_meas, df_angles)
    print("\nAIMA 2 (flat) pipeline done.")


if __name__ == "__main__":
    main()
