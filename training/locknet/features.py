"""Hashing tabanlı TF-IDF özellikleri.

Sözlük yerine her n-gram'ı MurmurHash3 ile sabit sayıda kutuya (bucket)
dağıtıyoruz. İki faydası var:
- Eklentiye kelime listesi gitmez; eğitim verisindeki kullanıcı adları,
  isimler vb. modelden okunamaz (eski sözlükte gerçek kullanıcı adları vardı).
- Model dosyası küçük ve boyutu sabit kalır.

Aynı mantık `extension/lib/features.js` içinde birebir uygulanır.
Özellikler:
- karakter n-gram (2-5), her kelime " kelime " olarak çevrelenir
  (scikit-learn'deki analyzer="char_wb" ile aynı kural)
- kelime unigram + bigram
Önekler ("c:" / "w:") iki türün aynı kutuya düşmesini azaltır.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse
from sklearn.utils import murmurhash3_32

CHAR_MIN, CHAR_MAX = 2, 5
WORD_MAX = 2


def ngramlar(metin: str) -> list[str]:
    """Ön işlenmiş metnin tüm n-gram'ları (tekrarlar dahil)."""
    kelimeler = [k for k in metin.split(" ") if k]
    cikti: list[str] = []
    for kelime in kelimeler:
        w = " " + kelime + " "
        for n in range(CHAR_MIN, CHAR_MAX + 1):
            if len(w) < n:
                break
            for i in range(len(w) - n + 1):
                cikti.append("c:" + w[i : i + n])
    for n in range(1, WORD_MAX + 1):
        for i in range(len(kelimeler) - n + 1):
            cikti.append("w:" + " ".join(kelimeler[i : i + n]))
    return cikti


def kutu(ngram: str, n_kutu: int) -> int:
    return murmurhash3_32(ngram, seed=0, positive=True) % n_kutu


def sayim_matrisi(metinler, n_kutu: int) -> sparse.csr_matrix:
    satirlar, sutunlar = [], []
    for r, metin in enumerate(metinler):
        for g in ngramlar(metin):
            satirlar.append(r)
            sutunlar.append(kutu(g, n_kutu))
    veri = np.ones(len(satirlar), dtype=np.float32)
    m = sparse.csr_matrix((veri, (satirlar, sutunlar)), shape=(len(metinler), n_kutu))
    m.sum_duplicates()
    return m


class HashTfidf:
    """sublinear tf (1 + log tf) * idf, sonra L2 normalizasyonu.

    min_df altında kalan kutuların idf'i 0 yapılır (özellik yok sayılır).
    """

    def __init__(self, n_kutu: int = 2**19, min_df: int = 3):
        self.n_kutu = n_kutu
        self.min_df = min_df
        self.idf: np.ndarray | None = None

    def fit(self, metinler):
        m = sayim_matrisi(metinler, self.n_kutu)
        df = np.bincount(m.indices, minlength=self.n_kutu)
        n = m.shape[0]
        idf = np.log((1 + n) / (1 + df)) + 1.0
        idf[df < self.min_df] = 0.0
        self.idf = idf.astype(np.float32)
        return self

    def transform(self, metinler) -> sparse.csr_matrix:
        m = sayim_matrisi(metinler, self.n_kutu)
        m.data = 1.0 + np.log(m.data)
        m = m @ sparse.diags(self.idf)
        m = m.tocsr()
        m.eliminate_zeros()
        normlar = np.sqrt(np.asarray(m.multiply(m).sum(axis=1)).ravel())
        normlar[normlar == 0] = 1.0
        return sparse.diags(1.0 / normlar) @ m

    def fit_transform(self, metinler):
        return self.fit(metinler).transform(metinler)
