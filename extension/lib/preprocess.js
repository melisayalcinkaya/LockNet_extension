// training/locknet/preprocess.py ile birebir aynı kurallar.
// Bir kuralı değiştirirsen ikisini birlikte değiştir; training/tests/test_parity.py
// iki tarafı binlerce örnekte karşılaştırır.
(function (kok) {
  "use strict";

  const HARFLER = "a-zçğıöşüâîû";
  const HARF_RAKAM = HARFLER + "0-9";

  // Python ve JS'de \s farklı karakterleri kapsar; bu yüzden boşluk kümesi elle tanımlı.
  const TUM_BOSLUK_RE = /[\t\n\v\f\r \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff\u001c-\u001f]+/g;
  const URL_RE = /(?:https?:\/\/|www\.|pic\.twitter\.com\/)[^ ]+/gi;
  const MENTION_RE = /(^| )@[A-Za-z0-9_]+/g;
  const LEET = { 4: "a", "@": "a", 3: "e", 1: "i", 0: "o", 5: "s", $: "s", 7: "t", 9: "g" };
  const LEET_KARAKTER = Object.keys(LEET).join("");
  const LEET_TOKEN_RE = new RegExp(`[${HARF_RAKAM}@$]+`, "g");
  const ICERIDEKI_ISARET_RE = new RegExp(`(?<=[${HARF_RAKAM}])[.*_'’\`\\-]+(?=[${HARF_RAKAM}])`, "g");
  const IZINSIZ_RE = new RegExp(`[^${HARF_RAKAM}@ ]`, "g");
  const TEKRAR_RE = new RegExp(`([${HARFLER}])\\1{2,}`, "g");
  const TEK_HARF_DIZISI_RE = new RegExp(`(?:^|(?<= ))(?:[${HARFLER}] ){2,}[${HARFLER}](?= |$)`, "g");
  const HARF_RE = new RegExp(`[${HARFLER}]`);
  const BOSLUK_RE = / +/g;

  function turkceKucukHarf(metin) {
    return metin.replace(/I/g, "ı").replace(/İ/g, "i").toLowerCase().replace(/̇/g, "");
  }

  function leetCoz(token) {
    if (token === "@user") return token;
    const harfVar = HARF_RE.test(token);
    let leetVar = false;
    for (const c of token) if (LEET_KARAKTER.includes(c)) leetVar = true;
    if (!(harfVar && leetVar) || /^[0-9]{2,}/.test(token)) return token;
    let cikti = "";
    for (const c of token) cikti += LEET[c] !== undefined ? LEET[c] : c;
    return cikti;
  }

  function onIsle(metin) {
    metin = String(metin).normalize("NFC");
    metin = metin.replace(TUM_BOSLUK_RE, " ");
    metin = metin.replace(URL_RE, " url ");
    metin = metin.replace(MENTION_RE, (_, bas) => bas + " @user ");
    metin = turkceKucukHarf(metin);
    metin = metin.replace(ICERIDEKI_ISARET_RE, "");
    metin = metin.replace(LEET_TOKEN_RE, (t) => leetCoz(t));
    metin = metin.replace(IZINSIZ_RE, " ");
    metin = metin.replace(BOSLUK_RE, " ").trim();
    metin = metin
      .split(" ")
      .map((t) => (t === "@user" ? t : t.replace(/@/g, " ")))
      .join(" ");
    metin = metin.replace(TEKRAR_RE, "$1$1");
    metin = metin.replace(BOSLUK_RE, " ").trim();
    metin = metin.replace(TEK_HARF_DIZISI_RE, (m) => m.replace(/ /g, ""));
    return metin;
  }

  const api = { onIsle, turkceKucukHarf };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else kok.LockNetOnIsleme = api;
})(typeof self !== "undefined" ? self : this);
