let model;
let sozluk = {};
let hazirMi = false;

// ── Sözlük ve modeli yükle ───────────────────────────────────────
async function kaynaklariYukle(modelUrl, sozlukUrl) {
  try {
    const sozlukYanit = await fetch(sozlukUrl);
    sozluk = await sozlukYanit.json();

    model = await tf.loadLayersModel(modelUrl);
    hazirMi = true;
    console.log("🤖 LockNet AI ve Kelime Sözlüğü Sandbox içinde başarıyla senkronize oldu!");

    window.parent.postMessage({ action: 'hazir' }, '*');
  } catch (error) {
    console.error("❌ Yükleme hatası:", error);
  }
}

// ── Tokenizer — max_length 25'ten 50'ye güncellendi ─────────────
function metniSayiyaCevir(text, maxLength = 50) {
  const temizMetin = text
    .toLowerCase()
    .replace(/http\S+|www\S+/g, '')          // URL temizle
    .replace(/@\S+/g, '')                     // mention temizle
    .replace(/#\S+/g, '')                     // hashtag temizle
    .replace(/[^\w\sçğışöüçğişöü]/gi, ' ')  // noktalama temizle
    .replace(/\s+/g, ' ')
    .trim();

  const kelimeler = temizMetin.split(' ');
  const dizi = new Array(maxLength).fill(0);

  for (let i = 0; i < Math.min(kelimeler.length, maxLength); i++) {
    const kelime = kelimeler[i];
    dizi[i] = sozluk[kelime] !== undefined ? sozluk[kelime] : 1;
  }
  return dizi;
}

// ── Mesajları dinle ──────────────────────────────────────────────
window.addEventListener('message', async (event) => {
  const data = event.data;
  if (!data || !data.action) return;

  if (data.action === 'init') {
    await kaynaklariYukle(data.modelUrl, data.sozlukUrl);
    return;
  }

  if (data.action === 'predict') {
    if (!hazirMi || !model || !sozluk) return;

    const { text, elementId } = data;
    try {
      const sayisalDizi = metniSayiyaCevir(text);
      const tahmin = model.predict(tf.tensor2d([sayisalDizi], [1, 50]));
      const skor = tahmin.dataSync()[0];

      tahmin.dispose();

      event.source.postMessage({ score: skor, elementId }, event.origin);
    } catch (err) {
      console.error("Tahmin esnasında hata:", err);
      event.source.postMessage({ score: 0, elementId }, event.origin);
    }
  }
});