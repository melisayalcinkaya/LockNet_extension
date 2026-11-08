// BERT WordPiece tokenizer (Hugging Face tokenizers ile aynı sonuç).
// Girdi önce preprocess.js'ten geçtiği için yalnızca küçük harf, rakam, "@" ve
// boşluk içerir; bu yüzden BertNormalizer'ın (lowercase=false, strip_accents=null)
// yapacağı bir şey kalmaz. BertPreTokenizer boşlukta ve noktalama işaretinde böler.
(function (kok) {
  "use strict";

  function noktalama(c) {
    const k = c.codePointAt(0);
    if ((k >= 33 && k <= 47) || (k >= 58 && k <= 64) || (k >= 91 && k <= 96) || (k >= 123 && k <= 126)) return true;
    return /\p{P}/u.test(c);
  }

  function onBol(metin) {
    const parcalar = [];
    for (const kelime of metin.split(/\s+/)) {
      if (!kelime) continue;
      let birikim = "";
      for (const c of kelime) {
        if (noktalama(c)) {
          if (birikim) parcalar.push(birikim);
          parcalar.push(c);
          birikim = "";
        } else birikim += c;
      }
      if (birikim) parcalar.push(birikim);
    }
    return parcalar;
  }

  function tokenizerOlustur(tokenizerJson, maksUzunluk) {
    const model = tokenizerJson.model;
    const sozluk = new Map(Object.entries(model.vocab));
    const onek = model.continuing_subword_prefix || "##";
    const maksKarakter = model.max_input_chars_per_word || 100;
    const unk = sozluk.get(model.unk_token || "[UNK]");
    const cls = sozluk.get("[CLS]");
    const sep = sozluk.get("[SEP]");

    function kelimeParcala(kelime) {
      const karakterler = Array.from(kelime);
      if (karakterler.length > maksKarakter) return [unk];
      const cikti = [];
      let bas = 0;
      while (bas < karakterler.length) {
        let son = karakterler.length;
        let bulunan = null;
        while (bas < son) {
          let alt = karakterler.slice(bas, son).join("");
          if (bas > 0) alt = onek + alt;
          if (sozluk.has(alt)) {
            bulunan = sozluk.get(alt);
            break;
          }
          son--;
        }
        if (bulunan === null) return [unk];
        cikti.push(bulunan);
        bas = son;
      }
      return cikti;
    }

    function kodla(metin) {
      let ids = [];
      for (const p of onBol(metin)) ids.push(...kelimeParcala(p));
      ids = ids.slice(0, maksUzunluk - 2);
      return [cls, ...ids, sep];
    }

    return { kodla };
  }

  const api = { tokenizerOlustur, onBol };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else kok.LockNetWordPiece = api;
})(typeof self !== "undefined" ? self : this);
