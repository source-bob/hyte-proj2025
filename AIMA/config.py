# config.py
"""
Глобальные настройки AIMA для работы с Movesense-сенсором.
"""

import os
import movesense as ms  # файл movesense.py должен лежать где-то в PYTHONPATH / рядом с этим модулем

# === НАСТРОЙКИ УСТРОЙСТВА ===

# MAC-адрес твоего Movesense (замени на свой при необходимости)
MOVESENSE_ADDRESS: str = "0C:8C:DC:3C:9D:19"

# Какой сенсор используем (смотри enum Sensor в movesense.py)
MOVESENSE_SENSOR = ms.Sensor.IMU9  # IMU9 = Acc + Gyro + Magn

# Частота дискретизации (Гц). Допустимые значения в доке: 13, 26, 52, 104, 208, 516
MOVESENSE_SAMPLERATE_HZ: int = 104

CALIB_REC_LENGTH_SEC: int = 5    # калибровка (статичный отрезок)
# Длительность одной записи (секунды).
REC_LENGTH_SEC: int = 35

# Задержка перед стартом записи (секунды).
START_DELAY_SEC: int = 5

# === ФАЙЛЫ И ПАПКИ ===

# Папка, куда movesense.py будет сохранять CSV
DATA_FOLDER: str = os.path.join("data")

# Нужно ли вообще сохранять CSV (movesense сам добавит имя файла и timestamp)
SAVE_TO_CSV: bool = True

# Можно добавить флаг для отладки (например, не сохранять CSV, а только возвращать df)
DEBUG_MODE: bool = False
