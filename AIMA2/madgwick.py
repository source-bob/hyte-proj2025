import numpy as np

class MadgwickAHRS:
    def __init__(self, sample_period=1/104, beta=0.1):
        self.sample_period = sample_period
        self.beta = beta
        self.quaternion = np.array([1.0, 0.0, 0.0, 0.0])

    def update(self, gx, gy, gz, ax, ay, az, mx=None, my=None, mz=None):
        q1, q2, q3, q4 = self.quaternion

        # Нормализация акселерометра
        if not (ax == 0 and ay == 0 and az == 0):
            norm = np.sqrt(ax * ax + ay * ay + az * az)
            ax /= norm
            ay /= norm
            az /= norm

        # Нормализация магнетометра
        if mx is not None:
            norm = np.sqrt(mx * mx + my * my + mz * mz)
            mx /= norm
            my /= norm
            mz /= norm

        # Преобразование угловых скоростей в rad/s
        gx = np.radians(gx)
        gy = np.radians(gy)
        gz = np.radians(gz)

        # Вспомогательные переменные
        _2q1mx = 2.0 * q1 * mx if mx is not None else 0
        _2q1my = 2.0 * q1 * my if mx is not None else 0
        _2q1mz = 2.0 * q1 * mz if mx is not None else 0
        _2q2mx = 2.0 * q2 * mx if mx is not None else 0

        # Градиентный шаг — упрощённая версия (если магнетометра нет)
        f1 = 2*(q2*q4 - q1*q3) - ax
        f2 = 2*(q1*q2 + q3*q4) - ay
        f3 = 2*(0.5 - q2*q2 - q3*q3) - az

        J_11or24 = 2*q3
        J_12or23 = 2*q4
        J_13or22 = 2*q1
        J_14or21 = 2*q2

        step = np.array([
            J_14or21*f2 - J_11or24*f1,
            J_12or23*f1 + J_13or22*f2 - J_14or21*f3,
            J_12or23*f2 - J_11or24*f3 - J_13or22*f1,
            J_14or21*f1 - J_12or23*f3
        ])

        step /= np.linalg.norm(step)

        # Производная кватерниона
        q_dot = 0.5 * np.array([
            -q2*gx - q3*gy - q4*gz,
             q1*gx + q3*gz - q4*gy,
             q1*gy - q2*gz + q4*gx,
             q1*gz + q2*gy - q3*gx
        ]) - self.beta * step

        # Обновляем кватернион
        self.quaternion += q_dot * self.sample_period
        self.quaternion /= np.linalg.norm(self.quaternion)

        return self.quaternion
