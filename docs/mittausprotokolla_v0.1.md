# 📊 Mittausprotokolla v0.1 – AI Motion Analyzer

## 1. Tavoite

Tämän mittausprotokollan tarkoituksena on määrittää toistettavat ja turvalliset olosuhteet MoveSense-IMU-anturin datankeruuta varten.  
Mittauksen avulla kerätään raakadata tekoälymallin koulutusta ja validointia varten.  
Kokeessa mitataan alaraajan liikkeet (kyykky ja kävely) ja analysoidaan polven linjaus (varus/valgus) sekä liikkeen tyyppi.

---

## 2. Mittausasetelma

| Elementti | Kuvaus |
|------------|---------|
| **Anturin sijainti** | MoveSense-IMU kiinnitetään **sääriluun yläosaan (tibian etupuolelle)** joustavalla tarranauhalla. <br>Lisäanturi (valinnainen) voidaan kiinnittää **reiden keskiosaan** liikeanalyysin tarkentamiseksi. |
| **Kiinnityksen tarkkuus** | Anturin tulee olla tiiviisti ihoa vasten, siten että liike ei aiheuta siirtymää. Anturin nuoli osoittaa eteenpäin (liikesuunta). |
| **Vaatetus** | Kevyet urheiluvaatteet (shortsit, joustava housumateriaali). Vaatteiden ei tule peittää anturia. |
| **Alustan pinta** | Tasainen, liukumaton lattia (esim. salin matto tai laminaatti). |
| **Lämmön ja kosteuden olosuhteet** | Mittaus suoritetaan sisätiloissa, normaali huonelämpötila (~20–22 °C). Kosteus ei kriittinen, mutta kirjataan mittauspäivänä. |

---

## 3. Mittausprotokolla

### 3.1 Kyykkytesti
- **Toistojen määrä:** 5–10 kyykkyä rauhallisessa tahdissa.  
- **Suoritusohje:** Jalat hartioiden leveydellä, selkä suorana. Kyykky noin 90° polvikulmaan.  
- **Tallennuksen alku/loppu:**  
  - Tallennus alkaa “Valmis”-komennolla ja päättyy viimeisen kyykyn jälkeen 2 s tauon jälkeen.  
  - Datan keruu jatkuvana (100 Hz).  
- **Tavoite:** Mitata fleksio-/ekstensio-kulma ja varus/valgus-kuormituksen aikana.

### 3.2 Kävelytesti
- **Toistojen määrä:** 3–5 edestakaista kävelysarjaa (5–10 m matka).  
- **Tallennuksen alku/loppu:**  
  - Tallennus alkaa ensimmäisestä askeleesta, päättyy viimeisen askeleen jälkeen.  
- **Tavoite:** Tunnistaa liikkeen tyyppi ja mitata polven dynaaminen kulma kävelyn aikana.

---

## 4. Osallistujat

| Tunniste | Sukupuoli | Ikä | Rooli |
|-----------|------------|-----|-------|
| H1 | mies | 25 | Testihenkilö 1 (pääpilotti) |
| H2 | nainen | 23 | Testihenkilö 2 |
| H3 | mies | 26 | Aputestaaja / datan tarkkailija |

🧩 **Osallistujien määrä:** 2–3 henkilöä pilottivaiheessa.  
Tavoitteena on arvioida mittauksen toistettavuutta ja tarkkuutta ennen laajempaa datankeruuta.

---

## 5. Kerättävät metrikat

| Mittaus | Kuvaus | Anturin data |
|----------|----------|---------------|
| **Kulmat** | Fleksio, ekstensio, varus/valgus | Euler-kulmat (roll, pitch, yaw) |
| **Kvaternionit** | Avaruuden rotaatioasento | q0, q1, q2, q3 |
| **Kiihtyvyys** | Liikkeen lineaarinen kiihtyvyys | ax, ay, az (m/s²) |
| **Gyroskooppi** | Kulmanopeudet liikeakselien suhteen | gx, gy, gz (°/s) |
| **Aikaleima** | Jokainen datapiste aikaleimataan reaaliaikaisesti | t (ms) |

Datan tallennusmuoto: **CSV**  
Näytteenottotaajuus: **100 Hz**

---

## 6. Turvallisuus ja dokumentointi

- Osallistujille kerrotaan testin kulku ja varotoimet ennen mittausta.  
- Mittausdata anonymisoidaan (vain tunnisteet H1–H3).  
- Kokeen jälkeen data tallennetaan turvallisesti projektin kansioon `/data/raw/`.  
- Mahdolliset poikkeamat (anturin siirtymä, tekniset virheet) kirjataan lokiin `test_log.txt`.

---

## 7. Yhteenveto

Mittausprotokolla tarjoaa toistettavan ja turvallisen menetelmän kerätä IMU-dataa MoveSense-laitteella kyykky- ja kävelyliikkeistä.  
Kerättyä dataa käytetään tekoälymallin kehittämiseen ja polvikulman tarkkuuden validointiin.

---

