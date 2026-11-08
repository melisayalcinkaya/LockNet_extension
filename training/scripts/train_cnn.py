"""CNN modeli: karakter dalı + kelime-hash dalı (Kim-CNN tarzı).

Melisa'nın v2/v3 fikirlerinin (çoklu çekirdek boyutu, karakter dalı) temiz
veriyle yeniden denenmesi. Kelime dalı da sözlük yerine MurmurHash kutuları
kullanır; eklentiye kelime listesi gitmez.

Kullanım (depo kökünden):  python training/scripts/train_cnn.py
Çıktı: results/cnn.json, training/runs/cnn/model.pt
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn
from sklearn.utils import murmurhash3_32

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from locknet import data, metrics  # noqa: E402
from locknet.preprocess import on_isle  # noqa: E402

KOK = Path(__file__).resolve().parents[2]
ALFABE = " abcçdefgğhıijklmnoöpqrsştuüvwxyzâîû0123456789@"
KARAKTER_ID = {c: i + 2 for i, c in enumerate(ALFABE)}  # 0 = dolgu, 1 = bilinmeyen
MAKS_KARAKTER = 240
MAKS_KELIME = 48
KELIME_KUTU = 2**15
SEED = 42


def kodla(metinler):
    k = np.zeros((len(metinler), MAKS_KARAKTER), dtype=np.int64)
    w = np.zeros((len(metinler), MAKS_KELIME), dtype=np.int64)
    for r, m in enumerate(metinler):
        for i, c in enumerate(m[:MAKS_KARAKTER]):
            k[r, i] = KARAKTER_ID.get(c, 1)
        for i, kelime in enumerate(m.split(" ")[:MAKS_KELIME]):
            if kelime:
                w[r, i] = 1 + murmurhash3_32("w:" + kelime, seed=0, positive=True) % (KELIME_KUTU - 1)
    return torch.from_numpy(k), torch.from_numpy(w)


class LockNetCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.kar_emb = nn.Embedding(len(ALFABE) + 2, 32, padding_idx=0)
        self.kar_conv = nn.ModuleList([nn.Conv1d(32, 96, k, padding=k // 2) for k in (3, 5, 7)])
        self.kel_emb = nn.Embedding(KELIME_KUTU, 64, padding_idx=0)
        self.kel_conv = nn.ModuleList([nn.Conv1d(64, 64, k, padding=k // 2) for k in (1, 2, 3)])
        self.bas = nn.Sequential(nn.Dropout(0.5), nn.Linear(96 * 3 + 64 * 3, 64), nn.ReLU(), nn.Dropout(0.3), nn.Linear(64, 1))
        self.emb_dropout = nn.Dropout(0.2)

    @staticmethod
    def _havuz(x, maske, convlar):
        cikti = []
        for c in convlar:
            h = torch.relu(c(x))[:, :, : maske.shape[1]]
            h = h.masked_fill(~maske[:, None, :], -1e4)
            cikti.append(h.max(dim=2).values.clamp(min=0))
        return cikti

    def forward(self, kar, kel):
        a = self.emb_dropout(self.kar_emb(kar)).transpose(1, 2)
        b = self.emb_dropout(self.kel_emb(kel)).transpose(1, 2)
        oz = self._havuz(a, kar > 0, self.kar_conv) + self._havuz(b, kel > 0, self.kel_conv)
        return self.bas(torch.cat(oz, dim=1)).squeeze(1)


def tahmin(model, kar, kel, parti=512):
    model.eval()
    with torch.no_grad():
        return torch.cat([torch.sigmoid(model(kar[i : i + parti], kel[i : i + parti])) for i in range(0, len(kar), parti)]).numpy()


def main() -> None:
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    torch.set_num_threads(max(1, torch.get_num_threads()))
    egitim, dogrulama, test = data.bolumler()
    X = {ad: kodla([on_isle(t) for t in df.metin]) for ad, df in [("egitim", egitim), ("dogrulama", dogrulama), ("test", test)]}
    y_egitim = torch.tensor(egitim.etiket.values, dtype=torch.float32)

    model = LockNetCNN()
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-4)
    pozitif_agirlik = torch.tensor((y_egitim == 0).sum() / (y_egitim == 1).sum())
    kayip_fn = nn.BCEWithLogitsLoss(pos_weight=pozitif_agirlik.sqrt())

    en_iyi, en_iyi_durum, sabir, gecmis = -1.0, None, 0, []
    n = len(y_egitim)
    for epok in range(1, 21):
        model.train()
        t0 = time.time()
        sira = torch.randperm(n)
        toplam = 0.0
        for i in range(0, n, 64):
            idx = sira[i : i + 64]
            opt.zero_grad()
            kayip = kayip_fn(model(X["egitim"][0][idx], X["egitim"][1][idx]), y_egitim[idx])
            kayip.backward()
            opt.step()
            toplam += kayip.item() * len(idx)
        s = tahmin(model, *X["dogrulama"])
        e = metrics.esik_sec(dogrulama.etiket, s)
        m = metrics.olc(dogrulama.etiket, s, e)
        gecmis.append({"epok": epok, "egitim_kaybi": round(toplam / n, 4), "sure_sn": round(time.time() - t0, 1), **m})
        print(gecmis[-1], flush=True)
        if m["macro_f1"] > en_iyi:
            en_iyi, sabir = m["macro_f1"], 0
            en_iyi_durum = {k: v.clone() for k, v in model.state_dict().items()}
        else:
            sabir += 1
            if sabir >= 4:
                break

    model.load_state_dict(en_iyi_durum)
    s_dog = tahmin(model, *X["dogrulama"])
    esik = metrics.esik_sec(dogrulama.etiket, s_dog)
    esik_temkinli = metrics.esik_sec(dogrulama.etiket, s_dog, en_fazla_yanlis_alarm=0.02)
    t0 = time.perf_counter()
    s_test = tahmin(model, *kodla([on_isle(t) for t in test.metin]))
    sure_ms = (time.perf_counter() - t0) * 1000 / len(test)

    parametre = sum(p.numel() for p in model.parameters())
    sonuc = {
        "model": "CNN: karakter (3,5,7) + kelime-hash (1,2,3) dalları",
        "parametre": parametre,
        "float16_boyut_kb": round(parametre * 2 / 1024),
        "gecmis": gecmis,
        "dogrulama": metrics.olc(dogrulama.etiket, s_dog, esik),
        "test": metrics.olc(test.etiket, s_test, esik),
        "test_temkinli_esik": metrics.olc(test.etiket, s_test, esik_temkinli),
        "python_ms_cumle": round(sure_ms, 3),
    }
    zor_yol = KOK / "training" / "tests" / "data" / "zor_ornekler.json"
    zor = json.loads(zor_yol.read_text(encoding="utf-8"))
    zs = tahmin(model, *kodla([on_isle(z["metin"]) for z in zor]))
    sonuc["zor_ornekler"] = [{**z, "skor": round(float(p), 3)} for z, p in zip(zor, zs)]
    sonuc["zor_ornek_dogruluk"] = round(float(np.mean([(p >= esik) == bool(z["etiket"]) for z, p in zip(zor, zs)])), 3)

    (KOK / "results").mkdir(exist_ok=True)
    (KOK / "results" / "cnn.json").write_text(json.dumps(sonuc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    kayit = KOK / "training" / "runs" / "cnn"
    kayit.mkdir(parents=True, exist_ok=True)
    torch.save({"durum": model.state_dict(), "esik": esik, "esik_temkinli": esik_temkinli}, kayit / "model.pt")
    print(json.dumps({k: sonuc[k] for k in ("parametre", "dogrulama", "test", "test_temkinli_esik")}, indent=2))


if __name__ == "__main__":
    main()
