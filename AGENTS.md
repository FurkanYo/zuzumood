# AGENTS.md

Bu doküman, bu proje üzerinde çalışacak bir sonraki yapay zeka ajanı için kısa ama operasyonel bir rehberdir.

## Proje Özeti
- Proje: **ZuzuMood** (React + TypeScript + Vite).
- Router: `HashRouter` kullanıyor (`/#/shop`, `/#/product/:id`).
- Ürün kaynağı: `products/EtsyListingsDownload.csv`.
- Ürün datası runtime'da `services/data.ts` içinde CSV parse edilerek üretiliyor.

## Kritik Mimari Kararlar
1. **Tek kaynak CSV**
   - Sitede gösterilen tüm ürünler yalnızca `products/EtsyListingsDownload.csv` dosyasından gelir.
   - Bu dosyada olmayan ürün listede görünmez.
2. **Görsel kaynağı Etsy**
   - Kart ve detay görseli CSV'deki `IMAGE1` alanından gelir (Etsy CDN URL).
3. **Otomatik güncelleme davranışı**
   - CSV dosyası güncellenirse development ortamında HMR ile data yenilenir.
   - Production için yeni build/deploy ile güncelleme yayına alınır.
4. **Kategori çıkarımı**
   - Kategoriler başlık ve etiketlerdeki anahtar kelimelerden türetilir (`services/data.ts`).

## Dosya Yapısı (Önemli)
- `services/data.ts`: CSV parser + ürün oluşturma + kategori çıkarımı.
- `products/EtsyListingsDownload.csv`: Etsy export verisi (tek gerçek kaynak).
- `pages/Shop.tsx`, `pages/Home.tsx`, `pages/ProductDetail.tsx`: Ürün verisini `PRODUCTS` üzerinden kullanır.
- `public/sitemap.xml`, `public/robots.txt`: SEO tarama yapılandırması.
- `vite-env.d.ts`: Vite `?raw` import type desteği.

## SEO Notları
- `index.html` içinde temel title/description/keywords tanımlı.
- `public/sitemap.xml` mevcut rotaları içerir.
- Yeni route eklenirse sitemap ve robots kontrol edilmelidir.

## Geliştirme Komutları
- `npm run dev`
- `npm run build`
- `npm run preview`

## Değişiklik Yaparken Kontrol Listesi
1. Ürün datası yalnızca CSV'den geliyor mu?
2. CSV parse işlemi quote/newline içeren açıklamalarda bozulmuyor mu?
3. Yeni route eklendiyse sitemap güncellendi mi?
4. Build başarılı mı?
5. Node modules içinde değişiklik yapılmadı mı?

## Bilinen Kısıt
- Etsy export dosyasında doğrudan listing URL yoksa ürün linki Etsy shop search query ile üretilir.

## Teslim Standartları
- Kod değişikliği sonrası build çalıştır.
- Commit + PR kaydı oluştur.
- Final raporda dosya ve satır referanslarıyla değişikliği özetle.
