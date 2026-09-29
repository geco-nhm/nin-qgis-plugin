# SYMBOLOGY_3.0 — plan

Branch: `symbology`. Status: **iteration 1 committed (draft 2), iteration 2 in progress**. Last updated 2026-09-29.

Iteration 1 output: `nin_qgis_plugin/csv/symbology/hovedtype_colours.csv`,
`docs/symbology/fargeoversikt.html`, documentation in `docs/symbology/README.md`.

Goal: a documented, reproducible cartography for NiN 3.0 *kartleggingsenheter*
at 1:5 000 (M005), 1:20 000 (M020) and 1:50 000 (M050). Grunntyper are out of
scope.

## 1. What was ingested

| Source | What it gives us |
| --- | --- |
| NiN 2 cartography specification (Word) | Full NiN 2.x 1:5000 specification: fill, outline and hatch per unit (RGB, line width, rotation, spacing). 344 classes. |
| `Ulik_nin-kartografi.docx` | The design reasoning: alternative 1 (hatch) vs alternative 2 (signature glyphs), the reused "rød tråd" colours and symbols, and the QGIS legend problem with font markers. |
| `NiN5000_VEGA_nin_v050823.qml`, `NN20000_LYGRA_nin_v160821.qml` | Working QGIS implementations (rule-based renderer; SimpleFill + LinePatternFill / PointPatternFill / FontMarker). Template for our QML export. |
| `nin_s1..s6.jpg`, `eks_skravur_og_signatur_qgis.png` | Hand-annotated signature proposal and a test rendering. |

Principles worth keeping from the old system:

- One fill colour per hovedtype, chosen by association (forest green, water
  blue, rock grey, soil brown, mire purple).
- Hatch **angle** encodes kalkinnhold: kalkfattig `/`, intermediær `—`, kalkrik `|`.
- Hatch **colour** encodes drought exposure: blue (moist), grey, yellow (dry).
- Dotted outline for kildepåvirkning (blue) and gjødsling (brown).
- Symbol **density** encodes degree; dashed vs solid separates paired concepts.
- Reused glyphs: `^` skred, `~` flom, `:` littoral, `o` sterkt endret, `=` bunn.

Known weaknesses of the old system that we should fix:

- Hovedtype fills were taken from unrelated ColorBrewer ramps, so T8–T14 are
  pink/red and T15–T17 brown for no ecological reason.
- Too much hatch gives a restless map (the author's own conclusion).
- Hand-made: no rule says why a unit got its symbol, so it cannot be
  regenerated when the type system changes.
- The legend cannot show font-marker signatures.

## 2. What NiN 3.0 looks like (from the plugin catalogue)

Mapping units exist only for *Natursystem* (C-PE-NA): 138 hovedtyper in 7
hovedtypegrupper.

| Gruppe | Hovedtyper | M005 | M020 | M050 | Max units in one hovedtype (M005) |
| --- | --- | --- | --- | --- | --- |
| NA-T Fastmark | 50 | 312 | 165 | 92 | 41 (TG01 Nakne løsmasser) |
| NA-V Våtmark | 22 | 76 | 47 | 24 | 19 (VA01 Åpen jordvannsmyr) |
| NA-L Innsjøbunn | 18 | 78 | 58 | 42 | 15 |
| NA-O Elvebunn | 9 | 51 | 36 | 29 | 18 |
| NA-M Marin bunn | 23 | 146 | 93 | 51 | 31 |
| NA-F Limniske vannmasser | 15 | 92 | 92 | 92 | 18 |
| NA-I Snø og is | 1 | 4 | 2 | 2 | 4 |
| **Sum** | **138** | **759** | **493** | **332** | |

Two facts make a rule-based system possible:

1. **The scales nest.** Via the grunntyper table every M005 unit maps to one
   M020 unit and every M020 unit to one M050 unit. Exceptions: 4 M005 units
   straddle two M020 units (LA02-M005-13, MC02-M005-08, VB01-M005-04,
   VK02-M005-01); M020 → M050 has none.
2. **Units are described by variables.** `var_M005/M020/M050` list the
   gradient steps (LM-KA kalkinnhold, LM-UF uttørkingsfare, LM-KI
   kildevannspåvirkning, ... 54 variables) that define each unit. 22 M005
   units have no variable rows and need a fallback.

## 3. Design

Three independent visual channels, so each answers one question.

| Channel | Encodes | Constant across scales? |
| --- | --- | --- |
| Fill colour | Hovedtype (hue family = ecosystem) | Yes |
| Overlay pattern (hatch, dots, glyphs) and outline | Kartleggingsenhet within the hovedtype | Refined with scale |
| Label | Short code, e.g. `TB01-05` | Code changes with scale |

### 3.1 Fill colour: hue family per ecosystem

Hovedtyper are grouped into colour families; within a family they differ in
lightness and slightly in hue. Fills stay light to medium so that overlay
patterns and the background map remain readable.

| Family | Hovedtyper (examples) | Colour | Convention |
| --- | --- | --- | --- |
| Forest | TB01, TF01, TF02, TI01, TM06 | Greens | N50, AR5, old NiN |
| Semi-natural | TK01, TK02, TL01, TD05, TE08 | Yellows | Old NiN T31–T34 |
| Heath | TK03, TH01 | Ochre, orange | Old NiN T34 |
| Arable and intensive | TO01–TO04, TN01–TN03 | Orange to pale red | AR5 jordbruk |
| Alpine heath, grassland, snowbed | TA03, TA04, TC08, TD06 | Olive, grey-green | Vegetation maps |
| Bare rock, scree, boulder | TA01, TA02, TD01, TC01, TC02 | Greys, grey-beige | Old NiN "fjell: grå" |
| Bare sediment, shore, dunes | TG01, TC03, TE01, TE03 | Sand, beige | |
| Disturbance (slide, frost, flood) | TE02, TD02, TE05, TE09 | Browns | Old NiN "jord: brun" |
| Strongly modified | TM01–TM05 | Neutral greys, dark outline | Old NiN T35–T39 |
| Mire and wetland | VA01, VC01, VC02 ... | Purples | Old NiN "myr: lilla" |
| Wetland forest | VB01, VF01, VF02, VI01 | Green-purple blend | Forest and mire |
| Semi-natural wetland | VK01, VK02 | Yellow-purple blend | |
| Lake bottom | NA-L | Medium blues | |
| River bottom | NA-O | Teal blues | |
| Marine bottom | NA-M | Light to deep sea blues | Sea charts |
| Water bodies | NA-F | Pale blues | |
| Snow and ice | NA-I | Near-white cyan | N50 bre |

The palette is hand-curated in one file and machine-checked (minimum colour
distance between hovedtyper that can be neighbours, colour-blind simulation).

### 3.2 Overlay pattern: a grammar driven by the defining variables

Each defining variable is bound to one visual property, the same in every
hovedtype, so the map reader learns it once.

| Variable | Visual property | Values |
| --- | --- | --- |
| LM-KA Kalkinnhold | Hatch angle | fattig 45°, intermediær 0°, rik 90°; spacing for sub-steps |
| LM-UF, LM-UE Uttørking | Hatch colour | blue, grey, yellow |
| LM-KI Kildevannspåvirkning | Outline | blue dotted |
| LM-HI, LM-HG Hevd, gjødsling | Outline or dashed hatch | brown dotted; dashed = weaker |
| LM-SV Snødekke | Hatch colour | white, orange, dark red |
| LM-MF Myrflatepreg | Solid vs dashed | flate solid, kant dashed |
| Grain size, substrate | Dot pattern | size and density |
| Slide, flood, littoral | Glyph pattern | `^`, `~`, `:` |

Units that the grammar cannot separate (no variable rows, or two units with
the same result) get a pattern from an ordered fallback library. A validator
guarantees that every symbol is unique within its hovedtype.

Patterns use simple markers, not a custom font, so legends work in QGIS.

### 3.3 Aggregation between scales: symbol inheritance

Symbols are assigned top-down along the nesting tree.

| Scale | Rule | Result |
| --- | --- | --- |
| M050 | Fill + primary property only (usually hatch angle, or no pattern when the hovedtype has one unit) | Calm map, at most a few patterns per hovedtype |
| M020 | Inherits the M050 parent's symbol and adds one modifier (colour or spacing) | Children look like their parent |
| M005 | Inherits the M020 parent's symbol and adds one more modifier (dash, density, outline) | Full detail |

Example, Fastmarksskogsmark TB01: M050 `Kalkskog` = green with vertical
hatch. Its M020 child `Frisk kalkskog og kalk-bærlyngskog` = the same with
blue hatch (moist). Its M005 child `Frisk kalkskog` = the same, solid;
`Kalk-bærlyngskog` = the same, dashed.

Pattern sizes are in millimetres, so the pattern looks the same on paper at
every scale. The 4 units that straddle two parents inherit from the parent
holding most of their grunntyper; this is listed in the documentation.

### 3.4 Rules taken from the 2020 review comments

The NiN 2 draft was reviewed by experts in the NiN community. The full list, with what was done about each comment, is in
`docs/symbology/README.md`. The rules that change this plan:

- Clear green is reserved for forest. Forest against mountain must be obvious.
- The area-dominant hovedtyper (TA01-TA04, TB01, VA01, VB01) must stand out
  from every other fill.
- All polygons get a white outline. Outline colour carries no information,
  so section 3.2 no longer uses dotted outlines for kilde and hevd.
- Blue pattern means water influence (kilde, flom, fosse, moist variants),
  green filled circles mean trees in wetland, yellow pattern means
  semi-natural use. These hold across all hovedtyper.
- Patterns may borrow the fill colour of an ecologically linked hovedtype
  (våtsnøleie borrows from snøleie, permafrost wetland from oppfrysingsmark).
- Few, clearly different hatch angles. Density is never the only difference.
  Prefer symbols over hatch where possible.
- Spare colours are reserved per family so new hovedtyper never change
  existing colours.

## 4. Pipeline

Plain Python, no QGIS needed to generate or test. Everything regenerates
from the catalogue tables when the NiN API changes.

```text
nin_qgis_plugin/csv/attribute_tables/*.csv     (exists)
        |
symbology_tools/palette.toml                   hand-curated hovedtype colours
symbology_tools/pattern_rules.toml             variable -> visual property
        |
symbology_tools/build_symbology.py
        |
nin_qgis_plugin/csv/symbology/symbology_M005.csv, _M020.csv, _M050.csv
        |                       (one row per unit: fill, outline, pattern, parent)
        +--> validate_symbology.py   uniqueness, contrast, inheritance, coverage
        +--> render_overview.py      SVG/HTML legend sheets per scale
        +--> export_qml.py           symbology/qml/NiN3_M005.qml, _M020, _M050
        +--> plugin (project_setup)  builds QGIS symbols from the CSV
```

## 5. Iterations

| # | Deliverable | Review point |
| --- | --- | --- |
| 0 | Reference material committed; this plan | Plan approved |
| 1 | Hovedtype palette (138 colours) + colour overview | Colours accepted |
| 2 | Pattern grammar + symbols for all three scales + rendered overview + validator | Symbols accepted |
| 3 | QML export, tested in QGIS against the old QML | Works in QGIS |
| 4 | Plugin integration (replaces hash colours), unit tests, user guide chapter | Release |

## 6. Decisions (2026-09-29)

| Question | Decision |
| --- | --- |
| Scope | Land and wetland first: NA-T and NA-V (72 hovedtyper; 388 / 212 / 116 units). Water groups keep a plain fill until a later iteration. |
| Pattern style | Hybrid, rule-based: hatch, dots, simple glyphs and dotted outlines. No custom font. |
| Plugin use | The new symbology replaces the hash colours. Standalone QML files are also produced. |
| Language | Norwegian for documentation and overview. |
