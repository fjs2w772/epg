import requests
import gzip
import xml.etree.ElementTree as ET

# Feed unico completo Italia
feeds = {
    "ItalyFull": "http://rytecepg.ipservers.eu/epg_data/rytecxmltvItaly.gz"
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

    # Decompressione GZIP
    xml_data = gzip.decompress(resp.content)

    # Parse XML
    feed_root = ET.fromstring(xml_data)

    # Copia CHANNEL
    for ch in feed_root.findall("channel"):
        cid = ch.get("id")
        if cid not in seen_channels:
            root_combined.append(ch)
            seen_channels.add(cid)

    # Copia PROGRAMMES
    for pr in feed_root.findall("programme"):
        key = (pr.get("start"), pr.get("stop"), pr.get("channel"))
        if key not in seen_programmes:
            root_combined.append(pr)
            seen_programmes.add(key)

# Salva XMLTV finale
tree = ET.ElementTree(root_combined)
tree.write("epg.xml", encoding="utf-8", xml_declaration=True)

# Crea epg.xz compresso
import lzma
with lzma.open("epg.xz", "wb") as f:
    with open("epg.xml", "rb") as infile:
        f.write(infile.read())

print("🎉 EPG XMLTV generata correttamente (TEST BASE - MIRROR IPServers).")
