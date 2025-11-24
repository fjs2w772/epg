import requests
import lzma
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import copy

# ---------------------------------------------------
# FUNZIONI UTILI
# ---------------------------------------------------

def _shift_orario_xmltv(value, ore=1):
    """
    Shifta un orario XMLTV di 'ore' ore.
    """
    if not value:
        return value
    base = value[:14]
    resto = value[14:]
    dt = datetime.strptime(base, "%Y%m%d%H%M%S")
    dt_new = dt + timedelta(hours=ore)
    return dt_new.strftime("%Y%m%d%H%M%S") + resto


def aggiungi_metadati_canale(ch):
    """
    Aggiunge metadati minimi per rendere il canale compatibile con TiviMate:
    - display-name senza lingua
    - display-name lang="it"
    - display-name lang="en"
    - url placeholder
    """
    nome = None
    for dn in ch.findall("display-name"):
        nome = dn.text
        break

    if nome:
        # display-name senza lingua
        if ch.find("display-name[@lang]") is None:
            ET.SubElement(ch, "display-name").text = nome

        # display-name lang="it"
        if ch.find("display-name[@lang='it']") is None:
            dn = ET.SubElement(ch, "display-name")
            dn.set("lang", "it")
            dn.text = nome

        # display-name lang="en"
        if ch.find("display-name[@lang='en']") is None:
            dn = ET.SubElement(ch, "display-name")
            dn.set("lang", "en")
            dn.text = nome

    # url generico richiesto da TiviMate
    if ch.find("url") is None:
        ET.SubElement(ch, "url").text = "https://example.com"


def rinomina_canale(root, channel_id, nuovo_nome):
    """
    Cambia il nome commerciale del canale.
    """
    for ch in root.findall("channel"):
        if ch.get("id") == channel_id:
            # elimina vecchi display-name
            for dn in list(ch.findall("display-name")):
                ch.remove(dn)
            # ricrea i display-name standard
            dn = ET.SubElement(ch, "display-name")
            dn.text = nuovo_nome

            dn_it = ET.SubElement(ch, "display-name")
            dn_it.set("lang", "it")
            dn_it.text = nuovo_nome

            dn_en = ET.SubElement(ch, "display-name")
            dn_en.set("lang", "en")
            dn_en.text = nuovo_nome

            print(f"[OK] RINOMINATO: {channel_id} -> {nuovo_nome}")
            return

    print(f"[ATTENZIONE] Canale {channel_id} non trovato (rinomina)")


def crea_canale_plus1(root, original_id, nuovo_id, nuovo_nome):
    """
    Duplica il canale e crea un +1 con programmi shiftati.
    """

    # trova channel originale
    originale = None
    for ch in root.findall("channel"):
        if ch.get("id") == original_id:
            originale = ch
            break
    if originale is None:
        print(f"[ERRORE] {original_id} non trovato (crea +1)")
        return

    # duplica channel
    nuovo_ch = copy.deepcopy(originale)
    nuovo_ch.set("id", nuovo_id)

    # display-name personalizzato
    for dn in list(nuovo_ch.findall("display-name")):
        nuovo_ch.remove(dn)

    dn = ET.SubElement(nuovo_ch, "display-name")
    dn.text = nuovo_nome

    dn_it = ET.SubElement(nuovo_ch, "display-name")
    dn_it.set("lang", "it")
    dn_it.text = nuovo_nome

    dn_en = ET.SubElement(nuovo_ch, "display-name")
    dn_en.set("lang", "en")
    dn_en.text = nuovo_nome

    # metadati
    aggiungi_metadati_canale(nuovo_ch)

    root.insert(0, nuovo_ch)

    # FIX: lista fissa dei programmes
    all_programmes = list(root.findall("programme"))
    count = 0
    nuovi_prog = []

    for prog in all_programmes:
        if prog.get("channel") == original_id:
            np = copy.deepcopy(prog)
            np.set("channel", nuovo_id)

            for attr in ("start", "stop"):
                v = np.get(attr)
                if v:
                    np.set(attr, _shift_orario_xmltv(v, ore=1))

            count += 1
            nuovi_prog.append(np)

    for p in nuovi_prog:
        root.append(p)

    print(f"[OK] +1 CREATO: {original_id} → {nuovo_id} ({nuovo_nome}) — Programmi copiati: {count}")


def modifica_epg(root):
    """
    Rinomina e crea +1 SOLO per i canali della tua lista.
    Aggiunge metadati completi a TUTTI i canali.
    """

    # MAPPA ID REALI
    id_map = {ch.get("id").lower(): ch.get("id") for ch in root.findall("channel")}

    # RINOMINE
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

    for user_id, nome in rinomina.items():
        key = user_id.lower()
        if key in id_map:
            rinomina_canale(root, id_map[key], nome)
        else:
            print(f"[WARN] Cannot rename {user_id}: not found")

    # +1
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

    for user_id, nome in plus1.items():
        key = user_id.lower()
        if key in id_map:
            real = id_map[key]
            crea_canale_plus1(root, real, real + ".plus1", nome)
        else:
            print(f"[WARN] Cannot create +1 for {user_id}: not found")

    # METADATI COMPLETI PER TUTTI I CANALI
    for ch in root.findall("channel"):
        aggiungi_metadati_canale(ch)


# ---------------------------------------------------
# DOWNLOAD E UNIONE FEED RYTEC
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
    r = requests.get(url)
    r.raise_for_status()

    xml_data = lzma.decompress(r.content)
    feed_root = ET.fromstring(xml_data)

    for ch in feed_root.findall("channel"):
        cid = ch.get("id")
        if cid not in seen_channels:
            root_combined.append(ch)
            seen_channels.add(cid)

    for pr in feed_root.findall("programme"):
        key = (pr.get("start"), pr.get("stop"), pr.get("channel"))
        if key not in seen_programmes:
            root_combined.append(pr)
            seen_programmes.add(key)

print("Applico modifiche personalizzate...")
modifica_epg(root_combined)

# SALVA XML
tree = ET.ElementTree(root_combined)
tree.write("epg.xml", encoding="utf-8", xml_declaration=True)

# CREA COMPRESSO
with lzma.open("epg.xz", "wb") as f:
    with open("epg.xml", "rb") as infile:
        f.write(infile.read())

print("🎉 EPG generata correttamente e compatibile con TiviMate!")
