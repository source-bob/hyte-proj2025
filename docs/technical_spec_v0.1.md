# ⚙️ Tekninen spesifikaatio v0.1 – AI Motion Analyzer

## 1. Johdanto

Tämän dokumentin tarkoituksena on määrittää AI Motion Analyzer -järjestelmän tekniset vaatimukset.  
Järjestelmä hyödyntää MoveSense-IMU-anturia alaraajan liikkeiden mittaamiseen ja tekoälymallia liikkeiden luokitteluun (esim. kyykky, askel, sivuttaissiirtymä).  
Mittauksen avulla voidaan analysoida polven linjausta (varus/valgus), fleksio-ekstensio-kulmaa sekä lateraalista siirtymää.

---

## 2. Mitattavat parametrit

| Parametri | Kuvaus | Yksikkö | Tavoite |
|------------|---------|----------|----------|
| **Varus/Valgus-kulma** | Polven linjauksen poikkeama kuormituksen aikana | astetta (°) | Keskiarvo liikkeen aikana |
| **Fleksio / Ekstensio** | Polven taivutus ja ojennus liikkeen aikana | astetta (°) | Maksimiarvo liikesyklissä |
| **Lateraalinen siirtymä** | Säären sivuttaisliike suhteessa reiteen | millimetriä (mm) tai laskennallinen kulma | Keskimääräinen arvo |
| **Liikkeen tyyppi** | Tekoälyn tunnistama liike (kyykky, askel, sivuttaissiirtymä) | luokka | CNN-mallin luokitus (3 liiketyyppiä) |

---

## 3. Anturin sijoitus

| Anturi | Sijainti | Perustelu |
|---------|-----------|------------|
| **IMU 1** | Säären yläosa (tibian etupuolella) | Tämä sijainti mittaa tehokkaasti säären rotaatiota ja polvikulmaa ilman lihas-artefaktoja. |
| **IMU 2 (valinnainen)** | Reiden keskiosa (femurin etupuolella) | Parantaa kulma-arvioiden tarkkuutta ja mahdollistaa kaksiosaisen liikeanalyysin (reisi–sääri). |

📍 **Perustelu:**  
Sääriluun yläosa on suositeltava kiinnityspaikka, koska se liikkuu vakaasti suhteessa polviniveleen ja tuottaa vähiten häiriötä pehmytkudosten liikkeistä.  
Reisiosuus voidaan lisätä, jos halutaan tarkempi kulman laskenta (kahden anturin menetelmä).

---

## 4. Näytteenottotaajuus ja datamuoto

| Parametri | Arvo | Perustelu |
|------------|------|-----------|
| **Näytteenottotaajuus** | 100 Hz (minimi), 200 Hz (optimi) | 100 Hz riittää hitaammille liikkeille (kävely, kyykky); 200 Hz mahdollistaa nopeammat liikkeet ja vähentää aliasointia. |
| **Datamuoto** | CSV tai JSON | Kumpikin muoto sisältää aikaleimat, kiertokulmat (roll, pitch, yaw), kiihtyvyydet ja kulmanopeudet. |
| **Datan siirto** | Bluetooth Low Energy (BLE) | MoveSense tukee BLE-yhteyttä, mikä mahdollistaa reaaliaikaisen datan siirron sovellukselle. |

---

## 5. Tarkkuusvaatimukset

| Mittaus | Tavoitetarkkuus | Hyväksyttävä raja | Lähde |
|----------|-----------------|-------------------|-------|
| Varus/Valgus-kulma | ±1–3° | ±5° | Sensors 2024, Jordan et al. 2021 |
| Fleksio / Ekstensio | ±2° | ±5° | Sensors 2024 |
| Lateraalinen siirtymä | ±3 mm | ±6 mm | Arvioitu liikesignaalin perusteella |

---

## 6. Yhteenveto

AI Motion Analyzer hyödyntää MoveSense-IMU-teknologiaa ja tekoälymallia liikkeiden analysointiin.  
Anturit sijoitetaan sääreen ja mahdollisesti reiteen, datan näytteenottotaajuus on 100–200 Hz ja tavoitetarkkuus 1–3°.  
Järjestelmä tarjoaa kannettavan, kustannustehokkaan ja kliinisesti riittävän ratkaisun polven linjauksen arviointiin.

---
