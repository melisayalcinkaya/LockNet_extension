"""Eklentiye giden int8 ONNX modellerini, tarayıcıdaki yöntemle (tek cümle,
dolgusuz) yeniden ölçer; eşikleri doğrulama setinde yeniden seçer.

Kullanım: python training/scripts/olc_onnx.py [bert-kısa-ad ...]
(argüman verilmezse extension/model/bert-* klasörlerinin hepsi)

Günceller: extension/model/bert-*/meta.json (esik, esik_temkinli)
           results/bert-*.json (int8_* alanları)
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from locknet import data, metrics  # noqa: E402
from locknet.onnx_skor import OnnxBert  # noqa: E402

KOK = Path(__file__).resolve().parents[2]


def olc(dizin: Path, dogrulama, test) -> None:
    m = OnnxBert(dizin)
    s_dog = m.skorla(list(dogrulama.metin))
    esik = metrics.esik_sec(dogrulama.etiket, s_dog)
    esik_t = metrics.esik_sec(dogrulama.etiket, s_dog, en_fazla_yanlis_alarm=0.02)
    t0 = time.perf_counter()
    s_test = m.skorla(list(test.metin))
    ms = (time.perf_counter() - t0) * 1000 / len(test)

    meta = {**m.meta, "esik": esik, "esik_temkinli": esik_t, "parti": 1}
    (dizin / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    yol = KOK / "results" / f"{dizin.name}.json"
    sonuc = json.loads(yol.read_text())
    sonuc.pop("int8_ms_cumle_parti64", None)
    sonuc["int8_test"] = metrics.olc(test.etiket, s_test, esik)
    sonuc["int8_test_temkinli_esik"] = metrics.olc(test.etiket, s_test, esik_t)
    sonuc["int8_ms_cumle_tekli"] = round(ms, 3)
    sonuc["int8_not"] = "int8 skorları tek cümle, dolgusuz hesaplandı (tarayıcıdaki gibi); bkz. training/locknet/onnx_skor.py"
    yol.write_text(json.dumps(sonuc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(dizin.name, json.dumps({"int8_test": sonuc["int8_test"], "ms": sonuc["int8_ms_cumle_tekli"]}, ensure_ascii=False), flush=True)


def main() -> None:
    _, dogrulama, test = data.bolumler()
    adlar = sys.argv[1:] or sorted(p.name for p in (KOK / "extension" / "model").glob("bert-*"))
    for ad in adlar:
        olc(KOK / "extension" / "model" / ad, dogrulama, test)


if __name__ == "__main__":
    main()
