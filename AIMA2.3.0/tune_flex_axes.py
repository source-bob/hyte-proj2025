import os
from dataclasses import dataclass
from typing import Tuple, List, Dict

import numpy as np
import pandas as pd

from config import MOVESENSE_SAMPLERATE_HZ
from angles import compute_quaternions, compute_knee_angles
from metrics import detect_reps


# ============================================================
#  ВХОДНЫЕ ДАННЫЕ
# ============================================================

@dataclass
class FileInfo:
    path: str
    movement_type: str           # "squat" / "walk" / "lateral"
    target_flex_range: Tuple[float, float]    # (min, max) по сессии (например mean max per rep)
    target_frontal_range: Tuple[float, float] # (min, max) по сессии (например RMS)


# Пример — ПОДРЕДАКТИРУЙ ПОД СВОИ ФАЙЛЫ И ЦЕЛЕВЫЕ ДИАПАЗОНЫ
FILES_INFO: List[FileInfo] = [
    # Присед: хотим ~ 90–110° средней максимальной флексии, varus/valgus ~ 5–15°
    FileInfo(
        path="data/sessions/proc_bob_squat_reps_test2_20251207_210939.csv",
        movement_type="squat",
        target_flex_range=(15.0, 25.0),
        target_frontal_range=(3.0, 12.0),
    ),
    FileInfo(
        path="data/sessions/proc_bob_squat_reps_test3_20251207_211149.csv",
        movement_type="squat",
        target_flex_range=(15.0, 25.0),
        target_frontal_range=(3.0, 12.0),
    ),

    # Ходьба: флексия меньше, фронтальные отклонения тоже меньше
    FileInfo(
        path="data/sessions/proc_bob_walk_reps_test1_normal_20251207_235815.csv",
        movement_type="walk",
        target_flex_range=(8.0, 20.0),
        target_frontal_range=(0.0, 8.0),
    ),

    FileInfo(
        path="data/sessions/proc_bob_walk_reps_test1_slow_20251208_000107.csv",
        movement_type="walk",
        target_flex_range=(8.0, 20.0),
        target_frontal_range=(0.0, 8.0),
    ),

    FileInfo(
        path="data/sessions/proc_bob_walk_reps_test1_veryslow_20251208_000350.csv",
        movement_type="walk",
        target_flex_range=(8.0, 20.0),
        target_frontal_range=(0.0, 8.0),
    ),

    FileInfo(
        path="data/sessions/proc_bob_walk_reps_test1_fast_20251208_000621.csv",
        movement_type="walk",
        target_flex_range=(8.0, 20.0),
        target_frontal_range=(0.0, 8.0),
    ),

    # Lateral: флексия ещё меньше, фронтальные отклонения больше
    FileInfo(
        path="data/sessions/proc_bob_lateral_reps_test4_normal_20251207_235348.csv",
        movement_type="lateral",
        target_flex_range=(5.0, 18.0),
        target_frontal_range=(5.0, 15.0),
    ),

    FileInfo(
        path="data/sessions/proc_bob_lateral_reps_test3_normal_20251207_231021.csv",
        movement_type="lateral",
        target_flex_range=(5.0, 18.0),
        target_frontal_range=(5.0, 15.0),
    ),

    FileInfo(
        path="data/sessions/proc_bob_lateral_reps_test1_20251207_224906.csv",
        movement_type="lateral",
        target_flex_range=(5.0, 18.0),
        target_frontal_range=(5.0, 15.0),
    ),

    FileInfo(
        path="data/sessions/proc_bob_lateral_reps_test_slow_20251207_225157.csv",
        movement_type="lateral",
        target_flex_range=(5.0, 18.0),
        target_frontal_range=(5.0, 15.0),
    ),
]


# ============================================================
#  КАНДИДАТЫ ДЛЯ ОСЕЙ
# ============================================================

@dataclass(frozen=True)
class AxisSpec:
    col: str    # имя колонки в df_angles
    sign: float # 1.0 или -1.0


# Кандидаты для флексии (угол сгибания)
FLEX_CANDIDATES: List[AxisSpec] = [
    AxisSpec("KneeAngle_fused_deg", +1.0),
    AxisSpec("KneeAngle_filt_deg", +1.0),
    AxisSpec("Pitch_deg", +1.0),
    AxisSpec("Pitch_deg", -1.0),   # на случай, если знак нужно инвертировать
    AxisSpec("Roll_deg", +1.0),
    AxisSpec("Roll_deg", -1.0),
]

# Кандидаты для фронтального индекса (varus/valgus)
FRONTAL_CANDIDATES: List[AxisSpec] = [
    AxisSpec("KneeValgus_fused_deg", +1.0),
    AxisSpec("KneeValgus_filt_deg", +1.0),
    AxisSpec("Roll_deg", +1.0),
    AxisSpec("Roll_deg", -1.0),
]



# ============================================================
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def load_proc_and_angles(csv_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Загружает PROC-файл и пересчитывает углы (Yaw/Pitch/Roll + KneeAngle_*).
    Ожидаем, что в файле уже есть *_corr-колонки.
    """
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(csv_path)

    df_proc = pd.read_csv(csv_path)
    has_corr = any(col.endswith("_corr") for col in df_proc.columns)
    if not has_corr:
        raise ValueError(
            f"File {csv_path} doesn't look like PROC (no *_corr columns)."
        )

    quats = compute_quaternions(df_proc)
    df_angles = compute_knee_angles(df_proc, quats)
    return df_proc, df_angles


def compute_rep_boundaries(peaks: np.ndarray, n_samples: int) -> np.ndarray:
    """
    Простейшие границы репов: середины между соседними пиками.
    """
    peaks = np.asarray(peaks, dtype=int)
    m = len(peaks)
    if m == 0:
        return np.array([0, n_samples - 1], dtype=int)

    boundaries = np.zeros(m + 1, dtype=int)
    boundaries[0] = 0
    boundaries[-1] = n_samples - 1
    for i in range(1, m):
        boundaries[i] = (peaks[i - 1] + peaks[i]) // 2
    return boundaries


def session_stats_for_axes(
    df_angles: pd.DataFrame,
    peaks: np.ndarray,
    flex_axis: AxisSpec,
    frontal_axis: AxisSpec,
    samplerate_hz: float,
) -> Dict[str, float]:
    """
    Считает агрегаты по сессии для заданных осей:
      - flex_mean_max: средний максимум (по модулю) флексии по репам
      - frontal_rms: RMS фронтального индекса по всей записи
    """
    n = len(df_angles)
    if n == 0 or len(peaks) == 0:
        return {"flex_mean_max": 0.0, "frontal_rms": 0.0}

    if flex_axis.col not in df_angles.columns:
        raise KeyError(f"Flex column '{flex_axis.col}' not in df_angles")

    if frontal_axis.col not in df_angles.columns:
        raise KeyError(f"Frontal column '{frontal_axis.col}' not in df_angles")

    flex_signal = df_angles[flex_axis.col].to_numpy(dtype=float) * flex_axis.sign
    frontal_signal = df_angles[frontal_axis.col].to_numpy(dtype=float) * frontal_axis.sign

    boundaries = compute_rep_boundaries(peaks, n)

    # 1) per-rep max(|flex|)
    per_rep_max = []
    for i in range(len(peaks)):
        start = int(boundaries[i])
        end = int(boundaries[i + 1])
        seg = flex_signal[start:end + 1]
        per_rep_max.append(np.max(np.abs(seg)))
    flex_mean_max = float(np.mean(per_rep_max)) if per_rep_max else 0.0

    # 2) RMS по фронтальному индексу за всю запись
    frontal_rms = float(np.sqrt(np.mean(frontal_signal ** 2)))

    return {
        "flex_mean_max": flex_mean_max,
        "frontal_rms": frontal_rms,
    }


def range_error(value: float, target_range: Tuple[float, float]) -> float:
    """
    Скалярная ошибка: насколько value далеко от целевого диапазона.
    Если value внутри диапазона, берём середину.
    Нормируем на половину ширины диапазона.
    """
    lo, hi = target_range
    mid = 0.5 * (lo + hi)
    span = max(1e-6, 0.5 * (hi - lo))   # защита от деления на ноль
    return ((value - mid) / span) ** 2


def evaluate_axes_for_file(
    info: FileInfo,
    flex_axis: AxisSpec,
    frontal_axis: AxisSpec,
) -> Tuple[float, Dict[str, float]]:
    """
    Возвращает (ошибка по файлу, stats), либо (np.inf, {}) при неудаче.
    """
    try:
        df_proc, df_angles = load_proc_and_angles(info.path)
    except Exception as e:
        print(f"[WARN] failed to load {info.path}: {e}")
        return np.inf, {}

    # Детектим репы текущим пайплайном
    res = detect_reps(
        df_proc=df_proc,
        movement_type=info.movement_type,
        samplerate_hz=MOVESENSE_SAMPLERATE_HZ,
    )
    peaks = res.peaks
    if len(peaks) == 0:
        print(f"[WARN] no reps in {os.path.basename(info.path)}")
        return np.inf, {}

    try:
        stats = session_stats_for_axes(
            df_angles,
            peaks,
            flex_axis=flex_axis,
            frontal_axis=frontal_axis,
            samplerate_hz=MOVESENSE_SAMPLERATE_HZ,
        )
    except KeyError as e:
        # если какой-то оси нет — комбинация осей невалидна
        return np.inf, {}

    flex_err = range_error(stats["flex_mean_max"], info.target_flex_range)
    frontal_err = range_error(stats["frontal_rms"], info.target_frontal_range)

    # Можно варьировать веса; пока даём флексии вес 1.0, фронталу 1.0
    total_err = float(flex_err + frontal_err)
    return total_err, stats


# ============================================================
#  GRID SEARCH ПО ОСЯМ
# ============================================================

def grid_search_axes():
    results = []

    for flex_ax in FLEX_CANDIDATES:
        for front_ax in FRONTAL_CANDIDATES:
            total_err_all = 0.0
            per_file_stats = []
            valid = True

            for info in FILES_INFO:
                err, stats = evaluate_axes_for_file(info, flex_ax, front_ax)
                if not np.isfinite(err):
                    valid = False
                    break
                total_err_all += err
                per_file_stats.append((info, stats, err))

            if not valid:
                continue

            results.append({
                "flex_axis": flex_ax,
                "frontal_axis": front_ax,
                "total_err": total_err_all,
                "per_file": per_file_stats,
            })

    if not results:
        print("[ERROR] No valid axis combinations tested.")
        return

    # сортируем по суммарной ошибке
    results.sort(key=lambda r: r["total_err"])
    best = results[0]

    print("\n=== BEST AXIS COMBINATION (min total_err) ===")
    print(
        f"Flex: {best['flex_axis'].col} * {best['flex_axis'].sign:+.1f} , "
        f"Frontal: {best['frontal_axis'].col} * {best['frontal_axis'].sign:+.1f}"
    )
    print(f"Total error over all files: {best['total_err']:.3f}\n")

    print("Per-file stats for BEST combination:")
    for info, stats, err in best["per_file"]:
        print(f"  {os.path.basename(info.path)}  ({info.movement_type})")
        print(
            f"    flex_mean_max = {stats['flex_mean_max']:.1f} deg "
            f"(target {info.target_flex_range[0]}–{info.target_flex_range[1]})"
        )
        print(
            f"    frontal_rms   = {stats['frontal_rms']:.1f} deg "
            f"(target {info.target_frontal_range[0]}–{info.target_frontal_range[1]})"
        )
        print(f"    file_error    = {err:.3f}")

    print("\n=== TOP 10 AXIS COMBINATIONS ===")
    for r in results[:10]:
        fa = r["flex_axis"]
        va = r["frontal_axis"]
        print(
            f"Flex={fa.col}*{fa.sign:+.1f}  "
            f"Frontal={va.col}*{va.sign:+.1f}  "
            f"--> total_err={r['total_err']:.3f}"
        )


if __name__ == "__main__":
    grid_search_axes()
