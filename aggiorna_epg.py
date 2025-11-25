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
#  RINOMINE CANALI (come concordato)
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
#  CANALI PER I QUALI CREARE VERSIONE +1
# ------------------------------------------

plus1_map = {
    "Italia1.it": "Italia 1 +1 HD",
    "La7.it": "La 7 +1 HD",
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
    "20Mediaset.it": "Mediaset 20 +1",
    "FoodNetwork.it": "Food Network +1",
    "TwentySeven.it": "Twenty Seven +1",
    "Rai5.it": "Rai 5 +1",
    "Rai4.it": "Rai 4 +1",
    "Tv8.it": "TV8 +1"
}

# ------------------------------------------
#  ECCEZIONI PER XTREAM CODES
# (usano lo stesso id del canale base!)
# ------------------------------------------

xtream_same_id_plus1 = {
    "Italia1.it": "Italia 1 +1 HD",
    "La7.it": "La 7 +1 HD"
}

# ------------------------------------------
#  CREAZIONE XML COMBINATO
# ------------------------------------------

root_combined = ET.Element("tv")
seen_channels = set()
seen_programmes = set()

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
#  ELABORAZIONE FEED
# ------------------------------------------

for name, url in feeds.items():
    print(f"Scarico feed {name}...")
    resp = requests.get(url)
    resp.raise_for_status()
    xml_data = lzma.decompress(resp.content)
    feed_root = ET.fromstring(xml_data)

    # CANALI ORIGINALI
    for ch in feed_root.findall("channel"):
        cid = ch.attrib["id"]

        # RINOMINA CANALI
        if cid in rename_map:
            for dn in ch.findall("display-name"):
                dn.text = rename_map[cid]

        if cid not in seen_channels:
            root_combined.append(ch)
            seen_channels.add(cid)

        # CREAZIONE +1 — CASO NORMALE
        if cid in plus1_map and cid not in xtream_same_id_plus1:
            new_id = cid + ".plus1"
            if new_id not in seen_channels:
                plus_ch = ET.Element("channel", id=new_id)
                dn = ET.SubElement(plus_ch, "display-name")
                dn.text = plus1_map[cid]
                root_combined.append(plus_ch)
                seen_channels.add(new_id)

        # CREAZIONE +1 — CASO XTREAM (STESSO ID)
        if cid in xtream_same_id_plus1:
            new_id = cid  # stesso id!
            alias_name = xtream_same_id_plus1[cid]

            plus_ch = ET.Element("channel", id=new_id)
            dn = ET.SubElement(plus_ch, "display-name")
            dn.text = alias_name

            root_combined.append(plus_ch)

    # PROGRAMMI
    for pr in feed_root.findall("programme"):
        key = (pr.attrib["start"], pr.attrib["stop"], pr.attrib["channel"])

        if key not in seen_programmes:
            root_combined.append(pr)
            seen_programmes.add(key)

        cid = pr.attrib["channel"]

        # CREAZIONE PROGRAMMI +1 NORMALI
        if cid in plus1_map and cid not in xtream_same_id_plus1:
            fmt = "%Y%m%d%H%M%S %z"
            start = datetime.strptime(pr.attrib["start"], fmt) + timedelta(hours=1)
            stop = datetime.strptime(pr.attrib["stop"], fmt) + timedelta(hours=1)

            new_pr = ET.Element(
                "programme",
                start=start.strftime(fmt),
                stop=stop.strftime(fmt),
                channel=cid + ".plus1"
            )

            for child in pr:
                new_child = ET.SubElement(new_pr, child.tag, child.attrib)
                new_child.text = child.text

            root_combined.append(new_pr)

        # CREAZIONE PROGRAMMI +1 XTREAM (STESSO ID)
        if cid in xtream_same_id_plus1:
            fmt = "%Y%m%d%H%M%S %z"
            start = datetime.strptime(pr.attrib["start"], fmt) + timedelta(hours=1)
            stop = datetime.strptime(pr.attrib["stop"], fmt) + timedelta(hours=1)

            new_pr = ET.Element(
                "programme",
                start=start.strftime(fmt),
                stop=stop.strftime(fmt),
                channel=cid
            )

            for child in pr:
                new_child = ET.SubElement(new_pr, child.tag, child.attrib)
                new_child.text = child.text

            root_combined.append(new_pr)

# ------------------------------------------
#  SALVATAGGIO XML + XZ
# ------------------------------------------

indent(root_combined)
tree = ET.ElementTree(root_combined)
tree.write("epg.xml", encoding="utf-8", xml_declaration=True)

with lzma.open("epg.xz", "wb") as f:
    with open("epg.xml", "rb") as infile:
        f.write(infile.read())

print("✅ EPG generata con +1 corretti per XTream Codes!")
