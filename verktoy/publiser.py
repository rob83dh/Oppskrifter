#!/usr/bin/env python3
"""Bygger, kontrollerer og publiserer oppskriftsappen i én kommando.

Kjøres fra repo-roten:
    python3 verktoy/publiser.py                  bygg, sjekk, test, commit og push
    python3 verktoy/publiser.py -m "SJ20 laks"   egen commit-melding
    python3 verktoy/publiser.py --sjekk          bare kontroller, endrer ingenting
    python3 verktoy/publiser.py --ikke-push      alt unntatt commit og push
    python3 verktoy/publiser.py --uten-test      hopp over nettlesertesten
    python3 verktoy/publiser.py --bump-sw        tving ny cache-versjon i sw.js

Stopper ved første feil, før noe er pushet.

Hva skriptet gjør:
  1. Sjekker at du står på main og ikke ligger bak GitHub.
  2. Oppdaterer topplinjen i oppskrifter.md (antall og dato) automatisk.
  3. Kontrollerer innholdsfortegnelse, lenker, ID-er og kjøkkentabell.
  4. Bygger data og injiserer i index.html og oppskrifter.html.
  5. Bumper sw.js bare hvis selve appen (utenom data) er endret.
  6. Kjører test_app.py.
  7. Commit og push. GitHub Pages er oppdatert etter ca. ett minutt.
"""
import argparse, collections, datetime, json, os, re, subprocess, sys

HER = os.path.dirname(os.path.abspath(__file__))
ROT = os.path.dirname(HER)
sys.path.insert(0, HER)
import build  # noqa: E402

MD = 'oppskrifter.md'
HTML = ['index.html', 'oppskrifter.html']
SW = 'sw.js'
NK = 'verktoy/nk_tabell.json'  # redigeres for hånd, men følger med i commiten
DATA_RE = re.compile(r'(<script id="data" type="application/json">)(.*?)(</script>)', re.S)
SIDE = 'https://rob83dh.github.io/Oppskrifter/'

# Ordene i topplinjen -> gruppenavnet i data
TOPPLINJE = {'hovedretter': 'Hovedrett', 'tilbehør': 'Tilbehør', 'saus/marinade': 'Saus/Marinade',
             'supper': 'Suppe', 'småretter': 'Smårett', 'desserter': 'Dessert',
             'grunnoppskrifter': 'Grunnoppskrift', 'salater': 'Salat', 'sjømat': 'Sjømat',
             'frokost': 'Frokost', 'brød': 'Brød', 'bakverk': 'Bakverk'}
MND = ['januar', 'februar', 'mars', 'april', 'mai', 'juni', 'juli', 'august',
       'september', 'oktober', 'november', 'desember']

feil, advarsler = [], []


def git(*a, sjekk=True):
    r = subprocess.run(['git', *a], cwd=ROT, capture_output=True, text=True)
    if sjekk and r.returncode:
        sys.exit('git %s feilet:\n%s' % (' '.join(a), r.stderr))
    return r.stdout


def les(f):
    return open(os.path.join(ROT, f), encoding='utf-8').read()


def skriv(f, s):
    open(os.path.join(ROT, f), 'w', encoding='utf-8').write(s)


def fra_head(f):
    r = subprocess.run(['git', 'show', 'HEAD:' + f], cwd=ROT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ''


def uten_data(html):
    return DATA_RE.sub(r'\1\3', html)


def uten_topplinje(md):
    return re.sub(r'^Sist oppdatert:.*$', '', md, count=1, flags=re.M)


# ---------------------------------------------------------------- kontroller

def sjekk_git():
    gren = git('rev-parse', '--abbrev-ref', 'HEAD').strip()
    if gren != 'main':
        feil.append('Du står på grenen «%s», ikke main.' % gren)
    git('fetch', '--quiet', 'origin')
    bak = git('rev-list', '--count', 'HEAD..origin/main').strip()
    if bak != '0':
        feil.append('Lokal kopi ligger %s commit(s) bak GitHub. Kjør «git pull --rebase» først.' % bak)


def oppdater_topplinje(md, data):
    """Skriver riktige tall inn i topplinjen, i samme rekkefølge som før."""
    m = re.search(r'^Sist oppdatert: (.*?) · \*\*(\d+) oppskrifter\*\* · (.*)$', md, re.M)
    if not m:
        advarsler.append('Fant ikke topplinjen («Sist oppdatert: …») – ikke oppdatert.')
        return md
    teller = collections.Counter(k for r in data['R'] for k in r['ka'])
    deler = []
    for del_ in m.group(3).split(', '):
        mm = re.match(r'(\d+) (.+)$', del_.strip())
        navn = mm.group(2) if mm else del_
        grp = TOPPLINJE.get(navn.lower())
        if grp is None:
            advarsler.append('Ukjent gruppe i topplinjen: «%s»' % navn)
            deler.append(del_.strip())
        else:
            deler.append('%d %s' % (teller[grp], navn))
    mangler = set(teller) - {TOPPLINJE[re.sub(r'^\d+ ', '', d).lower()] for d in deler
                             if re.sub(r'^\d+ ', '', d).lower() in TOPPLINJE}
    if mangler:
        advarsler.append('Grupper som mangler i topplinjen: %s' % ', '.join(sorted(mangler)))

    dato = m.group(1)
    if uten_topplinje(md) != uten_topplinje(fra_head(MD)):
        i = datetime.date.today()
        dato = '%d. %s %d' % (i.day, MND[i.month - 1], i.year)

    ny = 'Sist oppdatert: %s · **%d oppskrifter** · %s' % (dato, len(data['R']), ', '.join(deler))
    gammel = m.group(0)
    if ny != gammel:
        print('  Topplinje:  %s\n           → %s' % (gammel[16:90], ny[16:90]))
    return md.replace(gammel, ny, 1)


def sjekk_innhold(md, data):
    linjer = md.split('\n')
    ids = [r['id'] for r in data['R']]
    dup = [k for k, v in collections.Counter(ids).items() if v > 1]
    if dup:
        feil.append('Samme nummer brukt flere ganger: %s' % ', '.join(dup))

    h2 = re.findall(r'^## ([A-ZÆØÅ]{0,2}\d+)\.', md, re.M)
    # Bare tabellen under «## Innhold» – «Lett og proteinrik» har egne rader
    innhold = re.search(r'^## Innhold$(.*?)(?=^## )', md, re.M | re.S)
    toc = re.findall(r'^\| *([A-ZÆØÅ]{0,2}\d+) *\|', innhold.group(1) if innhold else '', re.M)
    if not innhold:
        feil.append('Fant ikke seksjonen «## Innhold».')
    tc = collections.Counter(toc)
    if set(h2) - set(tc):
        feil.append('Oppskrift uten rad i innholdsfortegnelsen: %s' % ', '.join(sorted(set(h2) - set(tc))))
    if set(tc) - set(h2):
        feil.append('Rad i innholdsfortegnelsen uten oppskrift: %s' % ', '.join(sorted(set(tc) - set(h2))))
    flere = [k for k, v in tc.items() if v > 1]
    if flere:
        feil.append('Flere rader i innholdsfortegnelsen for: %s' % ', '.join(flere))

    # Lenker: GitHubs slug-algoritme på alle overskrifter, med -1, -2 ved like navn
    slugs = set()
    for l in linjer:
        if re.match(r'^#{1,6} ', l):
            b = build.slug(l.lstrip('#').strip())
            k, n = b, 1
            while k in slugs:
                k, n = '%s-%d' % (b, n), n + 1
            slugs.add(k)
    brutt = sorted({x for x in re.findall(r'\]\(#([^)\s]+)\)', md) if x not in slugs})
    if brutt:
        feil.append('Brutte interne lenker (%d): %s' % (len(brutt), ', '.join(brutt[:15])))

    # Kjøkken som mangler i nk_tabell.json faller ut av regionsøk som «asiatisk»
    kjente = set(build.NK.values())
    uten = [(r['id'], r['kj']) for r in data['R'] if r['nk'] not in kjente]
    if uten:
        advarsler.append('%d retter mangler oppslag i nk_tabell.json (vises ikke på regionsøk):\n      %s'
                         % (len(uten), '\n      '.join('%-5s %s' % x for x in uten)))


def injiser(html, js):
    treff = DATA_RE.findall(html)
    if len(treff) != 1:
        feil.append('Fant %d datablokker i HTML-fila, ventet nøyaktig én.' % len(treff))
        return html
    ny = DATA_RE.sub(lambda m: m.group(1) + js + m.group(3), html)
    # Validering: datablokken skal kunne leses igjen, og script-taggene gå opp
    tilbake = json.loads(DATA_RE.search(ny).group(2))
    if len(tilbake['R']) != len(json.loads(js)['R']):
        feil.append('Datablokken ble ikke lest tilbake riktig.')
    if ny.count('<script') != ny.count('</script>'):
        feil.append('Script-taggene går ikke opp (%d åpne, %d lukkede).'
                    % (ny.count('<script'), ny.count('</script>')))
    return ny


def bump_sw(tving):
    endret = tving or any(uten_data(les(f)) != uten_data(fra_head(f)) for f in HTML)
    if not endret:
        return False
    s = les(SW)
    m = re.search(r"var CACHE = 'oppskrifter-v(\d+)';", s)
    if not m:
        feil.append('Fant ikke cache-versjonen i sw.js.')
        return False
    nr = int(m.group(1))
    if fra_head(SW) and fra_head(SW) != s:
        return True  # allerede bumpet i denne runden
    skriv(SW, s.replace(m.group(0), "var CACHE = 'oppskrifter-v%d';" % (nr + 1)))
    print('  sw.js:      oppskrifter-v%d → v%d (appen er endret)' % (nr, nr + 1))
    return True


def nye_ider(data):
    gammel = DATA_RE.search(fra_head('index.html') or '')
    før = {r['id'] for r in json.loads(gammel.group(2))['R']} if gammel else set()
    return [r['id'] for r in data['R'] if r['id'] not in før]


def neste_ledige(data):
    høyest = collections.defaultdict(int)
    for r in data['R']:
        m = re.match(r'([A-ZÆØÅ]*)(\d+)$', r['id'])
        høyest[m.group(1)] = max(høyest[m.group(1)], int(m.group(2)))
    return ' · '.join('%s%d' % (k, v + 1) for k, v in sorted(høyest.items()))


def stopp_hvis_feil():
    for a in advarsler:
        print('  ADVARSEL: ' + a)
    if feil:
        print()
        for f in feil:
            print('  FEIL: ' + f)
        sys.exit('\nStoppet. Ingenting er pushet.')


# ---------------------------------------------------------------- hovedløp

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('-m', '--melding', help='commit-melding (ellers lages en automatisk)')
    ap.add_argument('--sjekk', action='store_true', help='bare kontroller, endre ingenting')
    ap.add_argument('--ikke-push', action='store_true', help='ikke commit og push')
    ap.add_argument('--uten-test', action='store_true', help='hopp over test_app.py')
    ap.add_argument('--bump-sw', action='store_true', help='tving ny cache-versjon i sw.js')
    a = ap.parse_args()

    print('1. Git');
    sjekk_git()
    stopp_hvis_feil()

    print('2. Bygger data fra %s' % MD)
    md = les(MD)
    data = build.parse(md)
    md_ny = oppdater_topplinje(md, data)
    print('  %d oppskrifter' % len(data['R']))

    print('3. Kontrollerer innhold')
    sjekk_innhold(md_ny, data)
    js = json.dumps(data, ensure_ascii=False)
    nye_html = {f: injiser(les(f), js) for f in HTML}
    stopp_hvis_feil()
    advarsler.clear()

    if a.sjekk:
        endres = [f for f in HTML if nye_html[f] != les(f)] + ([MD] if md_ny != md else [])
        print('\nAlt i orden. Ville endret: %s' % (', '.join(endres) or 'ingenting'))
        print('Neste ledige nummer: %s' % neste_ledige(data))
        return

    print('4. Skriver filer')
    if md_ny != md:
        skriv(MD, md_ny)
    for f in HTML:
        if nye_html[f] != les(f):
            skriv(f, nye_html[f])
    bump_sw(a.bump_sw)
    stopp_hvis_feil()

    if not a.uten_test:
        print('5. Tester appen i nettleser')
        r = subprocess.run([sys.executable, os.path.join(HER, 'test_app.py')], cwd=ROT)
        if r.returncode:
            sys.exit('\nTesten feilet. Filene er bygget, men ingenting er pushet.')

    endret = git('status', '--porcelain', '--', MD, SW, NK, *HTML).strip()
    if not endret:
        print('\nIngen endringer å publisere.')
        return
    print('\nEndringer:')
    print(git('diff', '--stat', '--', MD, SW, NK, *HTML))
    if a.ikke_push:
        print('Bygget, men ikke pushet (--ikke-push).')
        return

    nye = nye_ider(data)
    melding = a.melding or ('Nye oppskrifter: %s' % ', '.join(nye) if nye else 'Oppdaterte oppskrifter')
    print('6. Commit og push: %s' % melding)
    git('add', MD, SW, NK, *HTML)
    git('commit', '--quiet', '-m', melding)
    git('push', '--quiet', 'origin', 'main')
    print('\nPublisert. %s er oppdatert om ca. ett minutt.' % SIDE)


if __name__ == '__main__':
    main()
