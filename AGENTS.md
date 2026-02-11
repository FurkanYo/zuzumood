# AGENTS.md

Bu doküman, bu proje üzerinde çalışacak bir sonraki yapay zeka ajanı için operasyonel rehberdir.

## Proje Özeti
- Proje: **ZuzuMood** (React + TypeScript + Vite).
- Router: `HashRouter` (`/#/shop`, `/#/product/:id`).
- Ürün kaynağı: **tek kaynak** `products/EtsyListingsDownload.csv`.
- Ürün datası runtime'da `services/data.ts` içinde CSV parse edilerek üretiliyor.
- AI chat: `components/AIStylist.tsx` içinde Gemini (`@google/genai`) ile çalışıyor.

## Kritik Mimari Kararlar
1. **Tek kaynak CSV**
   - Sitede gösterilen ürünler yalnızca `products/EtsyListingsDownload.csv` dosyasından gelir.
   - Bu dosyada olmayan ürün listede görünmez.
2. **Görsel kaynağı Etsy CDN**
   - Kart ve detay görseli CSV'deki `IMAGE1` alanından gelir.
   - Bazı ortamlarda Etsy görselleri CORS/CORB yüzünden bloklanabilir; bu durum AI chat ile doğrudan ilgili değildir.
3. **AI API key çözümü (deployment kritik)**
   - Frontend’de kullanılan ana değişken: `VITE_GEMINI_API_KEY`.
   - Fallback sırası: `GEMINI_API_KEY` → `GEMINI_KEY` → `API_KEY`.
   - `vite.config.ts` içinde bu anahtarlar `__GEMINI_API_KEY__` ve eski `process.env.*` tanımlarıyla derleme anında gömülür.
4. **Otomatik güncelleme davranışı**
   - CSV dosyası development ortamında HMR ile yenilenir.
   - Production için yeni build/deploy gerekir.
5. **Kategori çıkarımı**
   - Kategoriler başlık ve etiketlerdeki anahtar kelimelerden türetilir (`services/data.ts`).

## Dosya Yapısı (Önemli)
- `services/data.ts`: CSV parser + ürün oluşturma + kategori çıkarımı.
- `products/EtsyListingsDownload.csv`: Etsy export verisi (tek gerçek kaynak).
- `components/AIStylist.tsx`: Gemini entegrasyonu, chat UI, öneri ürünleri.
- `pages/Shop.tsx`, `pages/Home.tsx`, `pages/ProductDetail.tsx`: Ürün verisini `PRODUCTS` üzerinden kullanır.
- `public/sitemap.xml`, `public/robots.txt`: SEO tarama yapılandırması.
- `vite.config.ts`: env yükleme + anahtar inject + alias.
- `vite-env.d.ts`: Vite `import.meta.env` ve global define tipleri.

## AI Stylist Davranışı (Güncel)
- Prompt artık **daha kısa, pratik, kullanıcı diline uyumlu** cevap üretmeye odaklıdır.
- Satın alma/ödeme/kargo niyetli sorularda yanıtın içinde Etsy mağaza linki geçmesi zorunludur: `https://www.etsy.com/shop/ZuzuMood`.
- Öneri ürün sayısı en fazla **4** ile sınırlandı.
- Model boş/bozuk `message` döndürürse UI tarafında güvenli fallback mesajı gösterilir.
- Ürün bağlamına `price` ve `etsyUrl` da eklendi; ürün uydurma riskini azaltır.

## SEO Notları
- `index.html` içinde title/description/keywords tanımlı.
- `public/sitemap.xml` en az `/` ve `/#/shop` içerir.
- Yeni route eklendiğinde `sitemap.xml` ve gerekirse `robots.txt` güncellenmelidir.
- HashRouter kullanıldığı için canonical ve sosyal paylaşım meta stratejisi ayrıca değerlendirilmelidir.

## Chatbot Troubleshooting
1. Tarayıcı console’da `An API Key must be set when running in a browser` görürsen:
   - Netlify environment variables içinde `VITE_GEMINI_API_KEY` tanımlı mı kontrol et.
   - Değişken eklendikten sonra **yeniden deploy** et (eski build’e sonradan eklenen env yansımaz).
2. Sadece `GEMINI_KEY`/`API_KEY` varsa:
   - Uygulama fallback ile çalışabilir ama standart olarak `VITE_GEMINI_API_KEY` kullan.
3. `index.css 404`:
   - `index.html` içinde hardcoded `/index.css` referansı olmamalı.
4. Etsy görsel CORS hataları:
   - Ürün görsellerini etkiler; chatbot text cevap üretimini normalde engellemez.
5. Yanıtlar aşırı “kurumsal/lüks” ise:
   - `components/AIStylist.tsx` içindeki `systemInstruction` kurallarını kontrol et.
   - JSON schema + kısa cevap limiti + dil uyumu maddeleri korunmalı.

## Geliştirme Komutları
- `npm install`
- `npm run dev`
- `npm run build`
- `npm run preview`

## Değişiklik Yaparken Kontrol Listesi
1. Ürün datası yalnızca CSV'den geliyor mu?
2. CSV parse işlemi quote/newline içeren açıklamalarda bozulmuyor mu?
3. Yeni route eklendiyse sitemap güncellendi mi?
4. Build başarılı mı?
5. Node modules içinde değişiklik yapılmadı mı?
6. AI ile ilgili değişiklikte env isimleri dokümante edildi mi?
7. Chatbot mesaj tonu gerçek kullanıcı sorularında kısa ve net mi?

## Bilinen Kısıt
- Etsy export dosyasında doğrudan listing URL yoksa ürün linki Etsy shop search query ile üretilir.

## Son Görev Özeti (2026-02-11)
- Kullanıcı şikâyeti: chatbot çok uzun ve “saçma/marka metni” gibi cevaplar üretiyordu.
- Yapılanlar:
  - `components/AIStylist.tsx` prompt yeniden yazıldı (kısa, net, kullanıcı dilinde).
  - Satın alma soruları için Etsy URL zorunluluğu eklendi.
  - Öneri ürün ID limiti 4 yapıldı.
  - Boş `message` için güvenli fallback metni eklendi.
- SEO/Sitemap kontrolü:
  - Yeni route eklenmedi, bu yüzden `public/sitemap.xml` değişmedi.

## Teslim Standartları
- Kod değişikliği sonrası build çalıştır.
- Commit + PR kaydı oluştur.
- Final raporda dosya ve satır referanslarıyla değişikliği özetle.
