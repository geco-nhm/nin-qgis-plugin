# SYMBOLOGY_3.0 — plan

Branch: `symbology`. Status: **variant B chosen and in the plugin (2026-10-07); awaiting review before field and print tests**. Last updated 2026-09-29.

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

Done in iteration 1. The families, the rules and the numbers are in
`docs/symbology/README.md`; the colours are in
`nin_qgis_plugin/csv/symbology/hovedtype_colours.csv`.

### 3.2 Overlay pattern: a grammar driven by the defining variables

Done in iteration 2 (draft 1). Each defining variable is bound to one visual
property, the same in every hovedtype: `variable_rules.csv`. Fixed marks per
hovedtype are in `hovedtype_patterns.csv`. Units that the rules cannot
separate are told apart by dashed or dotted hatch, then by a neutral marker.
Simple markers only, no custom font, so legends work in QGIS.

### 3.3 Aggregation between scales

The first plan was top-down inheritance: a child keeps its parent's symbol
and adds a modifier. Iteration 2 uses a simpler rule instead, because it
keeps one meaning per visual property at every scale:

- The same rules are applied at every scale to the unit's own variable ranges.
- A variable is drawn only where it separates units of the hovedtype at
  that scale, so coarse scales get simpler symbols.
- Every unit records its parent at the next coarser scale (`parent_kode_id`).

Cost: a child does not always share its parent's hatch angle (131 of 212
do between M020 and M050). Open for review.

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

| # | Deliverable | Status |
| --- | --- | --- |
| 0 | Reference material committed; this plan | Done |
| 1 | Hovedtype palette (72 colours, land and wetland) + colour overview | Draft 2, revised after the 2020 review comments. Needs colour review |
| 2 | Pattern rules + symbols for all three scales + rendered overview + validator | Draft 1. Needs review |
| 3 | QML export, rendered by QGIS 3.40 | Draft 1. Not compared side by side with the old QML, not tried in QGIS 4 |
| 4 | Plugin integration (replaces hash colours), unit and QGIS tests | Code done and tested at symbol level. User guide not updated |
| 5 | Trial on three mapped areas (M020) with the plugin's symbols | Done 2026-10-05; redrawn at the mapping scale 1:20 000 on 2026-10-07. Three rules corrected; findings in `docs/symbology/README.md` |
| 6 | Variant B: kalkfattig as unhatched baseline, drought as coloured rings | Chosen 2026-10-07 and used by the plugin. Variant A kept in `symbology/utkast_A` |

## 5.1 Open issues for the next round

1. Done: TG01 shows løsmassetype as one of seven shades of its fill
   (`subtype_colours.csv`); at most three pattern layers.
2. Accepted (2026-10-07): neutral tie-breaks stay. Every unit still has
   its own symbol; only the fill is shared within a hovedtype.
3. Aggregation: keep the same-rules approach, or return to strict
   inheritance so that a child always shows its parent's hatch angle.
4. Water groups (NA-L, NA-O, NA-M, NA-F, NA-I) have one fill per group.
5. "Myrkosten" (vegetation map symbols, 1980) was recommended by two
   reviewers but is not among the reference files.
6. Print and field test, QGIS 4 test, user guide chapter.
7. From the trial at 1:20 000: patterns vanish in 223 of 263 polygons
   (narrower than 160 m). Fill is now 65 % opaque. Kalkfattig hatch covered
   95 % of the area, which led to proposal B (13 %).
8. Done: variant B chosen. Moist ground is a filled blue circle, frisk a
   blue ring. B needs 34 tie-breaks at M005 against 31 in A; the three
   extra (TA01) were only told apart in A by two near-identical greys.

## 6. Decisions (2026-09-29)

| Question | Decision |
| --- | --- |
| Scope | Land and wetland first: NA-T and NA-V (72 hovedtyper; 388 / 212 / 116 units). Water groups keep a plain fill until a later iteration. |
| Pattern style | Hybrid, rule-based: hatch, dots, simple glyphs and dotted outlines. No custom font. |
| Plugin use | The new symbology replaces the hash colours. Standalone QML files are also produced. |
| Language | Norwegian for documentation and overview. |
| Fill opacity (2026-10-07) | Polygon fills 65 % opaque in the plugin. |
| Tie-breaks (2026-10-07) | Accepted, as long as every unit keeps its own symbol (checked automatically). |
| TG01 (2026-10-07) | One shade of the fill per løsmassetype. |
| Variant (2026-10-07) | B: kalkfattig without hatch, drought as rings; moist and frisk get different marks. |
