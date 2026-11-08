"""int8 ONNX BERT modeliyle puanlama — tarayıcıdakiyle aynı yöntem.

Önemli: `quantize_dynamic` ile nicemlenmiş modelde etkinleşmelerin ölçeği
(scale) her çalıştırmada bütün girdi tensörü üzerinden hesaplanır. Birden çok
cümle dolguyla aynı partiye konursa bir cümlenin skoru, yanındaki cümlelere ve
dolguya göre değişir (OffensEval'de 0.4'e varan fark ölçtük). Bu yüzden her
cümle tek başına (parti boyutu 1, dolgusuz) puanlanır; eklenti de aynısını yapar.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .preprocess import on_isle


class OnnxBert:
    def __init__(self, dizin: Path | str):
        import onnxruntime as ort
        from tokenizers import Tokenizer

        dizin = Path(dizin)
        self.meta = json.loads((dizin / "meta.json").read_text())
        self.tok = Tokenizer.from_file(str(dizin / "tokenizer.json"))
        self.tok.no_padding()
        self.tok.enable_truncation(self.meta["maks_uzunluk"])
        self.oturum = ort.InferenceSession(str(dizin / "model.onnx"))

    def skorla(self, metinler) -> np.ndarray:
        cikti = np.empty(len(metinler), dtype=np.float32)
        for i, t in enumerate(metinler):
            ids = np.array([self.tok.encode(on_isle(t)).ids], dtype=np.int64)
            lg = self.oturum.run(None, {"input_ids": ids, "attention_mask": np.ones_like(ids)})[0][0]
            cikti[i] = 1 / (1 + np.exp(lg[0] - lg[1]))
        return cikti
