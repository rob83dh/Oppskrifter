# Oppskriftssamlingen – sammendrag

Last opp denne sammen med `oppskrifter.md` når du starter en ny samtale.
**Last også opp `build.py`, `nk_tabell.json`, `oppskrifter.html`, `index.html` og `sw.js` hvis appen skal bygges.**

---

## Hva prosjektet er

En personlig oppskriftssamling i `oppskrifter.md` med en søkbar HTML-app bygget rundt den. Appen ligger på GitHub Pages og brukes fra telefon, nettbrett og maskin.

**Status: 509 oppskrifter.** Appen er bygget og i synk med markdown per 28. juli 2026.

| Gruppe | Antall | Gruppe | Antall |
|---|---|---|---|
| Hovedretter | 164 | Småretter | 34 |
| Tilbehør | 71 | Desserter | 34 |
| Sauser og marinader | 65 | Grunnoppskrifter | 31 |
| Supper | 54 | Salater | 25 |
| Sjømat | 22 | Frokost | 16 |
| Brød | 13 | Bakverk | 6 |

Summen er 535 fordi 26 retter står med dobbel type.

**Neste ledige nummer:** 195 · B20 · D35 · F17 · G32 · S35 · SA8 · SJ17 · SU30 · T135

---

## Filer og byggekjede

```
oppskrifter.md              ← kilden, alt redigeres her
   ↓ build.py + nk_tabell.json
data.json                   ← 509 poster, 21 felter hver
   ↓ injiseres i <script id="data"> i begge HTML-filene
oppskrifter.html            (lokal bruk)
nettversjon/index.html      (GitHub Pages)
nettversjon/sw.js           (bump cache ved hver endring)
```

**GitHub:** `rob83dh/Oppskrifter` → `rob83dh.github.io/Oppskrifter`

**Service worker-cache står på `oppskrifter-v64`.** Bump alltid ved endringer, ellers får telefonen den gamle versjonen fra offline-lageret.

### Viktig om build.py

De originale `build.py`, `make_html.py` og `make_web.py` gikk tapt. `build.py` er **rekonstruert** ved å lese appens egen datablokk og verifisere byte for byte mot de 404 postene som lå der. 17 av 21 felter reproduseres identisk på alle 404.

`make_html.py` og `make_web.py` trengs ikke lenger: hele appen — CSS, JavaScript, handleliste, favoritter — ligger allerede i HTML-filene. Bare `<script id="data" type="application/json">` skal byttes ut.

**To kjente avvik mot den gamle appen**, begge enkeltoppskrifter:
- **B2** – `mi` blir 55 (aktiv tid) mot originalens 295 (inkludert natten i kjøleskap)
- **G9** – «1 stor eller 2 mindre pizzaer» gir `porsjoner`, originalen ga `pizzaer`

**Test:** `test_app.py` kjører Playwright mot `oppskrifter.html` og sjekker antall, tre søkefelt, gruppenedtrekk, åpning, beslektet-lenker, porsjonsskalering og konsollfeil.

Sikkerhetskopier ligger i `/tmp/sikkerhetskopi*.md` (1–48).

---

## Appens funksjoner

**Søk:** tre felt (Matrett, Matvare, Kjøkken) + gruppe-nedtrekk. Alle virker sammen.

**Utvalg-gruppene** nederst i nedtrekket er filtre, ikke plasseringer — en rett blir liggende i sin vanlige gruppe samtidig. De defineres i HTML-fila med `utvalg(verdi, tekst, test)` pluss en gren i `render()`. Grenen **må** ligge før `g.charAt(0) === '_'`, som ellers fanger alt som begynner med understrek og tolker det som tidsfilter. I dag: under 20/30/45 minutter, «Lett og proteinrik» (51) og «Hellstrøm» (100, filtrerer på kildefeltet).

**Favoritter:** stjerne på hvert kort og i detaljvisningen. Egen bolk «Mine» øverst i nedtrekket, som skjuler seg når den er tom.

**Handleliste:**
- Kurvikon på kortene, knapp i detaljvisningen. Følger porsjonsvelgeren.
- Rettene står øverst med porsjoner, med kryss for å fjerne.
- Varer slås sammen på tvers av retter.
- **Trykk på en rad** = grå og gjennomstreket, blir stående, men er ikke med når du deler.
- «Egne varer» nederst: fritekstfelt, hver linje kan strekes ut eller slettes med kryss.
- «Har du sannsynligvis»-bolk for basisvarer.
- Knapper: **Del listen** (lenke, hovedknapp) · Del som tekst · Fjern alle kryss.
- Åpner noen en delt lenke, havner de i **gjestemodus** uten vei inn i samlingen.

**Detaljvisning:** porsjonsvelger, avhuking av ingredienser, skjermlås, beslektede lenker, makrotall.

**Basisregler** (hva som havner i «Har du sannsynligvis»): alt som ender på sukker, mel eller olje · alt som ender på pulver, frø eller flak · alt merket tørket eller malt · en liste med hele krydder. Inneholder navnet «fersk» eller «frisk», er det aldri basis.

---

## Konvensjoner

**Kildehierarki:** Hellstrøm → Gladkokken → Matprat → asiatiske (Maangchi, CJ Eats, RecipeTin, Serious Eats med vurderinger) → klassisk standardversjon.

**Sosiale kilder:** ta med antall likes i kildefeltet. Terskel rundt 1000.

**Navngiving:**
- Proteinet skal stå i overskriften.
- Har flere retter samme protein, legges forfatteren til: `– [Forfatter] sin versjon`.
- Grunnboka-oppskriftene bruker genitiv: `Hellstrøms risotto`.
- Rettens etablerte navn beholdes og oversettes ikke (Katsu curry, ikke Katsukarri).
- **Bokas interne nummerering brukes ikke som navn.** «Pesto 1» og «Pesto 2» ble til `Hellstrøms pesto` og `Hellstrøms pesto med smør`, med bokas navn nevnt i notatet.

**Notatformat:** stikkord for tall og fakta, hele setninger for navn og begrunnelse. Notatene skal forklare *hvorfor*, ikke gjenta fremgangsmåten.

**Notater skal ikke telle.** «Femte Hellstrøm-oppskrift i samlingen» ruster og ble fjernet tre steder. Skriv beslektet-lenker i stedet.

**Merking av inngrep i kilden:** `*(Omregnet.)*` · `*(Presisert.)*` · `*(Lagt til.)*` · `*(Flagget.)*`

**Metriske mål.** Regn om fra cups og ounces, og merk det.

**Dobbel type:** `Sjømat · Salat` – oppskriften dukker opp i begge grupper. Brukes når retten hører reelt hjemme to steder, f.eks. dumplingsupper (`Hovedrett · Suppe`) og laks som hovedrett (`Hovedrett · Sjømat`).

**Grunnoppskrift er byggeklosser, ikke retter.** Deiger, røre, krydderblandinger og krafter. En saus hører til Saus/Marinade selv om den brukes i andre retter — majones, bechamel og marinara lå feilplassert her til 28. juli. Sylting og konservering hører til Tilbehør.

**Grunnoppskriftene ligger i logisk rekkefølge**, ikke kronologisk: pastadeiger (G1–G5), pizzadeiger (G6–G9), andre deiger og røre (G10–G13), flatbrød (G14–G16), meieri (G17), krydderblandinger (G18–G20), krafter (G21–G31). Legger du til en ny, sett den inn der den hører hjemme og renummerer resten.

**Beslektet-mønster:** `- **Beslektet:** [navn (nr. X)](#slug) beskrivelse`

**Lenketekst:** formen er `navn (nummer)` – `soyamarinert agurk (T3)`, ikke `T3 soyamarinert agurk`. Navnet er full tittel med liten forbokstav, unntatt egennavn (Hellstrøms, Filips, Biscoff) og forkortelser (BBQ). Står lenken der en rett allerede er nevnt ved navn, eller midt i en setning som forklarer den, holder det med nummeret alene – da unngår du «misosuppe – se misosuppe (nr. 6)».

**Ligner navnene på hverandre, kortes de ned til det som skiller.** Fem dumplingsupper blir `med reker (nr. 39)`, `saltnpiipas versjon (nr. 41)`, `tom yum (nr. 43)` – ikke full tittel fem ganger. Oppramsinger trenger en innledning: «Se også de øvrige dumplingsuppene: …»

---

## Arbeidsflyt når en oppskrift skal inn

1. **Sjekk duplikater først.** Søk på rettens navn, hovedingrediensen *og* samlingens egen terminologi. En glipp skjedde fordi jeg søkte «ribbe» mens samlingen sier «sideflesk». Sjekk også om samme kokk allerede står med en annen versjon — SU5 og SU21 er begge Hellstrøms løksuppe, fra ulike kilder.
2. Hent kilden. Facebook-lenker med `fbclid` er for lange for `web_fetch` – finn den rene adressen via søk.
3. Skriv et Python-skript som føyer oppskriften inn i riktig seksjon og legger til rad i innholdsfortegnelsen.
4. **Kontroller lenkene.** Bygg GitHubs slug-algoritme og sjekk at alle `](#...)` treffer en overskrift. Sjekk også at hver overskrift har nøyaktig én rad i innholdsfortegnelsen, og omvendt.
5. Oppdater topplinjen med nye tall.
6. `build.py`, injiser i begge HTML-filene, bump `sw.js`.
7. `test_app.py`.
8. `present_files`.

**Nye kjøkken må inn i `nk_tabell.json`.** Uten oppslag faller søket tilbake på kjøkkennavnet alene, og retten dukker ikke opp på regionsøk som «asiatisk» eller «europeisk».

---

## Kjente feil og uløste ting

**Porsjonsvelgeren skalerer ikke tall i parentes.** Bevisst regel, fordi «1 boks (400 g)» ikke skal dobles – og den delen virker: testet 29. juli, boksstørrelser og flaskevolum står stille mens antallet skalerer. Unicode-brøker skalerer også, i motsetning til hva som sto her før.

**Men parentes betyr to ting, og regelen skiller ikke.** «(400 g)» er en pakningsstørrelse som skal stå. «(70 g)» etter et måleskjeantall er en omregning som skal skalere. Derfor: **skriv den skalerbare mengden først og utenfor parentes.** `70 g proteinpulver — ca. 2½ måleskje` skalerer riktig; `2½ måleskje proteinpulver (70 g)` gjør det ikke. Tankestrek fungerer der parentes ikke gjør det – risomregningene (`3 dl kokt ris — ca. 1,2 dl tørr ris`) skalerer korrekt.

**Brøker skalerer ujevnt.** «¼ loff» ved 8 porsjoner blir stående som «⅛ loff» uansett porsjonstall. Gjelder unicode-brøker.



**Grunnboka** – 95 oppskrifter er inne. Saus-, suppe-, kraft- og tilbehørskapitlene er ferdig fotografert.

**Ingredienser som ikke brukes, hører hjemme i fremgangsmåten – ikke i et notat.** Seks oppskrifter hadde en ingrediens i lista som aldri ble nevnt i stegene, forklart i et notat under. Notatet leses ikke mens du lager mat. Alle seks er nå skrevet inn som steg, merket `*(Steget mangler i kilden – se notat.)*`. Verst var S16, som hoppet fra kald masse til panering uten å forme krokettene, og B3, som aldri fylte éclairsene.

**Oppvarming-kolonnen ble fjernet 29. juli.** Den var utfylt for 21 av 509, flere av verdiene var gale – frityrstekt kylling og ramen sto som «god» – og kolonnen vises ikke i appen i det hele tatt. Der oppvarming betyr noe, står det i notatet til retten, konkret: «sausen tykner når den er kald». Det er mer nyttig enn en merkelapp.

**Boblen om skjermknappen må aldri stå i veien.** Den dekker Favoritt- og Handleliste-knappene i oppskriftshodet, så den har `pointer-events:none` – trykk går rett gjennom til knappene under, og samme trykk lukker boblen via lytteren på `document`. Den forsvinner også ved første blaing (med 8 px terskel, så åpningens egen scroll ikke teller) og etter fem sekunder.

**De to HTML-filene kan komme i utakt.** `oppskrifter.html` og `nettversjon/index.html` har samme appkode, men de vedlikeholdes hver for seg. 30. juli manglet nettversjonen hele boble-logikken i flere dager fordi en gjenoppbygging brukte enkeltfila som mal for den ene og en eldre fil for den andre. **Sjekk alltid begge etter en endring** – testen kjører bare mot `oppskrifter.html`.

**Handlelisten sorteres etter butikkrekkefølge, oppskriften ikke.** `BUTIKK`-tabellen i app-JS-en har sju avdelinger i den rekkefølgen du går gjennom en Kiwi: frukt og grønt, kjøtt og fisk, meieri, brød, tørrvarer, krydder og olje, frys. Ukjente varer havner sist, ikke gjemt bort. Ingen overskrifter – varene legger seg bare riktig. `sorterButikk()` brukes to steder: i visningen og i delefunksjonen, som må ha samme rekkefølge.

**Oppskriftens egen ingrediensliste røres aldri.** Den følger bruksrekkefølgen i fremgangsmåten, gruppert etter deler av retten, slik at du kan lese ovenfra og ned mens du jobber. Det er en helt annen logikk enn butikkrutens, og de to skal ikke blandes.

**Lengste treff vinner i `butikkPlass()`.** Derfor havner «kyllinglårfilet» hos kjøtt selv om «kylling» også står der. Legger du til nye ord, husk flertallsformer – «gulrøtter» og «stilkselleri» ble oversett i første runde.

**Egne notater lagres per enhet.** Feltet nederst i hver oppskrift skriver til `localStorage` under nøkkelen `oppskrifter-egne-notater`, som et objekt fra oppskrifts-id til tekst. Ingen synkronisering mellom enheter, og ingen deling mellom brukere – det er meningen, siden lenken er delt med andre. Tømmes feltet, slettes oppføringen. Lagring skjer 400 ms etter siste tastetrykk, ikke per bokstav.

**Kortmarkør for notater ble forsøkt og forkastet.** Koden som bygger kortene ligger inne i en JS-streng med `\'`-escaping, og innskudd der brekker fila på måter som ikke gir JS-feil – appen bare slutter å rendre. To forsøk måtte rulles tilbake 30. juli. Vil du ha markøren, bygg den ved å endre `card`-malen strukturelt, ikke ved strengerstatning.

**Handlelisteknappen bytter form.** På forsiden står det «Handleliste (3 retter)» med kurvikon. Inne i en oppskrift krymper den til en ren sirkel på 46 px med bare ikonet – tallet ligger igjen i `aria-label`. `tegnKurvTall()` kalles både i `apne()` og `tilbake()` så formen følger modus. Knappen dekker et korts egen kurvknapp i de fleste blaposisjoner; det er målt, og luft nederst i lista løser det ikke. La det være.

**Tilbakeknappen sier bare «Tilbake».** Pilen forklarer retningen. Den lange «Tilbake til søket» står igjen som `aria-label` på ikonknappen `#tosearch`, der den er hele forklaringen en skjermleser får.

**Sida skal ikke indekseres, og det styres av `noindex`-taggen – ikke av robots.txt.** Begge HTML-filene har `noindex, nofollow, noarchive` i hodet. `robots.txt` slipper crawlere inn med vilje: blokkerer man crawling, får Google aldri lest noindex-taggen, og en side som allerede er indeksert blir liggende som naken lenke. Dette er den vanligste feilen på området, og den ble gjort her 30. juli før den ble rettet samme dag. GitHub Pages er offentlig uansett – dette hindrer bare at samlingen dukker opp i søk.

**Nettversjonen er en PWA med fire filer:** `index.html`, `sw.js`, `manifest.webmanifest` og `robots.txt`. De tre første er listet i `FILES` i sw.js; robots.txt skal ikke caches. Manifestet ligger i GitHub-repoet, ikke i utdata-mappa – be brukeren om det hvis det trengs, ikke lag et nytt.

**Ikonene ligger som base64 inne i manifestet**, ikke som egne filer. Det er med vilje: færre filer å laste opp fra telefon. Manifestet har tre ikoner – 192, 512 og 512 maskable – der maskable gjenbruker samme bilde som 512. Det er trygt her, fordi motivet bare strekker seg til 67 % av halve bredden mens Androids trygge sone går til 80 %. Bakgrunnen er ensfarget ut i hjørnene, så beskjæringen tar bare grønt felt.

**Favoritter og handleliste migreres automatisk.** Omnummereringen 29. juli ville ellers tømt dem for de 47 grunnoppskriftene. Migreringen ligger øverst i app-JS-en, kjører én gang, og merker seg med nøkkelen `oppskrifter-migrering`. Omnummererer du igjen, må du legge til en ny migrering med ny dato – `lagreFav()` lagrer bare id-er som finnes, så gamle favoritter forsvinner ved første stjernemerking uten den.

---

## Tekniske fallgruver

**Escaping i generert JavaScript.** Regex-literaler (`/\s+/`) skal ha én backslash, `new RegExp('...')` skal ha to. Over-escaping ødela hele sammenslåingen i handlelisten uten å gi feilmelding.

**Variabelrekkefølge.** En regex som ble bygget ved innlasting brukte en variabel som defineres lenger nede, og fikk `undefined` inn i seg. Bygg regexer ved første bruk.

**Enhetsgjenkjenning** må kreve mellomrom etter enheten, ellers blir «løk» til «1 liter øk».

**Seksjonsnavn:** brødene ligger under `# Bakverk`, ikke `# Brød`. `# Grunnoppskrifter` er siste seksjon og har ingen etterfølgende `# `. Oppskriftens kropp må stoppe ved neste `# `, ellers lekker seksjonsoverskriften inn i HTML-en.

**localStorage er per adresse.** Favoritter og handleliste på `github.io` og i den lokale fila er to separate lagre.

**`navigator.share` skal ha ett felt.** Sender du både `title`, `text` og `url`, plukker enkelte mottakerapper bare det ene og kaster resten. Dette ødela først WhatsApp-delingen, deretter SMS-lenken.

### Regler i build.py som ikke er åpenbare

- **Kursiv strippes i ingredienslister, men blir `<em>` i notater.** `*(Presisert.)*` står som ren tekst blant ingrediensene.
- **Fet skrift avbrytes av kursiv inni.** `**tekst (*canela*)**` gir literal `**`, ikke `<strong>`. Regexen er `\*\*([^*]+)\*\*`.
- **`mi` teller bare aktiv tid.** Marinering, heving, siling, bløtlegging, salting og fryser ekskluderes — men ikke hvis «inkludert» står i samme ledd, og ikke hvis tiden står i parentes.
- **Aksentkartet er med vilje ufullstendig.** `æøå` og `àáçèéêíóô` foldes i søkefeltene; `ñ ö î ì ù` gjør det ikke. Slik var originalen, og det ble beholdt for å treffe eksakt.
- **`nk` nøkles på kjøkken *og* plassering i innholdsfortegnelsen.** «Asiatisk-inspirert» gir tre ulike søkestrenger avhengig av hvilken undertabell retten står i.
- **`ti`, `p`, `kj` og `ki` leses fra oppskriftens egen kildelinje**, ikke innholdsfortegnelsen. Kildelinjen kan gå over to linjer. Mangler et felt, faller den tilbake på innholdsfortegnelsen.

---

## Nylig arbeid

Denne økten begynte med opprydding: nr. 121 og 123 over på genitivform, tre tellende notater fjernet, topplinjen rettet, og verifisering av at de sju døde ankerne fra tidligere ikke lenger finnes.

Deretter kom 77 oppskrifter fra Hellstrøms Grunnboka i fem runder — tilbehør og grunnoppskrifter, sauser og smør, vinaigretter, supper og krafter. Samlingen gikk fra 432 til 509, og Grunnboka står nå for 95 av dem.

Til slutt ble byggekjeden gjenoppbygget. Appen viste 404 oppskrifter og hadde ligget ett bygg bak i to økter; nettversjonen og den lokale fila var ikke engang i synk med hverandre. `build.py` ble rekonstruert fra appens egen datablokk, verifisert mot de 404 postene, og begge HTML-filene er nå på 509 med alle Playwright-tester grønne.
