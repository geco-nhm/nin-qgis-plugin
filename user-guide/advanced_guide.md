# Veiledning: Opprette nye felt og legge dem inn i skjema i QGIS

Denne veiledningen beskriver hvordan du oppretter nye felt i et lag og legger dem inn i redigeringsskjemaet (Attributes Form) i QGIS. Skjermbildene er referert direkte i teksten slik at dokumentet kan eksporteres til HTML.

---

## 1. Åpne egenskaper for laget

![Skjermbilde 1 – Åpne egenskaper for laget](images/Screenshot%202026-01-20%20at%2018.02.10.png)

- Høyreklikk på laget (nin_polygons) i laglisten.
- Velg Properties… (Egenskaper) fra menyen.
- I dialogen som åpnes, velg fanen Fields i venstremenyen.

Dette viser alle eksisterende attributtfelt i laget.

---

## 2. Aktiver redigering av felt

![Skjermbilde 2 – Aktiver redigering](images/Screenshot%202026-01-20%20at%2018.02.25.png)

- Klikk på blyant-ikonet øverst i feltlisten for å aktivere redigering av strukturen.
- Når redigering er aktivert, kan du legge til, slette eller endre felt.

---

## 3. Legg til nytt felt

![Skjermbilde 3 – Legg til felt](images/Screenshot%202026-01-20%20at%2018.04.02.png)

- Klikk på ikonet Legg til felt (gult ark med grønt plusstegn).
- Dialogen Add Field åpnes.

---

## 4. Opprett feltet NVE_ID

![Skjermbilde 4 – Definer feltet NVE_ID](images/Screenshot%202026-01-20%20at%2018.05.07.png)

- Skriv NVE_ID i feltet Name.
- Velg datatype Integer (32 bit).
- Kontroller at Provider type settes automatisk til integer.
- Klikk OK for å opprette feltet.

Dette feltet brukes til å lagre numerisk ID fra NVE.

---

## 5. Opprett feltet firma

![Skjermbilde 5 – Velg tekstfelt](images/Screenshot%202026-01-20%20at%2018.05.52.png)

- Klikk igjen på Legg til felt.
- Skriv firma i Name.
- Velg datatype Text (string).

---

## 6. Angi lengde for tekstfelt

![Skjermbilde 6 – Angi lengde](images/Screenshot%202026-01-20%20at%2018.06.07.png)

- Når datatype er satt til tekst, angi Length = 50.
- Klikk OK for å opprette feltet.

Dette bestemmer maksimal lengde på teksten som kan lagres i feltet.

---

## 7. Kontroller at feltene er lagt til

![Skjermbilde 7 – Feltene er opprettet](images/Screenshot%202026-01-20%20at%2018.06.18.png)

- De nye feltene NVE_ID og firma vises nå nederst i feltlisten.
- Klikk Apply eller OK for å lagre endringene i lagets struktur.

---

## 8. Åpne fanen Attributes Form

![Skjermbilde 8 – Attributes Form](images/Screenshot%202026-01-20%20at%2018.07.13.png)

- Gå til fanen Attributes Form i venstremenyen.
- Her konfigureres hvordan redigeringsskjemaet for laget skal se ut.

---

## 9. Flytt feltet NVE_ID inn i skjemaet

![Skjermbilde 9 – Dra NVE_ID inn i skjema](images/Screenshot%202026-01-20%20at%2018.08.16.png)

- Finn feltet NVE_ID i listen Available Widgets.
- Dra feltet over til ønsket plassering i Form Layout (for eksempel øverst under Type 1).

---

## 10. Flytt feltet firma inn i skjemaet

![Skjermbilde 10 – Dra firma inn i skjema](images/Screenshot%202026-01-20%20at%2018.08.46.png)

- Finn feltet firma i Available Widgets.
- Dra feltet til ønsket plassering i skjemaet, rett under NVE_ID.

---

## 11. Lagre oppsettet

- Klikk Apply eller OK for å lagre skjemaoppsettet.
- Når du nå åpner attributtskjemaet for laget, vil feltene NVE_ID og firma vises i skjemaet.

---

## 12. Sett felttype til Value Map

![Skjermbilde 11 – Velg Widget Type Value Map](images/Screenshot%202026-01-20%20at%2018.10.59.png)

- Marker feltet firma i Form Layout.
- I høyre panel, under Widget Type, velg Value Map.
- Dette gjør at feltet vises som en nedtrekksliste med forhåndsdefinerte verdier.

---

## 13. Legg inn verdier i Value Map

![Skjermbilde 12 – Definer verdier i Value Map](images/Screenshot%202026-01-20%20at%2018.13.21.png)

- I tabellen under Value og Description, legg inn ønskede koder og visningsnavn:
  - 1 – biofokus
  - 2 – ecofact
  - 3 – norkonsult
  - 4 – multikonsult
- Alternativt kan du bruke Load Data from CSV File hvis listen finnes i en fil.

Verdien i kolonnen Value lagres i databasen, mens Description vises i skjemaet.

---

## 14. Kontroller skjemaet i redigeringsmodus

![Skjermbilde 13 – Feltene vises i skjema](images/Screenshot%202026-01-20%20at%2018.15.56.png)

- Åpne attributtskjemaet for en flate i laget.
- Øverst i skjemaet vises nå feltene:
  - NVE id – må være heltall
  - firma (som nedtrekksliste)

Dette bekrefter at både nye felt og skjemaoppsett fungerer korrekt.

---

## 15. Velg verdi fra nedtrekkslisten

![Skjermbilde 14 – Velg firma fra liste](images/Screenshot%202026-01-20%20at%2018.16.43.png)

- Klikk på nedtrekkslisten for feltet firma.
- Velg ønsket firma fra listen (for eksempel norkonsult).
- Verdien lagres automatisk når objektet lagres.

---
---

## Resultat

Du har nå:

- Opprettet nye felt i attributtabellen.
- Definert riktig datatype og lengde.
- Lagt feltene inn i redigeringsskjemaet slik at de kan fylles ut ved digitalisering eller redigering.
- Konfigurert feltet firma som en nedtrekksliste med forhåndsdefinerte verdier.

Denne strukturen fungerer direkte for eksport til HTML (for eksempel via MkDocs, Pandoc eller Sphinx).