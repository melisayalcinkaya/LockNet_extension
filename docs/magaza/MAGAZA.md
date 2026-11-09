# Chrome Web Store kaydı

Geliştirici panelinde (https://chrome.google.com/webstore/devconsole) doldurulacak alanlar. Paket: `python scripts/paketle.py` → `dist/locknet-<sürüm>.zip`.

## Mağaza bilgileri

**Ad:** LockNet

**Özet (en fazla 132 karakter):**
Türkçe saldırgan ve küfürlü metinleri sayfada bulanıklaştırır. Model tarayıcında çalışır; metinler cihazından çıkmaz.

**Kategori:** Erişilebilirlik (alternatif: Araçlar)

**Dil:** Türkçe

**Açıklama:**

```
LockNet, ziyaret ettiğin sitelerdeki Türkçe hakaret ve küfür içeren metinleri otomatik olarak bulanıklaştırır. Gizlenen bir metni görmek istersen üzerine tıklaman yeterli.

• Cihazda çalışır: Türkçe BERT modeli eklentinin içindedir ve WebAssembly ile tarayıcında çalışır. Okunan metinler hiçbir sunucuya gönderilmez.
• İki hassasiyet modu: "Dengeli" saldırgan metinlerin çoğunu yakalar; "Temkinli" yalnızca emin olduğu metinleri gizler.
• Güven listesi: İstediğin siteyi tek tıkla taramanın dışında bırakabilirsin.
• Dinamik sayfalarla uyumlu: Sonradan yüklenen yorumlar ve sonsuz kaydırma da taranır; önce ekranda görünen metinler değerlendirilir.

Nasıl ölçüldü?
Model, OffensEval-2020 Türkçe veri setiyle eğitildi ve Türkçe haber, forum ve sözlük sitelerinden toplanıp elle etiketlenen ayrı bir web test setinde denendi. Rastgele web metinlerinde yanlış alarm oranı Dengeli modda yaklaşık %2, Temkinli modda yaklaşık %1'dir.

Sınırlamalar: İroni, ima ve yazım hatalı küfürleri kaçırabilir; sert ama hakaret içermeyen eleştirileri ara sıra gizleyebilir. Yalnızca Türkçe metinler için tasarlanmıştır.

Açık kaynak: https://github.com/melisayalcinkaya/LockNet_extension
```

**Görseller (`docs/magaza/`):**
- Ekran görüntüleri (1280×800): `magaza_1.png`, `magaza_2.png`
- Küçük tanıtım kutucuğu (440×280): `tanitim_440x280.png`
- Simge (128×128): `extension/icons/128.png`

## Gizlilik sekmesi

**Tek amaç (single purpose):**
Web sayfalarındaki Türkçe saldırgan metinleri cihaz üzerinde çalışan bir modelle tespit edip bulanıklaştırmak.

**İzin gerekçeleri:**
- *Ana makine izinleri (http/https içerik betiği):* Eklentinin amacı, kullanıcının açtığı her sayfadaki metinleri değerlendirip saldırgan olanları bulanıklaştırmaktır; bu yüzden içerik betiği tüm sayfalarda çalışır. Metinler yalnızca yerelde işlenir.
- *storage:* Açık/kapalı durumu, hassasiyet modu ve güven listesini saklamak için.
- *offscreen:* WebAssembly modelini, sekmelerden ayrı tek bir görünmez eklenti sayfasında bir kez yükleyip çalıştırmak için.
- *activeTab:* Açılır pencerede o anki sitenin adını göstermek ve güven listesine eklemek için.

**Uzak kod:** Hayır. Tüm JavaScript ve WebAssembly dosyaları paketin içindedir.

**Veri kullanımı:** Hiçbir kullanıcı verisi toplanmaz veya aktarılmaz. "Web sitesi içeriği" yalnızca cihazda işlenir ve hiçbir yere gönderilmez; bu nedenle veri toplama kutucuklarının hiçbiri işaretlenmez. Üç beyan da onaylanır (satılmaz, amaç dışı kullanılmaz, kredi değerlendirmesi için kullanılmaz).

**Gizlilik politikası URL'si:**
https://github.com/melisayalcinkaya/LockNet_extension/blob/main/PRIVACY.md
