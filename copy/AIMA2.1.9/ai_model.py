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

LABEL_MAP = {"squat": 0, "walk": 1, "lateral": 2}
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
    df_proc: pd.DataFrame,
    df_metrics: pd.DataFrame,
    seq_len: int = SEQ_LEN,
    samplerate_hz: int = 104,
) -> np.ndarray:
    """
    Вырезает сегменты вокруг пиков для каждого повтора.
    Теперь каналы: [GyroZ_corr, AccNorm_filt] из df_proc.
    """

    # 1. Берём нужные сигналы из обработанного IMU-датафрейма
    gyro = df_proc["GyroZ_corr"].to_numpy()
    acc_norm = df_proc["AccNorm_filt"].to_numpy()

    n = len(df_proc)
    half_window = seq_len // 2
    segments = []

    # 2. Для каждого повтора вырезаем окно вокруг peak_index
    for _, row in df_metrics.iterrows():
        peak = int(row["peak_index"])
        start = max(0, peak - half_window)
        end = min(n, peak + half_window)

        seg_g = gyro[start:end]
        seg_a = acc_norm[start:end]

        # 3. Если сегмент короче, дополняем до seq_len значением на краю
        if len(seg_g) < seq_len:
            pad_len = seq_len - len(seg_g)
            seg_g = np.pad(seg_g, (0, pad_len), mode="edge")
            seg_a = np.pad(seg_a, (0, pad_len), mode="edge")

        # 4. Собираем [каналы, время]
        seg = np.stack([seg_g, seg_a], axis=0)
        segments.append(seg)

    if not segments:
        return np.empty((0, CHANNELS, seq_len), dtype=np.float32)

    return np.stack(segments).astype(np.float32)


def _extract_sliding_segments_for_cnn(
    df_proc: pd.DataFrame,
    seq_len: int = SEQ_LEN,
    step: int = 32,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Вырезает из df_proc скользящие окна фиксированной длины для 1D-CNN.
    Каналы: [GyroZ_corr, AccNorm_filt].

    Возвращает:
        segments: (n_windows, CHANNELS, seq_len)
        start_idx: (n_windows,) индексы начала окна
        end_idx:   (n_windows,) индексы конца (не включая)
        center_idx:(n_windows,) центр окна (для привязки ко времени)
    """
    gyro = df_proc["GyroZ_corr"].to_numpy()
    acc_norm = df_proc["AccNorm_filt"].to_numpy()

    n = len(df_proc)
    if n == 0:
        return (
            np.empty((0, CHANNELS, seq_len), dtype=np.float32),
            np.empty((0,), dtype=int),
            np.empty((0,), dtype=int),
            np.empty((0,), dtype=int),
        )

    segments = []
    start_idx = []
    end_idx = []
    center_idx = []

    # Если запись короче окна — паддим один сегмент
    if n < seq_len:
        pad_len = seq_len - n
        gyro_pad = np.pad(gyro, (0, pad_len), mode="edge")
        acc_pad = np.pad(acc_norm, (0, pad_len), mode="edge")
        seg = np.stack([gyro_pad, acc_pad], axis=0)
        segments.append(seg)
        start_idx.append(0)
        end_idx.append(seq_len)
        center_idx.append(seq_len // 2)
    else:
        start = 0
        while start + seq_len <= n:
            end = start + seq_len
            seg_g = gyro[start:end]
            seg_a = acc_norm[start:end]
            seg = np.stack([seg_g, seg_a], axis=0)

            segments.append(seg)
            start_idx.append(start)
            end_idx.append(end)
            center_idx.append((start + end) // 2)

            start += step  # шаг скользящего окна

    segments = np.stack(segments).astype(np.float32)
    start_idx = np.asarray(start_idx, dtype=int)
    end_idx = np.asarray(end_idx, dtype=int)
    center_idx = np.asarray(center_idx, dtype=int)

    return segments, start_idx, end_idx, center_idx


def classify_reps_cnn(
    df_proc: pd.DataFrame,
    df_metrics: pd.DataFrame,
    model: nn.Module,
    device: torch.device,
    seq_len: int = SEQ_LEN,
) -> dict:
    # Теперь вырезаем сегменты из df_proc (IMU)
    segments = _extract_rep_segments_for_cnn(df_proc, df_metrics, seq_len=seq_len)
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
            "prob_squat": float(p[LABEL_MAP["squat"]]),
            "prob_walk": float(p[LABEL_MAP["walk"]]),
            "prob_lateral": float(p[LABEL_MAP["lateral"]]),
        })

    dominant_class = max(counts.items(), key=lambda kv: kv[1])[0] if counts else None

    return {"counts": counts, "per_rep": per_rep, "dominant_class": dominant_class}


def classify_sequence_cnn(
    df_proc: pd.DataFrame,
    model: nn.Module,
    device: torch.device,
    seq_len: int = SEQ_LEN,
    step: int = 32,
) -> Dict[str, Any]:
    """
    Классификация движения по всей записи скользящими окнами.

    Возвращает:
        {
            "counts": {class_name: n_windows, ...},
            "per_window": [ {...}, ... ],
            "dominant_class": str | None,
        }
    """
    segments, start_idx, end_idx, center_idx = _extract_sliding_segments_for_cnn(
        df_proc, seq_len=seq_len, step=step
    )

    if segments.shape[0] == 0:
        return {"counts": {}, "per_window": [], "dominant_class": None}

    x = torch.from_numpy(segments).to(device)

    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1).cpu().numpy()

    per_window: List[Dict[str, Any]] = []
    counts = {name: 0 for name in LABEL_MAP.keys()}

    for i, p in enumerate(probs):
        idx = int(np.argmax(p))
        cls = IDX2LABEL[idx]
        counts[cls] += 1

        per_window.append({
            "window_id": int(i),
            "start_index": int(start_idx[i]),
            "end_index": int(end_idx[i]),
            "center_index": int(center_idx[i]),
            "pred_class": cls,
            "prob_squat": float(p[LABEL_MAP["squat"]]),
            "prob_walk": float(p[LABEL_MAP["walk"]]),
            "prob_lateral": float(p[LABEL_MAP["lateral"]]),
        })

    dominant_class = max(counts.items(), key=lambda kv: kv[1])[0] if counts else None

    return {
        "counts": counts,
        "per_window": per_window,
        "dominant_class": dominant_class,
    }
