import requests
import lzma
import xml.etree.ElementTree as ET
import copy

# ----------------------------
# FEED RYTEC ORIGINALI
# ----------------------------
feeds = {
    "Sky": "http://www.xmltvepg.nl/rytecIT_Sky.xz",
    "Basic": "http://www.xmltvepg.nl/rytecIT_Basic.xz",
    "SportMovies": "http://www.xmltvepg.nl/rytecIT_SportMovies.xz",
}

# ----------------------------
# CANALI MINI-EPG (OPZIONE B)
# id Rytec -> nome come lo vuoi vedere in TiviMate
# ----------------------------
mini_channels_display = {
    # NON si associano
    "Nove.it": "Discovery Nove",
    "Italia1.it.plus1": "Italia 1 +1",
    "La7.it.plus1": "La 7 +1",

    # +1 problematici
    "Cielo.it.plus1": "Cielo +1",
    "Giallo.it.plus1": "Discovery Giallo +1",
    "Cine34.it.plus1": "Cine 34 +1",
    "RealTimePlus1.it": "Real Time +1",
    "FoodNetwork.it.plus1": "Food Network +1",
    "TwentySeven.it.plus1": "27 Twentyseven +1",
    "DMAXPlus1.it": "Discovery Dmax +1",
    "Rai5.it.plus1": "Rai 5 +1",
    "Rai4.it.plus1": "Rai 4 +1",
}

mini_ids = set(mini_channels_display.keys())

# ----------------------------
# STRUTTURA XML DI USCITA
# ----------------------------
root = ET.Element("tv")

# li accumuliamo separati così siamo sicuri:
# prima tutti i <channel>, poi tutti i <programme>
channels_out = {}
programmes_out = []

# ----------------------------
# SCARICO E FILTRO I FEED
# ----------------------------
for name, url in feeds.items():
    print(f"Scarico feed {name} da {url}...")
    resp = requests.get(url)
    resp.raise_for_status()
    xml_data = lzma.decompress(resp.content)

    feed_root = ET.fromstring(xml_data)

    # --- CHANNELS ---
    for ch in feed_root.findall("channel"):
        cid = ch.attrib.get("id")
        if cid in mini_ids and cid not in channels_out:
            # costruiamo un channel "pulito", stile file che ti funziona
            ch_out = ET.Element("channel", id=cid)

            # display-name principale uguale a come ti torna comodo in TiviMate
            dn = ET.SubElement(ch_out, "display-name", lang="it")
            dn.text = mini_channels_display[cid]

            channels_out[cid] = ch_out

    # --- PROGRAMMES ---
    for pr in feed_root.findall("programme"):
        cid = pr.attrib.get("channel")
        if cid in mini_ids:
            # clona il programme dal feed originale
            pr_copy = copy.deepcopy(pr)
            programmes_out.append(pr_copy)

# ----------------------------
# COSTRUZIONE FINALE DELL'ALBERO
# ----------------------------

# 1) tutti i channel (ordinati per id, solo per avere ordine stabile)
for cid in sorted(channels_out.keys()):
    root.append(channels_out[cid])

# 2) poi tutti i programme
for pr in programmes_out:
    root.append(pr)

tree = ET.ElementTree(root)

# ----------------------------
# SCRIVI mini_epg.xml
# ----------------------------
tree.write("mini_epg.xml", encoding="utf-8", xml_declaration=True)

# ----------------------------
# CREA mini_epg.xz (opzionale ma utile)
# ----------------------------
with lzma.open("mini_epg.xz", "wb") as f:
    with open("mini_epg.xml", "rb") as infile:
        f.write(infile.read())

print("✅ MINI EPG generata (mini_epg.xml + mini_epg.xz) con i 12 canali selezionati.")
