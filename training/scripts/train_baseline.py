"""Taban model: hashing TF-IDF + lojistik regresyon.

Kullanım (depo kökünden):
    python training/scripts/train_baseline.py

Çıktılar:
    results/baseline.json                 ölçümler (doğrulama + test)
    extension/model/baseline/meta.json    eklentinin okuyacağı ayarlar
    extension/model/baseline/weights.bin  idf ve katsayılar (float16)
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from locknet import data, features, metrics  # noqa: E402
from locknet.preprocess import on_isle  # noqa: E402

KOK = Path(__file__).resolve().parents[2]
N_KUTU = 2**19
ZOR_ORNEKLER = Path(__file__).resolve().parents[1] / "tests" / "data" / "zor_ornekler.json"


def main() -> None:
    egitim, dogrulama, test = data.bolumler()
    Xm = {ad: [on_isle(t) for t in df.metin] for ad, df in [("egitim", egitim), ("dogrulama", dogrulama), ("test", test)]}

    vek = features.HashTfidf(n_kutu=N_KUTU, min_df=3).fit(Xm["egitim"])
    X = {ad: vek.transform(m) for ad, m in Xm.items()}

    # Hiperparametre araması yalnızca doğrulama setinde.
    deneme = []
    for C in (1, 2, 4, 8, 16):
        for agirlik in (None, "balanced"):
            m = LogisticRegression(C=C, class_weight=agirlik, max_iter=4000)
            m.fit(X["egitim"], egitim.etiket)
            s = m.predict_proba(X["dogrulama"])[:, 1]
            e = metrics.esik_sec(dogrulama.etiket, s)
            deneme.append({"C": C, "class_weight": agirlik, **metrics.olc(dogrulama.etiket, s, e)})
            print(deneme[-1])
    en_iyi = max(deneme, key=lambda d: d["macro_f1"])
    model = LogisticRegression(C=en_iyi["C"], class_weight=en_iyi["class_weight"], max_iter=4000)
    model.fit(X["egitim"], egitim.etiket)

    s_dog = model.predict_proba(X["dogrulama"])[:, 1]
    esik = metrics.esik_sec(dogrulama.etiket, s_dog)
    esik_temkinli = metrics.esik_sec(dogrulama.etiket, s_dog, en_fazla_yanlis_alarm=0.02)

    t0 = time.perf_counter()
    s_test = model.predict_proba(vek.transform([on_isle(t) for t in test.metin]))[:, 1]
    sure_ms = (time.perf_counter() - t0) * 1000 / len(test)

    sonuc = {
        "model": "hashing TF-IDF (karakter 2-5 + kelime 1-2) + lojistik regresyon",
        "kutu_sayisi": N_KUTU,
        "secilen": {"C": en_iyi["C"], "class_weight": en_iyi["class_weight"]},
        "hiperparametre_aramasi": deneme,
        "dogrulama": metrics.olc(dogrulama.etiket, s_dog, esik),
        "test": metrics.olc(test.etiket, s_test, esik),
        "test_temkinli_esik": metrics.olc(test.etiket, s_test, esik_temkinli),
        "python_ms_cumle": round(sure_ms, 3),
    }

    if ZOR_ORNEKLER.exists():
        zor = json.loads(ZOR_ORNEKLER.read_text(encoding="utf-8"))
        zs = model.predict_proba(vek.transform([on_isle(z["metin"]) for z in zor]))[:, 1]
        sonuc["zor_ornekler"] = [{**z, "skor": round(float(p), 3)} for z, p in zip(zor, zs)]
        sonuc["zor_ornek_dogruluk"] = round(float(np.mean([(p >= esik) == bool(z["etiket"]) for z, p in zip(zor, zs)])), 3)

    # Eklenti için dışa aktarım: yalnızca kullanılan kutular sıfırdan farklı.
    cikti = KOK / "extension" / "model" / "baseline"
    cikti.mkdir(parents=True, exist_ok=True)
    idf = vek.idf.astype(np.float16)
    katsayi = model.coef_.ravel().astype(np.float16)
    (cikti / "weights.bin").write_bytes(idf.tobytes() + katsayi.tobytes())
    meta = {
        "tur": "hash-tfidf-lr",
        "surum": 1,
        "kutu_sayisi": N_KUTU,
        "karakter_ngram": [features.CHAR_MIN, features.CHAR_MAX],
        "kelime_ngram": [1, features.WORD_MAX],
        "sabit": float(model.intercept_[0]),
        "esik": esik,
        "esik_temkinli": esik_temkinli,
        "agirliklar": "weights.bin: float16 idf[kutu_sayisi] + float16 katsayi[kutu_sayisi], little-endian",
    }
    (cikti / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    sonuc["eklenti_boyutu_kb"] = round((cikti / "weights.bin").stat().st_size / 1024)

    (KOK / "results").mkdir(exist_ok=True)
    (KOK / "results" / "baseline.json").write_text(json.dumps(sonuc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: sonuc[k] for k in ("secilen", "dogrulama", "test", "test_temkinli_esik", "eklenti_boyutu_kb")}, indent=2))


if __name__ == "__main__":
    main()
