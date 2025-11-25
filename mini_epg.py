import requests
import lzma
import xml.etree.ElementTree as ET
import copy

# ------------------------------------------
#  FEED RYTEC ORIGINALI
# ------------------------------------------
feeds = {
    "Sky": "http://www.xmltvepg.nl/rytecIT_Sky.xz",
    "Basic": "http://www.xmltvepg.nl/rytecIT_Basic.xz",
    "SportMovies": "http://www.xmltvepg.nl/rytecIT_SportMovies.xz",
}

# ------------------------------------------
#  CANALI DELLA MINI EPG (ID RYTEC -> NOME PROVIDER)
# ------------------------------------------
mini_channels_display = {
    # NON si associavano
    "Italia1.it.plus1": "Italia 1 + 1",
    "La7.it.plus1": "La 7 + 1",

    # +1 con problemi di guida / shift
    "Cielo.it.plus1": "Cielo +1",
    "Giallo.it.plus1": "Giallo +1",
    "Cine34.it.plus1": "Cine 34 +1",
    "RealTimePlus1.it": "Real Time +1",
    "FoodNetwork.it.plus1": "Food Network +1",
    "TwentySeven.it.plus1": "27 Twentyseven +1",
    "DMAXPlus1.it": "Discovery Dmax +1",
    "Rai5.it.plus1": "Rai 5 +1",
    "Rai4.it.plus1": "Rai 4 +1",
}

mini_ids = set(mini_channels_display.keys())

# ------------------------------------------
#  STRUTTURA XML DI USCITA
# ------------------------------------------
root = ET.Element("tv")

# li teniamo separati: prima channels, poi programmes
channels_out = {}
programmes_out = []

print("🔍 Scarico feed Rytec e filtro solo i 12 canali della mini EPG...")

# ------------------------------------------
#  SCARICO E PROCESSO I FEED
# ------------------------------------------
for name, url in feeds.items():
    print(f"   → Scarico feed {name} da {url}")
    resp = requests.get(url)
    resp.raise_for_status()
    xml_data = lzma.decompress(resp.content)
    feed_root = ET.fromstring(xml_data)

    # --- CHANNELS ---
    for ch in feed_root.findall("channel"):
        cid = ch.attrib.get("id")
        if cid in mini_ids and cid not in channels_out:
            # creiamo un channel pulito stile XML di riferimento
            ch_out = ET.Element("channel", id=cid)

            dn = ET.SubElement(ch_out, "display-name", lang="it")
            dn.text = mini_channels_display[cid]

            channels_out[cid] = ch_out

    # --- PROGRAMMES ---
    for pr in feed_root.findall("programme"):
        cid = pr.attrib.get("channel")
        if cid in mini_ids:
            programmes_out.append(copy.deepcopy(pr))

# ------------------------------------------
#  COSTRUZIONE FINALE: PRIMA CHANNEL, POI PROGRAMME
# ------------------------------------------
print("🧱 Costruisco mini_epg.xml (channels prima, poi programmes)...")

# 1) tutti i channel, ordinati per id (solo per avere ordine stabile)
for cid in sorted(channels_out.keys()):
    root.append(channels_out[cid])

# 2) tutti i programmes
for pr in programmes_out:
    root.append(pr)

# ------------------------------------------
#  FUNZIONE INDENT PER AVERE XML FORMATTATO (NON TUTTO SU UNA RIGA)
# ------------------------------------------
def indent(elem, level=0):
    space = "  "
    i = "\n" + level * space
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + space
        for child in elem:
            indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i

indent(root)

# ------------------------------------------
#  SALVA mini_epg.xml
# ------------------------------------------
tree = ET.ElementTree(root)
tree.write("mini_epg.xml", encoding="utf-8", xml_declaration=True)

print("🎉 MINI EPG generata correttamente in mini_epg.xml")
