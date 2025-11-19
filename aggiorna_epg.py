import requests
import lzma
import xml.etree.ElementTree as ET

# URL dei feed Rytec
feeds = {
    "Sky": "http://www.xmltvepg.nl/rytecIT_Sky.xz",
    "Basic": "http://www.xmltvepg.nl/rytecIT_Basic.xz",
    "SportMovies": "http://www.xmltvepg.nl/rytecIT_SportMovies.xz"
}

# Root del nuovo XMLTV
root_combined = ET.Element("tv")

# Set per evitare duplicati
seen_channels = set()
seen_programmes = set()

for name, url in feeds.items():
    print(f"Scarico feed {name}...")
    resp = requests.get(url)
    resp.raise_for_status()

    # Decomprimi
    xml_data = lzma.decompress(resp.content)

    # Parse XML
    feed_root = ET.fromstring(xml_data)

    # ---------------------------
    # 1️⃣ Copia i CHANNEL
    # ---------------------------
    for ch in feed_root.findall("channel"):
        channel_id = ch.attrib.get("id")

        if channel_id not in seen_channels:
            root_combined.append(ch)
            seen_channels.add(channel_id)

    # ---------------------------
    # 2️⃣ Copia i PROGRAMMES
    # ---------------------------
    for pr in feed_root.findall("programme"):
        key = (
            pr.attrib.get("start"),
            pr.attrib.get("stop"),
            pr.attrib.get("channel")
        )

        if key not in seen_programmes:
            root_combined.append(pr)
            seen_programmes.add(key)

# Salva XMLTV finale
tree = ET.ElementTree(root_combined)
tree.write("epg.xml", encoding="utf-8", xml_declaration=True)

# Crea epg.xz compresso
with lzma.open("epg.xz", "wb") as f:
    with open("epg.xml", "rb") as infile:
        f.write(infile.read())

print("🎉 EPG XMLTV generata correttamente e compatibile con TiviMate!")
