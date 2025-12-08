# madgwick.py

import numpy as np


class MadgwickAHRS:
    """
    Реализация фильтра Madgwick для оценки ориентации по IMU.

    Важно:
      - gx, gy, gz ожидаются в градусах/сек (dps) -> внутри переводятся в rad/s
      - ax, ay, az — любые единицы, главное, что вектор != 0
      - mx, my, mz (опционально) — магнетометр; если None, используем IMU-only вариант
    """

    def __init__(self, sample_period: float = 1.0 / 104.0, beta: float = 0.1):
        self.sample_period = float(sample_period)
        self.beta = float(beta)
        # Кватернион в формате [w, x, y, z]
        self.quaternion = np.array([1.0, 0.0, 0.0, 0.0], dtype=float)

    # ------------------------------------------------------------------ #
    #  Публичный интерфейс: один метод update для обоих режимов
    # ------------------------------------------------------------------ #
    def update(
        self,
        gx: float,
        gy: float,
        gz: float,
        ax: float,
        ay: float,
        az: float,
        mx: float | None = None,
        my: float | None = None,
        mz: float | None = None,
    ) -> np.ndarray:
        """
        Обновляет оценку ориентации.

        Если mx/my/mz == None -> используется IMU-only алгоритм.
        """

        if mx is None or my is None or mz is None:
            self._update_imu(gx, gy, gz, ax, ay, az)
        else:
            self._update_ahrs(gx, gy, gz, ax, ay, az, mx, my, mz)

        return self.quaternion.copy()

    # ------------------------------------------------------------------ #
    #  Внутренние реализация: с магнетометром / без
    # ------------------------------------------------------------------ #
    def _update_imu(self, gx, gy, gz, ax, ay, az):
        """Madgwick IMU-only (без магнетометра)."""

        q1, q2, q3, q4 = self.quaternion  # w, x, y, z

        # Нормализация акселерометра
        a = np.array([ax, ay, az], dtype=float)
        norm = np.linalg.norm(a)
        if norm < 1e-12:
            # Нет полезного акселерометра — интегрируем только гироскоп
            self._integrate_gyro(gx, gy, gz)
            return
        ax, ay, az = a / norm

        # Перевод гироскопа в rad/s
        gx = np.deg2rad(gx)
        gy = np.deg2rad(gy)
        gz = np.deg2rad(gz)

        # Вспомогательные переменные
        _2q1 = 2.0 * q1
        _2q2 = 2.0 * q2
        _2q3 = 2.0 * q3
        _2q4 = 2.0 * q4
        _4q1 = 4.0 * q1
        _4q2 = 4.0 * q2
        _4q3 = 4.0 * q3
        _8q2 = 8.0 * q2
        _8q3 = 8.0 * q3
        q1q1 = q1 * q1
        q2q2 = q2 * q2
        q3q3 = q3 * q3
        q4q4 = q4 * q4

        # Функция ошибки (разница между измеренным и ожидаемым направлением гравитации)
        f1 = _2q2 * q4 - _2q1 * q3 - ax
        f2 = _2q1 * q2 + _2q3 * q4 - ay
        f3 = 1.0 - _2q2 * q2 - _2q3 * q3 - az

        # Якобиан
        J_11 = -_2q3
        J_12 = _2q4
        J_13 = -_2q1
        J_14 = _2q2
        J_32 = 2.0 * J_14
        J_33 = 2.0 * J_11

        # Градиент
        step = np.array(
            [
                J_14 * f2 - J_11 * f1,
                J_12 * f1 + J_13 * f2 - J_32 * f3,
                J_12 * f2 - J_33 * f3 - J_13 * f1,
                J_14 * f1 + J_11 * f2,
            ],
            dtype=float,
        )

        step_norm = np.linalg.norm(step)
        if step_norm > 1e-12:
            step /= step_norm
        else:
            step[:] = 0.0

        # Производная кватерниона
        q_dot = 0.5 * np.array(
            [
                -q2 * gx - q3 * gy - q4 * gz,
                q1 * gx + q3 * gz - q4 * gy,
                q1 * gy - q2 * gz + q4 * gx,
                q1 * gz + q2 * gy - q3 * gx,
            ],
            dtype=float,
        ) - self.beta * step

        # Интегрируем и нормализуем
        q = np.array([q1, q2, q3, q4], dtype=float) + q_dot * self.sample_period
        q /= np.linalg.norm(q)

        self.quaternion = q

    def _update_ahrs(self, gx, gy, gz, ax, ay, az, mx, my, mz):
        """Полный Madgwick AHRS с магнетометром."""

        q1, q2, q3, q4 = self.quaternion  # w, x, y, z

        # Нормализация акселерометра
        a = np.array([ax, ay, az], dtype=float)
        norm = np.linalg.norm(a)
        if norm < 1e-12:
            self._integrate_gyro(gx, gy, gz)
            return
        ax, ay, az = a / norm

        # Нормализация магнетометра
        m = np.array([mx, my, mz], dtype=float)
        norm = np.linalg.norm(m)
        if norm < 1e-12:
            # Нет адекватного магнетометра -> падаем в IMU-only
            self._update_imu(gx, gy, gz, ax, ay, az)
            return
        mx, my, mz = m / norm

        # Gyro в rad/s
        gx = np.deg2rad(gx)
        gy = np.deg2rad(gy)
        gz = np.deg2rad(gz)

        # Вспомогательные
        _2q1 = 2.0 * q1
        _2q2 = 2.0 * q2
        _2q3 = 2.0 * q3
        _2q4 = 2.0 * q4
        _2q1q3 = 2.0 * q1 * q3
        _2q3q4 = 2.0 * q3 * q4
        q1q1 = q1 * q1
        q2q2 = q2 * q2
        q3q3 = q3 * q3
        q4q4 = q4 * q4

        # Ссылки на формулы — см. оригинальную статью Madgwick 2010

        # Вычисление вспомогательного вектора b (проекция магнитного поля)
        hx = (
            mx * q1q1
            - _2q1 * my * q4
            + _2q1 * mz * q3
            + mx * q2q2
            + _2q2 * my * q3
            + _2q2 * mz * q4
            - mx * q3q3
            - mx * q4q4
        )
        hy = (
            _2q1 * mx * q4
            + my * q1q1
            - _2q1 * mz * q2
            + _2q2 * mx * q3
            - my * q2q2
            + my * q3q3
            + _2q3 * mz * q4
            - my * q4q4
        )
        _2bx = np.sqrt(hx * hx + hy * hy)
        _2bz = (
            -_2q1 * mx * q3
            + _2q1 * my * q2
            + mz * q1q1
            + _2q2 * mx * q4
            - mz * q2q2
            + _2q3 * my * q4
            - mz * q3q3
            + mz * q4q4
        )
        _4bx = 2.0 * _2bx
        _4bz = 2.0 * _2bz

        # Функция ошибки (гравитация + магнитное поле)
        f1 = _2q2 * q4 - _2q1 * q3 - ax
        f2 = _2q1 * q2 + _2q3 * q4 - ay
        f3 = 1.0 - _2q2 * q2 - _2q3 * q3 - az
        f4 = (
            _2bx * (0.5 - q3q3 - q4q4)
            + _2bz * (q2 * q4 - q1 * q3)
            - mx
        )
        f5 = (
            _2bx * (q2 * q3 - q1 * q4)
            + _2bz * (q1 * q2 + q3 * q4)
            - my
        )
        f6 = (
            _2bx * (q1 * q3 + q2 * q4)
            + _2bz * (0.5 - q2q2 - q3q3)
            - mz
        )

        # Градиент (см. вывод Madgwick)
        J_11 = -_2q3
        J_12 = _2q4
        J_13 = -_2q1
        J_14 = _2q2
        J_32 = 2.0 * J_14
        J_33 = 2.0 * J_11

        step = np.array(
            [
                J_14 * f2 - J_11 * f1,
                J_12 * f1 + J_13 * f2 - J_32 * f3,
                J_12 * f2 - J_33 * f3 - J_13 * f1,
                J_14 * f1 + J_11 * f2,
            ],
            dtype=float,
        )

        step_norm = np.linalg.norm(step)
        if step_norm > 1e-12:
            step /= step_norm
        else:
            step[:] = 0.0

        # Производная кватерниона
        q_dot = 0.5 * np.array(
            [
                -q2 * gx - q3 * gy - q4 * gz,
                q1 * gx + q3 * gz - q4 * gy,
                q1 * gy - q2 * gz + q4 * gx,
                q1 * gz + q2 * gy - q3 * gx,
            ],
            dtype=float,
        ) - self.beta * step

        # Интеграция и нормализация
        q = np.array([q1, q2, q3, q4], dtype=float) + q_dot * self.sample_period
        q /= np.linalg.norm(q)
        self.quaternion = q

    # ------------------------------------------------------------------ #
    #  Fallback: чистая интеграция гироскопа (если нет Acc/Magn)
    # ------------------------------------------------------------------ #
    def _integrate_gyro(self, gx, gy, gz):
        """Если акселерометр/магнетометр нулевые — интегрируем только гироскоп."""

        q1, q2, q3, q4 = self.quaternion
        gx = np.deg2rad(gx)
        gy = np.deg2rad(gy)
        gz = np.deg2rad(gz)

        q_dot = 0.5 * np.array(
            [
                -q2 * gx - q3 * gy - q4 * gz,
                q1 * gx + q3 * gz - q4 * gy,
                q1 * gy - q2 * gz + q4 * gx,
                q1 * gz + q2 * gy - q3 * gx,
            ],
            dtype=float,
        )

        q = np.array([q1, q2, q3, q4], dtype=float) + q_dot * self.sample_period
        norm = np.linalg.norm(q)
        if norm > 1e-12:
            q /= norm
        else:
            q[:] = np.array([1.0, 0.0, 0.0, 0.0])

        self.quaternion = q
