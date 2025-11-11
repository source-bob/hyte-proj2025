# 🧾 Test Log – MoveSense BLE Connection & Pilot Recording  
**Projekti:** AI Motion Analyzer (AIMA)  
**Versio:** v0.9  
**Päivämäärä:** 2025-10-28  
**Mittauksen vastuuhenkilö:** Tech Lead / Data Engineer  

---

## 🔹 Testi 1 – BLE-yhteyden tarkistus  

| Aika | Kesto | Näytteenottotaajuus | Tila | Tulos | Tiedosto |
|------|--------|----------------------|-------|--------|-----------|
| 2025-10-28 | 30 s | 52 Hz | ✅ | Yhteys toimi ilman katkoksia | `/data/movesense/testi_ble_conn_2025-10-28.csv` |

**Huomiot:**  
- Ensimmäinen onnistunut yhteys MoveSense-anturiin (BLE).  
- Data tallentui täydellisesti (10 saraketta: ax–mz).  
- Ei havaittu pakettien menetystä tai aikaleiman hyppäyksiä.  

---

## 🔹 Testi 2 – Kyykkytesti (pilot)  

| Aika | Kesto | Näytteenottotaajuus | Tila | Tulos | Tiedosto |
|------|--------|----------------------|-------|--------|-----------|
| 2025-10-29 | 30 s | 104 Hz | ✅ | Tallennus onnistui | `/data/movesense/testi_kyykky_oj_2025-11-4` |

**Huomiot:**  
- Suoritettiin 5–10 kyykkyä rauhallisesti, kuten mittausprotokollassa.  
- Anturi sijoitettu oikein (sääriluun yläosa).  
- Ei havaittu datakatkoksia tai signaalihäiriöitä.  
- Kiihtyvyys- ja gyroskooppikäyrät näyttävät odotetuilta.  

---

## 🔹 Testi 3 – Kävelytesti (pilot)  

| Aika | Kesto | Näytteenottotaajuus | Tila | Tulos | Tiedosto |
|------|--------|----------------------|-------|--------|-----------|
| 2025-10-29 | 30 s | 104 Hz | ✅ | Tallennus onnistui | `/data/movesense/testi_kävely_oj_2025-11-4` |

**Huomiot:**  
- 5–10 m kävelymatka, 3–5 edestakaista sarjaa.  
- Anturi kiinnitetty kuten protokollassa.  
- Datan jatkuvuus ja amplitudi vakaa.  
- Magneettikenttäarvot vaihtelivat liikkeen aikana odotetusti, mutta palautuivat vakaasti lähtötasolle – ei havaittua drift-ilmiötä.  

---

## 🔸 Yhteenveto  

Kaikki mittaukset (BLE-testi, kyykky, kävely) suoritettiin onnistuneesti.  
Näytteenottotaajuus todettiin vakaaksi (104 Hz) ja tiedostojen tallennusvirheitä ei havaittu. 

---


>**[2025-10-30]** IMU-datan tallennus vahvistettu – 3 datasarjaa (kyykky, kävely, yhteystesti). Näytteenottotaajuus 104 Hz / 52 Hz (kyykky ja kävely / BLE-yhteys testi) ± 1 Hz , aikaleimarakenne yhtenäinen. Kaikki tiedostot tallennettu hakemistoon `/data/movesense/`.

>**[2025-11-5]** Calibration

>Accelerometer calibration (6 orientations):
Bias < 0.05 m/s², scale within ±1.5 % — within tolerance.
No correction required.

>Gyroscope bias (static, 15 s):
GyroX ≈ 0 °/s, GyroY = −0.13 °/s, GyroZ = −0.10 °/s.
All within ±0.2 °/s; correction applied for Y-axis (?).
