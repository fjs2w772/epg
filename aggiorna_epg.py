import requests
import lzma
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import copy
import xml.dom.minidom as minidom

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
# FORMATTAZIONE XMLTV MULTILINEA
# ---------------------------------------------------

def formatta_canale(channel_element, nome):
    """Ricrea struttura del canale in formato XMLTV standard (multilinea)."""

    # Rimuovi nodi esistenti
    for child in list(channel_element):
        channel_element.remove(child)

    # display-name lang="it" → primo (standard Rytec)
    dn_it = ET.SubElement(channel_element, "display-name")
    dn_it.set("lang", "it")
    dn_it.text = nome

    # display-name lang="en"
    dn_en = ET.SubElement(channel_element, "display-name")
    dn_en.set("lang", "en")
    dn_en.text = nome

    # display-name default
    dn_default = ET.SubElement(channel_element, "display-name")
    dn_default.text = nome

# ---------------------------------------------------
# RINOMINA CANALE
# ---------------------------------------------------

def rinomina_canale(root, channel_id, nuovo_nome):
    for ch in root.findall("channel"):
        if ch.get("id") == channel_id:
            formatta_canale(ch, nuovo_nome)
            print(f"[OK] Rinominato: {channel_id} → {nuovo_nome}")
            return
    print(f"[WARN] Canale da rinominare non trovato: {channel_id}")

# ---------------------------------------------------
# CREA CANALE +1
# ---------------------------------------------------

def crea_canale_plus1(root, original_id, nuovo_id, nuovo_nome):

    # Trova canale originale
    originale = None
    for ch in root.findall("channel"):
        if ch.get("id") == original_id:
            originale = ch
            break

    if originale is None:
        print(f"[ERRORE] Canale originale non trovato: {original_id}")
        return

    # Crea nuovo channel da zero
    nuovo_ch = ET.Element("channel")
    nuovo_ch.set("id", nuovo_id)
    formatta_canale(nuovo_ch, nuovo_nome)
    root.insert(0, nuovo_ch)

    # Duplica programmes
    all_programmes = list(root.findall("programme"))
    count = 0
    nuovi_prog = []

    for prog in all_programmes:
        if prog.get("channel") == original_id:
            np = copy.deepcopy(prog)
            np.set("channel", nuovo_id)

            # Shift orari
            for attr in ("start", "stop"):
                oldval = np.get(attr)
                if oldval:
                    np.set(attr, shift_orario(oldval, 1))

            nuovi_prog.append(np)
            count += 1

    # Append finali
    for p in nuovi_prog:
        root.append(p)

    print(f"[OK] Creato +1: {original_id} → {nuovo_id}  |  Programmi duplicati: {count}")

# ---------------------------------------------------
# MODIFICHE FINALI
# ---------------------------------------------------

def modifica_epg(root):

    # Mappa ID reali presenti nell'EPG
    id_map = {ch.get("id").lower(): ch.get("id") for ch in root.findall("channel")}

    # --- RINOMINE ---
    rinomina = {
        "Nove.it": "Nove",
        "20mediaset.it": "Mediaset 20",
        "raisport.it": "Rai Sport+",
        "topcrime.it": "TopCrime",
        "la7cinema.it": "LA 7 Cinema",
        "hgtv.it": "HGTV Home Garden",
        "skysportaction.it": "Sky Sport Golf",
        "daznzona.it": "Dazn 1",
        "zonadazn2.it": "Dazn 2",
        "tgcom24.it": "Tgcom 24"
    }

    for user_id, newname in rinomina.items():
        key = user_id.lower()
        if key in id_map:
            rinomina_canale(root, id_map[key], newname)
        else:
            print(f"[WARN] Non trovato per rinomina: {user_id}")

    # --- +1 ---
    plus1 = {
        "italia1.it": "Italia 1 +1",
        "la7.it": "La7 +1",
        "cielo.it": "Cielo +1",
        "20mediaset.it": "Mediaset 20 +1",
        "giallo.it": "Giallo +1",
        "cine34.it": "Cine 34 +1",
        "skyarte.it": "Sky Arte HD +1",
        "skynature.it": "Sky Nature +1",
        "skycinemadue.it": "Sky Cinema Due +1",
        "skycinemaaction.it": "Sky Cinema Action +1",
        "skycinemacollection.it": "Sky Cinema Collection +1",
        "skycinemacomedy.it": "Sky Cinema Comedy +1",
        "skycinemadrama.it": "Sky Cinema Drama +1",
        "skycinemaromance.it": "Sky Cinema Romance +1",
        "skycinemasuspense.it": "Sky Cinema Suspense +1"
    }

    for user_id, newname in plus1.items():
        key = user_id.lower()
        if key in id_map:
            real = id_map[key]
            crea_canale_plus1(root, real, real + ".plus1", newname)
        else:
            print(f"[WARN] Non trovato per +1: {user_id}")

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
    print(f"Scarico feed {name}...")
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
# APPLICO LE MODIFICHE
# ---------------------------------------------------

print("Applico rinomine e creazione canali +1...")
modifica_epg(root_combined)

# ---------------------------------------------------
# SALVATAGGIO PRETTY PRINT
# ---------------------------------------------------

xml_bytes = ET.tostring(root_combined, encoding="utf-8")
xml_pretty = minidom.parseString(xml_bytes).toprettyxml(indent="  ")

with open("epg.xml", "w", encoding="utf-8") as f:
    f.write(xml_pretty)

# Creazione compressa
with lzma.open("epg.xz", "wb") as f:
    f.write(xml_pretty.encode("utf-8"))

print("🎉 EPG generata con successo! XML formattato correttamente per TiviMate.")
