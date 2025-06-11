# Introduksjon

![QGIS 3.34+ required](https://img.shields.io/badge/QGIS-3.34%252B-green?logo=qgis&logoColor=white)

<a href="nin_qgis_plugin/README_english.md" style="padding: 6px 12px; background-color: #007acc; color: white; border-radius: 4px; text-decoration: none;">🌐 Switch to English</a>

## Bakgrunn

Artsdatabanken lanserte Natur i Norge (NiN) versjon 3.0 i 2024. I den forbindelse er det utviklet et programtillegg (plugin) for QGIS som tilrettelegger for feltbasert kartlegging etter NiN 3.0.

Formålet med programtillegget er å gjøre NiN-kartlegging mer tilgjengelig og effektiv -- både for fagpersoner og brukere uten spesialisert teknisk kompetanse.

## Om veilederen

Denne veilederen gir en praktisk innføring i bruk av programtillegget, og forutsetter at brukeren har grunnleggende kjennskap til kartlegging etter NiN 3.0. Veilederen viser hele arbeidsflyten -- fra oppsett i QGIS til bruk i felt og etterarbeid.

Programtillegget dekker alle typesystemer og tilpassede målestokker i NiN 3.0, men omfatter foreløpig ikke variabelsystemet.

📘 [Les veilederen her](https://geco-nhm.github.io/nin-qgis-plugin/)

# Installering

Programtillegget kan installeres via programtilleggsmenyen i QGIS:

1.  Åpne QGIS
2.  Gå til `Plugins` → `Manage and Install Plugins...`
3.  Søk etter "Natur i Norge kartlegging"
4.  Klikk `Installer`

## Alternativ: Installer siste versjon via GitHub

Ettersom utviklingen skjer løpende, lastes nye versjoner jevnlig opp til GitHub. Dersom du ønsker den nyeste versjonen før den er tilgjengelig i QGIS-programtilleggsbiblioteket, kan du:

-   Gå til <https://github.com/Artsdatabanken/nin-innsyn>
-   Last ned `.zip`-filen
-   Pakk ut og legg til manuelt via `Plugins` → `Install from ZIP`

# Bruk

## Funksjoner

Programtillegget gir deg følgende valgmuligheter for å sette opp et tilpasset kartleggingsprosjekt:

-   Velge typesystem og relevante hovedtypegrupper
-   Velge ønsket kartleggingsmålestokk
-   Velge lagringsplassering for prosjektet
-   Definere koordinatsystem for prosjekt og `.gpkg`-filer
-   Velge bakgrunnskart

## Komme i gang

1.  Åpne QGIS
2.  Installer og aktiver programtillegget
3.  Åpne programtillegget og opprett prosjekt ved å velge:
    -   Typesystem
    -   Kartleggingsmålestokk
    -   Koordinatsystem
    -   Lagringsmappe
    -   Ønskede bakgrunnskart
4.  Klikk på `Lag geopackage-fil og forbered prosjekt`

**Dette oppretter automatisk:**

-   En QGIS-prosjektfil
-   En `.gpkg`-fil med nødvendige kartlag tilpasset kartleggingsformålet

**Resultat:**

-   Alle kartlag fra `.gpkg`-filer lastes inn
-   Hierarkiske relasjoner opprettes (mellom hovedtyper og hovedtypegrupper)
-   `Topological editing` aktiveres
-   `Avoid overlap` aktiveres i `nin_polygons`
-   Snapping settes til 5 px (hjørner og segmenter)
-   Kartlaget `nin_polygons` settes opp med:
    -   Tilfeldig fargesymbologi
    -   Skriftmarkering (label) basert på grunntype innenfpr den utvalgte hovedtypegruppen

## Videre tilpasning

Dersom prosjektet krever et annet oppsett enn det som er gitt av standardinnstillingene:

-   Legg til egne raster- eller vektordata (f.eks. flybilder, verneområder, høydedata) via vanlige QGIS-funksjoner
-   Opprett nye lag, symbologi eller tilpass layout etter behov

## Eksport til QField

Etter at prosjekt og `.gpkg`-filer er opprettet kan det overføres til QField for bruk i felt:

1.  Kopier hele prosjektmappen til mobil/nettbrett/felt-PC
2.  Åpne prosjektet i QField
3.  Start kartlegging ute i felt

Når feltarbeidet er ferdig kan dataene synkroniseres tilbake til QGIS for videre bearbeiding.

## Kartleggingsprosedyre

1.  Velg laget `nin_polygons`
2.  Slå på redigering
3.  Legg til nytt polygon
4.  Fyll ut NiN-informasjon i attributtskjemaet
5.  Velg relevante variabler for valgt type
6.  Hvis polygonen inneholder flere naturtyper:
    -   Sett "Andel av naturtype" til mindre enn 100
    -   Velg "sammensatt" eller "mosaikk"
7.  Ta eventuelt bilde (hvis enheten har kamera)
8.  Klikk OK for å lagre polygonet

Kartleggingsveiledning finnes på [Artsdatabankens nettsider](https://www.artsdatabanken.no).

# For utviklere

Kode er tilgjengelig via GitHub: <https://github.com/geco-nhm/nin-qgis-plugin>

## Funksjonalitet

-   Generering av QGIS-prosjekt og `.gpkg`-filer
-   Automatisk oppsett av kartlag og symbologi
-   Støtte for eksport til QField

## Bidra

Utviklere og fagpersoner inviteres til å bidra gjennom:

-   Feilrapporter
-   Forslag til forbedringer
-   Pull requests på GitHub

# Hjelp

[Hjelpesider for QGIS](https://docs.qgis.org/3.34/en/docs/training_manual/index.html)\
[Hjelpesider for QField](https://docs.qfield.org/get-started/tutorials/get-started-qfs/)\
[Hjelpesider for NiN](https://naturinorge.artsdatabanken.no/)

# Forfattere

Navn og kontakinfo: \@ [Lasse Keetz](https://github.com/orgs/geco-nhm/people/lasseke) \@ [Peter Horvath](https://github.com/orgs/geco-nhm/people/peterhor) \@ [Anne B. Nilsen](https://github.com/orgs/geco-nhm/people/9ls1)

Programtillegget ble utviklet med finansiell støtte fra [NINA](https://www.nina.no/)

Ikonet som brukes for programtillegget ble lastet ned fra <a href="https://www.flaticon.com/free-icons/enviroment" title="enviroment icons">Flaticon - Enviroment icons created by Eucalyp</a>