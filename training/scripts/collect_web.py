"""Web test seti için Türkçe sayfalardan metin blokları toplar.

Eklentinin göreceği şeyi taklit eder: sayfadaki p/li/h1-h3/span/div
öğelerinden 5-200 karakterlik metinler. robots.txt'e uyar, site başına
saniyede en fazla bir istek atar, yalnızca birkaç sayfa okur.

Kullanım: python training/scripts/collect_web.py ci-out/web_bloklari.jsonl [--odak]
(--odak: yalnızca sözlük/forum/şikâyet sitelerinde konu sayfalarına girer)
"""

from __future__ import annotations

import json
import random
import re
import sys
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

AJAN = "LockNetTestSetBot/0.1 (+https://github.com/melisayalcinkaya/LockNet_extension)"
BASLANGIC = {
    "haber": [
        "https://www.bbc.com/turkce",
        "https://www.ntv.com.tr/",
        "https://www.sozcu.com.tr/",
        "https://www.hurriyet.com.tr/",
        "https://www.trthaber.com/",
    ],
    "spor": ["https://www.fanatik.com.tr/", "https://www.sporx.com/"],
    "sozluk": ["https://eksisozluk.com/", "https://www.uludagsozluk.com/", "https://www.incisozluk.com.tr/"],
    "forum": ["https://forum.donanimhaber.com/", "https://www.technopat.net/sosyal/", "https://www.kizlarsoruyor.com/"],
    "sikayet_yorum": ["https://www.sikayetvar.com/", "https://www.hepsiburada.com/"],
    "ansiklopedi": ["https://tr.wikipedia.org/wiki/%C3%96zel:Rastgele"],
}
SAYFA_SITE_BASI = 12
# İkinci tur: yorum/entry sayfalarına odaklan (adres kalıbı, sayfa sayısı).
ODAK = {
    "eksisozluk.com": (r"--\d+", 45),
    "forum.donanimhaber.com": (r"--\d{5,}", 45),
    "www.sikayetvar.com": (r"/[a-z0-9-]+/[a-z0-9-]{25,}$", 30),
}
ETIKETLER = ["p", "li", "h1", "h2", "h3", "span", "div", "a", "td"]
BLOK_ICI = {"p", "div", "li", "ul", "ol", "table", "section", "article"}


def robot(site: str) -> RobotFileParser:
    rp = RobotFileParser()
    try:
        r = requests.get(urljoin(site, "/robots.txt"), headers={"User-Agent": AJAN}, timeout=10)
        rp.parse(r.text.splitlines() if r.ok else [])
    except requests.RequestException:
        rp.parse([])
    return rp


def bloklar(html: str) -> list[str]:
    corba = BeautifulSoup(html, "html.parser")
    for e in corba(["script", "style", "noscript", "svg", "template"]):
        e.decompose()
    cikti = []
    for e in corba.find_all(ETIKETLER):
        if any(c.name in BLOK_ICI for c in e.find_all(recursive=False)):
            continue
        t = re.sub(r"\s+", " ", e.get_text(" ", strip=True))
        if 5 < len(t) < 200:
            cikti.append(t)
    return cikti


def main(cikti_yolu: str) -> None:
    rnd = random.Random(7)
    oturum = requests.Session()
    oturum.headers["User-Agent"] = AJAN
    oturum.headers["Accept-Language"] = "tr-TR,tr;q=0.9"
    gorulen = set()
    durum = {}
    with open(cikti_yolu, "w", encoding="utf-8") as f:
        for tur, siteler in BASLANGIC.items():
            for baslangic in siteler:
                alan = urlparse(baslangic).netloc
                rp = robot(f"https://{alan}")
                kalip, sinir = ODAK.get(alan, (None, SAYFA_SITE_BASI)) if ODAK_MODU else (None, SAYFA_SITE_BASI)
                if ODAK_MODU and alan not in ODAK:
                    continue
                kuyruk, okunan, sayac = [baslangic], set(), 0
                while kuyruk and len(okunan) < sinir:
                    url = kuyruk.pop(0)
                    if url in okunan or not rp.can_fetch(AJAN, url):
                        continue
                    okunan.add(url)
                    try:
                        r = oturum.get(url, timeout=15)
                        time.sleep(1.0)
                    except requests.RequestException as e:
                        durum.setdefault(alan, []).append(f"hata {type(e).__name__}")
                        continue
                    durum.setdefault(alan, []).append(r.status_code)
                    if not r.ok or "text/html" not in r.headers.get("content-type", ""):
                        continue
                    r.encoding = r.apparent_encoding if not r.encoding or r.encoding.lower() == "iso-8859-1" else r.encoding
                    for t in bloklar(r.text):
                        if t not in gorulen:
                            gorulen.add(t)
                            sayac += 1
                            f.write(json.dumps({"metin": t, "tur": tur, "alan": alan}, ensure_ascii=False) + "\n")
                    corba = BeautifulSoup(r.text, "html.parser")
                    linkler = [urljoin(url, a["href"]).split("#")[0] for a in corba.find_all("a", href=True)]
                    linkler = [u for u in linkler if urlparse(u).netloc == alan and u not in okunan]
                    rnd.shuffle(linkler)
                    if kalip:
                        # Konu/entry sayfalarını öne al.
                        linkler.sort(key=lambda u: not re.search(kalip, urlparse(u).path))
                        kuyruk = [u for u in kuyruk if re.search(kalip, urlparse(u).path)] + [u for u in kuyruk if not re.search(kalip, urlparse(u).path)]
                    kuyruk.extend(linkler[:40])
                print(alan, "sayfa", len(okunan), "blok", sayac, "durum", durum.get(alan, [])[:6], flush=True)
    json.dump(durum, open(cikti_yolu + ".durum.json", "w"), indent=1)


ODAK_MODU = "--odak" in sys.argv

if __name__ == "__main__":
    main(sys.argv[1])
