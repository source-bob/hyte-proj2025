# features.py

import numpy as np
import pandas as pd

# Кандидаты на колонку с углом сгибания колена
FLEX_COL_CANDIDATES = [
    "KneeAngle_fused_filt_deg",  # старое имя
    "KneeAngle_filt_deg",        # новое из angles.py
    "KneeFlex_filt_deg",         # на всякий случай
    "Flex_filt",                 # если где-то уже скопировано
]

def get_flex_column_name(df_angles: pd.DataFrame) -> str:
    """Находит колонку с углом сгибания колена.

    Мы поддерживаем несколько вариантов имён (см. FLEX_COL_CANDIDATES),
    чтобы основной пайплайн и отладочные скрипты работали с одной и той же
    таблицей углов, независимо от мелких изменений имён колонок.
    """
    for col in FLEX_COL_CANDIDATES:
        if col in df_angles.columns:
            return col
    raise KeyError(
        f"No flexion angle column found in df_angles. "
        f"Available columns: {list(df_angles.columns)}"
    )


def session_features_from_metrics(
    df_metrics: pd.DataFrame,
    df_angles: pd.DataFrame,
    samplerate_hz: int = 104,
) -> dict:
    """Агрегированные признаки по сессии (для rule-based и CNN).

    df_metrics — одна строка на повтор, приходит из compute_rep_metrics.
    df_angles — покадровые углы из compute_knee_angles.
    """

    feats: dict[str, float] = {}
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

    # 1) Флексия (per-rep максимум уже посчитан в df_metrics)
    flex = df_metrics["max_angle_deg"].to_numpy()
    feats["flex_max_deg"]  = float(np.max(flex))
    feats["flex_mean_deg"] = float(np.mean(flex))
    feats["flex_std_deg"]  = float(np.std(flex))

    # 2) Длительность повторов
    dur = df_metrics["duration_sec"].to_numpy()
    feats["rep_duration_mean"] = float(np.mean(dur))
    feats["rep_duration_std"]  = float(np.std(dur))

    # 3) Темп (reps / min)
    total_time = len(df_angles) / samplerate_hz
    feats["tempo_reps_per_min"] = float(n_reps / total_time * 60.0) if total_time > 0 else 0.0

   
    # 4) Varus/valgus на уровне репов, если есть per-rep индекс
    if "valgus_rms_rep_deg" in df_metrics.columns:
        vals = df_metrics["valgus_rms_rep_deg"].dropna().to_numpy()
        if vals.size > 0:
            feats["valgus_mean_deg"] = float(np.mean(vals))
            feats["valgus_std_deg"]  = float(np.std(vals))
            feats["valgus_min_deg"]  = float(np.min(vals))
            feats["valgus_max_deg"]  = float(np.max(vals))
            feats["valgus_rms_deg"]  = float(np.sqrt(np.mean(vals ** 2)))
        else:
            for k in ["valgus_mean_deg","valgus_std_deg",
                    "valgus_min_deg","valgus_max_deg","valgus_rms_deg"]:
                feats[k] = 0.0
    else:
        # fallback на старое поведение, если вдруг нет per-rep индекса
        if "KneeValgus_filt_deg" in df_angles.columns:
            valgus = df_angles["KneeValgus_filt_deg"].to_numpy()
            feats["valgus_mean_deg"] = float(np.mean(valgus))
            feats["valgus_std_deg"]  = float(np.std(valgus))
            feats["valgus_min_deg"]  = float(np.min(valgus))
            feats["valgus_max_deg"]  = float(np.max(valgus))
            feats["valgus_rms_deg"]  = float(np.sqrt(np.mean(valgus ** 2)))
        else:
            for k in ["valgus_mean_deg","valgus_std_deg",
                    "valgus_min_deg","valgus_max_deg","valgus_rms_deg"]:
                feats[k] = 0.0


    # 5) Скорость и jerk по траектории флексии
    flex_col = get_flex_column_name(df_angles)
    flex_angle = df_angles[flex_col].to_numpy()

    if flex_angle.size >= 3:
        vel = np.diff(flex_angle) * samplerate_hz
        jerk = np.diff(vel) * samplerate_hz
        feats["flex_vel_rms"]  = float(np.sqrt(np.mean(vel ** 2)))
        feats["flex_jerk_rms"] = float(np.sqrt(np.mean(jerk ** 2)))
    else:
        feats["flex_vel_rms"]  = 0.0
        feats["flex_jerk_rms"] = 0.0

    return feats
