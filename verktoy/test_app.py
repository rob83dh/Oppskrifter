#!/usr/bin/env python3
"""Røyktest av appen i en ekte nettleser (Playwright/Chromium).

Kjøres fra repo-roten:  python3 verktoy/test_app.py
Tester begge HTML-filene via en lokal webserver, slik at service workeren
oppfører seg som på GitHub Pages.

Sjekker: antall retter, de tre søkefeltene, gruppenedtrekket,
åpning av en oppskrift, porsjonsskalering og konsollfeil.
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
        b.close()
    srv.shutdown()
    sys.exit(0 if alt_ok else 1)


if __name__ == '__main__':
    main()
