#!/usr/bin/env python3
"""Røyktest av appen i en ekte nettleser (Playwright/Chromium).

Kjøres fra repo-roten:  python3 verktoy/test_app.py
Tester begge HTML-filene via en lokal webserver, slik at service workeren
oppfører seg som på GitHub Pages.

Sjekker: antall retter, de tre søkefeltene, gruppenedtrekket,
åpning av en oppskrift, porsjonsskalering og konsollfeil.

Omregningen kontrolleres for ALLE oppskrifter på alle porsjonsvalg appen
tilbyr, opp til fire ganger oppskriften (minst 12): ingen mengde skal få
brøker som ⅜ eller ⅝, ¾, «1¼», «½ ss», spenn som «1–1», eller bli 0.
Pluss noen kjente fasitsvar.
"""
import json, re, sys, threading, functools, http.server, socketserver, os
from playwright.sync_api import sync_playwright

ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILER = ['index.html', 'oppskrifter.html']


def antall_i_data(fil):
    s = open(os.path.join(ROT, fil), encoding='utf-8').read()
    m = re.search(r'<script id="data" type="application/json">(.*?)</script>', s, re.S)
    return len(json.loads(m.group(1))['R'])


def start_server():
    class Stille(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    h = functools.partial(Stille, directory=ROT)
    srv = socketserver.TCPServer(('127.0.0.1', 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def test_fil(page, url, n):
    feil = []
    page.on('pageerror', lambda e: feil.append('JS-feil: %s' % e))
    page.on('console', lambda m: m.type == 'error' and feil.append('Konsoll: %s' % m.text))
    page.goto(url)
    page.wait_for_selector('#list .card')

    def vist():
        return page.locator('#list .card').count()

    tekst = page.locator('#count').inner_text()
    tall = int(re.search(r'\d+', tekst).group())
    assert tall == n, 'telleren viser %d, data har %d' % (tall, n)

    for felt, ord_ in [('#q1', 'ramen'), ('#q2', 'laks'), ('#q3', 'asiatisk')]:
        page.fill(felt, ord_)
        assert vist() > 0, 'ingen treff på «%s» i %s' % (ord_, felt)
        page.fill(felt, '')

    page.fill('#q1', 'xyzqqq')
    assert vist() == 0, 'tullesøk ga treff'
    page.fill('#q1', '')

    valg = page.locator('#grp option').count()
    assert valg >= 12, 'bare %d valg i gruppenedtrekket' % valg
    verdier = [v for v in page.locator('#grp option').evaluate_all('o => o.map(x => x.value)')
               if v and not v.startswith('_')]
    page.select_option('#grp', verdier[0])
    assert 0 < vist() < n, 'gruppefilteret filtrerer ikke'
    page.select_option('#grp', '')

    page.locator('#list .card').first.click()
    page.wait_for_function("document.body.classList.contains('reading')")
    detalj = page.locator('#detail').inner_text()
    assert len(detalj) > 100, 'detaljvisningen er tom'

    # Porsjonsskalering: finn en +-knapp i detaljvisningen og se at noe endrer seg
    pluss = page.locator('#detail button', has_text=re.compile(r'^\+$'))
    if pluss.count():
        før = page.locator('#detail').inner_text()
        pluss.first.click()
        assert page.locator('#detail').inner_text() != før, 'porsjonsvelgeren endrer ingenting'
    else:
        feil.append('Fant ingen +-knapp for porsjoner (sjekk velgeren i testen)')

    return feil


RAR = re.compile(r'[⅛⅜⅝⅞⅓⅔⅕⅖⅗⅘⅙⅚]')
LIKT_SPENN = re.compile(r'(?<![\d,½¼¾])(\d+(?:,\d+)?[½¼¾]?|[½¼¾])–\1(?![\d,½¼¾])')
NULL = re.compile(r'(?<![\d,])0(?=\s|–)(?!\s*(?:eller|tipo))')
# Robs skjeregler: ikke ¾, ikke 1¼/2¼ osv., ikke halve ss
TREKVART = re.compile(r'¾')
KVART_ETTER_TALL = re.compile(r'\d¼')
HALV_SS = re.compile(r'½\s*ss\b')

# (id, porsjoner, ingredienslinje som må finnes)
FASIT = [
    ('D18', 4, 'Revet skall og saft av 2 sitroner (ca. 0,8 dl saft)'),
    ('142', 2, '½ sjalottløk'),
    ('142', 2, '1 hvitløksfedd (bare 3 brukes – se notat)'),
    ('142', 2, '½ sitron'),
    ('D18', 4, '100 g sukker'),
]


def test_skalering(b, fil):
    """Kjører appens egne omregningsfunksjoner på alle oppskrifter."""
    s = open(os.path.join(ROT, fil), encoding='utf-8').read()
    data = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', s, re.S).group(1))
    js = s[s.index('var FRAC'):s.index('/* ---------- porsjonsvelger')]
    jobber = []
    for r in data['R']:
        if not r['b']:
            continue
        # samme steg som + og − i appen
        st, k = r['st'] or 1, 1
        while k * st <= max(4 * r['b'], 12) + 1e-9:
            n = round(k * st, 2)
            if n != r['b']:
                jobber.append([r['id'], n, n / r['b'], r['ing']])
            k += 1
    page = b.new_page()
    page.set_content('<html></html>')
    page.add_script_tag(content=js)
    ut = page.evaluate('(J) => J.map(j => j[3].map(l => skaler(l, j[2])))', jobber)
    page.close()
    feil = []
    for (rid, n, _, ing), res in zip(jobber, ut):
        for o, l in zip(ing, res):
            for rx, navn in ((RAR, 'brøk'), (LIKT_SPENN, 'likt spenn'), (NULL, 'null'),
                             (TREKVART, '¾'), (KVART_ETTER_TALL, '1¼ e.l.'), (HALV_SS, '½ ss')):
                if len(rx.findall(l)) > len(rx.findall(o)):
                    feil.append('%s til %s (%s): «%s» → «%s»' % (rid, n, navn, o, l))
    svar = {(rid, n): res for (rid, n, _, _), res in zip(jobber, ut)}
    for rid, n, linje in FASIT:
        if linje not in svar.get((rid, n), []):
            feil.append('%s til %s: fant ikke «%s»' % (rid, n, linje))
    return feil, len(jobber)


def main():
    srv, port = start_server()
    alt_ok = True
    with sync_playwright() as p:
        b = p.chromium.launch()
        for f in FILER:
            n = antall_i_data(f)
            page = b.new_page()
            try:
                feil = test_fil(page, 'http://127.0.0.1:%d/%s' % (port, f), n)
            except AssertionError as e:
                feil = ['FEIL: %s' % e]
            except Exception as e:
                feil = ['FEIL (%s): %s' % (type(e).__name__, e)]
            harde = [x for x in feil if not x.startswith('Fant ingen')]
            print('%-18s %s' % (f, 'OK (%d retter)' % n if not harde else 'FEILET'))
            for x in feil:
                print('   ', x)
            alt_ok &= not harde
            page.close()
            sk, antall = test_skalering(b, f)
            print('%-18s %s' % ('  omregning', 'OK (%d porsjonsvalg)' % antall if not sk
                                else 'FEILET (%d linjer)' % len(sk)))
            for x in sk[:15]:
                print('   ', x)
            alt_ok &= not sk
        b.close()
    srv.shutdown()
    sys.exit(0 if alt_ok else 1)


if __name__ == '__main__':
    main()
