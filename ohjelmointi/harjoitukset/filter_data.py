# filter_data.py
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt

# 🔹 1. Asetukset
FILEPATH = "data/movesense/kyykky_testi.csv"
CUTOFF = 5          # Katkotaajuus (Hz)
FS = 104            # Näytteenottotaajuus (Hz)
ORDER = 4           # Suotimen järjestys

# 🔹 2. Butterworth low-pass -suodin
def butter_lowpass_filter(data, cutoff, fs, order=4):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = filtfilt(b, a, data)
    return y

# 🔹 3. Lue data
df = pd.read_csv(FILEPATH)

# Tarkistetaan sarakkeet
print("Sarakkeet:", df.columns)

# Jos Timestamp-sarakkeessa on NaN, luodaan numeerinen aika-akseli
if df['Timestamp'].isna().any():
    df['Time'] = [i / FS for i in range(len(df))]
else:
    df['Time'] = df['Timestamp']

# 🔹 4. Suodatetaan kiihtyvyys ja gyroskooppi
for col in ['AccX', 'AccY', 'AccZ', 'GyroX', 'GyroY', 'GyroZ']:
    df[col + '_filtered'] = butter_lowpass_filter(df[col], CUTOFF, FS, ORDER)

# 🔹 5. Piirretään vertailukaavio (ennen / jälkeen suodatuksen)
plt.figure(figsize=(10, 5))
plt.plot(df['Time'], df['AccX'], label='Ennen suodatusta', alpha=0.5)
plt.plot(df['Time'], df['AccX_filtered'], label='Suodatettu (5 Hz)', linewidth=2)
plt.xlabel('Aika (s)')
plt.ylabel('Kiihtyvyys (m/s²)')
plt.title('Butterworth-suodatus – AccX (Kyykkytesti)')
plt.legend()
plt.grid()
plt.tight_layout()
plt.show()

# 🔹 6. Tallenna suodatettu data
output_path = FILEPATH.replace(".csv", "_filtered.csv")
df.to_csv(output_path, index=False)
print(f"✅ Suodatettu data tallennettu: {output_path}")
