# 🧭 Taustatutkimus v0.9 – AI Motion Analyzer

## 1. Johdanto

Tämän projektin tavoitteena on kehittää tekoälypohjainen järjestelmä, joka hyödyntää MoveSense-IMU-anturia alaraajan liikkeiden tunnistamiseen ja polven linjauksen (varus/valgus) analysointiin.
Polven virheasennot, kuten varus ja valgus, liittyvät merkittävästi nivelrikon riskiin ja etenemiseen (Brouwer et al., 2007).

Projektimme yhdistää terveysteknologian ja tekoälyn tarjotakseen kannettavan, reaaliaikaisen ja kustannustehokkaan tavan liikkeiden seurantaan ilman laboratorio-olosuhteita.
Kehitys toteutetaan yhdellä anturilla (säären yläosa), ja kohderyhmänä ovat terveet nuoret aikuiset (opiskelijat).
Koska projekti on osa koulukurssia, sitä ei luokitella lääkinnälliseksi laitteeksi, mutta suunnittelussa huomioidaan perusperiaatteet, kuten turvallisuus, riskien minimointi ja jatkokehityskelpoisuus.

---

## 2. Kirjallisuusanalyysi

Kirjallisuuskatsaus perustuu viiteen keskeiseen julkaisuun, jotka kattavat sekä kliinisen taustan että IMU-teknologian ja tekoälyn sovellukset liikkeiden analysoinnissa.

### 2.1 Virhemarginaalit

Tutkimusten perusteella IMU-anturit kykenevät mittaamaan polvikulmaa 1–4° tarkkuudella, mikä vastaa kliinisiä vaatimuksia:

- Keskimääräinen virhe vaihtelee **0.9° – 4.3°**, riippuen liikkeen nopeudesta, kalibroinnista ja referenssistä ([Jordan et al., 2021](https://www.research.ed.ac.uk/files/216369254/JordanEtal2021CEJSSMValidityOfAnInertialMeasurementUnit.pdf); [Sensors 2024](https://www.mdpi.com/1424-8220/24/2/695)).
- Ex vivo -olosuhteissa virhe on jopa **alle 1°**, mikä on kliinisesti merkityksetön ([Sensors 2024, Ex Vivo](https://www.mdpi.com/1424-8220/24/11/3324)).
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

Tässä projektissa käytetään yksinkertaistettua versiota (vain yksi anturi), joka soveltuu hyvin **peruspilotille ja kehityskäyttöön**.  
Useimmat tutkimukset suoritettiin **10–20 osallistujalla**, mutta kouluprojektissa osallistujamäärä rajoitetaan 2–3 henkilöön.

### 2.4 Tekoälyn rooli

Uusimpien tutkimusten mukaan **1D-CNN-pohjaiset** mallit soveltuvat erinomaisesti IMU-aikasarjadataan ja voivat luokitella liikkeet (esim. kyykky, kävely, sivuttaisaskel) erittäin tarkasti.
- Sensors (2024) -julkaisun mukaan CNN-mallit saavuttavat >93 % tarkkuuden fitness-liikkeiden tunnistuksessa jopa yksianturiratkaisulla, mikä tekee menetelmästä kevyen ja helposti integroitavan.
- Malli kykenee erottamaan liikkeiden piirteitä suoraan kiihtyvyys- ja gyroskooppidatasta ilman lisäsensoreita tai kameradataa.

Tämä tukee projektin tavoitetta kehittää reaaliaikainen ja helposti käytettävä AI-moduuli, joka voi analysoida MoveSense-datan ja antaa välittömän palautteen käyttäjälle esimerkiksi kuntoutuksen tai urheiluharjoittelun yhteydessä.

---

## 3. Keskeiset havainnot

- IMU-järjestelmät saavuttavat 1–4° tarkkuuden polvikulman mittauksessa, mikä täyttää kliiniset rajat.
- Video- ja optiset menetelmät toimivat edelleen referenssinä, mutta IMU tarjoaa kannettavan ja skaalautuvan vaihtoehdon.
- CNN-pohjainen tekoäly mahdollistaa liikkeiden tunnistamisen ilman visuaalista seurantaa, myös yhdellä anturilla.
- Tekniikka soveltuu rehabilitaatioon, urheiluanalytiikkaan ja nivelrikon varhaiseen havaitsemiseen.
- Projekti toimii kehitysalustana tuleville lääkinnällisille sovelluksille, joissa vaaditaan reaaliaikaista biomekaanista analyysiä.

---

## 4. Miksi tämä on tärkeää

> Tämä tutkimus yhdistää terveysteknologian, tekoälyn ja biomekaniikan käytännön sovellukseksi.
MoveSense-antureiden avulla voidaan seurata polven liikkeitä ilman laboratorioita, ja CNN-pohjainen tekoäly voi tunnistaa liikkeen tyypin ja mahdolliset poikkeamat reaaliajassa.
Näin voidaan tukea kuntoutusta, urheilusuoritusten analyysiä ja nivelrikon varhaista tunnistusta, mikä parantaa elämänlaatua ja vähentää terveydenhuollon kuormitusta.

---

## 5. Lähteet

1. Brouwer G.M. et al. *Association between valgus and varus alignment and the development and progression of osteoarthritis of the knee.* Arthritis & Rheumatism, 56(4), 1204–1211, [2007](https://pubmed.ncbi.nlm.nih.gov/17393449/)  
2. Jordan M.J. et al. *Validity of an Inertial Measurement Unit System to Assess Lower-Limb Kinematics.* CEJSSM, [2021](https://www.pure.ed.ac.uk/ws/portalfiles/portal/216369254/JordanEtal2021CEJSSMValidityOfAnInertialMeasurementUnit.pdf)  
3. *Knee Angle Estimation with Dynamic Calibration Using Inertial Sensors.* Sensors, [2024](https://www.mdpi.com/1424-8220/24/2/695?utm_source=chatgpt.com)  
4. *Validation of Inertial-Measurement-Unit-Based Ex Vivo Knee Joint Angle Estimation.* Sensors, [2024](https://www.mdpi.com/1424-8220/24/11/3324?utm_source=chatgpt.com)  
5. *IMU-Based Fitness Activity Recognition Using CNNs for Time Series Classification.* Sensors, [2024](https://www.mdpi.com/1424-8220/24/3/742?utm_source=chatgpt.com)

---


> (päivitetty versio ohjaajan tapaamisen jälkeen)
