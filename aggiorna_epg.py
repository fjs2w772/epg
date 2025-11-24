import requests
import gzip
import xml.etree.ElementTree as ET

# FEED UNICO COMPLETO RYTEC - MIRROR XMLTV.SE
FEED_URL = "http://xmltv.xmltv.se/rytecxmltvItaly.gz"

print(f"Scarico feed unico Rytec...")
resp = requests.get(FEED_URL)
resp.raise_for_status()

# Decomprimi GZIP
xml_data = gzip.decompress(resp.content)

# Parse XML
root = ET.fromstring(xml_data)

# Salva epg.xml
with open("epg.xml", "wb") as f:
    f.write(xml_data)

print("🎉 EPG generata correttamente da feed unico Rytec!")
print(f"Totale canali: {len(root.findall('channel'))}")
print(f"Totale programmi: {len(root.findall('programme'))}")
