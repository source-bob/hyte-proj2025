import numpy as np
import pandas as pd
from processing import lowpass_rolling
from madgwick import MadgwickAHRS


def quat_to_euler(w, x, y, z):
    # roll (X-axis rotation)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = np.degrees(np.arctan2(sinr_cosp, cosr_cosp))

    # pitch (Y-axis rotation)
    sinp = 2 * (w * y - z * x)
    if abs(sinp) >= 1:
        pitch = np.degrees(np.sign(sinp) * (np.pi / 2))
    else:
        pitch = np.degrees(np.arcsin(sinp))

    # yaw (Z-axis rotation)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = np.degrees(np.arctan2(siny_cosp, cosy_cosp))

    return roll, pitch, yaw


def compute_knee_flexion_angles(df_proc, calib_params, alpha=0.98):
    df = df_proc.copy()

    fs = calib_params.get("samplerate_hz", 104)
    dt = 1.0 / fs

    ax = df["AccX_corr"].to_numpy()
    ay = df["AccY_corr"].to_numpy()
    az = df["AccZ_corr"].to_numpy()

    gx = df["GyroX_corr"].to_numpy()
    gy = df["GyroY_corr"].to_numpy()
    gz = df["GyroZ_corr"].to_numpy()

    mx = df["MagnX_corr"].to_numpy()
    my = df["MagnY_corr"].to_numpy()
    mz = df["MagnZ_corr"].to_numpy()

    ahrs = MadgwickAHRS(sample_period=dt, beta=0.08)

    quat_w = []
    quat_x = []
    quat_y = []
    quat_z = []

    roll_list = []
    pitch_list = []

    for i in range(len(df)):
        q = ahrs.update(
            gx[i], gy[i], gz[i],
            ax[i], ay[i], az[i],
            mx[i], my[i], mz[i]
        )

        w, x, y, z = q
        quat_w.append(w)
        quat_x.append(x)
        quat_y.append(y)
        quat_z.append(z)

        roll, pitch, yaw = quat_to_euler(w, x, y, z)

        roll_list.append(roll)
        pitch_list.append(pitch)

    df["Roll_raw"] = roll_list      # varus/valgus
    df["Pitch_raw"] = pitch_list    # flexion

    # Нормировка относительно начальной стоики
    df["KneeValgus_fused_deg"] = df["Roll_raw"] - df["Roll_raw"][0]
    df["KneeAngle_fused_deg"] = df["Pitch_raw"] - df["Pitch_raw"][0]

    df["KneeValgus_filt_deg"] = lowpass_rolling(df, "KneeValgus_fused_deg", 0.25)
    df["KneeAngle_fused_filt_deg"] = lowpass_rolling(df, "KneeAngle_fused_deg", 0.25)

    df["Quat_w"] = quat_w
    df["Quat_x"] = quat_x
    df["Quat_y"] = quat_y
    df["Quat_z"] = quat_z

    return df
