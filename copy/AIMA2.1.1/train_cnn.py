# train_cnn.py
"""
Обучение 1D-CNN для классификации типа движения (squat / walk / lateral)
по обработанным IMU-сигналам из df_proc.

Использует:
 - config.SESSIONS_DIR  (где лежат proc_*.csv)
 - ai_model.Simple1DCNN, SEQ_LEN, CHANNELS, LABEL_MAP
 - _extract_sliding_segments_for_cnn для формирования окон
"""

import os
import glob
from typing import List, Tuple, Dict, Any

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split
from torch.optim import Adam

from config import SESSIONS_DIR
from ai_model import (
    Simple1DCNN,
    SEQ_LEN,
    CHANNELS,
    LABEL_MAP,
    _extract_sliding_segments_for_cnn,
)


# ==========================
#   ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==========================

def infer_movement_from_session_label(session_label: str) -> str | None:
    """
    Пытаемся угадать класс движения по session_label.
    Ожидаем, что в нём содержится одно из слов: squat / walk / lateral.

    Примеры:
      H1_squat
      H2_walk
      H3_lateral_pre
    """
    s = session_label.lower()
    for cls_name in LABEL_MAP.keys():
        if cls_name in s:
            return cls_name
    return None


def parse_base_name_from_proc_filename(path: str) -> str:
    """
    proc_<session_label>_<timestamp>.csv -> <session_label>_<timestamp>
    """
    base = os.path.basename(path)
    assert base.startswith("proc_") and base.endswith(".csv")
    return base[len("proc_"):-4]


def split_session_label_and_timestamp(base_name: str) -> Tuple[str, str]:
    """
    <session_label>_<timestamp> -> (session_label, timestamp)
    timestamp формата YYYYMMDD_HHMMSS, поэтому отрезаем по последнему "_".
    """
    session_label, ts = base_name.rsplit("_", 1)
    return session_label, ts


# ==========================
#        DATASET
# ==========================

class IMUMovementDataset(Dataset):
    """
    Датасет скользящих окон IMU-сигналов для обучения CNN.

    Каждое окно:
      shape = (CHANNELS, SEQ_LEN)
      label = {0, 1, 2} по LABEL_MAP
    """

    def __init__(self, sessions_dir: str, seq_len: int = SEQ_LEN, step: int = 32):
        self.samples: List[Tuple[np.ndarray, int]] = []
        self.seq_len = seq_len
        self.step = step

        proc_pattern = os.path.join(sessions_dir, "proc_*.csv")
        proc_files = sorted(glob.glob(proc_pattern))

        if not proc_files:
            print(f"[WARN] Не найдено файлов {proc_pattern} — нечего обучать.")
            return

        print(f"[INFO] Найдено {len(proc_files)} файлов proc_*.csv")

        for path in proc_files:
            base_name = parse_base_name_from_proc_filename(path)
            session_label, ts = split_session_label_and_timestamp(base_name)

            movement = infer_movement_from_session_label(session_label)
            if movement is None:
                print(f"[INFO] Пропускаю {path} — не удалось определить класс движения.")
                continue

            label_idx = LABEL_MAP[movement]
            print(f"[INFO] Загружаю {path}, session_label={session_label}, movement={movement}")

            df_proc = pd.read_csv(path)

            # Убираем возможный столбец session_id
            if "session_id" in df_proc.columns:
                df_proc = df_proc.drop(columns=["session_id"])

            # Используем ту же функцию, что и в боевом коде
            segments, start_idx, end_idx, center_idx = _extract_sliding_segments_for_cnn(
                df_proc, seq_len=self.seq_len, step=self.step
            )

            # _extract_sliding_segments_for_cnn уже должен возвращать np.ndarray,
            # но на всякий случай проверим
            segments = np.asarray(segments, dtype=np.float32)

            if segments.shape[0] == 0:
                print(f"[INFO] В {path} не удалось извлечь ни одного окна — пропуск.")
                continue

            for seg in segments:
                # seg.shape = (CHANNELS, SEQ_LEN)
                self.samples.append((seg.astype(np.float32), label_idx))

        print(f"[INFO] Всего окон для обучения: {len(self.samples)}")

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        x, y = self.samples[idx]
        x_t = torch.from_numpy(x)  # (C, L)
        y_t = torch.tensor(y, dtype=torch.long)
        return x_t, y_t


# ==========================
#       ОБУЧЕНИЕ
# ==========================

def train_epoch(model, loader, criterion, optimizer, device) -> Tuple[float, float]:
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0

    for x, y in loader:
        x = x.to(device)
        y = y.to(device)

        optimizer.zero_grad()
        logits = model(x)
        loss = criterion(logits, y)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * x.size(0)

        preds = torch.argmax(logits, dim=1)
        correct += (preds == y).sum().item()
        total += y.size(0)

    avg_loss = total_loss / max(total, 1)
    acc = correct / max(total, 1)
    return avg_loss, acc


def eval_epoch(model, loader, criterion, device) -> Tuple[float, float]:
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            y = y.to(device)

            logits = model(x)
            loss = criterion(logits, y)

            total_loss += loss.item() * x.size(0)
            preds = torch.argmax(logits, dim=1)
            correct += (preds == y).sum().item()
            total += y.size(0)

    avg_loss = total_loss / max(total, 1)
    acc = correct / max(total, 1)
    return avg_loss, acc


def main():
    # 1. Готовим датасет
    dataset = IMUMovementDataset(SESSIONS_DIR, seq_len=SEQ_LEN, step=32)

    if len(dataset) == 0:
        print("[ERROR] В датасете нет образцов. Запиши несколько сессий (H1_squat, H1_walk, H1_lateral) и запусти снова.")
        return

    # 2. Делим на train/val
    val_ratio = 0.2
    n_total = len(dataset)
    n_val = max(1, int(n_total * val_ratio))
    n_train = n_total - n_val

    train_set, val_set = random_split(dataset, [n_train, n_val])
    print(f"[INFO] Train samples: {len(train_set)}, Val samples: {len(val_set)}")

    train_loader = DataLoader(train_set, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=64, shuffle=False)

    # 3. Модель, оптимизатор
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = Simple1DCNN(in_channels=CHANNELS, seq_len=SEQ_LEN, n_classes=len(LABEL_MAP))
    model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = Adam(model.parameters(), lr=1e-3)

    # 4. Обучение
    n_epochs = 25
    best_val_acc = 0.0
    best_state = None

    for epoch in range(1, n_epochs + 1):
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = eval_epoch(model, val_loader, criterion, device)

        print(
            f"Epoch {epoch:02d}/{n_epochs} | "
            f"train_loss={train_loss:.4f}, train_acc={train_acc:.3f} | "
            f"val_loss={val_loss:.4f}, val_acc={val_acc:.3f}"
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_state = model.state_dict().copy()

    if best_state is None:
        print("[WARN] Лучшая модель не зафиксирована, сохраняем последнюю версию.")
        best_state = model.state_dict()

    # 5. Сохраняем модель в файл, который читает load_cnn_model
    model_path = "cnn_model.pth"
    torch.save(best_state, model_path)
    print(f"[INFO] Лучшая модель сохранена в {model_path} (val_acc={best_val_acc:.3f})")


if __name__ == "__main__":
    main()
