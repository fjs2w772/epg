import requests
import lzma
import xml.etree.ElementTree as ET

# ----------------------------
# FEED RYTEC ORIGINALI
# ----------------------------
feeds = {
    "Sky": "http://www.xmltvepg.nl/rytecIT_Sky.xz",
    "Basic": "http://www.xmltvepg.nl/rytecIT_Basic.xz",
    "SportMovies": "http://www.xmltvepg.nl/rytecIT_SportMovies.xz"
}

# ----------------------------
# CANALI DA INCLUDERE NELLA MINI EPG
# ----------------------------
mini_channels = {
    "Nove.it",
    "Italia1.it.plus1",
    "La7.it.plus1",
    "Cielo.it.plus1",
    "Giallo.it.plus1",
    "Cine34.it.plus1",
    "RealTimePlus1.it",
    "FoodNetwork.it.plus1",
    "TwentySeven.it.plus1",
    "DMAXPlus1.it",
    "Rai5.it.plus1",
    "Rai4.it.plus1"
}

# ----------------------------
# CREA STRUTTURA XML
# ----------------------------
root_mini = ET.Element("tv")
added_channels = set()

# ----------------------------
# PROCESSA FEED
# ----------------------------
for name, url in feeds.items():
    print(f"Scarico feed {name}...")
    resp = requests.get(url)
    resp.raise_for_status()
    xml_data = lzma.decompress(resp.content)

    feed_root = ET.fromstring(xml_data)

    # CHANNELS
    for ch in feed_root.findall("channel"):
        cid = ch.attrib["id"]

        if cid in mini_channels and cid not in added_channels:
            root_mini.append(ch)
            added_channels.add(cid)

    # PROGRAMMES
    for pr in feed_root.findall("programme"):
        cid = pr.attrib["channel"]

        if cid in mini_channels:
            root_mini.append(pr)

# ----------------------------
# SALVA mini_epg.xml
# ----------------------------
tree = ET.ElementTree(root_mini)
tree.write("mini_epg.xml", encoding="utf-8", xml_declaration=True)

# ----------------------------
# CREA mini_epg.xz
# ----------------------------
with lzma.open("mini_epg.xz", "wb") as f:
    with open("mini_epg.xml", "rb") as infile:
        f.write(infile.read())

print("✅ MINI EPG generata con successo!")
