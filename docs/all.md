## nykyinen [sprinttiraportti_RyhmäA_s2025](https://docs.google.com/spreadsheets/d/1Lcqfv9uUJj410RH7PICg-WAVF7unhfjf/edit?gid=90830429#gid=90830429) Drive:ssa


# 👥 Projektitiimi ja roolit – AIMA

## Tiimin yleiskuvaus

Tässä projektissa kehitetään MoveSense-anturiin perustuva AI-järjestelmä, joka tunnistaa polven liikkeet (kyykky, kävely, sivuttaissiirtymä).  
Projekti kattaa laitteiston, ohjelmiston, tekoälyn ja käyttöliittymän kehityksen.  

> Tämä dokumentti määrittelee vastuualueet ja työnjaon selkeyden vuoksi.

---

## Tiimin kokoonpano

| Rooli | Nimi | Vastuualue |
|-------|------|-------------|
| **Team Lead** | - | Projektin johtaminen, aikataulutus, dokumentointi ja yhteys ohjaajiin |
| **Tech Lead (AI & Data)** | - | Anturidatan käsittely, Python-analytiikka ja tekoälymallien integrointi |
| **Hardware Lead (MoveSense & Prototyyppi)** | - | Anturin liittäminen, kiinnitysratkaisut, prototyypin fyysinen toteutus |
| **Research Lead** | - | Kirjallisuuskatsaus, taustatutkimus ja tutkimuskysymysten määrittely |
| **Protocol Owner** | - | Mittausprotokollan suunnittelu ja valvonta, testien toistettavuuden varmistaminen |
| **Data Engineer** | - | Datan esikäsittely, suodatus, tallennus (CSV) ja tiedon eheys |
| **ML Engineer** | - | AI-luokittelun toteutus, mallin koulutus ja validointi |
| **UI/UX Designer** | - | Käyttöliittymän (Figma) ja visualisoinnin suunnittelu |
| **QA & Validation Engineer** | - | Mittausprotokollan testaus, tulosten validointi ja virhemarginaalien arviointi |
| **Presentation Lead** | - | Mid-review- ja loppuesitysten valmistelu, visuaaliset materiaalit ja viestintä |

> *Huom:* Projektissa kaikki roolit toteutetaan saman henkilön toimesta (ChatGPT-moniroolinen kehitysmalli).

---

## Roolien välinen yhteistyö

- **Team Lead** vastaa kokonaisuuden hallinnasta ja sprinttien koordinoinnista.  
- **Research Lead** ja **Protocol Owner** tekevät yhteistyötä mittausprotokollan ja tutkimuksellisten vaatimusten osalta.  
- **Data Engineer** ja **ML Engineer** muodostavat tekoälyketjun datan käsittelystä mallin validointiin.  
- **Hardware Lead** ja **Tech Lead** varmistavat MoveSense-anturin toimivuuden ja datan luotettavuuden.  
- **QA & Validation Engineer** seuraa mittausten laatua ja dokumentoi tulokset.  
- **Presentation Lead** huolehtii viestinnästä, esityksistä ja raportoinnista ohjaajille.

---

# 📚 Kirjallisuushaun suunnitelma (Taustatutkimus)

---

## 🎯 Tutkimuskysymykset (Research questions)

- **Voiko MoveSense IMU -anturi mitata polven varus/valgus-kulmia tarkkuudella ≤3° liikkeen aikana?**  
- **Kuinka IMU-pohjainen mittaus eroaa videopohjaisesta analyysistä polven linjauksen arvioinnissa?**  
- **Voidaanko tekoälyn avulla luokitella alaraajan liikkeet (kyykky, kävely, sivuttaisliike) MoveSense-datan perusteella?**  
- *(valinnainen)* **Miten polven virheasennot (varus/valgus) liittyvät nivelrikon kehittymiseen?**  
  (Brouwer 2007, Sharma 2010)

💬 *Huomio:* Nämä kysymykset ovat melko erilaisia — kaksi ensimmäistä liittyvät mittaukseen, kolmas tekoälyyn ja neljäs lääketieteeseen. Esityksessä voidaan käyttää ensimmäiset kolme.

---

## 🧭 Tietokannat (Databases)

- **PubMed** – lääketieteelliset tutkimukset (esim. nivelrikko, polven biomekaniikka)  
- **IEEE Xplore** – tekniset artikkelit (esim. IMU, sensoriteknologia)  
- **ScienceDirect** – yleiset terveysteknologian julkaisut  
- **Google Scholar** – laajempi haku ja viitteiden tarkistus  

---

## 🔍 Hakumenetelmiä (Search method examples)

| Pääteema | Hakulause / esimerkkihaku | Tietokanta |
|-----------|----------------------------|-------------|
| **IMU-tarkkuus polvessa** | "varus valgus knee IMU accuracy" | PubMed, IEEE Xplore |
| **MoveSense-validointi** | "MoveSense IMU knee angle validation" | ScienceDirect |
| **Vertailu videomittaukseen** | "IMU vs video knee joint angle error" | IEEE Xplore, Scholar |
| **Polven linjaus ja nivelrikko** | "knee alignment osteoarthritis varus study Brouwer 2007" | PubMed |
| **Tekoäly liikkeentunnistuksessa** | "AI motion classification IMU knee" | ScienceDirect, Scholar |

---

## 👥 Vastuuhenkilöt (Responsibilities)

| Tehtävä | Henkilö |
|----------|----------|
| IMU-tarkkuus ja validointi | **Research Lead** |
| Tekoäly ja liikkeiden luokittelu | **AI / Data Specialist** |
| Polven linjauksen lääketieteellinen tausta |  **Medical Research Advisor** |

---

📄 *Tätä tiedostoa voi myöhemmin täydentää uusilla hakusanoilla, lähteillä tai tutkimuskysymyksillä.*

# 📚 Kirjallisuushaku ja alustava valinta

---

## 🔍 Hakusanat, joita käytettiin

- “varus valgus knee IMU accuracy”  
- “inertial measurement unit knee joint kinematics validation”  
- “MoveSense IMU knee angle”  
- “AI motion classification IMU knee”  
- “knee alignment osteoarthritis varus study Brouwer 2007”  
- “wearable IMU gait analysis knee flexion”  

---

## 🧠 Valitut artikkelit ja tiivistelmät (5 tärkeintä)

| № | Lähde ja linkki | Tavoite | Menetelmät | Keskeinen tulos |
|---|------------------|----------|--------------|------------------|
| **1** | Brouwer et al., 2007 — *Association between valgus and varus alignment and the development and progression of osteoarthritis of the knee* ([PubMed](https://pubmed.ncbi.nlm.nih.gov/17393449/)) | Tutkia, miten polven varus- ja valgusasento vaikuttavat nivelrikon kehittymiseen ja etenemiseen. | Pitkittäistutkimus (6 v), n = 1501, röntgenkuvat. | Varusasento → kaksinkertainen riski nivelrikon kehittymiseen, kolminkertainen etenemiseen. Tuo kliinisen perustan projektin tärkeydelle. |
| **2** | *Knee Angle Estimation with Dynamic Calibration Using Inertial Sensors*, Sensors 2024 ([MDPI](https://www.mdpi.com/1424-8220/24/2/695?utm_source=chatgpt.com)) | Arvioida IMU-antureiden tarkkuus polven kulman mittauksessa dynaamisessa liikkeessä. | Kahden IMU:n (ylä- ja alareisi) mittaus + videoreferenssi. | Keskimääräinen virhe ≈ 3°, korrelaatio > 0.95 videomenetelmään. Tulokset osoittavat, että IMU-mittaus sopii polvikulman seurantaan. |
| **3** | *Validation of Inertial-Measurement-Unit-Based Ex Vivo Knee Joint Angle Estimation*, Sensors 2024 ([MDPI](https://www.mdpi.com/1424-8220/24/11/3324?utm_source=chatgpt.com)) | Validointi IMU-menetelmälle kuormitetussa olosuhteessa. | Ex vivo testaus laboratoriossa, antureiden vertailu referenssijärjestelmään. | Virhe vain 0.9° ± 0.4° abduktio/adduktio-suunnassa → erittäin tarkka järjestelmä. |
| **4** | Jordan et al., 2021 — *Validity of an Inertial Measurement Unit System to Assess Lower-Limb Kinematics*, CEJSSM ([Research Edinburgh](https://www.pure.ed.ac.uk/ws/portalfiles/portal/216369254/JordanEtal2021CEJSSMValidityOfAnInertialMeasurementUnit.pdf)) | Tarkistaa IMU-järjestelmän validiteetin liikkeen aikana. | IMU vs optinen mittaus urheilusuorituksissa. | Hyvä yhteys (r ≥ 0.7), virhe 3.6–4.3°. Soveltuu kenttäolosuhteisiin. |
| **5** | *IMU-Based Fitness Activity Recognition Using CNNs for Time Series Classification*, Sensors 2024  ([MDPI](https://www.mdpi.com/1424-8220/24/3/742?utm_source=chatgpt.com)) | Tutkia 1D-CNN-mallien soveltuvuutta fitness-aktiviteettien luokitteluun IMU-aikasarjadatasta. | IMU-datan käyttö eri liiketyyppien tunnistamiseen 1D-CNN-malleilla. | CNN-pohjaiset mallit pystyvät luokittelemaan liikkeitä luotettavasti, myös yksianturiratkaisuilla. Soveltuu pienimuotoiseen aktiviteettien tunnistukseen.

---

📄 *Tätä osiota voi täydentää lisäämällä linkit DOI-numeroihin, tutkimusten päähuomiot tai uudet artikkelit myöhemmiltä päiviltä.*


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


# 🗒️ Tapaamispöytäkirja v0.1 – AI Motion Analyzer

## 1. Tapaamisen tiedot

| Päivä | Aika | Kesto | Paikka / Tapa |
|--------|------|--------|----------------|
| 29.10.2025 | klo 12:15 | n. 25 min | Kampus / Lähi |

**Osallistujat:**  
- A – opiskelija (projektin vastuuhenkilö)  
- Mikael Soini – ohjaaja / opettaja  

---

## 2. Tapaamisen tavoitteet

- Keskustella mittausprotokollan ja teknisen määrittelyn hyväksynnästä  
- Täydentää validointivaatimukset (virhetaso)  
- Vahvistaa kohderyhmä ja testihenkilöiden määrä  
- Saada hyväksyntä MoveSense-yhteyden toteutukseen (Sprintti 2)

---

## 3. Keskustelun pääkohdat

| Teema | Keskustelun sisältö | Päätös / Kommentit |
|--------|--------------------|--------------------|
| **Validointivaatimukset** | Ohjaaja suositteli keskustelemaan tarkkuusvaatimuksista toisen opettajan kanssa. | Nykyiset tekniset rajat (±1–3°, hyväksyttävä ±5°) säilytetään toistaiseksi opiskelijan päätöksellä, kunnes saadaan lisäohjeistus. |
| **Kohderyhmä** | Mittaukset tehdään omilla raajoilla ja/tai opiskelijaryhmän jäsenillä (2–3 henkilöä). | Kohderyhmä: nuoret aikuiset (terveet opiskelijat). |
| **Mittausprotokolla** | Protokolla on alustava versio. Ohjaaja ehdotti tarkennuksia myöhemmin, kun toinen opettaja on kommentoinut sisältöä. | Käytetään nykyistä versiota toistaiseksi ilman muutoksia. |
| **Anturien määrä ja sijoitus** | Ensimmäisessä versiossa käytetään vain yhtä anturia (säären yläosa). | Hyväksytty. |
| **MoveSense-yhteys ja dataformaatti** | Datan keruu tapahtuu CSV-muodossa. BLE-yhteys otetaan käyttöön Pythonilla. | Hyväksytty. |
| **Tietosuoja ja standardit** | Koska projekti on koulutyö, ei vaadita tietosuojaselvitystä eikä virallisten lääketieteellisten standardien noudattamista. Opiskelija kuitenkin huomioi perusperiaatteet (turvallisuus, riskien minimointi, mahdollinen jatkokehitys). | Hyväksytty. Ei erillisiä toimenpiteitä vaadita. |
| **Sprinttisuunnitelma** | Nykyinen sprinttisuunnitelma arvioitiin toimivaksi ja etenee suunnitellusti. | Hyväksytty. Ei muutoksia. |

---

## 4. Päätökset ja jatkotoimenpiteet

| Päätös | Vastuutaho | Aikataulu |
|---------|-------------|-----------|
| Keskustelu mittausprotokollasta ja validointivaatimuksista järjestetään toisen opettajan kanssa. | **Team Lead** | mahdollisimman pian |
| Nykyistä teknistä määrittelyä ja mittausprotokollaa käytetään toistaiseksi sellaisenaan. | **Tech Lead (AI & Data)** | heti |
| MoveSense-yhteys toteutetaan yhdellä anturilla, CSV-formaatilla. | **Hardware Lead (MoveSense & prototyyppi)** | Sprintti 2 aikana |
| Ei tarvetta tietosuojaselvitykselle tai standardidokumenteille, mutta perusperiaatteet huomioidaan. | **QA & Validation Engineer** | jatkuva |


---

## 5. Yhteenveto

Tapaamisessa varmistettiin, että projekti etenee suunnitellusti.  
Ohjaaja ei vielä vahvistanut teknistä määrittelyä tai mittausprotokollaa, vaan suositteli lisäkeskustelua toisen opettajan kanssa validointivaatimusten ja mittausmenetelmien osalta.  
Opiskelija jatkaa kuitenkin nykyisen version pohjalta, jotta aikataulu pysyy hallittuna.  
MoveSense-yhteys toteutetaan yhdellä anturilla CSV-muodossa, ja kohderyhmäksi vahvistettiin terveet nuoret aikuiset (opiskelijat).  

---


# ⚠️ Riskianalyysi v0.9 – AI Motion Analyzer

## 1. Johdanto

Tässä dokumentissa arvioidaan AI Motion Analyzer (AIMA) -projektin keskeiset riskit ja rajoitukset.  
Koska projekti toteutetaan koulutyönä eikä sitä luokitella lääkinnälliseksi laitteeksi, arviointi keskittyy prototyypin käytön, datan käsittelyn ja eettisten näkökulmien turvallisuuteen.

---

## 2. Riskitaulukko

| **Riski** | **Todennäköisyys** | **Vaikutus** | **Vähennystoimet** | **Huomio sääntelyyn ja etiikkaan** |
|----------|--------------------|--------------|---------------------|-------------------------------------|
| Anturin siirtymä liikkeen aikana | Keskitaso | Keskitaso | Käytä joustavaa kiinnitystä ja tarkista anturin sijainti ennen mittausta. | Ei MDR-vaatimuksia, mutta noudatetaan turvallisen käytön periaatteita. |
| Anturin puristus / epämukavuus | Matala | Keskitaso | Testaa kiinnitys omalla raajalla ennen käyttöä, varmista ettei paina ihoa. | Fyysinen turvallisuus huomioitu (ei kliininen käyttö). |
| Datan virheellisyys / kalibroinnin puute | Keskitaso | Keskitaso | Suorita testikalibrointi ennen mittausta; varmista anturin orientaatio (yksi anturi lisää kalibrointiriippuvuutta). | Ei eettistä riskiä, mutta vaikutus validointiin. |
| BLE-yhteyden katkeaminen tallennuksen aikana | Keskitaso | Matala | Toteuta automaattinen uudelleenkytkentä tai varoitus käyttöliittymässä. | Tekninen riski, ei eettinen. |
| Osallistujien tietosuoja (tallennettu data) | Matala | Matala | Käytä anonyymejä tiedostonimiä (esim. “H1_data.csv”), älä tallenna henkilötietoja. | GDPR-periaatteet huomioitu, vaikka virallista vaatimusta ei ole. |
| Laitteen rikkoutuminen tai yhteyden menetys mittauksen aikana | Matala | Keskitaso | Käytä varmistettua kiinnitystä ja suojaa anturi kolhuilta. | Ei MDR-vaatimuksia, mutta noudatetaan prototyyppiturvallisuutta. |
| Eettinen suostumus osallistujilta | Matala | Korkea | Kerro mittauksen tarkoitus ja pyydä suullinen suostumus ennen tallennusta. | Eettinen periaate, ei virallinen vaatimus. |
| AI-mallin väärä luokittelu (CNN-mallin virhetulkinta) | Keskitaso | Keskitaso | Lisää datan validointi ja manuaalinen tarkistus Pythonilla; konfiguroi CNN uudelleen tarvittaessa. | Ei kliininen riski, mutta tärkeä kehitysvaiheessa. |
| AI-mallin ylitulkinta / datan vinouma (bias) | Matala | Keskitaso | Käytä monipuolista opetusdataa ja testaa eri liikesarjoilla; vältä ylioppimista. | Eettinen huomio: vääristynyt malli voi antaa virheellisiä tuloksia. |

---

## 3. Yhteenveto

Projektin riskit liittyvät ensisijaisesti teknisiin ja mittaustilanteen käytännön riskeihin.  
Eettiset ja tietosuojariskit ovat matalia, koska mittaukset tehdään pienellä opiskelijaryhmällä ilman henkilötietoja.  
AI-mallin käyttö tuo uusia mutta hallittavia riskejä, kuten väärät luokitukset tai datan bias, jotka minimoidaan validoinnilla, kalibroinnilla ja monipuolisella datalla.

Kaikki riskit arvioidaan ja hallitaan prototyyppivaiheen aikana ennen mahdollisia jatkokehitysversioita.


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


# 📊 Mittausprotokolla v1.0 – AI Motion Analyzer

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
- **Tallennus**: alkaa "Valmis"-komennosta, päättyy automaattisesti 30 sekunnin jälkeen.  
- **Tavoite**: mitata fleksio/ekstensio ja varus/valgus kuormituksen aikana
### 3.2 Kävelytesti

- **Toistot**: 3–5 edestakaista (5–10 m)  
- **Tallennus**: alkaa ensimmäisestä askeleesta, päättyy automaattisesti 30 sekunnin jälkeen.
- **Tavoite**: tunnistaa liikkeen tyyppi ja polvikulman muutos dynaamisessa liikkeessä

>Näytteenottotaajuus 100 Hz, datankeruu jatkuvana BLE-yhteyden kautta.

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
| **Magneettikenttä** | suunnan vakautus ja kalibrointi | mx, my, mz (µT)  
| **Aikaleima**    | reaaliaikainen t (ms)       | automaattinen BLE-yhteys    |

📁 **Tallennusmuoto**: CSV  
📈 **Näytteenottotaajuus**: 104 Hz

---

## 6. Turvallisuus ja dokumentointi

- Osallistujille kerrotaan testin kulku ja mahdolliset riskit.  
- Data anonymisoidaan (H1–H3).  
- Tallennus → `/data/raw/` kansioon; poikkeamat kirjataan `test_log.txt`-tiedostoon.

---

## 7. Yhteenveto

Mittausprotokolla varmistaa toistettavat ja turvalliset mittaukset yhdellä MoveSense-anturilla.  
Kerätty IMU-data toimii pohjana CNN-mallin kehittämiselle ja kulmatarkkuuden validoinnille.

>Mittausprotokollaa päivitettiin vastaamaan todellisia mittausparametreja (100 Hz, 30 s, 10 datariviä per näyte).
>Tämä versio toimii pohjana datankeruun ja suodatuksen toteutukselle Sprintti 2:n aikana.




# 📋 Suunniteltu käyttö ja käyttäjäprofiilit (v0.1)

| Käyttäjä | Käyttökonteksti | Tehtävä | Käyttötiheys | Toiminnalliset vaatimukset | Ei-toiminnalliset vaatimukset | Rajoitukset |
|-----------|-----------------|----------|---------------|-----------------------------|-------------------------------|--------------|
| **Urheilija (nuori, 18–30 v)** | Kuntosali tai urheiluhalli | Kyykky- ja askelharjoitusten analysointi ja palautteen saanti | Päivittäin tai useita kertoja viikossa | Järjestelmä tunnistaa liikkeen (kyykky, askel, sivuttaisliike) ja antaa palautteen heti | Tarkkuus ±3°, vasteaika < 1 s | Anturin kiinnitys polveen, ei saa liikkua harjoituksen aikana; ei vedenkestävä |
| **Kuntoutuja (leikkauksen jälkeen)** | Koti / fysioterapian vastaanotto | Polven koukistusliikkeiden seuranta ja edistymisen arviointi | 3–5 kertaa viikossa | Näyttää liikkeen kulman ja kehityksen ajan myötä, antaa suosituksia liikkeen toistosta | Tarkkuus ±2°, vasteaika < 2 s | Anturin oltava mukava pitkässä käytössä; vaatetus ei saa estää liikettä |
| **Ikääntynyt käyttäjä (65+)** | Kotiympäristö | Kävelyn linjauksen seuranta ja mahdollisten poikkeamien tunnistus | 1–2 kertaa viikossa | Tunnistaa epävakaat liikkeet tai poikkeamat polven linjauksessa | Tarkkuus ±4°, yksinkertainen käyttöliittymä | Ei liikaa painoa anturissa; käyttö helppoa ilman ohjausta |


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
