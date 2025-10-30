# ⚙️ Tekninen spesifikaatio v0.9 – AI Motion Analyzer

## 1. Johdanto

Tämän dokumentin tarkoituksena on määrittää AI Motion Analyzer (AIMA) -järjestelmän tekniset vaatimukset.  
Järjestelmä hyödyntää MoveSense-IMU-anturia alaraajan liikkeiden mittaamiseen ja tekoälymallia (1D-CNN) liikkeiden luokitteluun (kyykky, kävely, sivuttaisliike).  
Mittauksen avulla analysoidaan polven linjausta (varus/valgus), fleksio-ekstensio-kulmaa sekä liikkeen tyyppiä.

---

## 2. Mitattavat parametrit

| **Parametri**            | **Kuvaus**                                      | **Yksikkö**     | **Tavoite**                          |
|--------------------------|--------------------------------------------------|------------------|--------------------------------------|
| Varus/Valgus-kulma       | Polven linjauksen poikkeama kuormituksen aikana | astetta (°)      | Keskimääräinen arvo liikkeen aikana |
| Fleksio / Ekstensio      | Polven taivutus ja ojennus liikkeen aikana      | astetta (°)      | Maksimiarvo syklin aikana           |
| Lateraalinen siirtymä    | Säären sivuttaisliike suhteessa reiteen         | laskennallinen kulma | Keskimääräinen arvo             |
| Liikkeen tyyppi          | CNN-mallin tunnistama liike                     | luokka           | Tunnistustarkkuus ≥ 90 %            |

---

## 3. Anturin sijoitus

| **Anturi** | **Sijainti**                     | **Perustelu**                                                                 |
|------------|----------------------------------|-------------------------------------------------------------------------------|
| IMU 1      | Säären yläosa (tibian etupuolella) | Ensisijainen mittauspiste; mittaa luotettavasti fleksio- ja valgus-kulmat ilman lihas-artefaktoja. |
| IMU 2 (valinnainen) | Reiden keskiosa (femurin etupuolella) | Käytetään vain, jos halutaan parantaa kulma-arvioiden tarkkuutta kaksiosaisella menetelmällä. |

📍 *Perustelu:*  
Yksi anturi (säären yläosa) on hyväksytty perusratkaisuksi ohjaajan kanssa 29.10.2025.  
Se on vakaa suhteessa polviniveleen ja soveltuu hyvin pilot-vaiheeseen.

---

## 4. Näytteenottotaajuus ja datamuoto
| **Parametri**          | **Arvo**                          | **Perustelu**                                                                 |
|------------------------|-----------------------------------|--------------------------------------------------------------------------------|
| Näytteenottotaajuus    | 100 Hz (minimi), 200 Hz (optimi) | 100 Hz riittää perusliikkeisiin; 200 Hz vähentää aliasointia ja soveltuu nopeampiin liikkeisiin. |
| Datamuoto              | CSV (ensisijainen) / JSON        | CSV helpottaa analyysiä Pythonissa ja toimii suoraan CNN-mallin syötteenä.    |
| Datan siirto           | Bluetooth Low Energy (BLE)       | MoveSense tukee BLE-yhteyttä reaaliaikaiseen datansiirtoon.                   |

---

## 5. Tarkkuusvaatimukset

| **Mittaus**            | **Tavoitetarkkuus** | **Hyväksyttävä raja** | **Lähde**                          |
|------------------------|---------------------|------------------------|------------------------------------|
| Varus/Valgus-kulma     | ± 1–3°              | ± 5°                   | Sensors 2024; Jordan et al. 2021   |
| Fleksio / Ekstensio    | ± 2°                | ± 5°                   | Sensors 2024                       |
| CNN-luokittelu         | ≥ 93 % tarkkuus     | ≥ 85 % hyväksyttävä    | Sensors 2024 (CNN-malli)          |

---

## 6. Yhteenveto

AIMA-järjestelmä hyödyntää MoveSense-IMU-teknologiaa ja CNN-pohjaista tekoälymallia liikkeiden analysointiin.  
Anturi sijoitetaan säären yläosaan, näytteenottotaajuus on 100–200 Hz ja tavoitetarkkuus 1–3°.  
Järjestelmä on kannettava, edullinen ja kliinisesti riittävän tarkka ratkaisu polven linjauksen ja liikkeen analyysiin.