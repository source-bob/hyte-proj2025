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