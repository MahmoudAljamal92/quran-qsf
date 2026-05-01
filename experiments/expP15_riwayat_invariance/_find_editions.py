"""Quick scratch: query alquran.cloud for available Arabic Quran editions
to find the right Warsh/Qalun/Duri identifiers."""
import json
import urllib.request

URL = "https://api.alquran.cloud/v1/edition?format=text&type=quran&language=ar"
req = urllib.request.Request(URL, headers={"User-Agent": "QSF-research/v7.9-cand"})
with urllib.request.urlopen(req, timeout=30) as r:
    j = json.loads(r.read())

editions = j.get("data", [])
print(f"Total Arabic editions: {len(editions)}")
for e in editions:
    print(f"  {e['identifier']:35s} | {e['name']}")
