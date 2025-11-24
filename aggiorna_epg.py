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
    Rinomina il display-name di un canale esistente.
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
    """
    if not value:
        return value

    base = value[:14]   # YYYYMMDDHHMMSS
    resto = value[14:]  # timezone o altro

    dt = datetime.strptime(base, "%Y%m%d%H%M%S")
    dt_new = dt + timedelta(hours=ore)
    return dt_new.strftime("%Y%m%d%H%M%S") + resto


def crea_canale_plus1(root, original_id, nuovo_id, nuovo_nome):
    """
    Duplica un canale + i suoi programme con shift +1h.
    """
    # Trova il channel originale
    originale = None
    for ch in root.findall("channel"):
        if ch.get("id") == original_id:
            originale = ch
            break

    if originale is None:
        print(f"[ERRORE] Channel {original_id} non trovato (crea +1)")
        return

    # Duplica <channel>
    nuovo_canale = copy.deepcopy(originale)
    nuovo_canale.set("id", nuovo_id)

    dn = nuovo_canale.find("display-name")
    if dn is not None:
        dn.text = nuovo_nome
    else:
        ET.SubElement(nuovo_canale, "display-name").text = nuovo_nome

    root.insert(0, nuovo_canale)

    # FIX IMPORTANTE: crea una lista fissa dei programme
    all_programmes = list(root.findall("programme"))

    programmi_da_aggiungere = []
    count = 0

    for prog in all_programmes:
        if prog.get("channel") == original_id:
            nuovo_prog = copy.deepcopy(prog)
            nuovo_prog.set("channel", nuovo_id)

            for attr in ("start", "stop"):
                old = nuovo_prog.get(attr)
                if old:
                    nuovo_prog.set(attr, _shift_orario_xmltv(old, ore=1))

            programmi_da_aggiungere.append(nuovo_prog)
            count += 1

    for p in programmi_da_aggiungere:
        root.append(p)

    print(f"[OK] CREATO +1: {original_id} -> {nuovo_id} ({nuovo_nome}) | Programmi copiati: {count}")


def modifica_epg(root):
    """
    Crea canali +1 e rinomina.
    """
    # Mappa ID reali trovati nei <channel>
    id_map = {}
    for ch in root.findall("channel"):
        cid = ch.get("id")
        if cid:
            id_map[cid.lower()] = cid

    # 🔵 Duplica +1
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

    for user_id, nuovo_nome in plus1.items():
        key = user_id.lower()
        if key not in id_map:
            print(f"[ATTENZIONE] Nessun channel simile a {user_id} trovato (per +1)")
            continue

        real_id = id_map[key]
        nuovo_id = real_id + ".plus1"

        crea_canale_plus1(root, real_id, nuovo_id, nuovo_nome)

    # 🟡 Rinomina
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

    for user_id, nuovo_nome in rinomina.items():
        key = user_id.lower()
        if key not in id_map:
            print(f"[ATTENZIONE] Nessun channel simile a {user_id} trovato (rinomina)")
            continue

        real_id = id_map[key]
        rinomina_canale(root, real_id, nuovo_nome)


# ---------------------------------------------------
# DOWNLOAD E MERGE DEI FEED RYTEC
# ---------------------------------------------------

feeds = {
    "Sky": "http://www.xmltvepg.nl/rytecIT_Sky.xz",
    "Basic": "http://www.xmltvepg.nl/rytecIT_Basic.xz",
    "SportMovies": "http://www.xmltvepg.nl/rytecIT_SportMovies.xz"
}

root_combined = ET.Element("tv")

seen_channels = set()
seen_programmes = set()

for name, url in feeds.items():
    print(f"Scarico feed {name}...")
    resp = requests.get(url)
    resp.raise_for_status()

    xml_data = lzma.decompress(resp.content)
    feed_root = ET.fromstring(xml_data)

    # CHANNEL
    for ch in feed_root.findall("channel"):
        cid = ch.get("id")
        if cid not in seen_channels:
            root_combined.append(ch)
            seen_channels.add(cid)

    # PROGRAMMES
    for pr in feed_root.findall("programme"):
        key = (
            pr.get("start"),
            pr.get("stop"),
            pr.get("channel")
        )
        if key not in seen_programmes:
            root_combined.append(pr)
            seen_programmes.add(key)

# ---------------------------------------------------
# MODIFICHE FINALI (RINOMINE + +1)
# ---------------------------------------------------

print("Applico modifiche (rinomine + canali +1)...")
modifica_epg(root_combined)

# ---------------------------------------------------
# SALVATAGGIO XML + COMPRESSO
# ---------------------------------------------------

tree = ET.ElementTree(root_combined)
tree.write("epg.xml", encoding="utf-8", xml_declaration=True)

with lzma.open("epg.xz", "wb") as f:
    with open("epg.xml", "rb") as infile:
        f.write(infile.read())

print("🎉 EPG XMLTV generata correttamente e compatibile con TiviMate!")
