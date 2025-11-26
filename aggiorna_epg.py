import requests
import lzma
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple, Optional

# ------------------------------------------
#  FEED ORIGINALI (FUNZIONANTI)
# ------------------------------------------

FEEDS: Dict[str, str] = {
    "Sky": "http://www.xmltvepg.nl/rytecIT_Sky.xz",
    "Basic": "http://www.xmltvepg.nl/rytecIT_Basic.xz",
    "SportMovies": "http://www.xmltvepg.nl/rytecIT_SportMovies.xz",
}

# ------------------------------------------
#  RINOMINE CANALI
# ------------------------------------------

RENAME_MAP: Dict[str, str] = {
    "Nove.it": "Nove",
    "20Mediaset.it": "Mediaset 20",
    "TopCrime.it": "TopCrime",
    "LA7Cinema.it": "LA 7 Cinema",
    "HGTV.it": "HGTV Home Garden",
    "SkySportAction.it": "Sky Sport Golf",
    "DAZNZona.it": "Dazn 1",
    "ZonaDAZN2.it": "Dazn 2",
    "Tgcom24.it": "Tgcom 24",
    "RaiSport.it": "Rai Sport+",
}

# ----------------------------------------------------
#  DISPLAY-NAME FORZATI PER MATCH AUTOMATICO TIVIMATE
# ----------------------------------------------------

FORCED_DISPLAYNAMES: Dict[str, List[str]] = {
    "Nove.it": ["Discovery Nove FHD", "Nove", "NOVE"],
}

# ------------------------------------------
#  CANALI +1 DA CREARE
# ------------------------------------------

PLUS1_MAP: Dict[str, str] = {
    "Italia1.it": "Italia 1 +1",
    "La7.it": "La7 +1",
    "Cielo.it": "Cielo +1",
    "Giallo.it": "Giallo +1",
    "Cine34.it": "Cine 34 +1",
    "Tv8.it": "TV8 +1",
}

# ------------------------------------------
#  UTILITY
# ------------------------------------------

def indent(elem: ET.Element, level: int = 0) -> None:
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


def download_and_parse_feed(name: str, url: str) -> Optional[ET.Element]:
    try:
        print(f"[INFO] Scarico feed '{name}' da {url}...")
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        xml_data = lzma.decompress(resp.content)
        root = ET.fromstring(xml_data)
        print(f"[OK] Feed '{name}' scaricato e parsato.")
        return root
    except Exception as exc:
        print(f"[ERRORE] Impossibile processare feed '{name}': {exc}")
        return None


# ------------------------------------------
#  COSTRUZIONE EPG
# ------------------------------------------

def build_epg() -> ET.Element:
    root = ET.Element("tv")

    combined_channels: List[ET.Element] = []
    combined_programmes: List[ET.Element] = []

    seen_channels: Set[str] = set()
    seen_programmes: Set[Tuple[str, str, str]] = set()

    for name, url in FEEDS.items():
        feed_root = download_and_parse_feed(name, url)
        if feed_root is None:
            continue

        for ch in feed_root.findall("channel"):
            cid = ch.attrib.get("id")
            if not cid:
                continue

            if cid in RENAME_MAP:
                for dn in ch.findall("display-name"):
                    dn.text = RENAME_MAP[cid]

            if cid not in seen_channels:
                combined_channels.append(ch)
                seen_channels.add(cid)

            if cid in PLUS1_MAP:
                plus_id = cid + ".plus1"
                if plus_id not in seen_channels:
                    new_ch = ET.Element("channel", id=plus_id)
                    dn = ET.SubElement(new_ch, "display-name")
                    dn.text = PLUS1_MAP[cid]
                    combined_channels.append(new_ch)
                    seen_channels.add(plus_id)

        for pr in feed_root.findall("programme"):
            start = pr.attrib.get("start")
            stop = pr.attrib.get("stop")
            channel = pr.attrib.get("channel")

            if not start or not stop or not channel:
                continue

            key = (start, stop, channel)

            if key not in seen_programmes:
                combined_programmes.append(pr)
                seen_programmes.add(key)

            if channel in PLUS1_MAP:
                fmt = "%Y%m%d%H%M%S %z"
                start_dt = datetime.strptime(start, fmt) + timedelta(hours=1)
                stop_dt = datetime.strptime(stop, fmt) + timedelta(hours=1)

                new_pr = ET.Element(
                    "programme",
                    start=start_dt.strftime(fmt),
                    stop=stop_dt.strftime(fmt),
                    channel=channel + ".plus1",
                )

                for child in pr:
                    new_child = ET.SubElement(new_pr, child.tag, child.attrib)
                    new_child.text = child.text

                new_key = (
                    new_pr.attrib["start"],
                    new_pr.attrib["stop"],
                    new_pr.attrib["channel"],
                )

                if new_key not in seen_programmes:
                    combined_programmes.append(new_pr)
                    seen_programmes.add(new_key)

    for ch in combined_channels:
        if ch.attrib.get("id") in FORCED_DISPLAYNAMES:
            for name in FORCED_DISPLAYNAMES[ch.attrib["id"]]:
                dn = ET.SubElement(ch, "display-name")
                dn.text = name

    for ch in combined_channels:
        root.append(ch)

    for pr in combined_programmes:
        root.append(pr)

    return root


# ------------------------------------------
#  MAIN
# ------------------------------------------

def main() -> None:
    print("[INFO] Generazione EPG in corso...")
    root = build_epg()
    indent(root)
    tree = ET.ElementTree(root)
    tree.write("epg.xml", encoding="utf-8", xml_declaration=True)
    print("[OK] File EPG generato: epg.xml")


if __name__ == "__main__":
    main()

# ------------------------------------------
#  CREAZIONE epg.xz (sempre lo stesso file)
# ------------------------------------------

with lzma.open("epg.xz", "wb") as f:
    with open("epg.xml", "rb") as infile:
        f.write(infile.read())

print("[OK] File compresso generato: epg.xz")
