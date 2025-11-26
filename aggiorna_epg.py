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
    # --- NOVE ---
    "Nove.it": [
        "Discovery Nove FHD", "Nove", "NOVE"
    ],

    # --- ITALIA 1 +1 ---
    "Italia1.it.plus1": [
        "Italia 1 +1 HD", "Italia 1 +1", "Italia1 +1"
    ],

    # --- LA7 +1 ---
    "La7.it.plus1": [
        "La 7 +1 HD", "La 7 +1", "La7 +1"
    ],

    # --- TV8 ---
    "Tv8.it": [
        "Tv 8 FHD", "TV 8", "Tv8", "TV8"
    ],
    "Tv8.it.plus1": [
        "TV 8 +1 HD", "TV 8 +1", "TV8 +1", "Tv8 +1"
    ],

    # --- CIELO ---
    "Cielo.it": [
        "Cielo FHD", "Cielo"
    ],
    "Cielo.it.plus1": [
        "Cielo +1 HD", "Cielo +1"
    ],

    # --- GIALLO ---
    "Giallo.it": [
        "Discovery Giallo FHD", "Giallo"
    ],
    "Giallo.it.plus1": [
        "Discovery Giallo +1 HD", "Giallo +1"
    ],

    # --- LA7D / LA7 CINEMA ---
    "La7d.it": [
        "La 7d FHD", "La7d", "La7 Cinema"
    ],

    # --- CINE34 ---
    "Cine34.it": [
        "Cine 34 FHD", "Cine34", "Cine 34"
    ],
    "Cine34.it.plus1": [
        "Cine 34 +1 HD", "Cine34 +1", "Cine 34 +1"
    ],

    # --- HGTV ---
    "HGTV.it": [
        "Discovery HGTV Home Garden FHD", "HGTV Home Garden", "HGTV"
    ],

    # --- TOP CRIME ---
    "TopCrime.it": [
        "Top Crime FHD", "TopCrime", "Top Crime"
    ],

    # --- REAL TIME ---
    "RealTime.it": [
        "Real Time FHD", "Real Time", "RealTime"
    ],
    "RealTime.it.plus1": [
        "Real Time +1 HD", "Real Time +1", "RealTime +1"
    ],

    # --- FOOD NETWORK ---
    "FoodNetwork.it": [
        "Food Network FHD", "Food Network"
    ],
    "FoodNetwork.it.plus1": [
        "Food Network +1 HD", "Food Network +1"
    ],

    # --- 27 / TWENTYSEVEN ---
    "TwentySeven.it": [
        "27 Twentyseven FHD", "TwentySeven", "27"
    ],
    "TwentySeven.it.plus1": [
        "27 Twentyseven +1 HD", "TwentySeven +1", "27 +1"
    ],

    # --- DMAX ---
    "DMAX.it": [
        "Discovery Dmax FHD", "DMAX", "Dmax"
    ],
    "DMAX.it.plus1": [
        "Discovery Dmax +1 HD", "DMAX +1", "Dmax +1"
    ],

    # --- RAI 5 ---
    "Rai5.it": [
        "Rai 5 FHD", "Rai 5", "Rai5"
    ],
    "Rai5.it.plus1": [
        "Rai 5 +1 HD", "Rai 5 +1", "Rai5 +1"
    ],

    # --- RAI 4 ---
    "Rai4.it": [
        "Rai 4 Fhd", "Rai 4", "Rai4"
    ],
    "Rai4.it.plus1": [
        "Rai 4 +1 HD", "Rai4 +1", "Rai 4 +1"
    ],

    # --- RAI SPORT+ ---
    "RaiSport.it": [
        "Rai Sport + FHD", "Rai Sport+", "RaiSport+"
    ]
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
    "Tv8.it": "TV8 +1",
}

# ------------------------------------------
#  FUNZIONI DI UTILITÀ
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


def main() -> None:
    print("[INFO] Generazione EPG in corso...")
    root = build_epg()
    indent(root)
    tree = ET.ElementTree(root)
    tree.write("epg.xml", encoding="utf-8", xml_declaration=True)
    print(f"[OK] File EPG generato: epg.xml")


if __name__ == "__main__":
    main()
