# sensor_io.py
"""
Модуль для записи данных с Movesense-сенсора в рамках проекта AIMA.

Использует movesense.MovesenseClient из файла movesense.py.
"""

import asyncio
from typing import Optional

import movesense as ms
from config import (
    MOVESENSE_ADDRESS,
    MOVESENSE_SENSOR,
    MOVESENSE_SAMPLERATE_HZ,
    REC_LENGTH_SEC,
    START_DELAY_SEC,
    DATA_FOLDER,
    SAVE_TO_CSV,
)


class AimaMoveSenseRecorder:
    """
    Упрощённый интерфейс для работы с Movesense:
    - подключиться
    - записать один отрезок
    - получить pandas.DataFrame
    """

    def __init__(
        self,
        address: str = MOVESENSE_ADDRESS,
        sensor=MOVESENSE_SENSOR,
        samplerate_hz: int = MOVESENSE_SAMPLERATE_HZ,
        rec_length_sec: int = REC_LENGTH_SEC,
        start_delay_sec: int = START_DELAY_SEC,
        data_folder: str = DATA_FOLDER,
        save_to_csv: bool = SAVE_TO_CSV,
        filename_prefix: str = None,
    ) -> None:
        self.address = address
        self.sensor = sensor
        self.samplerate_hz = samplerate_hz
        self.rec_length_sec = rec_length_sec
        self.start_delay_sec = start_delay_sec
        self.data_folder = data_folder
        self.save_to_csv = save_to_csv
        self.filename_prefix = filename_prefix

        # "Голый" клиент из movesense.py
        self._device = ms.MovesenseClient(self.address)

    async def _record_async(self) -> ms.Record:
        """
        Асинхронная запись одного отрезка данных.
        Используется внутри record_once_* методов.
        """
        async with self._device as client:
            # ПЕРЕД записью переименуем устройство,
            # чтобы файл назывался так, как мы хотим.
            if self.filename_prefix is not None:
                self._device.set_name(self.filename_prefix)
            record = await client.subscribe(
                sensor=self.sensor,
                samplerate=self.samplerate_hz,
                rec_length=self.rec_length_sec,
                start_delay=self.start_delay_sec,
                filepath=self.data_folder,
                save_to_csv=self.save_to_csv,
            )
            return record

    def record_once(self) -> ms.Record:
        """
        Синхронный вызов записи.
        Возвращает movesense.Record (можно получить и numpy, и pandas).
        """
        record = asyncio.run(self._record_async())
        return record

    def record_once_to_pandas(self):
        """
        Записать один отрезок и вернуть pandas.DataFrame.
        Удобно для дальнейшей обработки в нашем pipeline.
        """
        record = self.record_once()
        df = record.to_pandas()
        return df

    def record_once_to_numpy(self):
        """
        Записать один отрезок и вернуть numpy.array.
        """
        record = self.record_once()
        arr = record.to_numpy()
        return arr


# Небольшой тестовый запуск этого модуля напрямую:
if __name__ == "__main__":
    recorder = AimaMoveSenseRecorder()
    df = recorder.record_once_to_pandas()
    print(df.head())
    print(df.tail())
