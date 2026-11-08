"""Tüm modeller için ortak değerlendirme."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score

ESIKLER = np.round(np.arange(0.05, 0.96, 0.01), 2)


def olc(y, skor, esik: float) -> dict:
    y = np.asarray(y)
    tahmin = np.asarray(skor) >= esik
    temiz = y == 0
    return {
        "esik": float(esik),
        "macro_f1": round(float(f1_score(y, tahmin, average="macro")), 4),
        "f1_saldirgan": round(float(f1_score(y, tahmin)), 4),
        "precision": round(float(precision_score(y, tahmin, zero_division=0)), 4),
        "recall": round(float(recall_score(y, tahmin)), 4),
        # Temiz metinlerin yüzde kaçı yanlışlıkla işaretlendi (eklentide bulanıklaşan temiz metin).
        "yanlis_alarm": round(float(tahmin[temiz].mean()), 4),
        "roc_auc": round(float(roc_auc_score(y, skor)), 4),
    }


def esik_sec(y, skor, en_fazla_yanlis_alarm: float | None = None) -> float:
    """Doğrulama setinde macro F1'i en yüksek yapan eşik.

    en_fazla_yanlis_alarm verilirse, yalnızca o sınırın altında kalan eşikler arasından seçer.
    """
    y = np.asarray(y)
    skor = np.asarray(skor)
    en_iyi, en_iyi_esik = -1.0, 0.5
    for e in ESIKLER:
        t = skor >= e
        if en_fazla_yanlis_alarm is not None and t[y == 0].mean() > en_fazla_yanlis_alarm:
            continue
        f = f1_score(y, t, average="macro")
        if f > en_iyi:
            en_iyi, en_iyi_esik = f, float(e)
    return en_iyi_esik
