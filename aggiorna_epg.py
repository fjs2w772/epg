import requests
import lzma
import xml.etree.ElementTree as ET

# URL dei feed Rytec
feeds = {
    "Sky": "http://www.xmltvepg.nl/rytecIT_Sky.xz",
    "Basic": "http://www.xmltvepg.nl/rytecIT_Basic.xz",
    "SportMovies": "http://www.xmltvepg.nl/rytecIT_SportMovies.xz"
}

# Lista per salvare tutti gli eventi
all_programs = []

for name, url in feeds.items():
    print(f"Scarico feed {name}...")
    resp = requests.get(url)
    resp.raise_for_status()
    # Decomprimi l'xz
    decompressed = lzma.decompress(resp.content)
    # Parse XML
    root = ET.fromstring(decompressed)
    # Aggiungi tutti gli eventi alla lista
    for program in root.findall("programme"):
        all_programs.append(program)

# Creiamo il nuovo XML combinato
root_combined = ET.Element("tv")

for program in all_programs:
    root_combined.append(program)

tree = ET.ElementTree(root_combined)

# Salviamo in epg.xml temporaneo
tree.write("epg.xml", encoding="utf-8")

# Comprimiamo in xz
with lzma.open("epg.xz", "wb") as f:
    with open("epg.xml", "rb") as infile:
        f.write(infile.read())

print("EPG combinata salvata in epg.xz")

