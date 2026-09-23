import requests
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple, Optional
import xml.etree.ElementTree as ET

# ------------------------------------------
# CONFIGURAZIONE API SKY
# ------------------------------------------
SKY_CHANNELS_URL = "https://apid.sky.it/gtv/v1/channels"
SKY_EVENTS_URL = "https://apid.sky.it/gtv/v1/events"

# ------------------------------------------
# RINOMINE E MAPPE (Mantenute dal tuo progetto)
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

FORCED_DISPLAYNAMES: Dict[str, List[str]] = {
    "9115": ["Sky Uno FHD", "Sky Uno", "SKY UNO"],
    # Aggiungi qui altri ID scoperti nell'API di Sky se vuoi forzare i nomi per TiviMate
}

# ------------------------------------------
# FUNZIONI DI UTILITÀ
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


def fetch_sky_channels() -> List[dict]:
    """Scarica l'elenco ufficiale dei canali da Sky."""
    try:
        print("[INFO] Scarico la lista dei canali da Sky...")
        resp = requests.get(SKY_CHANNELS_URL, params={"env": "DTH"}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("channels", [])
    except Exception as exc:
        print(f"[ERRORE] Impossibile scaricare i canali Sky: {exc}")
        return []


def fetch_sky_events(channel_id: str, days: int = 3) -> List[dict]:
    """Scarica gli eventi/programmi per uno specifico ID canale Sky."""
    now = datetime.utcnow()
    from_date = now.strftime("%Y-%m-%dT00:00:00Z")
    to_date = (now + timedelta(days=days)).strftime("%Y-%m-%dT23:59:59Z")
    
    params = {
        "env": "DTH",
        "channels": channel_id,
        "pageSize": 100,
        "pageNum": 0,
        "from": from_date,
        "to": to_date
    }
    
    try:
        resp = requests.get(SKY_EVENTS_URL, params=params, timeout=30)
        if resp.status_code == 200:
            return resp.json().get("events", [])
    except Exception as exc:
        print(f"[ERRORE] Impossibile scaricare eventi per il canale {channel_id}: {exc}")
    return []


def build_epg() -> ET.Element:
    root = ET.Element("tv")
    
    channels = fetch_sky_channels()
    if not channels:
        print("[ERRORE] Nessun canale trovato dalle API di Sky.")
        return root

    combined_channels: List[ET.Element] = []
    combined_programmes: List[ET.Element] = []
    seen_channels: Set[str] = set()
    seen_programmes: Set[Tuple[str, str, str]] = set()

    for ch_data in channels:
        ch_id = str(ch_data.get("id"))
        ch_name = ch_data.get("name", "Unknown")
        
        if not ch_id:
            continue

        # Creazione elemento canale XMLTV
        ch_elem = ET.Element("channel", id=ch_id)
        dn = ET.SubElement(ch_elem, "display-name")
        dn.text = RENAME_MAP.get(ch_name, ch_name)
        
        combined_channels.append(ch_elem)
        seen_channels.add(ch_id)

        # Scarichiamo la programmazione per questo canale
        print(f"[INFO] Recupero palinsesto per: {ch_name} (ID: {ch_id})")
        events = fetch_sky_events(ch_id, days=2)
        
        for ev in events:
            start_str = ev.get("startTime")
            stop_str = ev.get("endTime")
            title = ev.get("title", "")
            
            # Estrazione avanzata per catturare la trama ufficiale e fonderla con il cast
            descrizione = ev.get("longDescription") or ev.get("description") or ev.get("synopsis") or ""
            
            cast_list = ev.get("cast", [])
            if isinstance(cast_list, list):
                cast_str = ", ".join([c.get("name", str(c)) for c in cast_list if c])
            else:
                cast_str = str(cast_list)

            # Unione pulita di trama e cast per replicare le informazioni del decoder
            if descrizione and cast_str:
                full_desc = f"{descrizione}\n\nCast: {cast_str}"
            elif descrizione:
                full_desc = descrizione
            elif cast_str:
                full_desc = f"Cast: {cast_str}"
            else:
                full_desc = ""
            
            if not start_str or not stop_str:
                continue
                
            # Formato data standard atteso dalle API: 2026-09-23T... -> conversione XMLTV (YYYYMMDDHHMMSS +0000)
            try:
                dt_start = datetime.strptime(start_str.split(".")[0], "%Y-%m-%dT%H:%M:%S")
                dt_stop = datetime.strptime(stop_str.split(".")[0], "%Y-%m-%dT%H:%M:%S")
                
                fmt_xml = "%Y%m%d%H%M%S +0000"
                start_formatted = dt_start.strftime(fmt_xml)
                stop_formatted = dt_stop.strftime(fmt_xml)
            except Exception:
                continue

            key = (start_formatted, stop_formatted, ch_id)
            if key not in seen_programmes:
                pr_elem = ET.Element("programme", start=start_formatted, stop=stop_formatted, channel=ch_id)
                
                title_elem = ET.SubElement(pr_elem, "title", lang="it")
                title_elem.text = title
                
                if full_desc:
                    desc_elem = ET.SubElement(pr_elem, "desc", lang="it")
                    desc_elem.text = full_desc
                
                combined_programmes.append(pr_elem)
                seen_programmes.add(key)

    # Aggiunta display-names forzati se presenti
    for ch in combined_channels:
        cid = ch.attrib.get("id")
        if cid in FORCED_DISPLAYNAMES:
            for name in FORCED_DISPLAYNAMES[cid]:
                dn = ET.SubElement(ch, "display-name")
                dn.text = name

    for ch in combined_channels:
        root.append(ch)
    for pr in combined_programmes:
        root.append(pr)

    return root


def main() -> None:
    print("[INFO] Generazione EPG da API ufficiali Sky in corso...")
    root = build_epg()
    indent(root)
    tree = ET.ElementTree(root)
    tree.write("epg_sky.xml", encoding="utf-8", xml_declaration=True)
    print("[OK] File EPG di Sky generato con successo: epg_sky.xml")


if __name__ == "__main__":
    main()
