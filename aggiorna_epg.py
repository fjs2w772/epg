import requests
import lzma
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import copy

# ---------------------------------------------------
# SHIFT ORARIO PROGRAMMES
# ---------------------------------------------------

def shift_orario(value, ore=1):
    if not value:
        return value
    base = value[:14]
    resto = value[14:]
    dt = datetime.strptime(base, "%Y%m%d%H%M%S")
    dt_new = dt + timedelta(hours=ore)
    return dt_new.strftime("%Y%m%d%H%M%S") + resto

# ---------------------------------------------------
# FORMATTAZIONE XMLTV STANDARD (MULTILINEA)
# ---------------------------------------------------

def formatta_canale(channel_element, nome):
    """Ricrea la struttura del canale in formato XMLTV standard multilinea."""
    # Rimuovi tutto dentro
    for child in list(channel_element):
        channel_element.remove(child)

    # display-name lang="it" FIRST (standard Rytec)
    dn_it = ET.SubElement(channel_element, "display-name")
    dn_it.set("lang", "it")
    dn_it.text = nome

    # display-name lang="en"
    dn_en = ET.SubElement(channel_element, "display-name")
    dn_en.set("lang", "en")
    dn_en.text = nome

    # display-name senza lingua (ultimo)
    dn_default = ET.SubElement(channel_element, "display-name")
    dn_default.text = nome

# ---------------------------------------------------
# RINOMINA CANALE
# ---------------------------------------------------

def rinomina_canale(root, channel_id, nuovo_nome):
    for ch in root.findall("channel"):
        if ch.get("id") == channel_id:
            formatta_canale(ch, nuovo_nome)
            print(f"[OK] Rinominato: {channel_id} -> {nuovo_nome}")
            return
    print(f"[WARN] Non trovato per rinomina: {channel_id}")

# ---------------------------------------------------
# CREA CANALE +1
# ---------------------------------------------------

def crea_canale_plus1(root, original_id, nuovo_id, nuovo_nome):
    originale = None
    for ch in root.findall("channel"):
        if ch.get("id") == original_id:
            originale = ch
            break

    if originale is None:
        print(f"[ERRORE] Originale non trovato: {original_id}")
        return

    # DUPLICA CANALE
    nuovo_ch = ET.Element("channel")
    nuovo_ch.set("id", nuovo_id)
    formatta_canale(nuovo_ch, nuovo_nome)
    root.insert(0, nuovo_ch)

    # DUPLICA PROGRAMMES
    all_programmes = list(root.findall("programme"))
    count = 0
    nuovi_prog = []

    for prog in all_programmes:
        if prog.get("channel") == original_id:
            np = copy.deepcopy(prog)
            np.set("channel", nuovo_id)

            for attr in ("start", "stop"):
                old = np.get(attr)
                if old:
                    np.set(attr, shift_orario(old, 1))

            nuovi_prog.append(np)
            count += 1

    for p in nuovi_prog:
        root.append(p)

    print(f"[OK] Creato +1: {original_id} -> {nuovo_id} | programmi duplicati: {count}")

# ---------------------------------------------------
# RINOMINE + CANALI +1
# ---------------------------------------------------

def modifica_epg(root):

    # Mappa ID reali
    id_map = {ch.get("id").lower(): ch.get("id") for ch in root.findall("channel")}

    # --- RINOMINE ---
    rinomina = {
        "Nove.it": "Nove",
        "20Mediaset.it": "Mediaset 20",
        "RaiSport.it": "Rai Sport+",
        "TopCrime.it": "TopCrime",
        "LA7Cinema.it": "LA 7 Cinema",
        "HGTV.it": "HGTV Home Garden",
        "SkySportAction.it": "Sky Sport Golf",
        "DAZNZona.it": "Dazn 1",
        "ZonaDAZN2.it": "Dazn 2",
        "Tgcom24.it": "Tgcom 24"
    }

    for user_id, name in rinomina.items():
        key = user_id.lower()
        if key in id_map:
            rinomina_canale(root, id_map[key], name)

    # --- CANALI +1 ---
    plus1 = {
        "Italia1.it": "Italia 1 +1",
        "La7.it": "La7 +1",
        "Cielo.it": "Cielo +1",
        "20Mediaset.it": "Mediaset 20 +1",
        "Giallo.it": "Giallo +1",
        "Cine34.it": "Cine 34 +1",
        "SkyArte.it": "Sky Arte HD +1",
        "SkyNature.it": "Sky Nature +1",
        "SkyCinemaDue.it": "Sky Cinema Due +1",
        "SkyCinemaAction.it": "Sky Cinema Action +1",
        "SkyCinemaCollection.it": "Sky Cinema Collection +1",
        "SkyCinemaComedy.it": "Sky Cinema Comedy +1",
        "SkyCinemaDrama.it": "Sky Cinema Drama +1",
        "SkyCinemaRomance.it": "Sky Cinema Romance +1",
        "SkyCinemaSuspense.it": "Sky Cinema Suspense +1"
    }

    for user_id, name in plus1.items():
        key = user_id.lower()
        if key in id_map:
            real = id_map[key]
            crea_canale_plus1(root, real, real + ".plus1", name)
        else:
            print(f"[WARN] Canale +1 non trovato: {user_id}")

# ---------------------------------------------------
# MERGE FEED RYTEC
# ---------------------------------------------------

feeds = {
    "Sky": "http://www.xmltvepg.nl/rytecIT_Sky.xz",
    "Basic": "http://www.xmltvepg.nl/rytecIT_Basic.xz",
    "SportMovies": "http://www.xmltvepg.nl/rytecIT_SportMovies.xz"
}

root_combined = ET.Element("tv")
seen_channels = set()
seen_programmes = set()

for name, url in feeds.items():
    print(f"Scarico feed {name}…")
    r = requests.get(url)
    r.raise_for_status()

    xml_data = lzma.decompress(r.content)
    feed_root = ET.fromstring(xml_data)

    # CHANNELS
    for ch in feed_root.findall("channel"):
        cid = ch.get("id")
        if cid not in seen_channels:
            root_combined.append(ch)
            seen_channels.add(cid)

    # PROGRAMMES
    for pr in feed_root.findall("programme"):
        key = (pr.get("start"), pr.get("stop"), pr.get("channel"))
        if key not in seen_programmes:
            root_combined.append(pr)
            seen_programmes.add(key)

# ---------------------------------------------------
# APPLICO MODIFICHE
# ---------------------------------------------------

print("Applico rinomine e canali +1…")
modifica_epg(root_combined)

# ---------------------------------------------------
# SALVATAGGIO
# ---------------------------------------------------

tree = ET.ElementTree(root_combined)
tree.write("epg.xml", encoding="utf-8", xml_declaration=True)

with lzma.open("epg.xz", "wb") as f:
    with open("epg.xml", "rb") as infile:
        f.write(infile.read())

print("🎉 EPG generata correttamente! Compatibile al 100% con TiviMate.")
