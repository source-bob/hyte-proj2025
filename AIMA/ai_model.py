# ai_model.py

import os
from typing import List, Dict, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn


# === ПАРАМЕТРЫ CNN (должны совпадать с train_cnn.py) ===

SEQ_LEN = 128
CHANNELS = 2  # KneeAngle_fused_filt_deg + KneeValgus_filt_deg

LABEL_MAP: Dict[str, int] = {
    "good": 0,
    "valgus": 1,
    "fast": 2,
}
IDX2LABEL = {v: k for k, v in LABEL_MAP.items()}


# === 1. Rule-based оценка техники по session_features ===

def evaluate_technique_rule_based(session_features: Dict) -> Dict:
    """
    Простая интерпретируемая модель:
    на вход — словарь фичей (из features.session_features_from_metrics),
    на выход — score 0–100, класс и текстовые комментарии.
    """

    n_reps = session_features.get("n_reps", 0) or 0
    flex_max = abs(session_features.get("flex_max_deg", 0.0) or 0.0)
    tempo = session_features.get("tempo_reps_per_min", 0.0) or 0.0
    valgus_rms = abs(session_features.get("valgus_rms_deg", 0.0) or 0.0)
    jerk_rms = abs(session_features.get("flex_jerk_rms", 0.0) or 0.0)

    score = 50.0
    comments: List[str] = []

    # 1) Кол-во повторов
    if n_reps < 5:
        score -= 15
        comments.append("Мало повторений — анализ менее надёжен.")
    elif n_reps < 10:
        score -= 5
        comments.append("Небольшое количество повторений, но анализ возможен.")
    else:
        score += 5
        comments.append("Хорошее количество повторений для анализа.")

    # 2) Глубина сгибания
    if flex_max < 20:
        score -= 15
        comments.append("Глубина сгибания небольшая — присед скорее поверхностный.")
    elif flex_max < 40:
        score += 0
        comments.append("Глубина сгибания в комфортном диапазоне.")
    else:
        score += 5
        comments.append("Очень глубокие приседания — следи за комфортом коленей.")

    # 3) Темп
    if tempo < 15:
        comments.append("Темп приседаний довольно медленный.")
    elif tempo <= 40:
        score += 5
        comments.append("Темп приседаний находится в комфортном диапазоне.")
    else:
        score -= 10
        comments.append("Приседания слишком быстрые — техника может страдать.")

    # 4) Valgus/varus
    if valgus_rms < 15:
        score += 5
        comments.append("Очень небольшие боковые отклонения колена — отличная стабилизация.")
    elif valgus_rms < 30:
        comments.append("Есть умеренные боковые отклонения колена — в пределах нормы.")
    else:
        score -= 15
        comments.append("Есть значительные отклонения — возможен varus/valgus и повышенная нагрузка на колено.")

    # 5) Плавность (jerk)
    if jerk_rms < 80:
        score += 5
        comments.append("Движение выглядит очень плавным.")
    elif jerk_rms < 180:
        comments.append("Движение выглядит довольно плавным.")
    else:
        score -= 10
        comments.append("Движение довольно резкое — стоит смягчить амортизацию.")

    # Ограничим score
    score = max(0.0, min(100.0, score))

    if score >= 85:
        class_name = "отличная техника"
    elif score >= 65:
        class_name = "хорошая/приемлемая техника"
    elif score >= 45:
        class_name = "средняя техника"
    else:
        class_name = "проблемная техника"

    return {
        "score": score,
        "class_name": class_name,
        "label": class_name,
        "comments": comments,
    }


def evaluate_technique(session_features: Dict) -> Dict:
    """
    Обёртка — сейчас просто вызываем rule-based модель.
    Оставляем этот интерфейс, чтобы main.py не ломать.
    """
    res = evaluate_technique_rule_based(session_features)
    # на случай будущих изменений всегда гарантируем наличие "label"
    if "label" not in res:
        res["label"] = res.get("class_name", "unknown")
    return res


# === 2. Утилита ресэмплинга для CNN ===

def resample_sequence(seq: np.ndarray, target_len: int = SEQ_LEN) -> np.ndarray:
    """
    Линейная интерполяция временного ряда до фиксированной длины.
    seq: shape (N, C)
    out: shape (target_len, C)
    """
    n, c = seq.shape
    old_t = np.linspace(0.0, 1.0, n)
    new_t = np.linspace(0.0, 1.0, target_len)
    out = np.zeros((target_len, c), dtype=np.float32)
    for i in range(c):
        out[:, i] = np.interp(new_t, old_t, seq[:, i])
    return out


# === 3. Архитектура CNN (должна совпадать с train_cnn.py) ===

class SquatCNN(nn.Module):
    def __init__(self, channels: int = CHANNELS, n_classes: int = 3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(channels, 32, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.MaxPool1d(2),

            nn.Conv1d(32, 64, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.MaxPool1d(2),

            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveMaxPool1d(1),  # (B, 128, 1)

            nn.Flatten(),             # (B, 128)
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, n_classes),
        )

    def forward(self, x):
        return self.net(x)


def load_cnn_model(
    model_path: str = "models/aima_cnn.pt",
) -> Tuple[SquatCNN, torch.device]:
    """
    Загружаем обученную CNN с диска.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Не найден файл модели {model_path}. "
            f"Сначала запусти train_cnn.py."
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = SquatCNN()
    state_dict = torch.load(model_path, map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model, device


# === 4. Классификация повторений CNN ===

def classify_reps_cnn(
    df_angles: pd.DataFrame,
    df_metrics: pd.DataFrame,
    model: SquatCNN,
    device: torch.device,
) -> Dict:
    """
    На вход:
      - df_angles: полный временной ряд углов (KneeAngle_fused_filt_deg, KneeValgus_filt_deg и т.д.)
      - df_metrics: таблица повторов (rep_start_idx, rep_end_idx, rep_id, ...)

    На выход:
      - словарь с:
          'per_rep': список словарей по каждому повтору
          'counts': сколько повторов каждого класса
          'dominant_class': класс-победитель (string)
    """

    samples = []
    rep_ids = []

    for _, row in df_metrics.iterrows():
        s = int(row["rep_start_idx"])
        e = int(row["rep_end_idx"])
        if e <= s + 5:
            continue

        seg = df_angles.iloc[s:e]

        if "KneeAngle_fused_filt_deg" not in seg.columns or \
           "KneeValgus_filt_deg" not in seg.columns:
            raise RuntimeError(
                "В df_angles нет колонок KneeAngle_fused_filt_deg / KneeValgus_filt_deg."
            )

        sig = seg[["KneeAngle_fused_filt_deg",
                   "KneeValgus_filt_deg"]].to_numpy()
        x_resampled = resample_sequence(sig, SEQ_LEN)   # (T, C)
        samples.append(x_resampled.astype(np.float32))
        rep_ids.append(int(row.get("rep_id", len(rep_ids) + 1)))

    if not samples:
        return {
            "per_rep": [],
            "counts": {},
            "dominant_class": None,
        }

    x = np.stack(samples)                          # (N, T, C)
    x = np.transpose(x, (0, 2, 1))                 # (N, C, T)
    x_tensor = torch.from_numpy(x).to(device)

    with torch.no_grad():
        logits = model(x_tensor)                   # (N, 3)
        probs = torch.softmax(logits, dim=1).cpu().numpy()
        preds = np.argmax(probs, axis=1)

    per_rep = []
    counts: Dict[str, int] = {name: 0 for name in LABEL_MAP.keys()}

    for rep_id, y_idx, p in zip(rep_ids, preds, probs):
        label_str = IDX2LABEL[int(y_idx)]
        counts[label_str] += 1
        per_rep.append({
            "rep_id": rep_id,
            "pred_class": label_str,
            "prob_good": float(p[LABEL_MAP["good"]]),
            "prob_valgus": float(p[LABEL_MAP["valgus"]]),
            "prob_fast": float(p[LABEL_MAP["fast"]]),
        })

    # определим доминирующий класс по большинству
    dominant_class = None
    if counts:
        dominant_class = max(counts.items(), key=lambda kv: kv[1])[0]

    return {
        "per_rep": per_rep,
        "counts": counts,
        "dominant_class": dominant_class,
    }
