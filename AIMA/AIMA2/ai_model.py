# ai_model.py

import os
from typing import Dict, Any, List

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

# === Конфиг CNN ===
SEQ_LEN = 128
CHANNELS = 2  # flex + valgus

LABEL_MAP = {"good": 0, "valgus": 1, "fast": 2}
IDX2LABEL = {v: k for k, v in LABEL_MAP.items()}


# ---------- Rule-based оценка ----------

def evaluate_technique(session_feats: Dict[str, float]) -> Dict[str, Any]:
    comments: List[str] = []
    score = 50

    n_reps = session_feats.get("n_reps", 0.0)
    flex_mean = session_feats.get("flex_mean_deg", 0.0)
    tempo = session_feats.get("tempo_reps_per_min", 0.0)
    valgus_rms = session_feats.get("valgus_rms_deg", 0.0)
    jerk_rms = session_feats.get("flex_jerk_rms", 0.0)

    if n_reps < 5:
        score -= 15
        comments.append("Небольшое количество повторений, но анализ возможен.")
    elif n_reps >= 10:
        score += 5
        comments.append("Хорошее количество повторений для анализа.")

    if flex_mean < 10:
        score -= 15
        comments.append("Глубина сгибания небольшая — присед скорее поверхностный.")
    elif flex_mean > 25:
        score += 5
        comments.append("Глубина сгибания в хорошем диапазоне.")
    else:
        comments.append("Глубина сгибания в комфортном диапазоне.")

    if tempo > 45:
        score -= 10
        comments.append("Приседания довольно быстрые — техника может страдать.")
    else:
        comments.append("Темп приседаний находится в комфортном диапазоне.")

    if valgus_rms < 10:
        score += 10
        comments.append("Очень небольшие боковые отклонения колена — отличная стабилизация.")
    elif valgus_rms > 25:
        score -= 15
        comments.append("Есть значительные отклонения — возможен varus/valgus и повышенная нагрузка на колено.")
    else:
        comments.append("Есть умеренные боковые отклонения колена — в пределах нормы.")

    if jerk_rms < 30:
        score += 5
        comments.append("Движение выглядит плавным.")
    else:
        comments.append("Движение довольно резкое — стоит смягчить амортизацию.")

    score = max(0, min(100, score))

    if score >= 70:
        label = "хорошая/приемлемая техника"
    elif score >= 40:
        label = "средняя техника"
    else:
        label = "проблемная техника"

    return {"score": score, "label": label, "comments": comments}


# ---------- 1D-CNN ----------

class Simple1DCNN(nn.Module):
    def __init__(self, in_channels: int = CHANNELS, seq_len: int = SEQ_LEN, n_classes: int = 3):
        super().__init__()
        self.conv1 = nn.Conv1d(in_channels, 16, kernel_size=5, padding=2)
        self.bn1 = nn.BatchNorm1d(16)
        self.conv2 = nn.Conv1d(16, 32, kernel_size=5, padding=2)
        self.bn2 = nn.BatchNorm1d(32)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.fc = nn.Linear(32, n_classes)

    def forward(self, x):
        x = torch.relu(self.bn1(self.conv1(x)))
        x = torch.relu(self.bn2(self.conv2(x)))
        x = self.pool(x).squeeze(-1)
        x = self.fc(x)
        return x


def load_cnn_model(
    model_path: str = "cnn_model.pth",
    in_channels: int = CHANNELS,
    seq_len: int = SEQ_LEN,
):
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Файл с моделью CNN не найден: {model_path}. "
            f"Сначала обучи модель (train_cnn.py)."
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = Simple1DCNN(in_channels=in_channels, seq_len=seq_len, n_classes=len(LABEL_MAP))
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    return model, device


def _extract_rep_segments_for_cnn(
    df_angles: pd.DataFrame,
    df_metrics: pd.DataFrame,
    seq_len: int = SEQ_LEN,
    samplerate_hz: int = 104,
) -> np.ndarray:
    """
    Вырезает сегменты вокруг пиков flexion для каждого повтора.
    Каналы: [flex, valgus].
    """
    flex = df_angles["KneeAngle_fused_filt_deg"].to_numpy()
    valgus = df_angles["KneeValgus_filt_deg"].to_numpy()
    n = len(df_angles)

    half_window = seq_len // 2
    segments = []

    for _, row in df_metrics.iterrows():
        peak = int(row["peak_index"])
        start = max(0, peak - half_window)
        end = min(n, peak + half_window)
        seg_f = flex[start:end]
        seg_v = valgus[start:end]

        if len(seg_f) < seq_len:
            pad_len = seq_len - len(seg_f)
            seg_f = np.pad(seg_f, (0, pad_len), mode="edge")
            seg_v = np.pad(seg_v, (0, pad_len), mode="edge")

        seg = np.stack([seg_f, seg_v], axis=0)
        segments.append(seg)

    if not segments:
        return np.empty((0, CHANNELS, seq_len), dtype=np.float32)

    return np.stack(segments).astype(np.float32)


def classify_reps_cnn(
    df_angles: pd.DataFrame,
    df_metrics: pd.DataFrame,
    model: nn.Module,
    device: torch.device,
    seq_len: int = SEQ_LEN,
) -> dict:
    segments = _extract_rep_segments_for_cnn(df_angles, df_metrics, seq_len=seq_len)
    if len(segments) == 0:
        return {"counts": {}, "per_rep": [], "dominant_class": None}

    x = torch.from_numpy(segments).to(device)
    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1).cpu().numpy()

    per_rep = []
    counts = {name: 0 for name in LABEL_MAP.keys()}

    for i, p in enumerate(probs):
        idx = int(np.argmax(p))
        cls = IDX2LABEL[idx]
        counts[cls] += 1

        per_rep.append({
            "rep_id": int(i + 1),
            "pred_class": cls,
            "prob_good": float(p[LABEL_MAP["good"]]),
            "prob_valgus": float(p[LABEL_MAP["valgus"]]),
            "prob_fast": float(p[LABEL_MAP["fast"]]),
        })

    dominant_class = max(counts.items(), key=lambda kv: kv[1])[0] if counts else None

    return {"counts": counts, "per_rep": per_rep, "dominant_class": dominant_class}
