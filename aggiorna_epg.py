import requests
import lzma
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import copy

# ---------------------------------------------------
# FUNZIONI DI SUPPORTO: RINOMINA E +1
# ---------------------------------------------------

def rinomina_canale(root, channel_id, nuovo_nome):
    """
    Rinomina il display-name di un canale esistente
    senza toccare l'ID né i programmi.
    """
    trovato = False
    for ch in root.findall("channel"):
        if ch.get("id") == channel_id:
            dn = ch.find("display-name")
            if dn is not None:
                dn.text = nuovo_nome
            else:
                dn = ET.SubElement(ch, "display-name")
                dn.text = nuovo_nome
            print(f"[OK] RINOMINATO: {channel_id} -> {nuovo_nome}")
            trovato = True
            break
    if not trovato:
        print(f"[ATTENZIONE] Canale {channel_id} non trovato (rinomina)")


def _shift_orario_xmltv(value, ore=1):
    """
    Shifta un orario XMLTV di 'ore' ore.
    Supporta formati tipo:
    - YYYYMMDDHHMMSS
    - YYYYMMDDHHMMSS +0000
    - YYYYMMDDHHMMSS +0100
    """
    if not value:
        return value

    # primi 14 caratteri = data/ora
    base = value[:14]
    resto = value[14:]  # eventuale timezone o altro

    dt = datetime.strptime(base, "%Y%m%d%H%M%S")
    dt_new = dt + timedelta(hours=ore)
    return dt_new.strftime("%Y%m%d%H%M%S") + resto


def crea_canale_plus1(root, original_id, nuovo_id, nuovo_nome):
    """
    Crea un canale +1:
    - duplica la definizione <channel>
    - crea nuovi <programme> con start/stop +1h
    - mantiene intatto il canale originale
    """
    # 1. Duplica la sezione <channel>
    originale = None
    for ch in root.findall("channel"):
        if ch.get("id") == original_id:
            originale = ch
            break

    if originale is None:
        print(f"[ERRORE] Canale {original_id} non trovato (crea +1)")
        return

    nuovo_canale = copy.deepcopy(originale)
    nuovo_canale.set("id", nuovo_id)

    # cambia il display-name
    dn = nuovo_canale.find("display-name")
    if dn is not None:
        dn.text = nuovo_nome
    else:
        ET.SubElement(nuovo_canale, "display-name").text = nuovo_nome

    # inserisci il nuovo canale all'inizio (solo per ordine estetico)
    root.insert(0, nuovo_canale)

    # 2. Duplica tutti i programmes del canale originale con +1h
    programmi_da_aggiungere = []

    for prog in root.findall("programme"):
        if prog.get("channel") == original_id:
            nuovo_prog = copy.deepcopy(prog)
            nuovo_prog.set("channel", nuovo_id)

            # shift start e stop
            for attr in ("start", "stop"):
                old = nuovo_prog.get(attr)
                if not old:
                    continue
                nuovo_prog.set(attr, _shift_orario_xmltv(old, ore=1))

            programmi_da_aggiungere.append(nuovo_prog)

    for p in programmi_da_aggiungere:
        root.append(p)

    print(f"[OK] CREATO +1: {original_id} → {nuovo_id} ({nuovo_nome})")


def modifica_epg(root):
    """
    Applica tutte le modifiche richieste:
    - creazione canali +1
    - rinomina di alcuni canali esistenti
    """
    # 🔵 DUPLICAZIONI +1 (manteniamo gli originali intatti)
    plus1 = {
        "Italia1.it": "Italia 1 +1",
        "La7.it": "La7 +1",
        "Cielo.it": "Cielo +1",
        "20Mediaset.it": "Mediaset 20 +1",
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
    }

    for original_id, nuovo_nome in plus1.items():
        nuovo_id = original_id + ".plus1"
        crea_canale_plus1(root, original_id, nuovo_id, nuovo_nome)

    # 🟡 RINOMINE (solo display-name, niente duplicazione)
    rinomina = {
        "Nove.it": "Nove",
        "20Mediaset.it": "Mediaset 20",
        "RaiSport.it": "Rai Sport+",
        "TopCrime.it": "TopCrime",
        "LA7Cinema.it": "LA 7 Cinema",
        "HGTV.it": "HGTV Home Garden",
        "SkySportAction.it": "Sky Sport Golf",
        "DAZNZona.it": "Dazn 1",
        "ZonaDAZN2.it": "Dazn 2",
        "Tgcom24.it": "Tgcom 24",
    }

    for cid, nn in rinomina.items():
        rinomina_canale(root, cid, nn)


# ---------------------------------------------------
# CODICE ORIGINALE: DOWNLOAD E MERGE DEI FEED RYTEC
# ---------------------------------------------------

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

# ---------------------------------------------------
# 🔧 APPLICA MODIFICHE (RINOMINE + CANALI +1)
# ---------------------------------------------------

print("Applico modifiche: rinomine e canali +1...")
modifica_epg(root_combined)

# ---------------------------------------------------
# SALVATAGGIO FINALE COME PRIMA (epg.xml + epg.xz)
# ---------------------------------------------------

tree = ET.ElementTree(root_combined)
tree.write("epg.xml", encoding="utf-8", xml_declaration=True)

# Crea epg.xz compresso (lasciato IDENTICO al tuo script originale)
with lzma.open("epg.xz", "wb") as f:
    with open("epg.xml", "rb") as infile:
        f.write(infile.read())

print("🎉 EPG XMLTV generata correttamente e compatibile con TiviMate!")
