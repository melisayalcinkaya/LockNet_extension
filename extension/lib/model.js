// Taban model (hashing TF-IDF + lojistik regresyon) için tarayıcı içi tahmin.
// Hiçbir metin dışarı gönderilmez; her şey bu dosyada, kullanıcının tarayıcısında hesaplanır.
(function (kok) {
  "use strict";

  const onIsleme = typeof module !== "undefined" ? require("./preprocess.js") : kok.LockNetOnIsleme;
  const ozellik = typeof module !== "undefined" ? require("./features.js") : kok.LockNetOzellik;

  // IEEE 754 yarım duyarlıklı (float16) sayıyı float32'ye çevir.
  function float16Dizisi(tampon, bayt, adet) {
    const g = new DataView(tampon, bayt, adet * 2);
    const cikti = new Float32Array(adet);
    for (let i = 0; i < adet; i++) {
      const h = g.getUint16(i * 2, true);
      const isaret = h & 0x8000 ? -1 : 1;
      const us = (h >> 10) & 0x1f;
      const kesir = h & 0x3ff;
      let v;
      if (us === 0) v = kesir * 2 ** -24;
      else if (us === 31) v = kesir ? NaN : Infinity;
      else v = (1 + kesir / 1024) * 2 ** (us - 15);
      cikti[i] = isaret * v;
    }
    return cikti;
  }

  function modelOlustur(meta, agirlikTamponu) {
    const n = meta.kutu_sayisi;
    const idf = float16Dizisi(agirlikTamponu, 0, n);
    const katsayi = float16Dizisi(agirlikTamponu, n * 2, n);

    function skor(hamMetin) {
      const metin = onIsleme.onIsle(hamMetin);
      let nokta = 0;
      let kare = 0;
      for (const [k, c] of ozellik.sayim(metin, n)) {
        const w = idf[k];
        if (w === 0) continue;
        const v = (1 + Math.log(c)) * w;
        kare += v * v;
        nokta += v * katsayi[k];
      }
      const z = meta.sabit + (kare > 0 ? nokta / Math.sqrt(kare) : 0);
      return 1 / (1 + Math.exp(-z));
    }

    return { meta, skor, esik: meta.esik, esikTemkinli: meta.esik_temkinli };
  }

  async function yukle(metaUrl, agirlikUrl) {
    const meta = await (await fetch(metaUrl)).json();
    const tampon = await (await fetch(agirlikUrl)).arrayBuffer();
    return modelOlustur(meta, tampon);
  }

  const api = { modelOlustur, yukle, float16Dizisi };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else kok.LockNetModel = api;
})(typeof self !== "undefined" ? self : this);
