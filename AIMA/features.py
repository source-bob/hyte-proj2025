# features.py

import numpy as np
import pandas as pd


def session_features_from_metrics(
    df_metrics: pd.DataFrame,
    df_angles: pd.DataFrame,
    samplerate_hz: int = 104,
) -> dict:
    """
    Строит набор признаков (features) для всей сессии на основе:
      - метрик по повторениям (df_metrics)
      - углов во времени (df_angles)

    Эти признаки потом можно скормить ML-модели.
    """

    feats: dict[str, float] = {}

    # ------ 1. Базовые характеристики повторов ------

    n_reps = len(df_metrics)
    feats["n_reps"] = float(n_reps)

    if n_reps > 0:
        max_flex = df_metrics["max_angle_deg"].max()
        mean_flex = df_metrics["max_angle_deg"].mean()
        std_flex = df_metrics["max_angle_deg"].std(ddof=0)

        mean_dur = df_metrics["duration_sec"].mean()
        std_dur = df_metrics["duration_sec"].std(ddof=0)

        feats["flex_max_deg"] = float(max_flex)
        feats["flex_mean_deg"] = float(mean_flex)
        feats["flex_std_deg"] = float(std_flex if not np.isnan(std_flex) else 0.0)

        feats["rep_duration_mean"] = float(mean_dur)
        feats["rep_duration_std"] = float(std_dur if not np.isnan(std_dur) else 0.0)

        # Tempo ~ reps per minute
        total_time = df_metrics["t_peak_sec"].max() - df_metrics["t_peak_sec"].min()
        if total_time > 0:
            feats["tempo_reps_per_min"] = float(n_reps / total_time * 60.0)
        else:
            feats["tempo_reps_per_min"] = 0.0
    else:
        # fallback, если вдруг нет повторов
        feats.update({
            "flex_max_deg": 0.0,
            "flex_mean_deg": 0.0,
            "flex_std_deg": 0.0,
            "rep_duration_mean": 0.0,
            "rep_duration_std": 0.0,
            "tempo_reps_per_min": 0.0,
        })

    # ------ 2. Valgus/varus стабильность ------

    if "KneeValgus_filt_deg" in df_angles.columns:
        valgus = df_angles["KneeValgus_filt_deg"].to_numpy()

        feats["valgus_mean_deg"] = float(np.nanmean(valgus))
        feats["valgus_std_deg"] = float(np.nanstd(valgus))
        feats["valgus_min_deg"] = float(np.nanmin(valgus))
        feats["valgus_max_deg"] = float(np.nanmax(valgus))

        # RMS (root mean square) как индекс "общей латеральной активности"
        feats["valgus_rms_deg"] = float(np.sqrt(np.nanmean(valgus**2)))
    else:
        feats.update({
            "valgus_mean_deg": 0.0,
            "valgus_std_deg": 0.0,
            "valgus_min_deg": 0.0,
            "valgus_max_deg": 0.0,
            "valgus_rms_deg": 0.0,
        })

    # ------ 3. Flexion smoothness (по fused углу) ------

    if "KneeAngle_fused_filt_deg" in df_angles.columns:
        ang = df_angles["KneeAngle_fused_filt_deg"].to_numpy()
        # производная как "скорость"
        vel = np.diff(ang) * samplerate_hz
        jerks = np.diff(vel) * samplerate_hz

        feats["flex_vel_rms"] = float(np.sqrt(np.nanmean(vel**2))) if len(vel) > 0 else 0.0
        feats["flex_jerk_rms"] = float(np.sqrt(np.nanmean(jerks**2))) if len(jerks) > 0 else 0.0
    else:
        feats["flex_vel_rms"] = 0.0
        feats["flex_jerk_rms"] = 0.0

    return feats
