# Oppskriftssamlingen

Personlig oppskriftssamling i `oppskrifter.md`, publisert som PWA på
https://rob83dh.github.io/Oppskrifter/ (GitHub Pages fra `main`).
Rob sender lenker, tekst eller skjermbilder; du legger oppskriftene inn.
Svar på norsk.

Konvensjoner for innhold, navngiving, notater, lenker og nummerering står i
@docs/prosjektsammendrag.md. **Der den og denne fila er uenige, gjelder denne
fila.** Særlig er avsnittene «Filer og byggekjede» og «Arbeidsflyt» i
sammendraget erstattet av det som står under, og tallene der (antall,
neste ledige nummer, cache-versjon) er utdaterte – hent dem fra repoet.

## Filer

```
oppskrifter.md          ← kilden, alt redigeres her
index.html              ← appen på GitHub Pages (datablokk injiseres)
oppskrifter.html        ← samme app til lokal bruk (datablokk injiseres)
i-dag.html, manifest.webmanifest, robots.txt  ← røres ikke av byggingen
sw.js                   ← service worker, bumpes automatisk ved behov
verktoy/build.py        ← markdown → data (rekonstruert, gir byte-lik data)
verktoy/nk_tabell.json  ← kjøkken → regionsøkeord
verktoy/naering.py      ← kontroll av kcal/protein
verktoy/publiser.py     ← hele byggekjeden i én kommando
verktoy/test_app.py     ← røyktest i Chromium (Playwright)
verktoy/hent_video.py   ← tekst, tale og skjermbilder fra TikTok/Instagram/YouTube
.video/                 ← arbeidsmappe for videoer, ignoreres av git
```

HTML-filene redigeres aldri for hånd for å endre oppskrifter. Appen leser
ikke `oppskrifter.md` selv; den ser bare det som er injisert.

## Arbeidsflyt for en ny oppskrift

1. `git pull --rebase` før du begynner.
2. `python3 verktoy/publiser.py --sjekk` – viser neste ledige nummer per prefiks
   og bekrefter at utgangspunktet er rent.
3. **Sjekk duplikater** med grep: rettens navn, hovedingrediensen og
   samlingens egne ord (samlingen sier «sideflesk», ikke «ribbe»). Sjekk også
   om samme kokk allerede har en versjon.
4. Hent kilden. Facebook-lenker med `fbclid` må renses først.
5. Rediger `oppskrifter.md` med Python, og bruk `assert s.count(old) == 1`
   før hver `replace()`. Tre ting per oppskrift: oppskriftsteksten foran riktig
   seksjonsskille, raden i innholdsfortegnelsen under riktig kjøkkengruppe, og
   eventuelle beslektet-lenker begge veier. **Topplinjen oppdateres
   automatisk** av publiser.py – ikke rør tallene der.
6. Nytt kjøkken? Legg det inn i `verktoy/nk_tabell.json`, ellers faller retten
   ut av regionsøk som «asiatisk». publiser.py advarer om dette.
7. `python3 verktoy/publiser.py` – bygger, kontrollerer, tester, committer og
   pusher. Commit-meldingen lages av nye nummer; bruk `-m` for noe annet.
8. Si fra til Rob hva som ble lagt inn (nummer og tittel). Siden er oppdatert
   etter ca. ett minutt.

Stopper publiser.py med FEIL, rett feilen i `oppskrifter.md` og kjør på nytt.
Bruk aldri `--uten-test` eller hopp over kontroller for å få noe ut.

## Videooppskrifter (TikTok, Instagram Reels, YouTube)

Oppskriften står sjelden komplett i teksten under videoen. Mengder og steg
ligger ofte bare i det som sies eller i tekst på skjermen. Hent derfor alt:

1. `python3 verktoy/hent_video.py <lenke>` – lager `.video/<id>/` med
   `oppsummering.md` (konto, dato, likes, videotekst, transkribert tale med
   tidspunkt) og kontaktark `ark-01.jpg …` med 9 skjermbilder hver.
   Instagram feiler ofte uten innlogging: prøv `--cookies chrome`.
2. Les `oppsummering.md`. **Se så på hvert kontaktark** – mengder,
   temperaturer og ingredienser som bare vises på skjermen finnes ikke i
   talen. Er teksten for liten, åpne enkeltbildet i `.video/<id>/bilder/`
   (filnavnet er sekundet i videoen).
3. Sett sammen ingredienser og fremgangsmåte fra alle tre kildene. Der de
   motsier hverandre, gjelder det som står på skjermen foran det som sies,
   og begge foran videoteksten. Nevn motsigelsen i notatet.
4. Mengder som ikke står noe sted, skal ikke gjettes stille: skriv et
   fornuftig anslag merket `*(Lagt til.)*`, eller `*(Flagget.)*` hvis det
   er usikkert, og si fra til Rob.
5. Kildefeltet: `@konto (TikTok, dato)` pluss antall likes, som før.
6. Slett `.video/<id>/` når oppskriften er publisert.

## Typiske feil å se etter i kilder

Enheter (cups, ounces, tablespoons → metrisk, merket `*(Omregnet.)*`),
fettprosent i fløte, eddikstyrke, ingredienser som er vanskelige å få tak i
i Norge (chipotle i adobo, spesielle chili, mirin vs. aji-mirin), salt og
pepper som mangler i ingredienslista, og motsigelser mellom oppskriftskortet
og brødteksten.

## Git

- Jobb direkte på `main`; én commit per økt eller per oppskrift er greit.
- Ikke force-push. Ikke commit `__pycache__` eller midlertidige filer.
- Store endringer på tvers av mange oppskrifter (språk, enheter): gjør dem i
  egne commits, slik at de kan reverseres hver for seg.
