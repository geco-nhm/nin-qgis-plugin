# Kartografi for NiN 3.0

Denne mappa dokumenterer kartografien for kartleggingsenheter i NiN 3.0 i
målestokkene 1:5 000, 1:20 000 og 1:50 000. Arbeidet skjer i flere steg.
Planen og status står i [symbology/PLAN.md](../../symbology/PLAN.md).

| Steg | Innhold | Status |
| --- | --- | --- |
| 1 | Fyllfarge for hver hovedtype | Utkast 2, revidert etter kommentarene til NiN 2-utkastet |
| 2 | Skravur og symboler for kartleggingsenhetene, i tre målestokker | Ikke startet |
| 3 | Stilfiler for QGIS (QML) | Ikke startet |
| 4 | Kartografien tas i bruk i programtillegget | Ikke startet |

Hver hovedtypegruppe har en grunnfarge. For fastmarkssystemer (NA-T) og
våtmarkssystemer (NA-V) har hver av de 72 hovedtypene sin egen farge. De
andre gruppene tegnes foreløpig med grunnfargen.

## Prinsipp

Kartet bruker tre uavhengige virkemidler. Hvert av dem svarer på ett spørsmål.

| Virkemiddel | Viser | Lik i alle målestokker |
| --- | --- | --- |
| Fyllfarge | Hovedtype | Ja |
| Skravur og symboler | Kartleggingsenhet innen hovedtypen | Forfines med målestokken |
| Påskrift | Kode, for eksempel `TB01-05` | Koden følger målestokken |

Alle figurer har tynt, hvitt omriss. Omrissfarge bærer ikke informasjon.

## Steg 1: farger

Oversikten ligger i [fargeoversikt.html](fargeoversikt.html). Åpne fila i en
nettleser.

Hovedtyper som hører sammen økologisk, har farger fra samme fargefamilie og
skiller seg fra hverandre i lyshet og litt i fargetone.

| Fargefamilie | Fargetone | Hovedtyper |
| --- | --- | --- |
| Skogsmark | Grønn | TB01, TF01, TF02, TI01, TM06 |
| Fjellhei og snøleie | Lysebrun; snøleie nesten hvit | TA03, TA04, TD06, TC08 |
| Naturlig åpen eng | Strågul | TC05, TC06, TC07, TD04, TD05, TE08 |
| Semi-naturlig eng | Gul | TK01, TK02, TL01, TN02 |
| Hei | Oker | TK03, TH01 |
| Jordbruksmark og grøntanlegg | Oransje til lakserød | TO01–TO04, TN01, TN03 |
| Berg | Grå | TA01, TA02, TC01, TC02 |
| Løsmasser og strand | Sand og gråbeige | TG01, TC03, TC04, TE01, TE03, TE04, TE06, TE07 |
| Ras-, skred- og frostmark | Brun | TD01, TD02, TD03, TE02, TE05, TE09 |
| Sterkt endret fastmark | Nøytral grå | TM01–TM05 |
| Myr og åpen våtmark | Lilla | VA01, VC01, VC05, VE01, VG01, VG02 |
| Kilde | Blålilla | VC02, VC03, VC04 |
| Våtmarksskogsmark | Blågrønn | VB01, VF01, VF02, VI01 |
| Semi-naturlig våtmark | Rosa | VK01, VK02 |
| Sterkt endret våtmark | Grålilla til magenta | VM01–VM06, VO01 |

### Krav til fargene

Kravene kontrolleres automatisk av `symbology_tools/palette.py` og av
enhetstestene. Fargeforskjell måles som avstand i fargerommet OKLab, der 0,02
er så vidt synlig.

| Krav | Grense | Utkast 2 |
| --- | --- | --- |
| Alle hovedtyper med kartleggingsenheter har en farge | 72 av 72 | Oppfylt |
| Minste fargeforskjell mellom to farger | 0,03 | 0,034 |
| Minste fargeforskjell fra en arealmessig dominerende hovedtype til alle andre farger | 0,045 | 0,047 |
| Minste fargeforskjell mellom skogsmark og fjellhei eller fjellgrasmark | 0,08 | 0,095 |
| Klar grønn brukes bare på skogsmark og våtmarksskogsmark | Ingen unntak | Oppfylt |
| Lyshet, slik at skravur og påskrift er lesbar oppå fargen | 0,50 til 0,96 | Oppfylt |
| Hver fargefamilie har minst én ledig farge holdt av | 15 av 15 | Oppfylt |

Arealmessig dominerende hovedtyper er TA01, TA02, TA03, TA04, TB01, VA01 og
VB01.

### Kjent begrensning: fargesyn

Det er ikke mulig å holde 72 farger fra hverandre for alle typer fargesyn.
Med simulert rød-grønn fargesvakhet blir 18 til 22 av 2 556 fargepar
vanskelige å skille. Derfor bærer også skravur og påskrift informasjon, og
fargen alene skal aldri være eneste kjennetegn.

## Kommentarer til NiN 2-utkastet og hvordan de er fulgt opp

Utkastet til kartografi for NiN 2 fra desember 2020 har kommentarer fra
fagpersoner i NiN-miljøet, med svar fra forfatteren.

Typekodene er nye i NiN 3.0. Tabellen bruker kodene fra NiN 2 slik de står i
kommentarene, og viser hvilke hovedtyper i NiN 3.0 de gjelder.

### Fulgt opp i steg 1 (farger)

| Kommentar | Oppfølging |
| --- | --- |
| Grønn grunnfarge bør være forbeholdt skog (T5, T6, T7, T22, T23, T24, T25, T28, T29) | Klar grønn brukes bare i familiene skogsmark og våtmarksskogsmark. Kontrolleres automatisk |
| Større forskjell mellom T3 fjellhei og T4 skog; skillet mellom skog og fjell er avgjørende | TA03 og TA04 er lysebrune, TB01 er grønn. Forskjellen er 0,095 og kontrolleres automatisk |
| De arealmessig dominerende hovedtypene (T1–T4, V1, V2) må skille seg fra alle andre; T1–T4 er altfor like | Eget krav på 0,045 for TA01–TA04, TB01, VA01 og VB01 |
| Farger bør følge tradisjonen i vegetasjonskartlegging og ligne naturen | Fargefamilier med begrunnelse i `colour_families.csv` |
| Snøleie bør være hvit med skravur, ikke grønn | TC08 Snøleie er nesten hvit med svakt lilla skjær |
| T6 Strandberg bør ligne T1 Nakent berg | TC01 og TA01 er begge grå, i familien berg |
| Rasmark og skredmark (T13, T16, T17, T25) bør ha beslektede grunnfarger | TD01, TD02, TD03 og TE02 er samlet i den brune familien ras-, skred- og frostmark |
| Sand vises i lys brun; stein og grus i grått sammen med bart fjell | TG01 og TE01 er sandfarget; TC03 er gråbeige |
| Blå grunnfarger forbeholdes limnisk og våtmark | Ingen fastmarkstype har blå grunnfarge. Flommark (TE03, TE04) er kjølig grå |
| Bytt grunnfarge mellom V1 og V3: nedbørsmyr er fattig og lavproduktiv, jordvannsmyr rikere | VA01 har sterkere og mørkere lilla enn VC01. Kontrolleres automatisk |
| V2 og V8 må vises tydeligere som skog | Våtmarksskogsmark er blågrønn. Grønne symboler kommer i steg 2 |
| T38 Treplantasje oppfattes som skog av alle og bør harmoniseres med T4 | TI01 og TM06 ligger i den grønne skogfamilien |
| Moderat og sterkt endrete systemer bør ha farger som skiller seg klart fra naturlige | Egne familier: sterkt endret fastmark (grå) og sterkt endret våtmark (grålilla til magenta) |
| Hvitt omriss rundt alle klasser; omrissfarge er vanskelig å lese | Alle figurer har hvitt omriss. Omrissfarge bærer ikke informasjon |
| Vis grunnfarge for alle sju hovedtypegrupper, og la dokumentet følge hierarkiet | `hovedtypegruppe_colours.csv`. Oversikten starter med hovedtypegruppene |
| Kan fargepaletter eller symboler holdes av til systemet endres? Kan typer enkelt legges til og trekkes fra? | `reserved_colours.csv` har ledige farger i hver familie. Farger er lagret per kode og endres ikke når nye typer kommer til |
| Kodene bør ha ledende nuller slik at de sorteres riktig | Løst i NiN 3.0: kodene har ledende nuller (`TB01-M005-01`) |
| Antall klasser er usikkert; bruk Artsdatabanken som fasit | Alt leses fra katalogen som hentes fra Artsdatabankens API. En test melder fra når katalogen og fargene ikke stemmer overens |
| Stilfiler i QML kan bare brukes i QGIS | Symbolene lagres i åpne CSV-tabeller. QML lages fra tabellene i steg 3 |

### Skal følges opp i steg 2 (skravur og symboler)

| Kommentar | Regel for steg 2 |
| --- | --- |
| Alt som er knyttet til fuktighet og vann, bør vises med blått (T15, T18, T30, T31-C-13/14, T32-C-9/10) | Blå skravur eller blå symboler betyr vannpåvirkning: kilde, flom, fosse og fuktutforminger. Gjelder i alle hovedtyper |
| Ny fastmark på tidligere våtmark (T36): blå symboler | TM02, TM04 og TM05 får blå symboler |
| Skog i våtmark (V2, V8): grønn skravur, helst fylte grønne sirkler | VB01, VF01, VF02 og VI01 får grønne fylte sirkler |
| Treplantasje: grønne symboler | TM06 får grønne symboler |
| Semi-naturlig myr og våteng (V9, V10): skravur i semi-naturlig gul i stedet for omrissfarge | VK01 og VK02 får gul skravur |
| Torvtak og grøftet torvmark (V11, V12): blå skravur som viser myr | VM01–VM03 får blå skravur |
| Skravur i V6 bør ha grunnfargen til T7 Snøleie, slik at økologien kobles | VC04 får skravur i fargen til TC08 |
| Skravur i V7 bør ha fargen til T19 Oppfrysingsmark | VC05 og VE01 får skravur i fargen til TE05 |
| Vanskelig å skille typer på vinkel og tetthet i skravur; slitsomt å lese kart med mye skravur | Få og klart ulike vinkler. Tetthet brukes aldri alene. Symboler foretrekkes framfor skravur der det er mulig |
| Flere symboltyper er ofte vanskelige å lese | Få symboltyper, og hver har én betydning |
| Skravurlinjer var knapt synlige (L4) | Krav til kontrast mellom skravur og fyllfarge, kontrollert automatisk |
| Uklart hvilke virkemidler som hører til hovedtype og hvilke til kartleggingsenhet | Fyllfarge viser hovedtype. Skravur og symboler viser kartleggingsenhet |
| Hovedtyper betinget av spesielle miljøvariabler er sjeldne; mindre viktig at de skilles veldig klart | Enkleste symboler går til de vanligste typene |
| Definer symbolstørrelse (diameter?) og forskjellen på forskyvning og offset | Hver kolonne i symboltabellen får entydig definisjon og enhet |
| Hvordan fungerer kartografien i digitale kart? | Størrelser oppgis i millimeter og kontrolleres i QGIS på skjerm i steg 3 |
| Prinsippene fra «myrkosten» (vegetasjonskart, 1980) har stor tro | Vurderes for våtmark. Kilden er ikke blant referansefilene |

### Ikke overførbare

| Kommentar | Årsak |
| --- | --- |
| T8 og T7 kan bytte grunnfarge | Løst ved at snøleie er nesten hvit |
| T28 Polarørken bør være lys brun | Hovedtypen har ingen kartleggingsenheter i NiN 3.0-katalogen |
| Presiseringer i innledningen til Word-dokumentet | Gjelder det gamle dokumentet |

## Filer

| Fil | Innhold |
| --- | --- |
| `nin_qgis_plugin/csv/symbology/hovedtypegruppe_colours.csv` | Grunnfarge per hovedtypegruppe |
| `nin_qgis_plugin/csv/symbology/hovedtype_colours.csv` | Fasit: én farge per hovedtype. Redigeres for hånd |
| `nin_qgis_plugin/csv/symbology/reserved_colours.csv` | Ledige farger holdt av til nye hovedtyper |
| `nin_qgis_plugin/csv/symbology/colour_families.csv` | Fargefamilier med begrunnelse |
| `symbology_tools/colour.py` | Fargeregning: OKLab, fargeforskjell og simulert fargesyn |
| `symbology_tools/palette.py` | Leser og kontrollerer fargene |
| `symbology_tools/render_palette_overview.py` | Lager `fargeoversikt.html` |
| `tests/unit/test_symbology_palette.py` | Enhetstester |
| `symbology/` | Tidligere kartografi for NiN 2, til inspirasjon |

## Endre en farge

1. Endre `fill_hex` i `hovedtype_colours.csv`.
2. Kontroller fargene: `python symbology_tools/palette.py`
3. Lag oversikten på nytt: `python symbology_tools/render_palette_overview.py`
4. Kjør testene: `python -m pytest -q`

## Legge til en ny hovedtype

Når NiN-katalogen oppdateres og får en ny hovedtype med kartleggingsenheter,
melder kontrollen at den mangler farge.

1. Velg fargefamilie og flytt en ledig farge fra `reserved_colours.csv` til
   en ny rad i `hovedtype_colours.csv`.
2. Legg en ny ledig farge i `reserved_colours.csv` for familien.
3. Kontroller, lag oversikten og kjør testene som over.

Eksisterende farger endres ikke.
