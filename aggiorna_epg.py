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

    # --- ITALIA 1 (base) ---
    "Italia1.it": [
        "Italia Uno", "Italia1", "Italia 1"
    ],
    # --- ITALIA 1 +1 ---
    "Italia1.it.plus1": [
        "Italia 1 +1", "Italia 1 +1 HD", "Italia 1 +1 FHD",
        "Italia Uno +1", "ITALIA 1 +1"
    ],

    # --- LA7 (base) ---
    "La7.it": [
        "La 7", "La7"
    ],
    # --- LA7 +1 ---
    "La7.it.plus1": [
        "La 7 +1", "LA 7 +1", "La7 +1", "LA7 +1"
    ],

    # --- TV8 ---
    "Tv8.it": [
        "Tv 8 FHD", "TV 8", "Tv8", "TV8"
    ],
    "Tv8.it.plus1": [
        "TV 8 +1", "TV 8 +1 HD", "TV 8 +1 FHD",
        "TV8 +1", "Tv8 +1"
    ],

    # --- CIELO ---
    "Cielo.it": [
        "Cielo FHD", "Cielo"
    ],
    "Cielo.it.plus1": [
        "Cielo +1", "Cielo +1 HD", "Cielo +1 FHD"
    ],

    # --- GIALLO ---
    "Giallo.it": [
        "Discovery Giallo FHD", "Giallo"
    ],
    "Giallo.it.plus1": [
        "Discovery Giallo +1", "Discovery Giallo +1 HD", "Giallo +1"
    ],

    # --- CINE34 ---
    "Cine34.it": [
        "Cine 34 FHD", "Cine34", "Cine 34"
    ],
    "Cine34.it.plus1": [
        "Cine 34 +1", "Cine 34 +1 HD", "Cine34 +1"
    ],

    # --- REAL TIME ---
    "RealTime.it": [
        "Real Time FHD", "Real Time", "RealTime"
    ],
    "RealTime.it.plus1": [
        "Real Time +1", "Real Time +1 HD", "Real Time +1 FHD", "RealTime +1"
    ],

    # --- FOOD NETWORK ---
    "FoodNetwork.it": [
        "Food Network FHD", "Food Network"
    ],
    "FoodNetwork.it.plus1": [
        "Food Network +1", "Food Network +1 HD", "Food Network +1 FHD"
    ],

    # --- 27 / TWENTYSEVEN ---
    "TwentySeven.it": [
        "27 Twentyseven FHD", "TwentySeven", "27"
    ],
    "TwentySeven.it.plus1": [
        "27 Twentyseven +1", "27 Twentyseven +1 HD", "TwentySeven +1", "27 +1"
    ],

    # --- DMAX ---
    "DMAX.it": [
        "Discovery Dmax FHD", "DMAX", "Dmax"
    ],
    "DMAX.it.plus1": [
        "Discovery Dmax +1", "Discovery Dmax +1 HD", "DMAX +1", "Dmax +1"
    ],

    # --- RAI 5 ---
    "Rai5.it": [
        "Rai 5 FHD", "Rai 5", "Rai5"
    ],
    "Rai5.it.plus1": [
        "Rai 5 +1", "Rai 5 +1 HD", "Rai5 +1"
    ],

    # --- RAI 4 ---
    "Rai4.it": [
        "Rai 4 Fhd", "Rai 4", "Rai4"
    ],
    "Rai4.it.plus1": [
        "Rai 4 +1", "Rai 4 +1 HD", "Rai4 +1"
    ],

    # --- RAI SPORT+ ---
    "RaiSport.it": [
        "Rai Sport + FHD", "Rai Sport+", "RaiSport+"
    ],

    # --- NOVE (già sopra) / REAL TIME / ecc. altre già coperte ---
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
    "DMAX.it": "Discovery Dmax +1",
    "RealTime.it": "Real Time +1",
    "Giallo.it.plus_check": "Giallo +1",  # placeholder se necessario, ma il +1 reale è gestito sopra
}

# ------------------------------------------
#  FUNZIONI DI UTILITÀ
# ------------------------------------------


def indent(elem: ET.Element, level: int = 0) -> None:
    """
    Format XML with indentation to keep epg.xml leggibile.
    """
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
    """
    Scarica il feed .xz, decomprime e restituisce la root XML.
    Se qualcosa va storto, restituisce None (il resto dei feed continua).
    """
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


def apply_rename_map_to_channel(channel: ET.Element) -> None:
    """
    Applica RENAME_MAP al channel-id, modificando i display-name se necessario.
    """
    cid = channel.attrib.get("id")
    if cid in RENAME_MAP:
        new_name = RENAME_MAP[cid]
        for dn in channel.findall("display-name"):
            dn.text = new_name


def create_plus1_channel(original_id: str, display_name: str) -> ET.Element:
    """
    Crea un nuovo elemento <channel> per il canale +1 con vari display-name.
    """
    new_id = original_id + ".plus1"
    ch = ET.Element("channel", id=new_id)

    # display-name senza lang
    dn0 = ET.SubElement(ch, "display-name")
    dn0.text = display_name

    # display-name IT
    dn1 = ET.SubElement(ch, "display-name", lang="it")
    dn1.text = display_name

    # display-name EN
    dn2 = ET.SubElement(ch, "display-name", lang="en")
    dn2.text = display_name

    return ch


def create_plus1_programme(original: ET.Element, new_channel_id: str) -> Optional[ET.Element]:
    """
    Crea un nuovo <programme> spostato di +1h per il canale +1.
    Mantiene lo stesso timezone dell'originale.
    """
    fmt = "%Y%m%d%H%M%S %z"
    try:
        start_str = original.attrib["start"]
        stop_str = original.attrib["stop"]

        start_dt = datetime.strptime(start_str, fmt) + timedelta(hours=1)
        stop_dt = datetime.strptime(stop_str, fmt) + timedelta(hours=1)

        new_pr = ET.Element(
            "programme",
            start=start_dt.strftime(fmt),
            stop=stop_dt.strftime(fmt),
            channel=new_channel_id,
        )

        # Copia tutti i sotto-elementi (title, sub-title, desc, ecc.)
        for child in original:
            new_child = ET.SubElement(new_pr, child.tag, child.attrib)
            new_child.text = child.text

        return new_pr
    except Exception as exc:
        print(f"[ERRORE] Impossibile creare programme +1 per {original.attrib.get('channel')}: {exc}")
        return None


def add_forced_displaynames_to_channel(channel: ET.Element) -> None:
    """
    Aggiunge alias di display-name per migliorare il match su Tivimate,
    evitando duplicati.
    """
    cid = channel.attrib.get("id")
    if cid not in FORCED_DISPLAYNAMES:
        return

    existing_names: Set[str] = set()
    for dn in channel.findall("display-name"):
        if dn.text:
            existing_names.add(dn.text.strip())

    for name in FORCED_DISPLAYNAMES[cid]:
        if name not in existing_names:
            new_dn = ET.SubElement(channel, "display-name")
            new_dn.text = name
            existing_names.add(name)


# ------------------------------------------
#  LOGICA PRINCIPALE
# ------------------------------------------


def build_epg() -> ET.Element:
    """
    Scarica tutti i feed, combina channels e programmes,
    genera i +1, applica rinomine e alias, e restituisce la root <tv>.
    """
    root = ET.Element("tv")

    # Conserviamo canali e programmi separati per garantire
    # che tutti i <channel> vengano prima dei <programme>.
    combined_channels: List[ET.Element] = []
    combined_programmes: List[ET.Element] = []

    seen_channels: Set[str] = set()
    seen_programmes: Set[Tuple[str, str, str]] = set()

    for name, url in FEEDS.items():
        feed_root = download_and_parse_feed(name, url)
        if feed_root is None:
            # Passa al prossimo feed
            continue

        # -------------------------
        #  CHANNELS ORIGINALI
        # -------------------------
        for ch in feed_root.findall("channel"):
            cid = ch.attrib.get("id")
            if not cid:
                continue

            # RINOMINA CANALI
            apply_rename_map_to_channel(ch)

            # Aggiungi solo se non già visto
            if cid not in seen_channels:
                combined_channels.append(ch)
                seen_channels.add(cid)

            # AGGIUNTA CANALE +1 SE PREVISTO
            if cid in PLUS1_MAP:
                plus1_id = cid + ".plus1"
                if plus1_id not in seen_channels:
                    display_name_plus1 = PLUS1_MAP[cid]
                    plus_ch = create_plus1_channel(cid, display_name_plus1)
                    combined_channels.append(plus_ch)
                    seen_channels.add(plus1_id)

        # -------------------------
        #  PROGRAMMI ORIGINALI
        # -------------------------
        for pr in feed_root.findall("programme"):
            start = pr.attrib.get("start")
            stop = pr.attrib.get("stop")
            channel = pr.attrib.get("channel")

            if not start or not stop or not channel:
                continue

            key = (start, stop, channel)

            # Aggiungi programma originale se non visto
            if key not in seen_programmes:
                combined_programmes.append(pr)
                seen_programmes.add(key)

            # Se il canale ha una versione +1, crea anche il relativo programme
            if channel in PLUS1_MAP:
                plus1_id = channel + ".plus1"
                new_pr = create_plus1_programme(pr, plus1_id)
                if new_pr is not None:
                    new_key = (
                        new_pr.attrib["start"],
                        new_pr.attrib["stop"],
                        new_pr.attrib["channel"],
                    )
                    if new_key not in seen_programmes:
                        combined_programmes.append(new_pr)
                        seen_programmes.add(new_key)

    # -------------------------
    #  AGGIUNTA DISPLAY-NAME FORZATI
    # -------------------------
    for ch in combined_channels:
        add_forced_displaynames_to_channel(ch)

    # -------------------------
    #  ASSEMBLA <tv>: PRIMA CHANNELS, POI PROGRAMMES
    # -------------------------
    for ch in combined_channels:
        root.append(ch)

    for pr in combined_programmes:
        root.append(pr)

    return root


def main() -> None:
    """
    Entry point: costruisce l'EPG e scrive epg.xml.
    """
    print("[INFO] Generazione EPG in corso...")
    root = build_epg()

    # Formattazione leggibile
    indent(root)

    tree = ET.ElementTree(root)
    output_filename = "epg.xml"

    tree.write(output_filename, encoding="utf-8", xml_declaration=True)
    print(f"[OK] File EPG generato: {output_filename}")


if __name__ == "__main__":
    main()
