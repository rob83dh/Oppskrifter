#!/usr/bin/env python3
"""Lager seksjonen «## Lett og proteinrik» i oppskrifter.md på nytt.

Kalles av publiser.py ved hver bygging, så listen aldri blir utdatert.
Næringsinnholdet regnes ut av naering.py fra ingredienslistene.

Regelen:
  - minst 28 g protein per porsjon (30 g er målet, 28–30 g er «på grensen»)
  - under 705 kcal per porsjon (700 er målet, med litt slingringsmonn)
  - bare hovedretter, sjømat, supper, salater, småretter og frokost –
    ikke tilbehør, grunnoppskrifter, desserter eller bakverk

Unntakene under er vurdert for hånd.
"""
import os, sys

HER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HER)
import naering  # noqa: E402

MIN_PROTEIN = 28.0
MAKS_KCAL = 705
IKKE_PREFIKS = ('T', 'G', 'D', 'B')

# Holdes utenfor selv om tallene ser bra ut – beregningen er misvisende.
UTELAT = {
    '202': 'mange ingredienser kan ikke beregnes',
    '208': 'flere ingredienser kan ikke beregnes',
    '221': 'pastaen mangler mengde, tallet gjelder bare sausen',
    'S36': 'bao-bollene er ikke med i beregningen',
    'SA5': '2 dl majones – ikke «lett»',
}

# Tas med selv om beregningen havner litt over 700 kcal.
TA_MED = {
    '12': 'kyllingpho – risnudlene løfter anslaget til ca. 710 kcal',
}

# Kilden oppgir selv næringsinnhold per porsjon, og det er sikrere enn anslaget.
KILDETALL = {
    '210': (575, 51.0),
}


def beregn_alle(data):
    """Returnerer {id: (kcal, protein)} for alle oppskrifter med porsjonsantall."""
    ut = {}
    for r in data['R']:
        p = naering.porsjoner(r)
        if not p:
            continue
        k, pr, _ = naering.beregn(r)
        ut[r['id']] = (k / p, pr / p)
    ut.update(KILDETALL)
    return ut


def velg(data, tall):
    rader = []
    for r in data['R']:
        i = r['id']
        if i not in tall or i in UTELAT or i.startswith(IKKE_PREFIKS):
            continue
        k, p = tall[i]
        if p >= MIN_PROTEIN and (k < MAKS_KCAL or i in TA_MED):
            rader.append((p, k, i))
    rader.sort(reverse=True)
    return rader


def seksjon(md, data):
    """Bygger seksjonsteksten. Lenketekstene hentes fra innholdsfortegnelsen."""
    import re
    lenke = {}
    for l in md.split('\n'):
        m = re.match(r'^\| ([A-ZÆØÅ]{0,2}\d+) \| (\[[^\]]+\]\(#[^)]+\))', l)
        if m:
            lenke.setdefault(m.group(1), m.group(2))
    tall = beregn_alle(data)
    rader = [x for x in velg(data, tall) if x[2] in lenke]
    tekst = ('## Lett og proteinrik\n\n'
             '%d retter med minst 30 g protein og under 700 kcal per porsjon. Listen lages på nytt '
             'automatisk hver gang samlingen publiseres, beregnet fra ingredienslistene med '
             '`naering.py`. Tallene er anslag med rundt 15 %% usikkerhet, siden kokesvinn, merkevarer '
             'og uveide ingredienser slår inn. Retter like under proteingrensen (28–30 g) eller like '
             'over 700 kcal er tatt med. Der kilden selv oppgir næringsinnhold, brukes kildens tall. '
             'Retter der viktige ingredienser mangler mengde, er holdt utenfor. '
             '%d av samlingens oppskrifter har porsjonsantall og kan beregnes.\n\n'
             '| # | Rett | kcal | Protein |\n|---|------|------|---------|\n'
             % (len(rader), len(tall)))
    tekst += '\n'.join('| %s | %s | %d | %.1f g |' % (i, lenke[i], round(k), p) for p, k, i in rader)
    return tekst + '\n'


def oppdater(md, data):
    """Bytter ut seksjonen i md. Returnerer ny md (uendret hvis seksjonen ikke finnes)."""
    a = md.find('\n## Lett og proteinrik\n')
    if a < 0:
        return md
    b = md.find('\n## ', a + 1)
    if b < 0:
        return md
    return md[:a + 1] + seksjon(md, data) + md[b:]
