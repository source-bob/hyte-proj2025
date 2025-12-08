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
    classify_sequence_cnn,
)
from segmentation import segment_movement



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
    print("=== AI Motion Analyzer (AIMA2) – prototyyppi ===")


    os.makedirs(SESSIONS_DIR, exist_ok=True)
    os.makedirs(METRICS_DIR, exist_ok=True)
    os.makedirs(FEATURES_DIR, exist_ok=True)

    session_label = input("Syötä session tunniste (esim. H1, H2, H3 + lyhyt kuvaus): ").strip() or "unlabeled"

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

    
    # --- 5. Определение типа движения через CNN (если модель есть) ---
    movement_class = None
    try:
        model, device = load_cnn_model()
        seq_res = classify_sequence_cnn(df_proc, model, device)
        movement_class = seq_res["dominant_class"]
    except:
        movement_class = None

    if movement_class is None:
        print("\n[INFO] CNN недоступен или не распознал движение — предполагаем squat")
        movement_class = "squat"

    print(f"\nTunnistettu liike (CNN tai fallback): {movement_class}")

    # --- 6. Сегментация движения ---
    peaks = segment_movement(df_proc, df_angles, movement_class)

    if len(peaks) == 0:
        print("\n❗ Повторы не найдены после сегментации.")
        plot_all(df_meas, df_angles)
        return

    print(f"Найдено сегментов ({movement_class}): {len(peaks)}")
    print("Индексы:", peaks)


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
    # Добавляем session_id, чтобы потом легко строить таблицы для Tulokset
    session_id = base_name  # включает и метку, и timestamp

    feats_path = os.path.join(FEATURES_DIR, f"features_{base_name}.csv")
    df_feats = pd.DataFrame([session_feats])
    df_feats.insert(0, "session_id", session_id)
    df_feats.to_csv(feats_path, index=False)
    print(f"\nФичи сохранены в {feats_path}")

    metrics_path = os.path.join(METRICS_DIR, f"metrics_{base_name}.csv")
    df_metrics_out = df_metrics.copy()
    df_metrics_out.insert(0, "session_id", session_id)
    df_metrics_out.to_csv(metrics_path, index=False)
    print(f"Метрики сохранены в {metrics_path}")

    angles_path = os.path.join(SESSIONS_DIR, f"angles_{base_name}.csv")
    df_angles_out = df_angles.copy()
    df_angles_out.insert(0, "session_id", session_id)
    df_angles_out.to_csv(angles_path, index=False)
    print(f"Углы сохранены в {angles_path}")

    # Сохраняем также обработанный IMU-сигнал (df_proc) для обучения CNN
    proc_path = os.path.join(SESSIONS_DIR, f"proc_{base_name}.csv")
    df_proc_out = df_proc.copy()
    df_proc_out.insert(0, "session_id", session_id)
    df_proc_out.to_csv(proc_path, index=False)
    print(f"Обработанный IMU-сигнал сохранён в {proc_path}")

    
    # --- 9. Клинически значимые метрики (без rule-based балла) ---
    print("\n=== Kliiniset perusmittarit (kulmat ja tempo) ===")

    # 1) Флексия колена
    flex_max = session_feats["flex_max_deg"]
    flex_mean = session_feats["flex_mean_deg"]
    print(f"Polven maksimi fleksio: {flex_max:.1f}°")
    print(f"Polven keskimääräinen fleksio: {flex_mean:.1f}°")

    # 2) Varus/valgus-положение
    valgus_mean = session_feats["valgus_mean_deg"]
    valgus_min = session_feats["valgus_min_deg"]
    valgus_max = session_feats["valgus_max_deg"]
    print(f"Varus/valgus-kulman keskiarvo: {valgus_mean:.1f}°")
    print(f"Varus/valgus-kulman minimi: {valgus_min:.1f}°")
    print(f"Varus/valgus-kulман maksimi: {valgus_max:.1f}°")

    # 3) Темп и длительность
    tempo = session_feats["tempo_reps_per_min"]
    rep_dur_mean = session_feats["rep_duration_mean"]
    rep_dur_std = session_feats["rep_duration_std"]
    print(f"Tempo: {tempo:.1f} toistoa/min")
    print(f"Toiston keskimääräinen kesto: {rep_dur_mean:.2f} s (± {rep_dur_std:.2f} s)")

    # 4) Немного “качества движения” без числа 0–100
    flex_vel_rms = session_feats["flex_vel_rms"]
    flex_jerk_rms = session_feats["flex_jerk_rms"]
    print(f"Liikkeen nopeuden RMS (fleksio): {flex_vel_rms:.2f} °/s")
    print(f"Liikkeen jerk RMS (fleksio): {flex_jerk_rms:.2f} °/s²")


    # --- 10. 1D-CNN оценка ---
    try:
        model, device = load_cnn_model()

        # 10a. Автоклассификация движения по всей записи (sliding window)
        seq_res = classify_sequence_cnn(df_proc, model, device)

        print("\n=== AI MOVEMENT TYPE (1D-CNN, sliding windows) ===")
        if seq_res["dominant_class"] is not None:
            dom = seq_res["dominant_class"]
            print(f"Tunnistettu liike (1D-CNN): {dom}")
        else:
            print("Liiketyyppiä ei voitu tunnistaa (ei tarpeeksi dataa).")

        counts_seq = seq_res["counts"]
        print("Ikkunajakauma (class per window):")
        for name in ["squat", "walk", "lateral"]:
            if name in counts_seq and counts_seq[name] > 0:
                print(f"  {name}: {counts_seq[name]} ikkunaa")

        # 10b. Классификация по отдельным повторам (как раньше, но на df_proc)
        cnn_res = classify_reps_cnn(df_proc, df_metrics, model, device)

        print("\n=== AI EVALUATION (1D-CNN per rep) ===")
        counts = cnn_res["counts"]
        per_rep = cnn_res["per_rep"]
        dominant = cnn_res["dominant_class"]

        print("Распределение классов по повторам:")
        for name in ["squat", "walk", "lateral"]:
            if name in counts:
                print(f"  {name}: {counts[name]} rep")

        if dominant is not None:
            print(f"\nДоминирующий класс по CNN (per rep): {dominant}")

        print("\nПервые 5 повторов (предсказания CNN):")
        for r in per_rep[:5]:
            print(
                f"  rep {r['rep_id']:>2}: {r['pred_class']}"
                f"  (P_squat={r['prob_squat']:.2f},"
                f" P_walk={r['prob_walk']:.2f},"
                f" P_lateral={r['prob_lateral']:.2f})"
            )
        
        # --- 10c. Сохранение результатов CNN в CSV ---
        # per_rep -> отдельный файл с оценкой каждого повтора
        session_id = base_name

        reps_cnn_path = os.path.join(SESSIONS_DIR, f"reps_cnn_{base_name}.csv")
        df_reps_cnn = pd.DataFrame(per_rep)
        df_reps_cnn.insert(0, "session_id", session_id)
        df_reps_cnn.to_csv(reps_cnn_path, index=False)
        print(f"\nCNN-per-rep tulokset tallennettu: {reps_cnn_path}")

        windows_cnn_path = os.path.join(SESSIONS_DIR, f"windows_cnn_{base_name}.csv")
        df_windows_cnn = pd.DataFrame(seq_res["per_window"])
        df_windows_cnn.insert(0, "session_id", session_id)
        df_windows_cnn.to_csv(windows_cnn_path, index=False)
        print(f"CNN sliding-window tulokset tallennettu: {windows_cnn_path}")


    except Exception as e:
        print("\n[WARN] Не удалось выполнить 1D-CNN оценку:", e)


    plot_all(df_meas, df_angles)
    print("\nAIMA2-putki valmis.")



if __name__ == "__main__":
    main()
