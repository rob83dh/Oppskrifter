#!/usr/bin/env python3
"""Bygger data.json fra oppskrifter.md.

Rekonstruert ved å lese appens egen datablokk og verifisere byte for byte
mot de 404 postene som allerede lå der.
"""
import re, json, sys, html, os

ORDER = ['Frokost','Hovedrett','Suppe','Sjømat','Salat','Smårett','Tilbehør',
         'Saus/Marinade','Brød','Bakverk','Dessert','Grunnoppskrift']
PLURAL = {'Frokost':'Frokost','Salat':'Salater','Hovedrett':'Hovedretter','Suppe':'Supper',
          'Sjømat':'Sjømat','Smårett':'Småretter','Tilbehør':'Tilbehør',
          'Saus/Marinade':'Sauser og marinader','Brød':'Brød','Bakverk':'Bakverk',
          'Dessert':'Desserter','Grunnoppskrift':'Grunnoppskrifter'}

HER = os.path.dirname(os.path.abspath(__file__))
NK = json.load(open(os.path.join(HER, 'nk_tabell.json'), encoding='utf-8'))

ENHETER = {'dl','liter','l','g','kg','ss','ts','stykker','biter','boller','brød',
           'baguetter','burgere','deigballer','dumplings','pizzaer','rundstykker',
           'smørbrød','tortillas','wontons','porsjoner','lefser','pannekaker',
           'sitroner','baller','kaker','muffins'}
ADJEKTIV = {'store','stor','stort','små','liten','lite','ca'}
UDELELIG = {'brød','pizzaer','baguetter','rundstykker','burgere','smørbrød'}


def esc(s):
    return html.escape(s, quote=True)


def slug(h):
    S = re.compile(
        "[\u0000-\u001F!-,\\./:-@\\[-\\^`\\{-~"
        "\u00A0-\u00A9\u00AB-\u00B4\u00B6-\u00B9\u00BB-\u00BF\u00D7\u00F7"
        "\u2010-\u2027\u2030-\u205E\u2060-\u2064\u206A-\u2071\u2075-\u207E"
        "\u2080-\u208E\u20A0-\u20BF\u2100-\u2101\u2103-\u2106\u2108-\u2109"
        "\u2114\u2116-\u2118\u211E-\u2123\u2125\u2127\u2129\u212E\u213A-\u213B"
        "\u2140-\u2144\u214A-\u214D\u214F-\u215F\u2189-\u24B5\u24EA-\u2BFF"
        "\u2E00-\u2E7F\u3000-\u3004\u3008-\u3020\u3030\uFD3E-\uFD3F\uFE45-\uFE46]",
        re.UNICODE)
    return S.sub('', h.lower().strip()).replace(' ', '-')


AKSENT = {'æ':'ae','ø':'o','å':'a','à':'a','á':'a','ç':'c',
          'è':'e','é':'e','ê':'e','í':'i','ó':'o','ô':'o'}

def norm(s):
    s = s.lower()
    return ''.join(AKSENT.get(c, c) for c in s)


def avkurs(s):
    return re.sub(r'\*(.+?)\*', r'\1', s)


def inline_ren(s):
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    return s


def inline(s, anchors):
    s = esc(s)

    def lenke(m):
        txt, href = m.group(1), m.group(2)
        if href.startswith('#'):
            return '<a class="ref" data-id="%s">%s</a>' % (
                esc(anchors.get(href[1:], '')), inline_ren(txt))
        return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (href, inline_ren(txt))

    s = re.sub(r'\[([^\]]*)\]\(([^)]+)\)', lenke, s)
    return inline_ren(s)


PASSIV = {'marinering','marinere','marinert','marinade','tørking','tørke',
          'heving','heve','avkjøling','avkjøle','kjøleskap','fryser','fryseren',
          'hviling','hvile','siling','bløtlegging','salting',
          'svelling','svelle','sveller'}

def tid_min(ti):
    """Aktiv tid. Passive perioder – marinering, heving, siling – teller ikke."""
    t = ti.lower()
    # En parentes etter en total betyr én av tre ting:
    #   «(+ 30 min marinering)»            – tillegg, behandles som vanlig tid
    #   «(inkl. 15 min salting)»           – allerede med i totalen, ignoreres
    #   «(5 min forb. + 15 min steking)»   – spesifiserer totalen
    # I det siste tilfellet bruker vi oppdelingen hvis den skiller ut passiv
    # tid, ellers totalen. Uten oppdeling ville «1 t 10 min (45 min marinering
    # + 25 min koking)» gitt 70 minutter aktiv tid i stedet for 25.
    i = t.find('(')
    if i > 0 and re.search(r'\d', t[:i]):
        for m in re.finditer(r'\(([^)]*)\)', t):
            inni = m.group(1)
            if not re.search(r'\d', inni) or inni.lstrip().startswith('+'):
                continue
            if re.search(r'inkl', inni):
                t = t.replace(m.group(0), ' ')
            elif any(o in inni for o in PASSIV):
                t = inni                      # oppdelingen skiller ut passiv tid
                break
            else:
                t = t.replace(m.group(0), ' ')
    treff = list(re.finditer(r'(\d+)\s*(½)?\s*(timer|time|t|min)\b', t))
    tot = 0
    for n, m in enumerate(treff):
        slutt = treff[n+1].start() if n+1 < len(treff) else len(t)
        etter = t[m.end():slutt]
        if etter.lstrip().startswith('('):     # parentes er en merknad, ikke egen tid
            etter = ''
        etter = re.split(r'[+)]', etter)[0]
        ord_ = re.findall(r'[a-zæøå]+', etter)
        if any(o in ord_ for o in PASSIV) and not ({'inkludert','inkl'} & set(ord_)):
            continue
        v = int(m.group(1)) + (0.5 if m.group(2) else 0)
        tot += v * 60 if m.group(3).startswith('t') else v
    return int(tot)


def tid_total(ti):
    """Total tid fra start til servering, passive perioder inkludert.
    Ved spenn brukes det høyeste tallet – «2–24 t marinering» blir 24 t."""
    t = ti.lower()
    i = t.find('(')
    if i > 0 and re.search(r'\d', t[:i]):
        for m in re.finditer(r'\(([^)]*)\)', t):
            inni = m.group(1)
            if re.search(r'\d', inni) and not inni.lstrip().startswith('+'):
                t = t.replace(m.group(0), ' ')
    tot = 0
    for m in re.finditer(r'(\d+)\s*(?:[–-]\s*(\d+))?\s*(½)?\s*(timer|time|t|min|døgn)\b', t):
        v = float(m.group(2) or m.group(1)) + (0.5 if m.group(3) else 0)
        e = m.group(4)
        tot += v * 1440 if e == 'døgn' else v * 60 if e.startswith('t') else v
    return int(tot)


def porsjon(p):
    if not p.strip() or p.strip() in ('–', '-', '—'):
        return 0, '', 0, 1
    m = re.search(r'(\d+(?:[,.]\d+)?)', p)
    if not m:
        return 0, '', 0, 1
    b = float(m.group(1).replace(',', '.'))
    b = int(b) if b == int(b) else b
    rest = re.sub(r'^\s*[–-]\s*\d+', '', p[m.end():])
    u = ''
    for w in re.findall(r'[a-zA-ZæøåÆØÅ]+|\S', rest):
        lw = w.lower()
        if lw in ADJEKTIV:
            continue
        if lw in ENHETER:
            u = lw
        break
    if not u:
        u = 'porsjoner'
    pb = 1 if u == 'porsjoner' else 0
    if b >= 100:
        st = b / 10
    elif b >= 20:
        st = 5
    elif b <= 1.5 and u not in UDELELIG:
        st = 0.5
    else:
        st = 1
    st = int(st) if st == int(st) else st
    return b, u, pb, st


def seksjoner(body, anchors):
    ing, out, mode = [], [], None
    i = 0
    while i < len(body):
        l = body[i]
        if l.startswith('### '):
            navn = l[4:].strip()
            out.append('<h3>%s</h3>' % inline(navn, anchors))
            mode = 'ing' if navn.lower().startswith('ingredienser') else None
            i += 1
            continue
        if l.strip() in ('---', '') or re.match(r'^\*\*(Kilde|Kjøkken|Tid|Porsjoner|Gir):\*\*', l):
            i += 1
            continue
        if l.startswith('- '):
            items = []
            while i < len(body) and body[i].startswith('- '):
                items.append(body[i][2:])
                i += 1
            if mode == 'ing':
                items = [re.sub(r'\[([^\]]*)\]\([^)]+\)', r'\1', x).replace('*', '')
                         for x in items]
                ing.extend(items)
                out.append('<ul>' + ''.join(
                    '<li class="ing" data-o="%s">%s</li>' % (esc(x), inline(x, anchors))
                    for x in items) + '</ul>')
            else:
                out.append('<ul>' + ''.join(
                    '<li>%s</li>' % inline(x, anchors) for x in items) + '</ul>')
            continue
        if re.match(r'^\d+\.\s', l):
            items = []
            while i < len(body) and re.match(r'^\d+\.\s', body[i]):
                items.append(re.sub(r'^\d+\.\s', '', body[i]))
                i += 1
            out.append('<ol>' + ''.join(
                '<li>%s</li>' % inline(x, anchors) for x in items) + '</ol>')
            continue
        out.append('<p>%s</p>' % inline(l, anchors))
        i += 1
    return ing, ''.join(out)


def bygg(rid, tittel, body, typ, mac, grp, anchors, tocfelt):
    ki = kj = ti = p = ''
    hodelinjer = []
    for n, l in enumerate(body):
        if l.startswith('**Kilde:**'):
            hodelinjer.append(l)
            k = n + 1
            while k < len(body) and re.match(r'^\*\*(Kjøkken|Tid|Porsjoner|Gir):\*\*', body[k]):
                hodelinjer.append(body[k]); k += 1
            break
    for l in hodelinjer:
        if True:
            for felt, verdi in re.findall(r'\*\*([^:*]+):\*\*\s*(.*?)(?=\s*·\s*\*\*|$)', l):
                v = avkurs(verdi.strip())
                if felt == 'Kilde':
                    ki = v
                elif felt == 'Kjøkken':
                    kj = v
                elif felt == 'Tid':
                    ti = v
                elif felt in ('Porsjoner', 'Gir'):
                    p = v
    ki = ki.rstrip('.').strip()
    if not kj: kj = tocfelt.get('kj', '')
    if not ti: ti = tocfelt.get('ti', '')
    if not p:  p  = tocfelt.get('p', '')
    if p.strip() in ('–', '-', '—') or not re.search(r'\d', p): p = ''
    ing, h = seksjoner(body, anchors)
    b, u, pb, st = porsjon(p)
    r = {'id': rid, 't': tittel, 'k': typ.split('·')[0].strip(),
         'ka': [x.strip() for x in typ.split('·')],
         'kj': kj, 'ti': ti, 'p': p, 'ki': ki, 'hb': '',
         'kc': mac[0], 'pr': mac[1],
         'b': b, 'u': u, 'pb': pb, 'st': st, 'mi': tid_min(ti), 'tt': tid_total(ti),
         'ing': ing, 'h': h}
    r['nt'] = norm(tittel + ' ' + rid)
    r['ni'] = norm(' ¦ '.join(ing))
    r['nk'] = NK.get('%s|%s|%s' % (kj, grp[0], grp[1]), norm(kj))
    return r


def parse(md):
    lines = md.split('\n')
    anchors = {}
    for l in lines:
        m = re.match(r'^## ([A-ZÆØÅ]{0,2}\d+)\.\s*(.*)$', l)
        if m:
            anchors[slug(l[3:])] = m.group(1)

    slutt = next((i for i, l in enumerate(lines)
                  if l.strip() == '## Lett og proteinrik'), len(lines))
    toc, macro, grp, tocf = {}, {}, {}, {}
    g = sub = ''
    for l in lines[:slutt]:
        if l.startswith('### '):
            g = l[4:].strip(); sub = ''
        elif l.startswith('#### '):
            sub = l[5:].strip()
        else:
            c = [x.strip() for x in l.strip().strip('|').split('|')]
            if len(c) == 6 and '](#' in c[1] and c[0] != '#' and not set(c[0]) <= set('-'):
                toc.setdefault(c[0], c[2])
                tocf.setdefault(c[0], {'kj': c[3], 'ti': c[4], 'p': c[5]})
                grp.setdefault(c[0], (g, sub))
    for l in lines[slutt:]:
        c = [x.strip() for x in l.strip().strip('|').split('|')]
        if len(c) == 4 and '](#' in c[1] and c[0] != '#' and not set(c[0]) <= set('-'):
            macro[c[0]] = (c[2], c[3].replace(' g', ''))

    idx = [i for i, l in enumerate(lines)
           if l.startswith('## ') and l.strip() not in ('## Innhold', '## Lett og proteinrik')]
    recs = []
    for n, i in enumerate(idx):
        end = idx[n + 1] if n + 1 < len(idx) else len(lines)
        for j in range(i + 1, end):
            if lines[j].startswith('# '):
                end = j; break
        m = re.match(r'^## ([A-ZÆØÅ]{0,2}\d+)\.\s*(.*)$', lines[i])
        if not m:
            continue
        rid = m.group(1)
        recs.append(bygg(rid, m.group(2).strip(), lines[i + 1:end],
                         toc.get(rid, ''), macro.get(rid, ('', '')),
                         grp.get(rid, ('', '')), anchors, tocf.get(rid, {})))
    return {'ORDER': ORDER, 'PLURAL': PLURAL, 'R': recs}


if __name__ == '__main__':
    d = parse(open(sys.argv[1], encoding='utf-8').read())
    json.dump(d, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False)
    print('Bygget %d oppskrifter -> %s' % (len(d['R']), sys.argv[2]))
