# train_cnn.py
#
# Обучение простой 1D-CNN по трём классам:
#   0 = good, 1 = valgus, 2 = fast

import os
import glob
from typing import List, Dict

import numpy as np
import pandas as pd

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split


# === Гиперпараметры ===

SEQ_LEN = 128          # длина окна (в сэмплах) на один rep
CHANNELS = 2           # используем 2 канала: flexion + valgus
BATCH_SIZE = 16
EPOCHS = 40
LR = 1e-3
RANDOM_SEED = 42


# === 1. Утилиты ===

def resample_sequence(seq: np.ndarray, target_len: int) -> np.ndarray:
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


# === 2. Dataset ===

class SquatDataset(Dataset):
    def __init__(
        self,
        sessions_root: str = "data/sessions",
        metrics_root: str = "data/metrics",
    ):
        self.samples: List[np.ndarray] = []
        self.labels: List[int] = []

        # маппинг строковых меток к классам
        self.label_map: Dict[str, int] = {
            "good": 0,
            "valgus": 1,
            "fast": 2,
        }

        angle_files = glob.glob(os.path.join(sessions_root, "angles_*.csv"))
        if not angle_files:
            raise RuntimeError(
                f"Не найдено файлов angles_*.csv в {sessions_root}. "
                "Сначала запусти main.py с разными session_label."
            )

        for angle_path in angle_files:
            fname = os.path.basename(angle_path)
            # ожидаем формат: angles_<label>_YYYYMMDD_....csv
            parts = fname.split("_")
            if len(parts) < 3:
                print(f"Пропускаю странное имя файла: {fname}")
                continue

            label_str = parts[1]
            if label_str not in self.label_map:
                print(f"Неизвестный label '{label_str}' в {fname}, пропускаю.")
                continue
            y = self.label_map[label_str]

            # строим соответствующее имя для metrics-файла
            base = fname.replace("angles_", "").replace(".csv", "")
            metrics_path = os.path.join(metrics_root, f"metrics_{base}.csv")
            if not os.path.exists(metrics_path):
                print(f"Нет metrics для {fname}, ожидалось: {metrics_path}")
                continue

            # читаем данные
            df_angles = pd.read_csv(angle_path)
            df_metrics = pd.read_csv(metrics_path)

            # на каждый rep вырезаем сегмент по индексам
            for _, row in df_metrics.iterrows():
                s = int(row["rep_start_idx"])
                e = int(row["rep_end_idx"])
                if e <= s + 5:
                    continue

                seg = df_angles.iloc[s:e]

                # берём два канала: сгибание и valgus/varus
                if "KneeAngle_fused_filt_deg" not in seg.columns or \
                   "KneeValgus_filt_deg" not in seg.columns:
                    raise RuntimeError(
                        "В df_angles нет нужных колонок "
                        "KneeAngle_fused_filt_deg / KneeValgus_filt_deg."
                    )

                sig = seg[["KneeAngle_fused_filt_deg",
                           "KneeValgus_filt_deg"]].to_numpy()

                # приводим к фиксированной длине
                x_resampled = resample_sequence(sig, SEQ_LEN)  # (SEQ_LEN, 2)

                self.samples.append(x_resampled.astype(np.float32))
                self.labels.append(y)

        if not self.samples:
            raise RuntimeError("Не удалось собрать ни одного сэмпла для датасета.")

        self.samples = np.stack(self.samples)   # (N, SEQ_LEN, CHANNELS)
        self.labels = np.array(self.labels, dtype=np.int64)

        print(f"Собрано сэмплов: {self.samples.shape[0]}")
        for name, idx in self.label_map.items():
            count = int((self.labels == idx).sum())
            print(f"  класс {idx} ({name}): {count} rep-сэмплов")

    def __len__(self):
        return self.samples.shape[0]

    def __getitem__(self, idx):
        x = self.samples[idx]              # (T, C)
        x = np.transpose(x, (1, 0))        # -> (C, T) для Conv1d
        y = self.labels[idx]
        return torch.from_numpy(x), torch.tensor(y, dtype=torch.long)


# === 3. Модель 1D-CNN ===

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


# === 4. Обучение ===

def train():
    torch.manual_seed(RANDOM_SEED)

    dataset = SquatDataset()
    n_total = len(dataset)
    print("Всего rep-сэмплов:", n_total)

    if n_total < 9:
        print("Очень мало данных (<9 сэмплов). CNN обучится, но будет чисто демонстрационной.")
    train_size = int(0.8 * n_total)
    val_size = n_total - train_size
    if val_size == 0:
        val_size = 1
        train_size = n_total - 1

    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Используем устройство:", device)

    model = SquatCNN().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0.0

        for x, y in train_loader:
            x = x.to(device)
            y = y.to(device)

            optimizer.zero_grad()
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * x.size(0)

        avg_loss = total_loss / train_size

        # валидация
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for x, y in val_loader:
                x = x.to(device)
                y = y.to(device)
                logits = model(x)
                preds = torch.argmax(logits, dim=1)
                correct += (preds == y).sum().item()
                total += y.size(0)

        val_acc = correct / total if total > 0 else 0.0
        print(f"Epoch {epoch+1}/{EPOCHS}  loss={avg_loss:.4f}  val_acc={val_acc:.3f}")

    # сохраняем модель
    os.makedirs("models", exist_ok=True)
    model_path = os.path.join("models", "aima_cnn.pt")
    torch.save(model.state_dict(), model_path)
    print(f"\n✅ Модель сохранена в: {model_path}")


if __name__ == "__main__":
    train()
