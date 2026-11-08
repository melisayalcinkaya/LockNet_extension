# LockNet — Gizlilik Politikası

Son güncelleme: 8 Kasım 2026

LockNet, ziyaret ettiğin web sayfalarındaki Türkçe metinleri **kendi tarayıcında** çalışan bir yapay zekâ modeliyle değerlendirir ve saldırgan bulduklarını bulanıklaştırır.

## Hangi veriler işlenir?

- **Sayfa metinleri:** Eklenti, açtığın sayfalardaki görünür metin bloklarını okur. Bu metinler yalnızca bilgisayarındaki eklenti içinde, bellekte puanlanır. **Hiçbir sunucuya gönderilmez, kaydedilmez, saklanmaz.** Eklentinin kendi dosyaları dışında hiçbir adrese ağ isteği yapılmaz.
- **Ayarlar:** Açık/kapalı durumu, hassasiyet modu (Dengeli/Temkinli) ve güven listesine eklediğin alan adları `chrome.storage.sync` ile saklanır. Chrome'da senkronizasyon açıksa bu ayarlar Google hesabın üzerinden kendi cihazların arasında eşitlenir. Bu ayarlara geliştirici erişemez.
- **Sayaçlar:** Açılır penceredeki "taranan" ve "gizlenen" sayıları yalnızca o sekme açıkken bellekte tutulur.

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

LockNet scores the Turkish text on the pages you visit with a machine-learning model that runs **entirely inside your browser** and blurs text it finds offensive. Page text is processed in memory on your device only; it is never sent to any server, logged or stored. The only data saved are your settings (on/off, sensitivity mode, trusted sites) in `chrome.storage.sync`. No analytics, no third-party services, no data sales or sharing. Contact: melisa.yky2001@gmail.com
