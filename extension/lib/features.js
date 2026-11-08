// training/locknet/features.py ile birebir aynı n-gram ve hashing kuralları.
(function (kok) {
  "use strict";

  const CHAR_MIN = 2;
  const CHAR_MAX = 5;
  const WORD_MAX = 2;
  const kodlayici = new TextEncoder();

  // MurmurHash3 x86 32-bit (seed 0), scikit-learn'ün murmurhash3_32(positive=True) çıktısıyla aynı.
  function murmur3(metin) {
    const b = kodlayici.encode(metin);
    const n = b.length;
    const c1 = 0xcc9e2d51;
    const c2 = 0x1b873593;
    let h = 0;
    const blok = n & ~3;
    for (let i = 0; i < blok; i += 4) {
      let k = b[i] | (b[i + 1] << 8) | (b[i + 2] << 16) | (b[i + 3] << 24);
      k = Math.imul(k, c1);
      k = (k << 15) | (k >>> 17);
      k = Math.imul(k, c2);
      h ^= k;
      h = (h << 13) | (h >>> 19);
      h = (Math.imul(h, 5) + 0xe6546b64) | 0;
    }
    let k = 0;
    switch (n & 3) {
      case 3:
        k ^= b[blok + 2] << 16;
      // falls through
      case 2:
        k ^= b[blok + 1] << 8;
      // falls through
      case 1:
        k ^= b[blok];
        k = Math.imul(k, c1);
        k = (k << 15) | (k >>> 17);
        k = Math.imul(k, c2);
        h ^= k;
    }
    h ^= n;
    h ^= h >>> 16;
    h = Math.imul(h, 0x85ebca6b);
    h ^= h >>> 13;
    h = Math.imul(h, 0xc2b2ae35);
    h ^= h >>> 16;
    return h >>> 0;
  }

  function ngramlar(metin) {
    const kelimeler = metin.split(" ").filter((k) => k.length > 0);
    const cikti = [];
    for (const kelime of kelimeler) {
      const w = " " + kelime + " ";
      for (let n = CHAR_MIN; n <= CHAR_MAX; n++) {
        if (w.length < n) break;
        for (let i = 0; i + n <= w.length; i++) cikti.push("c:" + w.slice(i, i + n));
      }
    }
    for (let n = 1; n <= WORD_MAX; n++) {
      for (let i = 0; i + n <= kelimeler.length; i++) cikti.push("w:" + kelimeler.slice(i, i + n).join(" "));
    }
    return cikti;
  }

  // Kutu -> sayım haritası.
  function sayim(metin, nKutu) {
    const m = new Map();
    for (const g of ngramlar(metin)) {
      const k = murmur3(g) % nKutu;
      m.set(k, (m.get(k) || 0) + 1);
    }
    return m;
  }

  const api = { murmur3, ngramlar, sayim, CHAR_MIN, CHAR_MAX, WORD_MAX };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else kok.LockNetOzellik = api;
})(typeof self !== "undefined" ? self : this);
