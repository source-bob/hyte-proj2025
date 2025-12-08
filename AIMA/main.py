# main.py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

from ai_model import evaluate_technique, load_cnn_model, classify_reps_cnn
from datetime import datetime
from features import session_features_from_metrics
from processing import preprocess_main_measurement
from metrics import detect_reps_from_angle, compute_rep_metrics
from angles import compute_knee_flexion_angles
from sensor_io import AimaMoveSenseRecorder
from config import MOVESENSE_SAMPLERATE_HZ, REC_LENGTH_SEC
from calibration import record_calibration_segment, compute_imu_offsets


def plot_all_in_one_window(df_meas, df_angles, title_prefix="Main measurement"):
    """
    Рисует всё в одном окне:
      1) Acc X/Y/Z
      2) Gyro X/Y/Z
      3) Magn X/Y/Z
      4) Knee flexion (fused)
      5) Knee valgus/varus
    """

    n = len(df_meas)
    t = np.arange(n) / MOVESENSE_SAMPLERATE_HZ

    fig, axes = plt.subplots(5, 1, figsize=(10, 14), sharex=True)

    # ---- 1. Acc ----
    ax_acc = axes[0]
    ax_acc.plot(t, df_meas["AccX"], label="AccX")
    ax_acc.plot(t, df_meas["AccY"], label="AccY")
    ax_acc.plot(t, df_meas["AccZ"], label="AccZ")
    ax_acc.set_title(f"{title_prefix} Accelerometer")
    ax_acc.set_ylabel("Acceleration (g)")
    ax_acc.legend(loc="upper right")

    # ---- 2. Gyro ----
    ax_gyro = axes[1]
    ax_gyro.plot(t, df_meas["GyroX"], label="GyroX")
    ax_gyro.plot(t, df_meas["GyroY"], label="GyroY")
    ax_gyro.plot(t, df_meas["GyroZ"], label="GyroZ")
    ax_gyro.set_title(f"{title_prefix} Gyroscope")
    ax_gyro.set_ylabel("Angular velocity")
    ax_gyro.legend(loc="upper right")

    # ---- 3. Magn ----
    ax_magn = axes[2]
    if all(col in df_meas.columns for col in ["MagnX", "MagnY", "MagnZ"]):
        ax_magn.plot(t, df_meas["MagnX"], label="MagnX")
        ax_magn.plot(t, df_meas["MagnY"], label="MagnY")
        ax_magn.plot(t, df_meas["MagnZ"], label="MagnZ")
    ax_magn.set_title(f"{title_prefix} Magnetometer")
    ax_magn.set_ylabel("Magnetic field")
    ax_magn.legend(loc="upper right")

    # ---- 4. Knee flexion ----
    ax_flex = axes[3]

    # основной канал – fused (фильтрованный) угол
    if "KneeAngle_fused_filt_deg" in df_angles.columns:
        ax_flex.plot(
            t,
            df_angles["KneeAngle_fused_filt_deg"],
            label="Fused angle (filtered)",
            linewidth=2,
        )
    elif "KneeAngle_fused_deg" in df_angles.columns:
        ax_flex.plot(
            t,
            df_angles["KneeAngle_fused_deg"],
            label="Fused angle",
            linewidth=2,
        )

    # если в будущем захочется, можно дополнительно рисовать raw pitch:
    if "Pitch_raw" in df_angles.columns:
        ax_flex.plot(
            t,
            df_angles["Pitch_raw"],
            label="Pitch (raw, from quat)",
            alpha=0.3,
        )

    ax_flex.set_title("Knee flexion angle")
    ax_flex.set_ylabel("Angle (deg)")
    ax_flex.legend(loc="upper right")

    # ---- 5. Valgus/varus ----
    ax_valgus = axes[4]
    if "KneeValgus_filt_deg" in df_angles.columns:
        ax_valgus.plot(
            t,
            df_angles["KneeValgus_filt_deg"],
            label="Valgus/varus (filtered)",
            linewidth=2,
        )
    elif "KneeValgus_fused_deg" in df_angles.columns:
        ax_valgus.plot(
            t,
            df_angles["KneeValgus_fused_deg"],
            label="Valgus/varus (fused)",
            linewidth=2,
        )

    ax_valgus.axhline(0.0, linestyle="--", alpha=0.3, label="Neutral")
    ax_valgus.set_title("Knee valgus/varus angle")
    ax_valgus.set_ylabel("Angle (deg)")
    ax_valgus.set_xlabel("Time (s)")
    ax_valgus.legend(loc="upper right")

    fig.tight_layout()
    plt.show()


def main():
    print("AIMA pipeline start")

    # Метка сессии для последующего обучения CNN
    session_label = input(
        "\nВведи метку этой сессии (например: good / valgus / fast): "
    ).strip() or "unlabeled"

    # Таймстамп для уникальных имён файлов
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Базовое имя файлов
    base_name = f"{session_label}_{timestamp}"

    # Папки для датасета
    os.makedirs("data/sessions", exist_ok=True)
    os.makedirs("data/metrics", exist_ok=True)
    os.makedirs("data/features", exist_ok=True)

    # 1) Калибровка
    df_calib = record_calibration_segment()
    calib_params = compute_imu_offsets(df_calib)

    # 2) Основное измерение
    print(f"\nТеперь запишем основное измерение (~{REC_LENGTH_SEC} секунд).")
    input("Когда будешь готов выполнять движение, нажми ENTER...")

    recorder = AimaMoveSenseRecorder(
        rec_length_sec=REC_LENGTH_SEC,
        filename_prefix="measurement"
    )
    df_meas = recorder.record_once_to_pandas()

    print("\n=== MAIN MEASUREMENT ===")
    print("Shape:", df_meas.shape)
    print("Head:\n", df_meas.head())

    # 3) Обработка данных
    df_proc = preprocess_main_measurement(df_meas, calib_params)

    print("\n=== After processing (df_proc) ===")
    print("Columns:", df_proc.columns)
    print(df_proc.head())

    # 4) Вычисление углов
    df_angles = compute_knee_flexion_angles(df_proc, calib_params)

    print("\n=== Knee angle computed ===")
    cols_to_show = [
        c for c in [
            "KneeAngle_fused_deg",
            "KneeAngle_fused_filt_deg",
            "KneeValgus_fused_deg",
            "KneeValgus_filt_deg",
        ] if c in df_angles.columns
    ]
    print(df_angles[cols_to_show].head())

    # 5) Один общий график со всеми сигналами
    plot_all_in_one_window(df_meas, df_angles, title_prefix="Main measurement")

    # 6) Поиск повторений
    peaks = detect_reps_from_angle(
        df_angles,
        column="KneeAngle_fused_filt_deg",
        samplerate_hz=MOVESENSE_SAMPLERATE_HZ,
    )

    if len(peaks) == 0:
        print("\n❗ Повторов не найдено — попробуй сделать более выраженные сгибания колена.")
        print("AIMA pipeline finished gracefully.")
        return

    print(f"\nНайдено повторений: {len(peaks)}")
    print("Индексы пиков:", peaks)

    # 7) Подсчёт метрик
    df_metrics = compute_rep_metrics(
        df_angles,
        peaks,
        samplerate_hz=MOVESENSE_SAMPLERATE_HZ
    )

    print("\n=== METRICS ===")
    print(df_metrics)

    # 8a) Признаки для AI-модели
    session_feats = session_features_from_metrics(
        df_metrics,
        df_angles,
        samplerate_hz=MOVESENSE_SAMPLERATE_HZ,
    )
    print("\n=== SESSION FEATURES (for AI) ===")
    for k, v in session_feats.items():
        print(f"{k}: {v:.3f}")

    # Сохраняем фичи с меткой сессии
    df_feats = pd.DataFrame([session_feats])
    feats_path = os.path.join("data", "features", f"features_{base_name}.csv")
    df_feats.to_csv(feats_path, index=False)
    print(f"\nФичи сохранены в {feats_path}")

    # Сохраняем метрики
    metrics_path = os.path.join("data", "metrics", f"metrics_{base_name}.csv")
    df_metrics.to_csv(metrics_path, index=False)
    print(f"Метрики сохранены в {metrics_path}")

    # Дополнительно сохраняем весь угол во времени (для CNN)
    angles_path = os.path.join("data", "sessions", f"angles_{base_name}.csv")
    df_angles.to_csv(angles_path, index=False)
    print(f"Углы сохранены в {angles_path}")

    # 8b) Оценка техники «ИИ-моделью» (rule-based)
    ai_result = evaluate_technique(session_feats)
    print("\n=== AI EVALUATION (rule-based) ===")
    print(f"Сводный балл: {ai_result['score']} / 100")
    print(f"Класс: {ai_result['label']}")
    print("Комментарии:")
    for c in ai_result["comments"]:
        print(" -", c)

    # 9) Оценка техники нейросетью 1D-CNN
    try:
        model, device = load_cnn_model()
        cnn_result = classify_reps_cnn(df_angles, df_metrics, model, device)

        print("\n=== AI EVALUATION (1D-CNN) ===")
        counts = cnn_result["counts"]
        per_rep = cnn_result["per_rep"]
        dominant = cnn_result["dominant_class"]

        print("Распределение классов по повторам:")
        for cls_name in ["good", "valgus", "fast"]:
            if cls_name in counts:
                print(f"  {cls_name}: {counts[cls_name]} rep")

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

    print("\nAIMA pipeline done (record + calibration + processing + angle + reps).")


if __name__ == "__main__":
    main()
