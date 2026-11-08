"""Python (eğitim) ile JS (eklenti) aynı girdide aynı sonucu üretmeli.

Eğitimde model bir şey görür, eklentide başka bir şey görürse model sahada
bozulur; eski LockNet'teki sorunlardan biri buydu.
"""

import json
import random
from pathlib import Path

import numpy as np
import pytest

from locknet.features import ngramlar
from locknet.preprocess import on_isle
from sklearn.utils import murmurhash3_32

ZOR = Path(__file__).with_name("data") / "zor_ornekler.json"
KOK = Path(__file__).resolve().parents[2]
MODEL = KOK / "extension" / "model" / "baseline"

KARAKTERLER = (
    "abcçdefgğhıijklmnoöprsştuüvyzABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ"
    "0123456789 .,!?*_-'’`@#$%&()/:;\"\t\n ̇éàâîûÂÎÛßẞΣσςΙ"
    "😂🤬👍​﻿ "
)


def ornek_metinler():
    rnd = random.Random(7)
    metinler = [z["metin"] for z in json.loads(ZOR.read_text(encoding="utf-8"))]
    for _ in range(3000):
        n = rnd.randint(0, 60)
        metinler.append("".join(rnd.choice(KARAKTERLER) for _ in range(n)))
    sablonlar = ["@{} selam", "http://{}.com bak", "{} {} {}", "{}'nin", "s.{}.k", "{}1{}3"]
    kelimeler = ["salak", "İstanbul", "IŞIK", "g3rizekali", "amk", "çoooook", "a", "o"]
    for _ in range(1000):
        s = rnd.choice(sablonlar)
        metinler.append(s.format(*(rnd.choice(kelimeler) for _ in range(s.count("{}")))))
    return metinler


METINLER = ornek_metinler()


def test_on_isleme_ayni(js):
    py = [on_isle(m) for m in METINLER]
    assert js("on_isle", METINLER) == py


def test_hash_ayni(js):
    islenmis = [on_isle(m) for m in METINLER[:800]]
    py = [[murmurhash3_32(g, seed=0, positive=True) for g in ngramlar(m)] for m in islenmis]
    assert js("hash", islenmis) == py


@pytest.mark.skipif(not (MODEL / "meta.json").exists(), reason="model henüz eğitilmedi")
def test_model_skoru_ayni(js):
    from locknet.features import HashTfidf

    meta = json.loads((MODEL / "meta.json").read_text())
    n = meta["kutu_sayisi"]
    w = np.frombuffer((MODEL / "weights.bin").read_bytes(), dtype="<f2").astype(np.float32)
    vek = HashTfidf(n_kutu=n)
    vek.idf = w[:n]
    X = vek.transform([on_isle(m) for m in METINLER])
    py = 1 / (1 + np.exp(-(X @ w[n:] + meta["sabit"])))
    js_skor = np.array(js("skor", METINLER, model_dizini="extension/model/baseline"))
    assert np.max(np.abs(js_skor - py)) < 1e-4
