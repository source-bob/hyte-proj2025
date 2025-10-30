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
