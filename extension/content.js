// İçerik betiği: sayfadaki metin bloklarını bulur, modele gönderir ve saldırgan
// bulunanları bulanıklaştırır. Model bu betikte değil, eklentinin offscreen
// sayfasında çalışır; metin hiçbir sunucuya gönderilmez.
(() => {
  "use strict";

  const EN_AZ = 5;
  const EN_FAZLA = 2000;
  const PARCA = 200;
  const PARTI = 24;
  const ATLA = "script,style,noscript,textarea,input,select,option,code,pre,svg,math,[contenteditable=''],[contenteditable='true']";

  let ayarlar = { aktif: true, mod: "dengeli", whitelist: [] };
  let esikler = null;
  let model = null;
  let hata = null;
  let basladi = false;
  const sayac = { taranan: 0, gizlenen: 0 };

  const blokOnbellek = new WeakMap();
  const gorulen = new WeakSet();
  const skorlar = new WeakMap();
  const puanlanan = new Set();
  const kuyruk = new Set();
  let gonderiliyor = false;
  let zamanlayici = null;

  // ── Ayarlar ─────────────────────────────────────────────────────
  const siteGuvenli = () => ayarlar.whitelist.includes(location.hostname);
  const calismali = () => ayarlar.aktif && !siteGuvenli();

  chrome.storage.sync.get(ayarlar, (d) => {
    ayarlar = d;
    if (calismali()) baslat();
  });

  chrome.storage.onChanged.addListener((d, alan) => {
    if (alan !== "sync") return;
    for (const k of Object.keys(d)) if (k in ayarlar) ayarlar[k] = d[k].newValue;
    if (calismali()) {
      baslat();
      hepsiniUygula();
    } else temizle();
  });

  chrome.runtime.onMessage.addListener((m, _g, yanit) => {
    if (m?.tur === "durum") yanit({ ...sayac, model, hata, calisiyor: calismali() });
  });

  // ── Görünüm ─────────────────────────────────────────────────────
  function stilEkle() {
    const s = document.createElement("style");
    s.textContent = `
      .locknet-gizli { filter: blur(6px) !important; cursor: pointer !important; user-select: none !important; transition: filter .15s; }
      .locknet-gizli:hover { filter: blur(4px) !important; }
      .locknet-acik { outline: 1px dashed rgba(200, 120, 0, .6); outline-offset: 2px; }`;
    (document.head || document.documentElement).appendChild(s);
  }

  // Gizli bloğa ilk tıklama içeriği gösterir; bağlantıya gitmez.
  document.addEventListener(
    "click",
    (o) => {
      const b = o.target instanceof Element && o.target.closest(".locknet-gizli");
      if (!b) return;
      o.preventDefault();
      o.stopPropagation();
      b.classList.replace("locknet-gizli", "locknet-acik");
      b.title = "LockNet: bu metni sen açtın.";
    },
    true,
  );

  function esik() {
    if (!esikler) return 1;
    return ayarlar.mod === "temkinli" ? esikler.esikTemkinli : esikler.esik;
  }

  function uygula(b) {
    if (b.classList.contains("locknet-acik")) return;
    const gizle = calismali() && skorlar.get(b) >= esik();
    const gizli = b.classList.contains("locknet-gizli");
    if (gizle && !gizli) {
      b.classList.add("locknet-gizli");
      b.title = "LockNet: bu metin saldırgan olabilir. Görmek için tıkla.";
      sayac.gizlenen++;
    } else if (!gizle && gizli) {
      b.classList.remove("locknet-gizli");
      b.removeAttribute("title");
      sayac.gizlenen--;
    }
  }

  function hepsiniUygula() {
    for (const b of puanlanan) {
      if (!b.isConnected) puanlanan.delete(b);
      else uygula(b);
    }
  }

  function temizle() {
    for (const b of puanlanan) {
      b.classList.remove("locknet-gizli", "locknet-acik");
      if (b.title.startsWith("LockNet")) b.removeAttribute("title");
    }
    sayac.gizlenen = 0;
  }

  // ── Metin bloklarını bulma ──────────────────────────────────────
  // Bir metin düğümünün bloğu: satır içi olmayan en yakın ata öğe.
  function blokBul(el) {
    const yol = [];
    let e = el;
    while (e && e !== document.body && e !== document.documentElement) {
      if (blokOnbellek.has(e)) {
        const b = blokOnbellek.get(e);
        yol.forEach((y) => blokOnbellek.set(y, b));
        return b;
      }
      yol.push(e);
      const g = getComputedStyle(e).display;
      if (g !== "inline" && g !== "contents") break;
      e = e.parentElement;
    }
    const b = yol.at(-1) || null;
    yol.forEach((y) => blokOnbellek.set(y, b));
    return b;
  }

  function blokMetni(b) {
    const parcalar = [];
    const y = document.createTreeWalker(b, NodeFilter.SHOW_TEXT);
    for (let n = y.nextNode(); n; n = y.nextNode()) {
      if (n.data.trim() && blokBul(n.parentElement) === b) parcalar.push(n.data);
    }
    return parcalar.join(" ").replace(/\s+/g, " ").trim();
  }

  // Uzun bloklar cümle sınırından ~200 karakterlik parçalara bölünür
  // (model en çok 64 parça-kelime görüyor); bloğun skoru en yüksek parçanın skorudur.
  function parcala(metin) {
    if (metin.length <= PARCA) return [metin];
    const cikti = [];
    let birikim = "";
    for (const c of metin.split(/(?<=[.!?…])\s+/)) {
      if (birikim && (birikim + " " + c).length > PARCA) {
        cikti.push(birikim);
        birikim = "";
      }
      birikim = birikim ? birikim + " " + c : c;
      while (birikim.length > PARCA * 1.5) {
        cikti.push(birikim.slice(0, PARCA));
        birikim = birikim.slice(PARCA);
      }
    }
    if (birikim) cikti.push(birikim);
    return cikti;
  }

  const gozlemci = new IntersectionObserver(
    (girdiler) => {
      for (const g of girdiler) {
        if (!g.isIntersecting) continue;
        gozlemci.unobserve(g.target);
        kuyruk.add(g.target);
      }
      planla();
    },
    { rootMargin: "1000px 0px" },
  );

  // guncelle: değişen bir alt ağaçtan geliyorsa, önceden puanlanmış bloklar yeniden puanlanır.
  function tara(kok, guncelle = false) {
    if (!calismali()) return;
    const y = document.createTreeWalker(kok, NodeFilter.SHOW_TEXT);
    for (let n = y.nextNode(); n; n = y.nextNode()) {
      const ata = n.parentElement;
      if (!ata || n.data.trim().length < 2 || ata.closest(ATLA)) continue;
      const b = blokBul(ata);
      if (!b) continue;
      if (gorulen.has(b)) {
        if (!guncelle || !puanlanan.has(b)) continue;
        puanlanan.delete(b);
      }
      gorulen.add(b);
      gozlemci.observe(b);
    }
  }

  // ── Modelle konuşma ─────────────────────────────────────────────
  function planla() {
    clearTimeout(zamanlayici);
    zamanlayici = setTimeout(gonder, 80);
  }

  async function gonder() {
    if (gonderiliyor || !kuyruk.size || !calismali()) return;
    gonderiliyor = true;
    const bloklar = [];
    const metinler = [];
    const sahip = [];
    for (const b of kuyruk) {
      kuyruk.delete(b);
      if (!b.isConnected) continue;
      const m = blokMetni(b);
      if (m.length < EN_AZ || m.length > EN_FAZLA) continue;
      bloklar.push(b);
      for (const p of parcala(m)) {
        metinler.push(p);
        sahip.push(bloklar.length - 1);
      }
      if (metinler.length >= PARTI) break;
    }
    try {
      if (metinler.length) {
        const y = await chrome.runtime.sendMessage({ hedef: "arka", metinler });
        if (y?.hata) throw new Error(y.hata);
        esikler = { esik: y.esik, esikTemkinli: y.esikTemkinli };
        model = y.model;
        hata = null;
        const enYuksek = bloklar.map(() => 0);
        y.skorlar.forEach((s, i) => (enYuksek[sahip[i]] = Math.max(enYuksek[sahip[i]], s)));
        bloklar.forEach((b, i) => {
          skorlar.set(b, enYuksek[i]);
          puanlanan.add(b);
          sayac.taranan++;
          uygula(b);
        });
      }
    } catch (h) {
      hata = String(h?.message || h);
      // Eklenti güncellendiyse bu sayfadaki betik artık bağlantısız; sessizce dur.
      if (!chrome.runtime?.id) return;
      bloklar.forEach((b) => kuyruk.add(b));
      await new Promise((r) => setTimeout(r, 2000));
    } finally {
      gonderiliyor = false;
    }
    if (kuyruk.size) planla();
  }

  // ── Başlatma ────────────────────────────────────────────────────
  function baslat() {
    if (basladi || !document.body) return;
    basladi = true;
    stilEkle();
    tara(document.body);
    let bekleyen = [];
    let z = null;
    new MutationObserver((kayitlar) => {
      for (const k of kayitlar) {
        if (k.type === "characterData") bekleyen.push(k.target.parentElement);
        else k.addedNodes.forEach((n) => bekleyen.push(n.nodeType === 3 ? n.parentElement : n));
      }
      clearTimeout(z);
      z = setTimeout(() => {
        const liste = bekleyen;
        bekleyen = [];
        for (const n of new Set(liste)) if (n && n.isConnected) tara(n, true);
      }, 150);
    }).observe(document.body, { childList: true, subtree: true, characterData: true });
  }
})();
