import requests

# URL EPG Rytec (Sky Italia)
URL = "http://www.xmltvepg.nl/rytecIT_Sky.xz"
OUTPUT = "epg.xz"

print("Scarico l'EPG Rytec Italia Sky...")

try:
    r = requests.get(URL)
    r.raise_for_status()
    with open(OUTPUT, "wb") as f:
        f.write(r.content)
    print("Download completato: epg.xz")
except Exception as e:
    print("Errore durante il download:", e)

