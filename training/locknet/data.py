"""OffensEval-2020 Türkçe veri seti (Çöltekin, LREC 2020, CC-BY).

Veri depoya konmaz; ilk kullanımda Hugging Face'ten indirilip
`data/cache/` altına yazılır.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

KOK = Path(__file__).resolve().parents[2]
ONBELLEK = KOK / "data" / "cache"
HF_DEPO = "coltekin/offenseval2020_tr"
HF_REVIZYON = "refs/convert/parquet"
DOSYALAR = {
    "train": "offenseval2020-turkish/train/0000.parquet",
    "test": "offenseval2020-turkish/test/0000.parquet",
}


def _parquet(bolum: str) -> Path:
    yerel = ONBELLEK / f"offenseval_{bolum}.parquet"
    if not yerel.exists():
        from huggingface_hub import hf_hub_download

        ONBELLEK.mkdir(parents=True, exist_ok=True)
        indirilen = hf_hub_download(HF_DEPO, DOSYALAR[bolum], repo_type="dataset", revision=HF_REVIZYON)
        yerel.write_bytes(Path(indirilen).read_bytes())
    return yerel


def offenseval(bolum: str) -> pd.DataFrame:
    """Sütunlar: id, metin, etiket (1 = saldırgan)."""
    df = pd.read_parquet(_parquet(bolum))
    return df.rename(columns={"tweet": "metin", "subtask_a": "etiket"})[["id", "metin", "etiket"]]


def bolumler(seed: int = 42, dogrulama_orani: float = 0.1):
    """train -> (egitim, dogrulama); test hiç dokunulmadan ayrı döner.

    Eşik ve hiperparametreler yalnızca doğrulama setinde seçilir; test seti
    sadece en sonda, bir kez ölçmek için kullanılır.
    """
    train = offenseval("train")
    test = offenseval("test")
    egitim, dogrulama = train_test_split(
        train, test_size=dogrulama_orani, random_state=seed, stratify=train["etiket"]
    )
    return egitim.reset_index(drop=True), dogrulama.reset_index(drop=True), test
