# Kartografi for NiN 3.0

Denne mappa dokumenterer kartografien for kartleggingsenheter i NiN 3.0 i
målestokkene 1:5 000, 1:20 000 og 1:50 000. Arbeidet skjer i flere steg.
Planen og status står i [symbology/PLAN.md](../../symbology/PLAN.md).

| Steg | Innhold | Status |
| --- | --- | --- |
| 1 | Fyllfarge for hver hovedtype | Utkast 2, revidert etter kommentarene til NiN 2-utkastet |
| 2 | Skravur og symboler for kartleggingsenhetene, i tre målestokker | Utkast 1 til gjennomsyn |
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

## Steg 2: skravur og symboler

Oversikten ligger i [symboloversikt.html](symboloversikt.html). Den viser
alle enhetene i de tre målestokkene side om side, med en forklaring til hvert
symbol.

Symbolene er ikke tegnet for hånd. De er beregnet fra miljøvariablene som
definerer hver kartleggingsenhet i NiN-katalogen, med reglene i
`variable_rules.csv` og `hovedtype_patterns.csv`.

| Målestokk | Enheter | Bare fyllfarge | Med skravur | Skilt med stiplet skravur eller ekstra symbol |
| --- | --- | --- | --- | --- |
| 1:5 000 | 388 | 25 | 294 | 25 |
| 1:20 000 | 212 | 25 | 149 | 6 |
| 1:50 000 | 116 | 30 | 53 | 2 |

### Reglene

| Virkemiddel | Viser | Verdier |
| --- | --- | --- |
| Skravurvinkel | Kalkinnhold (LM-KA) | Skrå = kalkfattig, vannrett = intermediær, loddrett = kalkrik |
| Skravurfarge | Uttørkingsfare, uttørkingseksponering og tørrleggingsvarighet | Blå, grå, oransje, mørk rød: fra friskt til tørt |
| Blå symboler | Vannpåvirkning: kilde, fuktig mark, vannsprut, overrisling, bølger og strøm | Sirkel, strek, kryss og rute |
| Hvit sirkel | Snøleiepreg | |
| Mørke firkanter og trekanter | Kornstørrelse, substrat og løsmassetype | |
| Mørk ring | Type inngrep i sterkt endret mark | |
| Gulbrune symboler | Hevd og gjødsling | Rute og trekant |
| Grønn sirkel | Skog i våtmark, og skogpreg i annen mark | |

Tre regler gjelder alle symboler:

1. En variabel tegnes bare når den skiller enheter i samme hovedtype i den
   aktuelle målestokken.
2. Laveste trinn av en variabel har ikke symbol. Høyere trinn har større
   symbol. Tetthet brukes ikke til å vise grad.
3. Et symbol har skravur og høyst tre typer symboler.

Noen hovedtyper har et fast kjennetegn på alle enhetene, for eksempel grønn
sirkel for skog i våtmark og blå skravur for flommark. De står i
`hovedtype_patterns.csv`.

### Aggregering mellom målestokkene

De samme reglene brukes i alle tre målestokker. En enhet i grov målestokk
dekker et videre spenn av hver variabel, og færre variabler skiller enhetene
fra hverandre. Symbolene får derfor færre deler jo grovere målestokken er.

| Målestokk | Deler oppå fyllfargen, gjennomsnitt | Eksempel: Fastmarksskogsmark TB01 |
| --- | --- | --- |
| 1:50 000 | 1,1 | Skravurvinkel viser kalkinnhold |
| 1:20 000 | 1,6 | I tillegg skravurfarge for uttørkingsfare og blå sirkel for fuktig mark |
| 1:5 000 | 1,8 | Samme virkemidler, med flere trinn |

Hver enhet er koblet til enheten den hører til i neste grovere målestokk
(kolonnen `parent_kode_id`). Koblingen går gjennom grunntypene i katalogen.

Skravurvinkelen settes ut fra midten av enhetens spenn i kalkinnhold. En
enhet som dekker hele spennet, har ikke skravur. Av enhetene i 1:5 000 har
374 av 386 samme skravurvinkel som enheten de hører til i 1:20 000. Fra
1:20 000 til 1:50 000 gjelder det 131 av 212, fordi enhetene i 1:50 000 ofte
spenner over både kalkfattig og intermediær.

### Kolonnene i symboltabellene

`symbology_M005.csv`, `symbology_M020.csv` og `symbology_M050.csv` har én rad
per kartleggingsenhet. Alle mål er i millimeter på papir eller skjerm og er
uavhengige av kartets målestokk.

| Kolonne | Innhold |
| --- | --- |
| `kode_id`, `navn` | Kartleggingsenheten |
| `hovedtype` | Hovedtypen enheten hører til |
| `parent_kode_id` | Enheten den hører til i neste grovere målestokk. Tom i 1:50 000 |
| `fill_hex`, `outline_hex` | Fyllfarge og omrissfarge |
| `hatch_angle` | Skravurvinkel i grader mot klokka fra vannrett. Tom betyr ingen skravur |
| `hatch_colour`, `hatch_style` | Skravurfarge og linjetype: `solid`, `dashed` (2,4 mm strek, 1,2 mm mellomrom) eller `dotted` (0,5 og 1,1 mm) |
| `hatch_spacing_mm`, `hatch_width_mm` | Avstand mellom skravurlinjene, målt vinkelrett på linjene, og linjetykkelse |
| `marker1_shape` til `marker3_shape` | Symbolform: `circle`, `ring`, `square`, `triangle`, `diamond`, `star`, `cross`, `cross2`, `line` eller `arrowhead` |
| `marker1_colour` til `marker3_colour` | Symbolfarge. Hvite symboler har mørk kantlinje |
| `marker1_size_mm` til `marker3_size_mm` | Største utstrekning av symbolet; diameter for sirkel og ring |
| `marker1_filled` til `marker3_filled` | 1 = fylt, 0 = bare omriss |
| `marker_spacing_mm` | Avstand mellom symbolene, vannrett og loddrett. Hver symboltype er forskjøvet i ruta slik at de ikke dekker hverandre |
| `forklaring` | Hva hver del av symbolet viser |

### Kjente svakheter i utkast 1

| Svakhet | Omfang |
| --- | --- |
| Symboler med fire deler oppå fyllfargen er tunge å lese | 27 enheter i 1:5 000, 10 i 1:20 000 og 3 i 1:50 000. De fleste er i TG01 Nakne løsmasser |
| Enheter som reglene ikke skiller, får stiplet skravur eller et nøytralt symbol uten egen betydning | 25 enheter i 1:5 000. Gjelder særlig TI01 og TM06, der katalogen ikke har variabler som skiller enhetene |
| To enheter i 1:5 000 er ikke koblet til noen enhet i 1:20 000 i katalogen | TA01-M005-23 Fuglestein og fugleberg, TC02-M005-04 Kalkfattig til litt kalkrik grotte |
| Symbolene er bare kontrollert i oversikten, ikke i QGIS eller på trykk | Gjøres i steg 3 |

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

### Fulgt opp i steg 2 (skravur og symboler)

| Kommentar | Oppfølging |
| --- | --- |
| Alt som er knyttet til fuktighet og vann, bør vises med blått (T15, T18, T30, T31-C-13/14, T32-C-9/10) | Blå skravur eller blå symboler betyr vannpåvirkning: kilde, flom, fosse og fuktutforminger. Gjelder i alle hovedtyper. TD04, TE03, TE04, TE08 og TF02 har blå skravur |
| Ny fastmark på tidligere våtmark (T36): blå symboler | TM02, TM04 og TM05 får blå symboler |
| Skog i våtmark (V2, V8): grønn skravur, helst fylte grønne sirkler | VB01, VF01, VF02 og VI01 får grønne fylte sirkler |
| Treplantasje: grønne symboler | TM06 får grønne symboler |
| Semi-naturlig myr og våteng (V9, V10): skravur i semi-naturlig gul i stedet for omrissfarge | VK01 og VK02 får gul skravur |
| Torvtak og grøftet torvmark (V11, V12): blå skravur som viser myr | VM01–VM03 får blå skravur |
| Skravur i V6 bør ha grunnfargen til T7 Snøleie, slik at økologien kobles | VC04 får skravur i fargen til TC08 |
| Skravur i V7 bør ha fargen til T19 Oppfrysingsmark | VC05 og VE01 får skravur i fargen til TE05 |
| Vanskelig å skille typer på vinkel og tetthet i skravur; slitsomt å lese kart med mye skravur | Tre vinkler for kalkinnhold og én nøytral. Tetthet brukes ikke; grad vises med symbolstørrelse |
| Flere symboltyper er ofte vanskelige å lese | Ti symbolformer. Form og farge har samme betydning i alle hovedtyper |
| Skravurlinjer var knapt synlige (L4) | Skravur og symboler gjøres mørkere eller lysere til lyshetsforskjellen mot fyllfargen er minst 0,22. Kontrolleres automatisk |
| Uklart hvilke virkemidler som hører til hovedtype og hvilke til kartleggingsenhet | Fyllfarge viser hovedtype. Skravur og symboler viser kartleggingsenhet |
| Hovedtyper betinget av spesielle miljøvariabler er sjeldne; mindre viktig at de skilles veldig klart | Ikke fulgt opp ennå. Reglene er like for vanlige og sjeldne typer |
| Definer symbolstørrelse (diameter?) og forskjellen på forskyvning og offset | Se «Kolonnene i symboltabellene» |
| Hvordan fungerer kartografien i digitale kart? | Størrelser oppgis i millimeter og kontrolleres i QGIS på skjerm i steg 3 |
| Prinsippene fra «myrkosten» (vegetasjonskart, 1980) har stor tro | Ikke fulgt opp. Kilden er ikke blant referansefilene |

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
| `nin_qgis_plugin/csv/symbology/variable_rules.csv` | Regler: hvilken variabel som styrer hvilket virkemiddel. Rekkefølgen er prioritet |
| `nin_qgis_plugin/csv/symbology/hovedtype_patterns.csv` | Faste kjennetegn for enkelte hovedtyper |
| `nin_qgis_plugin/csv/symbology/symbology_M005.csv`, `_M020.csv`, `_M050.csv` | Resultat: ett symbol per kartleggingsenhet. Lages av `patterns.py`, redigeres ikke for hånd |
| `symbology_tools/patterns.py` | Beregner og kontrollerer symbolene |
| `symbology_tools/render_symbol_overview.py` | Lager `symboloversikt.html` |
| `tests/unit/test_symbology_patterns.py` | Enhetstester |
| `tests/unit/test_symbology_palette.py` | Enhetstester |
| `symbology/` | Tidligere kartografi for NiN 2, til inspirasjon |

## Endre en farge

1. Endre `fill_hex` i `hovedtype_colours.csv`.
2. Kontroller fargene: `python symbology_tools/palette.py`
3. Lag oversikten på nytt: `python symbology_tools/render_palette_overview.py`
4. Kjør testene: `python -m pytest -q`

## Endre en regel for skravur eller symboler

1. Endre `variable_rules.csv` eller `hovedtype_patterns.csv`.
2. Beregn symbolene på nytt: `python symbology_tools/patterns.py`
3. Lag oversikten på nytt: `python symbology_tools/render_symbol_overview.py`
4. Kjør testene: `python -m pytest -q`

De samme stegene kjøres når NiN-katalogen er oppdatert. En test feiler hvis
symboltabellene ikke stemmer med katalogen og reglene.

## Legge til en ny hovedtype

Når NiN-katalogen oppdateres og får en ny hovedtype med kartleggingsenheter,
melder kontrollen at den mangler farge.

1. Velg fargefamilie og flytt en ledig farge fra `reserved_colours.csv` til
   en ny rad i `hovedtype_colours.csv`.
2. Legg en ny ledig farge i `reserved_colours.csv` for familien.
3. Kontroller, lag oversikten og kjør testene som over.

Eksisterende farger endres ikke.
