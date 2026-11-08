// Hizmet çalışanı: içerik betiklerinden gelen metinleri offscreen sayfasına iletir.
// Model, DOM ve WebAssembly gerektirdiği için hizmet çalışanında değil, tek bir
// görünmez offscreen sayfasında çalışır; böylece her sekme modeli ayrı ayrı yüklemez.
"use strict";

let acilis = null;

async function offscreenHazirla() {
  const yol = chrome.runtime.getURL("offscreen.html");
  const var_mi = await chrome.runtime.getContexts({ contextTypes: ["OFFSCREEN_DOCUMENT"], documentUrls: [yol] });
  if (var_mi.length) return;
  acilis ??= chrome.offscreen
    .createDocument({ url: "offscreen.html", reasons: ["WORKERS"], justification: "Metinleri cihaz üzerinde, WebAssembly ile çalışan modelle puanlamak" })
    .finally(() => (acilis = null));
  await acilis;
}

chrome.runtime.onMessage.addListener((mesaj, _gonderen, yanit) => {
  if (mesaj?.hedef !== "arka") return;
  offscreenHazirla()
    .then(() => chrome.runtime.sendMessage({ hedef: "offscreen", metinler: mesaj.metinler }))
    .then(yanit)
    .catch((h) => yanit({ hata: String(h?.message || h) }));
  return true;
});
