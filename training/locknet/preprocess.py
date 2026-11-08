"""Metin ön işleme.

Bu dosyadaki her kural `extension/lib/preprocess.js` içinde birebir aynı
şekilde uygulanır. Bir kuralı değiştirirsen ikisini birlikte değiştir;
`tests/test_parity.py` iki tarafın çıktısını binlerce örnekte karşılaştırır.

Kurallar sırasıyla:
1. Unicode NFC.
2. Adresler -> " url ", @kullanıcı -> " @user " (OffensEval'deki @USER/URL ile aynı).
3. Türkçe küçük harf: I -> ı, İ -> i (Python'un lower() fonksiyonu bunu bilmez).
4. Harf + rakam karışık kelimelerde leet çözümü: g3rizek4li -> gerizekali.
5. Kelime içindeki . * _ - ' işaretlerini sil: s.ktir -> sktir, ali'nin -> alinin.
6. İzin verilen karakterler dışındaki her şey boşluk.
7. Üçten fazla tekrar eden harfi ikiye indir: çoooook -> çook.
8. Boşlukla ayrılmış tek harfleri birleştir: a p t a l -> aptal.
"""

from __future__ import annotations

import re
import unicodedata

HARFLER = "a-zçğıöşüâîû"
HARF_RAKAM = HARFLER + "0-9"

# Python ve JS'de \s farklı karakterleri kapsar; bu yüzden boşluk kümesi elle tanımlı.
BOSLUK_KUMESI = "\t\n\v\f\r \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff\u001c-\u001f"
TUM_BOSLUK_RE = re.compile(f"[{BOSLUK_KUMESI}]+")
URL_RE = re.compile(r"(?:https?://|www\.|pic\.twitter\.com/)[^ ]+", re.IGNORECASE)
MENTION_RE = re.compile(r"(^| )@[A-Za-z0-9_]+")
LEET = {"4": "a", "@": "a", "3": "e", "1": "i", "0": "o", "5": "s", "$": "s", "7": "t", "9": "g"}
LEET_KARAKTER = "".join(LEET)
LEET_TOKEN_RE = re.compile(rf"[{HARF_RAKAM}@$]+")
ICERIDEKI_ISARET_RE = re.compile(rf"(?<=[{HARF_RAKAM}])[.*_'’`\-]+(?=[{HARF_RAKAM}])")
IZINSIZ_RE = re.compile(rf"[^{HARF_RAKAM}@ ]")
TEKRAR_RE = re.compile(rf"([{HARFLER}])\1{{2,}}")
TEK_HARF_DIZISI_RE = re.compile(rf"(?:^|(?<= ))(?:[{HARFLER}] ){{2,}}[{HARFLER}](?= |$)")
BOSLUK_RE = re.compile(r" +")


def turkce_kucuk_harf(metin: str) -> str:
    return metin.replace("I", "ı").replace("İ", "i").lower().replace("̇", "")


def _leet_coz(token: str) -> str:
    if token == "@user":
        return token
    harf_var = any(c.isalpha() for c in token)
    leet_var = any(c in LEET_KARAKTER for c in token)
    # "15temmuz", "2023te" gibi sayı ile başlayan ifadelere dokunma.
    if not (harf_var and leet_var) or re.match(r"[0-9]{2,}", token):
        return token
    return "".join(LEET.get(c, c) for c in token)


def on_isle(metin: str) -> str:
    metin = unicodedata.normalize("NFC", str(metin))
    metin = TUM_BOSLUK_RE.sub(" ", metin)
    metin = URL_RE.sub(" url ", metin)
    metin = MENTION_RE.sub(lambda m: m.group(1) + " @user ", metin)
    metin = turkce_kucuk_harf(metin)
    metin = ICERIDEKI_ISARET_RE.sub("", metin)
    metin = LEET_TOKEN_RE.sub(lambda m: _leet_coz(m.group(0)), metin)
    metin = IZINSIZ_RE.sub(" ", metin)
    metin = BOSLUK_RE.sub(" ", metin).strip()
    # @ yalnızca "@user" içinde kalır; kelime ortasında kalan @ leet olarak çözüldü.
    metin = " ".join(t if t == "@user" else t.replace("@", " ") for t in metin.split(" "))
    metin = TEKRAR_RE.sub(r"\1\1", metin)
    metin = BOSLUK_RE.sub(" ", metin).strip()
    metin = TEK_HARF_DIZISI_RE.sub(lambda m: m.group(0).replace(" ", ""), metin)
    return metin
