import requests
import lzma
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# ======================
# CONFIGURAZIONE CANALI
# ======================

# Mappa canali da rinominare (ID Rytec -> Nome Provider)
RENAME = {
    "Nove.it": "Discovery Nove FHD",
    "Giallo.it": "Discovery Giallo FHD",
    "TV8.it": "Tv 8 FHD",
}

# Canali che richiedono versione +1
PLUS1 = {
    "Italia1.it": "Italia 1 +1 HD",
    "La7.it": "La 7 +1 HD",
    "Giallo.it": "Discovery Giallo +1 HD",
    "TV8.it": "TV 8 +1 HD",
}

# FEED Rytec originali
FEEDS = {
    "Sky": "http://www.xmltvepg.nl/rytecIT_Sky.xz",
    "Basic": "http://www.xmltvepg.nl/rytecIT_Basic.xz",
    "SportMovies": "http://www.xmltvepg.nl/rytecIT_SportMovies.xz"
}

# ======================================
# PARSING E CREAZIONE NUOVO EPG UNICO
# ======================================

root = ET.Element("tv")
seen_channels = set()
seen_programmes = set()

print("Scaricamento feed...")

for name, url in FEEDS.items():
    print(f"  → {name}")
    r = requests.get(url)
    r.raise_for_status()
    xml_data = lzma.decompress(r.content)
    feed_root = ET.fromstring(xml_data)

    # -----------------------------
    # COPIA CANALI NORMALI + RINOMINA
    # -----------------------------
    for ch in feed_root.findall("channel"):
        orig_id = ch.attrib["id"]

        # Rinomina
        if orig_id in RENAME:
            new_name = RENAME[orig_id]
            ch.set("id", new_name)
            # Reset display-names
            for d in list(ch.findall("display-name")):
                ch.remove(d)
            ET.SubElement(ch, "display-name", {"lang": "it"}).text = new_name
            ET.SubElement(ch, "display-name", {"lang": "en"}).text = new_name

        # Inserisci solo una volta
        if ch.attrib["id"] not in seen_channels:
            seen_channels.add(ch.attrib["id"])
            root.append(ch)

    # -----------------------------
    # COPIA PROGRAMMI NORMALI
    # -----------------------------
    for pr in feed_root.findall("programme"):
        key = (pr.attrib["start"], pr.attrib["stop"], pr.attrib["channel"])
        if key not in seen_programmes:
            seen_programmes.add(key)
            root.append(pr)

# ======================================
# CREAZIONE CANALI +1
# ======================================

def shift_time(x):
    # formato Rytec: "20251124005400 +0000"
    dt = datetime.strptime(x[:14], "%Y%m%d%H%M%S") + timedelta(hours=1)
    return dt.strftime("%Y%m%d%H%M%S") + x[14:]

print("\nGenerazione canali +1...")

for orig_id, provider_name in PLUS1.items():

    # CREA CANALE NUOVO
    ch = ET.SubElement(root, "channel", {"id": provider_name})
    ET.SubElement(ch, "display-name", {"lang": "it"}).text = provider_name
    ET.SubElement(ch, "display-name", {"lang": "en"}).text = provider_name

    # CERCA PROGRAMMI ORIGINALI
    for pr in root.findall("programme"):
        if pr.attrib["channel"] == orig_id or pr.attrib["channel"] == RENAME.get(orig_id, orig_id):

            new_pr = ET.Element("programme")

            new_pr.set("start", shift_time(pr.attrib["start"]))
            new_pr.set("stop", shift_time(pr.attrib["stop"]))
            new_pr.set("channel", provider_name)

            # Copia figli
            for child in pr:
                new_pr.append(child)

            root.append(new_pr)

# ======================================
# SALVA FILE
# ======================================

tree = ET.ElementTree(root)
tree.write("epg.xml", encoding="utf-8", xml_declaration=True)

with lzma.open("epg.xz", "wb") as f:
    with open("epg.xml", "rb") as infile:
        f.write(infile.read())

print("\n🎉 EPG GENERATA CON SUCCESSO!")
