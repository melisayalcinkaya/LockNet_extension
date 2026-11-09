"""Chrome Web Store'a yüklenecek zip dosyasını hazırlar.

Kullanım (depo kökünden): python scripts/paketle.py
Çıktı: dist/locknet-<sürüm>.zip

Pakete yalnızca model/secim.json'da seçili model girer; diğer modeller ve
geliştirme dosyaları dışarıda kalır.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
EKLENTI = KOK / "extension"


def main() -> None:
    surum = json.loads((EKLENTI / "manifest.json").read_text(encoding="utf-8"))["version"]
    secili = json.loads((EKLENTI / "model" / "secim.json").read_text())["dizin"]
    hedef = KOK / "dist" / f"locknet-{surum}.zip"
    hedef.parent.mkdir(exist_ok=True)

    dosyalar = []
    for yol in sorted(EKLENTI.rglob("*")):
        if not yol.is_file():
            continue
        goreli = yol.relative_to(EKLENTI)
        parcalar = goreli.parts
        if parcalar[0] == "model" and len(parcalar) > 2 and parcalar[1] != secili:
            continue
        if yol.name.startswith(".") or yol.suffix in {".md", ".map"}:
            continue
        dosyalar.append((yol, goreli))

    with zipfile.ZipFile(hedef, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for yol, goreli in dosyalar:
            z.write(yol, goreli.as_posix())
    print(f"{hedef.relative_to(KOK)}: {len(dosyalar)} dosya, {hedef.stat().st_size / 2**20:.1f} MB (model: {secili})")


if __name__ == "__main__":
    main()
