# 📁 MoveSense IMU Data Structure

**File format:** CSV  
**Sampling rate:** 100 Hz  
**Recording length:** 30 s  
**Data columns:**

| Column | Description | Unit |
|---------|--------------|------|
| Timestamp | Milliseconds since start | ms |
| AccX, AccY, AccZ | Linear acceleration | m/s² |
| GyroX, GyroY, GyroZ | Angular velocity | °/s |
| MagnX, MagnY, MagnZ | Magnetic field strength | µT |

**Notes:**  
- Data is recorded via BLE in real time.  
- Sensor orientation: arrow forward, Y-axis upward.  
- Typical file size for 30 s @ 100 Hz ≈ 200 kB.
