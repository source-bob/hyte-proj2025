# pca_axes.py
"""
PCA-основы для выбора осей flex / frontal из Pitch/Roll.

Идея:
  - Берём временной ряд [Pitch_deg, Roll_deg].
  - Делаем PCA (двумерный).
  - Первая главная компонента -> ось сгибания (flex).
  - Вторая главная компонента -> фронтальный индекс (varus/valgus surrogate).

Важно:
  - Это опциональный слой поверх compute_knee_angles.
  - Мы переписываем KneeAngle_* и KneeValgus_* в df_angles,
    но имена колонок те же, так что остальной код не ломается.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass

from config import MOVESENSE_SAMPLERATE_HZ
from processing import lowpass_rolling


@dataclass
class PCAAxes:
    """
    Весовые векторы осей PCA для flex и frontal.

    flex_weights / frontal_weights — вектора длины 2:
      [w_pitch, w_roll]
    columns — имена исходных колонок (по умолчанию Pitch_deg, Roll_deg).
    """
    flex_weights: np.ndarray
    frontal_weights: np.ndarray
    columns: tuple[str, str] = ("Pitch_deg", "Roll_deg")


def _safe_get_2d_matrix(
    df_angles: pd.DataFrame,
    columns: tuple[str, str],
) -> np.ndarray:
    """
    Достаём матрицу [Pitch, Roll] (или другие 2 колонки) как float
    и выбрасываем строки с NaN.
    """
    col1, col2 = columns
    if col1 not in df_angles.columns or col2 not in df_angles.columns:
        raise KeyError(
            f"PCA: expected columns {columns}, "
            f"but df_angles has only {list(df_angles.columns)}"
        )

    X = df_angles[[col1, col2]].to_numpy(dtype=float)
    mask = np.all(np.isfinite(X), axis=1)
    X_valid = X[mask]

    return X_valid


def compute_pca_axes(
    df_angles: pd.DataFrame,
    columns: tuple[str, str] = ("Pitch_deg", "Roll_deg"),
) -> PCAAxes:
    """
    Считает PCA-оси для flex / frontal по двум углам (обычно Pitch/Roll).

    Возвращает PCAAxes:
      - flex_weights: первый главный компонент
      - frontal_weights: второй главный компонент
    """
    X_valid = _safe_get_2d_matrix(df_angles, columns)

    # Если данных мало или всё в NaN — fallback: единичная матрица
    if X_valid.shape[0] < 10:
        flex_w = np.array([1.0, 0.0], dtype=float)   # flex ≈ Pitch
        frontal_w = np.array([0.0, 1.0], dtype=float)  # frontal ≈ Roll
        return PCAAxes(flex_weights=flex_w, frontal_weights=frontal_w, columns=columns)

    # Центрируем по среднему, как в классическом PCA
    Xc = X_valid - np.mean(X_valid, axis=0, keepdims=True)

    # SVD: Xc = U S V^T, строки V^T — главные компоненты
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    components = Vt  # shape (2, 2)

    flex_w = components[0].astype(float)   # PC1
    frontal_w = components[1].astype(float)  # PC2

    # Небольшая эвристика: выравниваем знак по текущим индексам,
    # если они уже есть (чтобы не переворачивать "вверх ногами").
    col_flex = "KneeAngle_fused_deg"
    col_frontal = "KneeValgus_fused_deg"

    # Полная матрица для всей записи
    X_all = df_angles[list(columns)].to_numpy(dtype=float)

    def align_sign(existing_col: str, weights: np.ndarray) -> np.ndarray:
        if existing_col not in df_angles.columns:
            return weights
        y = df_angles[existing_col].to_numpy(dtype=float)
        if y.size != X_all.shape[0]:
            return weights
        # игнорируем NaN
        mask = np.isfinite(y) & np.all(np.isfinite(X_all), axis=1)
        if np.sum(mask) < 10:
            return weights

        proj = X_all[mask] @ weights
        y_valid = y[mask]
        # корреляция как proxy направления
        cov = np.cov(proj, y_valid)
        if cov.shape == (2, 2) and cov[0, 1] < 0:
            return -weights
        return weights

    flex_w = align_sign(col_flex, flex_w)
    frontal_w = align_sign(col_frontal, frontal_w)

    return PCAAxes(flex_weights=flex_w, frontal_weights=frontal_w, columns=columns)


def apply_pca_axes_to_angles(
    df_angles: pd.DataFrame,
    axes: PCAAxes,
    neutral_window_sec: float = 1.0,
    samplerate_hz: float = MOVESENSE_SAMPLERATE_HZ,
) -> pd.DataFrame:
    """
    Применяет PCA-оси к df_angles:
      - пересчитывает KneeAngle_fused/filt_deg,
      - пересчитывает KneeValgus_fused/filt_deg.

    Нейтральная поза: среднее за первые neutral_window_sec секунд, как в
    compute_knee_angles (первая секунда записи).
    """
    df = df_angles.copy()

    col1, col2 = axes.columns
    X_all = df[[col1, col2]].to_numpy(dtype=float)

    n = len(df)
    if n == 0:
        return df

    # Нейтраль — первые neutral_window_sec
    n0 = int(round(neutral_window_sec * samplerate_hz))
    n0 = max(1, min(n0, n))

    base = np.mean(X_all[:n0, :], axis=0, keepdims=True)
    X_rel = X_all - base  # убираем "нейтральную" позу

    flex = X_rel @ axes.flex_weights
    frontal = X_rel @ axes.frontal_weights

    df["KneeAngle_fused_deg"] = flex
    df["KneeValgus_fused_deg"] = frontal

    # Сглаживаем через тот же lowpass_rolling, что и в angles.py
    df["KneeAngle_filt_deg"] = lowpass_rolling(
        df, "KneeAngle_fused_deg", window_sec=0.25, samplerate_hz=int(samplerate_hz)
    )
    df["KneeValgus_filt_deg"] = lowpass_rolling(
        df, "KneeValgus_fused_deg", window_sec=0.25, samplerate_hz=int(samplerate_hz)
    )

    return df


def add_pca_based_angles(
    df_angles: pd.DataFrame,
    neutral_window_sec: float = 1.0,
    samplerate_hz: float = MOVESENSE_SAMPLERATE_HZ,
) -> tuple[pd.DataFrame, PCAAxes]:
    """
    Высокоуровневая обёртка:
      1) считаем PCA-оси из (Pitch_deg, Roll_deg),
      2) применяем их и пересчитываем KneeAngle_* / KneeValgus_*.

    Возвращает:
      df_new, axes
    """
    axes = compute_pca_axes(df_angles, columns=("Pitch_deg", "Roll_deg"))
    df_new = apply_pca_axes_to_angles(
        df_angles,
        axes=axes,
        neutral_window_sec=neutral_window_sec,
        samplerate_hz=samplerate_hz,
    )
    return df_new, axes
