"use strict";

const $ = (id) => document.getElementById(id);
const ACIKLAMA = {
  dengeli: "Saldırgan metinlerin çoğunu yakalar; arada temiz bir metni de gizleyebilir.",
  temkinli: "Yalnızca emin olduğu metinleri gizler; yanlış alarm çok nadir, bazılarını kaçırır.",
};

let sekme = null;
let host = "";

function durumYaz(aktif, guvenli, d) {
  document.body.classList.toggle("disabled", !aktif);
  $("statusDot").className = "status-dot" + (aktif && !guvenli ? "" : " passive");
  if (!aktif) $("statusText").textContent = "Devre dışı";
  else if (guvenli) $("statusText").textContent = "Bu site güven listesinde";
  else if (d?.hata) $("statusText").textContent = "Model yüklenemedi";
  else if (d) $("statusText").textContent = d.model ? `Aktif — ${d.model}` : "Aktif — model yükleniyor";
  else $("statusText").textContent = "Aktif — bu sayfada çalışmıyor";
}

function wlButon(listede) {
  $("whitelistBtn").textContent = listede ? "✓ Güven listesinde" : "Güven listesine ekle";
  $("whitelistBtn").classList.toggle("whitelisted", listede);
}

async function yenile() {
  const a = await chrome.storage.sync.get({ aktif: true, mod: "dengeli", whitelist: [] });
  $("masterToggle").checked = a.aktif;
  $(a.mod === "temkinli" ? "modTemkinli" : "modDengeli").checked = true;
  $("modDesc").textContent = ACIKLAMA[a.mod] || ACIKLAMA.dengeli;
  const guvenli = !!host && a.whitelist.includes(host);
  wlButon(guvenli);
  let d = null;
  if (sekme?.id != null) d = await chrome.tabs.sendMessage(sekme.id, { tur: "durum" }).catch(() => null);
  $("statTarama").textContent = d ? d.taranan : "—";
  $("statEngelendi").textContent = d ? d.gizlenen : "—";
  durumYaz(a.aktif, guvenli, d);
}

(async () => {
  [sekme] = await chrome.tabs.query({ active: true, currentWindow: true });
  try {
    const u = new URL(sekme.url);
    if (u.protocol.startsWith("http")) host = u.hostname;
  } catch (_) {}
  $("siteHost").textContent = host || "—";
  $("whitelistBtn").disabled = !host;
  await yenile();
  setInterval(yenile, 1000);
})();

$("masterToggle").addEventListener("change", (o) => chrome.storage.sync.set({ aktif: o.target.checked }).then(yenile));
document.querySelectorAll('input[name="mod"]').forEach((r) =>
  r.addEventListener("change", () => chrome.storage.sync.set({ mod: r.value }).then(yenile)),
);
$("whitelistBtn").addEventListener("click", async () => {
  if (!host) return;
  const { whitelist } = await chrome.storage.sync.get({ whitelist: [] });
  const yeni = whitelist.includes(host) ? whitelist.filter((h) => h !== host) : [...whitelist, host];
  await chrome.storage.sync.set({ whitelist: yeni });
  yenile();
});
