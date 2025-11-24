import requests
import lzma
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# ------------------------------------------
#  FEED ORIGINALI (FUNZIONANTI)
# ------------------------------------------

feeds = {
    "Sky": "http://www.xmltvepg.nl/rytecIT_Sky.xz",
    "Basic": "http://www.xmltvepg.nl/rytecIT_Basic.xz",
    "SportMovies": "http://www.xmltvepg.nl/rytecIT_SportMovies.xz"
}

# ------------------------------------------
#  RINOMINE CANALI (come volevi tu)
# ------------------------------------------

rename_map = {
    "Nove.it": "Nove",
    "20Mediaset.it": "Mediaset 20",
    "TopCrime.it": "TopCrime",
    "LA7Cinema.it": "LA 7 Cinema",
    "HGTV.it": "HGTV Home Garden",
    "SkySportAction.it": "Sky Sport Golf",
    "DAZNZona.it": "Dazn 1",
    "ZonaDAZN2.it": "Dazn 2",
    "Tgcom24.it": "Tgcom 24",
    "RaiSport.it": "Rai Sport+"
}

# ------------------------------------------
#  CANALI +1 DA CREARE (come concordato)
# ------------------------------------------

plus1_map = {
    "Italia1.it": "Italia 1 +1",
    "La7.it": "La7 +1",
    "Cielo.it": "Cielo +1",
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
    "SkyCinemaSuspense.it": "Sky Cinema Suspense +1",
    "20Mediaset.it": "Mediaset 20 +1"
}

# ------------------------------------------
#  CREAZIONE STRUTTURA XML COMBINATA
# ------------------------------------------

root_combined = ET.Element("tv")
seen_channels = set()
seen_programmes = set()

# ------------------------------------------
#  FUNZIONE: FORMATTARE XML (indent)
# ------------------------------------------

def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i

# ------------------------------------------
#  SCARICO E PROCESSO I FEED ORIGINALI
# ------------------------------------------

for name, url in feeds.items():
    print(f"Scarico feed {name}...")
    resp = requests.get(url)
    resp.raise_for_status()
    xml_data = lzma.decompress(resp.content)
    feed_root = ET.fromstring(xml_data)

    # -------------------------
    #  CHANNELS ORIGINALI
    # -------------------------
    for ch in feed_root.findall("channel"):
        cid = ch.attrib["id"]

        # RINOMINA CANALI
        if cid in rename_map:
            for dn in ch.findall("display-name"):
                dn.text = rename_map[cid]

        if cid not in seen_channels:
            root_combined.append(ch)
            seen_channels.add(cid)

        # AGGIUNTA CANALE +1
        if cid in plus1_map:
            new_id = cid + ".plus1"
            if new_id not in seen_channels:
                plus_ch = ET.Element("channel", id=new_id)

                # display-name senza lingue
                dn0 = ET.SubElement(plus_ch, "display-name")
                dn0.text = plus1_map[cid]

                # display-name IT
                dn1 = ET.SubElement(plus_ch, "display-name", lang="it")
                dn1.text = plus1_map[cid]

                # display-name EN
                dn2 = ET.SubElement(plus_ch, "display-name", lang="en")
                dn2.text = plus1_map[cid]

                root_combined.append(plus_ch)
                seen_channels.add(new_id)

    # -------------------------
    # PROGRAMMI ORIGINALI
    # -------------------------
    for pr in feed_root.findall("programme"):
        key = (
            pr.attrib["start"],
            pr.attrib["stop"],
            pr.attrib["channel"]
        )

        # Aggiungi programma originale
        if key not in seen_programmes:
            root_combined.append(pr)
            seen_programmes.add(key)

        # Duplica +1?
        cid = pr.attrib["channel"]
        if cid in plus1_map:

            # Shift orario di +1 ora
            fmt = "%Y%m%d%H%M%S %z"
            start = datetime.strptime(pr.attrib["start"], fmt) + timedelta(hours=1)
            stop = datetime.strptime(pr.attrib["stop"], fmt) + timedelta(hours=1)

            new_pr = ET.Element(
                "programme",
                start=start.strftime(fmt),
                stop=stop.strftime(fmt),
                channel=cid + ".plus1"
            )

            # Copia i sotto-elementi (title, desc, etc.)
            for child in pr:
                new_child = ET.SubElement(new_pr, child.tag, child.attrib)
                new_child.text = child.text

            root_combined.append(new_pr)

# ------------------------------------------
#  FORMATTAZIONE FINALE XML
# ------------------------------------------

indent(root_combined)

tree = ET.ElementTree(root_combined)
tree.write("epg.xml", encoding="utf-8", xml_declaration=True)

# ------------------------------------------
#  CREO epg.xz COME DA TUO SCRIPT ORIGINALE
# ------------------------------------------

with lzma.open("epg.xz", "wb") as f:
    with open("epg.xml", "rb") as infile:
        f.write(infile.read())

print("🎉 EPG Completata con rinomine e +1!")
