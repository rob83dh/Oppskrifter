#!/usr/bin/env python3
"""Beregner kcal og protein per porsjon fra ingredienslistene.

Verdiene er typiske tall fra Matvaretabellen og USDA, avrundet.
Skriptet rapporterer hver linje det ikke klarer å tolke, slik at
ingen tung ingrediens blir borte uten at det synes.
"""
import json, re, sys, collections

# navn: (kcal/100 g, protein g/100 g)
N = {
 # --- kjøtt og fugl (rå) ---
 'kyllingfilet':(165,31),'kyllingbryst':(165,31),'kyllingindrefilet':(110,23),
 'kyllinglårfilet':(175,25),'kyllinglår':(210,24),'kyllingschnitzel':(180,28),
 'kyllingvinger':(200,27),'kyllingkjøttdeig':(150,22),'kylling':(180,28),
 'kjøttdeig':(250,18),'karbonadedeig':(150,21),'svinekjøttdeig':(260,17),
 'høyrygg':(250,26),'short ribs':(320,17),'oksehase':(200,22),'oksehale':(260,22),
 'entrecôte':(280,25),'ytrefilet':(150,22),'indrefilet':(140,22),'biff':(220,26),
 'flankbiff':(190,24),'svinekam':(200,27),'svinefilet':(145,21),'svinenakke':(240,19),
 'svinesideflesk':(500,10),'sideflesk':(500,10),'ribbe':(400,15),
 'bacon':(400,13),'pancetta':(400,20),'guanciale':(650,10),'chorizo':(450,24),
 'pepperoni':(450,20),'kalkunpepperoni':(200,17),'skinke':(110,18),
 'lammekjøttdeig':(280,17),'lammeskank':(200,25),'lammebog':(240,19),
 # --- fisk og skalldyr ---
 'laksefilet':(210,22),'laks':(210,22),'røkelaks':(180,22),'torsk':(82,18),
 'tunfisk i olje':(190,25),'tunfisk':(110,25),'reker':(85,20),'blåskjell':(86,12),
 'sjøkreps':(90,19),'røye':(150,21),'kveite':(110,21),'ansjos':(200,29),
 # --- meieri og egg ---
 'gresk yoghurt':(59,10),'tykk yoghurt':(60,5),'yoghurt':(60,4),
 'cottage cheese':(81,12),'kremfløte':(340,2),'matfløte':(190,3),'fløte':(340,2),
 'seterrømme':(230,2),'rømme':(190,3),'crème fraîche':(230,2),
 'helmelk':(63,3),'melk':(50,3),'smør':(740,1),'meierismør':(740,1),
 'parmesan':(400,36),'pecorino':(390,32),'mozzarella':(280,22),'fetaost':(260,14),
 'cheddar':(400,25),'blåmuggost':(350,21),'gruyère':(410,30),'ost':(350,25),
 'kesam':(60,11),'ricotta':(150,11),'egg':(143,13),'eggeplomme':(320,16),
 # --- tørrvare og korn ---
 'jasminris':(355,7),'basmatiris':(355,7),'sushiris':(355,7),'arborioris':(350,7),
 'carnaroliris':(350,7),'risottoris':(350,7),'havreris':(360,12),'ris':(355,7),
 'spaghetti':(360,13),'risoni':(360,13),'pasta':(360,13),'nudler':(350,11),
 'ramen-nudler':(350,11),'risnudler':(360,6),'udon':(280,7),
 'hvetemel':(340,10),'mel':(340,10),'panko':(390,13),'brødsmuler':(390,13),
 'cornflakes':(380,8),'maisstivelse':(380,0),'potetmel':(330,0),
 'brød':(265,9),'baguette':(270,9),'tortilla':(300,8),'taco':(450,7),
 'havregryn':(370,13),'proteinpulver':(380,80),
 'bønner':(330,21),'hermetiske bønner':(90,6),'kikerter':(360,19),'linser':(350,25),
 'edamame':(120,11),'tofu':(120,12),
 # --- fett, nøtter, søtt ---
 'olivenolje':(884,0),'sesamolje':(884,0),'rapsolje':(884,0),'olje':(884,0),
 'majones':(700,1),'peanøttsmør':(590,25),'kokosmelk':(180,2),'kokosfløte':(230,2),
 'sukker':(400,0),'brunt sukker':(380,0),'honning':(300,0),'sirup':(300,0),
 'peanøtter':(570,26),'cashewnøtter':(550,18),'mandler':(580,21),
 'pinjekjerner':(670,14),'sesamfrø':(570,17),'valnøtter':(650,15),
 'pistasjnøtter':(560,20),'hasselnøtter':(630,15),
 # --- grønnsaker og frukt ---
 'tomat':(18,1),'cherrytomater':(18,1),'hermetiske tomater':(20,1),
 'tomatpuré':(80,5),'passata':(30,1),
 'løk':(40,1),'rødløk':(40,1),'sjalottløk':(40,1),'salatløk':(40,1),
 'vårløk':(32,2),'purre':(61,1),'hvitløk':(150,6),
 'gulrot':(41,1),'squash':(17,1),'aubergine':(25,1),'paprika':(31,1),
 'agurk':(15,1),'salat':(15,1),'spinat':(23,3),'brokkoli':(34,3),
 'blomkål':(25,2),'kål':(25,1),'kinakål':(16,1),'pak choi':(13,2),
 'potet':(77,2),'søtpotet':(86,2),'sopp':(22,3),'sjampinjong':(22,3),
 'aromasopp':(22,3),'kantarell':(38,2),'erter':(81,5),'mais':(86,3),
 'grønne bønner':(31,2),'aspargesbønner':(31,2),'asparges':(20,2),
 'avokado':(160,2),'oliven':(145,1),'stangselleri':(16,1),'selleri':(16,1),
 'ingefær':(80,2),'chili':(40,2),'jalapeño':(29,1),'lime':(30,1),'sitron':(29,1),
 'mango':(60,1),'ananas':(50,0),'eple':(52,0),'granateple':(83,2),
 # --- væske og smakssetting ---
 'vann':(0,0),'kraft':(5,1),'buljong':(5,1),'grønnsakskraft':(5,1),
 'kyllingkraft':(5,1),'soyasaus':(60,8),'fiskesaus':(35,5),'østerssaus':(120,3),
 'misopasta':(200,12),'mirin':(230,0),'riseddik':(20,0),'eddik':(20,0),
 'hvitvin':(80,0),'rødvin':(85,0),'vin':(80,0),'sherry':(120,0),
 'gochujang':(215,5),'sriracha':(95,2),'sweet chili':(250,0),'ketchup':(100,1),
 'dijonsennep':(150,8),'sennep':(150,8),'worcestershire':(80,0),
 'pizzasaus':(40,2),'salsa':(30,1),'kapers':(25,2),'cornichon':(20,1),
 'sylteagurk':(20,1),'kimchi':(30,2),'wasabi':(290,7),'tahini':(600,17),
 'mørk sjokolade':(550,8),'sjokolade':(540,7),'hvit sjokolade':(540,6),
 'mascarpone':(430,4),'kokoskrem':(330,3),'kondensert melk':(320,8),
 'digestivekjeks':(480,7),'kjeks':(480,7),'biscoff':(500,5),
 'makaroni':(360,13),'lasagneplater':(360,13),'rigatoni':(360,13),
 'fettuccine':(360,13),'tagliatelle':(360,13),'penne':(360,13),
 'couscous':(360,12),'bulgur':(350,12),'quinoa':(370,14),'gnocchi':(170,4),
 'rabarbra':(21,1),'gelatin':(340,85),'kakaopulver':(230,20),
 'sultanarosiner':(300,3),'rosiner':(300,3),'bakepulver':(0,0),'natron':(0,0),
 'gjær':(105,12),'tørrgjær':(325,40),'salt':(0,0),'pepper':(0,0),
 'femkrydder':(0,0),'oksekjake':(200,21),'oksekjeve':(200,21),
 'flankestek':(190,24),'storfekjøtt':(220,26),'margbein':(0,0),
 'nduja':(450,15),'bønnespirer':(30,3),'enchiladasaus':(50,1),
 'wakame':(45,3),'papaya':(43,1),'cognac':(250,0),'estragon':(35,3),
 'persille':(35,3),'koriander':(35,3),'mynte':(35,3),'basilikum':(23,3),
 'dill':(35,3),'gressløk':(30,3),'vaniljesukker':(400,0),'melis':(400,0),
 'shiitake':(34,2),'salsiccia':(320,15),'kalveskank':(110,21),'kalvebog':(130,20),
 'paneer':(320,18),'pastinakk':(75,1),'nachochips':(500,7),'madeira':(120,0),
 'rødbeter':(43,2),'petits pois':(81,5),'yuzujuice':(30,0),'bbq-saus':(170,1),
 'appelsinjuice':(45,1),'bocconcini':(280,18),'kalvefond':(20,2),
 'saint agur':(350,20),'koreansk pære':(42,0),'ragù':(150,10),'golden curry':(450,6),
 'karripasta':(180,4),'fiskekraft':(5,1),'dashi':(5,1),'harissa':(180,4),
 'sumak':(0,0),'galangal':(80,2),'søtningsmiddel':(0,0),'bein':(0,0),
 'buljongterning':(0,0),'sriracha-majones':(600,1),'lettmajones':(300,1),
}

# gram per stykk
STK = {
 'egg':55,'eggeplomme':17,'hvitløksfedd':4,'hvitløkfedd':4,'sjalottløk':30,
 'løk':110,'rødløk':110,'salatløk':130,'vårløk':15,'gulrot':70,'tomat':110,
 'cherrytomater':10,'paprika':150,'squash':250,'aubergine':300,'potet':120,
 'agurk':300,'avokado':150,'lime':60,'sitron':90,'chili':10,'jalapeño':15,
 'thaichili':2,'purre':150,'stangselleri':50,'kyllingfilet':200,'kyllingbryst':200,
 'kyllinglårfilet':100,'kyllinglår':155,'kyllingschnitzel':150,'laksefilet':125,
 'brød':35,'baguette':250,'tortilla':45,'skalotteløk':30,'mango':200,
 'kvister':2,'kvist':2,'bunt':30,'stilk':50,'boks':400,'pakke':400,
 'mais':180,'pak choi':100,'svinesideflesk':2500,
}
# egne standardvekter der oppskriften bruker «porsjoner» e.l.
SPESIAL = {
 'ramen-nudler':120, 'porsjoner kokt ris':200, 'porsjoner ris':200,
}

# gram per desiliter – volum til vekt avhenger av varen
TETTHET = {
 'hvetemel':60,'mel':60,'maisstivelse':60,'potetmel':70,'panko':45,'brødsmuler':45,
 'cornflakes':30,'havregryn':40,'proteinpulver':40,
 'parmesan':40,'pecorino':40,'mozzarella':40,'cheddar':40,'ost':40,
 'jasminris':85,'basmatiris':85,'sushiris':88,'arborioris':88,'carnaroliris':88,
 'risottoris':88,'havreris':85,'ris':85,'pasta':50,'nudler':50,
 'sukker':85,'brunt sukker':80,'honning':140,'sirup':140,
 'peanøtter':60,'cashewnøtter':55,'mandler':55,'pinjekjerner':60,'sesamfrø':60,
 'pistasjnøtter':55,'hasselnøtter':55,'valnøtter':50,
 'olivenolje':92,'sesamolje':92,'rapsolje':92,'olje':92,'majones':95,
 'tomatpuré':110,'soyasaus':105,'fiskesaus':105,'misopasta':120,
 'cottage cheese':95,'gresk yoghurt':100,'kokosmelk':100,
 'bønner':85,'kikerter':85,'linser':85,'edamame':80,'mais':80,
 'oliven':70,'kapers':60,'cornichon':70,'sylteagurk':70,'kimchi':70,
 'basilikum':20,'koriander':20,'persille':20,'dill':20,'salat':25,'spinat':25,
 'vårløk':40,'sopp':35,'sjampinjong':35,
}

# gram per skive – avhenger sterkt av varen
SKIVE = {'pepperoni':3,'kalkunpepperoni':3,'chorizo':5,'bacon':15,'skinke':15,
         'brød':35,'baguette':30,'ost':20,'ingefær':2,'tomat':15,'løk':10,
         'sitron':8,'lime':6,'agurk':8}

# gram per boks/pakke – varierer sterkt
BOKS = {'tunfisk':150,'ansjos':50,'tomat':400,'hermetiske tomater':400,
        'bønner':400,'kikerter':400,'linser':400,'kokosmelk':400,'mais':300,
        'tofu':400,'bacon':140,'pepperoni':100}
POTTE = 20

MÅL = {'g':1,'gram':1,'kg':1000,'ml':1,'dl':100,'l':1000,'ss':15,'ts':5,
       'kopp':240,'cup':240,'klype':0.5,'knivspiss':0.3,'never':30,'neve':30,
       'håndfull':30,'skive':25,'skiver':25,'boks':400,'bokser':400,
       'pakke':400,'pakker':400,'porsjon':150,'porsjoner':150,'stk':50}
BRØK = {'½':0.5,'¼':0.25,'¾':0.75,'⅓':1/3,'⅔':2/3,'⅛':0.125,'⅕':0.2,'⅖':0.4}


def tall(s):
    s = s.strip()
    for b, v in BRØK.items():
        if s.startswith(b):
            return v
        if b in s:
            m = re.match(r'^(\d+)' + re.escape(b), s)
            if m:
                return float(m.group(1)) + v
    m = re.match(r'^(\d+(?:[,.]\d+)?)\s*[–-]\s*(\d+(?:[,.]\d+)?)', s)
    if m:
        return (float(m.group(1).replace(',', '.')) + float(m.group(2).replace(',', '.'))) / 2
    m = re.match(r'^(\d+(?:[,.]\d+)?)', s)
    return float(m.group(1).replace(',', '.')) if m else None


# flertall og skrivevarianter -> oppslagsord
SYNONYM = [('gulrøtter','gulrot'),('kyllingschnitzler','kyllingschnitzel'),
           ('kyllingfileter','kyllingfilet'),('kyllingbryster','kyllingbryst'),
           ('laksefileter','laksefilet'),('maiskolber','mais'),('tomater','tomat'),
           ('poteter','potet'),('løker','løk'),('paprikaer','paprika'),
           ('agurker','agurk'),('limer','lime'),('sitroner','sitron'),
           ('avokadoer','avokado'),('bok choy','pak choi'),('ketsjup','ketchup'),
           ('farin','sukker'),('karriblanding','karripasta'),('sake','vin'),
           ('squashen','squash'),('eggene','egg'),('nudlene','nudler')]

HERMETISK = {'bønner':(90,6),'kikerter':(120,7),'linser':(100,8),
             'mais':(86,3),'tomat':(20,1)}

def slå_opp(linje):
    """Finner varen. Parentesen kan inneholde både alternativer som skal
    ignoreres – «selvhevende mel (eller hvetemel + bakepulver)» er mel, ikke
    bakepulver – og selve identifikasjonen: «blandet sjømat (reker, kamskjell)».
    Derfor leses teksten utenfor parentes først, og hele linjen bare hvis det
    ikke gir treff."""
    for tekst in (re.sub(r'\([^)]*\)', ' ', linje.lower()), linje.lower()):
        for a, b in SYNONYM:
            tekst = tekst.replace(a, b)
        beste = None
        for navn in N:
            if navn in tekst and (beste is None or len(navn) > len(beste)):
                beste = navn
        if beste:
            return beste
    return None


def vekt(linje):
    """Returnerer gram, eller None hvis mengden ikke lar seg lese."""
    t = linje.lower().replace('\u2013', '-')
    for a, b in SYNONYM:
        t = t.replace(a, b)
    # «2 laksefileter, ca. 225 g hver» – vekt per stykk, ganges med antallet
    m = re.search(r',\s*(?:ca\.\s*)?(\d+(?:[,.]\d+)?)\s*(g|kg)\b[^,]*\b(hver|per stk|stykket)', t)
    if m:
        n0 = tall(re.sub(r'^\s*(?:ca\.|omtrent|rundt)\s*', '', t)) or 1
        return n0 * float(m.group(1).replace(',', '.')) * MÅL[m.group(2)]
    # eksplisitt vekt i parentes eller etter tankestrek
    m = re.search(r'(?:—|–|-|\()\s*(?:ca\.\s*)?(\d+(?:[,.]\d+)?)\s*(g|kg|dl|ml)\b', t)
    if m:
        return float(m.group(1).replace(',', '.')) * MÅL[m.group(2)]
    t2 = re.sub(r'^\s*(?:ca\.|omtrent|rundt)\s*', '', t)
    n = tall(t2)
    if n is None:
        return None
    rest = re.sub(r'^[^a-zæøå]*', '', t2)
    m = re.match(r'([a-zæøå]+)', rest)
    enh = m.group(1) if m else ''
    if enh in ('boks', 'bokser', 'pakke', 'pakker'):
        # «à 150 g» eller «à 400 g» oppgir vekten direkte
        m2 = re.search(r'à\s*(\d+(?:[,.]\d+)?)\s*(g|ml|dl)\b', t)
        if m2:
            return n * float(m2.group(1).replace(',', '.')) * MÅL[m2.group(2)]
        for k, v in BOKS.items():
            if k in t:
                return n * v
        return n * 400
    if enh in ('potte', 'potter'):
        return n * POTTE
    if enh in ('skive', 'skiver'):
        navn = slå_opp(linje)
        for k, v in SKIVE.items():
            if k in t:
                return n * v
        return n * (SKIVE.get(navn) or 25)
    if enh in MÅL:
        g = n * MÅL[enh]
        if enh in ('dl','l','kopp','cup','ml'):      # volum – juster for tetthet
            navn = slå_opp(linje)
            if navn in TETTHET:
                g = g / 100 * TETTHET[navn]
        return g
    for k, v in SPESIAL.items():
        if k in t:
            return n * v
    beste, lng = None, 0
    for k, v in STK.items():
        if k in t and len(k) > lng:
            beste, lng = v, len(k)
    return n * beste if beste else None


def porsjoner(r):
    p = r['p']
    m = re.search(r'(\d+)\s*[–-]\s*(\d+)', p)
    if m:
        return (int(m.group(1)) + int(m.group(2))) / 2
    m = re.match(r'\s*(\d+)', p)
    return float(m.group(1)) if m else None


def beregn(r):
    kcal = prot = 0.0
    mangler = []
    for l in r['ing']:
        if not re.search(r'\d|\bsalt\b|pepper|krydder', l.lower()):
            continue
        g = vekt(l)
        n = slå_opp(l)
        if g is None or n is None:
            if re.search(r'\d', l):
                mangler.append(l)
            continue
        v = N[n]
        if n in HERMETISK and re.search(r'boks|hermetisk|avrent|avskylt', l.lower()):
            v = HERMETISK[n]
        kcal += g / 100 * v[0]
        prot += g / 100 * v[1]
    return kcal, prot, mangler


if __name__ == '__main__':
    d = json.load(open(sys.argv[1], encoding='utf-8'))
    ut = []
    for r in d['R']:
        if not r['kc']:
            continue
        p = porsjoner(r)
        k, pr, m = beregn(r)
        ut.append((r, p, k, pr, m))
    if '--mangler' in sys.argv:
        for r, p, k, pr, m in ut:
            if m:
                print(f"\n{r['id']} {r['t'][:44]}  ({len(m)} uleste)")
                for x in m:
                    print('    ', x[:76])
    else:
        print(f"{'id':6}{'kcal opp':>9}{'kcal ny':>9}{'prot opp':>10}{'prot ny':>9}  ulest")
        for r, p, k, pr, m in ut:
            if not p:
                print(f"{r['id']:6}  – porsjoner ikke lesbart: {r['p'][:30]}")
                continue
            print(f"{r['id']:6}{int(r['kc']):>9}{k/p:>9.0f}{float(r['pr']):>10.1f}{pr/p:>9.1f}  {len(m)}")
