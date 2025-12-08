"""
Глобальные настройки AIMA2 для работы с Movesense-сенсором.
Совмещает старый конфиг и новые параметры (папки, Madgwick и т.п.).
"""

import os
import movesense as ms  # файл movesense.py должен лежать рядом или в PYTHONPATH

# === НАСТРОЙКИ УСТРОЙСТВА ===

# MAC-адрес твоего Movesense
MOVESENSE_ADDRESS: str = "0C:8C:DC:3C:9D:19"

# Какой сенсор используем (см. enum Sensor в movesense.py)
MOVESENSE_SENSOR = ms.Sensor.IMU9  # IMU9 = Acc + Gyro + Magn

# Частота дискретизации (Гц). Допустимые значения: 13, 26, 52, 104, 208, 516
MOVESENSE_SAMPLERATE_HZ: int = 104

# === ВРЕМЕННЫЕ ПАРАМЕТРЫ ===

# Длительность калибровочного отрезка (статичная стойка)
CALIB_REC_LENGTH_SEC: int = 5

# Для нового кода AIMA2 используем синоним:
CALIB_LENGTH_SEC: int = CALIB_REC_LENGTH_SEC

# Длительность основной записи (секунды)
REC_LENGTH_SEC: int = 35

# Задержка перед стартом записи (секунды) — если используется в sensor_io / movesense
START_DELAY_SEC: int = 5

# === ФАЙЛЫ И ПАПКИ ===

# Базовая папка для данных (как раньше)
DATA_FOLDER: str = os.path.join("data")

# Синоним для нового кода
DATA_DIR: str = DATA_FOLDER

# Подпапки для разных типов данных
SESSIONS_DIR: str = os.path.join(DATA_FOLDER, "sessions")
METRICS_DIR: str = os.path.join(DATA_FOLDER, "metrics")
FEATURES_DIR: str = os.path.join(DATA_FOLDER, "features")

# Нужно ли сохранять CSV (используется в movesense/sensor_io)
SAVE_TO_CSV: bool = True

# Флаг для отладки
DEBUG_MODE: bool = False

# === ПАРАМЕТРЫ MADGWICK-ФИЛЬТРА ===

# Коэффициент "жёсткости" фильтра: больше — лучше следит за гироскопом,
# меньше — сильнее доверяет акселерометру/магнитометру.
MADGWICK_BETA: float = 0.1


REP_AXIS = {
    "squat":   "GyroY_corr",
    "walk":    "AccNorm_filt",
    "lateral": "GyroNorm_filt",
}

REP_POLARITY = {
    "squat":   1.0,
    "walk":    1.0,
    "lateral": 1.0,
}

REP_HP_WINDOW_SEC = 0.2

REP_MIN_DIST_SEC = {
    "squat":   1.2,
    "walk":    0.45,
    "lateral": 0.5,
}

REP_REL_HEIGHT = {
    "squat":   0.33,
    "walk":    0.3,
    "lateral": 0.35,
}
