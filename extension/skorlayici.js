// Offscreen sayfasında çalışır: modeli bir kez yükler, gelen metin partilerini puanlar.
// Metinler bu sayfadan dışarı çıkmaz; ağ isteği yalnızca eklentinin kendi
// dosyalarına (chrome-extension://) yapılır.
"use strict";

// Her cümle tek başına çalıştırılır: int8 dinamik nicemlemede etkinleşme ölçeği
// bütün tensörden hesaplandığı için, partideki komşu cümleler ve dolgu skoru
// değiştirir. Tekli çalıştırma Python'daki ölçümle birebir aynı sonucu verir.
const PARTI = 1;
let hazirlik = null;

async function jsonOku(yol) {
  return (await fetch(chrome.runtime.getURL(yol))).json();
}

async function bertYukle(dizin, meta) {
  ort.env.wasm.wasmPaths = chrome.runtime.getURL("vendor/ort/");
  // Eklenti sayfaları "cross-origin isolated" değil; çoklu iş parçacığı kullanılamaz.
  ort.env.wasm.numThreads = 1;
  const tokJson = await jsonOku(`${dizin}/tokenizer.json`);
  const tok = LockNetWordPiece.tokenizerOlustur(tokJson, meta.maks_uzunluk);
  const oturum = await ort.InferenceSession.create(chrome.runtime.getURL(`${dizin}/model.onnx`), {
    executionProviders: ["wasm"],
    graphOptimizationLevel: "all",
  });
  const pad = tokJson.model.vocab["[PAD]"] ?? 0;

  async function parti(metinler) {
    const kodlar = metinler.map((m) => tok.kodla(LockNetOnIsleme.onIsle(m)));
    const n = Math.max(...kodlar.map((k) => k.length));
    const ids = new BigInt64Array(kodlar.length * n).fill(BigInt(pad));
    const maske = new BigInt64Array(kodlar.length * n);
    kodlar.forEach((k, i) => {
      for (let j = 0; j < k.length; j++) {
        ids[i * n + j] = BigInt(k[j]);
        maske[i * n + j] = 1n;
      }
    });
    const boyut = [kodlar.length, n];
    const cikti = await oturum.run({
      input_ids: new ort.Tensor("int64", ids, boyut),
      attention_mask: new ort.Tensor("int64", maske, boyut),
    });
    const lg = cikti.logits.data;
    return kodlar.map((_, i) => 1 / (1 + Math.exp(lg[i * 2] - lg[i * 2 + 1])));
  }

  async function skorla(metinler) {
    const sira = metinler.map((m, i) => i).sort((a, b) => metinler[a].length - metinler[b].length);
    const sonuc = new Array(metinler.length);
    for (let i = 0; i < sira.length; i += PARTI) {
      const dilim = sira.slice(i, i + PARTI);
      const s = await parti(dilim.map((j) => metinler[j]));
      dilim.forEach((j, k) => (sonuc[j] = s[k]));
    }
    return sonuc;
  }

  return { skorla };
}

async function tabanYukle(dizin) {
  const m = await LockNetModel.yukle(chrome.runtime.getURL(`${dizin}/meta.json`), chrome.runtime.getURL(`${dizin}/weights.bin`));
  return { skorla: async (metinler) => metinler.map((t) => m.skor(t)) };
}

async function hazirla() {
  const { dizin: ad } = await jsonOku("model/secim.json");
  const dizin = `model/${ad}`;
  const meta = await jsonOku(`${dizin}/meta.json`);
  const model = meta.tur === "bert-onnx-int8" ? await bertYukle(dizin, meta) : await tabanYukle(dizin);
  return { ...model, ad, esik: meta.esik, esikTemkinli: meta.esik_temkinli };
}

chrome.runtime.onMessage.addListener((mesaj, _gonderen, yanit) => {
  if (mesaj?.hedef !== "offscreen") return;
  hazirlik ??= hazirla();
  hazirlik
    .then(async (m) => {
      const t0 = performance.now();
      const skorlar = mesaj.metinler.length ? await m.skorla(mesaj.metinler) : [];
      yanit({ skorlar, esik: m.esik, esikTemkinli: m.esikTemkinli, model: m.ad, ms: performance.now() - t0 });
    })
    .catch((h) => {
      hazirlik = null;
      yanit({ hata: String(h?.message || h) });
    });
  return true;
});
