"""Türkçe BERT ince ayarı (fine-tuning) ve tarayıcı için ONNX dışa aktarımı.

Kullanım (depo kökünden):
    python training/scripts/train_bert.py <hf-model-adı> [kısa-ad]
    ör. python training/scripts/train_bert.py ytu-ce-cosmos/turkish-mini-bert-uncased mini

Girdi, taban modelle aynı ön işlemeden geçer (Türkçe küçük harf, @user, url);
bu yüzden "uncased" modeller kullanılıyor. Eşik doğrulama setinde seçilir,
test seti bir kez ölçülür.

Çıktılar:
    results/bert-<kısa-ad>.json
    extension/model/bert-<kısa-ad>/ (model.onnx int8 + tokenizer.json + meta.json),
    yalnızca dosya 95 MB'tan küçükse (GitHub dosya sınırı 100 MB).
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from locknet import data, metrics  # noqa: E402
from locknet.preprocess import on_isle  # noqa: E402

KOK = Path(__file__).resolve().parents[2]
MAKS_UZUNLUK = 64
SEED = 42


def main() -> None:
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

    hf_ad = sys.argv[1]
    kisa = sys.argv[2] if len(sys.argv) > 2 else hf_ad.split("/")[-1]
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    torch.set_num_threads(os.cpu_count() or 2)

    egitim, dogrulama, test = data.bolumler()
    tok = AutoTokenizer.from_pretrained(hf_ad)
    model = AutoModelForSequenceClassification.from_pretrained(hf_ad, num_labels=2)
    parametre = sum(p.numel() for p in model.parameters())
    buyuk = parametre > 60_000_000
    epok_sayisi = 2 if buyuk else 4
    ogrenme = 3e-5 if buyuk else 6e-5

    def kodla(metinler):
        return tok([on_isle(t) for t in metinler], truncation=True, max_length=MAKS_UZUNLUK, padding=False)

    def yukleyici(df, karistir):
        k = kodla(df.metin)
        ornekler = [{"input_ids": a, "attention_mask": m, "labels": int(y)} for a, m, y in zip(k["input_ids"], k["attention_mask"], df.etiket)]

        def topla(parti):
            n = max(len(o["input_ids"]) for o in parti)
            ids = torch.full((len(parti), n), tok.pad_token_id)
            maske = torch.zeros((len(parti), n), dtype=torch.long)
            for i, o in enumerate(parti):
                ids[i, : len(o["input_ids"])] = torch.tensor(o["input_ids"])
                maske[i, : len(o["attention_mask"])] = 1
            return ids, maske, torch.tensor([o["labels"] for o in parti])

        return DataLoader(ornekler, batch_size=32 if karistir else 128, shuffle=karistir, collate_fn=topla)

    def skorla(yk):
        model.eval()
        cikti = []
        with torch.no_grad():
            for ids, maske, _ in yk:
                cikti.append(torch.softmax(model(input_ids=ids, attention_mask=maske).logits, -1)[:, 1])
        return torch.cat(cikti).numpy()

    egitim_yk = yukleyici(egitim, True)
    dog_yk = yukleyici(dogrulama, False)
    opt = torch.optim.AdamW(model.parameters(), lr=ogrenme, weight_decay=0.01)
    adim = epok_sayisi * len(egitim_yk)
    plan = get_linear_schedule_with_warmup(opt, int(0.06 * adim), adim)
    # Sınıf dengesizliği: saldırgan örnekler ~%19; hafif ağırlık.
    agirlik = torch.tensor([1.0, float(np.sqrt((egitim.etiket == 0).sum() / (egitim.etiket == 1).sum()))])
    kayip_fn = torch.nn.CrossEntropyLoss(weight=agirlik)

    gecmis, en_iyi, en_iyi_durum = [], -1.0, None
    for epok in range(1, epok_sayisi + 1):
        model.train()
        t0, toplam = time.time(), 0.0
        for i, (ids, maske, y) in enumerate(egitim_yk):
            opt.zero_grad()
            kayip = kayip_fn(model(input_ids=ids, attention_mask=maske).logits, y)
            kayip.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            plan.step()
            toplam += kayip.item()
            if i % 200 == 0:
                print(f"epok {epok} adım {i}/{len(egitim_yk)} kayıp {kayip.item():.4f} {time.time() - t0:.0f} sn", flush=True)
        s = skorla(dog_yk)
        e = metrics.esik_sec(dogrulama.etiket, s)
        m = metrics.olc(dogrulama.etiket, s, e)
        gecmis.append({"epok": epok, "egitim_kaybi": round(toplam / len(egitim_yk), 4), "sure_dk": round((time.time() - t0) / 60, 1), **m})
        print(gecmis[-1], flush=True)
        if m["macro_f1"] > en_iyi:
            en_iyi = m["macro_f1"]
            en_iyi_durum = {k: v.detach().clone() for k, v in model.state_dict().items()}

    model.load_state_dict(en_iyi_durum)
    s_dog = skorla(dog_yk)
    esik = metrics.esik_sec(dogrulama.etiket, s_dog)
    esik_temkinli = metrics.esik_sec(dogrulama.etiket, s_dog, en_fazla_yanlis_alarm=0.02)
    t0 = time.perf_counter()
    s_test = skorla(yukleyici(test, False))
    sure_ms = (time.perf_counter() - t0) * 1000 / len(test)

    zor = json.loads((KOK / "training" / "tests" / "data" / "zor_ornekler.json").read_text(encoding="utf-8"))
    import pandas as pd

    zs = skorla(yukleyici(pd.DataFrame({"metin": [z["metin"] for z in zor], "etiket": [z["etiket"] for z in zor]}), False))

    sonuc = {
        "model": hf_ad,
        "parametre": parametre,
        "epok": epok_sayisi,
        "ogrenme_orani": ogrenme,
        "gecmis": gecmis,
        "dogrulama": metrics.olc(dogrulama.etiket, s_dog, esik),
        "test": metrics.olc(test.etiket, s_test, esik),
        "test_temkinli_esik": metrics.olc(test.etiket, s_test, esik_temkinli),
        "python_ms_cumle_parti128": round(sure_ms, 3),
        "zor_ornekler": [{**z, "skor": round(float(p), 3)} for z, p in zip(zor, zs)],
        "zor_ornek_dogruluk": round(float(np.mean([(p >= esik) == bool(z["etiket"]) for z, p in zip(zor, zs)])), 3),
    }

    # ONNX (int8) dışa aktarım: tarayıcıda onnxruntime-web ile çalışır.
    hedef = KOK / "extension" / "model" / f"bert-{kisa}"
    hedef.mkdir(parents=True, exist_ok=True)
    gecici = KOK / "training" / "runs" / f"bert-{kisa}"
    gecici.mkdir(parents=True, exist_ok=True)
    model.eval()
    ornek = tok(["örnek bir cümle"], return_tensors="pt")
    torch.onnx.export(
        model,
        (ornek["input_ids"], ornek["attention_mask"]),
        str(gecici / "model_fp32.onnx"),
        input_names=["input_ids", "attention_mask"],
        output_names=["logits"],
        dynamic_axes={"input_ids": {0: "parti", 1: "uzunluk"}, "attention_mask": {0: "parti", 1: "uzunluk"}, "logits": {0: "parti"}},
        opset_version=17,
        dynamo=False,
    )
    from onnxruntime.quantization import QuantType, quantize_dynamic

    quantize_dynamic(str(gecici / "model_fp32.onnx"), str(gecici / "model.onnx"), weight_type=QuantType.QInt8)

    # int8 modeli de ölç: tarayıcıya giden dosya bu. Tek cümle, dolgusuz puanlanır
    # (dinamik nicemlemede skor partideki diğer cümlelere bağlı; bkz. locknet/onnx_skor.py).
    from locknet.onnx_skor import OnnxBert

    tok.save_pretrained(str(gecici / "tok"))
    (gecici / "meta.json").write_text(json.dumps({"maks_uzunluk": MAKS_UZUNLUK}))
    import shutil

    shutil.copy(gecici / "tok" / "tokenizer.json", gecici / "tokenizer.json")
    onnx8 = OnnxBert(gecici)
    s_dog8 = onnx8.skorla(list(dogrulama.metin))
    esik8 = metrics.esik_sec(dogrulama.etiket, s_dog8)
    esik8_t = metrics.esik_sec(dogrulama.etiket, s_dog8, en_fazla_yanlis_alarm=0.02)
    t0 = time.perf_counter()
    s_test8 = onnx8.skorla(list(test.metin))
    sonuc["int8_ms_cumle_tekli"] = round((time.perf_counter() - t0) * 1000 / len(test), 3)
    sonuc["int8_test"] = metrics.olc(test.etiket, s_test8, esik8)
    sonuc["int8_test_temkinli_esik"] = metrics.olc(test.etiket, s_test8, esik8_t)
    boyut = (gecici / "model.onnx").stat().st_size
    sonuc["int8_boyut_mb"] = round(boyut / 2**20, 1)

    if boyut < 95 * 2**20:
        (hedef / "model.onnx").write_bytes((gecici / "model.onnx").read_bytes())
        (hedef / "tokenizer.json").write_bytes((gecici / "tok" / "tokenizer.json").read_bytes())
        meta = {
            "tur": "bert-onnx-int8",
            "hf_model": hf_ad,
            "maks_uzunluk": MAKS_UZUNLUK,
            "esik": esik8,
            "esik_temkinli": esik8_t,
            "parti": 1,
            "girdiler": ["input_ids", "attention_mask"],
            "cikti": "logits[:, 1] softmax",
        }
        (hedef / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    else:
        sonuc["not"] = "int8 model 95 MB'tan büyük; depoya konmadı."

    (KOK / "results").mkdir(exist_ok=True)
    (KOK / "results" / f"bert-{kisa}.json").write_text(json.dumps(sonuc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: sonuc[k] for k in ("parametre", "test", "int8_test", "int8_boyut_mb", "int8_ms_cumle_parti64")}, indent=2))


if __name__ == "__main__":
    main()
