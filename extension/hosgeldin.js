"use strict";
const durum = document.getElementById("durum");

async function goster() {
  const { onay } = await chrome.storage.local.get({ onay: false });
  durum.textContent = onay ? "LockNet açık. Bu sekmeyi kapatabilirsin." : "";
}

document.getElementById("kabul").addEventListener("click", async () => {
  await chrome.storage.local.set({ onay: true });
  goster();
});

document.getElementById("ret").addEventListener("click", async () => {
  await chrome.storage.local.set({ onay: false });
  durum.textContent = "Eklenti hiçbir sayfayı okumayacak. İstersen chrome://extensions sayfasından kaldırabilirsin.";
});

goster();
