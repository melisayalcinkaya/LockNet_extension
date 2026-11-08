"""Modelleri Melisa'nın etiketlediği web test setinde ölçer.

Web test seti (cümleler) depoya konmaz: içinde forum ve sözlük
kullanıcılarının yazıları var. Yalnızca toplu ölçümler `results/web.json`
dosyasına yazılır.

Kullanım: python training/scripts/eval_web.py <etiketli.jsonl>
Her satır: {"metin": ..., "etiket": 1|0|-1, "neden": "rastgele"|"kelime"|"model"}
(-1 = "emin değilim", ölçüme katılmaz)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from locknet import metrics  # noqa: E402
from locknet.features import HashTfidf  # noqa: E402
from locknet.preprocess import on_isle  # noqa: E402

KOK = Path(__file__).resolve().parents[2]
MODELLER = KOK / "extension" / "model"


def taban_skor(dizin: Path, metinler):
    meta = json.loads((dizin / "meta.json").read_text())
    n = meta["kutu_sayisi"]
    w = np.frombuffer((dizin / "weights.bin").read_bytes(), dtype="<f2").astype(np.float32)
    v = HashTfidf(n_kutu=n)
    v.idf = w[:n]
    X = v.transform([on_isle(t) for t in metinler])
    return meta, 1 / (1 + np.exp(-(X @ w[n:] + meta["sabit"])))


def bert_skor(dizin: Path, metinler):
    import onnxruntime as ort
    from tokenizers import Tokenizer

    meta = json.loads((dizin / "meta.json").read_text())
    tok = Tokenizer.from_file(str(dizin / "tokenizer.json"))
    tok.enable_truncation(meta["maks_uzunluk"])
    tok.enable_padding()
    oturum = ort.InferenceSession(str(dizin / "model.onnx"))
    skor = []
    for i in range(0, len(metinler), 64):
        k = tok.encode_batch([on_isle(t) for t in metinler[i : i + 64]])
        ids = np.array([e.ids for e in k], dtype=np.int64)
        maske = np.array([e.attention_mask for e in k], dtype=np.int64)
        lg = oturum.run(None, {"input_ids": ids, "attention_mask": maske})[0]
        e = np.exp(lg - lg.max(1, keepdims=True))
        skor.append(e[:, 1] / e.sum(1))
    return meta, np.concatenate(skor)


def main(yol: str) -> None:
    satirlar = [json.loads(s) for s in Path(yol).read_text(encoding="utf-8").splitlines() if s.strip()]
    satirlar = [s for s in satirlar if s["etiket"] in (0, 1)]
    metinler = [s["metin"] for s in satirlar]
    y = np.array([s["etiket"] for s in satirlar])
    rastgele = np.array([s["neden"] == "rastgele" for s in satirlar])
    sonuc = {
        "aciklama": "Türkçe sitelerden toplanan metin blokları; Melisa etiketledi. Yanlış alarm (rastgele) yalnızca rastgele seçilen bloklarda ölçülür.",
        "cumle": int(len(y)),
        "saldirgan": int(y.sum()),
        "rastgele_cumle": int(rastgele.sum()),
        "modeller": {},
    }
    for dizin in sorted(MODELLER.iterdir()):
        if not (dizin / "meta.json").exists():
            continue
        meta, s = (taban_skor if dizin.name == "baseline" else bert_skor)(dizin, metinler)
        kayit = {}
        for ad, e in (("esik", meta["esik"]), ("temkinli", meta["esik_temkinli"])):
            m = metrics.olc(y, s, e)
            t = s >= e
            m["yanlis_alarm_rastgele"] = round(float(t[rastgele & (y == 0)].mean()), 4)
            kayit[ad] = m
        sonuc["modeller"][dizin.name] = kayit
        print(dizin.name, json.dumps(kayit, ensure_ascii=False))
    (KOK / "results").mkdir(exist_ok=True)
    (KOK / "results" / "web.json").write_text(json.dumps(sonuc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
