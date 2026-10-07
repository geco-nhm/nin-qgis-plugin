# Kartografi for NiN 3.0

Denne mappa dokumenterer kartografien for kartleggingsenheter i NiN 3.0 i
målestokkene 1:5 000, 1:20 000 og 1:50 000. Arbeidet skjer i flere steg.
Planen og status står i [symbology/PLAN.md](../../symbology/PLAN.md).

| Steg | Innhold | Status |
| --- | --- | --- |
| 1 | Fyllfarge for hver hovedtype | Utkast 2, revidert etter kommentarene til NiN 2-utkastet |
| 2 | Skravur og symboler for kartleggingsenhetene, i tre målestokker | Utkast 2: egne nyanser for TG01, tre regler rettet etter prøving |
| 3 | Stilfiler for QGIS (QML) | Utkast 2, tegnet og kontrollert i QGIS 3.40 |
| 4 | Kartografien tas i bruk i programtillegget | Koden er på plass og testet. Fyll 65 % dekkende. Brukerveiledningen er ikke oppdatert |
| 5 | Prøving på kartlagte data | Tre områder kartlagt i 1:20 000, tegnet i 1:20 000 og vurdert |
| 6 | Forslag B: kalkfattig uten skravur | Laget og prøvd på de samme dataene, til vurdering |

Utskriftsklare oversikter (A4, med sidetall):

| Oversikt | Nettleser | PDF |
| --- | --- | --- |
| Farger for hovedtyper | [fargeoversikt.html](fargeoversikt.html) | [fargeoversikt.pdf](fargeoversikt.pdf) |
| Symboler, utkast A (brukes i programtillegget) | [symboloversikt.html](symboloversikt.html) | [symboloversikt.pdf](symboloversikt.pdf) |
| Symboler, forslag B | [symboloversikt_forslag_B.html](symboloversikt_forslag_B.html) | [symboloversikt_forslag_B.pdf](symboloversikt_forslag_B.pdf) |
| Prøvekart 1:20 000, utkast A | [testkart_M020.png](testkart_M020.png) | [testkart_M020.pdf](testkart_M020.pdf) |
| Prøvekart 1:20 000, forslag B | [testkart_M020_forslag_B.png](testkart_M020_forslag_B.png) | [testkart_M020_forslag_B.pdf](testkart_M020_forslag_B.pdf) |

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
| Løsmasser og strand | Sand og gråbeige | TG01, TC03, TC04, TE01, TE03, TE04, TE06, TE07. TG01 har i tillegg sju nyanser, én per løsmassetype (se steg 2) |
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
| Minste fargeforskjell fra en arealmessig dominerende hovedtype til alle andre farger, også nyansene til TG01 | 0,045 | 0,047 |
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

Oversikten ligger i [symboloversikt.html](symboloversikt.html)
([pdf](symboloversikt.pdf)). Den viser alle enhetene i de tre målestokkene
side om side, med en forklaring til hvert symbol.

Symbolene er ikke tegnet for hånd. De er beregnet fra miljøvariablene som
definerer hver kartleggingsenhet i NiN-katalogen, med reglene i
`variable_rules.csv`, `hovedtype_patterns.csv` og `subtype_colours.csv`.

| Målestokk | Enheter | Bare fyllfarge | Med skravur | Skilt med prikket skravur eller nøytralt symbol |
| --- | --- | --- | --- | --- |
| 1:5 000 | 388 | 27 | 290 | 31 |
| 1:20 000 | 212 | 29 | 144 | 10 |
| 1:50 000 | 116 | 35 | 49 | 3 |

### Reglene

| Virkemiddel | Viser | Verdier |
| --- | --- | --- |
| Skravurvinkel | Kalkinnhold (LM-KA) | Skrå = kalkfattig, vannrett = intermediær, loddrett = kalkrik. En enhet som spenner over nesten hele skalaen, har ingen vinkel for kalk |
| Skravurfarge | Uttørkingsfare, uttørkingseksponering og tørrleggingsvarighet | Blå bare når hele spennet ligger i den fuktigste fjerdedelen. Ellers grå, oransje eller mørk rød etter midten av spennet. Et spenn over mer enn to tredeler av skalaen gir grå |
| Skravurtype | Myrflatepreg | Stiplet = hele spennet ligger i myrkant-halvdelen. Heltrukken = myrflate, eller både kant og flate |
| Prikket skravur | Ingen egen betydning | Skiller to enheter som ellers ville fått likt symbol |
| Nyanse av fyllfargen | Løsmassetype i TG01 Nakne løsmasser | Sju nyanser av sandfargen |
| Blå symboler | Vannpåvirkning: kilde, fuktig mark, vannsprut, overrisling, bølger og strøm | Sirkel, strek, kryss og rute |
| Hvit sirkel | Snøleiepreg | |
| Mørke firkanter | Kornstørrelse og substrat | Større firkant = grovere |
| Mørk ring | Type inngrep i sterkt endret mark | |
| Gulbrune symboler | Hevd og gjødsling | Rute og trekant |
| Sirkel i farge fra en annen hovedtype | Hva marka ligner (økologisk differensiering) | Rabbe, fjellhei, snøleie (hvit), skog (grønn) |
| Grønn sirkel | Skog i våtmark, og skogpreg i annen mark | |

Tre regler gjelder alle symboler:

1. En variabel tegnes bare når den skiller enheter i samme hovedtype i den
   aktuelle målestokken.
2. En enhet som omfatter variabelens laveste trinn, får ikke symbol for den.
   Symbolet betyr at egenskapen gjelder hele enheten. Enheter som ligger
   helt over det laveste trinnet, får symbol, og større symbol jo høyere
   trinn. Tetthet brukes ikke til å vise grad.
3. Et symbol har skravur og høyst tre typer symboler.

Noen hovedtyper har et fast kjennetegn på alle enhetene, for eksempel grønn
sirkel for skog i våtmark og blå skravur for flommark. De står i
`hovedtype_patterns.csv`.

### TG01 Nakne løsmasser: nyanse per løsmassetype

TG01 har 41 enheter i 1:5 000. De er kombinasjoner av løsmassetype (sju
verdier), kornstørrelse, hva marka ligner og kalkinnhold. I utkast 1 ble
løsmassetypen vist med en trekant i sju varianter, og de fleste enhetene
fikk tre eller fire mønsterlag oppå fyllfargen.

Nå får hver løsmassetype sin egen nyanse av sandfargen, slik
hovedtypene har hver sin farge. Enhetene i 1:50 000 er delt etter
løsmassetype, så der skiller fyllfargen dem alene.

| Løsmassetype | Farge | Begrunnelse |
| --- | --- | --- |
| A Stedegne løsmasser | `#E3B394` | Grunnfargen til TG01 |
| B Morene | `#B7A494` | Gråere og mørkere sand |
| C Hevet strand | `#E8CFAD` | Lys, gul sand som strand |
| D Breforland og snøavsmeltingsområde | `#CDACA5` | Kjølig, gråbeige |
| E Konsoliderte marine bresedimenter | `#CA97A0` | Rosagrå leirfarge |
| F Historisk skred | `#AE6D57` | Brun, beslektet med skred- og rasmark |
| G Flomskredmateriale | `#BC9171` | Brun, beslektet med flomskredmark |

Nyansene er kontrollert sammen med alle andre fyllfarger og følger de samme
kravene (minst 0,034 fra alle andre, minst 0,045 fra de arealmessig
dominerende). Resultat i 1:5 000:

| Mønsterlag oppå fyllfargen | 0 | 1 | 2 | 3 | 4 |
| --- | --- | --- | --- | --- | --- |
| Før (trekant for løsmassetype) | 1 | 5 | 16 | 18 | 1 |
| Nå (nyanse for løsmassetype) | 5 | 13 | 15 | 8 | 0 |

Regelen er generell: `subtype_colours.csv` kan gi nyanser til andre
hovedtyper der én variabel deler enhetene i tydelige grupper.

### Aggregering mellom målestokkene

De samme reglene brukes i alle tre målestokker. En enhet i grov målestokk
dekker et videre spenn av hver variabel, og færre variabler skiller enhetene
fra hverandre. Symbolene får derfor færre deler jo grovere målestokken er.

| Målestokk | Mønsterlag oppå fyllfargen, gjennomsnitt | Eksempel: Fastmarksskogsmark TB01 |
| --- | --- | --- |
| 1:50 000 | 0,9 | Kalkfattig til intermediær skog: vannrett skravur. Kalkskog: loddrett skravur |
| 1:20 000 | 1,3 | Blåbær-bærlyngskog: skrå skravur. Lyng- og lavskog: skrå skravur i mørk rød (tørkeutsatt) |
| 1:5 000 | 1,6 | Blåbærfuktskog: skrå blå skravur (frisk) og blå sirkel (fuktig mark) |

Hver enhet er koblet til enheten den hører til i neste grovere målestokk
(kolonnen `parent_kode_id`). Koblingen går gjennom grunntypene i katalogen.

Skravurvinkelen settes ut fra midten av enhetens spenn i kalkinnhold. Av
enhetene i 1:5 000 har 369 av 386 samme skravurvinkel som enheten de hører
til i 1:20 000. Fra 1:20 000 til 1:50 000 gjelder det 132 av 212, fordi
enhetene i 1:50 000 ofte spenner over både kalkfattig og intermediær.

### Nøytrale skillesymboler

Reglene gir to enheter samme symbol når de har samme klasse i alle
variabler som tegnes. Da får den ene prikket skravur, eller et nøytralt
mørkt symbol (vinkel, stjerne, plusstegn). Det skiller enhetene fra
hverandre, men sier ikke hva forskjellen er. Stiplet skravur brukes ikke
her, fordi den betyr myrkant.

Hver kartleggingsenhet har dermed sitt eget symbol: antall ulike symboler er
lik antall enheter i hver målestokk (388, 212 og 116). Det kontrolleres
automatisk. Det er fyllfargen som er felles for alle enheter i en hovedtype,
med vilje.

Nøytralt skillesymbol trengs av to grunner:

| Grunn | Eksempel |
| --- | --- |
| Katalogen har ingen variabel som skiller enhetene | TI01 Klart endret skogsmark: «hugd» mot «treslagstypeskiftet» er ikke en miljøvariabel. TM06 Sterkt endret skogsmark: enhetene er suksesjonsstadier |
| To spenn havner i samme klasse | TA01 Nakent berg: uttørkingseksponering har seks trinn i 1:5 000, men skravurfargen har fire klasser |

Enheter med nøytralt skillesymbol i 1:5 000: TA01 (9), VA01 (6), TI01 (4),
TA03, TG01, TM03 og TM06 (2 hver), TD06, TO04, VB01 og VC05 (1 hver).

### Kolonnene i symboltabellene

`symbology_M005.csv`, `symbology_M020.csv` og `symbology_M050.csv` har én rad
per kartleggingsenhet. Alle mål er i millimeter på papir eller skjerm og er
uavhengige av kartets målestokk.

| Kolonne | Innhold |
| --- | --- |
| `kode_id`, `navn` | Kartleggingsenheten |
| `hovedtype` | Hovedtypen enheten hører til |
| `parent_kode_id` | Enheten den hører til i neste grovere målestokk. Tom i 1:50 000 |
| `fill_hex`, `outline_hex` | Fyllfarge og omrissfarge. For TG01 er fyllfargen nyansen til løsmassetypen |
| `hatch_angle` | Skravurvinkel i grader mot klokka fra vannrett. Tom betyr ingen skravur |
| `hatch_colour`, `hatch_style` | Skravurfarge og linjetype: `solid`, `dashed` (myrkant; 2,4 mm strek, 1,2 mm mellomrom) eller `dotted` (skillesymbol; 0,5 og 1,1 mm) |
| `hatch_spacing_mm`, `hatch_width_mm` | Avstand mellom skravurlinjene (4 mm), målt vinkelrett på linjene, og linjetykkelse (0,25 mm) |
| `marker1_shape` til `marker3_shape` | Symbolform: `circle`, `ring`, `square`, `triangle`, `diamond`, `star`, `cross`, `cross2`, `line` eller `arrowhead` |
| `marker1_colour` til `marker3_colour` | Symbolfarge. Hvite symboler har mørk kantlinje |
| `marker1_size_mm` til `marker3_size_mm` | Største utstrekning av symbolet; diameter for sirkel og ring |
| `marker1_filled` til `marker3_filled` | 1 = fylt, 0 = bare omriss |
| `marker_spacing_mm` | Avstand mellom symbolene, vannrett og loddrett. Hver symboltype er forskjøvet i ruta slik at de ikke dekker hverandre |
| `forklaring` | Hva hver del av symbolet viser |

### Kjente svakheter i utkast 2

| Svakhet | Omfang |
| --- | --- |
| Symboler med fire mønsterlag oppå fyllfargen er tunge å lese | 8 enheter i 1:5 000: TK01 Semi-naturlig eng (6) og TF02 Flomskogsmark (2) |
| To enheter i 1:5 000 er ikke koblet til noen enhet i 1:20 000 i katalogen | TA01-M005-23 Fuglestein og fugleberg, TC02-M005-04 Kalkfattig til litt kalkrik grotte |
| Symbolene er tegnet i QGIS og prøvd på kartlagte data, men ikke på trykk eller i felt | Alle enheter |

## Steg 3: stilfiler for QGIS

| Fil | Innhold |
| --- | --- |
| `symbology/qml/NiN3_M005.qml` | Stil for 1:5 000, 759 enheter |
| `symbology/qml/NiN3_M020.qml` | Stil for 1:20 000, 493 enheter |
| `symbology/qml/NiN3_M050.qml` | Stil for 1:50 000, 332 enheter |

Stilfilene gjelder flatelag der koden til kartleggingsenheten står i feltet
`kode_id`, for eksempel `TB01-M005-03`. I QGIS lastes en stil inn fra
lagegenskapene: Symbologi, Stil, Last inn stil. Fyllfargen er helt dekkende i
stilfilene; programtillegget gjør den 65 % dekkende.

Enheter i limniske og marine systemer og i snø og is har bare grunnfargen
til hovedtypegruppa.

Prøvekart tegnet av QGIS 3.40 i 1:1000, ett rektangel på 34 × 22 mm per
enhet i fastmark og våtmark:

- [qgis_M050.png](qgis_M050.png)
- [qgis_M020.png](qgis_M020.png)
- [qgis_M005.png](qgis_M005.png)

Stilfilene og prøvekartene lages med
`python-qgis-ltr.bat symbology_tools/export_qml.py`.

## Steg 4: programtillegget

Programtillegget leser symboltabellene og bygger symbolene når et prosjekt
opprettes. De erstatter fargene som tidligere ble beregnet fra koden.

| Lag | Symbol |
| --- | --- |
| Flater | Fyllfarge som er 65 % dekkende (35 % gjennomsiktig), slik at bakgrunnskartet synes. Skravur og symboler er helt dekkende |
| Punkter | Sirkel i fyllfargen |
| Linjer | Linje i fyllfargen |

En type som ikke har eget symbol, får den første fargen som finnes av disse:
fargen til hovedtypen, grunnfargen til hovedtypegruppa, og til slutt en farge
beregnet fra koden. Det gjelder blant annet grunntyper.

Eksisterende prosjekter endres ikke. Stilen lagres i prosjektets GeoPackage
når prosjektet opprettes.

## Steg 5: prøving på kartlagte data

Tre kartlagte områder fra samme prosjekt (500 × 1000 m hver, 337 figurer,
25 kartleggingsenheter) er tegnet sammen i ett kart med programtilleggets
egne symboler, 65 % dekkende fyll, over Kartverkets gråtonekart.

**Målestokk.** Områdene er kartlagt i 1:20 000. Det framgår av dataene:
`kode_id_label` peker på rader i katalogtabellen, og bare i tabellen for
1:20 000 hører enheten til den hovedtypen som også er lagret på figuren (263
av 267 kartlagte figurer; 0 i 1:5 000 og 1:50 000. De fire andre viser til
en enhet som ikke lenger finnes i katalogen). Enhetskodene har derfor
formen `TH01-M020-01`. Kartet er tegnet i 1:20 000, og påskriftene viser
koden uten målestokk (`TH01-01`), slik programtillegget gjør.

- [testkart_M020.png](testkart_M020.png) ([pdf](testkart_M020.pdf))

Kartet lages med `python-qgis-ltr.bat symbology_tools/render_test_areas.py`
fra GeoPackage-filene i `symbology/`. Skriptet finner målestokken fra dataene.
GeoPackage-filene er ikke sjekket inn i Git.

### Tre feil som ble funnet og rettet

Den første tegningen av dataene viste tre feil i reglene. Alle er rettet i
symboltabellene, i stilfilene, i oversiktene og i reglene over.

| Funn i kartet | Årsak | Retting |
| --- | --- | --- |
| Blåbær-bærlyngskog (TB01-01), den vanligste skogenheten, hadde blå sirkler for fuktig mark | Enhetens spenn i vannmetning (0–c) omfattet de fuktige trinnene, og rangeringen ga alle verdier over det laveste et symbol | En enhet som omfatter variabelens laveste trinn, får ikke symbol. Symbolet betyr at egenskapen gjelder hele enheten |
| Kalkfattig avskoget bærlynghei (TH01-01) hadde blå skravur | Midten av spennet b–c lå i den nederste fjerdedelen | Blå skravur bare når hele spennet ligger i den fuktigste fjerdedelen. Et spenn over mer enn to tredeler av skalaen gir grå skravur |
| Jordvannsmyr (VA01-01) fikk stiplet skravur for myrkant, selv om enheten dekker både kant og flate | Myrflatepreg hadde ingen regel og ble tegnet med et nøytralt symbol | Ny regel: stiplet skravur bare når hele spennet ligger i myrkant-halvdelen, ellers heltrukken |

I tillegg ble skravuren gjort roligere (4 mm avstand og 0,25 mm strek i
stedet for 3 mm og 0,3 mm), fyllfargen gjort mer dekkende (65 % i stedet for
50 %), og stiplet skravur er nå forbeholdt myrkant.

### Vurdering i 1:20 000

Nabofigurer med ulik enhet (490 par) skilles slik:

| Hva skiller symbolene | Par |
| --- | --- |
| Fyllfarge, ofte sammen med skravur eller symbol | 417 |
| Bare skravurvinkel (samme hovedtype, ulikt kalkinnhold) | 60 |
| Bare skravurfarge (samme hovedtype, ulik uttørkingsfare) | 9 |
| Bare symbol (TM03-01 mot TM03-02) | 4 |

Alle par av nabofigurer med ulik enhet har ulike symboler.

Det som fungerer:

- Hovedtypene leses av fargen: skog grønn, avskoget hei oker, fjellhei
  lysebrun, myr lilla, sterkt endret grå. Skillet skog–fjell er tydelig.
- Med 65 % dekkende fyll kan fjellhei (TA03, lysebrun) og avskoget hei
  (TH01, oker) skilles på fargen i prøvekartet, og bakgrunnskartet synes
  fortsatt.
- De vanligste parene innen samme hovedtype (TH01-01 mot TH01-02, TB01-01
  mot TB01-02) skilles av skravurvinkel.

Det som ikke fungerer godt nok i 1:20 000:

| Svakhet | Omfang | Mulig tiltak |
| --- | --- | --- |
| Mønsteret får ikke plass i smale figurer. Et mønster trenger to ruter à 4 mm, det vil si 160 m i terrenget | 223 av 263 figurer med symbol er smalere enn 160 m | Påskriften bærer koden. Større avstand og større symboler i 1:20 000 og 1:50 000 vil vise mønsteret i flere figurer, men gjør det grovere |
| Skrå skravur dekker nesten hele kartet, fordi kalkfattig mark er vanligst | 95 % av det kartlagte arealet har skravur | Se forslag B |
| Påskriftene overlapper | Mange små figurer | Påskrift bare på figurer over en minstestørrelse, eller bare når figuren velges |
| Fire figurer viser til en enhet (fid 493) som ikke finnes i katalogen | Katalogen er regenerert etter kartleggingen | Ikke et kartografispørsmål; de vises røde |

## Forslag B: kalkfattig uten skravur

Forslaget er laget og prøvd, men ikke tatt i bruk i programtillegget.

- Symboloversikt: [symboloversikt_forslag_B.html](symboloversikt_forslag_B.html)
  ([pdf](symboloversikt_forslag_B.pdf))
- Prøvekart 1:20 000: [testkart_M020_forslag_B.png](testkart_M020_forslag_B.png)
  ([pdf](testkart_M020_forslag_B.pdf))
- Symboltabeller: `symbology/forslag_B/symbology_M005.csv` osv.

### Regler

| Virkemiddel | Utkast A | Forslag B |
| --- | --- | --- |
| Kalkfattig | Skrå skravur | Ingen skravur (grunntilstand) |
| Intermediær og kalkrik | Vannrett og loddrett skravur | Uendret |
| Uttørkingsfare, uttørkingseksponering, tørrleggingsvarighet | Skravurfarge: blå, grå, oransje, mørk rød | Liten sirkel i samme farger. Den grå klassen (den vanligste) er grunntilstand uten sirkel |
| Myrkant uten kalkskravur | Stiplet skravur | Stiplet skravur mot venstre. Myrflate uten kalkskravur får ingen skravur |

Uttørking får en egen bærer overalt, ikke bare der kalkinnholdet ikke
varierer. Da betyr hvert virkemiddel én ting i hele kartet: skravur er kalk,
sirkelens farge er vannbalanse (blå = fuktig eller frisk, hvit = snø,
oransje og mørk rød = tørt). Om uttørking skulle vises med skravurfarge der
det er skravur og med sirkel der det ikke er det, måtte kartleseren lære to
tegn for samme egenskap.

### Sammenligning

| | Utkast A | Forslag B |
| --- | --- | --- |
| Kartlagt areal med skravur, prøvekartet | 95 % | 13 % |
| Kartlagt areal med skravur eller symbol | 99 % | 28 % |
| Figurer med mønster som er for smale for mønsteret | 223 | 136 |
| Nabopar med ulik enhet og likt symbol | 0 | 0 |
| Nabopar innen samme hovedtype som skilles | 73 av 73 | 73 av 73 |
| Enheter med bare fyllfarge, 1:5 000 / 1:20 000 / 1:50 000 | 27 / 29 / 35 | 36 / 39 / 36 |
| Enheter med nøytralt skillesymbol, 1:5 000 | 31 | 37 |
| Enheter med fire mønsterlag, 1:5 000 | 8 | 11 |

Vurdering:

- Kartet blir mye roligere. Den vanligste marka (kalkfattig, noe
  tørkeutsatt) får bare fyllfarge, og skravur betyr nå at marka er
  kalkrikere enn vanlig. Det gjør kalkrik mark lett å finne.
- Kalkfattig og «kalkinnhold skiller ikke enhetene» ser like ut. Forskjellen
  går fram av påskriften og tegnforklaringen.
- Fuktig mark (blå sirkel for vannmetning) og frisk mark (blå sirkel for
  uttørkingsfare) får samme tegn. Det er økologisk rimelig, men i noen
  hovedtyper blir to enheter like og må skilles med nøytralt symbol. Derfor
  trengs 37 i stedet for 31 slike i 1:5 000, blant annet for Blåbærfuktskog
  mot Blåbærskog (TB01).
- Forslaget løser ikke problemet med smale figurer, men halverer omtrent
  antallet figurer der mønsteret ikke får plass, fordi færre figurer har
  mønster.

Anbefaling: forslag B gir et klart bedre kartbilde i 1:20 000. Før det tas i
bruk bør fuktig og frisk mark få to ulike tegn, slik at de seks ekstra
skillesymbolene forsvinner.

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
| Stilfiler i QML kan bare brukes i QGIS | Symbolene lagres i åpne CSV-tabeller med definerte kolonner. QML lages fra tabellene |

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
| Hvordan fungerer kartografien i digitale kart? | Størrelser er i millimeter og uavhengige av kartets målestokk. Tegnet i QGIS i steg 3 |
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
| `nin_qgis_plugin/csv/symbology/subtype_colours.csv` | Nyanser av fyllfargen per verdi av én variabel (TG01 per løsmassetype) |
| `symbology/forslag_B/` | Symboltabeller for forslag B. Brukes ikke av programtillegget |
| `nin_qgis_plugin/csv/symbology/symbology_M005.csv`, `_M020.csv`, `_M050.csv` | Resultat: ett symbol per kartleggingsenhet. Lages av `patterns.py`, redigeres ikke for hånd |
| `symbology_tools/patterns.py` | Beregner og kontrollerer symbolene |
| `symbology_tools/render_symbol_overview.py` | Lager `symboloversikt.html`, og `symboloversikt_forslag_B.html` med `--variant B` |
| `symbology_tools/print_overviews.py` | Skriver oversiktene ut til PDF med Edge eller Chrome |
| `tests/unit/test_symbology_patterns.py` | Enhetstester |
| `nin_qgis_plugin/symbology_styles.py` | Programtillegget: leser symboltabellene |
| `nin_qgis_plugin/symbology_symbols.py` | Programtillegget: bygger QGIS-symboler |
| `symbology_tools/export_qml.py` | Lager stilfiler og prøvekart. Krever QGIS |
| `symbology_tools/render_test_areas.py` | Tegner og vurderer kartlagte data fra `symbology/*.gpkg` i kartleggingsmålestokken. `--variant B` for forslag B. Krever QGIS |
| `tests/unit/test_symbology_styles.py`, `tests/qgis/test_symbology_symbols.py` | Tester for programtillegget |
| `tests/unit/test_symbology_palette.py` | Enhetstester |
| `symbology/` | Tidligere kartografi for NiN 2, til inspirasjon |

## Endre en farge

1. Endre `fill_hex` i `hovedtype_colours.csv`.
2. Kontroller fargene: `python symbology_tools/palette.py`
3. Lag oversikten på nytt: `python symbology_tools/render_palette_overview.py`
4. Lag PDF-ene på nytt: `python symbology_tools/print_overviews.py`
5. Kjør testene: `python -m pytest -q`

## Endre en regel for skravur eller symboler

1. Endre `variable_rules.csv`, `hovedtype_patterns.csv` eller `subtype_colours.csv`.
2. Beregn symbolene på nytt: `python symbology_tools/patterns.py`, og
   `python symbology_tools/patterns.py --variant B` for forslaget
3. Lag oversiktene på nytt: `python symbology_tools/render_symbol_overview.py`
   (med og uten `--variant B`), deretter `python symbology_tools/print_overviews.py`
4. Lag stilfilene på nytt: `python-qgis-ltr.bat symbology_tools/export_qml.py`
5. Lag prøvekartene på nytt: `python-qgis-ltr.bat symbology_tools/render_test_areas.py`
   (med og uten `--variant B`)
6. Kjør testene: `python -m pytest -q`

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
