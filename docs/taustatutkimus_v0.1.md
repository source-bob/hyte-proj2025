# 🧭 Taustatutkimus v0.1 – AI Motion Analyzer

## 1. Johdanto

Tämän projektin tavoitteena on kehittää tekoälypohjainen järjestelmä, joka hyödyntää MoveSense-IMU-anturia alaraajan liikkeiden tunnistamiseen ja polven linjauksen (varus/valgus) analysointiin.  
Polven virheasennot, kuten varus ja valgus, liittyvät merkittävästi nivelrikon riskiin ja etenemiseen.  
Aiemmat tutkimukset ovat osoittaneet, että varusasento kaksinkertaistaa nivelrikon kehittymisen riskin (Brouwer et al., 2007).  

Projektimme yhdistää terveysteknologian ja tekoälyn tarjotakseen kannettavan ja reaaliaikaisen tavan liikkeiden seurantaan ilman laboratorio-olosuhteita.

---

## 2. Kirjallisuusanalyysi

Kirjallisuuskatsaus perustuu viiteen keskeiseen julkaisuun, jotka käsittelevät sekä kliinistä taustaa että IMU-teknologian ja tekoälyn sovelluksia liikkeiden analysoinnissa.

### 2.1 Virhemarginaalit

Useiden tutkimusten perusteella IMU-anturit kykenevät mittaamaan polvikulmaa erittäin tarkasti:

- Keskimääräinen virhe vaihtelee **0.9° – 4.3°**, riippuen liikkeen nopeudesta ja kalibrointimenetelmästä ([Jordan et al., 2021](https://www.research.ed.ac.uk/files/216369254/JordanEtal2021CEJSSMValidityOfAnInertialMeasurementUnit.pdf); [Sensors 2024](https://www.mdpi.com/1424-8220/24/2/695)).
- Ex vivo-olosuhteissa virhe on jopa **alle 1°**, mikä on kliinisesti merkityksetön ([Sensors 2024, Ex Vivo](https://www.mdpi.com/1424-8220/24/11/3324)).
- Dynaamisessa liikkeessä virhemarginaali pysyy **noin 3°**, mikä on hyväksyttävissä kenttäkäytössä.

### 2.2 Referenssimenetelmät

Kaikissa validointitutkimuksissa IMU-tuloksia verrattiin **videopohjaisiin tai optisiin mocap-järjestelmiin**, jotka toimivat “kultaisena standardina”.

- Videoseuranta (2D / 3D) antaa erittäin tarkan kulma-arvion, mutta vaatii kiinteät olosuhteet ja laboratorioinfrastruktuurin.  
- IMU tarjoaa **liikkuvan ja kannettavan vaihtoehdon**, jonka tarkkuus on lähes vastaava.

### 2.3 Testausprotokollat

Tyypillisesti IMU-validointi sisältää:
- kahden anturin käyttö (reidessä ja sääressä),  
- kalibroinnin ennen liikettä (esim. dynaaminen nollaus),  
- vertailun referenssijärjestelmään (video/optinen mocap),  
- liikkeet kuten **kävely, kyykky ja polven fleksio-ekstensio**.  

Useimmat tutkimukset suoritettiin **10–20 osallistujalla**, ja datan käsittely sisälsi **Kalman- tai Madgwick-suodattimia** virheiden minimoimiseksi.

### 2.4 Tekoälyn rooli

Vuoden 2023 Frontiers-julkaisun mukaan CNN-pohjainen malli pystyy tunnistamaan liikkeet IMU-datasta yli **93 %:n tarkkuudella**.  
Tämä osoittaa, että tekoäly voi oppia erottelemaan liikkeiden piirteitä raakadatan perusteella ja tarjota välitöntä palautetta käyttäjälle.  
Yhdistämällä MoveSense-anturi ja kevyen AI-mallin voimme luoda älykkään, reaaliaikaisen seurantasovelluksen esimerkiksi polvivaivojen kuntoutukseen.

---

## 3. Keskeiset havainnot

- IMU-järjestelmät saavuttavat **1–4°** tarkkuuden polvikulman mittauksessa, mikä vastaa kliinisiä vaatimuksia.  
- Video- ja optiset menetelmät toimivat edelleen referenssinä, mutta IMU tarjoaa **kannettavan ja kustannustehokkaan vaihtoehdon**.  
- AI-pohjainen luokittelu tekee mahdolliseksi liikkeiden tunnistamisen ja analyysin ilman visuaalista seurantaa.  
- Teknologia soveltuu **rehabilitaatioon, urheiluun ja nivelrikon varhaiseen havaitsemiseen**.

---

## 4. Miksi tämä on tärkeää

> Tämä tutkimus on tärkeä, koska se yhdistää terveysteknologian, tekoälyn ja biomekaniikan.  
> MoveSense-antureiden avulla voidaan seurata polven liikkeitä ilman laboratorioita, ja tekoäly voi tunnistaa poikkeamat liikkeessä reaaliajassa.  
> Näin voidaan tukea **varhaista diagnoosia, kuntoutuksen tehokkuutta ja urheilijoiden liikeanalyysiä**, mikä parantaa elämänlaatua ja vähentää terveydenhuollon kuormitusta.

---

## 5. Lähteet

1. Brouwer G.M. et al. *Association between valgus and varus alignment and the development and progression of osteoarthritis of the knee.* Arthritis & Rheumatism, 56(4), 1204–1211, [2007](https://pubmed.ncbi.nlm.nih.gov)
2. Jordan M.J. et al. *Validity of an Inertial Measurement Unit System to Assess Lower-Limb Kinematics.* CEJSSM, [2021](https://www.mdpi.com) 
3. *Knee Angle Estimation with Dynamic Calibration Using Inertial Sensors.* Sensors, [2024](https://www.mdpi.com).  
4. *Validation of Inertial-Measurement-Unit-Based Ex Vivo Knee Joint Angle Estimation.* Sensors, [2024](https://www.research.ed.ac.uk).  
5. *AI-Based Human Activity Recognition Using IMU Sensors for Rehabilitation and Sports.* Frontiers in Bioengineering & Biotechnology, [2023](https://www.frontiersin.org).

---
