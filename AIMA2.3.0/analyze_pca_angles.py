# analyze_pca_angles.py
"""
Offline-анализ PCA-осей для углов Pitch/Roll.

Что делает:
  - находит все файлы angles_*.csv в SESSIONS_DIR
  - для каждого:
      * читает Pitch_deg и Roll_deg
      * считает PCA по двум осям
      * проецирует сигнал на PC1/PC2
      * добавляет колонки:
          Flex_PCA_deg      (нефильтрованный PCA-flex)
          Flex_PCA_filt_deg (сглаженный PCA-flex)
          Valgus_PCA_deg      (нефильтрованный PCA-frontal)
          Valgus_PCA_filt_deg (сглаженный PCA-frontal)
      * сохраняет новый CSV с префиксом pca_*.csv
  - НИЧЕГО не меняет в исходных файлах и не используется в основном пайплайне.

Это чисто исследовательский инструмент: смотреть, как выглядят PCA-оси,
сравнивать с базовыми KneeAngle/KneeValgus и т.п.
"""

import os
import glob
from typing import Tuple

import numpy as np
import pandas as pd

from config import MOVESENSE_SAMPLERATE_HZ, SESSIONS_DIR  # пути и samplerate
from processing import lowpass_rolling  # для сглаживания PCA-сигналов


def _get_pitch_roll_matrix(
    df_angles: pd.DataFrame,
    columns: Tuple[str, str] = ("Pitch_deg", "Roll_deg"),
) -> np.ndarray:
    """
    Достаёт матрицу [Pitch, Roll] как float и убирает строки с NaN.
    Возвращает X_all (с NaN) и X_valid (без NaN) для PCA.
    """
    col1, col2 = columns
    if col1 not in df_angles.columns or col2 not in df_angles.columns:
        raise KeyError(
            f"Ожидались колонки {columns}, но в df_angles есть только: "
            f"{list(df_angles.columns)}"
        )

    X_all = df_angles[[col1, col2]].to_numpy(dtype=float)
    mask = np.all(np.isfinite(X_all), axis=1)
    X_valid = X_all[mask]

    return X_all, X_valid


def _compute_pca_components(X_valid: np.ndarray) -> np.ndarray:
    """
    Классический PCA через SVD для матрицы (N, 2).
    Возвращает матрицу компонентов shape (2, 2):
      components[0] = PC1 (flex)
      components[1] = PC2 (frontal)
    """
    if X_valid.shape[0] < 10:
        # Слишком мало данных — возвращаем единичную матрицу: PC1=Pitch, PC2=Roll
        return np.eye(2, dtype=float)

    # Центрируем
    Xc = X_valid - np.mean(X_valid, axis=0, keepdims=True)

    # SVD: Xc = U S V^T, строки Vt — компоненты
    _, _, Vt = np.linalg.svd(Xc, full_matrices=False)
    components = Vt.astype(float)

    return components


def _apply_pca_to_angles(
    df_angles: pd.DataFrame,
    components: np.ndarray,
    columns: Tuple[str, str] = ("Pitch_deg", "Roll_deg"),
    neutral_window_sec: float = 1.0,
    samplerate_hz: float = MOVESENSE_SAMPLERATE_HZ,
) -> pd.DataFrame:
    """
    Применяет PCA-компоненты к (Pitch, Roll) и добавляет новые колонки:
      Flex_PCA_deg, Flex_PCA_filt_deg,
      Valgus_PCA_deg, Valgus_PCA_filt_deg.

    Важно: НИЧЕГО не трогает в KneeAngle_*/KneeValgus_*.
    """
    df = df_angles.copy()

    col1, col2 = columns
    X_all = df[[col1, col2]].to_numpy(dtype=float)

    n = len(df)
    if n == 0:
        return df

    # Нейтральная поза — первые neutral_window_sec секунд (как в compute_knee_angles)
    n0 = int(round(neutral_window_sec * samplerate_hz))
    n0 = max(1, min(n0, n))
    base = np.mean(X_all[:n0, :], axis=0, keepdims=True)
    X_rel = X_all - base

    # Разворачиваем компоненты
    flex_w = components[0]   # PC1
    frontal_w = components[1]  # PC2

    # Проекции
    flex_pca = X_rel @ flex_w
    valgus_pca = X_rel @ frontal_w

    # Добавляем сырые PCA-сигналы
    df["Flex_PCA_deg"] = flex_pca
    df["Valgus_PCA_deg"] = valgus_pca

    # И сглаженные версии (по аналогии с KneeAngle_filt / KneeValgus_filt)
    df["Flex_PCA_filt_deg"] = lowpass_rolling(
        df,
        "Flex_PCA_deg",
        window_sec=0.25,
        samplerate_hz=int(samplerate_hz),
    )
    df["Valgus_PCA_filt_deg"] = lowpass_rolling(
        df,
        "Valgus_PCA_deg",
        window_sec=0.25,
        samplerate_hz=int(samplerate_hz),
    )

    return df


def process_single_angles_file(path: str):
    """
    Загружает один angles_*.csv, считает PCA-оси и сохраняет pca_angles_*.csv
    в тот же каталог.
    """
    print(f"\n=== PCA-анализ файла: {os.path.basename(path)} ===")
    df_angles = pd.read_csv(path)

    try:
        X_all, X_valid = _get_pitch_roll_matrix(df_angles, columns=("Pitch_deg", "Roll_deg"))
    except KeyError as e:
        print(f"[WARN] Пропускаем файл: {e}")
        return

    components = _compute_pca_components(X_valid)
    flex_w = components[0]
    frontal_w = components[1]

    print("PCA-компоненты (Pitch, Roll):")
    print(f"  Flex_PCA  = [{flex_w[0]:+.3f}, {flex_w[1]:+.3f}]")
    print(f"  Valgus_PCA= [{frontal_w[0]:+.3f}, {frontal_w[1]:+.3f}]")

    df_pca = _apply_pca_to_angles(
        df_angles,
        components=components,
        columns=("Pitch_deg", "Roll_deg"),
        neutral_window_sec=1.0,
        samplerate_hz=MOVESENSE_SAMPLERATE_HZ,
    )

    # Имя выходного файла: pca_<старое имя>
    dirname = os.path.dirname(path)
    basename = os.path.basename(path)  # angles_xxx.csv
    out_name = f"pca_{basename}"
    out_path = os.path.join(dirname, out_name)

    df_pca.to_csv(out_path, index=False)
    print(f"[OK] PCA-расширенный файл сохранён как: {out_path}")


def main():
    print("=== AIMA2: offline PCA-анализ углов (Pitch/Roll) ===")
    print(f"Ищем файлы angles_*.csv в директории: {SESSIONS_DIR}")

    pattern = os.path.join(SESSIONS_DIR, "angles_*.csv")
    paths = sorted(glob.glob(pattern))

    if not paths:
        print("[INFO] Не найдено ни одного файла angles_*.csv.")
        return

    print(f"Найдено файлов: {len(paths)}")
    for p in paths:
        process_single_angles_file(p)

    print("\nГотово. Для каждого файла angles_*.csv создан файл pca_angles_*.csv с дополнительными PCA-колонками.")


if __name__ == "__main__":
    main()
