# LockNet — Gizlilik Politikası

Son güncelleme: 9 Kasım 2026

LockNet, ziyaret ettiğin web sayfalarındaki Türkçe metinleri **kendi tarayıcında** çalışan bir yapay zekâ modeliyle değerlendirir ve saldırgan bulduklarını bulanıklaştırır.

## Onay

Eklenti kurulduğunda bu bilgileri özetleyen bir sayfa açılır. Sen **"Kabul ediyorum, başlat"** demeden LockNet hiçbir sayfadaki metni okumaz. Eklentiyi açılır penceredeki ana anahtarla istediğin an durdurabilirsin; eklentiyi kaldırmak bütün ayarları siler.

## Hangi veriler işlenir?

- **Sayfa metinleri:** Eklenti, açtığın sayfalardaki görünür metin bloklarını okur. Bu metinler yalnızca bilgisayarındaki eklenti içinde, bellekte puanlanır. **Hiçbir sunucuya gönderilmez, kaydedilmez, saklanmaz.** Eklentinin kendi dosyaları dışında hiçbir adrese ağ isteği yapılmaz.
- **Ayarlar:** Açık/kapalı durumu, hassasiyet modu (Dengeli/Temkinli) ve güven listesine eklediğin alan adları `chrome.storage.sync` ile saklanır. Chrome'da senkronizasyon açıksa bu ayarlar Google hesabın üzerinden kendi cihazların arasında eşitlenir. Bu ayarlara geliştirici erişemez.
- **Sayaçlar:** Açılır penceredeki "taranan" ve "gizlenen" sayıları yalnızca o sekme açıkken bellekte tutulur.

## Chrome Web Store Kullanıcı Verileri Politikası

LockNet'in kullanıcı verisini kullanması ve aktarması, **Sınırlı Kullanım (Limited Use) şartları dahil**, [Chrome Web Store Kullanıcı Verileri Politikası](https://developer.chrome.com/docs/webstore/program-policies/limited-use)'na uygundur. Web sitesi içeriği yalnızca eklentinin tek amacı olan saldırgan metni bulanıklaştırmak için, yalnızca cihazda kullanılır; hiçbir kişiye veya üçüncü tarafa aktarılmaz, satılmaz, reklam ya da kredi değerlendirmesi için kullanılmaz ve hiçbir insan tarafından okunmaz.

## Neler yapılmaz?

- Kişisel veri, tarama geçmişi veya kullanım istatistiği toplanmaz.
- Analitik, reklam veya üçüncü taraf hizmeti kullanılmaz.
- Veri satılmaz ya da paylaşılmaz.

## İzinler neden gerekli?

| İzin | Neden |
|---|---|
| Tüm http/https sayfalarında içerik betiği | Sayfadaki metinleri okuyup bulanıklaştırabilmek için |
| `storage` | Ayarlarını hatırlamak için |
| `offscreen` | Modeli, sekmelerden ayrı tek bir görünmez eklenti sayfasında çalıştırmak için |
| `activeTab` | Açılır pencerede o anki sitenin adını gösterip güven listesine ekleyebilmek için |

## İletişim

Sorular için: melisa.yky2001@gmail.com

---

# LockNet — Privacy Policy (English)

LockNet scores the Turkish text on the pages you visit with a machine-learning model that runs **entirely inside your browser** and blurs text it finds offensive. Page text is processed in memory on your device only; it is never sent to any server, logged or stored. The only data saved are your settings (on/off, sensitivity mode, trusted sites) in `chrome.storage.sync`. No analytics, no third-party services, no data sales or sharing. LockNet's use and transfer of user data complies with the Chrome Web Store User Data Policy, including the Limited Use requirements. A consent page is shown on install; no page text is read before the user accepts. Contact: melisa.yky2001@gmail.com
