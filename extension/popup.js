const masterToggle    = document.getElementById('masterToggle');
const statusDot       = document.getElementById('statusDot');
const statusText      = document.getElementById('statusText');
const thresholdSlider = document.getElementById('thresholdSlider');
const thresholdValue  = document.getElementById('thresholdValue');
const thresholdDesc   = document.getElementById('thresholdDesc');
const statTarama      = document.getElementById('statTarama');
const statEngelendi   = document.getElementById('statEngelendi');
const siteHost        = document.getElementById('siteHost');
const whitelistBtn    = document.getElementById('whitelistBtn');

const DESCS = [
  { max: 30, text: 'Gevşek — yalnızca çok açık tehditler engellenir' },
  { max: 55, text: 'Dengeli — net zararlı içerikler engellenir' },
  { max: 75, text: 'Sıkı — şüpheli içerikler de engellenir' },
  { max: 91, text: 'Maksimum — neredeyse her şey filtrelenir' },
];

function thresholdDescription(val) {
  return DESCS.find(d => val <= d.max)?.text ?? DESCS.at(-1).text;
}

function applyActiveState(active) {
  document.body.classList.toggle('disabled', !active);
  statusDot.className    = 'status-dot' + (active ? '' : ' passive');
  statusText.textContent = active ? 'Aktif — sayfa taranıyor' : 'Devre dışı';
}

function whitelistBtnGuncelle(listede) {
  whitelistBtn.textContent = listede ? '✓ Güven listesinde' : 'Güven listesine ekle';
  whitelistBtn.classList.toggle('whitelisted', listede);
}

// ── Aktif sekmenin host'unu al ───────────────────────────────────
let mevcutHost = '';

chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  if (!tabs[0]?.url) return;
  try {
    mevcutHost = new URL(tabs[0].url).hostname;
    siteHost.textContent = mevcutHost;
  } catch (_) {
    siteHost.textContent = '—';
  }
});

// ── Ayarları yükle ───────────────────────────────────────────────
chrome.storage.sync.get(
  { aktif: true, esik: 50, whitelist: [], tarama: 0, engellendi: 0 },
  (ayarlar) => {
    masterToggle.checked = ayarlar.aktif;
    applyActiveState(ayarlar.aktif);

    thresholdSlider.value      = ayarlar.esik;
    thresholdValue.textContent = `%${ayarlar.esik}`;
    thresholdDesc.textContent  = thresholdDescription(ayarlar.esik);

    statTarama.textContent    = ayarlar.tarama;
    statEngelendi.textContent = ayarlar.engellendi;

    // Whitelist butonunu storage'dan taze oku
    const listede = mevcutHost && ayarlar.whitelist.includes(mevcutHost);
    whitelistBtnGuncelle(listede);
  }
);

// ── Master toggle ────────────────────────────────────────────────
masterToggle.addEventListener('change', () => {
  const aktif = masterToggle.checked;
  chrome.storage.sync.set({ aktif });
  applyActiveState(aktif);
});

// ── Eşik kaydırıcı ──────────────────────────────────────────────
thresholdSlider.addEventListener('input', () => {
  const val = Number(thresholdSlider.value);
  thresholdValue.textContent = `%${val}`;
  thresholdDesc.textContent  = thresholdDescription(val);
  chrome.storage.sync.set({ esik: val });
});

// ── Whitelist butonu ─────────────────────────────────────────────
whitelistBtn.addEventListener('click', () => {
  if (!mevcutHost) return;

  chrome.storage.sync.get({ whitelist: [] }, (d) => {
    let wl = d.whitelist;
    const listede = wl.includes(mevcutHost);

    if (listede) {
      wl = wl.filter(h => h !== mevcutHost);
    } else {
      wl.push(mevcutHost);
    }

    chrome.storage.sync.set({ whitelist: wl }, () => {
      whitelistBtnGuncelle(!listede);
    });
  });
});

// ── Storage değişikliklerini popup açıkken de yansıt ────────────
chrome.storage.onChanged.addListener((changes) => {
  if (changes.tarama)     statTarama.textContent    = changes.tarama.newValue;
  if (changes.engellendi) statEngelendi.textContent = changes.engellendi.newValue;

  if (changes.whitelist && mevcutHost) {
    const listede = changes.whitelist.newValue.includes(mevcutHost);
    whitelistBtnGuncelle(listede);
  }
});