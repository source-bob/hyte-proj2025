# features.py

import numpy as np
import pandas as pd


def session_features_from_metrics(
    df_metrics: pd.DataFrame,
    df_angles: pd.DataFrame,
    samplerate_hz: int = 104,
) -> dict:
    """
    Агрегированные признаки по сессии (для rule-based и дальнейшего обучения CNN).
    """

    feats = {}
    n_reps = len(df_metrics)
    feats["n_reps"] = float(n_reps)

    keys_zero = [
        "flex_max_deg", "flex_mean_deg", "flex_std_deg",
        "rep_duration_mean", "rep_duration_std", "tempo_reps_per_min",
        "valgus_mean_deg", "valgus_std_deg",
        "valgus_min_deg", "valgus_max_deg", "valgus_rms_deg",
        "flex_vel_rms", "flex_jerk_rms",
    ]

    if n_reps == 0:
        for k in keys_zero:
            feats[k] = 0.0
        return feats

    flex = df_metrics["max_angle_deg"].to_numpy()
    feats["flex_max_deg"] = float(np.max(flex))
    feats["flex_mean_deg"] = float(np.mean(flex))
    feats["flex_std_deg"] = float(np.std(flex))

    dur = df_metrics["duration_sec"].to_numpy()
    feats["rep_duration_mean"] = float(np.mean(dur))
    feats["rep_duration_std"] = float(np.std(dur))

    total_time = len(df_angles) / samplerate_hz
    feats["tempo_reps_per_min"] = float(n_reps / total_time * 60.0)

    valgus = df_angles["KneeValgus_filt_deg"].to_numpy()
    feats["valgus_mean_deg"] = float(np.mean(valgus))
    feats["valgus_std_deg"] = float(np.std(valgus))
    feats["valgus_min_deg"] = float(np.min(valgus))
    feats["valgus_max_deg"] = float(np.max(valgus))
    feats["valgus_rms_deg"] = float(np.sqrt(np.mean(valgus ** 2)))

    flex_angle = df_angles["KneeAngle_fused_filt_deg"].to_numpy()
    vel = np.diff(flex_angle) * samplerate_hz
    jerk = np.diff(vel) * samplerate_hz
    feats["flex_vel_rms"] = float(np.sqrt(np.mean(vel ** 2)))
    feats["flex_jerk_rms"] = float(np.sqrt(np.mean(jerk ** 2)))

    return feats
