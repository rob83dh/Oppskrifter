#!/usr/bin/env python3
"""Henter alt som trengs for å skrive en oppskrift fra en video.

Kjøres fra repo-roten:
    python3 verktoy/hent_video.py <lenke til TikTok/Instagram/YouTube>
    python3 verktoy/hent_video.py --cookies chrome <lenke>   (Instagram krever ofte innlogging)

Lager mappa .video/<id>/ (ignoreres av git) med:
    oppsummering.md   kilde, dato, likes, videotekst og hele transkripsjonen
    ark-01.jpg …      kontaktark med 9 skjermbilder hver, i tidsrekkefølge
    bilder/           enkeltbildene i full størrelse, navngitt etter sekund

Krever:  brew install yt-dlp ffmpeg whisper-cpp
Whisper-modellen (ca. 1,6 GB) lastes ned automatisk første gang.
"""
import glob, json, os, re, shutil, subprocess, sys, urllib.request

HER = os.path.dirname(os.path.abspath(__file__))
ROT = os.path.dirname(HER)
MODELL = os.path.expanduser('~/.cache/whisper/ggml-large-v3-turbo.bin')
MODELL_URL = 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin'
MAKS_BILDER = 63          # 7 kontaktark à 9
MND = ['januar', 'februar', 'mars', 'april', 'mai', 'juni', 'juli', 'august',
       'september', 'oktober', 'november', 'desember']


def kjør(*cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        sys.exit('Feilet: %s\n%s' % (' '.join(cmd[:3]), r.stderr[-1500:]))
    return r.stdout


def krev(prog, pakke):
    if not shutil.which(prog):
        sys.exit('Mangler %s. Installer med:  brew install %s' % (prog, pakke))


def whisper_prog():
    for p in ('whisper-cli', 'whisper-cpp'):
        if shutil.which(p):
            return p
    return None


def norsk_dato(d):
    if not d or len(d) != 8:
        return ''
    return '%d. %s %s' % (int(d[6:]), MND[int(d[4:6]) - 1], d[:4])


def tid(s):
    s = int(s)
    return '%d:%02d' % (s // 60, s % 60)


COOKIES = []   # settes med --cookies chrome|safari|firefox


def hent_metadata(url, mappe):
    info = json.loads(kjør('yt-dlp', '-J', '--no-warnings', *COOKIES, url))
    kjør('yt-dlp', '--no-warnings', *COOKIES, '-f', 'best[ext=mp4]/best', '-o',
         os.path.join(mappe, 'video.%(ext)s'), url)
    filer = glob.glob(os.path.join(mappe, 'video.*'))
    if not filer:
        sys.exit('Fant ikke nedlastet video.')
    return info, filer[0]


def transkriber(video, mappe):
    prog = whisper_prog()
    if not prog:
        return None, 'whisper-cpp er ikke installert (brew install whisper-cpp) – ingen transkripsjon.'
    if not os.path.exists(MODELL):
        os.makedirs(os.path.dirname(MODELL), exist_ok=True)
        print('Laster ned Whisper-modellen (ca. 1,6 GB, bare første gang)…')
        urllib.request.urlretrieve(MODELL_URL, MODELL + '.del')
        os.rename(MODELL + '.del', MODELL)
    wav = os.path.join(mappe, 'lyd.wav')
    kjør('ffmpeg', '-y', '-loglevel', 'error', '-i', video, '-vn', '-ar', '16000', '-ac', '1',
         '-c:a', 'pcm_s16le', wav)
    ut = os.path.join(mappe, 'tale')
    kjør(prog, '-m', MODELL, '-f', wav, '-l', 'auto', '-osrt', '-of', ut, '-np')
    os.remove(wav)
    srt = open(ut + '.srt', encoding='utf-8').read()
    linjer = []
    for blokk in re.split(r'\n\s*\n', srt.strip()):
        deler = blokk.split('\n')
        if len(deler) >= 3:
            m = re.match(r'(\d+):(\d+):(\d+)', deler[1])
            sek = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) if m else 0
            tekst = re.sub(r'\s+', ' ', ' '.join(deler[2:])).strip()
            if tekst and not re.fullmatch(r'\[.*\]|\(.*\)', tekst):   # [Musikk], (applaus)
                linjer.append('[%s] %s' % (tid(sek), tekst))
    return linjer, None


def skjermbilder(video, mappe):
    """Ett bilde i sekundet, like bilder fjernes, navngitt etter sekund."""
    b = os.path.join(mappe, 'bilder')
    os.makedirs(b, exist_ok=True)
    kjør('ffmpeg', '-y', '-loglevel', 'error', '-i', video,
         '-vf', 'fps=1,mpdecimate=hi=64*24:lo=64*12:frac=0.33,scale=720:-2',
         '-fps_mode', 'vfr', '-frame_pts', '1', '-q:v', '3', os.path.join(b, '%05d.jpg'))
    bilder = sorted(glob.glob(os.path.join(b, '*.jpg')))
    if len(bilder) > MAKS_BILDER:   # jevnt utvalg hvis videoen er lang
        steg = len(bilder) / MAKS_BILDER
        behold = {bilder[int(i * steg)] for i in range(MAKS_BILDER)}
        for f in bilder:
            if f not in behold:
                os.remove(f)
        bilder = sorted(behold)

    # Kontaktark: 3x3 i tidsrekkefølge, så Claude kan se mange bilder på én gang
    ark = []
    tmp = os.path.join(mappe, '_tmp')
    for n in range(0, len(bilder), 9):
        gruppe = bilder[n:n + 9]
        os.makedirs(tmp, exist_ok=True)
        for i, f in enumerate(gruppe):
            shutil.copy(f, os.path.join(tmp, '%02d.jpg' % i))
        navn = 'ark-%02d.jpg' % (len(ark) + 1)
        kjør('ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(tmp, '%02d.jpg'),
             '-vf', 'scale=400:-2,tile=3x3:padding=6:color=white', '-frames:v', '1',
             '-q:v', '3', os.path.join(mappe, navn))
        shutil.rmtree(tmp)
        sek = [tid(int(os.path.basename(f)[:5])) for f in gruppe]
        ark.append((navn, sek))
    return ark


def main():
    args = sys.argv[1:]
    if '--cookies' in args:
        i = args.index('--cookies')
        COOKIES.extend(['--cookies-from-browser', args[i + 1]])
        del args[i:i + 2]
    if len(args) != 1:
        sys.exit(__doc__)
    url = args[0].split('?')[0] if 'tiktok.com' in args[0] else args[0]
    krev('yt-dlp', 'yt-dlp')
    krev('ffmpeg', 'ffmpeg')

    print('Henter video og metadata…')
    tmp = os.path.join(ROT, '.video', '_ny')
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    info, video = hent_metadata(url, tmp)
    mappe = os.path.join(ROT, '.video', re.sub(r'[^\w-]', '', str(info.get('id', 'ukjent'))))
    shutil.rmtree(mappe, ignore_errors=True)
    os.rename(tmp, mappe)
    video = os.path.join(mappe, os.path.basename(video))

    print('Transkriberer tale…')
    tale, merknad = transkriber(video, mappe)
    print('Trekker ut skjermbilder…')
    ark = skjermbilder(video, mappe)

    konto = info.get('uploader_id') or info.get('uploader') or info.get('channel') or ''
    o = ['# Videokilde', '',
         '- **Lenke:** %s' % (info.get('webpage_url') or url),
         '- **Konto:** @%s (%s)' % (konto.lstrip('@'), info.get('extractor_key', '')),
         '- **Publisert:** %s' % (norsk_dato(info.get('upload_date')) or 'ukjent'),
         '- **Likes:** %s' % (info.get('like_count') if info.get('like_count') is not None else 'ukjent'),
         '- **Varighet:** %s' % tid(info.get('duration') or 0), '',
         '## Tekst under videoen', '', (info.get('description') or info.get('title') or '(ingen)').strip(), '',
         '## Tale (transkribert, tidspunkt i video)', '']
    o += tale if tale else ['(ingen tale funnet)' if tale is not None else merknad]
    o += ['', '## Kontaktark', '',
          'Hvert ark har 9 bilder, lest venstre→høyre, ovenfra og ned. '
          'Enkeltbilder i full størrelse ligger i bilder/, navngitt etter sekund.', '']
    o += ['- %s: %s' % (n, ', '.join(s)) for n, s in ark]
    open(os.path.join(mappe, 'oppsummering.md'), 'w', encoding='utf-8').write('\n'.join(o) + '\n')
    os.remove(video)

    print('\nFerdig: %s' % os.path.relpath(mappe, ROT))
    print('  oppsummering.md, %d kontaktark, %d tale-linjer'
          % (len(ark), len(tale or [])))


if __name__ == '__main__':
    main()
