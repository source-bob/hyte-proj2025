# 💬 Ohjaajatapaamisen valmistelu v0.1 – AI Motion Analyzer

## 1. Tavoite

Tämän dokumentin tarkoitus on valmistella kysymykset ja keskusteluteemat ohjaajan tapaamista varten (päivä 9 tai 10).  
Tapaamisen tavoitteena on saada palautetta mittausprotokollasta, teknisestä määrittelystä ja projektin etenemissuunnitelmasta.

---

## 2. Kysymyslista ohjaajalle

### 🔹 Tekninen tarkkuus ja hyväksymisrajat
1. Mikä on **vaadittu tarkkuus** (kulma- ja liikeanalyysin virhemarginaali), jotta projekti voidaan hyväksyä kurssilla?  
   - Riittääkö tavoitetaso ±3°, vai onko kurssilla asetettu selkeä raja (esim. < 5°)?  
2. Hyväksytäänkö MoveSense-anturin käyttö yksittäisenä mittauslaitteena, vai tulisiko käyttää kahta anturia (sääri + reisi)?

### 🔹 Mittausprotokolla ja turvallisuus
3. Voimmeko käyttää nykyistä mittausprotokollaa sellaisenaan, vai pitääkö se hyväksyttää erikseen ennen mittausten aloittamista?  
4. Tarvitaanko **eettinen hyväksyntä tai turvallisuusarviointi**, jos käytetään opiskelijoita testihenkilöinä?  
5. Miten projektimme luokitellaan: **tutkimus- vai kehitysprojekti**?  
   - Ja liittyykö siihen **MDR/IEC 60601-standardien** mukaisia vaatimuksia lääkinnällisen laitteen osalta?

### 🔹 Testiosallistujat
6. Kuinka monta testiosallistujaa (pilottivaiheessa) on suositeltavaa?  
   - Riittääkö 2–3 henkilöä, vai tulisiko laajentaa (esim. 5–10)?  
7. Onko sukupuolen, iän tai fyysisen kunnon suhteen suosituksia tai rajoituksia osallistujille?  

### 🔹 Datan käsittely ja yksityisyys
8. Riittääkö, että data anonymisoidaan (H1–H3), vai tuleeko osallistujilta pyytää kirjallinen suostumus?  
9. Onko ohjaajalla suosituksia **tietoturvakäytännöistä** datan säilytyksen ja jakamisen osalta (esim. GitHub, OneDrive)?  

### 🔹 Tekoälymallin rakenne ja validointi
10. Haluamme hyödyntää tekoälyä liikkeiden luokittelussa — pitäisikö mallin **validointi** suorittaa myös ohjatusti (esim. näyttö tunnistuksen onnistumisesta tapaamisessa)?  
11. Riittääkö simuloitu data alkuvaiheessa, vai vaaditaanko todellisia mittauksia ennen lopullista esitystä?

---

## 3. Keskusteluteemat

- Kurssin hyväksymisvaatimukset ja arviointikriteerit  
- Mittausprotokollan virallinen hyväksyntä  
- Testausmäärät ja turvallisuus  
- Datan käsittelyn eettiset näkökulmat  
- AI-mallin kehityksen aikataulu ja palautekäytännöt  

---

## 4. Ehdotus tapaamisen aikataululle

| Päivä | Aika | Kesto | Tapa |
|--------|------|--------|------|
| **Keskiviikko** | klo **11:45 – 12:00** | 15 min | Lähi |

---

# 📊 Mittausprotokolla v0.9 – AI Motion Analyzer

## 1. Tavoite

Määrittää toistettavat ja turvalliset olosuhteet MoveSense-IMU-anturin datankeruulle.  
Dataa käytetään tekoälymallin (CNN) koulutukseen ja validointiin sekä polvikulman analysointiin.

---

## 2. Mittausasetelma

| Elementti             | Kuvaus                                                                 |
|-----------------------|------------------------------------------------------------------------|
| **Anturin sijainti**  | MoveSense-IMU kiinnitetään sääriluun yläosaan joustavalla tarranauhalla. Valinnainen toinen anturi reiden keskiosaan. |
| **Kiinnityksen tarkkuus** | Anturi tiukasti ihoa vasten, nuoli osoittaa eteenpäin liikesuuntaan. |
| **Vaatetus**          | Kevyet urheiluvaatteet; anturi näkyvissä.                              |
| **Alusta**            | Tasainen, liukumaton pinta.                                            |
| **Olosuhteet**        | Sisätila, 20–22 °C, normaali kosteus.                                  |

---

## 3. Mittausprotokolla

### 3.1 Kyykkytesti

- **Toistot**: 5–10 kyykkyä rauhallisesti  
- **Ohje**: Selkä suorana, kyykky n. 90°  
- **Tallennus**: alkaa "Valmis"-komennosta, päättyy 2 s viiveellä  
- **Tavoite**: mitata fleksio/ekstensio ja varus/valgus kuormituksen aikana
### 3.2 Kävelytesti

- **Toistot**: 3–5 edestakaista (5–10 m)  
- **Tallennus**: alkaa ensimmäisestä askeleesta, päättyy viimeiseen  
- **Tavoite**: tunnistaa liikkeen tyyppi ja polvikulman muutos dynaamisessa liikkeessä

---

## 4. Osallistujat

| Tunniste | Sukupuoli | Ikä | Rooli           |
|----------|-----------|-----|-----------------|
| H1       | mies      | 25  | pilottitestaaja |
| H2       | nainen    | 23  | testihenkilö    |
| H3       | mies      | 26  | datan valvoja   |

🧩 Osallistujamäärä 2–3 henkilöä (terveet nuoret aikuiset, kuten ohjaajan hyväksymässä tapaamisessa).

---

## 5. Kerättävät metrikat

| Mittaus      | Kuvaus                     | Data                        |
|--------------|----------------------------|-----------------------------|
| **Kulmat**   | fleksio, ekstensio, varus/valgus | Euler (roll, pitch, yaw)     |
| **Kvaternionit** | rotaatioasento              | q0–q3                        |
| **Kiihtyvyys**   | lineaarinen kiihtyvyys      | ax, ay, az (m/s²)            |
| **Gyroskooppi**  | kulmanopeudet               | gx, gy, gz (°/s)             |
| **Aikaleima**    | reaaliaikainen t (ms)       | automaattinen BLE-yhteys    |

📁 **Tallennusmuoto**: CSV  
📈 **Näytteenottotaajuus**: 100 Hz

---

## 6. Turvallisuus ja dokumentointi

- Osallistujille kerrotaan testin kulku ja mahdolliset riskit.  
- Data anonymisoidaan (H1–H3).  
- Tallennus → `/data/raw/` kansioon; poikkeamat kirjataan `test_log.txt`-tiedostoon.

---

## 7. Yhteenveto

Mittausprotokolla varmistaa toistettavat ja turvalliset mittaukset yhdellä MoveSense-anturilla.  
Kerätty IMU-data toimii pohjana CNN-mallin kehittämiselle ja kulmatarkkuuden validoinnille.


