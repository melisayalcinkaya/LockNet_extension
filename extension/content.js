// ── Ayarları storage'dan çek ─────────────────────────────────────
let ayarlar = { aktif: true, esik: 50, whitelist: [] };
let eklentiBasladi = false;

chrome.storage.sync.get({ aktif: true, esik: 50, whitelist: [] }, (d) => {
  ayarlar = d;
  baslangicKontrol();
});

chrome.storage.onChanged.addListener((changes) => {
  if (changes.aktif)     ayarlar.aktif     = changes.aktif.newValue;
  if (changes.esik)      ayarlar.esik      = changes.esik.newValue;
  if (changes.whitelist) {
    ayarlar.whitelist = changes.whitelist.newValue;
    whitelistDegisti();
  }
});

function baslangicKontrol() {
  if (ayarlar.aktif && !ayarlar.whitelist.includes(location.hostname)) {
    if (!eklentiBasladi) {
      eklentiBasladi = true;
      baslatEklenti();
    }
  }
}

// Whitelist değişince anlık uygula
function whitelistDegisti() {
  const sitede = ayarlar.whitelist.includes(location.hostname);

  if (sitede) {
    // Whitelist'e eklendi → tüm sansürleri kaldır
    document.querySelectorAll('[data-locknet-denetlendi]').forEach(el => {
      el.style.filter = '';
      el.style.backgroundColor = '';
      el.style.cursor = '';
      el.title = '';
    });
  } else {
    // Whitelist'ten çıkarıldı → sayfayı yeniden tara
    if (!eklentiBasladi) {
      eklentiBasladi = true;
      baslatEklenti();
    }
  }
}

// ── Eklentiyi başlat ─────────────────────────────────────────────
function baslatEklenti() {
  const iframe = document.createElement('iframe');
  iframe.src = chrome.runtime.getURL('sandbox.html');
  iframe.style.display = 'none';
  document.body.appendChild(iframe);

  const elementHaritasi = new Map();
  let elementSayaci  = 0;
  let taramaSayisi   = 0;
  let engelSayisi    = 0;

  // ── Kuyruk sistemi ──────────────────────────────────────────────
  const kuyruk     = [];
  let isleniyor    = false;
  let sandboxHazir = false;

  function kuyrugaEkle(is) {
    kuyruk.push(is);
    sonrakiIsiBas();
  }

  function sonrakiIsiBas() {
    if (isleniyor || !sandboxHazir || kuyruk.length === 0) return;
    isleniyor = true;
    const is = kuyruk.shift();
    iframe.contentWindow.postMessage(
      { action: 'predict', text: is.text, elementId: is.elementId },
      '*'
    );
  }

  // ── Sandbox'tan gelen mesajları dinle ───────────────────────────
  window.addEventListener('message', (event) => {
    if (!event.data) return;

    if (event.data.action === 'hazir') {
      sandboxHazir = true;
      sonrakiIsiBas();
      return;
    }

    if (typeof event.data.score === 'undefined') return;

    isleniyor = false;
    sonrakiIsiBas();

    const { score, elementId } = event.data;
    const hedefElement = elementHaritasi.get(elementId);
    taramaSayisi++;

    // Skor geldiğinde whitelist kontrolü yap (aradan eklenmiş olabilir)
    if (ayarlar.whitelist.includes(location.hostname)) return;

    const esikOrani = ayarlar.esik / 100;

    if (hedefElement && score > esikOrani) {
      engelSayisi++;
      hedefElement.style.filter = 'blur(5px)';
      hedefElement.style.backgroundColor = '#ffcccc';
      hedefElement.style.cursor = 'pointer';
      hedefElement.title = `LockNet: Bu içerik zararlı bulundu (skor: %${Math.round(score * 100)})`;

      hedefElement.addEventListener('click', function goster() {
        this.style.filter = 'none';
        this.style.backgroundColor = '#fff8cc';
        this.title = 'LockNet: İçerik geçici olarak gösteriliyor.';
      }, { once: true });
    }

    chrome.storage.sync.set({ tarama: taramaSayisi, engellendi: engelSayisi });
  });

  // ── Sayfa tarama ────────────────────────────────────────────────
  function sayfayiDenetle() {
    if (!iframe.contentWindow) return;
    if (!ayarlar.aktif) return;
    if (ayarlar.whitelist.includes(location.hostname)) return;

    const elementler = document.querySelectorAll('p, span, h1, h2, h3, div');
    elementler.forEach(element => {
      const hamMetin = element.innerText ? element.innerText.trim() : '';

      if (
        hamMetin.length > 5 &&
        hamMetin.length < 200 &&
        !element.hasAttribute('data-locknet-denetlendi')
      ) {
        element.setAttribute('data-locknet-denetlendi', 'true');
        elementSayaci++;
        elementHaritasi.set(elementSayaci, element);
        kuyrugaEkle({ text: hamMetin, elementId: elementSayaci });
      }
    });
  }

  // ── Iframe yüklenince başlat ─────────────────────────────────────
  iframe.onload = () => {
    iframe.contentWindow.postMessage({
      action: 'init',
      modelUrl: chrome.runtime.getURL('locknet_web_modeli/model.json'),
      sozlukUrl: chrome.runtime.getURL('kelime_sozlugu.json')
    }, '*');

    sayfayiDenetle();

    const gozlemci = new MutationObserver(() => sayfayiDenetle());
    gozlemci.observe(document.body, { childList: true, subtree: true });
  };
}